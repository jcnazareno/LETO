"""Validation of the event-stream simulator against S10, the background-activity model and S17.

  python validate.py s10        # V1: S10 Table 8 detections (nominal) and S16 Table 3 (m636) in S10 numerics
  python validate.py realistic  # V1b: the same lattices with the realistic IMX636 / IMX646 profiles
  python validate.py ba         # V2: background-activity rates, count statistics, hot-pixel masking
  python validate.py texture    # V3: moving measured texture at 1.3e4 e-/s vs the S17 model
  python validate.py substep    # V5: 0.5/0.25/0.1 ms steps, fixed vs adaptive sub-steps, faint and bright flashes
  python validate.py refractory # V6: refractory period with the correction retrained per setting
  python validate.py sensitivity # V7: high-pass (bias_hpf stand-in) and leak-drift background activity
  python validate.py field_gain # V8: off-axis field gain in the energy reconstruction
  python validate.py shadow     # V9: analytic ridge test of the cast-shadow horizon march
  python validate.py hpf_retrained     # V7b: high-pass corners with the correction retrained per setting
  python validate.py particle_timestep # V10: particle-pulse convergence at 0.5 / 0.1 ms
  python validate.py all
Writes data/validation_<name>.json and figures/validation_*.png.
"""
from __future__ import annotations
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eventsim import profiles, scenes, sim, calibrate, trigger as trg   # noqa: E402
from eventsim.radiometry import dark_e_s   # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / 'data'
FIG = ROOT / 'figures'
ER = json.loads((DATA / 'event_response.json').read_text())
S10_CASES = [(1e4, 0.03), (2e4, 0.03), (2e4, 0.1), (4e4, 0.1), (4e4, 0.3), (1e5, 0.3), (1e5, 1.0), (3e5, 1.0)]
M636_CASES = [(1e4, 0.03), (2e4, 0.1), (2e4, 0.3), (4e4, 0.3), (4e4, 1.0), (1e5, 1.0)]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den; h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def boot_se(x, nb=2000, seed=0):
    """Bootstrap standard error of the median."""
    x = np.asarray(x, float)
    if x.size < 5:
        return None
    rng = np.random.default_rng(seed)
    return float(np.std(np.median(x[rng.integers(0, x.size, (nb, x.size))], 1)))


def two_prop_p(k1, n1, k2, n2):
    """Two-sided Fisher exact test p-value."""
    from scipy.stats import fisher_exact
    return float(fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1])


def stored(case, I0, E, tau):
    for c in ER['cases']:
        if c['sensor'] == case and c['I0'] == I0 and c['E_L_J'] == E and c['tau_f_s'] == tau:
            return c
    return None


def P_(sensor, sets=()):
    P = dict(sensor=profiles.load(sensor), optics=profiles.load('optics_16mm_f1'), env=profiles.load('environment'))
    profiles.apply_overrides(P, sets)
    return P


def lattice_grid(sensor, s10_case, I0, cases, per_case=144, seed=5, ncx=24, ncy=16, groups='patch', mode='stored',
                 sets=(), dt=5e-4, calib=None, vignette=1.0, range_km=3750.0, counterfactual_no_gain=False):
    P = P_(sensor, sets)
    cells_per = ncx * ncy
    flashes = []
    for E, tau in cases:
        flashes += [dict(E_J=E, tau_s=tau, range_km=range_km, case=(E, tau))] * per_case
    rng = np.random.default_rng(seed)
    rng.shuffle(flashes)
    # energy statistics use COMPLETE records only (one declared cohort for raw and corrected errors); censored
    # records are counted and kept as a labelled partial-record diagnostic; onset errors use every measured record
    # (the onset lies inside the observed stream whether or not the record is complete)
    res = {c: dict(k=0, n=0, lnerr=[], lag=[], onset=[], lncorr=[], lnerr_cens=[], n_meas=0, n_cens=0,
                   lnraw_nogain=[], lncorr_nogain=[]) for c in cases}
    nfalse = 0; wall = 0.0
    for b in range(0, len(flashes), cells_per):
        part = flashes[b:b + cells_per]
        cells = part + [None] * (cells_per - len(part))
        t = time.time()
        s = calibrate.lattice(P, cells, [I0] * cells_per, ncx, ncy, cell=8, seed=seed + b, groups=groups, log=lambda *a: None,
                              trigger_mode=mode, dt=dt, calib=calib, vignette=vignette)
        wall += time.time() - t
        sm = s.summary(); nfalse += sm['n_false']
        first = {}
        for d in s.detections:
            if d['label'] == 'flash' and d['match'] not in first:
                first[d['match']] = d
        for i, (f, row) in enumerate(zip(s.flashes, sm['per_flash'])):
            c = (f['E_J'], f['tau_s'])
            res[c]['n'] += 1; res[c]['k'] += int(row['detected'])
            if row['detected']:
                res[c]['lag'].append(row['lag_s'])
                if 'ln_err_raw' not in row:
                    continue
                res[c]['n_meas'] += 1; res[c]['onset'].append(row['onset_err_s'])
                if row.get('censored'):
                    res[c]['n_cens'] += 1; res[c]['lnerr_cens'].append(row['ln_err_raw'])
                    continue
                if calib is not None and 'ln_err_corr' not in row:
                    continue                      # keep raw and corrected on the same cohort
                res[c]['lnerr'].append(row['ln_err_raw'])
                if 'ln_err_corr' in row:
                    res[c]['lncorr'].append(row['ln_err_corr'])
                if counterfactual_no_gain and calib is not None:
                    # the same record reconstructed WITHOUT dividing by the field gain, through the correction
                    m = dict(first[i]['energy']); m['e_raw_J'] = m['e_raw_J'] * m['field_gain']
                    ec, _ = trg.apply_correction(m, calib)
                    res[c]['lnraw_nogain'].append(math.log(m['e_raw_J'] / f['E_J']))
                    res[c]['lncorr_nogain'].append(math.log(ec / f['E_J']))
    out = []
    for (E, tau), r in res.items():
        st = stored(s10_case, I0, E, tau) if s10_case else None
        row = dict(E_J=E, tau_s=tau, I0=I0, k=r['k'], n=r['n'], p=r['k'] / r['n'], wilson95=wilson(r['k'], r['n']),
                   n_measured=r['n_meas'], n_censored=r['n_cens'], n_energy_cohort=len(r['lnerr']),
                   raw_ln_median_censored_only=float(np.median(r['lnerr_cens'])) if r['lnerr_cens'] else None,
                   raw_ln_bias=float(np.median(r['lnerr'])) if r['lnerr'] else None,
                   raw_ln_sd=float(np.std(r['lnerr'])) if len(r['lnerr']) > 2 else None,
                   raw_ln_median_se=boot_se(r['lnerr']),
                   corr_ln_median=float(np.median(r['lncorr'])) if r['lncorr'] else None,
                   corr_ln_rms=float(np.sqrt(np.mean(np.square(r['lncorr'])))) if r['lncorr'] else None,
                   corr_ln_median_se=boot_se(r['lncorr']),
                   lag_median_s=float(np.median(r['lag'])) if r['lag'] else None,
                   **({} if not r['lncorr_nogain'] else dict(
                       raw_ln_median_without_gain_division=float(np.median(r['lnraw_nogain'])),
                       corr_ln_median_without_gain_division=float(np.median(r['lncorr_nogain'])),
                       corr_ln_median_se_without_gain_division=boot_se(r['lncorr_nogain']))),
                   onset_err_median_s=float(np.median(r['onset'])) if r['onset'] else None)
        if st:
            row.update(s10_k=st['k_detect'], s10_n=st['n_trials'], s10_raw_ln_bias=st['raw_ln_bias'], s10_raw_ln_sd=st['raw_ln_sd'],
                       s10_lag_median_s=st['trigger_lag_s_median'],
                       fisher_p=two_prop_p(r['k'], r['n'], st['k_detect'], st['n_trials']),
                       within_s10_wilson=wilson(st['k_detect'], st['n_trials'])[0] <= r['k'] / r['n'] <= wilson(st['k_detect'], st['n_trials'])[1])
        out.append(row)
    return dict(sensor=sensor, s10_case=s10_case, I0=I0, groups=groups, thresholds=mode, rows=out, false_detections=nfalse,
                wall_s=wall, dt=dt)


def v_s10():
    res = {}
    for I0 in (6500.0, 13000.0):
        print(f'S10 nominal at {I0:.0f}', flush=True)
        res[f'nominal_{I0:.0f}'] = lattice_grid('imx636_s10nominal', 'nominal', I0, S10_CASES)
        for r in res[f'nominal_{I0:.0f}']['rows']:
            print(f"  {r['E_J']:.0e} J {r['tau_s']} s: {r['k']}/{r['n']} (S10 {r.get('s10_k')}/{r.get('s10_n')}, p={r.get('fisher_p', float('nan')):.2f}) "
                  f"raw bias {r['raw_ln_bias']} (S10 {r.get('s10_raw_ln_bias')})", flush=True)
    print('S16 m636 at 13000', flush=True)
    res['m636_13000'] = lattice_grid('imx636_m636s10', 'm636', 13000.0, M636_CASES)
    for r in res['m636_13000']['rows']:
        print(f"  {r['E_J']:.0e} J {r['tau_s']} s: {r['k']}/{r['n']} (S16 {r.get('s10_k')}/{r.get('s10_n')})", flush=True)
    (DATA / 'validation_s10.json').write_text(json.dumps(res, indent=1, default=float))
    plot_s10(res)
    return res


def v_realistic():
    res = {}
    for sensor, case in (('imx636', 'm636'), ('imx646', 'm646_surrogate')):
        for groups in ('patch', 'cell'):
            key = f'{sensor}_{groups}_13000'
            print(key, flush=True)
            res[key] = lattice_grid(sensor, None, 13000.0, M636_CASES + [(4e4, 0.1), (1e5, 0.3)], groups=groups, mode='compute')
            res[key]['s10_reference_case'] = case
            for r in res[key]['rows']:
                st = stored(case, 13000.0, r['E_J'], r['tau_s'])
                if st:
                    r['s16_k'] = st['k_detect']; r['s16_n'] = st['n_trials']
                print(f"  {r['E_J']:.0e} J {r['tau_s']} s: {r['k']}/{r['n']} (S16 {r.get('s16_k')}/{r.get('s16_n')}) raw bias {r['raw_ln_bias']}", flush=True)
    (DATA / 'validation_realistic.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_ba(duration=30.0):
    res = {}
    for sensor, sets in (('imx636', ['sensor.mask.fraction=0.0']), ('imx636_s10nominal', [])):
        P = P_(sensor, sets)
        w, h = 160, 90
        dark = dark_e_s(P['sensor']['dark.current_fA'])
        sc = scenes.FlatScene(w, h, 0.0, 3150.0, P['env'], label='dark')
        s = sim.Simulation(sc, P['sensor'], P['optics'], P['env'], duration, seed=31, flashes=[], particles=None,
                           log=lambda *a: None)
        t = time.time(); s.run(); wall = time.time() - t
        ev = s.events
        cnt = np.bincount(ev['p'], minlength=w * h)
        cnt_ba = np.bincount(ev['p'][ev['src'] == 1], minlength=w * h)
        cnt_cmp = np.bincount(ev['p'][ev['src'] == 0], minlength=w * h)
        exp_rate = s.ba
        normal = ~s.hot
        # counts in 2 s windows for normal pixels: Fano factor
        W = 2.0
        nb = int(duration // W)
        b = np.minimum((ev['t'] / W).astype(int), nb - 1)
        sel = (ev['src'] == 1) & (ev['pol'] == 1)
        M = np.zeros((nb, w * h)); np.add.at(M, (b[sel], ev['p'][sel]), 1)
        mu = exp_rate * W
        fano_norm = float(((M[:, normal] - mu[normal]) ** 2).sum() / max(mu[normal].sum() * nb, 1e-9))
        # masking test: 60 s calibration ranking vs true hot pixels (on the profile with masking)
        P2 = P_(sensor)
        s2 = sim.Simulation(sc, P2['sensor'], P2['optics'], P2['env'], 0.5, seed=31, flashes=[], particles=None, log=lambda *a: None)
        mask_hot = float((s2.masked & s2.hot).sum() / max(s2.hot.sum(), 1)) if s2.hot.any() else None
        ba_after_mask = float(s2.ba[~s2.masked].mean())
        rows = dict(sensor=sensor, duration_s=duration, pixels=w * h, wall_s=wall,
                    mean_rate_observed_hz=float(cnt_ba.sum() / duration / (w * h)),
                    mean_rate_configured_hz=float(exp_rate.mean()),
                    normal_rate_observed_hz=float(cnt_ba[normal].sum() / duration / normal.sum()),
                    normal_rate_configured_hz=float(exp_rate[normal].mean()),
                    hot_fraction=float(s.hot.mean()), hot_rate_observed_hz=float(cnt_ba[s.hot].sum() / duration / max(s.hot.sum(), 1)),
                    hot_rate_configured_hz=float(exp_rate[s.hot].mean()) if s.hot.any() else None,
                    share_of_events_in_hot=float(cnt_ba[s.hot].sum() / max(cnt_ba.sum(), 1)),
                    comparator_events_per_px_s=float(cnt_cmp.sum() / duration / (w * h)),
                    fano_2s_normal=fano_norm, on_fraction=float((ev['pol'][ev['src'] == 1] == 1).mean()) if (ev['src'] == 1).any() else None,
                    regression_slope_obs_vs_cfg=float(np.polyfit(exp_rate * duration, cnt_ba, 1)[0]),
                    hot_pixels_masked_fraction=mask_hot, mean_ba_unmasked_hz=ba_after_mask,
                    s10_null_shot_mean_per_px_2s=ER['thresholds'].get('nominal_6500', {}).get('2.0', {}).get('shot_mean_per_pixel'))
        res[sensor] = rows
        print(sensor, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows.items()}, flush=True)
        if sensor == 'imx636':
            plot_ba(exp_rate, cnt_ba / duration, s.hot)
    (DATA / 'validation_ba.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_texture(duration=30.0, I0=1.3e4, cases=None, fname='validation_texture.json'):
    res = {}
    S17 = json.loads((DATA / 'texture_histograms.json').read_text())
    cases = cases or (('imx636_s10nominal', 'nominal', 'nominal_1.3e4', ()), ('imx636', 'm636', 'm636_1.3e4', ()))
    for sensor, case, hkey, sets in cases:
        P = P_(sensor, sets)
        sensor = sensor + ('+' + ','.join(sets) if sets else '')
        sc = scenes.build('nearside', P['sensor'], P['optics'], P['env'], crop_wh=(320, 180), duration=duration,
                          earthshine='target_mean', I0_target=I0)
        s = sim.Simulation(sc, P['sensor'], P['optics'], P['env'], duration, seed=41, flashes=[], particles=None, log=print)
        t = time.time(); s.run(); s.detect(); wall = time.time() - t
        sm = s.summary()
        W = 2.0; C = P['sensor']['threshold.C_on']
        ev = s.events
        nb = int(duration // W)
        lnB = [np.log(sc.photo_rate(k * W) + s.dark.reshape(s.h, s.w)) for k in range(nb + 1)]
        on = (ev['pol'] == 1) & (ev['src'] == 0)
        k = np.floor(ev['t'][on] / 5e-4).astype(np.int64)
        key = np.unique(k * s.P + ev['p'][on])
        st, px = key // s.P, key % s.P
        b = np.minimum((st * 5e-4 / W).astype(int), nb - 1)
        obs, pred = [], []
        for i in range(1, nb):           # skip the first window (initial reference phase)
            m = np.bincount(px[b == i], minlength=s.P).reshape(s.h, s.w).astype(float)
            rise = np.clip(lnB[i + 1] - lnB[i], 0, None) / C
            og = m[:-1, :-1] + m[1:, :-1] + m[:-1, 1:] + m[1:, 1:]
            pg = rise[:-1, :-1] + rise[1:, :-1] + rise[:-1, 1:] + rise[1:, 1:]
            obs.append(og.ravel()); pred.append(pg.ravel())
        obs = np.concatenate(obs); pred = np.concatenate(pred)
        bins = [0, 0.25, 0.5, 1, 2, 4, 8, 100]
        tab = []
        for a, bb in zip(bins[:-1], bins[1:]):
            sel = (pred >= a) & (pred < bb)
            if sel.sum() > 20:
                tab.append(dict(mu_pred_lo=a, mu_pred_hi=bb, n_groups=int(sel.sum()), mu_pred_mean=float(pred[sel].mean()),
                                obs_mean=float(obs[sel].mean()), obs_var=float(obs[sel].var()),
                                var_over_mean=float(obs[sel].var() / max(obs[sel].mean(), 1e-9))))
        # S17 histogram for the same window/group, whole near side
        edges = np.array(S17['bins'])
        hist = sum(np.array(S17['tiles'][tl][hkey]['2.0_2'], float) for tl in S17['tiles'])
        cen = np.sqrt(np.maximum(edges[:-1], 1e-12) * edges[1:]) / C
        def share_gt(x):
            return float(hist[cen > x].sum() / hist.sum())
        q = [0.99, 0.999, 0.9999]
        res[sensor] = dict(sensor=sensor, I0_target=I0, duration_s=duration, crop=list(sc.crop), wall_s=wall,
                           drift_px_s=sc.meta['ground']['drift_px_s'],
                           false_detections=sm['n_false'], n_trigger_rows=int(len(s.triggers)),
                           mean_background=float(np.mean(s.bg_chunks)),
                           comparator_events_per_px_s=float(on.sum() / duration / s.P),
                           off_events_per_px_s=float((ev['pol'] == -1).sum() / duration / s.P),
                           count_vs_prediction=tab,
                           pred_mu_quantiles_this_crop=dict(zip(map(str, q), np.quantile(pred, q).tolist())),
                           obs_count_quantiles_this_crop=dict(zip(map(str, q), np.quantile(obs, q).tolist())),
                           s17_share_mu_gt=dict((str(x), share_gt(x)) for x in (1, 2, 4.8, 7.5, 16)),
                           this_crop_share_mu_gt=dict((str(x), float((pred > x).mean())) for x in (1, 2, 4.8, 7.5, 16)),
                           thresholds_2s=[int(s.thr_maps[0, 3, 0].min()), int(s.thr_maps[0, 3, 0].max())],
                           expected_false_triggers_in_crop_run_at_budget=float(1.0 * (s.P / (1280 * 720)) / 6 * duration / 3600))
        print(sensor, json.dumps(res[sensor], default=float)[:1500], flush=True)
    (DATA / fname).write_text(json.dumps(res, indent=1, default=float))
    if fname == 'validation_texture.json':
        plot_texture(res)
    return res


def v_texture_prehistory():
    """S10 nominal numerics with a random initial reference: separates the start transient from comparator hysteresis."""
    return v_texture(cases=(('imx636_s10nominal', 'nominal', 'nominal_1.3e4', ('sensor.events.initial_reference="random"',)),),
                     fname='validation_texture_prehistory.json')


def _calib(name='imx636'):
    p = DATA / f'energy_calibration_{name}.json'
    return json.loads(p.read_text()) if p.exists() else None


SUB_CASES = [(1e4, 0.03), (2e4, 0.1), (4e4, 1.0), (3e5, 1.0), (1e6, 0.1), (3e6, 0.03), (3e6, 0.3)]


def v_substep():
    """V5 (rewritten for review E02): faint and bright flashes at 0.5, 0.25 and 0.1 ms steps, with the fixed-step
    kernel and with adaptive sub-steps (default) and tighter sub-step tolerances; raw and corrected energy with
    bootstrap standard errors of the median; plus the reviewer's 16-flash 3 MJ diagnostic."""
    res = dict(cases=[list(c) for c in SUB_CASES], configs={}, reviewer_diagnostic={})
    calib = _calib()
    configs = [('fixed', ['sensor.photoreceptor.adaptive_substeps=false']), ('adaptive', []),
               ('adaptive_tight', ['sensor.photoreceptor.substep_tau_fraction=0.25', 'sensor.photoreceptor.substep_dlnJ_max=0.05',
                                   'sensor.photoreceptor.substep_min_s=2e-6'])]
    for name, sets in configs:
        for dt in (5e-4, 2.5e-4, 1e-4):
            if name == 'adaptive_tight' and dt != 5e-4:
                continue
            key = f'{name}_dt{dt:g}'
            r = lattice_grid('imx636', None, 13000.0, SUB_CASES, per_case=48, ncx=16, ncy=12, groups='cell', mode='compute',
                             dt=dt, sets=sets, calib=calib, seed=17)
            res['configs'][key] = r
            print(key, [(r2['E_J'], r2['tau_s'], r2['k'], r2['n'], round(r2['raw_ln_bias'] or 0, 3),
                         None if r2['corr_ln_median'] is None else round(r2['corr_ln_median'], 3)) for r2 in r['rows']],
                  'wall', round(r['wall_s'], 1), flush=True)
    for name, sets in configs[:2]:
        for dt in (5e-4, 1e-4):
            r = lattice_grid('imx636', None, 13000.0, [(3e6, 0.03)], per_case=16, seed=930, ncx=4, ncy=4, groups='patch',
                             mode='stored', sets=sets, dt=dt)
            res['reviewer_diagnostic'][f'{name}_dt{dt:g}'] = r['rows'][0]
            print('reviewer diagnostic', name, dt, r['rows'][0]['k'], round(r['rows'][0]['raw_ln_bias'], 5), flush=True)
    (DATA / 'validation_substep.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_refractory(n_train=1152, n_test=576):
    """V6 (rewritten for review E07): for each refractory period the S11 correction is RETRAINED on that setting
    and tested on held-out flashes, so that the comparison is of recoverable (corrected) energy, by energy band."""
    from eventsim import calibrate as cal
    res = {}
    for r in (0.0, 1e-5, 5e-5, 2e-4):
        out = cal.run('imx636', n=n_train, seed=20261104, sets=[f'sensor.events.refractory_s={r}'], out=None,
                      tests=(('a_same_family', ('exp',), n_test),), log=lambda *a: None)
        t = out['tests']['a_same_family']
        res[f'{r:g}'] = dict(refractory_s=r, train_detected=[out['n_train_detected'], n_train], test_detected=t['detected'],
                             raw=t['raw'], corrected=t['corrected'], by_energy=t['by_energy'], train_raw=out['train_raw'],
                             outside_training_range_fraction=t['outside_training_range_fraction'])
        print(r, json.dumps(res[f'{r:g}'], default=float)[:600], flush=True)
    (DATA / 'validation_refractory.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_sensitivity():
    """V7 (review E08): sensitivity of detection and energy to a first-order high-pass on the change-detector input
    (bias_hpf stand-in; corner 0.1, 0.5 and 1.6 Hz) and to the v2e-like leak-drift background-activity model.
    Correction trained without them (as a fixed on-board correction would be)."""
    calib = _calib()
    cases = M636_CASES + [(1e6, 0.3), (3e6, 1.0)]
    res = {}
    for name, sets in (('baseline', []), ('hpf_1.6s', ['sensor.photoreceptor.hpf_tau_s=1.6']),
                       ('hpf_0.32s', ['sensor.photoreceptor.hpf_tau_s=0.32']), ('hpf_0.1s', ['sensor.photoreceptor.hpf_tau_s=0.1']),
                       ('ba_leak_drift', ['sensor.ba.model="leak_drift"'])):
        r = lattice_grid('imx636', None, 13000.0, cases, per_case=48, ncx=16, ncy=12, groups='cell', mode='compute',
                         sets=sets, calib=calib, seed=23)
        res[name] = r
        print(name, [(x['E_J'], x['tau_s'], x['k'], round(x['raw_ln_bias'] or 0, 3),
                      None if x['corr_ln_median'] is None else round(x['corr_ln_median'], 3)) for x in r['rows']],
              'false', r['false_detections'], flush=True)
    (DATA / 'validation_sensitivity.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_hpf_retrained(n_train=1152, n_test=576):
    """V7b: high-pass corner with the correction RETRAINED per setting, against the default (no high-pass)
    correction on the same held-out flashes. The retrained error is what the event stream still allows the
    estimator to recover; the difference to the default correction is estimator mismatch."""
    default = _calib()
    res = {}
    for name, tau in (('none', 0.0), ('hpf_1.6s', 1.6), ('hpf_0.32s', 0.32), ('hpf_0.1s', 0.1)):
        P = P_('imx636', [f'sensor.photoreceptor.hpf_tau_s={tau}'])
        rng = np.random.default_rng(20261105)
        train, ndt, ntt = calibrate.simulate_set(P, calibrate.draw_flashes(n_train, rng), ncx=24, ncy=12, cell=10, seed=11,
                                                 log=lambda *a: None)
        coef, frange, _, nused = calibrate.fit(train)
        test, nd, nt = calibrate.simulate_set(P, calibrate.draw_flashes(n_test, rng), ncx=24, ncy=12, cell=10, seed=13,
                                              log=lambda *a: None)
        own = dict(coef=coef.tolist(), feature_range=frange)
        raw, c_own, _ = calibrate.evaluate_rows(test, own)
        _, c_def, out_def = calibrate.evaluate_rows(test, default)
        E = np.exp(np.array([r['lnE'] for r in test if not r.get('censored')]))
        tau_f = np.array([r['tau'] for r in test if not r.get('censored')])
        def band(sel):
            if sel.sum() < 6:
                return None
            return dict(n=int(sel.sum()), raw=calibrate.stats(raw[sel]), retrained=calibrate.stats(c_own[sel]),
                        default_correction=calibrate.stats(c_def[sel]))
        res[name] = dict(hpf_tau_s=tau, corner_hz=(1 / (2 * math.pi * tau)) if tau else None, train_detected=[ndt, ntt],
                         test_detected=[nd, nt], raw=calibrate.stats(raw), retrained=calibrate.stats(c_own),
                         default_correction=calibrate.stats(c_def),
                         default_outside_training_range_fraction=float(out_def.mean()) if out_def.size else None,
                         by_tau={'tau_le_0.3': band(tau_f <= 0.3), 'tau_gt_0.3': band(tau_f > 0.3)},
                         by_energy={f'{lo:.0e}-{hi:.0e}': band((E >= lo) & (E < hi)) for lo, hi in ((1e4, 1e5), (1e5, 1e6), (1e6, 3.01e6))})
        print(name, 'detected', nd, nt, 'retrained rms', round(res[name]['retrained']['rms'], 3),
              'default rms', round(res[name]['default_correction']['rms'], 3), flush=True)
    (DATA / 'validation_hpf_retrained.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_particle_timestep(duration=20.0):
    """V10: particle-pulse convergence of the pixel kernel. A dark 160 x 90 px field with GCR (solar minimum, rate x
    1000 for statistics) at 0.5 and 0.1 ms steps, for prompt deposits, a 10% tail collected over 1 ms, and the
    extreme stress (0.5 px diffusion, all charge over 1 ms). Reports comparator events per hit and particle
    triggers. The adaptive sub-step choice uses the optical rate before deposits, so this tests that choice."""
    P = P_('imx636')
    w, h = 160, 90
    sc = scenes.FlatScene(w, h, 0.0, 3150.0, P['env'], label='dark')
    models = (('prompt', {}), ('tail10pct_1ms', dict(collection_tau_s=1e-3, collection_tail_fraction=0.1)),
              ('extreme_diff05_all_1ms', dict(diffusion_sigma_px=0.5, collection_tau_s=1e-3, collection_tail_fraction=1.0)))
    res = {}
    for name, extra in models:
        for dt in (5e-4, 1e-4):
            cfg = dict(let_epoch='solar_min', flux_cm2_s=4050.0, **extra)
            s = sim.Simulation(sc, P['sensor'], P['optics'], P['env'], duration, dt=dt, seed=61, flashes=[], particles=cfg,
                               log=lambda *a: None)
            t = time.time(); s.run(); s.detect(); wall = time.time() - t
            ev = s.events
            cmp_ = ev['src'] == 0
            per_hit = []; per_hit_on = []
            for hh in s.hits:
                pix = np.array([y * w + x for x, y in hh['pixels']])
                m = cmp_ & np.isin(ev['p'], pix) & (ev['t'] >= hh['t'] - 2e-6) & (ev['t'] < hh['t'] + 0.05)   # 1 us readout ticks
                per_hit.append(int(m.sum())); per_hit_on.append(int((m & (ev['pol'] == 1)).sum()))
            heavy = np.array([hh['heavy'] for hh in s.hits]); per_hit = np.array(per_hit); per_hit_on = np.array(per_hit_on)
            sm = s.summary()
            res[f'{name}_dt{dt:g}'] = dict(model=name, dt=dt, n_hits=len(s.hits), n_heavy=int(heavy.sum()),
                                          events_per_hit_mean=float(per_hit.mean()) if per_hit.size else None,
                                          on_events_per_heavy_hit_mean=float(per_hit_on[heavy].mean()) if heavy.any() else None,
                                          hits_with_events=int((per_hit > 0).sum()), particle_triggers=sm['n_particle_triggers'],
                                          false_triggers=sm['n_false'], extra_substeps=s.stats['extra_substeps'], wall_s=wall)
            print(name, dt, json.dumps(res[f'{name}_dt{dt:g}'], default=float), flush=True)
    (DATA / 'validation_particle_timestep.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_field_gain():
    """V8: point sources attenuated by the corner field gain of the full 16 mm frame (cos^4 = 0.908) against the
    centre (1.0), same seeds; the reconstruction divides by the known field gain. For the corner case the same
    records are also reconstructed without that division and passed through the correction (counterfactual)."""
    calib = _calib()
    res = {}
    cases = [(2e4, 0.1), (1e5, 0.3), (1e6, 0.1)]
    for g in (1.0, 0.908):
        r = lattice_grid('imx636', None, 13000.0, cases, per_case=96, ncx=16, ncy=12, groups='cell', mode='compute',
                         calib=calib, vignette=g, seed=29, counterfactual_no_gain=(g != 1.0))
        res[f'gain_{g:g}'] = r
    comp = []
    for a, b in zip(res['gain_1']['rows'], res['gain_0.908']['rows']):
        se = math.hypot(a['corr_ln_median_se'], b['corr_ln_median_se'])
        comp.append(dict(E_J=a['E_J'], tau_s=a['tau_s'], corner_minus_centre_corr_median=b['corr_ln_median'] - a['corr_ln_median'],
                         combined_median_se=se,
                         corner_minus_centre_corr_median_without_gain_division=b['corr_ln_median_without_gain_division'] - a['corr_ln_median'],
                         corner_minus_centre_raw_median=b['raw_ln_bias'] - a['raw_ln_bias'],
                         corner_minus_centre_raw_median_without_gain_division=b['raw_ln_median_without_gain_division'] - a['raw_ln_bias']))
        print(comp[-1], flush=True)
    res['comparison'] = comp
    res['note'] = ('Without the field-gain division the RAW energy is lower by exactly ln(0.908) = '
                   f'{math.log(0.908):.3f}; the corrected effect is evaluated through the quadratic correction '
                   '(comparison: *_without_gain_division), since the correction depends on ln E_raw nonlinearly.')
    (DATA / 'validation_field_gain.json').write_text(json.dumps(res, indent=1, default=float))
    return res


def v_shadow():
    """V9 (review E10): analytic ridge. A 3 km-high, 3 km-wide north-south ridge 30 km east of the map region,
    Sun from the east at 1.5-3.5 deg elevation. For every pixel of the central row the analytic lit fraction
    (horizon angle of the ridge top with lunar curvature, softened by the solar disc, the elevation of the Sun at
    that pixel) is compared with cast_shadow() on the extended grid, and with terrain outside the region missing
    (which the pre-review code replaced by the region's edge height, here 0 m)."""
    from eventsim.lunar_maps import RegionMaps, R_MOON_M
    rm = object.__new__(RegionMaps)
    res_deg = 1.0 / 76
    lat0, lat1, lon0, lon1 = -0.5, 0.5, 0.0, 2.0
    rm.res = res_deg; rm.lat_top = lat1; rm.lon_left = lon0
    nr = int(math.ceil((lat1 - lat0) / res_deg)); nc = int(math.ceil((lon1 - lon0) / res_deg))
    rm.lat = lat1 - (np.arange(nr) + 0.5) * res_deg; rm.lon = lon0 + (np.arange(nc) + 0.5) * res_deg
    rm.LAT, rm.LON = np.meshgrid(rm.lat, rm.lon, indexing='ij')
    km_per_deg = R_MOON_M / 1e3 * math.pi / 180
    H, half_w, dist = 3000.0, 1.5, 30.0
    lon_ridge = lon1 + dist / km_per_deg
    def hfn(la, lo):
        return np.where(np.abs(lo - lon_ridge) * km_per_deg < half_w, H, 0.0)
    rm.height = hfn(rm.LAT, rm.LON).astype(np.float32)
    rm.dy_m = res_deg * math.pi / 180 * R_MOON_M; rm.dx_m = rm.dy_m * np.cos(np.radians(rm.LAT))
    lon_s = math.radians(lon1 + 86.5)                  # subsolar longitude: Sun 3.5 deg above the east horizon at lon1, 1.5 deg at lon0
    sun = np.array([math.cos(lon_s), math.sin(lon_s), 0.0])
    lit_new = rm.cast_shadow(sun, height_fn=hfn)
    info_new = dict(rm.shadow_info)
    lit_clamp = rm.cast_shadow(sun, height_fn=lambda la, lo: np.where((lo >= lon0) & (lo <= lon1), hfn(la, lo), np.nan))
    info_clamp = dict(rm.shadow_info)
    row = nr // 2
    sun_r = math.radians(0.53 / 2)
    lit_an = np.zeros(nc)
    for k, lo in enumerate(rm.lon):
        el = math.asin(math.cos(math.radians(rm.lat[row])) * math.cos(lon_s - math.radians(lo)))
        D = (np.linspace(lon_ridge - half_w / km_per_deg, lon_ridge + half_w / km_per_deg, 61) - lo) * km_per_deg * 1e3 * math.cos(math.radians(rm.lat[row]))
        hor = math.atan(max(-1.0, float(np.max((H - D * D / (2 * R_MOON_M)) / D))))
        lit_an[k] = min(max((el - hor) / (2 * sun_r) + 0.5, 0.0), 1.0)
    dmax = float(np.max(np.abs(lit_new[row] - lit_an)))
    res = dict(ridge_height_m=H, ridge_width_km=2 * half_w, ridge_distance_east_of_region_km=dist,
               analytic_shadowed_fraction_of_row=float((lit_an < 0.5).mean()),
               extended_grid_shadowed_fraction_of_row=float((lit_new[row] < 0.5).mean()),
               clamped_grid_shadowed_fraction_of_row=float((lit_clamp[row] < 0.5).mean()),
               extended_vs_analytic_max_abs_lit_difference=dmax,
               extended_vs_analytic_pixels_differing_over_0p5=int(np.sum(np.abs(lit_new[row] - lit_an) > 0.5)),
               extended_info=info_new, clamped_info=info_clamp,
               note='Differences come from the 0.4 km march step and the bilinear sampling of the 3 km ridge on a '
                    '0.4 km grid. The clamped case flags all its rays as meeting missing terrain.')
    print(json.dumps(res, default=float), flush=True)
    (DATA / 'validation_shadow.json').write_text(json.dumps(res, indent=1, default=float))
    return res


# ---------------- plots ----------------
def _plt():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
    return plt


def plot_s10(res):
    plt = _plt()
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for ax, key, title in zip(axs, ('nominal_6500', 'nominal_13000', 'm636_13000'),
                              ('S10 nominal, 6.5e3 e-/s', 'S10 nominal, 1.3e4 e-/s', 'S16 m636, 1.3e4 e-/s')):
        rows = res[key]['rows']
        x = np.arange(len(rows))
        p = [r['p'] for r in rows]; lo = [max(0, r['p'] - r['wilson95'][0]) for r in rows]; hi = [max(0, r['wilson95'][1] - r['p']) for r in rows]
        ax.errorbar(x - 0.12, p, yerr=[lo, hi], fmt='o', color='#2a6f97', ms=4, capsize=2, label='this simulator (n=144)')
        ps = [r['s10_k'] / r['s10_n'] for r in rows]
        ws = [wilson(r['s10_k'], r['s10_n']) for r in rows]
        ax.errorbar(x + 0.12, ps, yerr=[[max(0, a - b[0]) for a, b in zip(ps, ws)], [max(0, b[1] - a) for a, b in zip(ps, ws)]], fmt='s',
                    color='#c8553d', ms=4, capsize=2, label='event_response.py (n=40)')
        ax.set_xticks(x); ax.set_xticklabels([f"{r['E_J']:.0e}\n{r['tau_s']:g} s" for r in rows], fontsize=7)
        ax.set_title(title); ax.set_ylim(-0.03, 1.05); ax.grid(axis='y', alpha=0.3)
    axs[0].set_ylabel('detection probability'); axs[0].legend(fontsize=7, loc='lower right')
    fig.text(0.5, 0.005, 'flash light energy E_L [J] and decay time, 3750 km', ha='center')
    plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig(FIG / 'validation_s10_detection.png', dpi=150); plt.close()


def plot_ba(cfg, obs, hot):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.loglog(cfg[~hot], np.maximum(obs[~hot], 1 / 30 / 2), '.', ms=2, alpha=0.4, color='#2a6f97', label='normal pixels')
    ax.loglog(cfg[hot], np.maximum(obs[hot], 1 / 30 / 2), '.', ms=3, alpha=0.7, color='#c8553d', label='hot pixels')
    lim = [1e-3, 1e2]; ax.plot(lim, lim, 'k--', lw=0.8, label='1:1')
    ax.set_xlabel('configured background-activity rate [Hz]'); ax.set_ylabel('simulated rate, 30 s [Hz]')
    ax.set_title('IMX636 profile, dark, no mask'); ax.legend(fontsize=7); ax.set_xlim(lim); ax.set_ylim(1e-2 / 2, 1e2)
    plt.tight_layout(); plt.savefig(FIG / 'validation_ba_rates.png', dpi=150); plt.close()


def plot_texture(res):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(4.8, 3.6))
    for (k, r), c in zip(res.items(), ('#2a6f97', '#c8553d')):
        t = r['count_vs_prediction']
        ax.plot([x['mu_pred_mean'] for x in t], [x['obs_mean'] for x in t], 'o-', color=c, ms=4, label=f'{k}: mean')
        ax.plot([x['mu_pred_mean'] for x in t], [x['obs_var'] for x in t], 's:', color=c, ms=3, label=f'{k}: variance')
    m = max(x['mu_pred_mean'] for r in res.values() for x in r['count_vs_prediction'])
    ax.plot([0, m], [0, m], 'k--', lw=0.8, label='mu = S/C (S17)')
    ax.set_xlabel('predicted texture counts per 2x2 group, 2 s [events]'); ax.set_ylabel('simulated ON counts (signal) [events]')
    ax.set_title('Moving measured texture, 1.3e4 e-/s'); ax.legend(fontsize=6.5)
    plt.tight_layout(); plt.savefig(FIG / 'validation_texture_counts.png', dpi=150); plt.close()


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    fns = dict(s10=v_s10, realistic=v_realistic, ba=v_ba, texture=v_texture, substep=v_substep, refractory=v_refractory,
               texture_prehistory=v_texture_prehistory, sensitivity=v_sensitivity, field_gain=v_field_gain, shadow=v_shadow,
               hpf_retrained=v_hpf_retrained, particle_timestep=v_particle_timestep)
    for k in (fns if what == 'all' else [what]):
        t = time.time(); fns[k](); print(f'{k} done in {time.time() - t:.0f} s', flush=True)
