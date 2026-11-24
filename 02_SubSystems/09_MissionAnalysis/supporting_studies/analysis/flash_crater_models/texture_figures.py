"""Figure for the measured moving texture (texture_measured.py): figures/lunar_texture/texture_false_triggers.png"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import DATA, ROOT
import event_response as er

BLUE, ORANGE, AQUA, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'


def main():
    h = json.loads((DATA / 'texture_histograms.json').read_text())
    t = json.loads((DATA / 'texture_measured.json').read_text())
    edges = np.array(h['bins']); c = np.sqrt(np.maximum(edges[:-1], 1e-12) * edges[1:])
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'xtick.color': INK2,
                         'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw=dict(width_ratios=[1, 1.35]))
    # (a) share of 2x2 groups whose texture adds more than mu counts in the 2 s window
    a = ax[0]
    for key, col, lab in (('nominal_1.3e4', BLUE, '1.3e4 e$^-$/s'), ('nominal_2.5e4', ORANGE, '2.5e4 e$^-$/s')):
        hist = sum(np.array(h['tiles'][tl][key]['2.0_2']) for tl in h['tiles'])
        f = hist / hist.sum(); ccdf = 1 - np.cumsum(f)
        a.loglog(edges[1:] / 0.25, np.maximum(ccdf, 1e-12), color=col, lw=2, label=f'measured, {lab}')
    s = er.SENSORS['nominal']
    for I0, col in ((1.3e4, BLUE), (2.5e4, ORANGE)):
        m = er.texture_mu(s, I0, 2.0, 2)
        a.plot([m], [0.01], 'o', ms=8, color=col, mec='white', mew=1.5)
    a.annotate('assumed edge\n(contrast 2, 1% of groups)', xy=(er.texture_mu(s, 2.5e4, 2.0, 2), 0.01), xytext=(0.15, 2e-4),
               fontsize=8, color=INK2, arrowprops=dict(arrowstyle='-', color=INK2, lw=0.8))
    a.set_xlim(0.05, 60); a.set_ylim(1e-9, 1.5)
    a.set_xlabel('texture counts added in 2 s, 2x2 group (nominal sensor)'); a.set_ylabel('share of groups exceeding')
    a.grid(True, which='major', color=GRID, lw=0.6); a.legend(frameon=False, fontsize=8, loc='lower left')
    a.set_title('a  Moving texture over the near side (WAC + LOLA)', loc='left', fontsize=9.5, color=INK)
    # (b) false triggers per hour with the adopted thresholds
    b = ax[1]
    keys = [('nominal', 13000.0), ('nominal', 25000.0), ('m636', 13000.0), ('m636', 25000.0), ('m636_tuned', 13000.0), ('m636_tuned', 25000.0)]
    labels = ['nominal\n1.3e4', 'nominal\n2.5e4', 'IMX636\n1.3e4', 'IMX636\n2.5e4', 'IMX636 tuned\n1.3e4', 'IMX636 tuned\n2.5e4']
    get = lambda s_, I0, m: [x for x in t['cases'] if x['sensor'] == s_ and x['I0'] == I0 and x['model'] == m][0]
    series = [('assumed edge (design)', lambda s_, I0: get(s_, I0, 'ramp')['rate_adopted_assumed'], INK2),
              ('measured texture', lambda s_, I0: get(s_, I0, 'ramp')['rate_adopted_measured'], BLUE),
              ('measured, Poisson bound', lambda s_, I0: get(s_, I0, 'poisson')['rate_adopted_measured'], ORANGE)]
    x = np.arange(len(keys)); wdt = 0.26
    for i, (lab, fn, col) in enumerate(series):
        v = [max(fn(*k), 1e-3) for k in keys]
        b.bar(x + (i - 1) * wdt, v, wdt - 0.03, color=col, label=lab, zorder=3)
    b.axhline(1.0, color=INK, lw=1, ls='--', zorder=4); b.text(-0.45, 1.25, 'budget 1/h', ha='left', fontsize=8, color=INK)
    b.set_yscale('log'); b.set_ylim(1e-3, 400); b.set_xticks(x); b.set_xticklabels(labels, fontsize=8)
    b.set_ylabel('false triggers per hour (six heads)'); b.grid(True, axis='y', color=GRID, lw=0.6, zorder=0)
    b.legend(frameon=False, fontsize=8, loc='upper left')
    b.set_title('b  Adopted thresholds, by sensor and background (e$^-$/s)', loc='left', fontsize=9.5, color=INK)
    fig.tight_layout()
    out = ROOT / 'figures' / 'lunar_texture' / 'texture_false_triggers.png'
    fig.savefig(out, dpi=200); print(out)


if __name__ == '__main__':
    main()
