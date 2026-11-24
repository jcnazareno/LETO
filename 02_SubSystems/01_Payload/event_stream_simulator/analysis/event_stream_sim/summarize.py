"""Collect per-run results and validation into data/results_summary.json, print Markdown tables,
and extract PNG stills from the videos into figures/.

  python summarize.py
"""
from __future__ import annotations
import json
import math
import subprocess
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'
FIG = ROOT / 'figures'
RUNS = ['nearside_imx636', 'farside_imx636', 'particles_imx636', 'particles_imx636_nomask', 'terminator_imx636',
        'terminator_imx636_nolitmask', 'terminator_far_imx636', 'terminator_far_imx636_nolitmask', 'limb_imx636', 'compare_nearside_imx636', 'compare_nearside_imx646',
        'nearside_imx636_full', 'particles_gcrmin_x100_imx636', 'particles_gcrmin_x100_imx636_nomask',
        'particles_gcrmax_x100_imx636', 'particles_gcrmin_x100_imx636_nomask_measuredhot',
        # stress runs added for the 4 Nov 2026 review (E04, E06, E09)
        'terminator_imx636_mapshift_p3', 'terminator_imx636_mapshift_m3', 'nearside_imx636_bgerr_p20',
        'nearside_imx636_bgerr_m20', 'nearside_imx636_geomean', 'nearside_imx636_ba03_fixed', 'nearside_imx636_ba03_retuned',
        'particles_gcrmin_x100_imx636_diff05', 'particles_gcrmin_x100_imx636_diff05_coll1ms',
        'particles_gcrmin_x100_imx636_coll5ms', 'particles_sep1000_imx636']


def run_row(tag):
    p = DATA / f'{tag}_truth.json'
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    sm, st, cf = d['summary'], d['stats'], d['config']
    pf = sm['per_flash']
    det = [r for r in pf if r['detected']]
    lag = [r['lag_s'] for r in det]
    onset = [r['onset_err_s'] for r in det if 'onset_err_s' in r]
    # energy statistics use complete records only (review E01); censored records are counted separately
    comp = [r for r in det if not r.get('censored')]
    corr = [r['ln_err_corr'] for r in comp if 'ln_err_corr' in r]
    raw = [r['ln_err_raw'] for r in comp if 'ln_err_raw' in r]
    P = cf['crop'][2] * cf['crop'][3]
    false = [dd for dd in d['detections'] if dd['label'] == 'false']
    return dict(tag=tag, scene=cf['scene'], sensor=cf['sensor'], crop=cf['crop'], duration_s=cf['duration_s'],
                n_flashes=sm['n_flashes'], n_detected=sm['n_detected'], n_false=sm['n_false'],
                false_triggers=[dict(t=f['t_trig'], x=f['x'], y=f['y'], W=f['W']) for f in false][:20],
                n_particle_hits=sm['n_particle_hits'], n_heavy=sm['n_heavy_hits'], n_particle_triggers=sm['n_particle_triggers'],
                # on board nothing labels a candidate as a particle: both count against the false-alarm budget (E09)
                n_false_operational=sm['n_false'] + sm['n_particle_triggers'],
                events=st['n_events'], ev_rate_kev_s=st['n_events'] / cf['duration_s'] / 1e3,
                ev_per_px_s=st['n_events'] / cf['duration_s'] / P, on_share=st['n_on'] / max(st['n_events'], 1),
                ba_share=st['n_ba'] / max(st['n_events'], 1), readout=st['readout'],
                lag_median_ms=float(np.median(lag) * 1e3) if lag else None,
                lag_range_ms=[float(np.min(lag) * 1e3), float(np.max(lag) * 1e3)] if lag else None,
                onset_err_median_ms=float(np.median(onset) * 1e3) if onset else None,
                onset_err_range_ms=[float(np.min(onset) * 1e3), float(np.max(onset) * 1e3)] if onset else None,
                n_censored=sum(1 for r in det if r.get('censored')),
                n_outside_training_range=sum(1 for r in comp if r.get('outside_training_range')),
                exposure=st.get('exposure'), integrator=st.get('integrator'), extra_substeps=st.get('extra_substeps'),
                trigger_model={k: (d.get('trigger') or {}).get(k) for k in ('case', 'model', 'group_bg', 'fingerprint', 'mapped_differences', 'mapped_adapted', 'unmapped_differences', 'heterogeneous_groups')},
                particle_cfg=cf.get('particle_cfg'), map_shift_px=cf.get('map_shift_px'), map_scale_err=cf.get('map_scale_err'),
                cast_shadow=d['scene'].get('cast_shadow'),
                ln_err_corr_median=float(np.median(corr)) if corr else None,
                ln_err_corr_rms=float(np.sqrt(np.mean(np.square(corr)))) if corr else None,
                ln_err_raw_median=float(np.median(raw)) if raw else None,
                wall_total_s=st.get('wall_total_s'), wall_pixel_s=st.get('wall_pixel_s'), wall_scene_s=st.get('wall_scene_s'),
                wall_trigger_s=st.get('wall_trigger_s'), peak_rss_MB=st.get('peak_rss_MB'),
                missed=[dict(E=r['E_J'], tau=r['tau_s'], range_km=r['range_km']) for r in pf if not r['detected']],
                per_flash=[dict(E=r['E_J'], tau=r['tau_s'], det=r['detected'],
                                lag_ms=r['lag_s'] * 1e3 if r.get('lag_s') is not None else None,
                                ln_corr=r.get('ln_err_corr'), ln_raw=r.get('ln_err_raw'), censored=r.get('censored'),
                                onset_err_ms=r['onset_err_s'] * 1e3 if r.get('onset_err_s') is not None else None)
                           for r in pf],
                scene_meta=dict(earth_phase=d['scene'].get('earth_phase_deg'), es_level=d['scene'].get('earthshine_level_e_s'),
                                ground=d['scene'].get('ground')))


def _strict(o):
    """Strict JSON: non-finite floats become null (review E13)."""
    if isinstance(o, dict):
        return {str(k): _strict(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_strict(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return float(o) if math.isfinite(float(o)) else None
    if isinstance(o, np.integer):
        return int(o)
    return o


def stills():
    for tag in ('nearside_imx636', 'farside_imx636', 'particles_imx636', 'terminator_imx636', 'terminator_far_imx636', 'particles_gcrmin_x100_imx636', 'limb_imx636',
                'compare_nearside_imx636_vs_imx646', 'nearside_imx636_full'):
        mp4 = OUT / f'{tag}.mp4'
        tj = DATA / f"{tag.replace('_vs_imx646', '')}_truth.json"
        if not mp4.exists() or not tj.exists():
            continue
        d = json.loads(tj.read_text())
        dets = [x for x in d['detections'] if x['label'] == 'flash']
        t = dets[min(1, len(dets) - 1)]['t_trig'] + 0.05 if dets else d['config']['duration_s'] / 2
        if 'particles' in tag and d['particle_hits']:
            t = d['particle_hits'][len(d['particle_hits']) // 2]['t'] + 0.01
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1',
                        str(FIG / f'still_{tag}.png')], check=False)


def main():
    rows = {t: run_row(t) for t in RUNS}
    rows = {k: v for k, v in rows.items() if v}
    val = {p.stem.replace('validation_', ''): json.loads(p.read_text()) for p in DATA.glob('validation_*.json')}
    out = dict(runs=rows, validation=val)
    cal = {p.stem: json.loads(p.read_text()) for p in DATA.glob('energy_calibration_*.json')}
    out['energy_calibration'] = {k: dict(n_train_detected=v['n_train_detected'], train_raw=v['train_raw'],
                                         feature_range=v.get('feature_range'), overrides=v.get('overrides'),
                                         tests={a: dict(raw=b['raw'], corrected=b['corrected'], detected=b.get('detected'),
                                                        by_condition=b.get('by_condition'), by_energy=b.get('by_energy'),
                                                        outside_training_range_fraction=b.get('outside_training_range_fraction'))
                                                for a, b in v['tests'].items()}) for k, v in cal.items()}
    (DATA / 'results_summary.json').write_text(json.dumps(_strict(out), indent=1, allow_nan=False))
    print('| Run | Events [kev/s] | Events per px per s | Flashes detected | False triggers | Particle hits (heavy) / triggers | Median lag [ms] | Energy error, corrected median/rms [ln] | Wall [s] | Peak RSS [MB] |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for k, r in rows.items():
        ce = f"{r['ln_err_corr_median']:+.2f} / {r['ln_err_corr_rms']:.2f}" if r['ln_err_corr_median'] is not None else '–'
        print(f"| {k} | {r['ev_rate_kev_s']:.1f} | {r['ev_per_px_s']:.3f} | {r['n_detected']}/{r['n_flashes']} | {r['n_false']} | "
              f"{r['n_particle_hits']} ({r['n_heavy']}) / {r['n_particle_triggers']} | {r['lag_median_ms'] or float('nan'):.0f} | {ce} | "
              f"{r['wall_total_s']:.0f} | {r['peak_rss_MB']:.0f} | censored {r['n_censored']} |")
    for k, v in out['energy_calibration'].items():
        print(k, v['n_train_detected'], {a: (round(b['corrected']['bias'], 3), round(b['corrected']['sd'], 3), b['detected']) for a, b in v['tests'].items()})
    stills()


if __name__ == '__main__':
    main()
