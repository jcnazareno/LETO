#!/usr/bin/env python3
"""Run generated short GMAT cases and check physical and numerical invariants."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import json
import math
from pathlib import Path
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def rows(path):
    result = []
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        try:
            values = list(map(float, line.split()))
        except ValueError:
            continue
        if values:
            result.append(values)
    return result


def inspect(folder, scripts, name):
    meta = json.loads((scripts/(name+'.manifest.json')).read_text())
    c = meta['config']
    data = rows(folder/'runs'/name/'history.txt')
    burns = rows(folder/'runs'/name/'burns.txt')
    assert data and all(len(r)==19 and all(math.isfinite(v) for v in r) for r in data)
    assert all(b[0]>=a[0]-1e-8 for a,b in zip(data,data[1:])), 'Time is not monotonic'
    assert abs(data[0][0]) < 1e-8
    expected_days = meta['monitor_days']+meta['image_days']
    assert data[-1][0] >= expected_days-1e-7, 'Stopped before requested duration'
    assert data[-1][0] < expected_days+(1 if meta['image_days'] else 1e-6), 'Unexpected mission duration'
    assert min(r[11] for r in data) > c['minimum_radius_altitude_km'], 'Spherical clearance guard reached'
    assert min(r[15] for r in data)>0, 'No propellant reserve'
    assert abs(data[0][14]-meta['science_start_mass_kg'])<1e-8
    dv = sum(r[2] for r in burns)
    assert abs(dv-data[-1][16])<1e-7, 'Delta-v ledger does not equal impulses'
    expected_mass = data[0][14]*math.exp(-dv/(9.80665*c['isp_s']))
    assert abs(data[-1][14]-expected_mass)<1e-6, 'Rocket equation mass mismatch'
    assert all(abs(r[14]-r[15]-c['dry_mass_kg'])<1e-8 for r in data)
    if meta['image_days']:
        assert len(burns)==2
        assert 480 < dv < 550
        start_image = next(r for r in data if r[1]==3)
        assert abs(start_image[8]-(c['moon_radius_km']+c['image_altitude_km']))<0.02
        assert start_image[9]<0.001
    if meta['artificial_controller_exercise_threshold']:
        assert burns and data[-1][17]>0, 'Controller branch not exercised'
        for b in burns:
            after = next(r for r in data if abs(r[0]-b[0])<1e-8 and abs(r[16]-b[3])<1e-7)
            assert after[9]<1e-7, 'Ideal circularization failed'
    return {'samples':len(data), 'duration_days':data[-1][0], 'min_sampled_radius_altitude_km':min(r[11] for r in data),
            'min_sampled_osculating_periapsis_altitude_km':min(r[12] for r in data),
            'max_eccentricity':max(r[9] for r in data), 'final_state_icrf_km_km_s':data[-1][2:8],
            'total_delta_v_m_s':dv, 'maintenance_delta_v_m_s':data[-1][17],
            'final_mass_kg':data[-1][14], 'final_fuel_kg':data[-1][15], 'burn_count':len(burns)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, default=ROOT/'outputs')
    p.add_argument('--console', default='gmat-console', help='GMAT console launcher on PATH or absolute path')
    p.add_argument('--suite', choices=['core','sensitivity','all'], default='core')
    p.add_argument('--jobs',type=int,default=2)
    p.add_argument('--timeout',type=int,default=1800,help='seconds per short case')
    p.add_argument('--inspect-only',action='store_true',help='check saved successful execution logs and outputs without rerunning')
    p.add_argument('--case',action='append',help='run only the named case; repeat as needed')
    p.add_argument('--rerun',action='store_true',help='back up existing case outputs before replacing them')
    args = p.parse_args()
    folder = args.folder.resolve()
    scripts = folder / 'scripts' if (folder / 'scripts').is_dir() else folder
    if scripts != folder and not args.inspect_only:
        p.error('The recorded scripts contain original output paths. Generate a fresh folder to run them.')
    core = ['validation_transfer','validation_controller_exercise','validation_high_30d','validation_low_30d']
    sensitivity = sorted(x.stem for x in scripts.glob('*.script') if x.stem.startswith(('convergence_','srp_','numerics_')))
    names = core if args.suite=='core' else sensitivity if args.suite=='sensitivity' else core+sensitivity
    if args.case: names=args.case
    if not 1<=args.jobs<=4:
        p.error('--jobs must be 1 through 4')
    backup = ROOT/'tmp/gmat_lunar_setup'/('backup-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S'))
    for name in names:
        run = folder/'runs'/name
        if (run/'history.txt').exists() and not args.inspect_only:
            if not args.rerun:
                p.error(f'{name} has recorded results. Select another folder or use --rerun to back them up.')
            backup.mkdir(parents=True,exist_ok=True)
            shutil.copytree(run,backup/name)
    def run_case(name):
        start = time.monotonic()
        logfile = folder/'runs'/name/'console.log'
        cmd = [args.console, '--startup_file', str(scripts/(name+'.console.startup.txt')),
               '--run', str(scripts/(name+'.script'))]
        try:
            if not args.inspect_only:
                with logfile.open('w') as f:
                    proc = subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=args.timeout)
                assert proc.returncode==0, f'exit {proc.returncode}'
            log = logfile.read_text()
            assert 'GMAT Integration test (Console version) successful!' in log
            assert 'Mission run completed.' in log
            assert '**** ERROR' not in log and 'Mission run failed' not in log
            result = {'status':'passed','exit_code':0,**inspect(folder,scripts,name)}
        except Exception as e:
            result = {'status':'failed','error':repr(e)}
        timing_key = 'inspection_wall_seconds' if args.inspect_only else 'execution_wall_seconds'
        result[timing_key] = time.monotonic()-start
        print(name+': '+result['status']+f' ({result[timing_key]:.1f}s)',flush=True)
        return name,result
    results = {}
    with ThreadPoolExecutor(args.jobs) as pool:
        for future in as_completed([pool.submit(run_case,n) for n in names]):
            name,result = future.result(); results[name]=result
            if not args.inspect_only:
                (folder/('validation_'+args.suite+'.json')).write_text(json.dumps(results,indent=2)+'\n')
    if any(r['status']!='passed' for r in results.values()):
        raise SystemExit(1)


if __name__=='__main__':
    main()
