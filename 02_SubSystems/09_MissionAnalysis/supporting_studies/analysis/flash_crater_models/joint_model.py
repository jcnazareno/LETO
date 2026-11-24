"""One selected population for pair yield and inference, version 3 (final review round: F05-F10, F12, F13).

Version 2 (review round 2: N07-N11, N13) introduced one population for yield and fit. Version 3 changes:
  * F08: the D >= 10 m normalisation is computed analytically (numerical integration of the power-law /
    lognormal population) instead of from the ~160 sampled tail events; detection tables are made
    monotonic in energy by isotonic regression (not a running maximum), and the effect of the finite
    40-trial detection grid is estimated by binomial bootstrap of the tables;
  * F10: imaging access depends on latitude (per-ring result of imaging_access_check.py: 100% to 66 deg,
    87.5% at 70 deg, none from 72 deg in the normal mode), times a scheduling factor (0.90; 0.80-0.95);
    pairs are reported by hemisphere and latitude band;
  * F07: the association rule is applied in generation, yield and likelihood. A site is accepted if
    exactly one confirmable new crater lies inside the 95% error region (circle of the semi-major axis
    at that flash's range) and between the before and after images. There is NO size window (it would
    truncate the residuals on the relation being measured). Sites with a second candidate are lost;
    sites whose own crater is not confirmed but which contain one unrelated crater become false pairs;
    the likelihood includes them as a mixture with a known contamination fraction;
  * F05/F13: measured energies get the condition-dependent bias and scatter of photometry_calibration.py
    (by decay time and background); the likelihood uses the calibrated scatter but not the bias, and it
    uses MEASURED decay time (0.3 in ln) and background (5%) for the detection probability, not the truth;
  * F13: the flash catalogue in the fit is the detected flashes NOT in the paired sample, with the size
    the yield model predicts for that sensor case (no measurement used twice);
  * F06: fits are run for the nominal sensor and for an adverse case (pessimistic sensor, its own
    catalogue size, the warm-sensor energy scatter of 0.33 and +10% bias for long flashes under bright
    earthshine); the dependence stress is also run with the pessimistic sensor;
  * F12: fifteen 25 mm heads use their own detection tables (thresholds for 15 heads).
Population: true flash energy ln E above ln(300 J), cumulative index b = alpha*s (alpha = 0.30 assumed,
  s = 3.25, 2.8-3.6 by reweighting); crater ln D = ln 4.3 m + alpha ln(E/84.9 kJ) + N(0, 0.252); decay
  log-uniform 0.03-1 s; range, latitude and earthshine jointly from observing opportunities.
Selection: flash detection (event_response.json, per sensor case), crater confirmation
  c_max*Phi((ln D - ln(k GSD))/0.15), availability 0.70, p_loc 0.95, access(lat) x scheduling 0.90,
  f_before 0.80, association (exp(-lambda)).
"""
import math
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from scipy.integrate import quad
from common import save_json, load_json, DATA
from event_response import dark_e, SENSORS

RNG = np.random.default_rng(20261113)
ALPHA, D_REF, E_REF, SIG_PHYS = 0.30, 4.3, 8.49e4, 0.252
S_NOM = 3.25
X_LOW = math.log(300.0)
N10, N10_SIG = 184.0, 46.0
ES_FULL = 18519.7
PHI_3000 = 0.0639        # six 16 mm heads, geometric, from coverage.json
PHI_25MM = 0.0663        # fifteen 25 mm heads
CMAX, KW = 0.85, 0.15
A_MOON = 3.79e7          # km2
ARCHIVE_YR = 20.0        # before (LRO, mostly 2009-2015) to after (about 2034) images
E_IMG = 2.03e4           # sites imaged: measured energy above the value predicting 2.8 m on the prior relation
YEARS = 2.5


def a0():
    return math.log(D_REF) - ALPHA * math.log(E_REF)


# ---------------- detection table ----------------
def pava(y):
    """Isotonic (non-decreasing) least-squares fit of a 1-D sequence."""
    y = list(map(float, y)); w = [1.0] * len(y); blocks = [[v, wt, 1] for v, wt in zip(y, w)]
    out = []
    for b in blocks:
        out.append(b)
        while len(out) > 1 and out[-2][0] > out[-1][0]:
            v2, w2, n2 = out.pop(); v1, w1, n1 = out.pop()
            out.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2, n1 + n2])
    res = []
    for v, _, n in out:
        res += [v] * n
    return np.array(res)


class DetTable:
    def __init__(self, er, sensor, boot_rng=None):
        rows = [c for c in er['cases'] if c['sensor'] == sensor]
        self.I0 = np.array(sorted({r['I0'] for r in rows}))
        self.tau = np.array(sorted({r['tau_f_s'] for r in rows}))
        self.E = np.array(sorted({r['E_L_J'] for r in rows}))
        P = np.zeros((len(self.I0), len(self.tau), len(self.E)))
        for r in rows:
            p = r['p_detect']
            if boot_rng is not None:
                p = boot_rng.binomial(r.get('n_trials', 40), p) / r.get('n_trials', 40)
            P[np.searchsorted(self.I0, r['I0']), np.searchsorted(self.tau, r['tau_f_s']), np.searchsorted(self.E, r['E_L_J'])] = p
        for i in range(P.shape[0]):
            for j in range(P.shape[1]):
                P[i, j] = pava(P[i, j])
        self.P = P
        self.lI, self.lt, self.lE = np.log(self.I0), np.log(self.tau), np.log(self.E)

    def __call__(self, lnE_eff, lntau, lnI0):
        lnE_eff, lntau, lnI0 = np.broadcast_arrays(lnE_eff, lntau, lnI0)
        def w(grid, v):
            i = np.clip(np.searchsorted(grid, v) - 1, 0, len(grid) - 2)
            f = np.clip((v - grid[i]) / (grid[i + 1] - grid[i]), 0, 1)
            return i, f
        ii, fi = w(self.lI, lnI0); it, ft = w(self.lt, lntau)
        out = np.zeros(lnE_eff.shape)
        ie = np.clip(np.searchsorted(self.lE, lnE_eff) - 1, 0, len(self.lE) - 2)
        fe = np.clip((lnE_eff - self.lE[ie]) / (self.lE[ie + 1] - self.lE[ie]), 0, 1)
        for di, wi in ((0, 1 - fi), (1, fi)):
            for dt, wt in ((0, 1 - ft), (1, ft)):
                rowsP = self.P[ii + di, it + dt]
                pv = np.take_along_axis(rowsP, ie[..., None], -1)[..., 0] * (1 - fe) + np.take_along_axis(rowsP, (ie + 1)[..., None], -1)[..., 0] * fe
                pv = np.where(lnE_eff < self.lE[0], 0.0, pv)
                out += wi * wt * pv
        return out


# ---------------- population ----------------
def population(n, b0):
    obs = np.load(DATA / 'observed_background_samples.npz')
    j = RNG.integers(0, len(obs['range_km']), n)
    x = X_LOW + RNG.exponential(1 / b0, n)
    y = a0() + ALPHA * x + RNG.normal(0, SIG_PHYS, n)
    lntau = RNG.uniform(math.log(0.03), math.log(1.0), n)
    return dict(x=x, y=y, lntau=lntau, d=obs['range_km'][j].astype(float), es=obs['es_rel'][j].astype(float) * ES_FULL,
                lat=obs['lat'][j].astype(float), near=obs['near'][j].astype(int), b0=b0)


def sub(pop, m):
    return {k: (v[m] if isinstance(v, np.ndarray) else v) for k, v in pop.items()}


def weights(pop, s):
    b = ALPHA * s
    return (b / pop['b0']) * np.exp(-(b - pop['b0']) * (pop['x'] - X_LOW))


_NORM = {}


def norm10(s):
    """Analytic P(D >= 10 m) per impact above X_LOW for index b = alpha*s (F08)."""
    if s not in _NORM:
        b = ALPHA * s
        f = lambda x: b * math.exp(-b * (x - X_LOW)) * norm.sf((math.log(10.0) - a0() - ALPHA * x) / SIG_PHYS)
        _NORM[s] = quad(f, X_LOW, X_LOW + 100, limit=500, points=[math.log(E_REF)])[0]
    return _NORM[s]


def p_flash(pop, tab, sensor):
    I0 = dark_e(SENSORS[sensor]['dark_fA']) + pop['es']
    return tab(pop['x'] + 2 * np.log(3750.0 / pop['d']), pop['lntau'], np.log(I0))


def p_crater(y, k=3.5, gsd=0.9, cmax=CMAX, kw=KW):
    return cmax * norm.cdf((y - math.log(k * gsd)) / kw)


def access(lat):
    """Normal-mode imaging access at 300 km in 6 months (per-ring result; linear between rings)."""
    a = np.abs(lat)
    return np.interp(a, [0, 66, 70, 72, 90], [1.0, 1.0, 0.875, 0.0, 0.0])


def r95(d):
    """95% error-region semi-major axis versus range (0.56 km at 3000 km nadir, 1.28 km at 65 deg / ~3750 km)."""
    return np.clip(0.56 + (1.28 - 0.56) * (d - 3000.0) / 750.0, 0.56, 1.4)


def unrelated_rate(s=S_NOM, n10=N10, k=3.5, gsd=0.9, cmax=CMAX):
    """Confirmable new craters per km2 per year: N10 (D/10 m)^-s, weighted by the confirmation curve."""
    f = lambda lnD: s * math.exp(-s * (lnD - math.log(10.0))) * cmax * norm.cdf((lnD - math.log(k * gsd)) / KW)
    v = quad(f, math.log(0.5), math.log(1000.0), limit=400)[0]
    return n10 * v / A_MOON


def lam_site(d, archive_yr=ARCHIVE_YR, **kw):
    return unrelated_rate(**kw) * math.pi * r95(d)**2 * archive_yr


def yield_terms(pop, pf, s=S_NOM, n10=N10, k=3.5, gsd=0.9, cmax=CMAX, phi=PHI_3000, avail=0.70, p_loc=0.95,
                p_sched=0.90, f_before=0.80, external=None, mask=None):
    """Expected pairs, false pairs and imaged sites per year. external: access share for Option C (no latitude
    limit of our own camera, no scheduling factor)."""
    w = weights(pop, s)
    if mask is not None:
        w = w * mask
    acc = (np.full(len(pop['x']), external) if external is not None else access(pop['lat']) * p_sched)
    lam = lam_site(pop['d'], s=s, n10=n10, k=k, gsd=gsd, cmax=cmax)
    pc = p_crater(pop['y'], k, gsd, cmax)
    scale = n10 * phi * avail * p_loc * f_before / norm10(s) / len(pop['x'])
    true_pairs = (w * pf * acc * pc * np.exp(-lam)).sum() * scale
    imaged = (pop['x'] >= math.log(E_IMG))                                  # sites chosen for imaging (measured ~ true here)
    false_pairs = (w * pf * acc * imaged * (1 - pc) * lam * np.exp(-lam)).sum() * scale
    sites = (w * pf * imaged).sum() * scale / f_before / p_loc               # all located sites above the imaging cut
    flashes = (w * pf).sum() * scale / f_before / p_loc
    return dict(pairs=true_pairs, false_pairs=false_pairs, sites_imaged=sites * p_loc, flashes=flashes,
                contamination=false_pairs / max(true_pairs + false_pairs, 1e-30))


def flash_eff_confirmable(pop, pf, s=S_NOM, k=3.5, gsd=0.9):
    w = weights(pop, s) * p_crater(pop['y'], k, gsd, 1.0)
    return float((w * pf).sum() / w.sum())


# ---------------- Monte Carlo over the non-sensor factors ----------------
SCEN = dict(avail=(0.70, 0.60, 0.80), p_loc=(0.95, 0.90, 0.98), p_sched=(0.90, 0.80, 0.95), f_before=(0.80, 0.60, 0.90),
            cmax=(0.85, 0.65, 0.95), k=(3.5, 5.0, 3.0), s=(3.25, 2.8, 3.6))


def tri(nom, lo, hi, u):
    a, b = min(lo, hi), max(lo, hi); c = min(max(nom, a), b)
    fc = (c - a) / (b - a)
    return np.where(u < fc, a + np.sqrt(u * (b - a) * (c - a)), b - np.sqrt((1 - u) * (b - a) * (b - c)))


def mc(pop, pf, years=YEARS, n=4000, external=None, gsd=0.9, phi=PHI_3000, stress=False):
    """Independent factors (default) or a shared-quantile dependence stress (N11)."""
    if stress:
        q = RNG.random(n)
        U = {k: q for k in SCEN}; U['k'] = 1 - q; un10 = q
    else:
        U = {k: RNG.random(n) for k in SCEN}; un10 = RNG.random(n)
    g = {kk: tri(nom, pes, opt, U[kk]) for kk, (nom, pes, opt) in SCEN.items()}
    n10 = np.clip(N10 + N10_SIG * norm.ppf(np.clip(un10, 1e-6, 1 - 1e-6)), 50, None)
    sg = np.linspace(2.8, 3.6, 5); kg = np.linspace(3.0, 5.0, 5)
    base = np.array([[yield_terms(pop, pf, s=s_, n10=N10, k=k_, gsd=gsd, cmax=1.0, phi=1.0, avail=1.0, p_loc=1.0,
                                  p_sched=1.0, f_before=1.0, external=(1.0 if external is not None else None))['pairs'] / N10
                      for k_ in kg] for s_ in sg])
    from scipy.interpolate import RegularGridInterpolator
    f = RegularGridInterpolator((sg, kg), np.log(np.maximum(base, 1e-30)))
    y1 = np.exp(f(np.stack([g['s'], g['k']], 1)))
    acc = g['p_sched'] if external is None else np.full(n, external)
    Y = n10 * phi * g['avail'] * g['p_loc'] * acc * g['f_before'] * g['cmax'] * y1
    tot = RNG.poisson(Y * years)
    return dict(p10=float(np.percentile(Y, 10)), p50=float(np.median(Y)), p90=float(np.percentile(Y, 90)),
                total_p10=float(np.percentile(tot, 10)), total_p50=float(np.median(tot)),
                P_ge_30=float((tot >= 30).mean()), P_ge_80=float((tot >= 80).mean()), P_ge_150=float((tot >= 150).mean()))


# ---------------- inference ----------------
XG = np.linspace(X_LOW, math.log(3e8), 260); DXG = XG[1] - XG[0]


def unrelated_lnD_density(y, s=S_NOM, k=3.5, gsd=0.9):
    """Density of ln D of a confirmed unrelated crater (production slope s times the confirmation curve)."""
    yy = np.linspace(math.log(0.5), math.log(300), 2000)
    g = s * np.exp(-s * yy) * norm.cdf((yy - math.log(k * gsd)) / KW)
    Z = g.sum() * (yy[1] - yy[0])
    return s * np.exp(-s * y) * norm.cdf((y - math.log(k * gsd)) / KW) / Z


def fit(sample, cat, tab, k=3.5, gsd=0.9, include_flash=True, eps=0.0):
    """sample: x_obs, sx, y_obs, sy, lntau_m, d, I0_m for pairs; cat: same (no y) for the unpaired catalogue.
    eps: known contamination fraction for the mixture term (0 = no mixture)."""
    y0 = math.log(k * gsd)
    def pf_grid(s_):
        if not include_flash:
            return np.ones((len(s_['x_obs']), len(XG)))
        return tab(XG[None, :] + 2 * np.log(3750.0 / s_['d'][:, None]), s_['lntau_m'][:, None], np.log(s_['I0_m'])[:, None])
    PFp = pf_grid(sample); PFc = pf_grid(cat) if include_flash else None
    Nxp = norm.pdf(sample['x_obs'][:, None], XG[None, :], sample['sx'][:, None])
    Nxc = norm.pdf(cat['x_obs'][:, None], XG[None, :], cat['sx'][:, None])
    y, sy = sample['y_obs'], sample['sy']
    gy = unrelated_lnD_density(y, k=k, gsd=gsd) if eps > 0 else None
    def nll(p):
        a, al, ls, lb = p; s = math.exp(ls); b = math.exp(lb)
        fx = b * np.exp(-b * (XG - X_LOW))
        mu = a + al * XG[None, :]
        st = np.sqrt(s * s + sy[:, None]**2)
        like_y = norm.pdf(y[:, None], mu, st)
        mpost = (mu * sy[:, None]**2 + y[:, None] * s * s) / st**2
        spost = s * sy[:, None] / st
        sel = norm.cdf((mpost - y0) / np.sqrt(spost**2 + KW * KW))
        L = (fx[None, :] * PFp * Nxp * like_y * sel).sum(1) * DXG
        Z = (fx[None, :] * PFp * norm.cdf((a + al * XG[None, :] - y0) / math.sqrt(s * s + KW * KW))).sum(1) * DXG
        Ltrue = L / np.clip(Z, 1e-300, None)
        if eps > 0:
            hx = (fx[None, :] * PFp * Nxp).sum(1) / np.clip((fx[None, :] * PFp).sum(1), 1e-300, None)
            Ltrue = (1 - eps) * Ltrue + eps * hx * gy
        ll = np.log(np.clip(Ltrue, 1e-300, None)).sum()
        if include_flash:
            Lc = (fx[None, :] * PFc * Nxc).sum(1) * DXG
            Zc = (fx[None, :] * PFc).sum(1) * DXG
            ll += np.log(np.clip(Lc, 1e-300, None)).sum() - np.log(np.clip(Zc, 1e-300, None)).sum()
        return -ll
    p0 = [a0(), ALPHA, math.log(0.25), math.log(ALPHA * S_NOM)]
    r = minimize(nll, p0, method='Nelder-Mead', options=dict(xatol=1e-5, fatol=1e-5, maxiter=4000))
    h = np.array([2e-3, 2e-3, 5e-3, 5e-3]); f0 = r.fun
    H = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            ei = np.eye(4)[i] * h[i]; ej = np.eye(4)[j] * h[j]
            H[i, j] = (nll(r.x + ei + ej) - nll(r.x + ei) - nll(r.x + ej) + f0) / (h[i] * h[j])
    try:
        cov = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        cov = np.full((4, 4), np.nan)
    return r.x, cov


def energy_errors(cal, n, lntau, I0, scale_sd=None, long_bright_bias=None):
    """Condition-dependent (bias, sd) of the corrected ln E from photometry_calibration.json."""
    t = cal['condition_table']
    tl = np.where(np.exp(lntau) > 0.3, 'tau_gt_0.3', 'tau_le_0.3'); bl = np.where(I0 > 1e4, 'bg_gt_1e4', 'bg_le_1e4')
    bias = np.zeros(n); sd = np.zeros(n)
    for i in range(n):
        e = t.get(f'{tl[i]}|{bl[i]}') or t['tau_le_0.3|bg_le_1e4']
        bias[i], sd[i] = e['bias'], e['sd']
    if scale_sd is not None:
        sd = sd * scale_sd
    if long_bright_bias is not None:
        bias = np.where((np.exp(lntau) > 0.3) & (I0 > 1e4), long_bright_bias, bias)
    return bias, sd


def run_fits(pop, pf, tab, sensor, N, ntr, cal, n_flash_total, eps, include_flash=True, mixture=True,
             scale_sd=None, long_bright_bias=None):
    out = []
    darkc = dark_e(SENSORS[sensor]['dark_fA'])
    w = weights(pop, S_NOM)
    lam = lam_site(pop['d'])
    pc = p_crater(pop['y'])
    acc = access(pop['lat'])
    p_true = pf * pc * acc * np.exp(-lam)
    p_false = pf * (1 - pc) * acc * (pop['x'] >= math.log(E_IMG)) * lam * np.exp(-lam)
    ncat = max(int(round(n_flash_total)) - N, 50)
    for _ in range(ntr):
        nfalse = RNG.binomial(N, eps)
        selp = RNG.random(len(pop['x'])) < p_true
        ip = RNG.choice(np.nonzero(selp)[0], N - nfalse, replace=False, p=w[selp] / w[selp].sum())
        qq = w * p_false                                  # false pairs: drawn in proportion to their expected rate
        iq = RNG.choice(len(pop['x']), nfalse, replace=True, p=qq / qq.sum()) if nfalse else np.array([], int)
        selc = (RNG.random(len(pop['x'])) < pf)
        selc[ip] = False; selc[iq] = False
        ic = RNG.choice(np.nonzero(selc)[0], ncat, replace=False, p=w[selc] / w[selc].sum())
        common = RNG.normal(0, 0.10); hoff = RNG.normal(0, 0.05, 6)
        def mk(idx):
            n = len(idx)
            I0 = darkc + pop['es'][idx]
            bias, sd = energy_errors(cal, n, pop['lntau'][idx], I0, scale_sd, long_bright_bias)
            return dict(x_obs=pop['x'][idx] + common + hoff[RNG.integers(0, 6, n)] + bias + RNG.normal(0, 1, n) * sd,
                        sx=np.hypot(sd, 0.05), lntau_m=pop['lntau'][idx] + RNG.normal(0, 0.3, n),
                        d=pop['d'][idx], I0_m=I0 * (1 + RNG.normal(0, 0.05, n)))
        idx_all = np.concatenate([ip, iq])
        smp = mk(idx_all); cat = mk(ic)
        # crater sizes: real crater for true pairs; an unrelated confirmed crater for false pairs
        y_true = pop['y'][idx_all].copy()
        if nfalse:
            yy = np.linspace(math.log(0.5), math.log(300), 4000)
            g = unrelated_lnD_density(yy); g = g / g.sum()
            y_true[N - nfalse:] = RNG.choice(yy, nfalse, p=g)
        Dpx = np.exp(y_true) / 0.9
        smp['sy'] = np.hypot(0.03, 0.35 / Dpx)
        smp['y_obs'] = y_true + RNG.normal(0, 1, N) * smp['sy']
        p, cov = fit(smp, cat, tab, include_flash=include_flash, eps=(eps if mixture else 0.0))
        a, al, ls, lb = p
        pred = {}
        for E in (1e4, 3e4, 1e5, 1e6):
            xe = math.log(E)
            ref = a0() + ALPHA * xe
            var = cov[0, 0] + xe**2 * cov[1, 1] + 2 * xe * cov[0, 1]
            pred[str(int(E))] = dict(err_vs_physical=a + al * xe - ref, fitted_sd=math.sqrt(max(var, 0)) if np.isfinite(var) else None)
        out.append(dict(alpha=al, alpha_sd=math.sqrt(max(cov[1, 1], 0)) if np.isfinite(cov[1, 1]) else None,
                        sigma=math.exp(ls), b=math.exp(lb), common=common, nfalse=int(nfalse), pred=pred))
    return out


def summarize_fits(f, N=None, ncat=None):
    al = np.array([r['alpha'] for r in f]); sd = np.array([r['alpha_sd'] if r['alpha_sd'] is not None else np.nan for r in f])
    sg = np.array([r['sigma'] for r in f]); bb = np.array([r['b'] for r in f])
    o = dict(n=len(f), N_pairs=N, n_catalogue=ncat, alpha_mean=float(al.mean()), alpha_bias=float(al.mean() - ALPHA),
             alpha_ensemble_sd=float(al.std()), alpha_fitted_sd_median=float(np.nanmedian(sd)),
             alpha_coverage_1sd=float(np.nanmean(np.abs(al - ALPHA) <= sd)),
             sigma_mean=float(sg.mean()), sigma_true=SIG_PHYS, sigma_ensemble_sd=float(sg.std()),
             sigma_rel_bias=float(sg.mean() / SIG_PHYS - 1),
             b_mean=float(bb.mean()), b_true=ALPHA * S_NOM, b_ensemble_sd=float(bb.std()),
             mean_false_pairs=float(np.mean([r['nfalse'] for r in f])))
    for E in ('10000', '30000', '100000', '1000000'):
        e = np.array([r['pred'][E]['err_vs_physical'] for r in f])
        s_ = np.array([r['pred'][E]['fitted_sd'] or np.nan for r in f])
        tot = np.sqrt(s_**2 + (ALPHA * 0.10)**2)
        sdv = float(e.std())
        o[f'lnD_at_{E}J'] = dict(bias=float(e.mean()), ensemble_sd=sdv, fitted_sd_incl_common_median=float(np.nanmedian(tot)),
                                 coverage_1sd=float(np.nanmean(np.abs(e) <= tot)),
                                 # crater-count conversion term at slope s: multiplicative 1-sigma deviations (F09)
                                 count_factor_upper=math.exp(S_NOM * sdv) - 1, count_factor_lower=1 - math.exp(-S_NOM * sdv),
                                 size_factor_upper=math.exp(sdv) - 1, size_factor_lower=1 - math.exp(-sdv))
    return o


# ---------------- association table (documentation) ----------------
def association():
    """Probability that an error region contains at least one unrelated confirmable new crater, with no size
    window (version-3 rule) and, for comparison, with the version-2 +-2 sigma size window."""
    out = {}
    rate = unrelated_rate()
    def win(D, r, y, sig=0.33):
        lo, hi = max(D * math.exp(-2 * sig), 3.15), D * math.exp(2 * sig)
        rg = lambda d: N10 * (d / 10.0) ** (-S_NOM) / A_MOON
        return 1 - math.exp(-(rg(lo) - rg(hi)) * math.pi * r * r * y)
    for r in (0.56, 1.3, 3.0, 15.0):
        for y in (10, 20, 25):
            out[f'r{r}_{y}yr'] = {'no_window': 1 - math.exp(-rate * math.pi * r * r * y),
                                  'window_3.5m': win(3.5, r, y), 'window_10m': win(10.0, r, y)}
    out['confirmable_unrelated_rate_per_km2_yr'] = rate
    return out


# ---------------- main ----------------
def main(yields_only=False, only_fits=None):
    try:
        previous_fits = load_json('joint_model.json').get('fits', {})
    except FileNotFoundError:
        previous_fits = {}
    er = load_json('event_response.json')
    cal = load_json('photometry_calibration.json')
    # revision-5 sensor envelope only; later cases (e.g. the sensor-trade cases 'm636...') are evaluated by
    # sensor_trade.py so that adding them does not change the random draws behind the revision-5 results
    REV5 = {'nominal', 'pessimistic', 'optimistic', 'warm_dark', 'high_C', 'slow', 'noisy', 'slow10', 'cap3',
            'law_sqrt', 'noise3', 'ba_burst', 'ba_telegraph', 'ba_hetero', 'nominal_25mm', 'pessimistic_25mm'}
    sensors = sorted({c['sensor'] for c in er['cases']} & REV5)
    pop = population(400_000, ALPHA * S_NOM)
    out = {'model': __doc__, 'sensors': sensors, 'cases': {}, 'norm10_analytic': norm10(S_NOM),
           'norm10_sampled_fraction': float((pop['y'] >= math.log(10.0)).mean())}
    tabs, pfs = {}, {}
    for sname in sensors:
        tab = DetTable(er, sname); tabs[sname] = tab
        pf = p_flash(pop, tab, sname); pfs[sname] = pf
        phi = PHI_25MM if '25mm' in sname else PHI_3000
        yt = yield_terms(pop, pf, phi=phi)
        c = dict(flash_eff_confirmable=flash_eff_confirmable(pop, pf),
                 flash_eff_confirmable_near=flash_eff_confirmable(sub(pop, pop['near'] == 1), pf[pop['near'] == 1]),
                 flash_eff_confirmable_far=flash_eff_confirmable(sub(pop, pop['near'] == 0), pf[pop['near'] == 0]),
                 nominal_per_yr_A=yt, mc_A=mc(pop, pf, phi=phi))
        if '25mm' not in sname:
            c['mc_C_access50'] = mc(pop, pf, external=0.5)
            c['mc_A_150km'] = mc(pop, pf, gsd=0.45)
            c['ratio_150_vs_300'] = yield_terms(pop, pf, gsd=0.45)['pairs'] / yt['pairs']
        out['cases'][sname] = c
        print(sname, round(c['flash_eff_confirmable'], 3), round(yt['pairs'] * YEARS, 1), round(c['mc_A']['total_p50']),
              round(c['mc_A']['P_ge_30'], 3), round(c['mc_A']['P_ge_80'], 3), 'contam', round(yt['contamination'], 4), flush=True)
    nom, pes = 'nominal', 'pessimistic'
    pf, pfp = pfs[nom], pfs[pes]
    ex = dict(
        mc_A_stress=mc(pop, pf, stress=True),
        mc_A_stress_pessimistic_sensor=mc(pop, pfp, stress=True),
        mc_C_access20=mc(pop, pf, external=0.2), mc_C_access80=mc(pop, pf, external=0.8),
        mc_C_access50_pessimistic=mc(pop, pfp, external=0.5),
        mc_A_1p5yr=mc(pop, pf, years=1.5),
        mc_ellipse=mc(pop, pf, phi=0.027, external=0.51),
        corner_pairs_2p5yr={})
    for sname, pp in ((nom, pf), (pes, pfp)):
        for anc in (138.0, 50.0):
            y = yield_terms(pop, pp, s=2.8, n10=anc, k=5.0, cmax=0.65, avail=0.60, p_loc=0.90, p_sched=0.80, f_before=0.60)
            ex['corner_pairs_2p5yr'][f'{sname}_{anc}'] = YEARS * y['pairs']
    # breakdown by hemisphere and latitude band (nominal)
    br = {}
    for lab, m in (('near', pop['near'] == 1), ('far', pop['near'] == 0), ('lat_0_30', np.abs(pop['lat']) < 30),
                   ('lat_30_60', (np.abs(pop['lat']) >= 30) & (np.abs(pop['lat']) < 60)), ('lat_60_90', np.abs(pop['lat']) >= 60)):
        br[lab] = YEARS * yield_terms(pop, pf, mask=m.astype(float))['pairs']
    ex['pairs_2p5yr_by_region'] = br
    # finite detection grid: binomial bootstrap of the tables (F08)
    boot = {}
    for sname in (nom, pes):
        v = []
        brng = np.random.default_rng(77)
        for _ in range(30):
            t = DetTable(er, sname, boot_rng=brng)
            v.append(YEARS * yield_terms(pop, p_flash(pop, t, sname))['pairs'])
        boot[sname] = dict(mean=float(np.mean(v)), sd=float(np.std(v)), rel_sd=float(np.std(v) / np.mean(v)))
    ex['grid_bootstrap_pairs_2p5yr'] = boot
    # population sampling error of the numerator (bootstrap over impacts)
    v = []
    for _ in range(30):
        ii = RNG.integers(0, len(pop['x']), len(pop['x']))
        v.append(YEARS * yield_terms(sub(pop, ii), pf[ii])['pairs'])
    ex['population_bootstrap_pairs_2p5yr'] = dict(mean=float(np.mean(v)), sd=float(np.std(v)))
    out['nominal_extra'] = ex
    out['association'] = association()
    print('extra', {k: (v if not isinstance(v, dict) else {a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()}) for k, v in ex.items()}, flush=True)
    if yields_only:                                   # keep the fits of the previous full run
        out['fits'] = previous_fits
        save_json('joint_model.json', out)
        return
    out['fits'] = previous_fits if only_fits else {}
    save_json('joint_model.json', out)
    # ---------- fits ----------
    fits = {}
    ynom = out['cases'][nom]['nominal_per_yr_A']; ypes = out['cases'][pes]['nominal_per_yr_A']
    eps_n, eps_p = ynom['contamination'], ypes['contamination']
    nf_n, nf_p = ynom['flashes'] * YEARS, ypes['flashes'] * YEARS
    plan = [('30', nom, 30, 120, {}), ('80', nom, 80, 100, {}), ('240', nom, 240, 60, {}),
            ('80_contamination_not_modelled', nom, 80, 60, dict(mixture=False)),
            ('80_without_flash_selection', nom, 80, 40, dict(include_flash=False)),
            ('adverse_30', pes, 30, 100, dict(scale_sd=0.33 / 0.20, long_bright_bias=0.10)),
            ('adverse_75', pes, 75, 80, dict(scale_sd=0.33 / 0.20, long_bright_bias=0.10))]
    if only_fits:
        fits = dict(previous_fits)
        plan = [p for p in plan if p[0] in only_fits]
    for key, sname, N, ntr, kw in plan:
        tab = tabs[sname]; pp = pfs[sname]
        eps = eps_n if sname == nom else eps_p
        nft = nf_n if sname == nom else nf_p
        res = run_fits(pop, pp, tab, sname, N, ntr, cal, nft, eps, **kw)
        fits[key] = summarize_fits(res, N=N, ncat=max(int(round(nft)) - N, 50))
        fits[key]['sensor'] = sname; fits[key]['options'] = kw; fits[key]['eps'] = eps
        print('fit', key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in fits[key].items() if not isinstance(v, dict)}, flush=True)
        out['fits'] = fits
        save_json('joint_model.json', out)
    out['fits'] = fits
    save_json('joint_model.json', out)


if __name__ == '__main__':
    import sys
    if 'assoc' in sys.argv:
        d = load_json('joint_model.json'); d['association'] = association(); save_json('joint_model.json', d)
    else:
        of = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('fits=')]
        main(yields_only='yields' in sys.argv, only_fits=of[0] if of else None)
