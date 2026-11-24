"""Moving-texture histograms from LROC WAC albedo and LOLA topography (run on the team computer).

Reads data/external/ALBEDO_WAC_HAPKE_NORMALIZED_REFLECTANCE_643NM/WAC_HAPKE_643NM_<tile>.IMG (float32,
76 pixels per degree, attached PDS3 label of 27360 bytes) and data/external/LOLA_DATA/ldem_64.img (int16 x
0.5 m, 64 pixels per degree, line 0 = 90 N, longitude 0-360 E). For each 5-degree latitude band (|lat| < 60):
  * albedo smoothed and resampled to the 0.9 km event-camera pixel; LOLA heights likewise;
  * earthshine shading: Lunar-Lambert (L = 0.7) for the Earth at the sub-Earth point (0 N, 0 E), normalised to
    a flat surface, only where the Earth is more than 10 deg above the horizon (the near side);
  * background B = dark + earthshine x albedo / near-side mean x shading, for each (dark, I0) case;
  * per window W the clipped rise d ln B = max(0, +-grad(ln B) x 0.41 px/s x W) along track (both drift
    directions), summed over 2x2 and 3x3 groups and histogrammed (log bins 1e-6..10).
Output: tmp/texture/texture_<tag>.json (merge into data/flash_crater_models/texture_histograms.json).
Usage: python texture_map.py <tile> <tag> <name:dark:I0> [...]
       e.g. python texture_map.py E350N0450 a nominal_1.3e4:6242:1.3e4 m636_2.5e4:6866:2.5e4
One tile with four cases takes about 1-2 minutes on a laptop. The 3 November 2026 run used tiles E350N0450,
E350N3150 and E350S3150 and the cases nominal_1.3e4, nominal_2.5e4, m636_1.3e4, m636_2.5e4, pess_4e4, pess_6e4.
"""
import sys, json, math, os
import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E = os.path.join(ROOT, 'data', 'external') + os.sep
TILES = {'E350N0450': (0, 70, 0, 90), 'E350N3150': (0, 70, 270, 360), 'E350S3150': (-70, 0, 270, 360)}
CAM_KM = 0.9; V_PX = 0.41; WINDOWS = (0.05, 0.2, 0.8, 2.0)
BINS = np.concatenate([[0], np.logspace(-6, 1, 141)])


def wac(tile):
    path = E + f'ALBEDO_WAC_HAPKE_NORMALIZED_REFLECTANCE_643NM/WAC_HAPKE_643NM_{tile}.IMG'
    rec, S = 27360, 6840
    L = (os.path.getsize(path) - rec) // (4 * S)
    a = np.fromfile(path, dtype='<f4', count=L * S, offset=rec).reshape(L, S).astype(np.float32)
    a[~np.isfinite(a) | (a <= 0) | (a > 2)] = np.nan
    return a


def ldem_box(lat0, lat1, lon0, lon1):
    mm = np.memmap(E + 'LOLA_DATA/ldem_64.img', dtype='<i2', mode='r', shape=(11520, 23040))
    r0, r1 = int((90 - lat1) * 64), int((90 - lat0) * 64); c0, c1 = int(lon0 * 64), int(lon1 * 64)
    return np.array(mm[r0:r1, c0:c1]).astype(np.float32) * 0.5


def earth_dir(lat, lon):
    """Unit vector to the sub-Earth point (0 N, 0 E) in local east-north-up components."""
    la, lo = np.radians(lat), np.radians(lon)
    p = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
    e_hat = np.stack([-np.sin(lo), np.cos(lo), np.zeros_like(lo)])
    n_hat = np.stack([-np.sin(la) * np.cos(lo), -np.sin(la) * np.sin(lo), np.cos(la)])
    earth = np.array([1.0, 0, 0])[:, None, None]
    return (earth * e_hat).sum(0), (earth * n_hat).sum(0), (earth * p).sum(0)


def main(tile, tag, cases):
    lat0, lat1, lon0, lon1 = TILES[tile]
    A = wac(tile); H = ldem_box(lat0, lat1, lon0, lon1)
    res = {}
    for b0 in range(int(lat0), int(lat1), 5):
        if abs(b0 + 2.5) > 60:
            continue
        r0, r1 = int((lat1 - (b0 + 5)) * 76), int((lat1 - b0) * 76)
        phi = math.radians(b0 + 2.5)
        fy = 0.399 / CAM_KM; fx = 0.399 * math.cos(phi) / CAM_KM
        a = A[r0:r1]; a = np.where(np.isfinite(a), a, np.nanmedian(a))
        a = ndimage.zoom(ndimage.gaussian_filter(a, (0.42 / fy, 0.42 / fx)), (fy, fx), order=1)
        h0, h1 = int((lat1 - (b0 + 5)) * 64), int((lat1 - b0) * 64)
        gy = 0.474 / CAM_KM; gx = 0.474 * math.cos(phi) / CAM_KM
        hgt = ndimage.zoom(ndimage.gaussian_filter(H[h0:h1], (0.42 / gy, 0.42 / gx)), (gy, gx), order=1)
        n0, n1 = min(a.shape[0], hgt.shape[0]), min(a.shape[1], hgt.shape[1]); a, hgt = a[:n0, :n1], hgt[:n0, :n1]
        lat = b0 + 5 - (np.arange(n0) + 0.5) * (5.0 / n0); lon = lon0 + (np.arange(n1) + 0.5) * ((lon1 - lon0) / n1)
        LAT, LON = np.meshgrid(lat, lon, indexing='ij')
        eE, eN, eU = earth_dir(LAT, LON)
        near = eU > math.cos(math.radians(80))
        if near.sum() < 1000:
            continue
        dzdn, dzde = np.gradient(hgt, CAM_KM * 1e3); dzdn = -dzdn          # rows run south
        nrm = np.sqrt(dzde ** 2 + dzdn ** 2 + 1)
        mu0 = np.clip((-dzde * eE - dzdn * eN + eU) / nrm, 0, None); mu = 1 / nrm; L = 0.7
        shade = (2 * L * mu0 / (mu0 + mu) + (1 - L) * mu0) / (2 * L * eU / (eU + 1) + (1 - L) * eU)
        I = a / np.nanmean(a[near]) * shade
        for name, dark, I0 in cases:
            lnB = np.log(dark + (I0 - dark) * I)
            g = np.gradient(lnB, axis=0)
            rc = res.setdefault(name, {})
            for W in WINDOWS:
                for sgn in (1, -1):
                    dpos = np.clip(sgn * g * V_PX * W, 0, None)
                    for size in (2, 3):
                        s = ndimage.uniform_filter(dpos, size) * size * size
                        hist, _ = np.histogram(s[near], BINS)
                        key = f'{W}_{size}'
                        rc[key] = (np.array(rc.get(key, np.zeros(len(BINS) - 1))) + hist).tolist()
        res['n_pixels'] = res.get('n_pixels', 0) + int(near.sum())
        print(tile, b0, int(near.sum()), flush=True)
    os.makedirs(os.path.join(ROOT, 'tmp', 'texture'), exist_ok=True)
    path = os.path.join(ROOT, 'tmp', 'texture', f'texture_{tag}.json')
    out = json.load(open(path)) if os.path.exists(path) else {}
    out[tile] = res; out['bins'] = BINS.tolist()
    json.dump(out, open(path, 'w'))


if __name__ == '__main__':
    cs = []
    for c in sys.argv[3:]:
        n, d, i = c.split(':'); cs.append((n, float(d), float(i)))
    main(sys.argv[1], sys.argv[2], cs)
