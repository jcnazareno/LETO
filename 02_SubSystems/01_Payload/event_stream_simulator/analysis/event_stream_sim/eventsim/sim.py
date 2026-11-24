"""Simulation orchestrator: pixel population, flash and particle injection, chunked kernel runs, readout, ESP,
trigger, energy estimate and ground truth."""
from __future__ import annotations
import math
import time
import numpy as np
from scipy.stats import norm
from . import pixel_kernel as pk
from . import readout as ro
from . import trigger as trg
from .radiometry import Radiometry, dark_e_s

KIND = {'exp': 0, 'double': 1, 'power': 2}
RISE_S = 2e-3


def profile_integral(tau, kind, t_cut):
    t = np.concatenate([np.linspace(0, 0.02, 4001)[1:], np.geomspace(0.02, max(t_cut, 0.021), 20000)[1:]])
    t = t[t <= t_cut]
    r = 1 - np.exp(-t / RISE_S)
    if kind == 'exp':
        p = r * np.exp(-t / tau)
    elif kind == 'double':
        tf = tau / 10
        p = r * (0.3 / tf * np.exp(-t / tf) + 0.7 / tau * np.exp(-t / tau))
    else:
        p = r * (1 + t / tau) ** -2.5
    return float(np.trapezoid(np.r_[0, p], np.r_[0, t]))


class _Over:
    """Profile view with a few keys overridden."""
    def __init__(self, base, over):
        self.base, self.over = base, over

    def __getitem__(self, k):
        return self.over[k] if k in self.over else self.base[k]


class Simulation:
    def __init__(self, scene, sensor, optics, env, duration, dt=5e-4, seed=20261104, flashes=(), particles=None,
                 chunk_s=0.5, kf_dt=0.05, t_cut=4.0, trigger_cfg=None, log=print):
        self.scene, self.sensor, self.optics, self.env = scene, sensor, optics, env
        self.duration, self.dt, self.seed = float(duration), float(dt), int(seed)
        self.chunk_s, self.kf_dt, self.t_cut = float(chunk_s), float(kf_dt), float(t_cut)
        self.w, self.h = scene.w, scene.h
        self.P = self.w * self.h
        self.rad = Radiometry(sensor, optics, env)
        self.rng = np.random.default_rng(self.seed)
        self.log = log
        self.trigger_cfg = dict(mode='compute', lit_limit=1e5, lit_margin=2, groups='all', allow2=None, allow3=None)
        self.trigger_cfg.update(trigger_cfg or {})
        self._pixels()
        self._flashes(list(flashes))
        self._particles(particles)

    # ---------------- pixel population ----------------
    def _pixels(self):
        S, rng, P = self.sensor, self.rng, self.P
        dT = S['dark.temperature_offset_C']
        d0 = dark_e_s(S['dark.current_fA']) * 2 ** (dT / S['dark.doubling_temperature_C'])
        sd = S['dark.spread_sigma_ln']
        self.dark = d0 * np.exp(rng.normal(-sd * sd / 2, sd, P)) if sd > 0 else np.full(P, d0)
        self.dark_nominal = d0
        # background activity: normal pixels (lognormal) and a hot population
        r, sg = S['ba.rate_hz'], S['ba.sigma_ln']
        z = rng.normal(0, 1, P)
        ba = r * np.exp(sg * z - sg * sg / 2) if sg > 0 else np.full(P, float(r))
        hot = rng.random(P) < S['hot.fraction']
        if hot.any():
            hs = S['hot.sigma_ln']
            ba[hot] = S['hot.rate_median_hz'] * np.exp(rng.normal(0, hs, hot.sum()))
        self.ba = ba; self.hot = hot
        # masking of the noisiest fraction from a dark calibration
        mf = S['mask.fraction']; masked = np.zeros(P, bool)
        if mf > 0:
            Tc = S['mask.calibration_s']
            if Tc and Tc > 0:
                est = rng.poisson(ba * Tc) / Tc + rng.random(P) * 1e-9
            else:
                est = z if not hot.any() else ba             # S16: rank by the true rate
            n = int(round(mf * P))
            if sg > 0 and not hot.any() and not (Tc and Tc > 0):
                masked = z > norm.ppf(1 - mf)                  # identical to event_response.py ba_mask
            elif n > 0:
                masked[np.argsort(est)[-n:]] = True
        self.masked = masked
        # thresholds
        sC, cmin = S['threshold.sigma_C'], S['threshold.C_min']
        z1 = rng.normal(0, 1, P)
        z2 = z1 if S['threshold.on_off_correlated'] else rng.normal(0, 1, P)
        self.C_on = np.clip(S['threshold.C_on'] + sC * z1, cmin, None)
        self.C_off = np.clip(S['threshold.C_off'] + sC * z2, cmin, None)
        self.px_x = (np.arange(P) % self.w).astype(np.float64)
        self.px_y = (np.arange(P) // self.w).astype(np.float64)

    # ---------------- flashes ----------------
    def _flashes(self, fl):
        sc, O = self.scene, self.optics
        s1, s2, hf = O['psf.sigma_px'], O['psf.halo_sigma_px'], O['psf.halo_fraction']
        rad_px = 4 * (s2 if hf > 0 else s1) + 1
        out = []
        for i, f in enumerate(fl):
            f = dict(f)
            f.setdefault('kind', 'exp'); f['id'] = i
            xi = int(min(max(math.floor(f['x']), 0), self.w - 1)); yi = int(min(max(math.floor(f['y']), 0), self.h - 1))
            d = f.get('range_km') or float(sc.range_km[yi, xi])
            if not np.isfinite(d):
                continue
            f['range_km'] = d
            vig = float(sc.point_gain_map[yi, xi])
            f['electrons'] = float(f['E_J'] * self.rad.flash_electrons_per_J(d) * vig)
            if f.get('static'):
                f['vx'], f['vy'] = 0.0, 0.0
            else:
                vx, vy = sc.flash_velocity(np.array([f['x']]), np.array([f['y']]), f['t_on'])
                f['vx'], f['vy'] = float(vx[0]), float(vy[0])
            f['norm'] = 1.0 / profile_integral(f['tau_s'], f['kind'], self.t_cut)
            out.append(f)
        self.flashes = out
        # per-pixel CSR lists
        lists = [[] for _ in range(self.P)]
        for j, f in enumerate(out):
            ext = rad_px + math.hypot(f['vx'], f['vy']) * self.t_cut
            x0, x1 = int(math.floor(f['x'] - ext)), int(math.ceil(f['x'] + ext + abs(f['vx']) * 0))
            y0, y1 = int(math.floor(f['y'] - ext)), int(math.ceil(f['y'] + ext))
            for yy in range(max(0, y0), min(self.h, y1 + 1)):
                for xx in range(max(0, x0), min(self.w, x1 + 1)):
                    lists[yy * self.w + xx].append(j)
        ptr = np.zeros(self.P + 1, np.int64)
        ptr[1:] = np.cumsum([len(l) for l in lists])
        self.fl_ptr = ptr
        self.fl_idx = np.array([j for l in lists for j in l], np.int64)
        n = len(out)
        g = lambda k, dt=np.float64: np.array([f[k] for f in out], dt) if n else np.zeros(0, dt)
        self.f_arr = dict(t0=g('t_on'), x0=g('x'), y0=g('y'), vx=g('vx'), vy=g('vy'), amp=g('electrons'),
                          tau=g('tau_s'), kind=np.array([KIND[f['kind']] for f in out], np.int64) if n else np.zeros(0, np.int64),
                          norm=g('norm'), tcut=np.full(n, self.t_cut), sep=np.zeros(n, np.int64))

    # ---------------- particles ----------------
    def _particles(self, cfg):
        """cfg None: particles off. cfg {} (or any dict): on, with the environment defaults for missing keys.
        (Before the 4 Nov 2026 review `if cfg:` treated {} as off, so the default 'gcr' preset injected nothing.)"""
        E = self.env
        hits = []
        self.particle_cfg = None if cfg is None else dict(cfg)
        if cfg is not None:
            rng = np.random.default_rng(self.seed + 77)
            flux = cfg.get('flux_cm2_s', E['particles.flux_cm2_s'])
            pitch_cm = self.sensor['array.pixel_pitch_um'] * 1e-4
            area = self.P * pitch_cm ** 2
            n = rng.poisson(flux * area * self.duration)
            model = cfg.get('model', E['particles.model'])
            if model == 'let_spectrum':
                from .particles import sample_hits
                Ep = E
                if 'let_epoch' in cfg:
                    Ep = _Over(E, {'particles.let_epoch': cfg['let_epoch']})
                hits = sample_hits(rng, n, self.duration, self.w, self.h, Ep, self.sensor['array.pixel_pitch_um'])
                n = 0
            fh = cfg.get('heavy_fraction', E['particles.heavy_fraction'])
            lo, hi = E['particles.heavy_range_e']; L0, L1 = E['particles.track_len_px']
            for i in range(n):
                t = rng.uniform(0.05, self.duration)
                heavy = rng.random() < fh
                base = math.exp(rng.uniform(math.log(lo), math.log(hi))) if heavy else \
                    E['particles.mip_deposit_e'] * math.exp(rng.normal(0, E['particles.mip_sigma_ln']))
                L = int(rng.integers(L0, L1 + 1)); ang = rng.uniform(0, math.pi)
                x0, y0 = rng.uniform(0, self.w), rng.uniform(0, self.h)
                pix = []
                for s in range(L):
                    xx = int(math.floor(x0 + s * math.cos(ang))); yy = int(math.floor(y0 + s * math.sin(ang)))
                    if 0 <= xx < self.w and 0 <= yy < self.h and (xx, yy) not in pix:
                        pix.append((xx, yy))
                if not pix:
                    continue
                dep = [float(base * math.exp(rng.normal(0, 0.3))) for _ in pix]
                hits.append(dict(id=len(hits), t=float(t), heavy=bool(heavy), pixels=pix, deposits_e=dep, length_px=L))
            # tracks entering the crop from outside (11 Nov 2026), separate random stream: in-crop hits unchanged
            if cfg.get('entering_tracks', E.get('particles.entering_tracks', True)):
                from .particles import sample_entering
                x0c, y0c = getattr(self.scene, 'crop', (0, 0, self.w, self.h))[:2]
                Wf, Hf = int(self.sensor['array.width_px']), int(self.sensor['array.height_px'])
                rate_px = flux * pitch_cm ** 2
                if model == 'let_spectrum':
                    M = 400
                    par = None
                else:
                    M = int(E['particles.track_len_px'][1])
                    par = dict(fh=fh, lo=lo, hi=hi, mip=E['particles.mip_deposit_e'], mip_sig=E['particles.mip_sigma_ln'],
                               L0=L0, L1=L1)
                if getattr(self.scene, 'kind', 'map') == 'map':
                    bounds = (max(-x0c, -M), min(Wf - x0c, self.w + M), max(-y0c, -M), min(Hf - y0c, self.h + M))
                else:
                    bounds = (-M, self.w + M, -M, self.h + M)
                rng_e = np.random.default_rng(self.seed + 79)
                hits += sample_entering(rng_e, rate_px, self.duration, self.w, self.h, Ep if model == 'let_spectrum' else E,
                                        self.sensor['array.pixel_pitch_um'], bounds, start_id=len(hits), max_px=M,
                                        model=model, param=par)
            # optional stress of the deposit model: lateral charge diffusion (Gaussian, sigma px) and delayed
            # collection of a fraction `collection_tail_fraction` of the charge (exponential, time constant s, split
            # into n pieces; the rest arrives promptly). Defaults reproduce the instantaneous single-pixel deposit.
            # Prompt collection in silicon pixel sensors takes ns to tens of ns (adjacent-device literature), i.e.
            # instantaneous here; millisecond tails need a specific trap/persistence/electronics mechanism and are
            # robustness stresses, not expected flight behaviour.
            sig = float(cfg.get('diffusion_sigma_px', 0.0)); tauc = float(cfg.get('collection_tau_s', 0.0))
            npc = int(cfg.get('collection_pieces', 8)); ftail = float(cfg.get('collection_tail_fraction', 1.0))
            if sig > 0 or tauc > 0:
                rng2 = np.random.default_rng(self.seed + 78)
                for hh in hits:
                    acc = {}
                    for (xx, yy), e in zip(hh['pixels'], hh['deposits_e']):
                        if sig > 0:
                            r = int(math.ceil(3 * sig))
                            from math import erf
                            fr = [0.5 * (erf((k + 0.5) / (sig * 2 ** 0.5)) - erf((k - 0.5) / (sig * 2 ** 0.5))) for k in range(-r, r + 1)]
                            for i, fy in enumerate(fr):
                                for j, fx in enumerate(fr):
                                    px, py = xx + j - r, yy + i - r
                                    if 0 <= px < self.w and 0 <= py < self.h and fx * fy * e > 1.0:
                                        acc[(px, py)] = acc.get((px, py), 0.0) + fx * fy * e
                        else:
                            acc[(xx, yy)] = acc.get((xx, yy), 0.0) + e
                    hh['pixels'] = list(acc); hh['deposits_e'] = list(acc.values())
                    if tauc > 0:
                        dts = rng2.exponential(tauc, (len(acc), npc))
                        hh['pieces_dt_s'] = dts.tolist(); hh['tail_fraction'] = ftail
        self.hits = hits
        lists = [[] for _ in range(self.P)]
        for hh in hits:
            for k, ((xx, yy), e) in enumerate(zip(hh['pixels'], hh['deposits_e'])):
                if 'pieces_dt_s' in hh:
                    ft = hh.get('tail_fraction', 1.0)
                    if ft < 1.0:
                        lists[yy * self.w + xx].append((hh['t'], e * (1.0 - ft)))
                    for dtp in hh['pieces_dt_s'][k]:
                        lists[yy * self.w + xx].append((hh['t'] + dtp, e * ft / len(hh['pieces_dt_s'][k])))
                else:
                    lists[yy * self.w + xx].append((hh['t'], e))
        for l in lists:
            l.sort()
        ptr = np.zeros(self.P + 1, np.int64); ptr[1:] = np.cumsum([len(l) for l in lists])
        self.dp_ptr = ptr
        self.dp_t = np.array([a for l in lists for a, _ in l], np.float64)
        self.dp_e = np.array([b for l in lists for _, b in l], np.float64)

    # ---------------- run ----------------
    def run(self):
        S, P = self.sensor, self.P
        t_wall = time.time()
        bg0 = self.scene.photo_rate(0.0).ravel().astype(np.float64)
        I0 = bg0 + self.dark
        J = I0.copy(); J2 = np.log(np.maximum(J, 1.0)); Vp = J2.copy()
        ref = Vp.copy()
        if S['events.initial_reference'] == 'random':
            # reference uniform inside the dead band: above the level by less than C_off, below it by less than C_on
            # (10 Nov 2026; before, the side was paired with a randomly chosen threshold, which is the same thing
            # only while C_on = C_off per pixel, as in every shipped profile; results for those are bit-identical)
            u = self.rng.uniform(-1, 1, P)
            self.rng.random(P)                       # unused draw, kept so the random stream is unchanged
            ref = ref + u * np.where(u > 0, self.C_off, self.C_on)
        blind = np.full(P, -1e30); next_ba = np.full(P, -1e30)
        tf = S['ba.telegraph_fraction']
        tstate = (self.rng.random(P) < tf).astype(np.int8) if tf > 0 else np.zeros(P, np.int8)
        next_sw = np.where(tstate == 1, self.rng.exponential(S['ba.telegraph_dwell_s'], P),
                           self.rng.exponential(S['ba.telegraph_dwell_s'] * (1 - tf) / max(tf, 1e-9), P)) if tf > 0 else np.full(P, 1e30)
        rng_st = pk.seed_states(self.seed, P)
        dp_next = self.dp_ptr[:-1].copy()
        law_sqrt = S['photoreceptor.law'] == 'sqrt'
        euler = S['photoreceptor.integrator'] == 'euler_s10'
        ba_leak = S['ba.model'] == 'leak_drift'
        adapt = bool(S.get('photoreceptor.adaptive_substeps', False))
        sub_frac = float(S.get('photoreceptor.substep_tau_fraction', 0.5))
        sub_dln = float(S.get('photoreceptor.substep_dlnJ_max', 0.1))
        sub_hmin = float(S.get('photoreceptor.substep_min_s', 5e-6))
        tau_hp = float(S.get('photoreceptor.hpf_tau_s', 0.0) or 0.0)
        dep_impulse = S.get('photoreceptor.deposit_model', 'step_current') == 'impulse'
        VLP = Vp.copy(); VLP0 = Vp.copy()
        n_sub_total = 0
        fa = self.f_arr
        n_chunks = int(math.ceil(self.duration / self.chunk_s - 1e-9))
        nsteps_c = int(round(self.chunk_s / self.dt))
        evs = []
        cap = 64
        self.bg_chunks = []
        t_scene = 0.0
        for c in range(n_chunks):
            t0 = c * self.chunk_s
            ns = min(nsteps_c, int(round((self.duration - t0) / self.dt)))
            kt = np.arange(t0, t0 + ns * self.dt + self.kf_dt * 1.01, self.kf_dt)
            if len(kt) < 2:
                kt = np.array([t0, t0 + ns * self.dt])
            ts = time.time()
            kf = np.stack([self.scene.photo_rate(tt).ravel() for tt in kt], 1).astype(np.float64)
            t_scene += time.time() - ts
            self.bg_chunks.append(kf.mean(1).reshape(self.h, self.w) + self.dark.reshape(self.h, self.w))
            saved = [a.copy() for a in (J, J2, Vp, ref, blind, next_ba, tstate, next_sw, rng_st, dp_next, VLP)]
            while True:
                out_t = np.zeros((self.h, cap)); out_p = np.zeros((self.h, cap), np.int32)
                out_pol = np.zeros((self.h, cap), np.int8); out_src = np.zeros((self.h, cap), np.int8)
                counts = np.zeros(self.h, np.int64); nsub = np.zeros(self.h, np.int64)
                pk.run_chunk(t0, ns, self.dt, kt, kf, self.dark, self.ba, self.C_on, self.C_off, self.masked,
                             self.px_x, self.px_y, self.w,
                             self.fl_ptr, self.fl_idx, fa['t0'], fa['x0'], fa['y0'], fa['vx'], fa['vy'], fa['amp'],
                             fa['tau'], fa['kind'], fa['norm'], fa['tcut'], fa['sep'],
                             self.optics['psf.sigma_px'], self.optics['psf.halo_sigma_px'], self.optics['psf.halo_fraction'], RISE_S,
                             self.dp_ptr, self.dp_t, self.dp_e, dp_next,
                             J, J2, Vp, ref, blind, next_ba, tstate, next_sw, rng_st,
                             law_sqrt, S['photoreceptor.tau_ref_s'], S['photoreceptor.I_ref_e_s'], S['photoreceptor.tau_cap_s'],
                             S['photoreceptor.tau_min_s'], euler, S['photoreceptor.second_stage_tau_s'], S['events.refractory_s'],
                             S['events.loss_fraction'], ba_leak, S['ba.on_fraction'], S['ba.burst_mean'], tf,
                             S['ba.telegraph_gain'], S['ba.telegraph_dwell_s'],
                             adapt, sub_frac, sub_dln, sub_hmin, tau_hp, VLP, VLP0, dep_impulse,
                             out_t, out_p, out_pol, out_src, counts, nsub)
                if counts.max() <= cap:
                    break
                cap = int(counts.max() * 1.5) + 64
                J, J2, Vp, ref, blind, next_ba, tstate, next_sw, rng_st, dp_next, VLP = [a.copy() for a in saved]
            n_sub_total += int(nsub.sum())
            sel = np.arange(cap)[None, :] < counts[:, None]
            e = dict(t=out_t[sel], p=out_p[sel], pol=out_pol[sel], src=out_src[sel])
            o = np.argsort(e['t'], kind='stable')
            evs.append({k: v[o] for k, v in e.items()})
            cap = max(64, int(counts.max() * 1.2) + 64)
        raw = {k: np.concatenate([e[k] for e in evs]) for k in evs[0]}
        t_pix = time.time() - t_wall - t_scene
        raw['x'] = (raw['p'] % self.w).astype(np.uint16); raw['y'] = (raw['p'] // self.w).astype(np.uint16)
        frac = P / (S['array.width_px'] * S['array.height_px'])
        ev, rstats = ro.readout(raw, S, frac)
        ev, estats = ro.esp(ev, S, self.w, self.h, frac, np.random.default_rng(self.seed + 5))
        self.events = ev
        self.stats = dict(n_raw=int(raw['t'].size), readout=rstats, esp=estats, wall_pixel_s=t_pix, wall_scene_s=t_scene,
                          n_events=int(ev['t'].size), n_on=int((ev['pol'] == 1).sum()), n_off=int((ev['pol'] == -1).sum()),
                          n_ba=int((ev['src'] == 1).sum()), extra_substeps=n_sub_total,
                          integrator=dict(adaptive_substeps=adapt and S['photoreceptor.integrator'] != 'euler_s10',
                                          tau_fraction=sub_frac, dlnJ_max=sub_dln, h_min_s=sub_hmin, dt_s=self.dt,
                                          hpf_tau_s=tau_hp, deposit_impulse=bool(dep_impulse and not euler)))
        self.log(f"  pixel kernel {t_pix:.1f} s, scene {t_scene:.1f} s, events {ev['t'].size} "
                 f"({ev['t'].size / self.duration / P:.3g} ev/s/px)")
        return ev

    # ---------------- trigger and energy ----------------
    def onboard_background(self, b):
        """The background map the on-board trigger is given: the true chunk background, optionally misregistered
        (trigger_cfg map_shift_px = (dx, dy), pointing/map error) and scaled (map_scale_err, common error)."""
        tc = self.trigger_cfg
        sh = tc.get('map_shift_px') or (0, 0)
        if sh[0] or sh[1]:
            from scipy import ndimage
            b = ndimage.shift(b, (sh[1], sh[0]), order=0, mode='nearest')
        return b * (1.0 + tc.get('map_scale_err', 0.0))

    def detect(self, calib=None):
        tc = self.trigger_cfg
        S = self.sensor
        case = S.s10_case if getattr(S, 's10_case', None) else tc['case']
        sens, info = trg.threshold_model(case, S, self.optics, tc.get('threshold_model', 'fixed'))
        table = trg.ThresholdTable(case, mode=tc['mode'], lit_limit=tc['lit_limit'], lit_margin=tc['lit_margin'],
                                   sens=sens, group_bg=tc.get('group_bg', 'hetero'), model=tc.get('threshold_model', 'fixed'),
                                   info=info)
        t_w = time.time()
        maps = np.stack([table.maps(self.onboard_background(b), tc['allow2'], tc['allow3']) for b in self.bg_chunks])
        self.thr_maps = maps
        self.threshold_info = table.describe()
        trig = trg.run_trigger(self.events, self.w, self.h, maps, self.chunk_s, t_end=self.duration)
        dets = trg.cluster(trig)
        dets = trg.match(dets, self.flashes, self.hits)
        self.stats['exposure'] = exposure_stats(maps, self.w, self.h, self.masked, tc['allow2'], tc['allow3'])
        bg_mean = np.mean(self.bg_chunks, 0)
        if tc.get('energy_bg', 'onset_chunk') == 'onset_chunk':
            nch = len(self.bg_chunks)
            bg_src = lambda t: self.onboard_background(self.bg_chunks[min(max(int(t // self.chunk_s), 0), nch - 1)])
        else:
            bg_src = self.onboard_background(bg_mean)
        rng = np.random.default_rng(self.seed + 9)
        for d in dets:
            m = trg.measure_energy(d, self.events, self.w, self.h, self.C_on, self.C_off, bg_src, self.scene.range_km,
                                   self.rad.flash_electrons_per_J, rng, bg_err=tc.get('bg_err', 0.05),
                                   t_end=self.duration, gain=self.scene.point_gain_map)
            d['energy'] = m
            if m and calib is not None and not m['censored']:
                d['energy']['e_corr_J'], d['energy']['outside_training_range'] = trg.apply_correction(m, calib)
        self.triggers = trig
        self.detections = dets
        self.stats['wall_trigger_s'] = time.time() - t_w
        self.stats['n_trigger_rows'] = int(len(trig))
        return dets

    def summary(self):
        fl, dets = self.flashes, self.detections
        found = {}
        for d in dets:
            if d['label'] == 'flash' and d['match'] not in found:
                found[d['match']] = d
        per_flash = []
        for i, f in enumerate(fl):
            d = found.get(i)
            row = dict(id=i, t_on=f['t_on'], x=f['x'], y=f['y'], E_J=f['E_J'], tau_s=f['tau_s'], kind=f['kind'],
                       range_km=f['range_km'], electrons=f['electrons'], detected=d is not None)
            if d is not None:
                row.update(t_trig=d['t_trig'], lag_s=d['t_trig'] - f['t_on'], W=d['W'])
                if d.get('energy'):
                    row.update(onset_err_s=d['energy']['onset_est'] - f['t_on'], e_raw_J=d['energy']['e_raw_J'],
                               ln_err_raw=math.log(max(d['energy']['e_raw_J'], 1e-9) / f['E_J']),
                               censored=d['energy'].get('censored', False), active_s=d['energy']['active_s'])
                    if 'e_corr_J' in d['energy']:
                        row['ln_err_corr'] = math.log(max(d['energy']['e_corr_J'], 1e-9) / f['E_J'])
                        row['outside_training_range'] = d['energy'].get('outside_training_range')
            per_flash.append(row)
        n_false = sum(d['label'] == 'false' for d in dets)
        n_part = sum(d['label'] == 'particle' for d in dets)
        n_false_near = sum(d['label'] == 'false' and 'near_flash' in d for d in dets)
        return dict(n_flashes=len(fl), n_detected=len(found), n_detections=len(dets), n_false=n_false,
                    n_false_near_flash=n_false_near,
                    n_particle_triggers=n_part, n_particle_hits=len(self.hits),
                    n_heavy_hits=sum(h['heavy'] for h in self.hits), per_flash=per_flash)


def correction_features(m):
    return trg.correction_features(m)


def exposure_stats(maps, w, h, masked, allow2=None, allow3=None):
    """Trigger exposure lost to the illumination mask and the count cap, from the per-chunk threshold maps
    (nchunk, 4 windows, 2 sizes, h, w): per window and group size the disabled share of the valid anchors, and per
    window the share of pixel-chunks not contained in ANY enabled 2x2 or 3x3 group (such pixels cannot contribute
    to a trigger in that window). Hot-masked pixels emit no events and are counted separately. This is crop- and
    run-specific; it is not a whole-Moon completeness map."""
    out = dict(masked_pixel_fraction=float(masked.mean()), by_window={})
    W_ = trg.WINDOWS
    for wi, W in enumerate(W_):
        row = {}
        cov_any = np.zeros((maps.shape[0], h, w), bool)
        for si, s in enumerate((2, 3)):
            en = maps[:, wi, si, :h - s + 1, :w - s + 1] < trg.DISABLED
            allow = allow2 if si == 0 else allow3
            valid = np.ones(en.shape[1:], bool) if allow is None else allow[:h - s + 1, :w - s + 1]
            row[f'disabled_{s}x{s}_anchor_fraction'] = float((~en[:, valid]).mean()) if valid.any() else None
            full = np.zeros((maps.shape[0], h, w), bool); full[:, :h - s + 1, :w - s + 1] = en & valid
            # a pixel (y, x) lies in the s x s groups anchored at (y - dy, x - dx), 0 <= dy, dx < s
            cov = np.zeros_like(full)
            for dy in range(s):
                for dx in range(s):
                    cov[:, dy:, dx:] |= full[:, :h - dy, :w - dx]
            cov_any |= cov
        row['uncovered_pixel_fraction'] = float((~cov_any).mean())
        out['by_window'][f'{W:g}'] = row
    out['disabled_2x2_anchor_fraction'] = out['by_window']['2']['disabled_2x2_anchor_fraction']
    return out
