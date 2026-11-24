#!/usr/bin/env python3
"""Summarize executed GMAT cases and separate analytical torque screens."""
import argparse
import csv
import json
import math
from pathlib import Path
from run_validation import rows

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCHEMA = ['elapsed_days','phase','x_icrf_km','y_icrf_km','z_icrf_km',
          'vx_icrf_km_s','vy_icrf_km_s','vz_icrf_km_s','sma_km','eccentricity',
          'inclination_lunar_equator_J2000_deg','radius_altitude_km','osculating_periapsis_altitude_km',
          'osculating_apoapsis_altitude_km','mass_kg','fuel_kg','total_dv_m_s','maintenance_dv_m_s','lowering_dv_m_s']


def separation(out, first, second):
    a=rows(out/'runs'/first/'history.txt')[-1]
    b=rows(out/'runs'/second/'history.txt')[-1]
    assert abs(a[0]-b[0])*86400<0.001
    return {'position_m':math.sqrt(sum((x-y)**2 for x,y in zip(a[2:5],b[2:5])))*1000,
            'velocity_m_s':math.sqrt(sum((x-y)**2 for x,y in zip(a[5:8],b[5:8])))*1000,
            'comparison_epoch_days':a[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=ROOT/'tmp/gmat_lunar_setup/generated')
    out = parser.parse_args().folder.resolve()
    if (out/'scripts').is_dir():
        parser.error('Summarize a fresh validation directory to preserve the recorded results.')
    config = json.loads((out/'model_provenance.json').read_text())['config']
    validated=json.loads((out/'validation_all.json').read_text())
    assert all(r['status']=='passed' for r in validated.values())
    comparisons={}
    for altitude in ['high','low']:
        comparisons[altitude]={
            'gravity_40_vs_80':separation(out, f'convergence_{altitude}_40',f'convergence_{altitude}_80'),
            'gravity_80_vs_120':separation(out, f'convergence_{altitude}_80',f'convergence_{altitude}_120'),
            'srp_low_vs_nominal':separation(out, f'srp_{altitude}_low',f'convergence_{altitude}_80'),
            'srp_high_vs_nominal':separation(out, f'srp_{altitude}_high',f'convergence_{altitude}_80')}
    comparisons['numerics_low_nominal_vs_tight']=separation(out, 'convergence_low_80','numerics_low_tight')
    (out/'sensitivity_results.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    for name in validated:
        data=rows(out/'runs'/name/'history.txt')
        with (out/'runs'/name/'history.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(SCHEMA);w.writerows(data)
    (out/'history_schema.json').write_text(json.dumps(SCHEMA,indent=2)+'\n')
    # Analytical screens only: these torques and omitted forces are NOT applied in GMAT.
    speedlight=299792458.;sigma=5.670374419e-8;deltaI=max(config['inertia_principal_kg_m2'])-min(config['inertia_principal_kg_m2'])
    torque={}
    for tag,alt in [('high',3000),('low',300)]:
        mass=rows(out/'runs'/f'validation_{tag}_30d'/'history.txt')[0][14]
        radius=(config['moon_radius_km']+alt)*1000
        gg=1.5*config['moon_mu_km3_s2']*1e9*deltaI/radius**3
        srpforce=1361/speedlight*config['cr']*config['srp_area_m2']
        view=(config['moon_radius_km']/(config['moon_radius_km']+alt))**2
        # A uniform 400 K emitting disk and a rounded 0.12 reflectance screen;
        # both assume maximum radiation momentum response 2, not measured optics.
        irforce=2*sigma*400**4*view*config['srp_area_m2']/speedlight
        albedoforce=2*0.12*1361*view*config['srp_area_m2']/speedlight
        torque[tag]={'nominal_altitude_km':alt,'assumed_mass_kg':mass,
                    'gravity_gradient_arbitrary_attitude_envelope_Nm':gg,
                    'gravity_gradient_1deg_misalignment_Nm':gg*math.sin(math.radians(2)),
                    'sunlit_srp_acceleration_1au_m_s2':srpforce/mass,
                    'sunlit_srp_torque_envelope_Nm':srpforce*config['cp_cm_offset_m'],
                    'omitted_uniform_400K_disk_ir_acceleration_screen_m_s2':irforce/mass,
                    'omitted_reflected_radiation_acceleration_screen_m_s2':albedoforce/mass}
    (out/'analytical_screens.json').write_text(json.dumps({'assumptions':{
        'inertias_kg_m2':config['inertia_principal_kg_m2'],'lever_arm_m':config['cp_cm_offset_m'],
        'misalignment_deg':1,'solar_flux_W_m2':1361,'uniform_disk_temperature_K':400,
        'rounded_reflectance':0.12,'planetary_radiation_momentum_response':2,
        'note':'Separate screening scenarios; not simultaneous maxima, propagated forces, measured inertia, or a pointing prediction.'},
        'cases':torque},indent=2)+'\n')
    print(json.dumps(comparisons,indent=2))


if __name__=='__main__':main()
