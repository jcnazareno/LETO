"""Event-camera response to slow lunar impact flashes, version 3 (final review round, F01-F04, F12).

Version 2 (review round 2, N01-N05) replaced the revision-3 model. Version 3 changes:
  * F01: the per-pixel null distribution is no longer renormalised. It is the convolution of (i) the
    simulated shot-noise event count (background activity switched off), floored by a Poisson law at
    1.5 x its mean, and (ii) the exact count distribution of the declared background-activity model at
    1.5 x its rate. Both factors are unnormalised majorants, so the exact (untruncated) group
    convolution bounds the group tail IF the physical noise follows the declared model with at most
    1.5 x the assumed rate. Mass above the count cap is kept in the last bin. This is an ASSUMED null
    model, not a bound on the physical sensor; sensitivity cases with bursty, telegraph-switching and
    pixel-to-pixel heterogeneous background activity show how thresholds and detection respond when the
    noise is not Poisson.
  * F02: the trigger counts at most ONE ON event per pixel per 0.5 ms step. A particle deposit changes
    the photocurrent within one step and therefore contributes at most one count per hit pixel; a flash
    rises through the photoreceptor over several steps. particle_check() simulates deposits and gives a
    union bound on particle-induced false triggers; texture_check() bounds moving lunar texture.
  * F03: the response law is a hypothesis. Latency (time to the first event after a step) is not the
    photoreceptor time constant; for a first-order filter the two differ by a factor that depends on the
    step size and threshold. Cases now include a ten-times slower reference (10 ms at 5 lx), a 3 s cap
    and a square-root law, besides the linear law with a 1 s cap.
  * F04: detections are stored as counts (k of n) so that binomial intervals can be quoted.
  * F12: cases for fifteen 25 mm heads use the 25 mm aperture and 15/6 times more trigger tests.
  * the median trigger lag (trigger time minus true onset) and the median onset-estimate error (first
    ON event of the triggering group minus true onset) are reported separately (review F10, C05).

Pixel model (per pixel, 0.5 ms steps)
  * photocurrent I = I0 + flash, I0 = dark current + earthshine (+ optical bias, if used), in detected
    e-/s; Poisson electrons each step;
  * photoreceptor = first-order low-pass of the photocurrent with a current-dependent time constant,
    linear law tau = tau_ref * I_ref / J (or square-root law tau = tau_ref * (I_ref/J)^0.5), capped at
    tau_cap; I_ref = 7.5e6 e-/s is the 5 lx level of this project's 30 Oct red-band bias fixture (not a
    spectrally matched calibration of the cited experiment); tau_ref = 1 ms nominal, chosen to equal the
    1 ms latency at 5 lx reported by McReynolds et al. (2024) - an assumption, see F03;
  * ON/OFF events when ln J moves by the pixel threshold C_i ~ N(C, 0.03); 1% event loss;
  * background activity (BA): extra ON events, Poisson at r_ba per pixel (nominal), or in bursts (mean
    burst size ba_m), or with telegraph switching (fraction ba_f of the time at ba_h x the low rate,
    mean dwell 1 s), or with a static per-pixel lognormal rate spread ba_sigma;
  * flash: PSF Gaussian sigma 0.5 px with a random sub-pixel centre; a 4 x 4 pixel patch is simulated.
Detection (on board): sliding windows W = 0.05, 0.2, 0.8, 2.0 s, evaluated every W/5, on every 2 x 2 and
  3 x 3 group of the patch, using clipped counts (<= 1 ON per pixel per step): trigger if the group's
  count >= n_min(W, size) and at least 3 pixels contributed. n_min is set so that the expected number of
  false triggers from the assumed null model is < 1 per hour over all heads (every overlapping group,
  window length and evaluation step counted as a test; 5.3e12 tests per hour for six heads).
Energy estimate (event-only): onset = first ON event of the triggering group in the trigger window; the
  record runs until all patch pixels have returned to their pre-flash decoded level, or 4 s. Each pixel's
  intensity is decoded from all its events with its calibrated threshold (5% error) and the measured
  background (common error 5% per flash). Raw energy = sum of decoded excess electrons / electrons per J.
Usage: python event_response.py   -> data/event_response.json
       python event_response.py <part> <case,case,...>  then  python event_response.py merge
"""
import math
import numpy as np
from scipy.stats import poisson, norm
from common import save_json, DATA

H, C_LIGHT = 6.626e-34, 2.998e8
E_PH = H * C_LIGHT / 750e-9
T_OPT, QE = 0.6, 0.5
DT = 5e-4
I_REF = 7.5e6
E_PER_LUX_BIAS = 1.5e6
Q_E = 1.602e-19
WINDOWS = (0.05, 0.2, 0.8, 2.0)
T_PRE, T_POST = 0.4, 4.0
NMAX = 400
GROUPS = [(i, j, 2) for i in range(3) for j in range(3)] + [(i, j, 3) for i in range(2) for j in range(2)]


def tests_per_hour(n_heads=6):
    return 2 * n_heads * 1280 * 720 * sum(3600.0 / (w / 5) for w in WINDOWS)   # 2x2 and 3x3 groups


TESTS_PER_HOUR = tests_per_hour(6)
BASE = dict(tau_ref=1e-3, C=0.25, dark_fA=1.0, r_ba=0.3, tau_cap=1.0, law='linear', ba_m=1.0, ba_f=0.0, ba_h=1.0,
            ba_sigma=0.0, ap_m=0.016, n_heads=6)
SENSORS = {
    'nominal':     dict(BASE),
    'pessimistic': dict(BASE, tau_ref=3e-3, C=0.30, dark_fA=5.55, r_ba=1.0),
    'optimistic':  dict(BASE, tau_ref=0.3e-3, C=0.20, dark_fA=0.3, r_ba=0.03),
    'warm_dark':   dict(BASE, dark_fA=5.55),
    'high_C':      dict(BASE, C=0.30),
    'slow':        dict(BASE, tau_ref=3e-3),
    'noisy':       dict(BASE, r_ba=1.0),
    # version 3 (F01-F03, F12)
    'slow10':      dict(BASE, tau_ref=10e-3),          # latency of 1 ms with a large step implies tau ~ 10-30 ms
    'cap3':        dict(BASE, tau_cap=3.0),             # slower dark limit (~0.05 Hz corner)
    'law_sqrt':    dict(BASE, law='sqrt'),              # weaker current dependence (faster near darkness)
    'noise3':      dict(BASE, r_ba=3.0),                # background activity outside the 0.03-1 Hz range
    'ba_burst':    dict(BASE, ba_m=3.0),                # BA in bursts, mean 3 events (Fano 5 before clipping)
    'ba_telegraph': dict(BASE, ba_f=0.1, ba_h=10.0),    # 10% of the time at 10x the low rate, 1 s dwell
    'ba_hetero':   dict(BASE, ba_sigma=1.0),            # static per-pixel lognormal spread of BA rate
    'nominal_25mm': dict(BASE, ap_m=0.025, n_heads=15),
    'pessimistic_25mm': dict(BASE, tau_ref=3e-3, C=0.30, dark_fA=5.55, r_ba=1.0, ap_m=0.025, n_heads=15),
}
# version 4 (sensor trade, 3 November 2026): cases from measured IMX636 data (McReynolds et al., AMOS 2025:
# dark current 1.1 +/- 0.5 fA, photoreceptor corner 6.49 Hz at 13.3 fA and 0.55 Hz at the dark limit, i.e. a
# linear current law with tau = 1/(2 pi f) = 24.5 ms at 13.3 fA -> tau_ref = 0.27 ms at I_REF; default-bias
# background activity ~0.03 Hz per pixel; tuned biases ~1 Hz with ON thresholds 0.05-0.15; about 2% of pixels
# carry >99% of the excess events and are masked). The spread of the remaining pixels (lognormal sigma 0.5)
# is an assumption. 'm646_surrogate' is NOT a measurement: it halves tau_ref as a stand-in for the IMX646's
# better rated low-light latency (Sony flyer: <=9 ms at 0.3 lx versus the IMX636's <=1 ms at 5 lx).
M636 = dict(BASE, tau_ref=0.27e-3, dark_fA=1.1, r_ba=0.03, ba_sigma=0.5, ba_mask=0.02)
SENSORS.update({
    'm636':           dict(M636),
    'm636_tuned':     dict(M636, C=0.10, r_ba=1.0),
    'm636_warm':      dict(M636, dark_fA=5.55),
    'm636_25mm':      dict(M636, ap_m=0.025, n_heads=15),
    'm646_surrogate': dict(M636, tau_ref=0.135e-3),
})


def dark_e(fA):
    return fA * 1e-15 / Q_E


def flash_electrons(E_L, d_km, ap_m=0.016):
    return E_L / E_PH * math.pi * (ap_m / 2)**2 / (2 * math.pi * (d_km * 1e3)**2) * T_OPT * QE


def profile(t, tau_f, kind):
    rise = 1 - np.exp(-np.clip(t, 0, None) / 2e-3)
    if kind == 'exp':
        p = rise * np.exp(-t / tau_f)
    elif kind == 'double':                     # 30% fast component at tau/10, 70% slow
        p = rise * (0.3 / (tau_f / 10) * np.exp(-t / (tau_f / 10)) + 0.7 / tau_f * np.exp(-t / tau_f))
    elif kind == 'power':                      # power-law tail
        p = rise * (1 + t / tau_f) ** -2.5
    else:
        raise ValueError(kind)
    return np.where(t > 0, p, 0.0)


def psf_fractions(rng, n, sigma=0.5):
    from scipy.special import erf
    cx = rng.uniform(1.5, 2.5, n); cy = rng.uniform(1.5, 2.5, n)
    edges = np.arange(5.0)
    fx = 0.5 * (erf((edges[None, 1:] - cx[:, None]) / (sigma * 2**0.5)) - erf((edges[None, :-1] - cx[:, None]) / (sigma * 2**0.5)))
    fy = 0.5 * (erf((edges[None, 1:] - cy[:, None]) / (sigma * 2**0.5)) - erf((edges[None, :-1] - cy[:, None]) / (sigma * 2**0.5)))
    return (fx[:, :, None] * fy[:, None, :]).reshape(n, 16)


def tau_of(J, sens):
    x = sens['tau_ref'] * (I_REF / np.maximum(J, 1.0)) ** (0.5 if sens.get('law') == 'sqrt' else 1.0)
    return np.clip(x, DT, sens['tau_cap'])


def simulate(E_L, tau_f, I0, sens, d_km=3750.0, trials=60, kind='exp', rng=None, signal=True,
             t_total=None, bg_err=0.05, keep_events=True, ref_offset=False, ba_symmetric=False, deposit=None):
    """E_L, tau_f and d_km may be scalars or arrays with one value per trial; I0 is one background level.
    ref_offset: start each pixel's reference at a random point within one threshold (finite prehistory).
    ba_symmetric: half of the BA events are OFF (sensitivity to the ON-only BA surrogate, F05).
    deposit: (step index per trial, (trials,16) electron array) for particle-hit tests."""
    rng = rng or np.random.default_rng(20261104)
    t_total = t_total or (T_PRE + T_POST)
    nsteps = int(round(t_total / DT))
    t = np.arange(nsteps) * DT
    P = trials * 16
    E_L = np.broadcast_to(np.asarray(E_L, float), (trials,)).copy()
    tau_f = np.broadcast_to(np.asarray(tau_f, float), (trials,)).copy()
    d_km = np.broadcast_to(np.asarray(d_km, float), (trials,)).copy()
    frac = psf_fractions(rng, trials).reshape(P)
    t_on = T_PRE - rng.uniform(0, 0.15, trials)
    n_tot = flash_electrons(E_L, d_km, sens.get('ap_m', 0.016)) if signal else np.zeros(trials)
    trial_of_pix = np.repeat(np.arange(trials), 16)
    ton = np.repeat(t_on, 16)
    amp = np.repeat(n_tot, 16) * frac
    C = np.clip(rng.normal(sens['C'], 0.03, P), 0.08, None)
    C_est = C * (1 + rng.normal(0, 0.05, P))
    J = np.full(P, float(I0)); ref = np.log(J)
    if ref_offset:
        ref = ref + rng.uniform(-1, 1, P) * C
    on = np.zeros((nsteps, P), dtype=np.int8) if keep_events else None
    off = np.zeros((nsteps, P), dtype=np.int8) if keep_events else None
    # background-activity rates (per pixel, per step)
    r_pix = np.full(P, sens['r_ba'])
    masked = np.zeros(P, bool)
    if sens.get('ba_sigma', 0) > 0:
        s = sens['ba_sigma']; x = rng.normal(-s * s / 2, s, P); r_pix = r_pix * np.exp(x)
        if sens.get('ba_mask', 0) > 0:          # hot-pixel mask: the noisiest fraction of pixels is switched off
            masked = (x + s * s / 2) / s > norm.ppf(1 - sens['ba_mask'])
    m = sens.get('ba_m', 1.0); f, hgain = sens.get('ba_f', 0.0), sens.get('ba_h', 1.0)
    r_low = r_pix / (1 - f + f * hgain)
    state = rng.random(P) < f
    p_switch_up = DT * f / ((1 - f) * 1.0) if f > 0 else 0.0     # mean dwell 1 s in the high state
    p_switch_dn = DT / 1.0
    if signal:
        base = profile(t[None, :], tau_f[:, None], kind)
        base = base / (base.sum(1, keepdims=True) * DT)
    if deposit is not None:
        dep_step, dep_e = deposit
        dep_e = np.asarray(dep_e).reshape(P)
        dep_k = np.repeat(np.asarray(dep_step), 16)
    for k in range(nsteps):
        lam = np.full(P, I0 * DT)
        if signal:
            idx = np.floor((t[k] - ton) / DT).astype(int)
            valid = idx >= 0
            sv = np.zeros(P)
            sv[valid] = base[trial_of_pix[valid], idx[valid]]
            lam = lam + amp * sv * DT
        counts = rng.poisson(lam).astype(float)
        if deposit is not None:
            counts = counts + np.where(dep_k == k, dep_e, 0.0)
        tau = tau_of(J, sens)
        J += (DT / tau) * (counts / DT - J)
        V = np.log(np.maximum(J, 1.0))
        up = V - ref >= C; dn = ref - V >= C
        n_on = np.zeros(P, np.int16); n_off = np.zeros(P, np.int16)
        while up.any() or dn.any():
            keep = rng.random(P) > 0.01
            ref[up] += C[up]; ref[dn] -= C[dn]
            n_on += (up & keep); n_off += (dn & keep)
            up = V - ref >= C; dn = ref - V >= C
        if sens['r_ba'] > 0:
            if f > 0:
                sw = rng.random(P)
                state = np.where(state, sw >= p_switch_dn, sw < p_switch_up)
                rate = np.where(state, r_low * hgain, r_low)
            else:
                rate = r_pix
            nb = rng.poisson(rate * DT / m)
            if m > 1:
                nb = np.where(nb > 0, rng.geometric(1.0 / m, P) * nb, 0)   # burst sizes (mean m)
            if ba_symmetric:
                half = rng.binomial(nb, 0.5)
                n_on += (nb - half).astype(np.int16); n_off += half.astype(np.int16)
            else:
                n_on += nb.astype(np.int16)
        if masked.any():
            n_on[masked] = 0; n_off[masked] = 0
        if keep_events:
            on[k] = np.clip(n_on, 0, 127); off[k] = np.clip(n_off, 0, 127)
    return dict(on=on, off=off, C_est=C_est, trials=trials, n_tot=n_tot, t_on=t_on, d_km=d_km,
                bg_est=I0 * (1 + rng.normal(0, bg_err, trials)), frac=frac.reshape(trials, 16), ap_m=sens.get('ap_m', 0.016))


# ---------- false-alarm thresholds (assumed null model) ----------
RATE_MARGIN = 1.5


def ba_pmf(sens, W, margin=RATE_MARGIN):
    """Exact per-pixel distribution of clipped background-activity counts in a window W under the declared
    BA model with the rate multiplied by `margin`: Poisson; bursts (clipping makes each burst one count);
    telegraph switching (mixture of the two constant-state Poissons, the most dispersed case for windows
    up to the 1 s dwell); static lognormal rate spread (mixture over the spread)."""
    k = np.arange(NMAX + 1)
    r = margin * sens['r_ba']
    if r <= 0:
        p = np.zeros(NMAX + 1); p[0] = 1.0
        return p
    m = sens.get('ba_m', 1.0); f, h = sens.get('ba_f', 0.0), sens.get('ba_h', 1.0); sg = sens.get('ba_sigma', 0.0)
    if sg > 0:
        z, wz = np.polynomial.hermite_e.hermegauss(40); wz = wz / wz.sum()
        if sens.get('ba_mask', 0) > 0:          # unmasked population only (masked pixels give no counts)
            keep = z <= norm.ppf(1 - sens['ba_mask'])
            if keep.sum() < 10:                 # resolve the truncated tail with a finer grid
                z = np.linspace(-6, norm.ppf(1 - sens['ba_mask']), 200); wz = norm.pdf(z)
                keep = np.ones_like(z, bool)
            z, wz = z[keep], wz[keep] / wz[keep].sum()
        p = sum(w * poisson.pmf(k, r * W * math.exp(sg * zz - sg * sg / 2)) for zz, w in zip(z, wz))
    elif f > 0:
        rl = r / (1 - f + f * h)
        p = (1 - f) * poisson.pmf(k, rl * W) + f * poisson.pmf(k, rl * h * W)
    else:
        p = poisson.pmf(k, r * W / m)
    return p


def null_pixel_pmf(I0, sens, seconds=20.0, npix=1008, rng=None):
    """Per-pixel clipped ON-count distribution in disjoint windows: shot-noise part from a noise-only
    simulation WITHOUT background activity (empirical, floored by a Poisson law at 1.5 x its mean), then
    convolved with the exact BA distribution at 1.5 x the BA rate. The result is an unnormalised majorant
    of the declared null model (no renormalisation; review F01)."""
    rng = rng or np.random.default_rng(7)
    sens0 = dict(sens, r_ba=0.0)
    r = simulate(1.0, 0.1, I0, sens0, trials=npix // 16, signal=False, t_total=seconds, rng=rng, keep_events=True)
    on = np.minimum(r['on'], 1).astype(np.int16)
    cs = np.vstack([np.zeros((1, on.shape[1]), np.int32), np.cumsum(on, 0)])
    pmfs = {}
    k = np.arange(NMAX + 1)
    for W in WINDOWS:
        nW = int(round(W / DT))
        starts = np.arange(int(0.5 / DT), on.shape[0] - nW, nW)
        cnt = (cs[starts + nW] - cs[starts]).ravel()
        emp = np.bincount(np.clip(cnt, 0, NMAX), minlength=NMAX + 1).astype(float); emp /= emp.sum()
        shot = np.maximum(emp, poisson.pmf(k, RATE_MARGIN * cnt.mean() + 1e-12))
        tot = np.convolve(shot, ba_pmf(sens, W))
        tot = np.concatenate([tot[:NMAX], [tot[NMAX:].sum()]])          # mass above the cap kept in the last bin
        pmfs[W] = dict(pmf=tot, n_samples=int(cnt.size), shot_mean=float(cnt.mean()),
                       ba_mean=float(sens['r_ba'] * W), majorant_total_mass=float(tot.sum()))
    return pmfs


def group_tail(p, n_min, npx=4, kmin=3):
    """Upper bound on P(sum of npx iid pixels >= n_min and >= kmin pixels non-zero) for a majorant p
    (exact if p is the true PMF); the convolution is not truncated."""
    p = np.asarray(p, float)
    p0 = p[0]; pnz = p.copy(); pnz[0] = 0.0
    conv = {0: np.array([1.0])}
    for k in range(1, npx + 1):
        conv[k] = np.convolve(conv[k - 1], pnz)
    tot = 0.0
    for k in range(kmin, npx + 1):
        w = math.comb(npx, k) * p0 ** (npx - k)
        tot += w * conv[k][n_min:].sum()
    return tot


TEXTURE = dict(ratio=2.0, frac_groups=0.01, v_px_s=0.41)     # assumed worst albedo edge and its prevalence


def texture_mu(sens, I0, W, size, ratio=None, v_px_s=None):
    """Mean clipped ON counts that a moving albedo edge of contrast `ratio` adds to a group in window W, at the
    ground-track speed of a nadir view from 3000 km (0.41 px/s); only earthshine is modulated by albedo."""
    ratio = ratio or TEXTURE['ratio']; v = v_px_s or TEXTURE['v_px_s']
    d = dark_e(sens['dark_fA']); es = max(I0 - d, 0.0)
    lo, hi = d + es * 2 / (1 + ratio), d + es * 2 * ratio / (1 + ratio)
    per_px = math.log(hi / lo) / sens['C']
    return size * size * per_px * min(1.0, W * v / 1.5)


def group_tail_plus(p, n_min, npx, mu):
    """Tail of the group sum when an independent Poisson(mu) count is added (moving texture)."""
    tot = np.array([1.0])
    for _ in range(npx):
        tot = np.convolve(tot, p)
    if mu > 0:
        tot = np.convolve(tot, poisson.pmf(np.arange(80), mu))
    return float(tot[n_min:].sum())


def thresholds(I0, sens, rng=None, texture=True):
    """n_min per window and group size so that the expected false triggers per hour, from the assumed null
    model plus (where earthshine is present) a moving albedo edge of contrast 2 in 1% of all groups, are
    below 1 over all heads. The texture term is a declared assumption (review F02)."""
    pm = null_pixel_pmf(I0, sens, rng=rng)
    nt = tests_per_hour(sens.get('n_heads', 6))
    out = {}
    for W, d in pm.items():
        p = d['pmf']
        res, res0 = {}, {}
        for size in (2, 3):
            mu = texture_mu(sens, I0, W, size) if texture else 0.0
            f = TEXTURE['frac_groups'] if mu > 0 else 0.0
            n = 3
            while group_tail(p, n, npx=size * size) > 1.0 / nt and n < NMAX:
                n += 1
            res0[size] = n
            while ((1 - f) * group_tail(p, n, npx=size * size) + f * group_tail_plus(p, n, size * size, mu)) > 1.0 / nt and n < NMAX:
                n += 1
            if n >= NMAX:
                n = 10**6                      # budget cannot be met within the count cap: this window/group is disabled
            res[size] = n
        out[W] = dict(n_min=res[2], n_min3=res[3], n_min_null_only=res0[2], n_min3_null_only=res0[3],
                      texture_mu_2x2=texture_mu(sens, I0, W, 2), texture_mu_3x3=texture_mu(sens, I0, W, 3),
                      shot_mean_per_pixel=d['shot_mean'], ba_mean_per_pixel=d['ba_mean'],
                      samples=d['n_samples'], majorant_total_mass=d['majorant_total_mass'],
                      tail_at_n=float(group_tail(p, res[2])), tail_at_n3=float(group_tail(p, res[3], npx=9)),
                      disabled=[sz for sz in (2, 3) if res[sz] >= 10**6], env=p)
    return out


# ---------- detection and energy reconstruction ----------
def detect_and_measure(r, thr, d_km=None, tmax_after=4.0, clip=True):
    d_arr = r['d_km'] if d_km is None else np.broadcast_to(np.asarray(d_km, float), (r['trials'],))
    on = r['on'].astype(np.int16); off = r['off'].astype(np.int16)
    nsteps, P = on.shape; trials = r['trials']
    on3 = on.reshape(nsteps, trials, 4, 4); off3 = off.reshape(nsteps, trials, 4, 4)
    trig = np.minimum(on3, 1) if clip else on3                          # F02: <= 1 count per pixel per step
    cs = np.concatenate([np.zeros((1, trials, 4, 4), np.int16), np.cumsum(trig, 0, dtype=np.int16)], 0)
    pres = np.concatenate([np.zeros((1, trials, 4, 4), np.int16), np.cumsum(on3 > 0, 0, dtype=np.int16)], 0)
    t_det = np.full(trials, np.inf); g_det = np.zeros((trials, 3), int); w_det = np.zeros(trials)
    for W in WINDOWS:
        nW = int(round(W / DT)); stride = max(1, nW // 5)
        ends = np.arange(nW, nsteps + 1, stride)
        cw = cs[ends] - cs[ends - nW]
        pw = (pres[ends] - pres[ends - nW]) > 0
        for gi, gj, gs in GROUPS:
            nmin = thr[W]['n_min'] if gs == 2 else thr[W]['n_min3']
            tot = cw[:, :, gi:gi + gs, gj:gj + gs].sum((2, 3))
            npx = pw[:, :, gi:gi + gs, gj:gj + gs].sum((2, 3))
            ok = (tot >= nmin) & (npx >= 3)
            first = np.where(ok.any(0), ok.argmax(0), -1)
            tt = np.where(first >= 0, ends[np.clip(first, 0, None)] * DT, np.inf)
            better = tt < t_det
            t_det[better] = tt[better]; g_det[better] = (gi, gj, gs); w_det[better] = W
    det = np.isfinite(t_det)
    e_raw = np.full(trials, np.nan); active = np.full(trials, np.nan); peak = np.full(trials, np.nan)
    npix = np.zeros(trials); onset_est = np.full(trials, np.nan)
    C_est = r['C_est'].reshape(trials, 4, 4)
    ap = r.get('ap_m', 0.016)
    for i in np.nonzero(det)[0]:
        gi, gj, gs = g_det[i]; kd = int(round(t_det[i] / DT)); kw = int(round(w_det[i] / DT))
        grp_on = on3[max(0, kd - kw):kd, i, gi:gi + gs, gj:gj + gs].sum((1, 2))
        k0 = max(0, kd - kw) + int(np.argmax(grp_on > 0))
        onset_est[i] = k0 * DT
        k1 = min(nsteps, k0 + int(tmax_after / DT))
        net = np.cumsum(on3[k0:k1, i] - off3[k0:k1, i], 0)
        lev = net * C_est[i]
        pos = np.clip(lev, 0, None)
        back = np.nonzero((pos.sum((1, 2)) == 0) & (np.arange(len(pos)) > int(0.05 / DT)))[0]
        kend = back[0] if len(back) else len(pos)
        exc = (np.exp(pos[:kend]) - 1.0) * r['bg_est'][i]
        e_raw[i] = exc.sum() * DT / flash_electrons(1.0, d_arr[i], ap)
        active[i] = kend * DT; peak[i] = lev[:kend].max() if kend else 0.0
        npix[i] = (net[:kend].max(0) > 0).sum() if kend else 0
    return dict(det=det, e_raw=e_raw, active=active, peak=peak, npix=npix, t_lag=t_det - r['t_on'],
                onset_err=onset_est - r['t_on'])


# ---------- particle hits and moving texture (F02) ----------
GCR_FLUX = 5.0           # particles cm^-2 s^-1 incl. secondaries, solar minimum, light shielding (assumed)
F_EVENT = 0.05           # share of hits that deposit enough charge (>~2e3 e-) in a pixel to fire it (assumed: ions, stopping protons)
SENSOR_CM2 = (1280 * 4.86e-4) * (720 * 4.86e-4)


def particle_check(sens, I0, thr, n=600, seed=31):
    """Deposits of 1e2-1e5 e- (log-uniform) per pixel along straight tracks of 1-5 pixels, no flash.
    Returns trigger fractions with and without clipping and a union bound on the hourly rate."""
    rng = np.random.default_rng(seed)
    dep = np.zeros((n, 16))
    for i in range(n):
        L = rng.integers(1, 6); x0, y0 = rng.integers(0, 4, 2); ang = rng.uniform(0, np.pi)
        for s in range(L):
            x = int(round(x0 + s * math.cos(ang))); y = int(round(y0 + s * math.sin(ang)))
            if 0 <= x < 4 and 0 <= y < 4:
                dep[i, 4 * x + y] = math.exp(rng.uniform(math.log(1e2), math.log(1e5)))
    step = rng.integers(int(0.5 / DT), int(1.5 / DT), n)
    r = simulate(1.0, 0.1, I0, sens, trials=n, signal=False, t_total=3.0, rng=rng, deposit=(step, dep))
    with_clip = detect_and_measure(r, thr, clip=True)['det'].mean()
    no_clip = detect_and_measure(r, thr, clip=False)['det'].mean()
    # union bound: a hit adds at most k pixels x 1 clipped count to any group containing it (k<=3 in a
    # 2x2, <=5 in a 3x3 for a straight track); tests containing the hit: 5 phases per window x groups
    hits_per_h = GCR_FLUX * SENSOR_CM2 * sens.get('n_heads', 6) * 3600 * F_EVENT
    bound = 0.0
    for W in WINDOWS:
        p = thr[W]['env']
        for size, kmax, ngrp in ((2, 3, 4), (3, 5, 9)):
            nmin = thr[W]['n_min'] if size == 2 else thr[W]['n_min3']
            bound += 5 * ngrp * group_tail(p, max(nmin - kmax, 0), npx=size * size, kmin=0)
    return dict(n=n, trigger_frac_clipped=float(with_clip), trigger_frac_unclipped=float(no_clip),
                event_capable_hits_per_hour=hits_per_h, deposit_to_fire_one_event_e=float(I0 * sens['tau_cap'] * (math.exp(sens['C']) - 1)), union_bound_false_triggers_per_hour=float(hits_per_h * bound))


def texture_check(sens, I0, thr):
    """False triggers per hour from moving albedo edges with the adopted thresholds: contrast 2 in 1% of the
    groups (the design assumption), contrast 2 in 10%, and contrast 1.2 in all groups."""
    out = {}
    for label, ratio, frac in (('ratio2_1pct', 2.0, 0.01), ('ratio2_10pct', 2.0, 0.10), ('ratio1.2_all', 1.2, 1.0)):
        rate = 0.0
        for W in WINDOWS:
            p = thr[W]['env']
            for size in (2, 3):
                mu = texture_mu(sens, I0, W, size, ratio=ratio)
                nmin = thr[W]['n_min'] if size == 2 else thr[W]['n_min3']
                ntests = sens.get('n_heads', 6) * 1280 * 720 * 3600.0 / (W / 5)
                rate += ntests * ((1 - frac) * group_tail(p, nmin, npx=size * size) + frac * group_tail_plus(p, nmin, size * size, mu))
        out[label] = rate
    return out


# ---------- grid ----------
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den; h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def main(sensor_names=None, tag=''):
    out = {'model': __doc__, 'tests_per_hour_6heads': TESTS_PER_HOUR, 'tests_per_hour_15heads': tests_per_hour(15),
           'sensors': SENSORS, 'thresholds': {}, 'cases': [], 'particle_check': {}, 'texture_check': {}}
    I0_GRID = (2e3, 6.5e3, 1.3e4, 2.5e4, 4e4, 6e4)      # dark current + earthshine
    E_GRID = np.array((2e3, 5e3, 1e4, 2e4, 4e4, 1e5, 3e5, 1e6, 3e6))
    TAU_GRID = (0.03, 0.1, 0.3, 1.0)
    per = 40
    names = list(sensor_names or SENSORS)
    for sname in names:
        seed = 100 + 7919 * (list(SENSORS).index(sname) + 1)
        sens = SENSORS[sname]
        for I0 in I0_GRID:
            if I0 < 0.95 * dark_e(sens['dark_fA']) or (I0 > 4.5e4 and dark_e(sens['dark_fA']) < 2e4):
                continue
            thr = thresholds(I0, sens, rng=np.random.default_rng(seed)); seed += 1
            out['thresholds'][f'{sname}_{I0:.0f}'] = {str(k): {a: b for a, b in v.items() if a != 'env'} for k, v in thr.items()}
            if I0 in (6.5e3, 1.3e4) or (I0 == 4e4 and sens['dark_fA'] > 5):
                out['particle_check'][f'{sname}_{I0:.0f}'] = particle_check(sens, I0, thr)
                out['texture_check'][f'{sname}_{I0:.0f}'] = texture_check(sens, I0, thr)
            for tau_f in TAU_GRID:
                E = np.repeat(E_GRID, per)
                r = simulate(E, tau_f, I0, sens, trials=len(E), rng=np.random.default_rng(seed)); seed += 1
                m = detect_and_measure(r, thr)
                for j, Ej in enumerate(E_GRID):
                    sl = slice(j * per, (j + 1) * per)
                    ok = m['det'][sl]
                    lr = np.log(m['e_raw'][sl][ok] / Ej) if ok.any() else np.array([])
                    kk = int(ok.sum())
                    out['cases'].append(dict(sensor=sname, I0=I0, tau_f_s=tau_f, E_L_J=float(Ej), p_detect=kk / per,
                                             k_detect=kk, n_trials=per, wilson95=wilson(kk, per),
                                             raw_ln_bias=float(np.median(lr)) if lr.size else None,
                                             raw_ln_sd=float(np.std(lr)) if lr.size > 2 else None,
                                             trigger_lag_s_median=float(np.median(m['t_lag'][sl][ok])) if ok.any() else None,
                                             onset_err_s_median=float(np.median(m['onset_err'][sl][ok])) if ok.any() else None,
                                             onset_err_s_p90=float(np.percentile(m['onset_err'][sl][ok], 90)) if ok.sum() > 3 else None))
            print(sname, I0, [(c['tau_f_s'], c['E_L_J'], round(c['p_detect'], 2)) for c in out['cases'][-36:] if c['E_L_J'] in (2e4, 1e5)], flush=True)
            save_json(f'event_response{tag}.json', out)
    save_json(f'event_response{tag}.json', out)


def merge_add():
    """Merge part files into the existing event_response.json, replacing the cases of the sensors they contain."""
    import json
    base = json.loads((DATA / 'event_response.json').read_text())
    for p in sorted(DATA.glob('event_response_part*.json')):
        d = json.loads(p.read_text())
        names = {c['sensor'] for c in d['cases']}
        base['cases'] = [c for c in base['cases'] if c['sensor'] not in names] + d['cases']
        for key in ('thresholds', 'particle_check', 'texture_check'):
            base[key] = {k: v for k, v in base[key].items() if not any(k.startswith(n + '_') and k[len(n) + 1:].isdigit() for n in names)}
            base[key].update(d[key])
        base['sensors'].update({n: SENSORS[n] for n in names})
        p.rename(p.with_suffix('.merged'))
    save_json('event_response.json', base)


def merge():
    import json
    parts = sorted(DATA.glob('event_response_part*.json'))
    base = None
    for p in parts:
        d = json.loads(p.read_text())
        if base is None:
            base = d
        else:
            for key in ('thresholds', 'particle_check', 'texture_check'):
                base[key].update(d[key])
            base['cases'] += d['cases']
    save_json('event_response.json', base)
    for p in parts:
        p.unlink()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'merge':
        merge()
    elif len(sys.argv) > 1 and sys.argv[1] == 'merge_add':
        merge_add()
    elif len(sys.argv) > 2:
        main(sys.argv[2].split(','), tag=f'_part{sys.argv[1]}')
    else:
        main()
