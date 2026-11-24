"""Pixel-parameter sensitivity (17 Nov 2026): refractory period and contrast threshold. Collects the runs of
run_pixel_sensitivity_2026-11-17.sh and the baseline runs, re-applies each variant's own energy correction to the
recorded energy features of every detection, and writes
  data/pixel_sensitivity/pixel_sensitivity_2026-11-17.json
  figures/pixel_sensitivity/pixel_sensitivity.png

  python pixel_sensitivity.py

Lattice precision and detection come from each variant's calibration file (held-out tests: 'a_same_family' =
exponential light curves, 'b_double_profile' = two-component); scene numbers from 20 s crop runs (8 flashes, or 4 in
the particle scene), corrected with the variant's calibration.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eventsim import trigger as trg      # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / 'data'
PS = DATA / 'pixel_sensitivity'
FIG = ROOT / 'figures' / 'pixel_sensitivity'
SCENES = ('nearside', 'farside', 'terminator', 'particles')
VARIANTS = [('C0p15', 'C = 0.15', 0.15, 10), ('C0p20', 'C = 0.20', 0.20, 10), ('base', 'baseline\nC = 0.25, 10 µs', 0.25, 10),
            ('C0p30', 'C = 0.30', 0.30, 10), ('C0p35', 'C = 0.35', 0.35, 10),
            ('refr79us', 'refractory\n79 µs', 0.25, 79), ('refr200us', 'refractory\n200 µs', 0.25, 200)]


def paths(v, sc):
    if v == 'base':
        t = {'particles': 'particles_gcrmin_x100_imx636'}.get(sc, f'{sc}_imx636')
        return DATA / f'{t}_truth.json', DATA / f'{t}_events.npz', DATA / 'energy_calibration_imx636.json'
    t = f'{sc}_imx636_{v}'
    return PS / f'{t}_truth.json', PS / f'{t}_events.npz', PS / f'energy_calibration_imx636_{v}.json'


def scene_row(v, sc):
    pt, pe, pc = paths(v, sc)
    if not pt.exists():
        return None
    d = json.loads(pt.read_text())
    calib = json.loads(pc.read_text()) if pc.exists() else None
    sm, cf = d['summary'], d['config']
    fl = {i: r for i, r in enumerate(sm['per_flash'])}
    raw, cor, out = [], [], 0
    for det in d['detections']:
        if det['label'] != 'flash' or not det.get('energy') or det['energy'].get('censored'):
            continue
        f = fl[det['match']]
        m = det['energy']
        raw.append(math.log(max(m['e_raw_J'], 1e-9) / f['E_J']))
        if calib is not None:
            ec, o = trg.apply_correction(m, calib)
            cor.append(math.log(max(ec, 1e-9) / f['E_J'])); out += int(o)
    raw, cor = np.array(raw), np.array(cor)
    cr = cf['crop']
    return dict(variant=v, scene=sc, tag=pt.name[:-11], code_version=cf['code_version'], overrides=cf['overrides'],
                threshold_model=cf['threshold_model'], calibration=pc.name if calib else None,
                n_flashes=sm['n_flashes'], n_detected=sm['n_detected'], n_false=sm['n_false'],
                n_particle_hits=sm['n_particle_hits'], n_particle_triggers=sm['n_particle_triggers'],
                events_per_px_s=d['stats']['n_events'] / cf['duration_s'] / (cr[2] * cr[3]),
                lag_median_ms=float(np.median([r['lag_s'] for r in sm['per_flash'] if r['detected']]) * 1e3),
                ln_err_raw_median=float(np.median(raw)) if raw.size else None,
                ln_err_raw_rms=float(np.sqrt(np.mean(raw ** 2))) if raw.size else None,
                ln_err_corr_median=float(np.median(cor)) if cor.size else None,
                ln_err_corr_rms=float(np.sqrt(np.mean(cor ** 2))) if cor.size else None,
                n_outside_training_range=out)


def calib_row(v):
    pc = paths(v, 'nearside')[2]
    if not pc.exists():
        return None
    c = json.loads(pc.read_text())
    a, b = c['tests']['a_same_family'], c['tests']['b_double_profile']
    return dict(variant=v, file=pc.name, threshold_model=c.get('threshold_model', 'fixed'), overrides=c['overrides'],
                train_detected_fraction=c['n_train_detected'] / c['n_train_flashes'],
                exp_detected=a['detected'], exp_raw_rms=a['raw']['rms'], exp_corr_rms=a['corrected']['rms'],
                exp_corr_bias=a['corrected']['bias'],
                exp_corr_rms_by_energy={k: v_['corrected']['rms'] for k, v_ in a['by_energy'].items()},
                double_detected=b['detected'], double_corr_rms=b['corrected']['rms'],
                double_corr_rms_by_energy={k: v_['corrected']['rms'] for k, v_ in b['by_energy'].items()})


def main():
    PS.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    cal = [r for r in (calib_row(v) for v, *_ in VARIANTS) if r]
    sce = [r for r in (scene_row(v, s) for v, *_ in VARIANTS for s in SCENES) if r]
    (PS / 'pixel_sensitivity_2026-11-17.json').write_text(json.dumps(dict(
        description='Pixel-parameter sensitivity: contrast threshold (trigger table re-tuned) and refractory period. Model '
                    'predictions; each variant uses its own energy correction. Baseline: C = 0.25, refractory 10 us.',
        variants=[dict(key=k, label=l.replace('\n', ' '), C=c, refractory_us=r) for k, l, c, r in VARIANTS],
        calibration=cal, scenes=sce), indent=1, default=float))

    keys = [k for k, *_ in VARIANTS]; labels = [l for _, l, *_ in VARIANTS]

    def seg(a, ys, fmt, **kw):
        """Threshold group (first five) and refractory group (baseline repeated at 10 us, then 79, 200 us) as separate lines."""
        ys = np.asarray(ys, float)
        a.plot(np.arange(5), ys[:5], fmt, **kw)
        kw.pop('label', None)
        a.plot([5.5, 6.5, 7.5], [ys[2], ys[5], ys[6]], fmt, **kw)
    x = np.arange(len(keys))
    cb = {r['variant']: r for r in cal}
    plt.rcParams.update({'font.size': 8})
    fig, ax = plt.subplots(2, 2, figsize=(12, 7.5))
    a = ax[0, 0]
    seg(a, [cb[k]['exp_corr_rms'] if k in cb else np.nan for k in keys], 'o-', c='#2a78d6', label='exponential, all energies')
    seg(a, [cb[k]['exp_corr_rms_by_energy'].get('1e+06-3e+06') if k in cb else np.nan for k in keys], 's--', c='#2a78d6',
           alpha=.6, label='exponential, 1–3 MJ')
    seg(a, [cb[k]['double_corr_rms'] if k in cb else np.nan for k in keys], 'o-', c='#eb6834', label='two-component, all energies')
    a.set_ylabel('corrected energy error rms [ln]'); a.set_title('(a) lattice energy precision (held-out tests, own correction)', loc='left')
    a.legend(frameon=False)
    a = ax[0, 1]
    seg(a, [100 * cb[k]['exp_detected'][0] / cb[k]['exp_detected'][1] if k in cb else np.nan for k in keys], 'o-', c='#2a78d6', label='exponential test set')
    seg(a, [100 * cb[k]['double_detected'][0] / cb[k]['double_detected'][1] if k in cb else np.nan for k in keys], 'o-', c='#eb6834', label='two-component test set')
    a.set_ylabel('flashes detected [%]'); a.set_title('(b) lattice detection, 10 kJ – 3 MJ', loc='left'); a.legend(frameon=False)
    col = {'nearside': '#2a78d6', 'farside': '#1baf7a', 'terminator': '#eb6834', 'particles': '#6250d6'}
    lab = {'nearside': 'near side', 'farside': 'far side', 'terminator': 'terminator', 'particles': 'particles (GCR ×100)'}
    sb = {(r['variant'], r['scene']): r for r in sce}
    for s in SCENES:
        seg(ax[1, 0], [sb[(k, s)]['ln_err_corr_rms'] if (k, s) in sb else np.nan for k in keys], 'o-', c=col[s], label=lab[s])
        seg(ax[1, 1], [sb[(k, s)]['events_per_px_s'] if (k, s) in sb else np.nan for k in keys], 'o-', c=col[s], label=lab[s])
    ax[1, 0].set_ylabel('corrected energy error rms [ln], 4–8 flashes'); ax[1, 0].set_title('(c) scene energy error (own correction)', loc='left')
    ax[1, 1].set_ylabel('events per px per s'); ax[1, 1].set_yscale('log'); ax[1, 1].set_title('(d) scene event rate', loc='left')
    ax[1, 0].legend(frameon=False); ax[1, 1].legend(frameon=False)
    for a in ax.flat:
        a.set_xticks([0, 1, 2, 3, 4, 5.5, 6.5, 7.5], ['0.15', '0.20', '0.25', '0.30', '0.35', '10 µs', '79 µs', '200 µs'])
        a.set_xlabel('contrast threshold C (refractory 10 µs)              |   refractory period (C = 0.25)')
        a.grid(alpha=.25, lw=.5); a.axvline(4.75, c='#999999', lw=.8)
        for xb in (2, 5.5):
            a.axvspan(xb - 0.3, xb + 0.3, color='#eeeeee', zorder=0)
    fig.suptitle('IMX636 pixel-parameter sensitivity: contrast threshold (trigger re-tuned) and refractory period (model; shaded = baseline)', fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / 'pixel_sensitivity.png', dpi=150); plt.close(fig)

    for r in cal:
        print(f"CAL {r['variant']:10s} det_train {r['train_detected_fraction']:.3f} exp det {r['exp_detected']} rms {r['exp_corr_rms']:.3f} "
              f"(1-3 MJ {r['exp_corr_rms_by_energy'].get('1e+06-3e+06', float('nan')):.3f}) double det {r['double_detected']} rms {r['double_corr_rms']:.3f}")
    for r in sce:
        print(f"SCN {r['variant']:10s} {r['scene']:10s} det {r['n_detected']}/{r['n_flashes']} false {r['n_false']} ptrig {r['n_particle_triggers']}"
              f" ev {r['events_per_px_s']:.4f} lag {r['lag_median_ms']:.0f} ms corr {r['ln_err_corr_median']:+.2f}/{r['ln_err_corr_rms']:.2f}")


if __name__ == '__main__':
    main()
