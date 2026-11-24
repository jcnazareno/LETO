"""Crater-injection test for the impact-energy conversion proposal (pre-SRR work item 2).

Question: with the TriScape200 crater camera at 300 km (0.9 m Bayer pixels), which fraction of fresh craters of
diameter D is found by a before/after comparison against an LROC NAC "before" image, and how well is D measured?
The answers replace two placeholders of the joint model (analysis/flash_crater_models/joint_model.py):

    confirmation  c(D) = CMAX * Phi((ln D - ln(k * GSD)) / KW)     now CMAX = 0.85, k = 3.5, KW = 0.15, GSD = 0.9 m
    diameter error  sd(ln D) = hypot(a, b / D_px)                     now a = 0.03, b = 0.35 px

Commands (run from this folder; see README.md):

    python crater_test.py selftest                       synthetic terrain, checks the whole chain (minutes)
    python crater_test.py inject  --before B.IMG [--after A.IMG] --gsd 0.5 --inc 45 --az 90 --out RUN
    python crater_test.py real    --list real_craters.csv --out RUN
    python crater_test.py review-export --before B.IMG [--after A.IMG] --gsd 0.5 --inc 45 --az 90 --out RUN
    python crater_test.py review-score  --out RUN --answers RUN/review/my_answers.csv
    python crater_test.py summary --runs RUN1 RUN2 ...   pooled fit of all runs -> data/crater_injection_test/

Images: PDS3 .IMG (LROC NAC CDR, read with the built-in label parser), GeoTIFF/TIFF (tifffile) or PNG/JPG (Pillow).
Only numpy, scipy, matplotlib, tifffile and Pillow are needed. Results are written to RUN/results.json.

Modelling assumptions (all configurable): fresh simple crater with depth/diameter 0.2, rim height 0.04 D and
ejecta height falling off as (r/R)^-3; a bright albedo halo of +10% out to 3 R; Lunar-Lambert photometry
(L = 0.7) with nadir viewing; cast shadows; pixel integration, a Gaussian PSF of 0.6 px, shot and read noise
for a mean signal of 300 e- per green pixel (proposal S8: 250-370 e-), and RGB Bayer sampling with bilinear
demosaicking. These choices are the main limitation of the injection mode; the 'real' mode uses craters that
actually formed during the LRO mission and therefore does not depend on the crater model.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage, optimize, signal, stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data' / 'crater_injection_test'

# current joint-model placeholders (for comparison plots)
JM = dict(CMAX=0.85, k=3.5, KW=0.15, GSD=0.9, a=0.03, b=0.35)

DEFAULTS = dict(gsd_dst=0.9, psf_px=0.6, signal_e=300.0, read_e=15.0, bayer=True,
                depth=0.20, rim=0.04, halo_amp=0.10, halo_extent=3.0, lunar_lambert_L=0.7,
                fa_per_km2=0.01)


# ----------------------------------------------------------------------------- image input
def _pds3_label(path):
    raw = open(path, 'rb').read(200000).decode('latin-1')
    m_end = re.search(r'^END\s*$', raw, re.M)
    lab = raw[:m_end.start()] if m_end else raw
    def get(key, block=None, default=None):
        txt = lab
        if block:
            m = re.search(r'OBJECT\s*=\s*%s(.*?)END_OBJECT\s*=\s*%s' % (block, block), lab, re.S)
            txt = m.group(1) if m else lab
        m = re.search(r'^\s*%s\s*=\s*(.+?)\s*$' % re.escape(key), txt, re.M)
        return m.group(1).strip().strip('"') if m else default
    return lab, get


def read_pds3(path):
    """Minimal PDS3 reader for single-band LROC NAC EDR/CDR images (attached or detached label)."""
    lab, get = _pds3_label(path)
    rec = int(get('RECORD_BYTES', default='1'))
    lines = int(get('LINES', 'IMAGE'))
    samples = int(get('LINE_SAMPLES', 'IMAGE'))
    bits = int(get('SAMPLE_BITS', 'IMAGE'))
    stype = get('SAMPLE_TYPE', 'IMAGE').upper()
    prefix = int(get('LINE_PREFIX_BYTES', 'IMAGE', '0') or 0)
    suffix = int(get('LINE_SUFFIX_BYTES', 'IMAGE', '0') or 0)
    ptr = get('^IMAGE')
    fname, offset = path, 0
    m = re.match(r'\(?\s*"?([^",)]+?)"?\s*,\s*(\d+)\s*(<BYTES>)?\s*\)?$', ptr or '')
    if m and not m.group(1).strip().isdigit():
        fname = os.path.join(os.path.dirname(path), m.group(1).strip())
        offset = (int(m.group(2)) - 1) * (1 if m.group(3) else rec)
    else:
        m2 = re.match(r'(\d+)\s*(<BYTES>)?', ptr or '1')
        offset = (int(m2.group(1)) - 1) * (1 if m2.group(2) else rec)
    if 'REAL' in stype:
        dt = ('>' if stype.startswith(('IEEE', 'MSB')) else '<') + 'f%d' % (bits // 8)
    else:
        dt = ('>' if stype.startswith('MSB') else '<') + ('u' if 'UNSIGNED' in stype else 'i') + '%d' % (bits // 8)
    rowbytes = prefix + samples * bits // 8 + suffix
    buf = np.fromfile(fname, dtype=np.uint8, count=rowbytes * lines, offset=offset).reshape(lines, rowbytes)
    img = buf[:, prefix:prefix + samples * bits // 8].copy().view(dt).reshape(lines, samples).astype(np.float32)
    bad = ~np.isfinite(img) | (img < -1e30) | (img > 1e30)
    if 'REAL' not in stype and 'UNSIGNED' not in stype:      # LROC CDR I/F: scaled int16, specials at the bottom
        bad |= img <= np.iinfo(np.dtype(dt)).min + 8
    img[bad] = np.nan
    return img


def read_image(path):
    p = str(path).lower()
    if p.endswith(('.img', '.lbl')):
        return read_pds3(path)
    if p.endswith(('.tif', '.tiff')):
        import tifffile
        a = tifffile.imread(path)
    else:
        from PIL import Image
        a = np.asarray(Image.open(path))
    a = np.asarray(a, dtype=np.float32)
    if a.ndim == 3:
        a = a[..., :3].mean(axis=2)
    return a


def crop(img, c0=None, size=None):
    """Return a NaN-free sub-image; if c0/size are given, crop (line, sample) window around c0."""
    if c0 is not None:
        l, s = c0
        h = size // 2
        img = img[max(0, l - h):l + h, max(0, s - h):s + h]
    good = np.isfinite(img)
    if not good.all():
        rows = np.where(good.all(axis=1))[0]
        cols = np.where(good[rows].all(axis=0))[0] if rows.size else np.array([], int)
        if rows.size < 32 or cols.size < 32:
            img = np.where(good, img, np.nanmedian(img))
        else:
            img = img[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    return img


def coregister(ref, mov):
    """Shift mov onto ref by phase correlation with a parabolic sub-pixel refinement."""
    a = ref - ref.mean(); b = mov - mov.mean()
    F = np.fft.fft2(a) * np.conj(np.fft.fft2(b))
    r = np.real(np.fft.ifft2(F / (np.abs(F) + 1e-12)))
    i, j = np.unravel_index(np.argmax(r), r.shape)
    def sub(c, n, axis):
        cm, cp = [(c - 1) % n, (c + 1) % n]
        v = (r[cm, j], r[i, j], r[cp, j]) if axis == 0 else (r[i, cm], r[i, j], r[i, cp])
        den = v[0] - 2 * v[1] + v[2]
        return c + (0.5 * (v[0] - v[2]) / den if den != 0 else 0.0)
    di, dj = sub(i, r.shape[0], 0), sub(j, r.shape[1], 1)
    di = di - r.shape[0] if di > r.shape[0] / 2 else di
    dj = dj - r.shape[1] if dj > r.shape[1] / 2 else dj
    return ndimage.shift(mov, (di, dj), order=1, mode='nearest'), (di, dj)


# ----------------------------------------------------------------------------- crater model
def crater_height(r_over_R, depth=0.2, rim=0.04):
    """Height in units of D for a fresh simple crater: parabolic bowl, rim, ejecta ~ (r/R)^-3."""
    x = np.asarray(r_over_R)
    inside = -2 * depth + (2 * depth + 2 * rim) * x ** 2       # z(0) = -depth*D, z(R) = rim*D (units of D: R = 0.5)
    outside = 2 * rim * np.maximum(x, 1e-6) ** -3
    return np.where(x <= 1, inside, outside) / 2.0


def sun_vector(inc_deg, az_deg):
    """Unit vector towards the Sun; az measured from image 'up' (-line) clockwise, inc from vertical."""
    i, a = math.radians(inc_deg), math.radians(az_deg)
    return np.array([-math.sin(i) * math.cos(a), math.sin(i) * math.sin(a), math.cos(i)])  # (dline, dsample, up)


def shade(z, dx, inc, az, L=0.7):
    """Lunar-Lambert reflectance of height map z [m] on a grid of spacing dx [m], relative to flat ground,
    including cast shadows. Viewing is nadir."""
    gl, gs = np.gradient(z, dx)
    n = np.stack([-gl, -gs, np.ones_like(z)]); n /= np.linalg.norm(n, axis=0)
    s = sun_vector(inc, az)
    mu0 = np.clip(n[0] * s[0] + n[1] * s[1] + n[2] * s[2], 0, None)
    mu = n[2]
    refl = 2 * L * mu0 / (mu0 + mu) + (1 - L) * mu0
    c0 = math.cos(math.radians(inc))
    flat = 2 * L * c0 / (c0 + 1) + (1 - L) * c0
    # cast shadows: march towards the Sun
    elev = math.radians(90 - inc)
    horiz = np.array([s[0], s[1]]); horiz = horiz / (np.linalg.norm(horiz) + 1e-12)
    lit = np.ones_like(z, bool)
    step = 0.5
    nmax = int(2 * max(z.shape) / step)
    for t in range(1, nmax):
        d = t * step
        zs = ndimage.shift(z, (-horiz[0] * d, -horiz[1] * d), order=1, mode='nearest')
        lit &= ~(zs > z + d * dx * math.tan(elev) + 1e-9)
        if d * dx * math.tan(elev) > (z.max() - z.min()) + 1e-6:
            break
    return np.where(lit, refl, 0.0) / flat


def render_ratio(D, gsd_src, inc, az, cfg, oversample=4):
    """Multiplicative brightness change (after/before) of a fresh crater of diameter D [m], on the source grid.
    Returns (ratio patch, half-size in source pixels)."""
    R = D / 2
    half = int(math.ceil(max(cfg['halo_extent'], 2.5) * R / gsd_src)) + 3
    n = 2 * half + 1
    dx = gsd_src / oversample
    c = np.arange(n * oversample) * dx - (n * gsd_src) / 2 + dx / 2
    L_, S_ = np.meshgrid(c, c, indexing='ij')
    rr = np.hypot(L_, S_) / R
    z = crater_height(rr, cfg['depth'], cfg['rim']) * D
    ratio = shade(z, dx, inc, az, cfg['lunar_lambert_L'])
    halo = 1 + cfg['halo_amp'] * np.where(rr <= 1, 1.0, np.exp(-(rr - 1) / max(cfg['halo_extent'] - 1, 0.1) * 2.3))
    ratio = ratio * halo
    ratio = ratio.reshape(n, oversample, n, oversample).mean(axis=(1, 3))
    return ratio, half


def inject(img, centres, Ds, gsd_src, inc, az, cfg):
    out = img.copy()
    for (l, s), D in zip(centres, Ds):
        ratio, h = render_ratio(D, gsd_src, inc, az, cfg)
        li, si = int(round(l)), int(round(s))
        sl = slice(li - h, li + h + 1); ss = slice(si - h, si + h + 1)
        if sl.start < 0 or ss.start < 0 or sl.stop > img.shape[0] or ss.stop > img.shape[1]:
            continue
        out[sl, ss] *= ratio
    return out


# ----------------------------------------------------------------------------- camera model
BAYER_GAIN = dict(R=0.90, G=1.00, B=0.75)   # relative channel signal for a grey lunar scene (assumption)


def degrade(img, gsd_src, cfg, rng, noise=True):
    """Resample to the crater camera (pixel integration + PSF), add shot/read noise with RGB Bayer sampling
    and bilinear demosaicking. Returns an image in units of mean signal (about 1)."""
    scale = cfg['gsd_dst'] / gsd_src
    a = ndimage.gaussian_filter(img, sigma=0.42 * scale) if scale > 1 else img
    a = ndimage.zoom(a, 1 / scale, order=1)
    a = ndimage.gaussian_filter(a, sigma=cfg['psf_px'])
    a = a / np.median(a)
    if not cfg['bayer']:
        if noise:
            e = rng.poisson(np.clip(a * cfg['signal_e'], 0, None)) + rng.normal(0, cfg['read_e'], a.shape)
            a = e / cfg['signal_e']
        return a.astype(np.float32)
    H, W = a.shape
    ii, jj = np.indices((H, W))
    ch = np.where((ii % 2 == 0) & (jj % 2 == 0), 'R', np.where((ii % 2 == 1) & (jj % 2 == 1), 'B', 'G'))
    gain = np.where(ch == 'R', BAYER_GAIN['R'], np.where(ch == 'B', BAYER_GAIN['B'], BAYER_GAIN['G']))
    sig = a * cfg['signal_e'] * gain
    if noise:
        sig = rng.poisson(np.clip(sig, 0, None)) + rng.normal(0, cfg['read_e'], a.shape)
    raw = sig / (cfg['signal_e'] * gain)           # flat-fielded mosaic
    planes = []
    k_rb = np.array([[0.25, 0.5, 0.25], [0.5, 1, 0.5], [0.25, 0.5, 0.25]])
    k_g = np.array([[0, 0.25, 0], [0.25, 1, 0.25], [0, 0.25, 0]])
    for c, k in (('R', k_rb), ('G', k_g), ('B', k_rb)):
        m = (ch == c).astype(float)
        planes.append(ndimage.convolve(raw * m, k, mode='mirror') / np.maximum(ndimage.convolve(m, k, mode='mirror'), 1e-9))
    return ((planes[0] + 2 * planes[1] + planes[2]) / 4).astype(np.float32)


# ----------------------------------------------------------------------------- detection and measurement
def noise_sigma(level, cfg):
    """Expected 1-sigma noise of one demosaicked pixel, in units of the mean signal, at a local signal level."""
    lv = np.clip(level, 1e-3, None)
    var = lv / cfg['signal_e'] + (cfg['read_e'] / cfg['signal_e']) ** 2
    return np.sqrt(var * (0.6 if cfg['bayer'] else 1.0))   # demosaicking averages part of the noise (approx.)


def change_map(before, after, cfg, tmpl):
    """Relative change r = after/before - 1 and its weight (for diameter fitting), and the detection statistic Z:
    the maximum over crater sizes of a matched filter (the expected crater change pattern for the known Sun
    geometry) applied to the noise-normalised difference, each filter map scaled to unit robust spread."""
    bs = ndimage.gaussian_filter(before, 0.5)
    sig = np.sqrt(noise_sigma(bs, cfg) ** 2 + noise_sigma(after, cfg) ** 2)
    q = (after - bs) / sig
    q = q - np.median(q)
    zs = []
    for T in tmpl.filters:
        F = signal.fftconvolve(q, T[::-1, ::-1], mode='same')
        med = np.median(F); mad = np.median(np.abs(F - med)) * 1.4826 + 1e-12
        zs.append((F - med) / mad)
    r = after / np.clip(bs, 1e-3, None) - 1.0
    w = (np.clip(bs, 1e-3, None) / sig) ** 2
    return (r - np.median(r), w), np.max(zs, axis=0)


def peaks(Z, thr, min_sep=3):
    mx = ndimage.maximum_filter(Z, size=2 * min_sep + 1)
    l, s = np.where((Z == mx) & (Z > thr))
    return list(zip(l, s, Z[l, s]))


class Templates:
    """Noise-free model change maps on the camera grid for a grid of diameters, for diameter estimation.
    All templates share one window so that their fits are directly comparable."""
    def __init__(self, inc, az, cfg, gsd_src, rng, Dmax=20.0):
        self.Ds = np.exp(np.linspace(math.log(0.8), math.log(Dmax), 60))
        raw = []
        for D in self.Ds:
            ratio, h = render_ratio(D, gsd_src, inc, az, cfg)
            pad = int(3 * cfg['gsd_dst'] / gsd_src) + 4
            base = np.ones((2 * (h + pad) + 1,) * 2, np.float32)
            base[pad:pad + 2 * h + 1, pad:pad + 2 * h + 1] = ratio
            m = degrade(base, gsd_src, cfg, rng, noise=False)
            raw.append(m / np.median(np.concatenate([m[0], m[-1], m[:, 0], m[:, -1]])) - 1.0)
        W = max(m.shape[0] for m in raw) | 1
        self.W = W
        self.t = []
        for m in raw:
            T = np.zeros((W, W), np.float32)
            o = (W - m.shape[0]) // 2
            T[o:o + m.shape[0], o:o + m.shape[1]] = m
            self.t.append(T)
        # matched filters for detection: every third template, cropped to its own support, unit norm
        self.filters = []
        for m in raw[::3]:
            self.filters.append((m / (np.linalg.norm(m) + 1e-12)).astype(np.float32))

    def fit(self, rw, l, s):
        r, w = rw
        h = self.W // 2
        best = None
        for dl in (-1, 0, 1):
            for dd in (-1, 0, 1):
                L0, S0 = l + dl - h, s + dd - h
                if L0 < 0 or S0 < 0 or L0 + self.W > r.shape[0] or S0 + self.W > r.shape[1]:
                    continue
                o = r[L0:L0 + self.W, S0:S0 + self.W]; ww = w[L0:L0 + self.W, S0:S0 + self.W]
                chis = []
                for T in self.t:
                    mm = (ww * T * T).sum()
                    a = min(max((ww * o * T).sum() / mm, 1 / 3), 3.0) if mm > 0 else 1.0
                    chis.append((ww * (o - a * T) ** 2).sum())
                chis = np.array(chis)
                if best is None or chis.min() < best[0].min():
                    best = (chis,)
        if best is None:
            return None
        chis = best[0]; i = int(np.argmin(chis)); x = np.log(self.Ds)
        if 0 < i < len(chis) - 1:
            den = chis[i - 1] - 2 * chis[i] + chis[i + 1]
            if den > 0:
                return float(math.exp(x[i] + 0.5 * (chis[i - 1] - chis[i + 1]) / den * (x[1] - x[0])))
        return float(self.Ds[i])


def calibrate_threshold(before_src, after_src, gsd_src, cfg, rng, tmpl, n=6):
    """Null runs (no injection): the threshold is set so that local maxima of the change statistic exceed it
    at the target false-alarm density (cfg['fa_per_km2'], candidates per km2)."""
    allpk, area, m = [], 0.0, 10
    for _ in range(n):
        b = degrade(before_src, gsd_src, cfg, rng); a = degrade(after_src, gsd_src, cfg, rng)
        _, Z = change_map(b, a, cfg, tmpl)
        Zc = Z[m:-m, m:-m]
        allpk += [p[2] for p in peaks(Zc, -np.inf)]
        area += Zc.size * cfg['gsd_dst'] ** 2 / 1e6
    allpk = np.sort(np.array(allpk))[::-1]
    target = cfg['fa_per_km2'] * area          # expected number of null peaks above the threshold in this area
    if target >= 5:
        return float(allpk[int(target)]), area
    # fewer than 5 null peaks expected above the target: extrapolate an exponential tail fitted to the top peaks
    top = allpk[:min(200, len(allpk))]
    n_above = np.arange(1, len(top) + 1)
    slope, icpt = np.polyfit(top, np.log(n_above), 1)          # ln N(>T) = icpt + slope*T, slope < 0
    thr = (math.log(target) - icpt) / slope
    return float(max(thr, top[0])), area


# ----------------------------------------------------------------------------- statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fit_confirmation(D, hit, gsd, fix_width=None):
    """MLE of c(D) = cmax * Phi((ln D - ln(k gsd)) / w) for binary outcomes."""
    D = np.asarray(D, float); hit = np.asarray(hit, float)
    def nll(p):
        cmax = 1 / (1 + math.exp(-p[0])); k = math.exp(p[1]); w = fix_width or math.exp(p[2])
        c = np.clip(cmax * stats.norm.cdf((np.log(D) - math.log(k * gsd)) / w), 1e-9, 1 - 1e-9)
        return -(hit * np.log(c) + (1 - hit) * np.log(1 - c)).sum()
    x0 = [1.7, math.log(3.5), math.log(0.2)]
    r = optimize.minimize(nll, x0[:2] if fix_width else x0, method='Nelder-Mead', options=dict(xatol=1e-4, fatol=1e-6, maxiter=4000))
    p = r.x
    return dict(c_max=float(1 / (1 + math.exp(-p[0]))), k_pixels=float(math.exp(p[1])),
                width_lnD=float(fix_width or math.exp(p[2])), n=int(len(D)), converged=bool(r.success))


def bootstrap_fit(D, hit, gsd, nb=200, seed=1):
    rng = np.random.default_rng(seed); D = np.asarray(D); hit = np.asarray(hit)
    out = []
    for _ in range(nb):
        i = rng.integers(0, len(D), len(D))
        out.append(fit_confirmation(D[i], hit[i], gsd))
    keys = ('c_max', 'k_pixels', 'width_lnD')
    return {k: [float(np.percentile([o[k] for o in out], 16)), float(np.percentile([o[k] for o in out], 84))] for k in keys}


def fit_diameter_error(Dpx, err):
    """sd(ln D_est/D_true) = hypot(a, b / D_px), fitted to binned robust spreads."""
    Dpx = np.asarray(Dpx); err = np.asarray(err)
    edges = np.quantile(Dpx, np.linspace(0, 1, min(8, max(2, len(Dpx) // 15)) + 1))
    xs, ys, ns = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (Dpx >= lo) & (Dpx <= hi)
        if m.sum() >= 5:
            e = err[m]
            xs.append(np.median(Dpx[m])); ys.append(1.4826 * np.median(np.abs(e - np.median(e)))); ns.append(int(m.sum()))
    if len(xs) < 2:
        return dict(a=None, b=None, bins=list(zip(xs, ys, ns)))
    f = lambda x, a, b: np.hypot(a, b / x)
    (a, b), _ = optimize.curve_fit(f, np.array(xs), np.array(ys), p0=[0.03, 0.35], bounds=([0, 0], [1, 5]))
    return dict(a=float(a), b=float(b), bias_median=float(np.median(err)),
                bins=[dict(D_px=float(x), sd=float(y), n=n) for x, y, n in zip(xs, ys, ns)])


# ----------------------------------------------------------------------------- runs
def run_injection(before_src, after_src, gsd_src, inc, az, cfg, out, D_grid, n_per_D, seed=0, label=''):
    rng = np.random.default_rng(seed)
    if after_src is None:
        after_src = before_src
    else:
        after_src, shift = coregister(before_src, after_src)
    tmpl = Templates(inc, az, cfg, gsd_src, rng)
    thr, area = calibrate_threshold(before_src, after_src, gsd_src, cfg, rng, tmpl)
    scale = cfg['gsd_dst'] / gsd_src
    H, W = before_src.shape
    rows = []
    per_img = 9
    margin_m = 3 * max(D_grid) + 30
    for D in D_grid:
        done = 0
        while done < n_per_D:
            k = min(per_img, n_per_D - done)
            # place craters on a jittered grid, well separated
            g = int(math.ceil(math.sqrt(per_img)))
            cl = np.linspace(margin_m / gsd_src, H - margin_m / gsd_src, g + 2)[1:-1]
            cs = np.linspace(margin_m / gsd_src, W - margin_m / gsd_src, g + 2)[1:-1]
            cen = [(l + rng.uniform(-3, 3), s + rng.uniform(-3, 3)) for l in cl for s in cs]
            cen = [cen[i] for i in rng.permutation(len(cen))[:k]]
            aft = inject(after_src, cen, [D] * k, gsd_src, inc, az, cfg)
            b = degrade(before_src, gsd_src, cfg, rng); a = degrade(aft, gsd_src, cfg, rng)
            d, Z = change_map(b, a, cfg, tmpl)
            pk = peaks(Z, thr)
            for (l, s) in cen:
                ld, sd = l / scale, s / scale
                Dpx = D / cfg['gsd_dst']
                near = [p for p in pk if math.hypot(p[0] - ld, p[1] - sd) <= max(2.0, Dpx)]
                hit = len(near) > 0
                Dest = None
                if hit:
                    p = max(near, key=lambda q: q[2])
                    Dest = tmpl.fit(d, int(p[0]), int(p[1]))
                rows.append(dict(D=D, D_px=Dpx, hit=int(hit), D_est=Dest))
            done += k
        n = [r for r in rows if r['D'] == D]
        print(f'{label} D={D:5.2f} m ({D / cfg["gsd_dst"]:4.1f} px): found {sum(r["hit"] for r in n)}/{len(n)}', flush=True)
    return summarize(rows, cfg, dict(mode='inject', label=label, gsd_src=gsd_src, inc=inc, az=az,
                                    threshold=thr, null_area_km2=area, fa_per_km2=cfg['fa_per_km2'],
                                    after_image='separate (coregistered)' if after_src is not before_src else 'same as before'), out)


def summarize(rows, cfg, meta, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    D = np.array([r['D'] for r in rows]); hit = np.array([r['hit'] for r in rows])
    res = dict(meta=meta, config={k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.items()}, n=len(rows))
    res['by_diameter'] = []
    for d in sorted(set(D.tolist())):
        m = D == d
        k, n = int(hit[m].sum()), int(m.sum())
        res['by_diameter'].append(dict(D=d, D_px=d / cfg['gsd_dst'], found=k, n=n, p=k / n, wilson95=wilson(k, n)))
    if hit.any() and (~hit.astype(bool)).any():
        res['confirmation_fit'] = fit_confirmation(D, hit, cfg['gsd_dst'])
        res['confirmation_fit_width_fixed_0.15'] = fit_confirmation(D, hit, cfg['gsd_dst'], fix_width=0.15)
        res['confirmation_fit_1sigma'] = bootstrap_fit(D, hit, cfg['gsd_dst'], nb=100)
    est = [(r['D_px'], math.log(r['D_est'] / r['D'])) for r in rows if r.get('D_est')]
    if len(est) >= 10:
        res['diameter_error'] = fit_diameter_error([e[0] for e in est], [e[1] for e in est])
    res['joint_model_placeholders'] = JM
    json.dump(res, open(out / 'results.json', 'w'), indent=1)
    with open(out / 'trials.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['D', 'D_px', 'hit', 'D_est']); w.writeheader(); w.writerows(rows)
    plot(res, rows, out)
    print('wrote', out / 'results.json')
    return res


def plot(res, rows, out):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    bd = res['by_diameter']; gsd = res['config']['gsd_dst']
    x = np.array([b['D'] for b in bd]); p = np.array([b['p'] for b in bd])
    lo = np.array([b['wilson95'][0] for b in bd]); hi = np.array([b['wilson95'][1] for b in bd])
    ax[0].errorbar(x, p, yerr=[np.clip(p - lo, 0, None), np.clip(hi - p, 0, None)], fmt='o', color='C0', label='measured (95%)')
    xx = np.exp(np.linspace(math.log(x.min() * 0.8), math.log(x.max() * 1.2), 200))
    ax[0].plot(xx, JM['CMAX'] * stats.norm.cdf((np.log(xx) - math.log(JM['k'] * JM['GSD'])) / JM['KW']), 'k--', label='joint-model placeholder')
    if 'confirmation_fit' in res:
        f = res['confirmation_fit']
        ax[0].plot(xx, f['c_max'] * stats.norm.cdf((np.log(xx) - math.log(f['k_pixels'] * gsd)) / f['width_lnD']), 'C0-',
                   label=f"fit: c_max {f['c_max']:.2f}, k {f['k_pixels']:.2f} px, w {f['width_lnD']:.2f}")
    ax[0].set_xscale('log'); ax[0].set_xlabel('crater diameter [m]'); ax[0].set_ylabel('fraction found'); ax[0].set_ylim(0, 1.02)
    ax[0].legend(fontsize=7); ax[0].set_title('Completeness')
    est = [(r['D_px'], math.log(r['D_est'] / r['D'])) for r in rows if r.get('D_est')]
    if est:
        e = np.array(est)
        ax[1].plot(e[:, 0], e[:, 1], '.', alpha=0.3, color='C1')
        xp = np.linspace(max(0.8, e[:, 0].min()), e[:, 0].max(), 100)
        ax[1].plot(xp, np.hypot(JM['a'], JM['b'] / xp), 'k--', label='placeholder ±1σ'); ax[1].plot(xp, -np.hypot(JM['a'], JM['b'] / xp), 'k--')
        if res.get('diameter_error', {}).get('a') is not None:
            de = res['diameter_error']
            ax[1].plot(xp, np.hypot(de['a'], de['b'] / xp), 'C1-', label=f"fit ±1σ: a {de['a']:.3f}, b {de['b']:.2f} px")
            ax[1].plot(xp, -np.hypot(de['a'], de['b'] / xp), 'C1-')
        ax[1].legend(fontsize=7)
    ax[1].set_xlabel('true diameter [camera pixels]'); ax[1].set_ylabel('ln(D measured / D true)'); ax[1].set_title('Diameter error')
    fig.tight_layout(); fig.savefig(Path(out) / 'crater_test.png', dpi=130); plt.close(fig)


# ----------------------------------------------------------------------------- real craters
def run_real(listfile, cfg, out, seed=0):
    """Real new craters from the LROC new-crater catalogue: before/after NAC chips centred on each crater."""
    rng = np.random.default_rng(seed)
    rows = []
    base = Path(listfile).parent
    for r in csv.DictReader(open(listfile)):
        gsd = float(r['gsd_m']); D = float(r['diam_m'])
        size = int(float(r.get('chip_m') or 600) / gsd)
        b = crop(read_image(base / r['before_file']), (int(float(r['before_line'])), int(float(r['before_sample']))), size)
        a = crop(read_image(base / r['after_file']), (int(float(r['after_line'])), int(float(r['after_sample']))), size)
        n = min(b.shape[0], a.shape[0]), min(b.shape[1], a.shape[1])
        b, a = b[:n[0], :n[1]], a[:n[0], :n[1]]
        a, _ = coregister(b, a)
        a = a * np.median(b) / np.median(a)
        inc, az = float(r.get('inc') or 45), float(r.get('az') or 90)
        tmpl = Templates(inc, az, cfg, gsd, rng)
        thr, _ = calibrate_threshold(b, b, gsd, cfg, rng, tmpl, n=3)    # noise-only null for this chip
        hits = 0
        for _ in range(int(r.get('repeats') or 5)):
            bd = degrade(b, gsd, cfg, rng); ad = degrade(a, gsd, cfg, rng)
            d, Z = change_map(bd, ad, cfg, tmpl)
            c = (Z.shape[0] // 2, Z.shape[1] // 2)
            Dpx = D / cfg['gsd_dst']
            near = [p for p in peaks(Z, thr) if math.hypot(p[0] - c[0], p[1] - c[1]) <= max(3.0, 1.5 * Dpx)]
            Dest = tmpl.fit(d, int(near[0][0]), int(near[0][1])) if near else None
            rows.append(dict(D=D, D_px=Dpx, hit=int(bool(near)), D_est=Dest))
            hits += bool(near)
        print(f"{r.get('crater_id', '?')}: D={D} m found {hits}x", flush=True)
    return summarize(rows, cfg, dict(mode='real', list=str(listfile)), out)


# ----------------------------------------------------------------------------- human review
def review_export(before_src, after_src, gsd_src, inc, az, cfg, out, D_range=(1.5, 8.0), n=120, seed=0):
    from PIL import Image
    rng = np.random.default_rng(seed)
    after_src = before_src if after_src is None else coregister(before_src, after_src)[0]
    out = Path(out) / 'review'; out.mkdir(parents=True, exist_ok=True)
    chip_m = 60.0
    hs = int(chip_m / 2 / gsd_src)
    key = []
    for i in range(n):
        l = rng.integers(hs + 20, before_src.shape[0] - hs - 20); s = rng.integers(hs + 20, before_src.shape[1] - hs - 20)
        has = rng.random() < 0.5
        D = float(math.exp(rng.uniform(math.log(D_range[0]), math.log(D_range[1])))) if has else 0.0
        bsrc = before_src[l - hs:l + hs, s - hs:s + hs]; asrc = after_src[l - hs:l + hs, s - hs:s + hs]
        off = (hs + rng.uniform(-0.25, 0.25) * hs, hs + rng.uniform(-0.25, 0.25) * hs)
        if has:
            asrc = inject(asrc, [off], [D], gsd_src, inc, az, cfg)
        bd = degrade(bsrc, gsd_src, cfg, rng); ad = degrade(asrc, gsd_src, cfg, rng)
        pair = np.concatenate([bd, np.full((bd.shape[0], 3), np.nan), ad], axis=1)
        lo, hi = np.nanpercentile(pair, [1, 99])
        img = np.nan_to_num((pair - lo) / (hi - lo), nan=1.0).clip(0, 1)
        img = np.kron(img, np.ones((6, 6)))
        cid = f'chip_{i:03d}'
        Image.fromarray((img * 255).astype(np.uint8)).save(out / f'{cid}.png')
        key.append(dict(chip_id=cid, crater=int(has), D=D, D_px=D / cfg['gsd_dst'],
                        line_px=(off[0] * gsd_src / cfg['gsd_dst']) if has else '', sample_px=(off[1] * gsd_src / cfg['gsd_dst']) if has else ''))
    with open(out.parent / 'review_key_DO_NOT_SHOW.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(key[0])); w.writeheader(); w.writerows(key)
    with open(out / 'my_answers.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['chip_id', 'new_crater_yes_no', 'diameter_px_optional'])
        for k in key:
            w.writerow([k['chip_id'], '', ''])
    print(f'wrote {n} chips to {out}; reviewers fill in my_answers.csv (left = before, right = after, 1 px = {cfg["gsd_dst"]} m)')


def review_score(out, answers, cfg):
    key = {r['chip_id']: r for r in csv.DictReader(open(Path(out) / 'review_key_DO_NOT_SHOW.csv'))}
    rows, fp, nnull = [], 0, 0
    for r in csv.DictReader(open(answers)):
        k = key[r['chip_id']]
        yes = r['new_crater_yes_no'].strip().lower() in ('y', 'yes', '1', 'true')
        if k['crater'] == '1':
            dpx = r.get('diameter_px_optional', '').strip()
            Dest = float(dpx) * cfg['gsd_dst'] if (yes and dpx) else None
            rows.append(dict(D=round(float(k['D']), 1), D_px=float(k['D_px']), hit=int(yes), D_est=Dest))
        else:
            nnull += 1; fp += yes
    res = summarize(rows, cfg, dict(mode='human review', false_positive_chips=fp, null_chips=nnull,
                                    false_positive_rate=fp / max(nnull, 1)), Path(out) / 'review_scored')
    return res


def pooled_summary(runs, cfg):
    rows = []
    for r in runs:
        rows += [dict(D=float(x['D']), D_px=float(x['D_px']), hit=int(x['hit']), D_est=float(x['D_est']) if x['D_est'] not in ('', 'None') else None)
                 for x in csv.DictReader(open(Path(r) / 'trials.csv'))]
    return summarize(rows, cfg, dict(mode='pooled', runs=[str(r) for r in runs]), DATA)


# ----------------------------------------------------------------------------- self-test on synthetic terrain
def synthetic_terrain(n=1400, gsd=0.5, seed=3, inc=55, az=90, cfg=DEFAULTS):
    """Fractal topography plus an old crater population, shaded with the same photometry."""
    rng = np.random.default_rng(seed)
    k = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    spec = (k + 1e-6) ** (-1.1) * np.exp(2j * np.pi * rng.random((n, n)))
    z = np.real(np.fft.ifft2(spec)); z = z / z.std() * 1.5                  # metres
    yy, xx = np.indices((n, n)) * gsd
    for _ in range(400):                                                     # degraded old craters
        D = 2.0 * (1 - rng.random()) ** (-1 / 2.0); D = min(D, 60)
        c = rng.random(2) * n * gsd
        rr = np.hypot(yy - c[0], xx - c[1]) / (D / 2)
        m = rr < 3
        z[m] += crater_height(rr[m], depth=0.08, rim=0.01) * D
    img = shade(z, gsd, inc, az, cfg['lunar_lambert_L'])
    alb = 1 + 0.08 * ndimage.gaussian_filter(rng.normal(size=(n, n)), 6) / 0.02
    return (img * np.clip(alb, 0.6, 1.4) + 0.02).astype(np.float32)


def selftest(out):
    cfg = dict(DEFAULTS)
    inc, az, gsd = 55.0, 90.0, 0.5
    print('synthetic terrain ...', flush=True)
    img = synthetic_terrain(inc=inc, az=az, cfg=cfg, gsd=gsd)
    res = run_injection(img, None, gsd, inc, az, cfg, out, D_grid=[1.8, 2.2, 2.5, 2.8, 3.1, 3.4, 3.8, 4.4, 5.5, 8.0], n_per_D=27, label='selftest')
    res['meta']['note'] = 'synthetic terrain: checks the code path only; not evidence about real LROC scenes'
    json.dump(res, open(Path(out) / 'results.json', 'w'), indent=1)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['selftest', 'inject', 'real', 'review-export', 'review-score', 'summary'])
    ap.add_argument('--before'); ap.add_argument('--after'); ap.add_argument('--gsd', type=float, help='source pixel scale [m]')
    ap.add_argument('--inc', type=float, default=45, help='Sun incidence angle from vertical [deg]')
    ap.add_argument('--az', type=float, default=90, help='Sun azimuth from image up (-line), clockwise [deg]')
    ap.add_argument('--chip', type=int, nargs=2, metavar=('LINE', 'SAMPLE'), help='centre of the test window in the source image')
    ap.add_argument('--chip-m', type=float, default=1500, help='test window size [m]')
    ap.add_argument('--D', type=float, nargs='+', default=[1.8, 2.2, 2.5, 2.8, 3.1, 3.4, 3.8, 4.4, 5.5, 8.0], help='diameters to inject [m]')
    ap.add_argument('--n', type=int, default=45, help='injections per diameter')
    ap.add_argument('--list'); ap.add_argument('--answers'); ap.add_argument('--runs', nargs='+')
    ap.add_argument('--out', default='run'); ap.add_argument('--seed', type=int, default=0)
    for k in ('signal_e', 'read_e', 'psf_px', 'halo_amp', 'halo_extent', 'depth', 'rim', 'fa_per_km2', 'gsd_dst'):
        ap.add_argument('--' + k.replace('_', '-'), type=float, default=DEFAULTS[k])
    ap.add_argument('--no-bayer', action='store_true')
    A = ap.parse_args()
    cfg = dict(DEFAULTS)
    for k in ('signal_e', 'read_e', 'psf_px', 'halo_amp', 'halo_extent', 'depth', 'rim', 'fa_per_km2', 'gsd_dst'):
        cfg[k] = getattr(A, k)
    cfg['bayer'] = not A.no_bayer
    if A.cmd == 'selftest':
        selftest(A.out)
    elif A.cmd in ('inject', 'review-export'):
        size = int(A.chip_m / A.gsd)
        b = crop(read_image(A.before), tuple(A.chip) if A.chip else None, size if A.chip else None)
        a = crop(read_image(A.after), tuple(A.chip) if A.chip else None, size if A.chip else None) if A.after else None
        if a is not None:
            n = min(b.shape[0], a.shape[0]), min(b.shape[1], a.shape[1]); b, a = b[:n[0], :n[1]], a[:n[0], :n[1]]
            a = a * np.median(b) / np.median(a)
        if A.cmd == 'inject':
            run_injection(b, a, A.gsd, A.inc, A.az, cfg, A.out, A.D, A.n, A.seed, label=Path(A.before).stem)
        else:
            review_export(b, a, A.gsd, A.inc, A.az, cfg, A.out, seed=A.seed)
    elif A.cmd == 'real':
        run_real(A.list, cfg, A.out, A.seed)
    elif A.cmd == 'review-score':
        review_score(A.out, A.answers, cfg)
    elif A.cmd == 'summary':
        pooled_summary(A.runs, cfg)


if __name__ == '__main__':
    main()
