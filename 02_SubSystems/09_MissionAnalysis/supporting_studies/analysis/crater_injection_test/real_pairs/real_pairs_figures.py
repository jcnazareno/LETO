"""Figures for real_pairs_run.py: figures/crater_injection_test/real_pairs_gallery.png and real_pairs_completeness.png.
Usage: python -I real_pairs_figures.py [windows_dir]   (re-registers the five located pairs; a few minutes)"""
import json, math, os, sys
import numpy as np
from scipy.stats import norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import real_pairs_run as rp                                                  # noqa: E402
ct = rp.ct
BLUE, ORANGE, AQUA, YELLOW, INK, INK2, GRID = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False})
FIG = os.path.join(rp.ROOT, 'figures', 'crater_injection_test')


def gallery(wdir):
    meta = {c['id']: c for c in json.load(open(os.path.join(HERE, 'nac_pairs.json')))['craters']}
    loc = json.load(open(os.path.join(HERE, 'located_craters.json')))['located']
    summ = {r['id']: r for r in json.load(open(os.path.join(rp.ROOT, 'data', 'crater_injection_test', 'real_pairs_summary.json')))['craters']}
    ids = ['C1', 'C3', 'C4', 'C5', 'C7']
    fig, ax = plt.subplots(3, len(ids), figsize=(2.3 * len(ids), 7.2))
    for j, cid in enumerate(ids):
        B, db = rp.load(wdir, cid, 'b'); A, da = rp.load(wdir, cid, 'a'); g = float(db['res']); inc = float(da['inc'])
        B, A, V, _ = rp.register(B, A, g, float(da['res'])); A, _ = rp.refine(B, A, V)
        Bc, Ac, Vc, (r0, c0) = rp.crop_pair(B, A, V)
        cfg = dict(ct.DEFAULTS); cfg['signal_e'] = 300.0 * math.cos(math.radians(inc)) / math.cos(math.radians(65.0))
        rng = np.random.default_rng(3)
        b = ct.degrade(Bc, g, cfg, rng); a = ct.degrade(Ac, g, cfg, rng); Z = rp.anomaly_stat(b, a, cfg)
        L, S = (loc[cid]['line'] - r0) * g / 0.9, (loc[cid]['sample'] - c0) * g / 0.9
        h = int(60 / 0.9); sl = (slice(int(L) - h, int(L) + h), slice(int(S) - h, int(S) + h))
        thr = summ[cid]['anomaly']['threshold']; found = summ[cid]['anomaly']['found']
        for i, (im, ttl) in enumerate(((b[sl], 'before (NAC, as 0.9 m)'), (a[sl], 'after'), (Z[sl], 'anomaly score'))):
            x = ax[i, j]
            if i < 2:
                x.imshow(im, cmap='gray', vmin=np.percentile(im, 1), vmax=np.percentile(im, 99))
            else:
                x.imshow(im, cmap='magma', vmin=0, vmax=max(thr * 1.6, 12))
                x.contour(im, levels=[thr], colors=[AQUA], linewidths=0.8)
            x.set_xticks([]); x.set_yticks([])
            if j == 0:
                x.set_ylabel(ttl, fontsize=8.5)
        ax[0, j].set_title(f"{cid}: D = {meta[cid]['D_m']} m\nfound {found}/4 (threshold {thr:.1f})", fontsize=8.5)
    ax[2, 0].text(0, -0.06, 'Each panel 120 m across, crater at the centre; contour: threshold for 0.01 false candidates per km² in that pair.',
                  transform=ax[2, 0].transAxes, fontsize=7.5, va='top', color=INK2)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'real_pairs_gallery.png'), dpi=170)


def completeness():
    s = json.load(open(os.path.join(rp.ROOT, 'data', 'crater_injection_test', 'real_pairs_summary.json')))
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    Dg = np.exp(np.linspace(math.log(1.5), math.log(8), 200))
    ax.plot(Dg, 0.85 * norm.cdf((np.log(Dg) - math.log(3.5 * 0.9)) / 0.15), color=INK2, ls='--', lw=1.5, label='joint-model placeholder')
    for key, col, lab in (('dark|well_registered', BLUE, 'dark halo (measured type), 3 well-registered pairs'),
                          ('dark|all_registered', AQUA, 'dark halo, all 5 registered pairs'),
                          ('none|well_registered', ORANGE, 'no halo, 3 well-registered pairs')):
        f = s['injection_fit'][key]
        D = np.array([float(k) for k in f['by_D']]); k = np.array([v[0] for v in f['by_D'].values()]); n = np.array([v[1] for v in f['by_D'].values()])
        ax.plot(D, k / n, 'o', color=col, ms=6, mec='white', mew=1)
        ax.plot(Dg, f['c_max'] * norm.cdf((np.log(Dg) - math.log(f['k_pixels'] * 0.9)) / f['width_lnD']), color=col, lw=2, label=lab)
    for r in s['craters']:
        if 'found' in r['anomaly']:
            ax.plot(r['D_m'], r['anomaly']['found'] / r['anomaly']['reps'], marker='*', ms=13, color=YELLOW, mec=INK, mew=0.6, ls='none')
            ax.annotate(r['id'], (r['D_m'], r['anomaly']['found'] / r['anomaly']['reps']), xytext=(5, -10), textcoords='offset points', fontsize=7.5, color=INK2)
    ax.plot([], [], marker='*', ms=11, color=YELLOW, mec=INK, mew=0.6, ls='none', label='real new craters (share of 4 noise repeats)')
    ax.set_xscale('log'); ax.set_xticks([2, 3, 4, 5, 6, 8]); ax.set_xticklabels(['2', '3', '4', '5', '6', '8'])
    ax.set_xlabel('crater diameter D [m]  (0.9 m camera pixels)'); ax.set_ylabel('share found at 0.01 false / km²')
    ax.set_ylim(-0.03, 1.05); ax.grid(True, color=GRID, lw=0.6); ax.legend(frameon=False, fontsize=7.5, loc='upper left')
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'real_pairs_completeness.png'), dpi=200)


if __name__ == '__main__':
    completeness()
    gallery(sys.argv[1] if len(sys.argv) > 1 else os.path.join(rp.ROOT, 'tmp', 'nac_chips', 'windows'))
