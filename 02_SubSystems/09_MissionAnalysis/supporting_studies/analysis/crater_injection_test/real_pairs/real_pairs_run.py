"""Real new-crater pairs at crater-camera resolution (pre-SRR follow-up, 3 November 2026).

Uses the before/after NAC windows of eight catalogued new craters (cut_windows.py) and answers:
  1. Registration: global affine (ORB features + RANSAC, four flip combinations), then a smooth residual
     shift field (cubic polynomial fitted to sub-pixel phase correlation of 192-pixel tiles).
  2. False candidates of a REAL pair: thresholds for 0.01 false candidates per km2 at 0.9 m, from the pair
     itself with the crater region (120 m) masked, for two detectors:
       - 'bowl': the kit's matched filter (crater_test.change_map; shading of a fresh bowl + bright halo);
       - 'anomaly': reflectance-anomaly detector: scale-normalised Laplacian of Gaussian of the locally
         gain-matched difference (sigma 1-10 camera pixels, both signs, max over scales, robust z).
  3. Located real craters: is each found at 0.9 m (TriScape200 model of crater_test.degrade), 4 noise repeats?
  4. Reflectance profiles of the located craters (after/before - 1 versus r/D, at NAC resolution).
  5. Injection into the real pairs with halo models ('dark': -8 % to 6 R, as measured; 'weak': -4 % to 4 R;
     'kit': the kit's +7.5 % to 3 R; 'none'), detected with the anomaly detector at the pair's threshold.
Outputs: data/crater_injection_test/real_pairs_summary.json, figures/crater_injection_test/real_pairs.png.
Usage: python -I real_pairs_run.py [windows_dir]   (default <repo>/tmp/nac_chips/windows; about 1-2 hours)
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.dirname(HERE))
import crater_test as ct                                                    # noqa: E402

I_F = 3.05185094759972e-05
SIG = (1.0, 1.5, 2.5, 4.0, 6.0, 10.0)
HALOS = {'dark': dict(halo_amp=-0.08, halo_extent=6.0), 'weak': dict(halo_amp=-0.04, halo_extent=4.0),
         'kit': dict(halo_amp=0.075, halo_extent=3.0), 'none': dict(halo_amp=0.0, halo_extent=3.0)}
D_GRID = [1.8, 2.2, 2.6, 3.0, 3.5, 4.0, 5.0, 6.5]


# ---------------------------------------------------------------- registration
def load(wdir, cid, t):
    d = np.load(os.path.join(wdir, f'win_{cid}{t}.npz')); dn = d['dn'].astype(np.float32)
    I = dn * I_F; I[dn <= -32752] = np.nan
    return I, d


def register(B, A, res_b, res_a):
    from skimage.feature import ORB, match_descriptors
    from skimage.measure import ransac
    from skimage.transform import AffineTransform, warp
    def prep(I):
        J = np.where(np.isfinite(I), I, np.nanmedian(I)); lo, hi = np.percentile(J, [1, 99]); return np.clip((J - lo) / (hi - lo), 0, 1)
    bad = ~np.isfinite(A)
    Az = ndimage.zoom(np.where(bad, np.nanmedian(A), A), res_a / res_b, order=1)
    badz = ndimage.zoom(bad.astype(np.float32), res_a / res_b, order=0) > 0.5
    f = 0.5
    orb = ORB(n_keypoints=3000, fast_threshold=0.05); orb.detect_and_extract(ndimage.zoom(prep(B), f, order=1))
    best = None
    for fv in (0, 1):
        for fh in (0, 1):
            Af = Az[::-1] if fv else Az; Af = Af[:, ::-1] if fh else Af
            o2 = ORB(n_keypoints=3000, fast_threshold=0.05); o2.detect_and_extract(ndimage.zoom(prep(Af), f, order=1))
            m = match_descriptors(orb.descriptors, o2.descriptors, cross_check=True, max_ratio=0.85)
            if len(m) < 10:
                continue
            src = o2.keypoints[m[:, 1]][:, ::-1]; dst = orb.keypoints[m[:, 0]][:, ::-1]
            model, inl = ransac((src, dst), AffineTransform, min_samples=3, residual_threshold=2.0, max_trials=3000,
                                rng=np.random.default_rng(0))
            n = int(inl.sum()) if inl is not None else 0
            if best is None or n > best[0]:
                best = (n, fv, fh, model)
    n, fv, fh, model = best
    Af = Az[::-1] if fv else Az; Af = Af[:, ::-1] if fh else Af
    bf = badz[::-1] if fv else badz; bf = bf[:, ::-1] if fh else bf
    M = model.params.copy(); M[:2, 2] /= f
    T = AffineTransform(matrix=M)
    Aw = warp(Af, T.inverse, output_shape=B.shape, order=1, preserve_range=True, cval=np.nan)
    bw = warp(bf.astype(float), T.inverse, output_shape=B.shape, order=0, preserve_range=True, cval=1) > 0.5
    valid = ndimage.binary_erosion(np.isfinite(B) & np.isfinite(Aw) & ~bw, iterations=15)
    Aw = np.nan_to_num(Aw * np.nanmedian(B[valid]) / np.nanmedian(Aw[valid])).astype(np.float32)
    return np.nan_to_num(B).astype(np.float32), Aw, valid, dict(inliers=n, flip=[fv, fh])


def tile_shifts(B, A, V, tile=192, step=128):
    from skimage.registration import phase_cross_correlation
    pts = []
    for y in range(0, B.shape[0] - tile, step):
        for x in range(0, B.shape[1] - tile, step):
            if not V[y:y + tile, x:x + tile].all():
                continue
            b = B[y:y + tile, x:x + tile]; a = A[y:y + tile, x:x + tile]
            b = b - ndimage.gaussian_filter(b, 8); a = a - ndimage.gaussian_filter(a, 8)
            sh, err, _ = phase_cross_correlation(b, a, upsample_factor=20, normalization=None)
            pts.append((y + tile / 2, x + tile / 2, sh[0], sh[1], err))
    return np.array(pts)


def refine(B, A, V):
    p = tile_shifts(B, A, V); p = p[p[:, 4] < np.percentile(p[:, 4], 90)]
    def basis(y, x):
        return [np.ones_like(y), y, x, y * y, x * y, x * x, y ** 3, x ** 3, y * y * x, y * x * x]
    M = np.stack(basis(p[:, 0] / B.shape[0], p[:, 1] / B.shape[1]), 1)
    co = []
    for c in (2, 3):
        w = np.ones(len(p))
        for _ in range(5):
            cf = np.linalg.lstsq(M * w[:, None], p[:, c] * w, rcond=None)[0]
            r = p[:, c] - M @ cf; s = 1.4826 * np.median(np.abs(r)) + 1e-6; w = (np.abs(r) < 3 * s).astype(float)
        co.append(cf)
    yy, xx = np.indices(B.shape, dtype=np.float32)
    BB = basis(yy / B.shape[0], xx / B.shape[1])
    dy = sum(c * m for c, m in zip(co[0], BB)); dx = sum(c * m for c, m in zip(co[1], BB))
    A2 = ndimage.map_coordinates(A, [yy - dy, xx - dx], order=3, mode='nearest').astype(np.float32)
    p2 = tile_shifts(B, A2, V)
    return A2, dict(tiles=int(len(p)), shift_rms_affine_px=float(np.sqrt((p[:, 2:4] ** 2).mean())),
                    shift_max_affine_px=float(np.abs(p[:, 2:4]).max()), shift_rms_refined_px=float(np.sqrt((p2[:, 2:4] ** 2).mean())))


# ---------------------------------------------------------------- detection
def anomaly_stat(b, a, cfg):
    bs, as_ = ndimage.gaussian_filter(b, 30), ndimage.gaussian_filter(a, 30)
    a = a * bs / np.clip(as_, 1e-3, None)
    q = (a - b) / np.sqrt(ct.noise_sigma(b, cfg) ** 2 + ct.noise_sigma(a, cfg) ** 2)
    zs = []
    for s in SIG:
        F = -ndimage.gaussian_laplace(q, s) * s * s
        med = np.median(F); mad = np.median(np.abs(F - med)) * 1.4826 + 1e-12
        zs.append(np.abs(F - med) / mad)
    return np.max(zs, 0)


def thr_from_peaks(pk, area, fa=0.01):
    pk = np.sort(np.asarray(pk))[::-1]; target = fa * area
    if target >= 5:
        return float(pk[int(target)])
    top = pk[:min(200, len(pk))]; n_above = np.arange(1, len(top) + 1)
    slope, icpt = np.polyfit(top, np.log(n_above), 1)
    return float(max((math.log(target) - icpt) / slope, top[0]))


def crop_pair(B, A, V, erode=40):
    V2 = ndimage.binary_erosion(V, iterations=erode)
    rows, cols = np.where(V2); r0, r1, c0, c1 = rows.min(), rows.max(), cols.min(), cols.max()
    return (B[r0:r1, c0:c1] / np.median(B[V2]), A[r0:r1, c0:c1] / np.median(A[V2]), V2[r0:r1, c0:c1], (r0, c0))


def sun_azimuth(Bc, g, inc, cfg):
    from scipy import signal
    q = Bc - ndimage.gaussian_filter(Bc, 20); best = None
    for az in range(0, 360, 20):
        ratio, _ = ct.render_ratio(12 * g, g, inc, az, cfg, oversample=2); t = ratio - ratio.mean(); t /= np.linalg.norm(t)
        s = np.percentile(signal.fftconvolve(q, t[::-1, ::-1], mode='same'), 99.9)
        if best is None or s > best[1]:
            best = (az, s)
    return best[0]


def null_and_crater(Bc, Ac, Vc, g, cfg, loc, D, detector, tm=None, reps=4, seed=3):
    rng = np.random.default_rng(seed); pk_null, area, zc = [], 0.0, []
    for _ in range(reps):
        b = ct.degrade(Bc, g, cfg, rng); a = ct.degrade(Ac, g, cfg, rng)
        Z = anomaly_stat(b, a, cfg) if detector == 'anomaly' else ct.change_map(b, a, cfg, tm)[1]
        vz = ndimage.zoom(Vc.astype(float), (Z.shape[0] / Vc.shape[0], Z.shape[1] / Vc.shape[1]), order=0) > 0.5
        mask = ndimage.binary_erosion(vz, iterations=12)
        yy, xx = np.indices(Z.shape)
        if loc is not None:
            mask &= np.hypot(yy - loc[0], xx - loc[1]) > 120.0 / cfg['gsd_dst']
            near = np.hypot(yy - loc[0], xx - loc[1]) <= max(4, 3 * D / cfg['gsd_dst'])
            zc.append(float(Z[near].max()))
        pk_null += [p[2] for p in ct.peaks(np.where(mask, Z, -1e9 if detector == 'bowl' else 0), -np.inf) if p[2] > -1e8]
        area += mask.sum() * cfg['gsd_dst'] ** 2 / 1e6
    thr = thr_from_peaks(pk_null, area)
    out = dict(threshold=thr, null_area_km2=float(area))
    if zc:
        out.update(crater_Z=zc, found=int(sum(z >= thr for z in zc)), reps=reps,
                   null_density_above_crater_per_km2=float(np.mean([np.sum(np.array(pk_null) >= z) for z in zc]) / area))
    return out


def halo_profile(B, A, l, s, D, g):
    edges = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 20])
    l, s = int(l), int(s); h = min(int(22 * D / g) + 20, l, s, B.shape[0] - l - 1, B.shape[1] - s - 1)
    b = B[l - h:l + h, s - h:s + h].astype(float); a = A[l - h:l + h, s - h:s + h].astype(float)
    sm = int(12 * D / g); a = a * ndimage.gaussian_filter(b, sm) / ndimage.gaussian_filter(a, sm)
    r = a / np.clip(b, 1e-3, None) - 1
    yy, xx = np.indices(r.shape)
    j = np.argmax(np.where(np.hypot(yy - h, xx - h) * g < 6, np.abs(ndimage.gaussian_filter(r, 0.4 * D / g)), 0))
    cy, cx = np.unravel_index(j, r.shape); rD = np.hypot(yy - cy, xx - cx) * g / D
    bg = np.median(r[(rD > 16) & (rD < 20)])
    prof = [(float(e0), float(e1), float(np.mean(r[(rD >= e0) & (rD < e1)]) - bg)) for e0, e1 in zip(edges[:-1], edges[1:])
            if ((rD >= e0) & (rD < e1)).sum() > 5]
    return dict(profile_r_over_D=prof, extent_r_over_D_2pct=float(max([p[1] for p in prof if abs(p[2]) > 0.02] or [0])))


def inject_run(Bc, Ac, Vc, g, inc, az, lc, thr, halo, reps=6, per=8, seed=11):
    cfg = dict(ct.DEFAULTS, depth=0.14, rim=0.028, **HALOS[halo])
    cfg['signal_e'] = 300.0 * math.cos(math.radians(inc)) / math.cos(math.radians(65.0))
    rng = np.random.default_rng(seed); sc = g / 0.9; recs = []
    for _ in range(reps):
        for Db in (D_GRID[0::2], D_GRID[1::2]):
            Ds = (list(Db) * (per // len(Db) + 1))[:per]; cen = []; tries = 0
            while len(cen) < len(Ds) and tries < 5000:
                tries += 1
                l = rng.uniform(80, Bc.shape[0] - 80); s = rng.uniform(80, Bc.shape[1] - 80)
                if not Vc[int(l), int(s)] or (lc is not None and math.hypot(l - lc[0], s - lc[1]) * g < 150):
                    continue
                if any(math.hypot(l - a_, s - b_) * g < 130 for a_, b_ in cen):
                    continue
                cen.append((l, s))
            Ds = Ds[:len(cen)]
            Ai = ct.inject(Ac, cen, Ds, g, inc, az, cfg)
            Z = anomaly_stat(ct.degrade(Bc, g, cfg, rng), ct.degrade(Ai, g, cfg, rng), cfg)
            yy, xx = np.indices(Z.shape)
            for (l, s), D in zip(cen, Ds):
                z = float(Z[np.hypot(yy - l * sc, xx - s * sc) <= max(3, 1.5 * D / 0.9)].max())
                recs.append(dict(D=D, Z=z, hit=bool(z >= thr)))
    return recs


def run_crater(args):
    wdir, c, loc = args
    cid, D = c['id'], c['D_m']
    B, db = load(wdir, cid, 'b'); A, da = load(wdir, cid, 'a')
    g, inc = float(db['res']), float(da['inc'])
    B, A, V, reg = register(B, A, g, float(da['res']))
    A, ref = refine(B, A, V); reg.update(ref)
    out = dict(id=cid, D_m=D, gsd_src=g, inc_after=inc, inc_before=float(db['inc']), registration=reg)
    Bc, Ac, Vc, (r0, c0) = crop_pair(B, A, V)
    cfg = dict(ct.DEFAULTS, depth=0.14, rim=0.028, halo_amp=0.075)
    cfg['signal_e'] = 300.0 * math.cos(math.radians(inc)) / math.cos(math.radians(65.0))
    az = sun_azimuth(Bc, g, inc, cfg); out['sun_az_fit'] = az
    lc = None if loc is None else (loc['line'] - r0, loc['sample'] - c0)
    lcam = None if lc is None else (lc[0] * g / 0.9, lc[1] * g / 0.9)
    out['anomaly'] = null_and_crater(Bc, Ac, Vc, g, cfg, lcam, D, 'anomaly')
    tm = ct.Templates(inc, az, cfg, g, np.random.default_rng(5))
    out['bowl'] = null_and_crater(Bc, Ac, Vc, g, cfg, lcam, D, 'bowl', tm=tm)
    out['same_image_bowl_threshold'] = ct.calibrate_threshold(Bc, Bc, g, cfg, np.random.default_rng(5), tm, n=4)[0]
    if loc is not None:
        out['halo'] = halo_profile(B, A, loc['line'], loc['sample'], D, g)
    if out['registration']['shift_rms_refined_px'] < 0.3:
        out['injection'] = {h: inject_run(Bc, Ac, Vc, g, inc, az, lc, out['anomaly']['threshold'], h) for h in HALOS}
    print(cid, {k: v for k, v in out.items() if k != 'injection'}, flush=True)
    return out


def main():
    wdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'tmp', 'nac_chips', 'windows')
    meta = json.load(open(os.path.join(HERE, 'nac_pairs.json')))
    loc = json.load(open(os.path.join(HERE, 'located_craters.json')))['located']
    from multiprocessing import Pool
    with Pool(2) as pool:
        res = pool.map(run_crater, [(wdir, c, loc.get(c['id'])) for c in meta['craters']])
    summ = dict(model=__doc__, craters=res, injection_fit={})
    for h in HALOS:
        for subset, pick in (('all_registered', lambda r: True), ('well_registered', lambda r: r['registration']['shift_rms_refined_px'] < 0.11)):
            recs = [x for r in res if 'injection' in r and pick(r) for x in r['injection'][h]]
            if recs:
                summ['injection_fit'][f'{h}|{subset}'] = dict(
                    ct.fit_confirmation([x['D'] for x in recs], [x['hit'] for x in recs], 0.9),
                    by_D={str(D): [sum(x['hit'] for x in recs if x['D'] == D), sum(1 for x in recs if x['D'] == D)] for D in D_GRID},
                    pairs=[r['id'] for r in res if 'injection' in r and pick(r)])
    os.makedirs(os.path.join(ROOT, 'data', 'crater_injection_test'), exist_ok=True)
    json.dump(summ, open(os.path.join(ROOT, 'data', 'crater_injection_test', 'real_pairs_summary.json'), 'w'), indent=1, default=float)
    for k, v in summ['injection_fit'].items():
        print(k, {a: b for a, b in v.items() if a != 'by_D'}, v['by_D'], flush=True)


if __name__ == '__main__':
    main()
