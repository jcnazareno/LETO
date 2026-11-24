"""Particle hits from a measured LET spectrum (CRaTER, 4 Nov 2026 update).

particles.model = 'let_spectrum' (default since 4 Nov 2026) or 'parametric' (S10: lognormal MIP deposits plus a
log-uniform heavy share on 1-5 px tracks).

let_spectrum: each hit draws a LET from the epoch's tabulated D2 histogram (particles.let_epoch = 'solar_min' or
'solar_max'; log-uniform within a bin), a cos-weighted isotropic direction on the sensor plane and a uniform entry
point. The straight track crosses a sensitive layer of particles.sensitive_depth_um under the pixel pitch; each
crossed pixel column receives LET x chord / particles.e_per_pair_eV, times a lognormal thin-layer straggling
factor (particles.straggling_sigma_ln). No diffusion. Derivation: derive_crater_particles.py.

Entering tracks (11 Nov 2026): sample_hits places entry points inside the crop. sample_entering adds the tracks that
enter from a ring around the crop (bounded by the sensor edges where known), drawn from a separate random stream so
that the in-crop hits stay identical; only the pixels inside the crop are kept.
"""
from __future__ import annotations
import math
import numpy as np


def _chords(x0, y0, phi, horiz_px, depth_um, cos_t):
    """3D chord (um) through each pixel column crossed by a track entering at (x0, y0) px."""
    if horiz_px < 1e-6:
        return [(int(math.floor(x0)), int(math.floor(y0)))], np.array([depth_um / cos_t])
    dx, dy = math.cos(phi), math.sin(phi)
    ts = [0.0, horiz_px]
    for d0, dd in ((x0, dx), (y0, dy)):
        if abs(dd) > 1e-12:
            lo, hi = sorted((d0, d0 + dd * horiz_px))
            for b in range(int(math.floor(lo)) + 1, int(math.ceil(hi))):
                ts.append((b - d0) / dd)
    ts = np.unique(np.clip(ts, 0, horiz_px))
    pix, ch = [], []
    for a, b in zip(ts[:-1], ts[1:]):
        if b - a < 1e-9:
            continue
        m = 0.5 * (a + b)
        pix.append((int(math.floor(x0 + dx * m)), int(math.floor(y0 + dy * m))))
        ch.append((b - a) / horiz_px * depth_um / cos_t)
    return pix, np.array(ch)


def sample_hits(rng, n, duration, w, h, env, pitch_um, max_px=400):
    epoch = env['particles.let_epoch']
    tab = env[f'particles.let_hist_{epoch}']
    edges = np.asarray(tab['edges_keV_um'], float); cnt = np.asarray(tab['counts'], float)
    p = cnt / cnt.sum()
    depth = env['particles.sensitive_depth_um']; eps = env['particles.e_per_pair_eV']
    sig = env['particles.straggling_sigma_ln']
    hits = []
    for _ in range(n):
        t = rng.uniform(0.05, duration)
        k = rng.choice(len(p), p=p)
        let = math.exp(rng.uniform(math.log(edges[k]), math.log(edges[k + 1])))
        cos_t = math.sqrt(rng.random()); sin_t = math.sqrt(1 - cos_t * cos_t)
        phi = rng.uniform(0, 2 * math.pi)
        x0, y0 = rng.uniform(0, w), rng.uniform(0, h)
        horiz = min(depth * sin_t / max(cos_t, 1e-6) / pitch_um, max_px)
        pix, ch = _chords(x0, y0, phi, horiz, depth, cos_t)
        keep = [(xy, c) for xy, c in zip(pix, ch) if 0 <= xy[0] < w and 0 <= xy[1] < h]
        if not keep:
            continue
        dep = [float(let * 1e3 / eps * c * math.exp(rng.normal(0, sig))) for _, c in keep]
        hits.append(dict(id=len(hits), t=float(t), heavy=bool(max(dep) > 2e3), pixels=[xy for xy, _ in keep],
                         deposits_e=dep, length_px=len(keep), let_keV_um=float(let), cos_theta=float(cos_t)))
    return hits


def _dist_to_rect(x, y, w, h):
    dx = max(0.0 - x, 0.0, x - w); dy = max(0.0 - y, 0.0, y - h)
    return math.hypot(dx, dy)


def sample_entering(rng, rate_per_px_s, duration, w, h, env, pitch_um, bounds, start_id=0, max_px=400,
                    model='let_spectrum', param=None):
    """Hits whose entry point lies outside the w x h crop but whose track reaches it. bounds = (x_lo, x_hi, y_lo, y_hi)
    of allowed entry points in crop coordinates (sensor edges, or +-max track length). rate_per_px_s: hit rate per
    pixel area. model 'parametric' uses param = dict(fh, lo, hi, mip, mip_sig, L0, L1) (S10 straight tracks)."""
    x_lo, x_hi, y_lo, y_hi = bounds
    area = (x_hi - x_lo) * (y_hi - y_lo) - w * h
    if area <= 0:
        return []
    n = rng.poisson(rate_per_px_s * area * duration)
    hits = []
    if model == 'let_spectrum':
        epoch = env['particles.let_epoch']
        tab = env[f'particles.let_hist_{epoch}']
        edges = np.asarray(tab['edges_keV_um'], float); cnt = np.asarray(tab['counts'], float)
        pr = cnt / cnt.sum()
        depth = env['particles.sensitive_depth_um']; eps = env['particles.e_per_pair_eV']
        sig = env['particles.straggling_sigma_ln']
    done = 0
    while done < n:
        x0, y0 = rng.uniform(x_lo, x_hi), rng.uniform(y_lo, y_hi)
        if 0 <= x0 < w and 0 <= y0 < h:
            continue                                   # inside the crop: already covered by sample_hits
        done += 1
        t = rng.uniform(0.05, duration)
        if model == 'let_spectrum':
            k = rng.choice(len(pr), p=pr)
            let = math.exp(rng.uniform(math.log(edges[k]), math.log(edges[k + 1])))
            cos_t = math.sqrt(rng.random()); sin_t = math.sqrt(1 - cos_t * cos_t)
            phi = rng.uniform(0, 2 * math.pi)
            horiz = min(depth * sin_t / max(cos_t, 1e-6) / pitch_um, max_px)
            if horiz < _dist_to_rect(x0, y0, w, h):
                continue
            pix, ch = _chords(x0, y0, phi, horiz, depth, cos_t)
            keep = [(xy, c) for xy, c in zip(pix, ch) if 0 <= xy[0] < w and 0 <= xy[1] < h]
            if not keep:
                continue
            dep = [float(let * 1e3 / eps * c * math.exp(rng.normal(0, sig))) for _, c in keep]
            hits.append(dict(id=start_id + len(hits), t=float(t), heavy=bool(max(dep) > 2e3), pixels=[xy for xy, _ in keep],
                             deposits_e=dep, length_px=len(keep), let_keV_um=float(let), cos_theta=float(cos_t), entered=True))
        else:
            q = param
            heavy = rng.random() < q['fh']
            base = math.exp(rng.uniform(math.log(q['lo']), math.log(q['hi']))) if heavy else \
                q['mip'] * math.exp(rng.normal(0, q['mip_sig']))
            L = int(rng.integers(q['L0'], q['L1'] + 1)); ang = rng.uniform(0, 2 * math.pi)
            if L < _dist_to_rect(x0, y0, w, h):
                continue
            pix = []
            for s_ in range(L):
                xx = int(math.floor(x0 + s_ * math.cos(ang))); yy = int(math.floor(y0 + s_ * math.sin(ang)))
                if 0 <= xx < w and 0 <= yy < h and (xx, yy) not in pix:
                    pix.append((xx, yy))
            if not pix:
                continue
            dep = [float(base * math.exp(rng.normal(0, 0.3))) for _ in pix]
            hits.append(dict(id=start_id + len(hits), t=float(t), heavy=bool(heavy), pixels=pix, deposits_e=dep,
                             length_px=L, entered=True))
    return hits
