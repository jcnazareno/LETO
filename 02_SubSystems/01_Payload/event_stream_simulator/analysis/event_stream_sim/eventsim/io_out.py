"""Event and ground-truth files.

HDF5 (<run>.h5):
  /events/t  int64   time stamp [us] (readout time, quantised to the timestamp resolution)
  /events/x  uint16  column in the crop [px] (add attrs crop_x0 for the sensor column)
  /events/y  uint16  row in the crop [px]
  /events/p  uint8   polarity, 1 = ON, 0 = OFF
  /events_v2e uint32 (N, 4) [t_us, x, y, p] with p in {0, 1}: the ROW LAYOUT of the v2e dvs_h5 output, under a
             different dataset name (upstream v2e writes this matrix as the root dataset /events, which here is a
             group). For a reader that expects the upstream path use `export_v2e()` / `run_sim.py export-v2e`.
             uint32 microseconds wrap above 4294.967295 s: the matrix is then not written (int64 /events/t only).
  /truth/... flashes, particle hits, hot/masked pixel maps; attrs: JSON of the run configuration and profiles
NPZ (<run>_events.npz): t_us, x, y, p (+1/-1), src (0 = comparator, 1 = background activity), t_pixel_us
(pixel time before readout queueing), plus masked/hot/dark/ba/C_on/C_off maps.
JSON (<run>_truth.json): configuration, scene metadata, every injected flash and particle hit, detections,
summary statistics.
"""
from __future__ import annotations
import json
import math
import warnings
import numpy as np

UINT32_MAX_US = 2 ** 32 - 1


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return float(o) if math.isfinite(float(o)) else None
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def write_all(base, s, config, write_h5=True, write_v2e_matrix=True):
    ev = s.events
    t_us = np.round(ev['t'] * 1e6).astype(np.int64)
    p01 = (ev['pol'] == 1).astype(np.uint8)
    W, H = s.w, s.h
    np.savez_compressed(f'{base}_events.npz', t_us=t_us, x=ev['x'], y=ev['y'], p=ev['pol'].astype(np.int8),
                        src=ev['src'].astype(np.int8), t_pixel_us=np.round(ev['t_pixel'] * 1e6).astype(np.int64),
                        masked=s.masked.reshape(H, W), hot=s.hot.reshape(H, W),
                        dark_e_s=s.dark.reshape(H, W).astype(np.float32), ba_hz=s.ba.reshape(H, W).astype(np.float32),
                        C_on=s.C_on.reshape(H, W).astype(np.float32), C_off=s.C_off.reshape(H, W).astype(np.float32),
                        bg_mean_e_s=np.mean(s.bg_chunks, 0).astype(np.float32),
                        range_km=np.asarray(s.scene.range_km, np.float32))
    truth = dict(config=config, scene=s.scene.meta, stats=s.stats, summary=s.summary(), flashes=s.flashes,
                 particle_hits=s.hits, detections=getattr(s, 'detections', []), trigger=getattr(s, 'threshold_info', None),
                 hot_pixels=np.nonzero(s.hot)[0].tolist(), masked_pixels=np.nonzero(s.masked)[0].tolist(),
                 conventions=dict(t='us', x='crop column', y='crop row', p_h5='1 = ON, 0 = OFF',
                                  p_npz='+1 = ON, -1 = OFF', crop=list(s.scene.crop)))
    truth = _clean(truth)
    with open(f'{base}_truth.json', 'w') as f:
        json.dump(truth, f, indent=1)
    if write_h5:
        import h5py
        with h5py.File(f'{base}.h5', 'w') as h:
            g = h.create_group('events')
            for k, v in (('t', t_us), ('x', ev['x'].astype(np.uint16)), ('y', ev['y'].astype(np.uint16)), ('p', p01)):
                g.create_dataset(k, data=v, compression='gzip', compression_opts=4, shuffle=True)
            g.attrs['t_unit'] = 'us'; g.attrs['p_convention'] = '1 = ON, 0 = OFF'
            g.attrs['width'] = W; g.attrs['height'] = H
            g.attrs['crop_x0'] = s.scene.crop[0]; g.attrs['crop_y0'] = s.scene.crop[1]
            if write_v2e_matrix and t_us.size and int(t_us.max()) > UINT32_MAX_US:
                warnings.warn('event times exceed the uint32 microsecond range (4295 s): /events_v2e not written')
                h.attrs['events_v2e_omitted'] = 'times exceed uint32 microseconds'
            elif write_v2e_matrix:
                m = np.column_stack([t_us.astype(np.uint32), ev['x'].astype(np.uint32), ev['y'].astype(np.uint32), p01.astype(np.uint32)])
                d = h.create_dataset('events_v2e', data=m, compression='gzip', compression_opts=4, shuffle=True)
                d.attrs['columns'] = 't_us,x,y,p (p: 1 = ON, 0 = OFF); row layout of v2e --dvs_h5, which names the dataset /events'
            tg = h.create_group('truth')
            tg.create_dataset('masked', data=s.masked.reshape(H, W).astype(np.uint8), compression='gzip')
            tg.create_dataset('hot', data=s.hot.reshape(H, W).astype(np.uint8), compression='gzip')
            if s.flashes:
                tg.create_dataset('flashes', data=np.array([[f['t_on'], f['x'], f['y'], f['E_J'], f['tau_s'], f['range_km'], f['electrons'], f['vx'], f['vy']] for f in s.flashes]))
                tg['flashes'].attrs['columns'] = 't_on_s,x_px,y_px,E_L_J,tau_s,range_km,electrons,vx_px_s,vy_px_s'
            if s.hits:
                rows = [[hh['t'], px, py, e] for hh in s.hits for (px, py), e in zip(hh['pixels'], hh['deposits_e'])]
                tg.create_dataset('particle_deposits', data=np.array(rows))
                tg['particle_deposits'].attrs['columns'] = 't_s,x_px,y_px,electrons'
            h.attrs['config_json'] = json.dumps(_clean(config))
            h.attrs['scene_json'] = json.dumps(_clean(s.scene.meta))
    return truth


def export_v2e(npz_path, h5_path):
    """Write an upstream-v2e-layout file: root dataset /events, uint32 (N, 4) [t_us, x, y, p], p in {0, 1}
    (analysis/v2e/v2ecore/emulator.py). Refuses streams longer than the uint32 microsecond range."""
    import h5py
    z = np.load(npz_path)
    t = z['t_us'].astype(np.int64)
    if t.size and (t.min() < 0 or t.max() > UINT32_MAX_US):
        raise ValueError(f'{npz_path}: times outside 0..{UINT32_MAX_US} us cannot be stored as v2e uint32')
    m = np.column_stack([t.astype(np.uint32), z['x'].astype(np.uint32), z['y'].astype(np.uint32),
                         (z['p'] == 1).astype(np.uint32)])
    with h5py.File(h5_path, 'w') as h:
        h.create_dataset('events', data=m, maxshape=(None, 4), dtype='uint32', compression='gzip')
    return h5_path
