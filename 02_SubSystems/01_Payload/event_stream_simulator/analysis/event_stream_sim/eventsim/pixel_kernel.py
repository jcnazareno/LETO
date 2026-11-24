"""Numba pixel front end: photons -> photoreceptor -> change detector -> events (one call per time chunk).

Per pixel and time step dt (0.5 ms default, finer allowed):
  1. photo-electrons ~ Poisson((background(t) + dark_i + flash_i(t)) h) + particle deposits in this (sub)step;
  2. photoreceptor: first-order low-pass of the photocurrent, tau = tau_ref (I_ref/J)^g (g = 1 linear, 0.5 sqrt),
     clipped to [tau_min, tau_cap]; 'euler_s10' integrator reproduces S10 (Euler, tau clipped at dt), otherwise
     exponential update with tau frozen over the (sub)step; optional second pole (source follower) on ln J with
     fixed tau2; optional first-order high-pass (time constant tau_hp, a bias_hpf stand-in) on the comparator input;
     ADAPTIVE SUB-STEPS (4 Nov 2026 review, E02): unless 'euler_s10', a step is split into m equal sub-steps when the
     photoreceptor is faster than the step or ln J would change by more than dlnmax in it:
     m = max(ceil(dt / (frac tau)), ceil(|d ln J| / dlnmax)), capped so that h = dt/m >= h_min. Each sub-step
     draws its own Poisson photons (so the photon-noise bandwidth follows tau, not the global step), re-evaluates
     the flash light curve at the sub-step centre and runs the comparator on its own segment. m = 1 (identical to
     the earlier kernel) for all dim pixels;
     CHARGE IMPULSES (handoff 3.3, 11 Nov 2026): with dep_impulse (profile photoreceptor.deposit_model = 'impulse',
     not with 'euler_s10') a particle deposit Q is not added to the sub-step's mean current but applied as the exact
     response of dJ/dt = (I - J)/tau(J) to Q delta(t): integral of tau(J) dJ from J0 to J1 equals Q, with tau clipped
     to [tau_min, tau_cap] (linear law: d ln J = Q/K, K = tau_ref I_ref, between the clips; tau_min bounds the rise
     as dJ = Q/tau_min; sqrt law: d sqrt(J) = Q/(2 tau_ref sqrt(I_ref))). The comparator sees the jump at the
     deposit time (a 0.1 us segment between the continuous parts of the sub-step; each deposit separately), so a jump gives one ON event per
     refractory period as an instantaneous step would, independent of the step length; the decay inside the rest of
     that sub-step is neglected and the following steps resolve it with the adaptive sub-steps. With a second pole
     or high-pass enabled the jump falls back to the end of the sub-step (linear comparator segment). Same random
     draws as before ('step_current' reproduces the earlier kernel);
  3. change detector on V = ln J (linear in time within a step): an ON (OFF) event when V - ref >= C_on,i
     (ref - V >= C_off,i), at the interpolated crossing time; after an event the pixel is blind for the
     refractory period and its reference is reset to V at the end of it (refractory 0 -> ref += C, as S10);
     each event is lost with probability `loss` (the reference still moves);
  4. background activity: 'poisson_additive' (S10) adds independent events at per-pixel rate r_i (optional bursts
     and telegraph switching) that do not move the reference and ignore the refractory period; 'leak_drift'
     moves the reference down at r_i * C_on,i per second so that leak events pass through the comparator.
Counter-based xoroshiro128+ generators per pixel make results independent of thread count.
"""
import math
import numpy as np
import numba as nb


@nb.njit(inline='always')
def _rotl(x, k):
    return (x << np.uint64(k)) | (x >> np.uint64(64 - k))


@nb.njit(inline='always')
def _next(st, p):
    s0 = st[p, 0]; s1 = st[p, 1]
    r = s0 + s1
    s1 ^= s0
    st[p, 0] = _rotl(s0, 24) ^ s1 ^ (s1 << np.uint64(16))
    st[p, 1] = _rotl(s1, 37)
    return r


@nb.njit(inline='always')
def _unif(st, p):
    return (float(_next(st, p) >> np.uint64(11)) + 0.5) * (1.0 / 9007199254740992.0)


@nb.njit(cache=True)
def _poisson(st, p, lam):
    if lam <= 0.0:
        return 0.0
    if lam < 30.0:
        L = math.exp(-lam); k = 0; prod = _unif(st, p)
        while prod > L:
            k += 1; prod *= _unif(st, p)
        return float(k)
    slam = math.sqrt(lam); loglam = math.log(lam)
    b = 0.931 + 2.53 * slam; a = -0.059 + 0.02483 * b
    invalpha = 1.1239 + 1.1328 / (b - 3.4); vr = 0.9277 - 3.6224 / (b - 2.0)
    while True:
        U = _unif(st, p) - 0.5; V = _unif(st, p)
        us = 0.5 - abs(U)
        k = math.floor((2.0 * a / us + b) * U + lam + 0.43)
        if us >= 0.07 and V <= vr:
            return k
        if k < 0 or (us < 0.013 and V > us):
            continue
        if (math.log(V) + math.log(invalpha) - math.log(a / (us * us) + b)) <= (-lam + k * loglam - math.lgamma(k + 1.0)):
            return k


@nb.njit(cache=True)
def seed_states(seed, n):
    st = np.empty((n, 2), np.uint64)
    for i in range(n):
        z = np.uint64(seed) * np.uint64(0x9E3779B97F4A7C15) + np.uint64(i) * np.uint64(0xBF58476D1CE4E5B9) + np.uint64(1)
        for j in range(2):
            z = z + np.uint64(0x9E3779B97F4A7C15)
            x = z
            x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
            x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
            st[i, j] = x ^ (x >> np.uint64(31))
    return st


@nb.njit(inline='always')
def _psf1(x0, x1, c, s1, s2, h):
    r1 = 1.0 / (s1 * 1.4142135623730951)
    v = 0.5 * (math.erf((x1 - c) * r1) - math.erf((x0 - c) * r1))
    if h > 0.0:
        r2 = 1.0 / (s2 * 1.4142135623730951)
        v = (1.0 - h) * v + h * 0.5 * (math.erf((x1 - c) * r2) - math.erf((x0 - c) * r2))
    return v


@nb.njit(inline='always')
def _profile(t, tau, kind, rise):
    if t <= 0.0:
        return 0.0
    r = 1.0 - math.exp(-t / rise)
    if kind == 0:
        return r * math.exp(-t / tau)
    elif kind == 1:
        tf = tau / 10.0
        return r * (0.3 / tf * math.exp(-t / tf) + 0.7 / tau * math.exp(-t / tau))
    else:
        return r * (1.0 + t / tau) ** -2.5


@nb.njit(inline='always')
def _flash_rate(tm, fa, fb, fl_idx, f_t0, f_x0, f_y0, f_vx, f_vy, f_amp, f_tau, f_kind, f_norm, f_tcut,
                pxx, pxy, psf_s1, psf_s2, psf_h, rise, fcache_t, fcache_v):
    r = 0.0
    for q in range(fa, fb):
        f = fl_idx[q]
        tt = tm - f_t0[f]
        if tt <= 0.0 or tt > f_tcut[f]:
            continue
        # PSF fraction of this pixel, refreshed every 10 ms of flash time (drift <= 0.005 px)
        if fcache_t[q - fa] < -1.0 or tt - fcache_t[q - fa] > 0.01:
            cx = f_x0[f] + f_vx[f] * tt
            cy = f_y0[f] + f_vy[f] * tt
            fx = _psf1(pxx, pxx + 1.0, cx, psf_s1, psf_s2, psf_h)
            fy = _psf1(pxy, pxy + 1.0, cy, psf_s1, psf_s2, psf_h)
            fcache_v[q - fa] = f_amp[f] * fx * fy * f_norm[f]
            fcache_t[q - fa] = tt
        if fcache_v[q - fa] > 0.0:
            r += fcache_v[q - fa] * _profile(tt, f_tau[f], f_kind[f], rise)
    return r


@nb.njit(inline='always')
def _tau_of(Jc, law_sqrt, tau_ref, I_ref):
    if law_sqrt:
        return tau_ref * math.sqrt(I_ref / Jc)
    return tau_ref * (I_ref / Jc)


@nb.njit(inline='always')
def _impulse(J0, Q, law_sqrt, tau_ref, I_ref, tau_min, tau_cap):
    """Exact photoreceptor state after an instantaneous charge Q [e-]: solve int_{J0}^{J1} tau(J) dJ = Q."""
    if law_sqrt:
        A = tau_ref * math.sqrt(I_ref)
        Ja = (A / tau_cap) ** 2
        Jb = (A / tau_min) ** 2
    else:
        K = tau_ref * I_ref
        Ja = K / tau_cap
        Jb = K / tau_min
    J = J0
    rem = Q
    if J < Ja:                                    # tau clipped at tau_cap: linear in J
        step = tau_cap * (Ja - J)
        if rem <= step:
            return J + rem / tau_cap
        rem -= step
        J = Ja
    if J < Jb:                                    # unclipped law
        if law_sqrt:
            sq = math.sqrt(J) + rem / (2.0 * A)
            Jn = sq * sq
            if Jn <= Jb:
                return Jn
            rem -= 2.0 * A * (math.sqrt(Jb) - math.sqrt(J))
        else:
            x = rem / K
            if x < math.log(Jb / J):
                return J * math.exp(x)
            rem -= K * math.log(Jb / J)
        J = Jb
    return J + rem / tau_min                      # tau clipped at tau_min


@nb.njit(inline='always')
def _cmp_seg(p, row, a0, a1, Va, Vb, con, coff, loss, rec, refr, ref, blind, rng, out_t, out_p, out_pol, out_src,
             n_out, cap):
    """Comparator on one linear segment [a0, a1] of V (same rules as the main loop). Returns the new n_out."""
    L = a1 - a0
    if blind[p] >= a1:
        ref[p] = Vb
        return n_out
    s = a0
    if blind[p] > a0:
        s = blind[p]
        ref[p] = Va + (Vb - Va) * (s - a0) / L
    guard = 0
    while guard < 4096:
        guard += 1
        pol = 0
        if Vb - ref[p] >= con:
            pol = 1; lev = ref[p] + con
        elif ref[p] - Vb >= coff:
            pol = -1; lev = ref[p] - coff
        else:
            break
        if Vb != Va:
            tc = a0 + (lev - Va) / (Vb - Va) * L
        else:
            tc = s
        if tc < s:
            tc = s
        if tc > a1 - 1e-10:
            tc = a1 - 1e-10
        if _unif(rng, p) >= loss and rec:
            if n_out < cap:
                out_t[row, n_out] = tc; out_p[row, n_out] = p
                out_pol[row, n_out] = pol; out_src[row, n_out] = 0
            n_out += 1
        if refr > 0.0:
            blind[p] = tc + refr
            if blind[p] >= a1:
                ref[p] = Vb
                break
            s = blind[p]
            ref[p] = Va + (Vb - Va) * (s - a0) / L
        else:
            ref[p] = lev
            s = tc
    return n_out


@nb.njit(parallel=True, cache=True)
def run_chunk(t_start, nsteps, dt, kf_t, kf_bg, dark, ba_rate, C_on, C_off, masked, px_x, px_y, width,
              fl_ptr, fl_idx, f_t0, f_x0, f_y0, f_vx, f_vy, f_amp, f_tau, f_kind, f_norm, f_tcut, f_sep,
              psf_s1, psf_s2, psf_h, rise,
              dp_ptr, dp_t, dp_e, dp_next,
              J, J2, Vp, ref, blind, next_ba, tstate, next_sw, rng,
              law_sqrt, tau_ref, I_ref, tau_cap, tau_min, euler, tau2, refr, loss,
              ba_leak, on_frac, burst_m, tele_f, tele_h, tele_dwell,
              adapt, sub_frac, sub_dlnmax, sub_hmin, tau_hp, VLP, VLP0, dep_impulse,
              out_t, out_p, out_pol, out_src, counts, nsub_out):
    H = counts.shape[0]
    cap = out_t.shape[1]
    K = kf_t.shape[0]
    m_cap = int(dt / sub_hmin + 1e-9) if sub_hmin > 0.0 else 1
    if m_cap < 1:
        m_cap = 1
    imp = dep_impulse and not euler
    for row in nb.prange(H):
        n_out = 0
        n_sub_extra = 0
        for col in range(width):
            p = row * width + col
            jk = 0
            dk = dark[p]
            rba = ba_rate[p]
            con = C_on[p]; coff = C_off[p]
            rec = not masked[p]
            fa = fl_ptr[p]; fb = fl_ptr[p + 1]
            fcache_t = np.full(max(fb - fa, 1), -1e30)
            fcache_v = np.zeros(max(fb - fa, 1))
            # telegraph rates
            if tele_f > 0.0:
                r_low = rba / (1.0 - tele_f + tele_f * tele_h)
            else:
                r_low = rba
            for k in range(nsteps):
                t0 = t_start + k * dt
                t1 = t0 + dt
                tm = t0 + 0.5 * dt
                while jk < K - 2 and kf_t[jk + 1] <= tm:
                    jk += 1
                wk = (tm - kf_t[jk]) / (kf_t[jk + 1] - kf_t[jk])
                if wk < 0.0:
                    wk = 0.0
                elif wk > 1.0:
                    wk = 1.0
                bg = kf_bg[p, jk] + (kf_bg[p, jk + 1] - kf_bg[p, jk]) * wk
                rate0 = bg + dk
                rate = rate0
                if fb > fa:
                    rate += _flash_rate(tm, fa, fb, fl_idx, f_t0, f_x0, f_y0, f_vx, f_vy, f_amp, f_tau, f_kind, f_norm,
                                        f_tcut, px_x[p], px_y[p], psf_s1, psf_s2, psf_h, rise, fcache_t, fcache_v)
                # number of sub-steps
                m = 1
                if adapt and (not euler) and m_cap > 1:
                    Jc = J[p]
                    if Jc < 1.0:
                        Jc = 1.0
                    tau = _tau_of(Jc, law_sqrt, tau_ref, I_ref)
                    if tau < tau_min:
                        tau = tau_min
                    if tau > tau_cap:
                        tau = tau_cap
                    a1 = dt / (sub_frac * tau)
                    gg = 1.0 - math.exp(-dt / tau)
                    jn = Jc + gg * (rate - Jc)
                    if jn < 1.0:
                        jn = 1.0
                    a2 = abs(math.log(jn / Jc)) / sub_dlnmax
                    a = a1 if a1 > a2 else a2
                    if a > 1.0:
                        m = int(math.ceil(a - 1e-12))
                        if m > m_cap:
                            m = m_cap
                h = dt / m
                n_sub_extra += m - 1
                for si in range(m):
                    s0 = t0 + si * h
                    s1 = s0 + h
                    if si == m - 1:
                        s1 = t1
                    rs = rate
                    if m > 1 and fb > fa:
                        rs = rate0 + _flash_rate(s0 + 0.5 * h, fa, fb, fl_idx, f_t0, f_x0, f_y0, f_vx, f_vy, f_amp, f_tau,
                                                 f_kind, f_norm, f_tcut, px_x[p], px_y[p], psf_s1, psf_s2, psf_h, rise,
                                                 fcache_t, fcache_v)
                    n = _poisson(rng, p, rs * h)
                    # particle deposits: impulses (exact jump below) or added to this sub-step's mean current
                    qdep = 0.0
                    Vq = 0.0
                    kq0 = dp_next[p]
                    while dp_next[p] < dp_ptr[p + 1] and dp_t[dp_next[p]] < s1:
                        if dp_t[dp_next[p]] >= s0:
                            if imp:
                                qdep += dp_e[dp_next[p]]
                            else:
                                n += dp_e[dp_next[p]]
                        dp_next[p] += 1
                    I = n / h
                    # photoreceptor
                    Jc = J[p]
                    if Jc < 1.0:
                        Jc = 1.0
                    tau = _tau_of(Jc, law_sqrt, tau_ref, I_ref)
                    if euler:
                        if tau < h:
                            tau = h
                        if tau > tau_cap:
                            tau = tau_cap
                        J[p] = J[p] + (h / tau) * (I - J[p])
                    else:
                        if tau < tau_min:
                            tau = tau_min
                        if tau > tau_cap:
                            tau = tau_cap
                        xx = h / tau
                        if xx < 0.01:
                            g = xx * (1.0 - 0.5 * xx * (1.0 - xx / 3.0))
                        else:
                            g = 1.0 - math.exp(-xx)
                        J[p] = J[p] + g * (I - J[p])
                        if qdep > 0.0:
                            Jq = J[p]
                            if Jq < 1.0:
                                Jq = 1.0
                            Vq = math.log(Jq)             # end of the continuous part, before the jump(s)
                            J[p] = _impulse(Jq, qdep, law_sqrt, tau_ref, I_ref, tau_min, tau_cap)   # = sequential jumps
                    Jv = J[p]
                    if Jv < 1.0:
                        Jv = 1.0
                    V1 = math.log(Jv)
                    if tau2 > 0.0:
                        J2[p] = J2[p] + (1.0 - math.exp(-h / tau2)) * (V1 - J2[p])
                        V1 = J2[p]
                    if tau_hp > 0.0:
                        VLP[p] = VLP[p] + (1.0 - math.exp(-h / tau_hp)) * (V1 - VLP[p])
                        V1 = V1 - VLP[p] + VLP0[p]
                    V0 = Vp[p]
                    Vp[p] = V1
                    if ba_leak:
                        ref[p] -= rba * con * h
                    # comparator with refractory period and crossing times interpolated within the sub-step
                    if qdep > 0.0 and imp and tau2 <= 0.0 and tau_hp <= 0.0:
                        # charge impulses: each deposit is its own instantaneous jump at its own time, between
                        # linear pieces of the continuous part (several deposits in one sub-step stay separate)
                        eps = 1e-7
                        Jcur = math.exp(Vq)
                        acc = 0.0
                        tprev = s0
                        Vprev = V0
                        for kk in range(kq0, dp_next[p]):
                            if dp_t[kk] < s0:
                                continue
                            td = dp_t[kk]
                            if td < tprev:
                                td = tprev
                            if td > s1 - 2.0 * eps:
                                td = s1 - 2.0 * eps
                            Vl = V0 + (Vq - V0) * (td - s0) / h + acc
                            if td > tprev:
                                n_out = _cmp_seg(p, row, tprev, td, Vprev, Vl, con, coff, loss, rec, refr, ref, blind, rng,
                                                 out_t, out_p, out_pol, out_src, n_out, cap)
                            Jn = _impulse(Jcur, dp_e[kk], law_sqrt, tau_ref, I_ref, tau_min, tau_cap)
                            dj = math.log(Jn / Jcur)
                            Jcur = Jn
                            n_out = _cmp_seg(p, row, td, td + eps, Vl, Vl + dj, con, coff, loss, rec, refr, ref, blind,
                                             rng, out_t, out_p, out_pol, out_src, n_out, cap)
                            acc += dj
                            tprev = td + eps
                            Vprev = Vl + dj
                        if s1 > tprev:
                            n_out = _cmp_seg(p, row, tprev, s1, Vprev, V1, con, coff, loss, rec, refr, ref, blind, rng,
                                             out_t, out_p, out_pol, out_src, n_out, cap)
                    elif blind[p] >= s1:
                        ref[p] = V1
                    else:
                        s = s0
                        if blind[p] > s0:
                            s = blind[p]
                            ref[p] = V0 + (V1 - V0) * (s - s0) / h
                        guard = 0
                        while guard < 4096:
                            guard += 1
                            pol = 0
                            if V1 - ref[p] >= con:
                                pol = 1; lev = ref[p] + con
                            elif ref[p] - V1 >= coff:
                                pol = -1; lev = ref[p] - coff
                            else:
                                break
                            if V1 != V0:
                                tc = s0 + (lev - V0) / (V1 - V0) * h
                            else:
                                tc = s
                            if tc < s:
                                tc = s
                            if tc > s1 - 1e-9:
                                tc = s1 - 1e-9
                            if _unif(rng, p) >= loss and rec:
                                if n_out < cap:
                                    out_t[row, n_out] = tc; out_p[row, n_out] = p
                                    out_pol[row, n_out] = pol; out_src[row, n_out] = 0
                                n_out += 1
                            if refr > 0.0:
                                blind[p] = tc + refr
                                if blind[p] >= s1:
                                    ref[p] = V1
                                    break
                                s = blind[p]
                                ref[p] = V0 + (V1 - V0) * (s - s0) / h
                            else:
                                ref[p] = lev
                                s = tc
                # additive background activity (independent of the comparator, S10)
                if (not ba_leak) and rba > 0.0:
                    if tele_f > 0.0:
                        while next_sw[p] < t1:
                            if tstate[p] == 1:
                                tstate[p] = 0
                                next_sw[p] += -math.log(_unif(rng, p)) * tele_dwell * (1.0 - tele_f) / tele_f
                            else:
                                tstate[p] = 1
                                next_sw[p] += -math.log(_unif(rng, p)) * tele_dwell
                            next_ba[p] = next_sw[p] - 1e9   # force redraw below at the new rate
                    reff = r_low * (tele_h if tstate[p] == 1 else 1.0) / burst_m
                    if next_ba[p] < t0 - 1e8:
                        next_ba[p] = t0 - math.log(_unif(rng, p)) / reff
                    while next_ba[p] < t1:
                        tb = next_ba[p]
                        m2 = 1
                        if burst_m > 1.0:
                            m2 = int(math.floor(math.log(_unif(rng, p)) / math.log(1.0 - 1.0 / burst_m))) + 1
                        for _ in range(m2):
                            pol = 1 if _unif(rng, p) < on_frac else -1
                            if rec:
                                if n_out < cap:
                                    out_t[row, n_out] = tb; out_p[row, n_out] = p
                                    out_pol[row, n_out] = pol; out_src[row, n_out] = 1
                                n_out += 1
                        next_ba[p] = tb - math.log(_unif(rng, p)) / reff
        counts[row] = n_out
        nsub_out[row] = n_sub_extra
