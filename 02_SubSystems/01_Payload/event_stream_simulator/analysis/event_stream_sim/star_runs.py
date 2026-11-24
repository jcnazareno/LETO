"""Stars beyond the limb: effect on the trigger (11 Nov 2026). Compares the limb scene without stars, with the
catalogue stars (default season) and with one test star of V = 1..5, and attributes false triggers to stars.

  python star_runs.py

Inputs: data/limb_imx636_truth.json (catalogue stars) and data/stars/
limb_imx636_nostars / limb_imx636_teststar_V<m> / limb_imx636_teststar_limb_V<m> (_truth.json, _events.npz).
Outputs: data/stars/star_runs_2026-11-11.json, figures/stars/star_runs.png.
A false trigger is attributed to a star when it lies within 4 px of the star's track position at the trigger time.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data'
FIG = ROOT / 'figures' / 'stars'
RUNS = [('no stars', DATA / 'stars' / 'limb_imx636_nostars', None),
        ('catalogue (season 0 deg)', DATA / 'limb_imx636', None)] + \
       [(f'test star V = {m}', DATA / 'stars' / f'limb_imx636_teststar_V{m}', m) for m in (1, 2, 3, 4, 5)] + \
       [(f'limb-crossing star V = {m}', DATA / 'stars' / f'limb_imx636_teststar_limb_V{m}', m) for m in (1, 2, 3, 4, 5)]


def star_pos(st, t, ts):
    tr = np.array([[p[0], p[1], p[2]] for p in st['track_px']], float)
    k = np.clip(np.searchsorted(ts, t) - 1, 0, len(ts) - 2)
    f = (t - ts[k]) / (ts[k + 1] - ts[k])
    x = tr[k, 0] + f * (tr[k + 1, 0] - tr[k, 0]); y = tr[k, 1] + f * (tr[k + 1, 1] - tr[k, 1])
    return x, y, bool(tr[k, 2] or tr[k + 1, 2])


def main():
    rows = []
    for label, base, mag in RUNS:
        p = Path(str(base) + '_truth.json')
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        z = np.load(str(base) + '_events.npz')
        sm = d['summary']; sc = d['scene']; dur = d['config']['duration_s']
        sky = ~np.isfinite(z['range_km'])
        on_sky = sky[z['y'], z['x']]
        cmp_ = z['src'] == 0
        smeta = sc.get('stars') or {}
        ts = np.array(smeta.get('track_t_s', []), float)
        stars = smeta.get('stars', [])
        false = [x for x in d['detections'] if x['label'] == 'false']
        by_star = 0; star_false = []
        for x in false:
            for st in stars:
                sx, sy, vis = star_pos(st, x['t_trig'], ts)
                if vis and np.hypot(sx - x['x'], sy - x['y']) <= 4.0:
                    by_star += 1; star_false.append(dict(t=x['t_trig'], W=x['W'], star=st['src'], V=st['V'])); break
        pf = [r for r in sm['per_flash'] if r['detected'] and not r.get('censored')]
        lc = [r['ln_err_corr'] for r in pf if r.get('ln_err_corr') is not None]
        rows.append(dict(label=label, tag=base.name, test_V=mag, code_version=d['config']['code_version'],
                         stars_in_field=[dict(src=s['src'], V=s['V'], e_s=s['e_s']) for s in stars],
                         n_flashes=sm['n_flashes'], n_detected=sm['n_detected'], n_false=sm['n_false'],
                         n_false_by_star=by_star, false_by_star=star_false,
                         sky_pixel_fraction=float(sky.mean()),
                         sky_event_rate_ev_s_px=float((cmp_ & on_sky).sum()) / dur / max(sky.sum(), 1),
                         ground_event_rate_ev_s_px=float((cmp_ & ~on_sky).sum()) / dur / max((~sky).sum(), 1),
                         ln_err_corr_rms=float(np.sqrt(np.mean(np.square(lc)))) if lc else None))
    FIG.mkdir(parents=True, exist_ok=True); (DATA / 'stars').mkdir(exist_ok=True)
    (DATA / 'stars' / 'star_runs_2026-11-11.json').write_text(json.dumps(dict(
        description='Limb scene (20 s, 6 flashes, ghost stray light) without stars, with BSC5 stars at the default '
                    'season, and with one test star of V = 1..5 at a random sky pixel. Model predictions.',
        runs=rows), indent=1))
    lab = [r['label'] for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    y = np.arange(len(rows))
    ax[0].barh(y, [r['n_false'] for r in rows], color='#c9c8c3', label='all false triggers')
    ax[0].barh(y, [r['n_false_by_star'] for r in rows], color='#eb6834', label='within 4 px of a star')
    ax[0].set_yticks(y, lab); ax[0].invert_yaxis(); ax[0].set_xlabel('false triggers per 20 s run')
    ax[0].legend(fontsize=7, frameon=False); ax[0].grid(alpha=.25, lw=.5, axis='x')
    ax[1].barh(y, [r['sky_event_rate_ev_s_px'] for r in rows], color='#2a78d6')
    ax[1].set_yticks(y, []); ax[1].invert_yaxis(); ax[1].set_xlabel('scene events per sky pixel per s')
    ax[1].grid(alpha=.25, lw=.5, axis='x')
    fig.suptitle('Stars behind the limb: limb crop, IMX636, 20 s (model; V = 0 star ≈ 1.7×10⁶ e⁻/s in 600–900 nm)', fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / 'star_runs.png', dpi=150); plt.close(fig)
    for r in rows:
        print(f"{r['label']:28s} det {r['n_detected']}/{r['n_flashes']} false {r['n_false']} (star {r['n_false_by_star']}) "
              f"sky ev {r['sky_event_rate_ev_s_px']:.4f} ground ev {r['ground_event_rate_ev_s_px']:.4f} "
              f"stars {[(s['src'], s['V']) for s in r['stars_in_field']]}")


if __name__ == '__main__':
    main()
