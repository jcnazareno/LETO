"""Reproduce arithmetic bounds; this script does not run a radiation transport model."""
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data/radiation_environment'
TMP = ROOT / 'tmp/radiation_environment_research'
P = json.loads((HERE / 'model_inputs.json').read_text())
DATA.mkdir(parents=True, exist_ok=True)

def save_csv(name, rows):
    with (DATA / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def visible_fraction(radius, altitude):
    return (1 + math.sqrt(1 - (radius / (radius + altitude)) ** 2)) / 2

# Recover curve centre-lines at chosen x from the original embedded raster.
# Exact colours distinguish overlapping curves; y windows prevent picking legend text.
cfg = P['nasa_fig10']
im = Image.open(ROOT / cfg['image']).convert('RGB')
preview = im.copy()
draw = ImageDraw.Draw(preview)
b = cfg['plot_pixels']
dose_rows = []
for case, rgb in cfg['rgb'].items():
    for i, thickness in enumerate(P['shield_mm']):
        mils = thickness / 0.0254
        x = b['left'] + math.log10(mils) / 4 * (b['right'] - b['left'])
        expected = cfg['expected_y_at_shield'][case][i]
        picks = []
        for xx in range(round(x)-3, round(x)+4):
            for yy in range(expected-14, expected+15):
                c = im.getpixel((xx, yy))
                if max(abs(c[k]-rgb[k]) for k in range(3)) <= 7 or (case=='Lunar_surface' and c==(127,127,127)):
                    picks.append(yy)
        if not picks:
            raise ValueError(f'No trace found at {case} {thickness} mm')
        y = statistics.median(picks)
        dose = 10 ** (7 - (y-b['top']) / (b['bottom']-b['top']) * 10)
        dose_rows.append(dict(case=case, shielding_mm=thickness, shielding_g_cm2=thickness*0.1*P['al_density_g_cm3'],
                              x_pixel=x, y_pixel=y, dose_krad_Si_year=dose, reading_fraction=0.15,
                              solar_state='maximum', confidence='source 95%; reading allowance separate',
                              geometry='solid Al sphere; Si target', source_id='RAD01', source_location='Fig10; printed p11; PDF p15',
                              status='digitized published model result; not a new model run'))
        draw.ellipse((x-8,y-8,x+8,y+8), outline=(0,0,0), width=2)
preview.save(TMP/'fig10_digitization_audit.png')
save_csv('nasa_fig10_digitized.csv',dose_rows)

def dose(case,t):
    return next(r['dose_krad_Si_year'] for r in dose_rows if r['case']==case and r['shielding_mm']==t)

comparisons=[]
for t in P['shield_mm']:
    ip=dose('Interplanetary',t)
    for leo in ['LEO550_6','LEO800_98']:
        ratio=ip/dose(leo,t)
        comparisons.append(dict(shielding_mm=t,lunar_proxy='unocculted interplanetary',leo=leo,
                                lunar_krad_Si_year=ip,leo_krad_Si_year=dose(leo,t),ratio=ratio,
                                reading_ratio_low=ratio*0.85/1.15,reading_ratio_high=ratio*1.15/0.85,
                                source='RAD01; same solar max, 95%, Si, sphere, annual normalization'))
save_csv('matched_comparison.csv',comparisons)

geometry=[]
for case,r,h in [('Earth_400',P['earth_radius_km'],400),('Earth_600',P['earth_radius_km'],600),
                 ('Moon_surface',P['moon_radius_km'],0),('Moon_100',P['moon_radius_km'],100),
                 ('Moon_distant',P['moon_radius_km'],50000-P['moon_radius_km'])]:
    f=visible_fraction(r,h)
    geometry.append(dict(case=case,radius_km=r,altitude_km=h,centre_distance_km=r+h,
                         blocked_solid_angle_sr=4*math.pi*(1-f),visible_fraction=f,
                         meaning='isotropic scalar primary flux only; not planar dose or secondary transport'))
save_csv('body_occultation.csv',geometry)

mass=[]
for t in P['shield_mm']:
    d=t/1000
    side=P['local_box_inner_side_m']
    mass.append(dict(shield_mm=t,areal_g_cm2=t*0.27,areal_kg_m2=t*2.7,
                     bus_skin_kg=t*2.7*P['whole_bus_shield_area_m2'],
                     local_box_exact_kg=((side+2*d)**3-side**3)*2700,
                     local_box_thinwall_kg=6*side**2*d*2700))
save_csv('shield_mass.csv',mass)

area=P['sensor']['nx']*P['sensor']['ny']*(P['sensor']['pitch_um']*1e-4)**2
hits=[]
for j in P['noaa_flux_pfu']:
    r=math.pi*area*j
    hits.append(dict(type='SEP incident front face; isotropic assumption',input_flux=j,
                     flux_unit='pfu = p cm-2 s-1 sr-1 above 10 MeV',area_cm2=area,
                     incident_rate_s=r,incident_hour=r*3600,
                     assumed_candidate_rate_s=r*P['incident_to_candidate_fraction_example'],
                     required_incident_to_confirmed_fraction=P['confirmed_false_budget_per_hour_example']/(r*3600),
                     status='screening only; before shielding, response, lunar geometry, confirmation'))
save_csv('sep_incident_screening.csv',hits)
quiet=[]
for f in P['gcr_scalar_flux_cm2_s_assumed']:
    rate=f*area/2 # Both faces of ideal planar detector in isotropic 4pi scalar field.
    quiet.append(dict(assumed_scalar_flux_cm2_s=f,rate_both_faces_s=rate,
                      ideal_poisson_patch_time_loss=rate*P['mask_patch_pixels_assumed']/
                      (P['sensor']['nx']*P['sensor']['ny'])*P['mask_duration_s_assumed'],
                      status='hypothetical flux sensitivity, not calibrated GCR hit prediction'))
save_csv('quiet_incident_sensitivity.csv',quiet)

availability=[]
for days in P['outage_days_per_year_assumed']:
    for rate in P['reset_rate_per_day_assumed']:
        available=(1-days/P['year_days'])/(1+rate*P['reset_recovery_s_assumed']/86400)
        availability.append(dict(storm_days_year=days,reset_rate_day=rate,recovery_s=P['reset_recovery_s_assumed'],
                                 radiation_availability=available,sample_multiplier=available,
                                 poisson_flux_error_multiplier=1/math.sqrt(available),
                                 status='allocation sensitivity, not predicted flight availability'))
save_csv('availability_sensitivity.csv',availability)
save_csv('let_reference_readings.csv',[
    dict(case=k,integral_flux_above_let_cm2_s=v,let_threshold_MeV_cm2_mg=10,
         al_shield_mm=2.54,reading_factor=2,angular_convention='not specified; not used for device rate',
         source='RAD01 Fig8 printed p9; order-of-magnitude reading')
    for k,v in P['nasa_fig8']['integral_flux_cm2_s'].items()])
save_csv('measurement_comparators.csv',[
    dict(source='RAD02 abstract/para22',quantity='integrated Si dose',original_value=12.2,
         original_unit='rad(Si)',interval='first333days LRO2009-2010',derived_rad_year=12.2/333*365.25,
         limit='quiet era, nonuniform shielding; not a mission design dose'),
    dict(source='RAD03 abstract',quantity='Si dose rate',original_value=372,
         original_unit='microGy(Si)/day',interval='selected CRaTER near-Moon model interpretation',
         derived_rad_year=372e-6*365.25/0.01,limit='different response and geometry; no matched ratio')])
save_csv('proton_test_comparator.csv',[
    dict(source='RAD05 section3.4 Table3',device='DAVIS346SN0498',proton_energy_MeV=64,
         fluence_p_cm2=1.498e11,tid_krad_Si=20,
         limit='combinedTIDandDD exposure; no NIEL equivalent conversion or lunar lifetime inferred')])

tid= dose('Interplanetary',2.54)
total3=3*tid+P['transfer_allowance_krad']
results=dict(review_date=P['review_date'],execution='arithmetic and raster digitization only; no SPENVIS/IRENE/FASTRAD/Geant4 run',
             dose_rows=dose_rows,comparisons=comparisons,geometry=geometry,mass=mass,sep_screening=hits,
             quiet_sensitivity=quiet,availability=availability,let=P['nasa_fig8'],
             headline=dict(imx636_area_cm2=area,ip_2_54_krad_year=tid,three_year_plus_transfer_krad=total3,
                           dose_tolerance_with_example_margin_krad=total3*P['dose_margin_example'],
                           lro_quiet_annual_rad=12.2/333*365.25,
                           low_lunar_primary_only_krad_year=tid*next(g['visible_fraction'] for g in geometry if g['case']=='Moon_100')))
(HERE/'model_results.json').write_text(json.dumps(results,indent=2)+'\n')

# Independent identities and source cross-check, rather than mirroring every line.
assert abs(area-0.2176782336)<1e-12
assert abs(visible_fraction(1737.4,0)-0.5)<1e-12
assert abs(visible_fraction(1737.4,1e10)-1)<1e-12
assert abs(1e-6*86400*1e-6-0.0000000864)<1e-15 # microGy/s to Gy/day identity
assert abs(dose('Lunar_surface',2.54)-2.17)/2.17<0.15
assert all(r['reading_ratio_low']<r['ratio']<r['reading_ratio_high'] for r in comparisons)
assert all(0<r['radiation_availability']<=1 for r in availability)
assert math.isclose(1*0.1*2.7,0.27)
assert math.isclose(1*0.001*2700,2.7)
assert math.isclose(1-5/365.25,0.9863107460643394)
manifest=[]
for p in sorted((TMP/'sources').glob('*')):
    manifest.append(dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(TMP/'source_cache_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(HERE/'calculation_validation.json').write_text(json.dumps(dict(status='passed',checks=['sensor area','occultation limits','Si unit conversion','Fig10 lunar value within 15% of printed 2.17','ratio reading bounds','availability bounds','Al mass conversion'],headline=results['headline']),indent=2)+'\n')
print(json.dumps(results['headline'],indent=2))
