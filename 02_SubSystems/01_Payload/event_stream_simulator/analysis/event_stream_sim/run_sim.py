"""Event-stream simulator CLI (lunar impact-flash monitoring, SMD project).

Commands (run from this folder; outputs go to ../../data and ../../outputs):
  python run_sim.py run --scene nearside --sensor imx636 --crop 320x180 --duration 20 --flashes 8 --video
  python run_sim.py run --scene farside --full-frame --duration 2
  python run_sim.py run --scene particles --particles sep100 --duration 20 --video
  python run_sim.py compare --scene farside --sensors imx636,imx646 --duration 20     (side-by-side video)
  python run_sim.py calibrate --sensor imx636                                      (energy correction, S11 style)
  python run_sim.py profiles                                                       (list profiles)
  python run_sim.py export-v2e --tag nearside_imx636                                (upstream v2e /events file)
Options: --set sensor.ba.rate_hz=0.3 --set env.straylight.mode=gradient ... (any profile key; sections sensor,
optics, env), --dt (pixel step, s), --seed, --I0-target (earthshine scaled so the crop-mean background equals it),
--thresholds compute|stored, --threshold-model fixed|retuned, --group-bg max|geomean, --lit-limit (e-/s),
--map-shift DX,DY and --map-scale-err (on-board background/mask map errors), --energy-bg onset_chunk|run_mean,
--bg-err, --record-pad (s of stream kept after the last flash onset), --particle-diffusion-px,
--particle-collection-tau, --no-h5, --flash-spec "E_J:tau_s[:kind],...", --tag.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
import time
import resource
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eventsim import profiles, scenes, sim, io_out, render   # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'
FIG = ROOT / 'figures'
for d in (DATA, OUT, FIG):
    d.mkdir(parents=True, exist_ok=True)

E_CYCLE = (1e4, 2e4, 4e4, 1e5, 3e5, 2e4, 4e4, 1e5)
TAU_CYCLE = (0.03, 0.1, 0.1, 0.3, 1.0, 0.03, 0.3, 1.0)
# gcr*: CRaTER-derived LET spectrum (environment.json, 4 Nov 2026); *_x100 multiply the rate by 100 for statistics
# (equivalent to 100 crop runs). SEP presets keep the S10 parametric deposits (no SEP spectrum in the CRaTER days).
PARTICLES = {'none': None, 'gcr': {}, 'gcr_min': {'let_epoch': 'solar_min'},
             'gcr_max': {'let_epoch': 'solar_max', 'flux_cm2_s': 1.56},
             'gcr_min_x100': {'let_epoch': 'solar_min', 'flux_cm2_s': 405.0},
             'gcr_max_x100': {'let_epoch': 'solar_max', 'flux_cm2_s': 156.0},
             'sep10': {'flux_cm2_s': 31.4, 'model': 'parametric'}, 'sep100': {'flux_cm2_s': 314.0, 'model': 'parametric'},
             'sep1000': {'flux_cm2_s': 3140.0, 'model': 'parametric'}}


def load_profiles(sensor, optics='optics_16mm_f1', sets=()):
    P = dict(sensor=profiles.load(sensor), optics=profiles.load(optics), env=profiles.load('environment'))
    profiles.apply_overrides(P, sets)
    return P


def make_flashes(n, w, h, duration, seed, spec=None, margin=10, t_first=0.6, t_last_pad=4.5):
    """Flash onsets are drawn uniformly in [t_first, duration - t_last_pad] for any number of flashes (one flash
    included). The default pad of 4.5 s leaves the full 4 s energy record plus a margin inside the stream; if the
    interval is empty a warning is printed and records may be censored."""
    if duration - t_last_pad < t_first + 0.1:
        print(f'  warning: duration {duration} s leaves no room for complete {t_last_pad} s records; '
              'energy records may be censored (flagged, excluded from energy statistics)')
    rng = np.random.default_rng(seed)
    pairs = []
    if spec:
        for item in spec.split(','):
            parts = item.split(':')
            pairs.append((float(parts[0]), float(parts[1]), parts[2] if len(parts) > 2 else 'exp'))
        n = len(pairs)
    else:
        pairs = [(E_CYCLE[i % len(E_CYCLE)], TAU_CYCLE[i % len(TAU_CYCLE)], 'exp') for i in range(n)]
    if n == 0:
        return []
    times = np.sort(rng.uniform(t_first, max(duration - t_last_pad, t_first + 0.1), n))
    out = []
    for i, (E, tau, kind) in enumerate(pairs):
        for _ in range(200):
            x, y = rng.uniform(margin, w - margin), rng.uniform(margin, h - margin)
            if all(math.hypot(x - f['x'], y - f['y']) > 14 or abs(times[i] - f['t_on']) > 4.5 for f in out):
                break
        out.append(dict(t_on=float(times[i]), x=float(x), y=float(y), E_J=E, tau_s=tau, kind=kind))
    return out


def load_calibration(name):
    """Energy correction energy_calibration_<name>.json (sensor name, or --calib-tag of a calibrate run)."""
    p = DATA / f'energy_calibration_{name}.json'
    return json.loads(p.read_text()) if p.exists() else None


def peak_rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def run_one(args, sensor_name=None, write=True, log=print):
    sensor_name = sensor_name or args.sensor
    P = load_profiles(sensor_name, args.optics, args.set)
    w, h = map(int, args.crop.split('x'))
    t_all = time.time()
    sc = scenes.build(args.scene, P['sensor'], P['optics'], P['env'], crop_wh=(w, h), duration=args.duration,
                      full_frame=args.full_frame, earthshine='target_mean' if args.I0_target else None,
                      I0_target=args.I0_target, jitter_seed=args.jitter_seed)
    t_scene = time.time() - t_all
    fl = make_flashes(args.flashes, sc.w, sc.h, args.duration, args.seed + 1, args.flash_spec, t_last_pad=args.record_pad)
    part = PARTICLES[args.particles if args.particles else ('sep100' if args.scene == 'particles' else 'gcr')]
    if part is not None and (args.particle_diffusion_px or args.particle_collection_tau):
        part = dict(part, diffusion_sigma_px=args.particle_diffusion_px, collection_tau_s=args.particle_collection_tau,
                    collection_tail_fraction=args.particle_tail_fraction)
    s = sim.Simulation(sc, P['sensor'], P['optics'], P['env'], args.duration, dt=args.dt, seed=args.seed, flashes=fl,
                       particles=part, chunk_s=args.chunk, log=log,
                       trigger_cfg=dict(mode=args.thresholds, lit_limit=args.lit_limit, threshold_model=args.threshold_model,
                                        group_bg=args.group_bg, energy_bg=args.energy_bg, bg_err=args.bg_err,
                                        map_shift_px=tuple(map(float, args.map_shift.split(','))), map_scale_err=args.map_scale_err))
    s.run()
    s.detect(calib=load_calibration(args.calib_tag or sensor_name))
    sm = s.summary()
    s.stats['wall_total_s'] = time.time() - t_all
    s.stats['wall_scene_setup_s'] = t_scene
    s.stats['peak_rss_MB'] = peak_rss_mb()
    tag = args.tag or f'{args.scene}_{sensor_name}' + ('_full' if args.full_frame else '')
    config = dict(command=' '.join(sys.argv), calib_tag=args.calib_tag, scene=args.scene, sensor=sensor_name, optics=args.optics, crop=list(sc.crop),
                  duration_s=args.duration, dt_s=args.dt, seed=args.seed, jitter_seed=args.jitter_seed, particles=args.particles, I0_target=args.I0_target,
                  thresholds=args.thresholds, lit_limit_e_s=args.lit_limit, overrides=list(args.set or []),
                  threshold_model=args.threshold_model, group_bg=args.group_bg, energy_bg=args.energy_bg, bg_err=args.bg_err,
                  map_shift_px=args.map_shift, map_scale_err=args.map_scale_err, record_pad_s=args.record_pad,
                  particle_cfg=s.particle_cfg, code_version='2026-11-11',
                  profiles={k: v.to_dict() for k, v in P.items()})
    log(f"  {tag}: flashes {sm['n_detected']}/{sm['n_flashes']} detected, false triggers {sm['n_false']}, "
        f"particle triggers {sm['n_particle_triggers']} of {sm['n_particle_hits']} hits, events {s.stats['n_events']}, "
        f"wall {s.stats['wall_total_s']:.1f} s, peak RSS {s.stats['peak_rss_MB']:.0f} MB")
    if write:
        io_out.write_all(str(DATA / tag), s, config, write_h5=not args.no_h5)
        kt = np.arange(0.0, args.duration + 1e-9, 2.5)
        kf = np.stack([np.log10(np.maximum(sc.photo_rate(t) + s.dark_nominal, 1.0)) for t in kt]).astype(np.float32)
        np.savez_compressed(DATA / f'{tag}_keyframes.npz', t=kt, log10_rate=kf, drift_px_s=np.array(sc.meta.get('ground', {}).get('drift_px_s', [0.0, 0.0])))
    s.tag = tag; s.config = config
    return s


def video(sims, labels, title, path, window=0.033, speed=1.0, t0=0.0, t1=None):
    r = render.Renderer(sims, labels, title, window=window, speed=speed)
    t = time.time()
    n = r.write_mp4(str(path), t0=t0, t1=t1)
    return r, n, time.time() - t


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['run', 'compare', 'calibrate', 'profiles', 'export-v2e'])
    ap.add_argument('--scene', default='nearside', choices=list(scenes.PRESETS))
    ap.add_argument('--sensor', default='imx636')
    ap.add_argument('--sensors', default='imx636,imx646')
    ap.add_argument('--optics', default='optics_16mm_f1')
    ap.add_argument('--crop', default='320x180')
    ap.add_argument('--full-frame', action='store_true')
    ap.add_argument('--duration', type=float, default=20.0)
    ap.add_argument('--dt', type=float, default=5e-4)
    ap.add_argument('--chunk', type=float, default=0.5)
    ap.add_argument('--seed', type=int, default=20261104)
    ap.add_argument('--jitter-seed', type=int, default=11, help='seed of the attitude-jitter path (default 11)')
    ap.add_argument('--flashes', type=int, default=8)
    ap.add_argument('--flash-spec', default=None)
    ap.add_argument('--particles', default=None, choices=list(PARTICLES))
    ap.add_argument('--I0-target', type=float, default=None)
    ap.add_argument('--thresholds', default='compute', choices=['compute', 'stored'])
    ap.add_argument('--lit-limit', type=float, default=1e5)
    ap.add_argument('--threshold-model', default='fixed', choices=['fixed', 'retuned'],
                    help='fixed: the profile\'s S10 case as is; retuned: that case with the run\'s profile values')
    ap.add_argument('--group-bg', default='hetero', choices=['hetero', 'max', 'geomean'])
    ap.add_argument('--energy-bg', default='onset_chunk', choices=['onset_chunk', 'run_mean'])
    ap.add_argument('--bg-err', type=float, default=0.05)
    ap.add_argument('--map-shift', default='0,0', help='on-board background/mask map misregistration DX,DY [px]')
    ap.add_argument('--map-scale-err', type=float, default=0.0)
    ap.add_argument('--record-pad', type=float, default=4.5)
    ap.add_argument('--particle-diffusion-px', type=float, default=0.0)
    ap.add_argument('--particle-collection-tau', type=float, default=0.0)
    ap.add_argument('--particle-tail-fraction', type=float, default=1.0,
                    help='share of the deposit collected with --particle-collection-tau (rest prompt)')
    ap.add_argument('--set', action='append', default=[])
    ap.add_argument('--tag', default=None)
    ap.add_argument('--calib-tag', default=None, help='use energy_calibration_<calib-tag>.json instead of the sensor default')
    ap.add_argument('--no-h5', action='store_true')
    ap.add_argument('--video', action='store_true')
    ap.add_argument('--window', type=float, default=0.033)
    ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--n', type=int, default=2400)
    a = ap.parse_args(argv)
    if a.command == 'profiles':
        for p in profiles.list_profiles():
            print(p)
        return
    if a.command == 'run':
        s = run_one(a)
        if a.video:
            r, n, tv = video([s], [f'events: {a.sensor}'], s.scene.label, OUT / f'{s.tag}.mp4', a.window, a.speed)
            print(f'  video {n} frames in {tv:.0f} s -> {OUT / (s.tag + ".mp4")}')
        return s
    if a.command == 'compare':
        names = a.sensors.split(',')
        tag = a.tag or f"compare_{a.scene}_{'_vs_'.join(names)}"
        sims = []
        for n in names:
            a.tag = f'compare_{a.scene}_{n}'
            sims.append(run_one(a, n))
        r, n, tv = video(sims, [f'events: {x}' for x in names], sims[0].scene.label + ' - sensor comparison',
                         OUT / f'{tag}.mp4', a.window, a.speed)
        print(f'  video {n} frames in {tv:.0f} s -> {OUT / (tag + ".mp4")}')
        return sims
    if a.command == 'calibrate':
        from eventsim import calibrate
        calibrate.run(a.sensor, n=a.n, seed=a.seed, optics=a.optics, sets=a.set, out=DATA, tag=a.tag,
                      threshold_model=a.threshold_model)
    if a.command == 'export-v2e':
        p = io_out.export_v2e(DATA / f'{a.tag}_events.npz', DATA / f'{a.tag}_v2e.h5')
        print(f'  wrote {p}')


if __name__ == '__main__':
    main()
