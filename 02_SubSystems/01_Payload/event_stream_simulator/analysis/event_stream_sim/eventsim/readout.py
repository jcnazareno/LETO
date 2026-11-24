"""Readout and on-chip event signal processing (ESP) applied to the time-ordered pixel events.

Order (as on the IMX636): arbiter/readout -> anti-flicker (AFK) -> spatio-temporal contrast / trail filter
(STC) -> event rate controller (ERC). All ESP blocks are off by default.
  * Readout: single-server queue with service time 1/R (R = sensor peak rate scaled to the crop's share of the
    array, assuming uniform activity elsewhere), FIFO depth scaled likewise; events that would wait longer than
    the FIFO depth are dropped. Time stamps are the readout times quantised to the timestamp resolution.
  * AFK (simplified functional model, not Sony's circuit): per 4x4 block, ON bursts that follow an OFF event start
    a 'cycle'; when `start` consecutive cycle periods fall in the 50-500 Hz band the block is muted until a period
    falls outside the band.
  * STC: per pixel, a burst is a run of same-polarity events separated by less than the threshold. stc_cut_trail
    keeps only the second event of each burst, stc_keep_trail keeps the second and later ones, trail keeps only
    the first one.
  * ERC: in each reference period (200 us) at most target_rate x period x crop share events pass; the excess is
    dropped at random.
"""
import math
import numpy as np
import numba as nb


@nb.njit(cache=True)
def _queue(t, R, depth):
    n = t.shape[0]
    out = np.empty(n); keep = np.ones(n, np.bool_)
    last = -1e30
    svc = 1.0 / R
    for i in range(n):
        to = t[i] if t[i] > last + svc else last + svc
        if (to - t[i]) * R > depth:
            keep[i] = False
            out[i] = t[i]
            continue
        out[i] = to; last = to
    return out, keep


def readout(ev, sensor, crop_fraction):
    t = ev['t']
    res = sensor['readout.timestamp_resolution_us'] * 1e-6
    lat = sensor['readout.fixed_latency_s']
    stats = dict(n_in=int(t.size), dropped_fifo=0, max_delay_s=0.0)
    if sensor['readout.limit_enabled'] and t.size:
        R = sensor['readout.max_rate_eps'] * crop_fraction
        depth = max(16.0, sensor['readout.fifo_events'] * crop_fraction)
        tout, keep = _queue(t, R, depth)
        stats['dropped_fifo'] = int((~keep).sum())
        stats['max_delay_s'] = float((tout - t)[keep].max()) if keep.any() else 0.0
        ev = {k: v[keep] for k, v in ev.items()}
        ev['t_pixel'] = ev['t'].copy()
        ev['t'] = tout[keep]
    else:
        ev['t_pixel'] = ev['t'].copy()
    ev['t'] = np.floor((ev['t'] + lat) / res + 1e-9) * res
    return ev, stats


@nb.njit(cache=True)
def _stc(t, p, pol, npx, thr, mode):
    keep = np.zeros(t.shape[0], np.bool_)
    last_t = np.full(npx, -1e30); last_pol = np.zeros(npx, np.int8); burst = np.zeros(npx, np.int32)
    for i in range(t.shape[0]):
        q = p[i]
        same = (pol[i] == last_pol[q]) and (t[i] - last_t[q] < thr)
        if same:
            burst[q] += 1
        else:
            burst[q] = 1
        if mode == 0:        # stc_cut_trail
            keep[i] = burst[q] == 2
        elif mode == 1:      # stc_keep_trail
            keep[i] = burst[q] >= 2
        else:                # trail
            keep[i] = burst[q] == 1
        last_t[q] = t[i]; last_pol[q] = pol[i]
    return keep


@nb.njit(cache=True)
def _afk(t, x, y, pol, nbx, nby, pmin, pmax, start):
    nb_ = nbx * nby
    keep = np.ones(t.shape[0], np.bool_)
    last_pol = np.zeros(nb_, np.int8); last_cyc = np.full(nb_, -1e30); good = np.zeros(nb_, np.int32)
    muted = np.zeros(nb_, np.bool_)
    for i in range(t.shape[0]):
        b = (y[i] // 4) * nbx + (x[i] // 4)
        if pol[i] == 1 and last_pol[b] == -1:
            per = t[i] - last_cyc[b]
            if pmin <= per <= pmax:
                good[b] += 1
                if good[b] >= start:
                    muted[b] = True
            else:
                good[b] = 0
                muted[b] = False
            last_cyc[b] = t[i]
        last_pol[b] = pol[i]
        if muted[b]:
            keep[i] = False
    return keep


def esp(ev, sensor, w, h, crop_fraction, rng):
    stats = {}
    if sensor['esp.afk_enabled'] and ev['t'].size:
        f0, f1 = sensor['esp.afk_band_hz']
        k = _afk(ev['t'], ev['x'].astype(np.int64), ev['y'].astype(np.int64), ev['pol'], (w + 3) // 4, (h + 3) // 4,
                 1.0 / f1, 1.0 / f0, int(sensor['esp.afk_start_periods']))
        stats['afk_dropped'] = int((~k).sum()); ev = {a: b[k] for a, b in ev.items()}
    if sensor['esp.stc_enabled'] and ev['t'].size:
        mode = {'stc_cut_trail': 0, 'stc_keep_trail': 1, 'trail': 2}[sensor['esp.stc_mode']]
        k = _stc(ev['t'], ev['p'].astype(np.int64), ev['pol'], w * h, float(sensor['esp.stc_threshold_s']), mode)
        stats['stc_dropped'] = int((~k).sum()); ev = {a: b[k] for a, b in ev.items()}
    if sensor['esp.erc_enabled'] and ev['t'].size:
        T = sensor['esp.erc_period_s']
        nmax = max(1, int(sensor['esp.erc_target_rate_eps'] * T * crop_fraction))
        b = np.floor(ev['t'] / T).astype(np.int64)
        key = rng.random(b.size)
        order = np.lexsort((key, b))
        bs = b[order]
        first = np.r_[0, np.nonzero(np.diff(bs))[0] + 1]
        rank = np.arange(bs.size) - np.repeat(first, np.diff(np.r_[first, bs.size]))
        k = np.zeros(b.size, bool); k[order[rank < nmax]] = True
        stats['erc_dropped'] = int((~k).sum()); ev = {a: v[k] for a, v in ev.items()}
    return ev, stats
