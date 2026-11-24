"""Pointing-jitter sensitivity (handoff 2026-11-11, item 3.5): collect the sweep runs of run_jitter_sweep_2026-11-11.sh
into data/jitter/jitter_sweep_2026-11-11.json and plot figures/jitter/jitter_sweep.png and
figures/jitter/jitter_sweep_timeseries.png.

  python jitter_sweep.py

Inputs: <scene>_imx636_jitter<rms>[_tc<corr>]_truth.json and _events.npz in data/jitter/.
Event-rate split: 'trigger-active' pixels have a run-mean background below the lit limit (the illumination mask
removes brighter pixels from the trigger); 'lit' pixels are above it. The jitter path is regenerated with the same
generator as geometry.Camera (seed 11, 10 ms grid) to relate event bursts to the angular rate.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data' / 'jitter'
FIG = ROOT / 'figures' / 'jitter'
FIG.mkdir(parents=True, exist_ok=True)
SCENES = ('terminator', 'nearside')
RMS = (0.2, 2, 5, 10, 20, 60)
TC_EXTRA = (0.1, 2.0)
RMS_EXT = (12, 14, 17)                  # terminator only, jitter seed 11
SEEDS_EXT = (12, 13, 14, 15)            # terminator, extra jitter paths
RMS_SEEDS = (5, 10, 14, 20)
PX_ARCSEC = 4.86e-6 / 16e-3 * 206264.806          # 62.65 arcsec per pixel at the centre (16 mm, 4.86 um)
ARCSEC = 1 / 206264.806


def tag(scene, j, tc=0.5, js=11):
    t = f'{scene}_imx636_jitter{str(j).replace(".", "p")}'
    if tc != 0.5:
        t = f'{t}_tc{str(tc).replace(".", "p")}'
    return t if js == 11 else f'{t}_js{js}'


def jitter_path(rms_arcsec, tc, duration, seed=11):
    """Copy of the generator in geometry.Camera.__init__ (radians, both axes)."""
    sig = rms_arcsec * ARCSEC
    rng = np.random.default_rng(seed)
    jt = np.arange(-1.0, duration + 2.0, 0.01)
    a = math.exp(-0.01 / tc) if tc > 0 else 0.0
    jx = np.zeros(len(jt)); jy = np.zeros(len(jt))
    e = rng.normal(0, sig * math.sqrt(1 - a * a), (len(jt), 2))
    jx[0], jy[0] = rng.normal(0, sig, 2)
    for k in range(1, len(jt)):
        jx[k] = a * jx[k - 1] + e[k, 0]; jy[k] = a * jy[k - 1] + e[k, 1]
    return jt, jx, jy


def collect(scene, j, tc, js=11):
    tg = tag(scene, j, tc, js)
    p = DATA / f'{tg}_truth.json'
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    sm, st, cf = d['summary'], d['stats'], d['config']
    dur = cf['duration_s']; lit = cf['lit_limit_e_s']
    z = np.load(DATA / f'{tg}_events.npz')
    h, w = z['bg_mean_e_s'].shape
    active = z['bg_mean_e_s'] < lit
    scene_ev = z['src'] == 0
    on_active = active[z['y'], z['x']]
    det = [r for r in sm['per_flash'] if r['detected'] and not r.get('censored')]
    lr = np.array([r['ln_err_raw'] for r in det]); lc = np.array([r['ln_err_corr'] for r in det if r.get('ln_err_corr') is not None])
    jt, jx, jy = jitter_path(j, tc, dur, seed=js)
    sel = (jt >= 0) & (jt <= dur)
    k5 = 5                                                              # 50 ms = scene keyframe spacing
    vel = np.hypot(jx[k5:] - jx[:-k5], jy[k5:] - jy[:-k5]) / 0.05 / ARCSEC   # arcsec/s over 50 ms
    vsel = (jt[:-k5] >= 0) & (jt[k5:] <= dur)
    ex = d['stats']['exposure']['by_window']
    bg = z['bg_mean_e_s']

    def local_max(x, y, r=4):
        x, y = int(x), int(y)
        return float(bg[max(y - r, 0):y + r + 1, max(x - r, 0):x + r + 1].max())
    dets = {x['match']: x for x in d['detections'] if x['label'] == 'flash'}
    per_flash = []
    for i, f in enumerate(sm['per_flash']):
        e = dets.get(i, {}).get('energy', {})
        per_flash.append(dict(id=i, x=f['x'], y=f['y'], E_J=f['E_J'], tau_s=f['tau_s'], detected=f['detected'],
                              censored=f.get('censored'), ln_err_raw=f.get('ln_err_raw'), ln_err_corr=f.get('ln_err_corr'),
                              active_s=e.get('active_s'), peak=e.get('peak'), npix=e.get('npix'), bg_est=e.get('bg_est'),
                              outside_training_range=f.get('outside_training_range'),
                              max_bg_9x9_e_s=local_max(f['x'], f['y'])))
    false = [dict(t_trig=x['t_trig'], W=x['W'], size=x['size'], x=x['x'], y=x['y'], count=x['count'],
                  bg_e_s=float(bg[int(x['y']), int(x['x'])]), max_bg_9x9_e_s=local_max(x['x'], x['y']))
             for x in d['detections'] if x['label'] == 'false']
    return dict(
        tag=tg, scene=scene, jitter_rms_arcsec=j, jitter_rms_px=j / PX_ARCSEC, jitter_corr_s=tc, jitter_seed=js,
        code_version=cf['code_version'], command=cf['command'], duration_s=dur, crop=cf['crop'],
        n_flashes=sm['n_flashes'], n_detected=sm['n_detected'], n_false=sm['n_false'],
        n_detections=sm['n_detections'], n_trigger_rows=st['n_trigger_rows'],
        n_events=st['n_events'], n_on=st['n_on'], n_off=st['n_off'], n_ba=st['n_ba'],
        event_rate_ev_s_px=st['n_events'] / dur / (w * h),
        scene_event_rate_ev_s_px=float(scene_ev.sum()) / dur / (w * h),
        active_pixel_fraction=float(active.mean()),
        active_event_rate_ev_s_px=float((scene_ev & on_active).sum()) / dur / max(active.sum(), 1),
        lit_event_rate_ev_s_px=float((scene_ev & ~on_active).sum()) / dur / max((~active).sum(), 1),
        disabled_2x2_fraction_W50ms=ex['0.05']['disabled_2x2_anchor_fraction'],
        ln_err_raw_mean=float(lr.mean()) if len(lr) else None, ln_err_raw_rms=float(np.sqrt((lr ** 2).mean())) if len(lr) else None,
        ln_err_corr_mean=float(lc.mean()) if len(lc) else None, ln_err_corr_rms=float(np.sqrt((lc ** 2).mean())) if len(lc) else None,
        n_flash_abs_ln_err_corr_gt_1=int(sum(1 for r in per_flash if r['ln_err_corr'] is not None and abs(r['ln_err_corr']) > 1)),
        realised_jitter_rms_arcsec_per_axis=float(np.sqrt(0.5 * (jx[sel] ** 2 + jy[sel] ** 2).mean()) / ARCSEC),
        realised_jitter_rate_rms_arcsec_s=float(np.sqrt((vel[vsel] ** 2).mean())),
        realised_jitter_rate_max_arcsec_s=float(vel[vsel].max()),
        per_flash=per_flash, false_triggers=false,
    )


def timeseries(scene, j, tc=0.5, bin_s=0.05):
    tg = tag(scene, j, tc)
    z = np.load(DATA / f'{tg}_events.npz')
    d = json.loads((DATA / f'{tg}_truth.json').read_text())
    dur, lit = d['config']['duration_s'], d['config']['lit_limit_e_s']
    h, w = z['bg_mean_e_s'].shape
    active = z['bg_mean_e_s'] < lit
    m = (z['src'] == 0) & active[z['y'], z['x']]
    edges = np.arange(0, dur + 1e-9, bin_s)
    n, _ = np.histogram(z['t_us'][m] * 1e-6, edges)
    return edges[:-1] + bin_s / 2, n / bin_s / max(active.sum(), 1)


def onset(rows):
    """Terminator, tau_c 0.5 s: false triggers per amplitude over all jitter paths."""
    out = []
    for j in sorted({r['jitter_rms_arcsec'] for r in rows if r['scene'] == 'terminator' and r['jitter_corr_s'] == 0.5}):
        rr = [r for r in rows if r['scene'] == 'terminator' and r['jitter_corr_s'] == 0.5 and r['jitter_rms_arcsec'] == j]
        nf = [r['n_false'] for r in rr]
        out.append(dict(jitter_rms_arcsec=j, n_paths=len(rr), seeds=[r['jitter_seed'] for r in rr], n_false=nf,
                        mean_false=float(np.mean(nf)), paths_with_false=int(sum(n > 0 for n in nf)),
                        rate_rms_arcsec_s=[r['realised_jitter_rate_rms_arcsec_s'] for r in rr],
                        flashes_abs_ln_err_gt_1=[r['n_flash_abs_ln_err_corr_gt_1'] for r in rr]))
    return out


def main():
    rows = []
    for s in SCENES:
        for j in RMS:
            r = collect(s, j, 0.5)
            if r: rows.append(r)
        for tc in TC_EXTRA:
            r = collect(s, 10, tc)
            if r: rows.append(r)
    for j in RMS_EXT:
        r = collect('terminator', j, 0.5)
        if r: rows.append(r)
    for js in SEEDS_EXT:
        for j in RMS_SEEDS:
            r = collect('terminator', j, 0.5, js)
            if r: rows.append(r)
    for s in SCENES:          # relative change against the 0.2 arcsec run of the same code
        base = next((r for r in rows if r['scene'] == s and r['jitter_rms_arcsec'] == 0.2), None)
        for r in rows:
            if base and r['scene'] == s:
                r['event_rate_rel_to_0p2'] = r['n_events'] / base['n_events']
                r['active_event_rate_rel_to_0p2'] = r['active_event_rate_ev_s_px'] / base['active_event_rate_ev_s_px']
    out = dict(
        description='Pointing-jitter sensitivity of the event-stream model (handoff 2026-11-11 item 3.5). Model '
                    'predictions for the recorded configurations; jitter amplitude and correlation time are assumptions.',
        generated='2026-11-11', script='analysis/event_stream_sim/jitter_sweep.py',
        runs_script='analysis/event_stream_sim/run_jitter_sweep_2026-11-11.sh',
        conventions=dict(pixel_scale_arcsec=PX_ARCSEC, jitter_model='first-order Gauss-Markov per image axis, seed 11, '
                         'same path scaled by the rms', keyframe_s=0.05,
                         active_pixels='run-mean background below the lit limit (trigger-active)',
                         energy_errors='complete (uncensored) records of detected flashes; ln(E_est/E_true)'),
        runs=rows, onset=onset(rows))
    (DATA / 'jitter_sweep_2026-11-11.json').write_text(json.dumps(out, indent=1, default=float))

    # ---- figure 1: sweep summary (six panels) ----
    col = {'terminator': '#eb6834', 'nearside': '#2a78d6'}
    lab = {'terminator': 'terminator', 'nearside': 'near side'}
    tcm = {0.1: '^', 2.0: 'v'}
    plt.rcParams.update({'font.size': 8, 'axes.edgecolor': '#888888', 'axes.labelcolor': '#0b0b0b',
                         'xtick.color': '#52514e', 'ytick.color': '#52514e'})
    fig, ax = plt.subplots(2, 3, figsize=(14, 8.2))
    A = ax.flat

    def sec_px(a):
        a.set_xscale('log'); a.grid(alpha=.25, which='both', lw=.5)
        a.axvline(0.2, c='#999999', ls=':', lw=1)
        a.secondary_xaxis('top', functions=(lambda v: v / PX_ARCSEC, lambda v: v * PX_ARCSEC)).set_xlabel('jitter rms [px]', color='#52514e')
        a.set_xlabel('jitter rms per axis [arcsec]')

    for s in SCENES:
        rr = sorted([r for r in rows if r['scene'] == s and r['jitter_corr_s'] == 0.5 and r['jitter_seed'] == 11],
                    key=lambda r: r['jitter_rms_arcsec'])
        xt = [r for r in rows if r['scene'] == s and r['jitter_corr_s'] != 0.5]
        if not rr: continue
        x = [r['jitter_rms_arcsec'] for r in rr]
        # (a) event rate in trigger-active pixels
        A[0].plot(x, [r['active_event_rate_ev_s_px'] for r in rr], 'o-', c=col[s], lw=2, ms=6, label=f'{lab[s]}, trigger-active px')
        if any(r['lit_event_rate_ev_s_px'] > 0 for r in rr):
            A[0].plot(x, [r['lit_event_rate_ev_s_px'] for r in rr], 's--', c=col[s], lw=1.2, ms=5, alpha=.7, label=f'{lab[s]}, lit (masked) px')
        for r in xt:
            A[0].plot(r['jitter_rms_arcsec'], r['active_event_rate_ev_s_px'], tcm[r['jitter_corr_s']], c=col[s], mfc='white', ms=8, mew=1.5)
        # (b) collapse on the angular rate
        for r in rr + xt:
            A[1].plot(r['realised_jitter_rate_rms_arcsec_s'], r['active_event_rate_rel_to_0p2'],
                      tcm.get(r['jitter_corr_s'], 'o'), c=col[s], mfc='white' if r['jitter_corr_s'] != 0.5 else col[s], ms=7, mew=1.5)
        A[1].plot(sorted(r['realised_jitter_rate_rms_arcsec_s'] for r in rr),
                  [r['active_event_rate_rel_to_0p2'] for r in sorted(rr, key=lambda r: r['realised_jitter_rate_rms_arcsec_s'])],
                  '-', c=col[s], lw=1, alpha=.6, label=lab[s])
        # (c) false triggers
        A[2].plot(x, [max(r['n_false'], 0.5) for r in rr], 'o-', c=col[s], lw=2, ms=6, label=f'{lab[s]}, jitter path 11')
        if s == 'terminator':
            on = onset(rows)
            for o in on:
                for js, nf in zip(o['seeds'], o['n_false']):
                    if js != 11:
                        A[2].plot(o['jitter_rms_arcsec'] * (1 + 0.03 * (js - 13.5)), max(nf, 0.5), 'o', c=col[s], mfc='white', ms=5, mew=1)
            multi = [o for o in on if o['n_paths'] > 1]
            if multi:
                A[2].plot([o['jitter_rms_arcsec'] for o in multi], [max(o['mean_false'], 0.5) for o in multi], 's--', c='#7a3412',
                          lw=1.2, ms=5, label='terminator, mean over 5 jitter paths')
                A[2].plot([], [], 'o', c=col[s], mfc='white', ms=5, label='terminator, other jitter paths')
        for r in xt:
            A[2].plot(r['jitter_rms_arcsec'], max(r['n_false'], 0.5), tcm[r['jitter_corr_s']], c=col[s], mfc='white', ms=8, mew=1.5)
        # (d) raw trigger rows
        A[3].plot(x, [r['n_trigger_rows'] for r in rr], 'o-', c=col[s], lw=2, ms=6, label=lab[s])
        for r in xt:
            A[3].plot(r['jitter_rms_arcsec'], r['n_trigger_rows'], tcm[r['jitter_corr_s']], c=col[s], mfc='white', ms=8, mew=1.5)
        # (e) per-flash corrected energy errors; (f) record active time
        off = {'terminator': 1.06, 'nearside': 0.94}[s]
        for r in rr:
            for f in r['per_flash']:
                if f['ln_err_corr'] is None: continue
                near_lit = f['max_bg_9x9_e_s'] > 1e5
                A[4].plot(r['jitter_rms_arcsec'] * off, f['ln_err_corr'], 'D' if near_lit else 'o', c=col[s],
                          mfc=col[s] if near_lit else 'white', ms=5, mew=1.2, alpha=.85)
                A[5].plot(r['jitter_rms_arcsec'] * off, f['active_s'], 'D' if near_lit else 'o', c=col[s],
                          mfc=col[s] if near_lit else 'white', ms=5, mew=1.2, alpha=.85)
    for a in (A[0], A[2], A[3], A[4], A[5]):
        sec_px(a)
    A[0].set_yscale('log'); A[0].set_ylabel('scene event rate [ev s⁻¹ px⁻¹]')
    A[0].plot([], [], '^', c='#52514e', mfc='white', label='τc = 0.1 s (10″)'); A[0].plot([], [], 'v', c='#52514e', mfc='white', label='τc = 2 s (10″)')
    A[0].legend(fontsize=7, frameon=False); A[0].set_title('(a) scene event rate', loc='left', fontsize=9)
    A[1].set_xscale('log'); A[1].set_yscale('log'); A[1].grid(alpha=.25, which='both', lw=.5)
    A[1].set_yticks([1, 1.5, 2, 3, 4, 6, 8]); A[1].yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%g')); A[1].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    A[1].set_xlabel('rms jitter rate over 50 ms (keyframe step) [arcsec s⁻¹]'); A[1].set_ylabel('active-pixel event rate / rate at 0.2″')
    A[1].plot([], [], 'o', c='#52514e', label='τc = 0.5 s'); A[1].plot([], [], '^', c='#52514e', mfc='white', label='τc = 0.1 s')
    A[1].plot([], [], 'v', c='#52514e', mfc='white', label='τc = 2 s')
    A[1].legend(fontsize=7, frameon=False); A[1].set_title('(b) same data against angular rate: τc variants collapse', loc='left', fontsize=9)
    A[2].set_yscale('log'); A[2].set_ylim(0.35, 100); A[2].set_ylabel('false triggers per 20 s run (0 plotted at 0.5)')
    A[2].axhline(0.5, c='#bbbbbb', lw=.8); A[2].legend(fontsize=7, frameon=False); A[2].set_title('(c) false triggers (all at lit/dark edges)', loc='left', fontsize=9)
    A[3].set_ylabel('raw trigger rows before grouping'); A[3].legend(fontsize=7, frameon=False); A[3].set_title('(d) trigger load', loc='left', fontsize=9)
    A[4].set_yscale('symlog', linthresh=1); A[4].set_yticks([-6, -3, -1, -0.5, 0, 0.5, 1, 3, 9]); A[4].yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%g')); A[4].axhspan(-0.5, 0.5, color='#dddddd', alpha=.5, lw=0)
    A[4].set_ylabel('per-flash ln(E_corr / E_true)'); A[4].set_title('(e) energy error per flash (8 flashes, all detected)', loc='left', fontsize=9)
    A[4].plot([], [], 'D', c='#52514e', label='lit terrain (>10⁵ e⁻/s) within 4 px'); A[4].plot([], [], 'o', c='#52514e', mfc='white', label='no lit terrain within 4 px')
    A[4].legend(fontsize=7, frameon=False, loc='upper left')
    A[5].set_ylabel('energy record active time [s]'); A[5].set_ylim(0, 4.3); A[5].set_title('(f) energy-record active time (4 s = full)', loc='left', fontsize=9)
    fig.suptitle('Pointing-jitter sweep: IMX636, 320 × 180 px crop, 20 s, 8 flashes per run, code ' + '/'.join(sorted({r['code_version'] for r in rows})) + ' '
                 '(model predictions; τc = 0.5 s unless marked; dotted line = baseline 0.2″; 1 px = 62.7″)', fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / 'jitter_sweep.png', dpi=150); plt.close(fig)

    # ---- figure 2: event-rate time series and the jitter angular rate (no twin axes) ----
    fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True, gridspec_kw=dict(height_ratios=[1, 1, 0.7]))
    for a, s in zip(ax, SCENES):
        for j, c in ((60, '#0b0b0b'), (20, '#8a8985'), (0.2, '#c9c8c3')):
            if not (DATA / f'{tag(s, j)}_truth.json').exists(): continue
            t, r = timeseries(s, j)
            a.plot(t, r, c=c, lw=1, label=f'{j}″ rms')
        a.set_ylabel('scene events, trigger-active px\n[ev s⁻¹ px⁻¹], 50 ms bins'); a.set_yscale('log')
        a.set_title(lab[s], loc='left', fontsize=9); a.grid(alpha=.25, lw=.5)
        a.legend(loc='upper right', fontsize=7, frameon=False, ncol=3)
    jt, jx, jy = jitter_path(60, 0.5, 20.0)
    k5 = 5
    v = np.hypot(jx[k5:] - jx[:-k5], jy[k5:] - jy[:-k5]) / 0.05 / ARCSEC / PX_ARCSEC
    tm = 0.5 * (jt[k5:] + jt[:-k5]); k = (tm >= 0) & (tm <= 20)
    ax[2].plot(tm[k], v[k], c='#eb6834', lw=1)
    ax[2].set_ylabel('jitter rate at 60″ rms\n[px s⁻¹], 50 ms differences'); ax[2].grid(alpha=.25, lw=.5)
    ax[2].set_title('pointing jitter angular rate (20″ run: same path × 1/3; 0.2″: × 1/300)', loc='left', fontsize=9)
    ax[-1].set_xlabel('time [s]')
    fig.suptitle('Scene events in trigger-active pixels over time (model; same Gauss-Markov path scaled, τc = 0.5 s; '
                 'first ≈2 s: initial-reference transient)', fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / 'jitter_sweep_timeseries.png', dpi=150); plt.close(fig)

    hdr = ('tag', 'rms″', 'τc', 'det', 'false', 'trig rows', 'ev/s/px all', 'active', 'lit', 'ln_err_corr rms')
    print(' | '.join(hdr))
    for r in rows:
        print(f"{r['tag']} | {r['jitter_rms_arcsec']} | {r['jitter_corr_s']} | {r['n_detected']}/{r['n_flashes']} | {r['n_false']} | "
              f"{r['n_trigger_rows']} | {r['event_rate_ev_s_px']:.4f} | {r['active_event_rate_ev_s_px']:.4f} | "
              f"{r['lit_event_rate_ev_s_px']:.4f} | {r['ln_err_corr_rms']}")


if __name__ == '__main__':
    main()
