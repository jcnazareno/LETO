"""Moving lunar texture from LROC WAC albedo and LOLA topography (pre-SRR follow-up, 3 November 2026).

The event-camera trigger thresholds of event_response.py (version 4) include a DECLARED texture term: a
moving albedo edge of contrast 2 in 1% of all trigger groups (review F02). This script replaces that
assumption by a measured distribution and asks what changes.

Input: data/flash_crater_models/texture_histograms.json, made on the team computer by texture_map.py
from the WAC Hapke-normalised 643 nm mosaic (399 m pixels, three tiles covering 70 S - 70 N, 0-90 E and
270-360 E, i.e. the whole near side) and LOLA LDEM_64 (474 m). For every 0.9 km event-camera pixel the
earthshine radiance is modelled as albedo x Lunar-Lambert shading for the Earth direction (sub-Earth point
0 N 0 E, Earth >10 deg above the horizon), the background is B = dark + earthshine, and the along-track
drift of 0.41 px/s gives per window W the clipped log-intensity rise of each pixel; the histogram is of the
group sum S = sum(max(0, d ln B)) over 2x2 and 3x3 groups (both drift directions).

Counts added by texture: mu = S / C per group. Three count models:
  * 'poisson': Poisson(mu) added to the null group sum (as in event_response.group_tail_plus; bounding);
  * 'ramp'   : per pixel (equal shares m = mu / npx) sub-Poisson Binomial(N, m/N), N = max(m / (1 - KAPPA),
               floor(m) + 1): variance about KAPPA * mu (KAPPA = 0.35) for large mu, and every pixel can fire
               one event more than its share for small mu. A contrast-threshold
               pixel on a slow, smooth rise fires almost deterministically; ramp_check() simulates the
               version-4 pixel model (shot noise, photoreceptor, threshold spread, BA, 1% loss) under a
               log-linear ramp and finds an added variance of 0.06-0.29 x mu (adopted model);
  * 'phase'  : each pixel fires floor(m + U) events with a random reference phase U (lower bound).
The texture count of each pixel is added to its null count (the version-4 per-pixel majorant), and the trigger
rule (group sum >= n_min with >= 3 pixels contributing) is applied exactly, as in event_response.group_tail.
Outputs (data/flash_crater_models/texture_measured.json):
  1. false triggers per hour with the adopted (version-4) thresholds, for the measured texture;
  2. texture-aware thresholds that meet the 1-per-hour budget with the measured texture;
  3. map-based masking: the share of groups that would have to be excluded per window (predicted from the
     map on board) to keep the adopted thresholds;
  4. flash detection with the texture-aware thresholds, on the SAME simulated flashes as the stored
     version-4 cases (seeds reproduced), for the affected sensors and backgrounds;
  5. the Option A yield with the texture-aware detection tables (same population and Monte Carlo as
     sensor_trade.py), without changing joint_model.json or event_response.json.

Usage: python texture_measured.py            (all steps; about 40 minutes)
       python texture_measured.py yields     (step 5 only, from the stored detection results)
"""
import sys
import json
import math
import numpy as np
from scipy.stats import poisson, binom
import event_response as er
from common import save_json, load_json, DATA

HIST = DATA / 'texture_histograms.json'
# histogram key -> (dark e-/s, I0 e-/s); dark families: 1.0 fA (6242), 1.1 fA (6866), 5.55 fA (34644)
HKEYS = {(6242, 13000): 'nominal_1.3e4', (6242, 25000): 'nominal_2.5e4', (6866, 13000): 'm636_1.3e4',
         (6866, 25000): 'm636_2.5e4', (34644, 40000): 'pess_4e4', (34644, 60000): 'pess_6e4'}
SENS = ['nominal', 'pessimistic', 'warm_dark', 'ba_hetero', 'm636', 'm636_tuned', 'm636_warm', 'm646_surrogate']
KCAP = 1200
KAPPA = 0.35           # texture count variance / mean ('ramp' model), from ramp_check()
EPS_MU = 0.02          # groups below this mean texture count are treated as texture-free (stored null formula)


def load_hist():
    h = json.loads(HIST.read_text())
    edges = np.array(h['bins'])
    out = {}
    for key in set(HKEYS.values()):
        acc = {}
        for tile in h['tiles']:
            for wk, v in h['tiles'][tile][key].items():
                acc[wk] = acc.get(wk, 0) + np.array(v, float)
        out[key] = acc
    return edges, out, h


def centres(edges):
    c = np.sqrt(np.maximum(edges[:-1], 1e-12) * edges[1:])
    c[0] = 0.0
    return c


def tex_pmf_px(m, model, cap=300):
    """Per-pixel count PMF added by texture of mean m (= group mean / npx; equal shares within a group)."""
    k = np.arange(cap + 1)
    if model == 'poisson':
        return poisson.pmf(k, m)
    fl = int(math.floor(m)); fr = m - fl
    if model == 'phase':
        p = np.zeros(cap + 1); p[fl] += 1 - fr; p[fl + 1] += fr
        return p
    if model == 'ramp':
        # Binomial(N, m/N): every pixel can fire one event more than its share (as in 'phase') and the
        # variance is at least about KAPPA*m for large m (ramp_check)
        N = max(int(math.ceil(m / (1 - KAPPA))), fl + 1)
        return binom.pmf(k, N, m / N)
    raise ValueError(model)


def tail_array(pp, npx, kmin=3):
    """T[n] = P(sum of npx iid pixel counts >= n and >= kmin pixels non-zero), for all n (exact, no truncation)."""
    p0 = pp[0]; pnz = pp.copy(); pnz[0] = 0.0
    conv = np.array([1.0]); tot = np.zeros(len(pp) * npx + 1)
    for k in range(1, npx + 1):
        conv = np.convolve(conv, pnz)
        if k >= kmin:
            w = math.comb(npx, k) * p0 ** (npx - k)
            tot[:len(conv)] += w * conv
    return np.concatenate([np.cumsum(tot[::-1])[::-1], [0.0]])


class GroupTail:
    """Tail P(group count >= n, >= 3 pixels non-zero) for the mixture over texture bins: per bin, each pixel's
    count is the null count (PMF p, the version-4 majorant) plus its share of the texture count."""

    def __init__(self, p, npx, mus, f, model):
        self.npx = npx
        self.T_null = tail_array(np.asarray(p, float), npx)
        sel = np.nonzero((mus >= EPS_MU) & (f > 0))[0]
        self.sel, self.mus, self.f = sel, mus, f
        self.f_tex = float(f[sel].sum())
        L = len(self.T_null) + 400 * npx
        self.Tb = np.zeros((len(sel), L))
        for i, b in enumerate(sel):
            t = np.convolve(p, tex_pmf_px(mus[b] / npx, model))
            T = tail_array(t, npx)
            self.Tb[i, :min(L, len(T))] = T[:L]
        self.T = np.zeros(L); self.T[:len(self.T_null)] = (1 - self.f_tex) * self.T_null
        self.T += f[sel] @ self.Tb

    def tail(self, n):
        return float(self.T[n]) if n < len(self.T) else 0.0

    def tail_masked(self, n, mu_cut):
        """Tail with all groups of texture mean above mu_cut excluded (not tested)."""
        keep = self.mus[self.sel] <= mu_cut
        t = (1 - self.f_tex) * (self.T_null[n] if n < len(self.T_null) else 0.0)
        return float(t + (self.f[self.sel][keep] @ self.Tb[keep, n] if keep.any() and n < self.Tb.shape[1] else 0.0))


def sensor_dark(sname):
    return int(round(er.dark_e(er.SENSORS[sname]['dark_fA'])))


def seeds_for(sname):
    """Reproduce the seed sequence of event_response.main() for this sensor: {I0: (thr_seed, [sim seeds])}."""
    I0_GRID = (2e3, 6.5e3, 1.3e4, 2.5e4, 4e4, 6e4)
    sens = er.SENSORS[sname]
    seed = 100 + 7919 * (list(er.SENSORS).index(sname) + 1)
    out = {}
    for I0 in I0_GRID:
        if I0 < 0.95 * er.dark_e(sens['dark_fA']) or (I0 > 4.5e4 and er.dark_e(sens['dark_fA']) < 2e4):
            continue
        ts = seed; seed += 1
        sims = []
        for _ in range(4):
            sims.append(seed); seed += 1
        out[I0] = (ts, sims)
    return out


def analyse_case(sname, I0, edges, hist, model):
    sens = er.SENSORS[sname]
    key = HKEYS[(sensor_dark(sname), int(I0))]
    mus_S = centres(edges)
    seeds = seeds_for(sname)
    thr = er.thresholds(I0, sens, rng=np.random.default_rng(seeds[I0][0]))
    nt = er.tests_per_hour(sens.get('n_heads', 6))
    rows, new_thr = [], {}
    rate_adopted = rate_assumed = 0.0
    for W in er.WINDOWS:
        p = thr[W]['env']
        new_thr[W] = dict(thr[W])
        for size in (2, 3):
            npx = size * size
            h = hist[key][f'{W}_{size}']
            f = h / h.sum()
            mus = mus_S / sens['C']
            gt = GroupTail(p, npx, mus, f, model)
            n_ad = thr[W]['n_min'] if size == 2 else thr[W]['n_min3']
            ntests = sens.get('n_heads', 6) * 1280 * 720 * 3600.0 / (W / 5)
            r_ad = ntests * gt.tail(n_ad)
            mu_as = er.texture_mu(sens, I0, W, size)
            r_as = ntests * ((1 - 0.01) * er.group_tail(p, n_ad, npx=npx) + 0.01 * er.group_tail_plus(p, n_ad, npx, mu_as))
            rate_adopted += r_ad; rate_assumed += r_as
            # texture-aware threshold (budget 1/nt per test, as in event_response.thresholds)
            n = 3
            while gt.tail(n) > 1.0 / nt and n < er.NMAX:
                n += 1
            n_tex = n if n < er.NMAX else 10**6
            # map-based masking at the adopted threshold: largest mu_cut that meets the budget
            order = np.argsort(mus)
            cuts = mus[order][f[order] > 0]
            lo, hi = 0, len(cuts) - 1
            if gt.tail(n_ad) <= 1.0 / nt:
                mu_cut, masked = float('inf'), 0.0
            else:
                while lo < hi:                       # binary search over the sorted bin centres
                    mid = (lo + hi + 1) // 2
                    if gt.tail_masked(n_ad, cuts[mid]) <= 1.0 / nt:
                        lo = mid
                    else:
                        hi = mid - 1
                mu_cut = float(cuts[lo]); masked = float(f[mus > mu_cut].sum())
            cdf = np.cumsum(f)
            rows.append(dict(W=W, size=size, n_min_adopted=int(n_ad), n_min_texture=int(n_tex),
                             rate_adopted_measured=float(r_ad), rate_adopted_assumed=float(r_as),
                             mu_p99=float(mus[np.searchsorted(cdf, 0.99)]), mu_p999=float(mus[np.searchsorted(cdf, 0.999)]),
                             mu_p9999=float(mus[min(len(mus) - 1, np.searchsorted(cdf, 0.9999))]),
                             mu_assumed_edge=float(mu_as), mask_mu_cut=mu_cut, mask_fraction=masked))
            new_thr[W]['n_min' if size == 2 else 'n_min3'] = int(n_tex)
    return dict(sensor=sname, I0=I0, model=model, rate_adopted_measured=rate_adopted, rate_adopted_assumed=rate_assumed,
                rows=rows), thr, new_thr


def redetect(sname, I0, thr_old, thr_sets, stored_cases):
    """Simulate the stored version-4 flashes again (same seeds) and detect with the adopted and the new
    threshold sets (thr_sets: {label: thresholds})."""
    sens = er.SENSORS[sname]
    E_GRID = np.array((2e3, 5e3, 1e4, 2e4, 4e4, 1e5, 3e5, 1e6, 3e6)); TAU_GRID = (0.03, 0.1, 0.3, 1.0); per = 40
    _, sims = seeds_for(sname)[I0]
    out = []
    for tau_f, sd in zip(TAU_GRID, sims):
        E = np.repeat(E_GRID, per)
        r = er.simulate(E, tau_f, I0, sens, trials=len(E), rng=np.random.default_rng(sd))
        m0 = er.detect_and_measure(r, thr_old)
        mm = {lab: er.detect_and_measure(r, t) for lab, t in thr_sets.items()}
        for j, Ej in enumerate(E_GRID):
            sl = slice(j * per, (j + 1) * per)
            st = [c for c in stored_cases if c['sensor'] == sname and c['I0'] == I0 and c['tau_f_s'] == tau_f and c['E_L_J'] == float(Ej)]
            row = dict(sensor=sname, I0=I0, tau_f_s=tau_f, E_L_J=float(Ej), n=per, k_adopted=int(m0['det'][sl].sum()),
                       k_stored=st[0]['k_detect'] if st else None)
            row.update({f'k_{lab}': int(m['det'][sl].sum()) for lab, m in mm.items()})
            out.append(row)
        print('  redetect', sname, I0, tau_f, [(r_['E_L_J'], r_['k_stored'], r_['k_adopted'], *[r_[f'k_{l}'] for l in thr_sets])
                                               for r_ in out[-9:]], flush=True)
    return out


def yields(er_json, names, pop):
    import joint_model as jm
    res = {}
    for s in names:
        tab = jm.DetTable(er_json, s)
        pf = jm.p_flash(pop, tab, s)
        phi = jm.PHI_25MM if '25mm' in s else jm.PHI_3000
        yt = jm.yield_terms(pop, pf, phi=phi)
        jm.RNG = np.random.default_rng(20261113)          # common random numbers for all tables
        mcA = jm.mc(pop, pf, phi=phi)
        res[s] = dict(flash_eff_confirmable=jm.flash_eff_confirmable(pop, pf), deterministic_pairs_2p5yr=yt['pairs'] * jm.YEARS,
                      mc_median=mcA['total_p50'], mc_p10=mcA['total_p10'], P_ge_80=mcA['P_ge_80'])
    return res


def tables(store, detection, labels):
    """Detection tables with the texture-aware thresholds: stored counts plus the same-sample change."""
    mod = {l: json.loads(json.dumps(store)) for l in labels}
    idx = {(d['sensor'], d['I0'], d['tau_f_s'], d['E_L_J']): d for d in detection}
    for l in labels:
        for c in mod[l]['cases']:
            d = idx.get((c['sensor'], c['I0'], c['tau_f_s'], c['E_L_J']))
            if d is not None and f'k_{l}' in d:
                k = int(min(c['n_trials'], max(0, c['k_detect'] + d[f'k_{l}'] - d['k_adopted'])))
                c['k_detect'] = k; c['p_detect'] = k / c['n_trials']
    return mod


def yield_step():
    """Option A yields for the adopted and texture-aware tables (population built once, as in joint_model.main)."""
    import joint_model as jm
    pop = jm.population(400_000, jm.ALPHA * jm.S_NOM)          # first use of jm.RNG: identical to joint_model.main()
    store = load_json('event_response.json'); out = load_json('texture_measured.json')
    mod = tables(store, out['detection'], LABELS)
    out['yield'] = {'adopted': yields(store, SENS, pop), **{l: yields(mod[l], SENS, pop) for l in LABELS}}
    for s in SENS:
        a = out['yield']['adopted'][s]
        print(f"{s:16s} adopted {a['deterministic_pairs_2p5yr']:.0f} (MC median {a['mc_median']:.0f}, P10 {a['mc_p10']:.0f}) | " +
              ' | '.join(f"{lab} {out['yield'][lab][s]['deterministic_pairs_2p5yr']:.0f} ({out['yield'][lab][s]['mc_median']:.0f}, "
                         f"{out['yield'][lab][s]['mc_p10']:.0f})" for lab in LABELS), flush=True)
    save_json('texture_measured.json', out)


def ramp_check(cases=(('nominal', 2.5e4), ('m636', 2.5e4)), W=2.0, S_px=(0.0, 0.47, 1.0, 1.9), P=20000, warm=1.0):
    """Version-4 pixel model under a log-linear background ramp of S_px (ln units) during the window W:
    mean and variance of the clipped ON count of 2x2 groups, against the texture mean mu = 4 S_px / C."""
    from scipy.stats import norm
    out = []
    for sname, I0 in cases:
        sens = er.SENSORS[sname]
        for Sp in S_px:
            rng = np.random.default_rng(1); DT = er.DT
            n_w = int(round(warm / DT)); n = n_w + int(round(W / DT)); g = Sp / W
            C = np.clip(rng.normal(sens['C'], 0.03, P), 0.08, None)
            J = np.full(P, float(I0)); ref = np.log(J)
            r_pix = np.full(P, sens['r_ba']); masked = np.zeros(P, bool)
            if sens.get('ba_sigma', 0) > 0:
                sg = sens['ba_sigma']; x = rng.normal(-sg * sg / 2, sg, P); r_pix = r_pix * np.exp(x)
                if sens.get('ba_mask', 0) > 0:
                    masked = (x + sg * sg / 2) / sg > norm.ppf(1 - sens['ba_mask'])
            cnt = np.zeros(P, int)
            for k in range(n):
                Ib = I0 * math.exp(g * max(0.0, (k - n_w) * DT))
                counts = rng.poisson(Ib * DT, P).astype(float)
                J += (DT / er.tau_of(J, sens)) * (counts / DT - J)
                V = np.log(np.maximum(J, 1.0))
                up = V - ref >= C; dn = ref - V >= C
                n_on = np.zeros(P, np.int16)
                while up.any() or dn.any():
                    keep = rng.random(P) > 0.01
                    ref[up] += C[up]; ref[dn] -= C[dn]
                    n_on += (up & keep)
                    up = V - ref >= C; dn = ref - V >= C
                n_on += rng.poisson(r_pix * DT).astype(np.int16)
                n_on[masked] = 0
                if k >= n_w:
                    cnt += np.minimum(n_on, 1)
            g4 = cnt[:(P // 4) * 4].reshape(-1, 4).sum(1)
            out.append(dict(sensor=sname, I0=I0, W=W, S_px=Sp, mu=4 * Sp / sens['C'], mean_2x2=float(g4.mean()),
                            var_2x2=float(g4.var()), p999_2x2=float(np.percentile(g4, 99.9)), max_2x2=int(g4.max())))
            print('ramp', out[-1], flush=True)
    for r in out:
        z = [q for q in out if q['sensor'] == r['sensor'] and q['S_px'] == 0.0][0]
        r['added_var_over_mu'] = (r['var_2x2'] - z['var_2x2']) / r['mu'] if r['mu'] > 0 else None
    return out


LABELS = ('ramp', 'ramp_raise', 'poisson_raise')     # threshold sets evaluated against the adopted (version-4) set


def main():
    """Threshold sets: 'ramp' = texture-aware thresholds from the measured texture (adopted count model; may be
    lower than version 4, which carries the declared edge); 'ramp_raise' = max(version 4, 'ramp') (keeps the
    declared margin, raises only where the measured texture needs it); 'poisson_raise' = max(version 4,
    Poisson-bound thresholds) (bounding count model)."""
    edges, hist, meta = load_hist()
    store = load_json('event_response.json')
    out = {'model': __doc__, 'threshold_sets': main.__doc__, 'cases': [], 'detection': [], 'thresholds_texture': {l: {} for l in LABELS}}
    out['ramp_check'] = ramp_check()
    for sname in SENS:
        dk = sensor_dark(sname)
        for (d, I0) in HKEYS:
            if d != dk or I0 not in seeds_for(sname):
                continue
            got = {}
            for mdl in ('poisson', 'ramp', 'phase'):
                got[mdl] = analyse_case(sname, float(I0), edges, hist, mdl)
                out['cases'].append(got[mdl][0])
            thr = got['ramp'][1]
            print(sname, I0, 'adopted thresholds with measured texture: ramp %.3f /h, poisson %.2f /h, phase %.3f /h '
                  '(assumed edge model %.2f /h)' % (got['ramp'][0]['rate_adopted_measured'], got['poisson'][0]['rate_adopted_measured'],
                                                    got['phase'][0]['rate_adopted_measured'], got['ramp'][0]['rate_adopted_assumed']), flush=True)
            cand = {'ramp': got['ramp'][2],
                    'ramp_raise': {W: dict(thr[W], n_min=max(thr[W]['n_min'], got['ramp'][2][W]['n_min']),
                                           n_min3=max(thr[W]['n_min3'], got['ramp'][2][W]['n_min3'])) for W in er.WINDOWS},
                    'poisson_raise': {W: dict(thr[W], n_min=max(thr[W]['n_min'], got['poisson'][2][W]['n_min']),
                                              n_min3=max(thr[W]['n_min3'], got['poisson'][2][W]['n_min3'])) for W in er.WINDOWS}}
            sets = {}
            for lab, new in cand.items():
                out['thresholds_texture'][lab][f'{sname}_{I0}'] = {str(W): {k: new[W][k] for k in ('n_min', 'n_min3')} for W in er.WINDOWS}
                if any(new[W]['n_min'] != thr[W]['n_min'] or new[W]['n_min3'] != thr[W]['n_min3'] for W in er.WINDOWS):
                    sets[lab] = new
                print('  ', lab, [(W, thr[W]['n_min'], new[W]['n_min'], thr[W]['n_min3'], new[W]['n_min3']) for W in er.WINDOWS], flush=True)
            if not sets:
                continue
            det = redetect(sname, float(I0), thr, sets, store['cases'])
            out['detection'] += det
            save_json('texture_measured.json', out)
    save_json('texture_measured.json', out)
    yield_step()


if __name__ == '__main__':
    yield_step() if sys.argv[1:2] == ['yields'] else main()
