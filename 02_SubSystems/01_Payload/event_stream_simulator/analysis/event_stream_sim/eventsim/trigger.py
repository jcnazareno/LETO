"""On-board trigger (S10 rule) on the generated event stream, clustering, event-only energy estimate, matching.

Trigger: every 2x2 and 3x3 pixel group, sliding windows W = 0.05, 0.2, 0.8, 2.0 s evaluated every W/5 up to the
end of the observed stream; at most one ON event per pixel per 0.5 ms step counts; a group triggers when its count
>= n_min(W, size, background) and at least 3 of its pixels contributed.

Thresholds. n_min comes from the S10 false-alarm model (event_response.thresholds): per-pixel majorant PMFs of the
clipped ON count in a window, combined by event_response.group_tail / group_tail_plus so that the expected false
triggers per hour stay below 1. Each pixel's background is rounded up to the next 0.2-ln bin (S10 convention).
  group_bg='hetero' (default): a group whose pixels fall in bins b_lo..b_hi uses the POINTWISE MAXIMUM of the
    per-bin PMFs over b_lo..b_hi (and the texture mean of b_hi). The pointwise maximum is a majorant of every
    pixel's PMF, and both tail formulas are sums of products of PMF entries, so the mixed group's tail is bounded
    term by term. Homogeneous groups (b_lo = b_hi) keep the S10 table value. This is a bound under the declared
    null model (independent pixels, the S10 majorants, the assumed texture term); it does not cover spatial or
    temporal correlations, or noise sources outside that model.
  group_bg='max': the threshold of the brightest pixel's bin (a heuristic: increasing thresholds do not imply
    that the lower-background pixels' distributions are dominated). group_bg='geomean': the geometric mean.
  The null-model sensor is the S10 case named in the profile ('fixed', default) or that case re-tuned to the
  run's values of the parameters S10 represents ('retuned'); see threshold_model() for what S10 cannot represent.
Groups with any pixel within 2 px of a pixel whose background exceeds the lit-surface limit (default 1e5 e-/s, about
four times the brightest earthshine) are excluded, as an on-board illumination mask predicted from orbit, attitude and
maps would do. The map can be shifted or scaled (Simulation.onboard_background) to stress pointing/map errors.
Triggers within 4 px and within the 4 s record of a detection are merged into it.
Energy (S10 detect_and_measure, per detection): 4x4 patch centred on the triggering group; onset = first ON event of
the group within the trigger window; per pixel decoded level = n_on C_on,est - n_off C_off,est (calibrated
thresholds with 5% error); record ends when all patch pixels are back at or below their pre-flash level (after
50 ms), after 4 s, or at the end of the observed stream (`t_end`; such a record is flagged `censored` and is not
corrected or used in energy statistics); E_raw = sum((exp(level+) - 1) x background estimate) dt / (electrons per J
at the pixel's slant range x field gain of the patch); the background estimate is the true background of the time
chunk at the onset with a 5% common error per flash (`bg_err`).
"""
from __future__ import annotations
import hashlib
import json
import math
import sys
import warnings
from pathlib import Path
import numpy as np
import numba as nb

WINDOWS = (0.05, 0.2, 0.8, 2.0)
DT_TRIG = 5e-4
DISABLED = 10 ** 6
FLASH_RESPONSE = Path(__file__).resolve().parents[2] / 'flash_response'
DATA = Path(__file__).resolve().parents[3] / 'data'
CACHE = DATA / 'thresholds_cache.json'
PMF_CACHE = DATA / 'null_pmf_cache'
# part of every cache key: bump when the threshold binning/lookup in this file changes. Homogeneous-group entries
# keep their earlier keys (unchanged algorithm); heterogeneous-group entries carry HET_VERSION.
THRESHOLD_ALGO_VERSION = 'esim-thr-2 (2026-11-04 review)'
HET_VERSION = 'het-pointwise-max-1'

# Profile value -> field of an event_response.py sensor case (the S10 null model's inputs). These can be re-tuned.
S10_FIELD_MAP = {
    ('sensor', 'photoreceptor.tau_ref_s'): 'tau_ref', ('sensor', 'threshold.C_on'): 'C',
    ('sensor', 'ba.rate_hz'): 'r_ba', ('sensor', 'photoreceptor.tau_cap_s'): 'tau_cap',
    ('sensor', 'photoreceptor.law'): 'law', ('sensor', 'ba.burst_mean'): 'ba_m',
    ('sensor', 'ba.telegraph_fraction'): 'ba_f', ('sensor', 'ba.telegraph_gain'): 'ba_h',
    ('sensor', 'ba.sigma_ln'): 'ba_sigma', ('sensor', 'mask.fraction'): 'ba_mask', ('optics', 'aperture_m'): 'ap_m',
}
# Pixel parameters that event_response.simulate() hard-codes: the value equivalent to S10, or a function of the
# profile giving it, and a condition under which the parameter matters. A profile that differs here is NOT
# represented by the null model in either threshold mode; the thresholds then remain a fixed approximation.
_EULER = lambda S: S.get('photoreceptor.integrator') == 'euler_s10'
S10_UNMAPPED = {
    'photoreceptor.integrator': ('euler_s10', None),
    'photoreceptor.tau_min_s': (5e-4, lambda S: not _EULER(S)),           # S10 floors tau at its 0.5 ms step
    'photoreceptor.adaptive_substeps': (False, lambda S: not _EULER(S)),
    'photoreceptor.second_stage_tau_s': (0.0, None),
    'photoreceptor.hpf_tau_s': (0.0, None),
    'threshold.C_off': (lambda S: S['threshold.C_on'], None),               # S10 uses one C for ON and OFF
    'threshold.sigma_C': (0.03, None),
    'threshold.C_min': (0.08, None),
    'threshold.on_off_correlated': (True, None),
    'events.refractory_s': (0.0, None),
    'events.loss_fraction': (0.01, None),
    'events.initial_reference': ('level', None),
    'dark.spread_sigma_ln': (0.0, None),
    'hot.fraction': (0.0, None),
    'mask.calibration_s': (0.0, lambda S: S.get('mask.fraction', 0) > 0),  # S10 masks by the true rate
    'ba.model': ('poisson_additive', None),
    'ba.on_fraction': (1.0, lambda S: S.get('ba.rate_hz', 0) > 0),
    'ba.telegraph_dwell_s': (1.0, lambda S: S.get('ba.telegraph_fraction', 0) > 0),
    'readout.limit_enabled': (False, None),
    'esp.erc_enabled': (False, None), 'esp.afk_enabled': (False, None), 'esp.stc_enabled': (False, None),
}


def _er():
    if str(FLASH_RESPONSE) not in sys.path:
        sys.path.insert(0, str(FLASH_RESPONSE))
    import event_response as er
    return er


def _same(a, b):
    if isinstance(a, (str, bool)) or isinstance(b, (str, bool)) or a is None or b is None:
        return a == b
    return math.isclose(float(a), float(b), rel_tol=1e-6, abs_tol=1e-12)


def s10_fields_from_profiles(sensor, optics):
    """The S10 null-model inputs implied by the simulated sensor/optics profiles (mapped parameters only).
    photoreceptor.I_ref_e_s is folded into tau_ref (S10 fixes I_REF; tau depends only on tau_ref * I_ref^g)."""
    src = dict(sensor=sensor, optics=optics)
    out = {}
    for (sec, key), field in S10_FIELD_MAP.items():
        try:
            out[field] = src[sec][key]
        except KeyError:
            continue
    try:
        g = 0.5 if sensor['photoreceptor.law'] == 'sqrt' else 1.0
        out['tau_ref'] = out['tau_ref'] * (sensor['photoreceptor.I_ref_e_s'] / _er().I_REF) ** g
    except KeyError:
        pass
    try:
        out['dark_fA'] = sensor['dark.current_fA'] * 2 ** (sensor['dark.temperature_offset_C'] / sensor['dark.doubling_temperature_C'])
    except KeyError:
        pass
    if out.get('ba_f', 0.0) == 0.0:
        out.pop('ba_h', None)              # telegraph gain is irrelevant without telegraph noise
    return out


def unmapped_differences(sensor):
    """Pixel parameters of the profile that the S10 null model cannot represent, where they differ from S10."""
    out = {}
    for key, (eq, cond) in S10_UNMAPPED.items():
        try:
            v = sensor[key]
        except KeyError:
            continue
        if cond is not None and not cond(sensor):
            continue
        e = eq(sensor) if callable(eq) else eq
        if not _same(v, e):
            out[key] = dict(s10_equivalent=e, simulated=v)
    return out


def threshold_model(case, sensor, optics, model='fixed'):
    """Null-model sensor dict for the trigger thresholds and how it relates to the simulated pixel.
    model='fixed': the named S10 case unchanged (the thresholds a fixed on-board table would use);
    model='retuned': that case with every MAPPED field replaced by the run's profile value.
    Returns (sens, info): info['mapped_differences'] lists mapped fields where the named case and the profile
    differ (re-tuned in 'retuned' mode); info['unmapped_differences'] lists pixel parameters S10 cannot represent
    at all; in both modes these are kept as a fixed approximation, never adapted."""
    er = _er()
    base = dict(er.SENSORS[case])
    prof = s10_fields_from_profiles(sensor, optics)
    mapped = {}
    for k, v in prof.items():
        b = base.get(k, 0.0 if k in ('ba_mask', 'ba_sigma', 'ba_f') else None)
        if not _same(b, v):
            mapped[k] = dict(null_model=b, simulated=v)
    if model == 'retuned':
        sens = dict(base, **prof)
    elif model == 'fixed':
        sens = base
    else:
        raise ValueError(f'unknown threshold model {model}')
    info = dict(mapped_differences=mapped, mapped_adapted=(model == 'retuned'),
                unmapped_differences=unmapped_differences(sensor))
    return sens, info


def _fingerprint(sens):
    er = _er()
    h = hashlib.sha256()
    h.update(THRESHOLD_ALGO_VERSION.encode())
    h.update(json.dumps(sens, sort_keys=True, default=str).encode())
    h.update(Path(er.__file__).read_bytes())
    return h.hexdigest()[:16]


def _tails(q, npx, mu, kmin=3):
    """Vectorised event_response.group_tail(q, n, npx, kmin) and group_tail_plus(q, n, npx, mu) for all n."""
    from scipy.stats import poisson
    q = np.asarray(q, float)
    q0 = q[0]; pnz = q.copy(); pnz[0] = 0.0
    L = npx * (len(q) - 1) + 1
    tail = np.zeros(L + 1)
    conv = np.array([1.0])
    for k in range(1, npx + 1):
        conv = np.convolve(conv, pnz)
        if k >= kmin:
            c = np.zeros(L); c[:len(conv)] = conv[:L]
            tail[:L] += math.comb(npx, k) * q0 ** (npx - k) * np.cumsum(c[::-1])[::-1]
    tot = np.array([1.0])
    for _ in range(npx):
        tot = np.convolve(tot, q)
    if mu > 0:
        tot = np.convolve(tot, poisson.pmf(np.arange(80), mu))
    tplus = np.zeros(len(tot) + 1); tplus[:len(tot)] = np.cumsum(tot[::-1])[::-1]
    return tail, tplus


def nmin_from_pmfs(pmfs, sens, I0_tex):
    """event_response.thresholds() logic for given per-window pixel majorant PMFs; texture mean at I0_tex."""
    er = _er()
    nt = er.tests_per_hour(sens.get('n_heads', 6))
    out = {}
    for W in WINDOWS:
        res = {}
        for size in (2, 3):
            mu = er.texture_mu(sens, I0_tex, W, size)
            f = er.TEXTURE['frac_groups'] if mu > 0 else 0.0
            tail, tplus = _tails(pmfs[W], size * size, mu)
            T = lambda n: tail[n] if n < len(tail) else 0.0
            Tp = lambda n: tplus[n] if n < len(tplus) else 0.0
            n = 3
            while T(n) > 1.0 / nt and n < er.NMAX:
                n += 1
            while ((1 - f) * T(n) + f * Tp(n)) > 1.0 / nt and n < er.NMAX:
                n += 1
            res[size] = DISABLED if n >= er.NMAX else n
        out[W] = (res[2], res[3])
    return out


class ThresholdTable:
    """n_min(W, size) versus background for one S10 null-model sensor: 'stored' (event_response.json grid, next grid
    point at or above the background; the named case only; mixed groups use the brightest pixel) or 'compute'
    (event_response.thresholds at the 0.2-ln bin, cached under a key that fingerprints the null-model parameters,
    event_response.py and this algorithm; mixed groups per group_bg, see the module docstring)."""

    def __init__(self, s10_case, mode='compute', bin_ln=0.2, lit_limit=1e5, lit_margin=2, sens=None, group_bg='hetero',
                 model='fixed', info=None):
        self.case, self.mode, self.bin_ln, self.lit_limit, self.lit_margin = s10_case, mode, bin_ln, lit_limit, lit_margin
        self.model = model
        self.info = dict(info or dict(mapped_differences={}, mapped_adapted=False, unmapped_differences={}))
        self.group_bg = group_bg if not (mode == 'stored' and group_bg == 'hetero') else 'max'
        self.sens = dict(sens) if sens is not None else dict(_er().SENSORS[s10_case])
        md, ud = self.info['mapped_differences'], self.info['unmapped_differences']
        if md:
            warnings.warn(f'trigger null model ({s10_case}): mapped S10 inputs {sorted(md)} differ from the profile; '
                          f'{"re-tuned to the profile" if model == "retuned" else "NOT adapted (fixed table)"}', stacklevel=2)
        if ud:
            warnings.warn(f'trigger null model ({s10_case}): pixel parameters {sorted(ud)} cannot be represented by S10; '
                          'thresholds keep them as a fixed approximation in either mode', stacklevel=2)
        self.fingerprint = _fingerprint(self.sens)
        self._mem = {}; self._pmf = {}; self._het = {}
        self.het_stats = dict(anchors=0, heterogeneous=0, raised=0, max_raise=0, max_bin_span=0)
        self.cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
        if mode == 'stored' and model == 'retuned' and md:
            raise ValueError('stored thresholds exist only for the named S10 cases; use --thresholds compute with a re-tuned model')
        if mode == 'stored':
            d = json.loads((DATA / 'event_response.json').read_text())
            self.stored = {}
            for k, v in d['thresholds'].items():
                name, i0 = k.rsplit('_', 1)
                if name == s10_case:
                    self.stored[float(i0)] = {float(w): (v[w]['n_min'], v[w]['n_min3']) for w in v}
            if not self.stored:
                raise KeyError(f'no stored thresholds for {s10_case}')
            self.grid = np.array(sorted(self.stored))

    def describe(self):
        return dict(case=self.case, model=self.model, mode=self.mode, group_bg=self.group_bg, bin_ln=self.bin_ln,
                    lit_limit=self.lit_limit, lit_margin_px=self.lit_margin, null_model_sensor=self.sens,
                    mapped_differences=self.info['mapped_differences'], mapped_adapted=self.info['mapped_adapted'],
                    unmapped_differences=self.info['unmapped_differences'],
                    note=('mapped_differences: S10 inputs where the named case and the profile differ (re-tuned only if '
                          'mapped_adapted). unmapped_differences: pixel parameters S10 cannot represent; the thresholds '
                          'treat them as a fixed approximation. An empty mapped list does not mean model equivalence.'),
                    heterogeneous_groups=dict(self.het_stats), fingerprint=self.fingerprint,
                    algorithm=THRESHOLD_ALGO_VERSION, het_algorithm=HET_VERSION)

    def _bin_pmfs(self, b):
        """Per-window pixel majorant PMFs of event_response.null_pixel_pmf at bin b (same seed as the n_min table)."""
        if b in self._pmf:
            return self._pmf[b]
        f = PMF_CACHE / f'{self.case}_{self.fingerprint}_b{b}.npz'
        if f.exists():
            z = np.load(f)
            pm = {W: z[f'W{W:g}'] for W in WINDOWS}
        else:
            er = _er()
            d = er.null_pixel_pmf(math.exp(b * self.bin_ln), self.sens, rng=np.random.default_rng(b + 11))
            pm = {float(W): np.asarray(d[W]['pmf'], float) for W in d}
            PMF_CACHE.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(f, **{f'W{W:g}': v for W, v in pm.items()})
        self._pmf[b] = pm
        return pm

    def get_hetero(self, b_lo, b_hi):
        """n_min for a group whose pixels lie in bins b_lo..b_hi: pointwise-max majorant over those bins."""
        if b_lo == b_hi:
            return self.get(math.exp(b_hi * self.bin_ln) * 0.9999)
        top = self.get(math.exp(b_hi * self.bin_ln) * 0.9999)
        if math.exp(b_hi * self.bin_ln) * 0.9999 > self.lit_limit:
            return top                                   # above the lit-surface limit: disabled anyway
        key = (b_lo, b_hi)
        if key in self._het:
            return self._het[key]
        ck = f'{self.case}|{self.fingerprint}|{HET_VERSION}|{b_lo}|{b_hi}'
        if ck in self.cache:
            res = {float(w): tuple(v) for w, v in self.cache[ck].items()}
        else:
            pms = [self._bin_pmfs(b) for b in range(b_lo, b_hi + 1)]
            q = {W: np.max(np.stack([pm[W] for pm in pms]), 0) for W in WINDOWS}
            res = nmin_from_pmfs(q, self.sens, math.exp(b_hi * self.bin_ln))
            # never below the brightest bin's own table value (same majorant family, guards rounding)
            res = {W: (max(res[W][0], top[W][0]), max(res[W][1], top[W][1])) for W in WINDOWS}
            cur = json.loads(CACHE.read_text()) if CACHE.exists() else {}
            cur.update(self.cache)
            cur[ck] = {str(w): list(v) for w, v in res.items()}
            self.cache = cur
            CACHE.write_text(json.dumps(self.cache, indent=0))
        self._het[key] = res
        return res

    def _compute(self, I0b):
        key = f'{self.case}|{self.fingerprint}|{I0b:.1f}'
        if key in self.cache:
            return {float(w): tuple(v) for w, v in self.cache[key].items()}
        er = _er()
        b = int(round(math.log(I0b) / self.bin_ln))
        thr = er.thresholds(float(I0b), self.sens, rng=np.random.default_rng(b + 11))
        res = {float(w): (int(thr[w]['n_min']), int(thr[w]['n_min3'])) for w in thr}
        # re-read before writing so that concurrent runs do not drop each other's entries
        cur = json.loads(CACHE.read_text()) if CACHE.exists() else {}
        cur.update(self.cache)
        cur[key] = {str(w): list(v) for w, v in res.items()}
        self.cache = cur
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(self.cache, indent=0))
        return res

    def get(self, I0):
        if I0 > self.lit_limit:
            return {w: (DISABLED, DISABLED) for w in WINDOWS}
        if self.mode == 'stored':
            i = np.searchsorted(self.grid, I0 * 0.999)
            g = self.grid[min(i, len(self.grid) - 1)]
            return self.stored[g]
        b = int(math.ceil(math.log(max(I0, 1.0)) / self.bin_ln - 1e-9))
        I0b = math.exp(b * self.bin_ln)
        if b not in self._mem:
            self._mem[b] = self._compute(I0b)
        return self._mem[b]

    def maps(self, bg_total, allow2=None, allow3=None, mask_bg=None):
        """Per-anchor threshold maps (4 windows x 2 sizes x h x w) for a background map (e-/s). mask_bg: the map
        the illumination mask is predicted from (default bg_total; a shifted copy stresses pointing errors)."""
        h, w = bg_total.shape
        out = np.full((len(WINDOWS), 2, h, w), DISABLED, np.int32)
        lb = np.log(np.maximum(bg_total, 1.0))
        bpix = np.ceil(lb / self.bin_ln - 1e-9).astype(int)
        swv = np.lib.stride_tricks.sliding_window_view
        for si, s in enumerate((2, 3)):
            if h < s or w < s:
                continue
            allow = (allow2 if si == 0 else allow3)
            allow = None if allow is None else allow[:h - s + 1, :w - s + 1]
            if self.group_bg in ('max', 'hetero'):
                I0g = swv(np.maximum(bg_total, 1.0), (s, s)).max((-1, -2))
            else:
                csum = np.pad(lb, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
                m = (csum[s:, s:] - csum[:-s, s:] - csum[s:, :-s] + csum[:-s, :-s]) / (s * s)
                I0g = np.exp(m)
            if self.mode == 'compute' and self.group_bg == 'hetero':
                bhi = swv(bpix, (s, s)).max((-1, -2)); blo = swv(bpix, (s, s)).min((-1, -2))
                sub = np.full((len(WINDOWS),) + bhi.shape, DISABLED, np.int32)
                todo = np.ones(bhi.shape, bool) if allow is None else allow.copy()
                pairs = np.unique(np.stack([blo[todo], bhi[todo]], 1), axis=0) if todo.any() else np.zeros((0, 2), int)
                for lo_, hi_ in pairs:
                    sel = todo & (blo == lo_) & (bhi == hi_)
                    tab = self.get_hetero(int(lo_), int(hi_))
                    for wi, W in enumerate(WINDOWS):
                        sub[wi][sel] = tab[W][si]
                    if lo_ != hi_ and math.exp(hi_ * self.bin_ln) * 0.9999 <= self.lit_limit:
                        top = self.get(math.exp(hi_ * self.bin_ln) * 0.9999)
                        n = int(sel.sum())
                        self.het_stats['heterogeneous'] += n
                        rz = max(tab[W][si] - top[W][si] for W in WINDOWS if tab[W][si] < DISABLED) if any(tab[W][si] < DISABLED for W in WINDOWS) else 0
                        if any(tab[W][si] > top[W][si] for W in WINDOWS):
                            self.het_stats['raised'] += n
                        self.het_stats['max_raise'] = max(self.het_stats['max_raise'], int(rz))
                        self.het_stats['max_bin_span'] = max(self.het_stats['max_bin_span'], int(hi_ - lo_))
                self.het_stats['anchors'] += int(todo.sum())
                out[:, si, :h - s + 1, :w - s + 1] = sub
                continue
            keys = np.ceil(np.log(np.maximum(I0g, 1.0)) / self.bin_ln - 1e-9).astype(int) if self.mode == 'compute' else None
            if self.mode == 'compute':
                for kb in np.unique(keys):
                    sel = keys == kb
                    tab = self.get(math.exp(kb * self.bin_ln) * 0.9999)
                    for wi, W in enumerate(WINDOWS):
                        out[wi, si, :h - s + 1, :w - s + 1][sel] = tab[W][si]
            else:
                uniq = np.unique(np.round(I0g, -1))
                for u in uniq:
                    sel = np.round(I0g, -1) == u
                    tab = self.get(float(u))
                    for wi, W in enumerate(WINDOWS):
                        out[wi, si, :h - s + 1, :w - s + 1][sel] = tab[W][si]
        # illumination mask: a group is excluded if any of its pixels lies within lit_margin_px of a pixel above the
        # lit-surface limit (covers drift within a 2 s window and the PSF)
        lit = (bg_total if mask_bg is None else mask_bg) > self.lit_limit
        if lit.any():
            from scipy import ndimage
            m = int(self.lit_margin)
            lit = ndimage.binary_dilation(lit, structure=np.ones((2 * m + 1, 2 * m + 1), bool)) if m > 0 else lit
            for si, s in enumerate((2, 3)):
                g = ndimage.maximum_filter(lit.astype(np.uint8), size=s, origin=-(s // 2) if s == 2 else -1, mode='constant') > 0
                out[:, si][:, g] = DISABLED
        if allow2 is not None:
            out[:, 0][:, ~allow2] = DISABLED
        if allow3 is not None:
            out[:, 1][:, ~allow3] = DISABLED
        return out


@nb.njit(cache=True)
def _scan(step, pix, w, h, sW, nmin, chunk_steps, kmin, cap, e_max):
    """step/pix: clipped ON events sorted by step. nmin: (nchunk, 2, h, w). Evaluations e (window ending at step
    e * sW) run only while e <= e_max, i.e. while the window ends inside the observed stream.
    Returns triggers (eval_step, size_idx, ax, ay, count)."""
    P = w * h
    nE = step.shape[0]
    out = np.zeros((cap, 5), np.int64); no = 0
    if nE == 0:
        return out[:0], 0
    cw = np.zeros(P, np.int32)
    stamp = np.full(P, -1, np.int64)
    gstamp = np.full((2, P), -1, np.int64)
    b = step // sW
    ia = 0; ir = 0
    e = b[0] + 1
    nch = nmin.shape[0]
    while e <= b[nE - 1] + 5 and e <= e_max:
        while ia < nE and b[ia] < e:
            cw[pix[ia]] += 1; ia += 1
        while ir < nE and b[ir] < e - 5:
            cw[pix[ir]] -= 1; ir += 1
        if ir == ia:
            if ia >= nE:
                break
            e = b[ia] + 1
            continue
        ch = (e * sW - 1) // chunk_steps
        if ch >= nch:
            ch = nch - 1
        for j in range(ir, ia):
            p = pix[j]
            if stamp[p] == e:
                continue
            stamp[p] = e
            x = p % w; y = p // w
            for si in range(2):
                s = si + 2
                for ay in range(max(0, y - s + 1), min(y, h - s) + 1):
                    for ax in range(max(0, x - s + 1), min(x, w - s) + 1):
                        a = ay * w + ax
                        if gstamp[si, a] == e:
                            continue
                        gstamp[si, a] = e
                        nm = nmin[ch, si, ay, ax]
                        if nm >= 1000000:
                            continue
                        tot = 0; npx = 0
                        for dy in range(s):
                            for dx in range(s):
                                c = cw[(ay + dy) * w + ax + dx]
                                tot += c
                                if c > 0:
                                    npx += 1
                        if npx >= kmin and tot >= nm:
                            if no < cap:
                                out[no, 0] = e * sW; out[no, 1] = si; out[no, 2] = ax; out[no, 3] = ay; out[no, 4] = tot
                            no += 1
        e += 1
    return out[:min(no, cap)], no


def run_trigger(ev, w, h, thr_maps, chunk_s, kmin=3, t_end=None):
    """ev: dict with t (s), p (pixel index), pol. thr_maps: (nchunk, 4, 2, h, w). t_end: end of the observed stream
    [s]; windows ending after it are not evaluated (None: the end of the last chunk of thr_maps). Returns triggers
    array (t_trig, W, size, ax, ay, count)."""
    on = ev['pol'] == 1
    k = np.floor(ev['t'][on] / DT_TRIG + 1e-9).astype(np.int64)
    p = ev['p'][on].astype(np.int64)
    key = np.unique(k * (w * h) + p)
    step = key // (w * h); pix = key % (w * h)
    chunk_steps = int(round(chunk_s / DT_TRIG))
    if t_end is None:
        t_end = thr_maps.shape[0] * chunk_s
    end_step = int(math.floor(t_end / DT_TRIG + 1e-9))
    res = []
    for wi, W in enumerate(WINDOWS):
        sW = int(round(W / 5 / DT_TRIG))
        e_max = end_step // sW
        nmin = np.ascontiguousarray(thr_maps[:, wi])
        cap = 200000
        while True:
            out, n = _scan(step, pix, w, h, sW, nmin, chunk_steps, kmin, cap, e_max)
            if n <= cap:
                break
            cap = n + 1000
        if len(out):
            res.append(np.column_stack([out[:, 0] * DT_TRIG, np.full(len(out), W), out[:, 1] + 2, out[:, 2], out[:, 3], out[:, 4]]))
    if not res:
        return np.zeros((0, 6))
    tr = np.vstack(res)
    return tr[np.argsort(tr[:, 0], kind='stable')]


def cluster(triggers, r_px=4.0, t_rec=4.0):
    """Greedy merge of triggers into detections (first trigger defines the detection)."""
    dets = []
    active = []
    for row in triggers:
        t, W, s, ax, ay, cnt = row
        cx, cy = ax + s / 2.0, ay + s / 2.0
        active = [d for d in active if t - d['t_trig'] <= t_rec]
        hit = None
        for d in active:
            if abs(d['x'] - cx) <= r_px and abs(d['y'] - cy) <= r_px:
                hit = d; break
        if hit is None:
            d = dict(t_trig=float(t), W=float(W), size=int(s), ax=int(ax), ay=int(ay), x=float(cx), y=float(cy),
                     count=int(cnt), n_triggers=1)
            dets.append(d); active.append(d)
        else:
            hit['n_triggers'] += 1
    return dets


def measure_energy(det, ev, w, h, C_on, C_off, bg_total, range_km, k_per_J, rng, bg_err=0.05, c_err=0.05, t_max=4.0,
                   centre=True, t_end=None, gain=None):
    """S10 event-only energy estimate for one detection. k_per_J: function range_km -> electrons per J.
    bg_total: background map (h x w), or a callable t -> map giving the background at the onset time.
    t_end: end of the observed stream [s]. Steps after it are not observed: a record that has not returned to
    its pre-flash level by then is `censored` (integrated over the observed part only). If t_end is None the
    stream is assumed to end at its last event (no evidence of silence beyond it).
    gain: field response map (h x w, e.g. the vignetting the scene applied to point sources); the decoded
    electrons are divided by its patch mean (1 if None)."""
    s = det['size']; ax, ay = det['ax'], det['ay']
    px0 = int(round(ax + s / 2 - 2)); py0 = int(round(ay + s / 2 - 2))
    px0 = min(max(px0, 0), w - 4); py0 = min(max(py0, 0), h - 4)
    t_tr, W = det['t_trig'], det['W']
    t = ev['t']
    i0 = np.searchsorted(t, t_tr - W - 1e-9); i1 = np.searchsorted(t, t_tr + t_max + W)
    sl = slice(i0, i1)
    x = ev['x'][sl].astype(int); y = ev['y'][sl].astype(int); pol = ev['pol'][sl]; tt = t[sl]
    # onset: first ON event of the triggering group in the window
    g = (x >= ax) & (x < ax + s) & (y >= ay) & (y < ay + s) & (pol == 1) & (tt >= t_tr - W) & (tt < t_tr)
    if not g.any():
        return None
    t_on = tt[g][0]
    k0 = int(math.floor(t_on / DT_TRIG + 1e-9))
    nst = int(t_max / DT_TRIG)
    if centre:
        # centre the 4x4 decode patch on the ON-event centroid within 9x9 px around the group, first 50 ms
        gx, gy = ax + s / 2.0, ay + s / 2.0
        c = (pol == 1) & (tt >= t_on) & (tt < t_on + 0.05) & (np.abs(x + 0.5 - gx) <= 4.5) & (np.abs(y + 0.5 - gy) <= 4.5)
        if c.sum() >= 3:
            px0 = int(round(np.mean(x[c] + 0.5) - 2)); py0 = int(round(np.mean(y[c] + 0.5) - 2))
            px0 = min(max(px0, 0), w - 4); py0 = min(max(py0, 0), h - 4)
    inp = (x >= px0) & (x < px0 + 4) & (y >= py0) & (y < py0 + 4) & (tt >= k0 * DT_TRIG) & (tt < (k0 + nst) * DT_TRIG)
    lev = np.zeros((nst, 16))
    if inp.any():
        kk = np.floor(tt[inp] / DT_TRIG + 1e-9).astype(int) - k0
        q = (y[inp] - py0) * 4 + (x[inp] - px0)
        pp = (y[inp]) * w + x[inp]
        ce_on = C_on[pp]; ce_off = C_off[pp]
        np.add.at(lev, (kk, q), np.where(pol[inp] == 1, ce_on, -ce_off))
    cal = (1 + rng.normal(0, c_err, 16))
    lev = np.cumsum(lev, 0) * cal[None, :]
    pos = np.clip(lev, 0, None)
    # observed part of the record (E01): steps whose interval ends at or before the end of the stream
    t_obs_end = float(t_end) if t_end is not None else (float(t[-1]) + DT_TRIG if t.size else k0 * DT_TRIG)
    nobs = int(min(max(math.floor((t_obs_end - k0 * DT_TRIG) / DT_TRIG + 1e-9), 0), nst))
    kk_all = np.arange(nst)
    back = np.nonzero((pos.sum(1) == 0) & (kk_all > int(0.05 / DT_TRIG)) & (kk_all < nobs))[0]
    kend = int(back[0]) if len(back) else nobs
    censored = bool(len(back) == 0 and nobs < nst)
    bmap = bg_total(t_on) if callable(bg_total) else bg_total
    bgp = bmap[py0:py0 + 4, px0:px0 + 4].ravel() * (1 + rng.normal(0, bg_err))
    exc = (np.exp(pos[:kend]) - 1.0) * bgp[None, :]
    d_km = float(np.nanmean(range_km[py0:py0 + 4, px0:px0 + 4]))
    g = float(np.mean(gain[py0:py0 + 4, px0:px0 + 4])) if gain is not None else 1.0
    e_raw = float(exc.sum() * DT_TRIG / (k_per_J(d_km) * g))
    active = kend * DT_TRIG
    peak = float(lev[:kend].max()) if kend else 0.0
    npix = int((lev[:kend].max(0) > 0).sum()) if kend else 0
    return dict(onset_est=float(t_on), e_raw_J=e_raw, active_s=active, peak=peak, npix=npix,
                bg_est=float(np.mean(bgp)), patch=[px0, py0], range_km=d_km, field_gain=g,
                censored=censored, observed_s=nobs * DT_TRIG, record_end_s=float(t_obs_end))


def base_features(m):
    return np.array([math.log(max(m['e_raw_J'], 1e-3)), math.log(max(m['active_s'], 1e-3)), m['peak'], m['npix'],
                     math.log(max(m['bg_est'], 1.0))])


def apply_correction(m, calib):
    """Corrected energy [J] and whether the record lies outside the training range. The quadratic correction is
    evaluated with each base feature clipped to its training range (no extrapolation), the raw ln E_raw kept."""
    x = base_features(m)
    fr = calib.get('feature_range')
    out = False
    if fr:
        lo, hi = np.asarray(fr['min']), np.asarray(fr['max'])
        out = bool(np.any(x < lo) or np.any(x > hi))
        x = np.clip(x, lo, hi)
    return float(m['e_raw_J'] * math.exp(_quad(x) @ np.asarray(calib['coef']))), out


def _quad(x):
    cols = [1.0] + list(x)
    for i in range(5):
        for j in range(i, 5):
            cols.append(x[i] * x[j])
    return np.array(cols)


def correction_features(m):
    x = base_features(m)
    cols = [1.0] + list(x)
    for i in range(5):
        for j in range(i, 5):
            cols.append(x[i] * x[j])
    return np.array(cols)


def match(dets, flashes, hits, r_px=3.5, t_lag_max=None):
    """Label each detection: 'flash' (index), 'particle' (index) or 'false'.
    A flash claims only its FIRST detection, and only if that detection triggered within t_lag_max of the flash onset
    (default: longest trigger window + 0.5 s, i.e. 2.5 s; observed lags are below 0.1 s in the scene runs). Any
    other detection within r_px of a flash's track and within the 4 s record + 2 s of its onset stays 'false' and is
    marked near_flash = flash index (11 Nov 2026; before, every detection within 3.5 px and 6 s of a flash was
    labelled as that flash, which hid false triggers next to flashes)."""
    if t_lag_max is None:
        t_lag_max = max(WINDOWS) + 0.5
    claimed = set()
    for d in sorted(dets, key=lambda x: x['t_trig']):
        d['label'] = 'false'; d['match'] = -1
        best = None; near = None
        for i, f in enumerate(flashes):
            dt = d['t_trig'] - f['t_on']
            if dt < 0 or dt > 6.0:
                continue
            fx = f['x'] + f['vx'] * dt; fy = f['y'] + f['vy'] * dt
            r = math.hypot(d['x'] - fx, d['y'] - fy)
            if r > r_px:
                continue
            if dt <= t_lag_max and i not in claimed and (best is None or r < best[0]):
                best = (r, i)
            elif near is None or r < near[0]:
                near = (r, i)
        if best is not None:
            d['label'] = 'flash'; d['match'] = best[1]; claimed.add(best[1])
            continue
        for i, hh in enumerate(hits):
            dt = d['t_trig'] - hh['t']
            if dt < 0 or dt > 2.1:
                continue
            r = min(math.hypot(d['x'] - (px + 0.5), d['y'] - (py + 0.5)) for px, py in hh['pixels'])
            if r <= r_px:
                d['label'] = 'particle'; d['match'] = i
                break
        if d['label'] == 'false' and near is not None:
            d['near_flash'] = near[1]
    return dets
