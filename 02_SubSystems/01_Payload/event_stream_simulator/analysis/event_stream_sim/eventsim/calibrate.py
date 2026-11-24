"""Flash lattices on flat per-cell backgrounds: energy-correction training (S11 style) and detection grids.

A lattice puts one flash in the centre of every cell (cell x cell px) of a crop, each cell with its own flat
background, and restricts trigger groups to each cell's central 4 x 4 patch (as S10's simulated patch) or to the
cell interior. Flashes are static (S10) and start at 0.4 s - U(0, 0.15) s; runs last 4.4 s.
Energy correction: quadratic regression of ln(E_true / E_raw) on [ln E_raw, ln active duration, peak decoded
level, pixels with events, ln background estimate] (S11), trained on detected flashes of this simulator with
E_L log-uniform 1e4-3e6 J, tau log-uniform 0.03-1 s, range and earthshine drawn jointly from the S13 observing
samples; held-out tests: new draws, two-component and power-law profiles.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
from . import profiles, scenes, sim, trigger as trg
from .radiometry import dark_e_s

OBS = Path(__file__).resolve().parents[3] / 'data' / 'observed_background_samples.npz'
ES_FULL = 18519.7


def lattice(P, flashes_cells, bg_cells, ncx, ncy, cell=8, seed=1, groups='patch', duration=4.4, log=print,
            trigger_mode='compute', dt=5e-4, calib=None, vignette=1.0, threshold_model='fixed'):
    """vignette: field gain applied to the point sources (and known to the reconstruction), for the E05 check."""
    """flashes_cells: list (len ncx*ncy) of dicts E_J, tau_s, kind, range_km (or None for an empty cell)."""
    w, h = ncx * cell, ncy * cell
    S, O, E = P['sensor'], P['optics'], P['env']
    dark = dark_e_s(S['dark.current_fA'])
    photo = np.zeros((h, w)); rng_map = np.full((h, w), 3750.0)
    rng = np.random.default_rng(seed)
    fl = []; allow2 = np.zeros((h, w), bool); allow3 = np.zeros((h, w), bool)
    for k in range(ncx * ncy):
        cx, cy = k % ncx, k // ncx
        x0, y0 = cx * cell, cy * cell
        photo[y0:y0 + cell, x0:x0 + cell] = max(bg_cells[k] - dark, 0.0)
        f = flashes_cells[k]
        px, py = x0 + (cell - 4) // 2, y0 + (cell - 4) // 2
        if groups == 'patch':
            allow2[py:py + 3, px:px + 3] = True; allow3[py:py + 2, px:px + 2] = True
        else:
            allow2[y0 + 1:y0 + cell - 2, x0 + 1:x0 + cell - 2] = True; allow3[y0 + 1:y0 + cell - 3, x0 + 1:x0 + cell - 3] = True
        if f is None:
            continue
        rng_map[y0:y0 + cell, x0:x0 + cell] = f.get('range_km', 3750.0)
        fl.append(dict(t_on=0.4 - rng.uniform(0, 0.15), x=px + 2 + rng.uniform(-0.5, 0.5), y=py + 2 + rng.uniform(-0.5, 0.5),
                       E_J=f['E_J'], tau_s=f['tau_s'], kind=f.get('kind', 'exp'), static=True, range_km=f.get('range_km', 3750.0), cell=k))
    sc = scenes.FlatScene(w, h, photo, rng_map, E, label='lattice')
    sc.vignette_map[:] = vignette
    s = sim.Simulation(sc, S, O, E, duration, dt=dt, seed=seed, flashes=fl, particles=None,
                       trigger_cfg=dict(mode=trigger_mode, allow2=allow2, allow3=allow3, threshold_model=threshold_model), log=log)
    s.run(); s.detect(calib=calib)
    return s


def draw_flashes(n, rng, kinds=('exp',)):
    with np.load(OBS) as z:
        obs = dict(range_km=z['range_km'].astype(np.float64), es_rel=z['es_rel'].astype(np.float64))
    j = rng.integers(0, len(obs['range_km']), n)
    out = []
    for i in range(n):
        out.append(dict(E_J=float(math.exp(rng.uniform(math.log(1e4), math.log(3e6)))),
                        tau_s=float(math.exp(rng.uniform(math.log(0.03), math.log(1.0)))),
                        kind=kinds[i % len(kinds)], range_km=float(obs['range_km'][j[i]]), es=float(obs['es_rel'][j[i]] * ES_FULL)))
    return out


def rows_from(s):
    rows = []
    sm = s.summary()
    found = {}
    for d in s.detections:
        if d['label'] == 'flash' and d['match'] not in found and d.get('energy') and d['energy']['e_raw_J'] > 0:
            found[d['match']] = d
    for i, f in enumerate(s.flashes):
        d = found.get(i)
        if d is None:
            continue
        m = d['energy']
        rows.append(dict(lnE=math.log(f['E_J']), feat=trg.correction_features(m).tolist(), base=trg.base_features(m).tolist(),
                         tau=f['tau_s'], bg=float(np.mean(s.bg_chunks[0][int(f['y']), int(f['x'])])), kind=f['kind'],
                         censored=bool(m.get('censored'))))
    return rows, sm


def simulate_set(P, flashes, ncx=32, ncy=18, cell=10, seed=0, log=print, threshold_model='fixed'):
    rows = []; ndet = 0; ntot = 0
    per = ncx * ncy
    dark = dark_e_s(P['sensor']['dark.current_fA'])
    for b in range(0, len(flashes), per):
        part = flashes[b:b + per]
        cells = part + [None] * (per - len(part))
        bgs = [dark + (f['es'] if f else 0.0) for f in cells]
        s = lattice(P, cells, bgs, ncx, ncy, cell=cell, seed=seed + b, groups='cell', log=log, threshold_model=threshold_model)
        r, sm = rows_from(s)
        rows += r; ndet += sm['n_detected']; ntot += sm['n_flashes']
        log(f'    batch {b // per}: detected {sm["n_detected"]}/{sm["n_flashes"]}, false {sm["n_false"]}')
    return rows, ndet, ntot


def stats(res):
    res = np.asarray(res)
    return dict(n=int(res.size), bias=float(res.mean()) if res.size else None, sd=float(res.std()) if res.size else None,
                median=float(np.median(res)) if res.size else None,
                rms=float(np.sqrt(np.mean(res ** 2))) if res.size else None)


def fit(train):
    """Least-squares quadratic correction on complete (uncensored) records; returns coef and feature range."""
    train = [r for r in train if not r.get('censored')]
    X = np.array([r['feat'] for r in train]); y = np.array([r['lnE'] for r in train]) - X[:, 1]
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    B = np.array([r['base'] for r in train])
    return coef, dict(min=B.min(0).tolist(), max=B.max(0).tolist()), y, len(train)


def evaluate_rows(rows, calib):
    """Raw and corrected ln errors (correction evaluated with features clipped to the training range)."""
    rows = [r for r in rows if not r.get('censored')]
    lnE = np.array([r['lnE'] for r in rows]); B = np.array([r['base'] for r in rows])
    lo, hi = np.asarray(calib['feature_range']['min']), np.asarray(calib['feature_range']['max'])
    coef = np.asarray(calib['coef'])
    corr_ln = np.array([b[0] + trg._quad(np.clip(b, lo, hi)) @ coef for b in B]) if len(B) else np.zeros(0)
    out = np.array([bool(np.any(b < lo) or np.any(b > hi)) for b in B]) if len(B) else np.zeros(0, bool)
    return B[:, 0] - lnE if len(B) else np.zeros(0), corr_ln - lnE, out


def run(sensor, n=2400, seed=20261112, optics='optics_16mm_f1', sets=(), out=None, log=print, tests=None, tag=None,
        threshold_model='fixed'):
    P = dict(sensor=profiles.load(sensor), optics=profiles.load(optics), env=profiles.load('environment'))
    profiles.apply_overrides(P, sets)
    rng = np.random.default_rng(seed)
    log(f'calibration for {sensor}: training {n} flashes')
    train, nd, nt = simulate_set(P, draw_flashes(n, rng), seed=seed, log=log, threshold_model=threshold_model)
    coef, frange, y, ntr = fit(train)
    res = {'sensor': sensor, 'overrides': list(sets or []), 'threshold_model': threshold_model, 'n_train_flashes': n, 'n_train_detected': len(train),
           'n_train_used': ntr, 'coef': coef.tolist(), 'feature_range': frange,
           'features': 'const, ln E_raw, ln active, peak, npix, ln bg_est, and all pairwise products (S11); '
                       'applied with the five base features clipped to feature_range (4 Nov 2026 review)',
           'train_raw': stats(-y), 'tests': {}}

    def evaluate(rows):
        raw, corr, outr = evaluate_rows(rows, res)
        rows = [r for r in rows if not r.get('censored')]
        tau = np.array([r['tau'] for r in rows]); bg = np.array([r['bg'] for r in rows])
        cond = {}
        for tl, tm in (('tau_le_0.3', tau <= 0.3), ('tau_gt_0.3', tau > 0.3)):
            for bl, bm in (('bg_le_1e4', bg <= 1e4), ('bg_gt_1e4', bg > 1e4)):
                sel = tm & bm
                cond[f'{tl}|{bl}'] = stats(corr[sel]) if sel.sum() > 10 else None
        E = np.exp(np.array([r['lnE'] for r in rows]))
        bands = {}
        for lo, hi in ((1e4, 1e5), (1e5, 1e6), (1e6, 3.01e6)):
            sel = (E >= lo) & (E < hi)
            bands[f'{lo:.0e}-{hi:.0e}'] = dict(raw=stats(raw[sel]), corrected=stats(corr[sel])) if sel.sum() > 5 else None
        return dict(raw=stats(raw), corrected=stats(corr), by_condition=cond, by_energy=bands,
                    outside_training_range_fraction=float(outr.mean()) if outr.size else None)
    tests = tests or (('a_same_family', ('exp',), 700), ('b_double_profile', ('double',), 450), ('b_power_profile', ('power',), 450))
    for name, kinds, k in tests:
        log(f'  test {name}')
        rows, nd2, nt2 = simulate_set(P, draw_flashes(k, rng, kinds), seed=seed + 1000 + k, log=log,
                                      threshold_model=threshold_model)
        res['tests'][name] = evaluate(rows); res['tests'][name]['detected'] = [nd2, nt2]
        log(f"    corrected bias {res['tests'][name]['corrected']['bias']:.3f} sd {res['tests'][name]['corrected']['sd']:.3f}")
    if out:
        Path(out, f'energy_calibration_{tag or sensor}.json').write_text(json.dumps(res, indent=1))
    return res
