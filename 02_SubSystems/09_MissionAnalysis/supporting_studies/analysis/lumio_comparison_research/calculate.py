"""Analytic geometry, exposure, bin integration, data volume and source-budget audit.

No trajectory propagation, instrument calibration or new LUMIO yield Monte Carlo.
"""
import csv,json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
I=json.loads((H/'model_inputs.json').read_text());D=ROOT/'data/lumio_comparison';F=ROOT/'figures/lumio_comparison'
D.mkdir(parents=True,exist_ok=True);F.mkdir(parents=True,exist_ok=True)
R=I['moon_radius_km'];angular=math.radians(I['field_of_view_deg']/I['pixels_per_side'])
geometry=[dict(centre_km=r,nadir_range_km=r-R,disc_deg=math.degrees(2*math.asin(R/r)),nadir_sampling_km=(r-R)*math.tan(angular),visible_surface_fraction=(1-R/r)/2) for r in I['centre_ranges_km']]
area=4*math.pi*R*R;days=I['year_days'];live_h=days*24*I['science_duty_fraction']
exposure=[dict(additional_availability=a,science_hours=live_h*a,dark_area_km2=area*I['published_mean_dark_surface_fraction'],area_time_km2_h=area*I['published_mean_dark_surface_fraction']*live_h*a*(1-I['published_obstruction_fraction'])) for a in I['additional_availability_cases']]
temporal=[]
for tau in I['decay_times_ms']:
    for T in I['integration_times_ms']:
        q=-math.expm1(-T/tau)
        temporal.append(dict(decay_ms=tau,integration_ms=T,peak_best=tau/T*q,peak_worst=tau/T*q/(1+q),early_fraction=-math.expm1(-I['early_window_ms']/tau)))
stats=[dict(count=n,poisson_relative_error=1/math.sqrt(n)) for n in [2,100,240,4200,5500,37000]]
bits=I['tile_side_pixels']**2*I['frames_per_flash']*I['channels']*I['bits_per_pixel']
headline={
 'synodic_cycles':days/I['synodic_month_days'],'ideal_science_days':days*I['science_duty_fraction'],
 'ideal_science_hours':live_h,'mean_dark_area_km2':exposure[0]['dark_area_km2'],
 'effective_whole_surface_years':exposure[0]['area_time_km2_h']/(area*days*24),
 'geometry_centre_flux_ratio':(86000/36000)**2,'geometry_nadir_flux_ratio':((86000-R)/(36000-R))**2,
 'angular_sampling_arcsec':I['field_of_view_deg']/I['pixels_per_side']*3600,
 'tile_bits_per_flash':bits,'annual_science_Gbit':bits*I['model_annual_detections']/1e9,
 'raw_two_channel_Mbit_s_15fps':I['pixels_per_side']**2*I['channels']*I['bits_per_pixel']*15/1e6,
 'raw_two_channel_TB_day_15fps':I['pixels_per_side']**2*I['channels']*I['bits_per_pixel']*15/8*86400/1e12,
 'model_scenario_relative_sd':I['model_scenario_standard_deviation']/I['model_annual_detections'],
 'N_trial_mean':math.ceil((I['trial_population_cv']/I['trial_mean_relative_error'])**2),
 'N_trial_two_group_each':math.ceil(2*(I['trial_two_group_sigma']*I['trial_population_cv']/I['trial_two_group_effect'])**2),
 'mass_subsystem_sum_kg':sum(I['mass_subsystem_margined_kg']),
 'mass_subsystem_minus_printed_kg':sum(I['mass_subsystem_margined_kg'])-I['mass_printed_dry_subtotal_kg'],
 'mass_total_using_printed_kg':sum(I[k] for k in ['mass_printed_dry_subtotal_kg','mass_system_margin_kg','mass_harness_kg','mass_propellant_kg']),
 'power_science_simple_headroom_W':I['power_available_W']-I['power_science_margined_W'],
 'power_headroom_minus_printed_W':I['power_available_W']-I['power_science_margined_W']-I['power_science_printed_margin_W'],
 'maneuver_shortfall_W':I['power_maneuver_margined_W']-I['power_available_W'],
 'ideal_battery_minutes_at_shortfall':I['battery_nameplate_Wh']/(I['power_maneuver_margined_W']-I['power_available_W'])*60,
 'delta_v_table_sum_ms':sum(sum(row) for row in I['delta_v_budget_rows_ms'])}
result={'scope':'Analytic screening and source arithmetic only','geometry':geometry,'exposure':exposure,'temporal':temporal,'statistics':stats,'headline':headline}
(D/'calculation_results.json').write_text(json.dumps(result,indent=2)+'\n')
for key in ['geometry','exposure','temporal','statistics']:
 with (D/f'{key}.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=result[key][0].keys());w.writeheader();w.writerows(result[key])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160})
def save(fig,name):
 fig.savefig(F/f'{name}.png',dpi=180,bbox_inches='tight');fig.savefig(F/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
r=np.linspace(35000,86000,250)
fig,ax=plt.subplots(1,2,figsize=(10.2,3.6),layout='constrained')
ax[0].plot(r/1000,np.degrees(2*np.arcsin(R/r)),color='#315980',lw=2,label='Lunar apparent diameter')
ax[0].axhline(6,color='#A55E29',ls='--',label='6 deg camera field')
ax[0].set(xlabel='Moon-centre distance (1000 km)',ylabel='Angular diameter (deg)',ylim=(0,7));ax[0].legend(fontsize=8)
ax[1].plot(r/1000,(r-R)*np.tan(angular),color='#315980',lw=2)
ax[1].set(xlabel='Moon-centre distance (1000 km)',ylabel='Nadir sampling (km/pixel)')
fig.suptitle('LUMIO geometry: full disc visibility does not establish localization or global coverage',fontsize=11)
save(fig,'geometry')
tau=np.logspace(-.1,2.5,250)
fig,ax=plt.subplots(figsize=(8.7,4.0),layout='constrained')
for T,c in [(1,'#35673E'),(5,'#58A474'),(23,'#6A688E'),(66,'#315980'),(78,'#AA642C')]:
 q=-np.expm1(-T/tau);best=tau/T*q;worst=best/(1+q)
 ax.plot(tau,best,label=f'{T} ms integration',color=c);ax.fill_between(tau,worst,best,color=c,alpha=.10)
ax.set(xscale='log',xlabel='Illustrative exponential decay time (ms)',ylabel='Largest bin mean / true peak',ylim=(0,1.04))
ax.legend(ncol=2,fontsize=8);ax.set_title('Ideal integration only: shaded ranges show unknown onset phase',fontsize=11)
save(fig,'temporal_integration')
fig,ax=plt.subplots(figsize=(9.5,2.8),layout='constrained')
for j,label,color in [(0,'Science window','#315980'),(1,'Navigation / engineering','#B6C4D1')]:
 for start in np.arange(0,2*I['synodic_month_days'],I['synodic_month_days']):
  ax.broken_barh([(start+j*I['synodic_month_days']/2,I['synodic_month_days']/2)],(0,1),facecolors=color,label=label if start==0 else None)
ax.set(xlim=(0,2*I['synodic_month_days']),ylim=(-.1,1.25),xlabel='Elapsed days in idealized two-lunation sequence',yticks=[])
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.2),ncol=2,frameon=False)
ax.set_title('Half-cycle operations: 182.6 science-window days per 365.25-day year',pad=38,fontsize=11)
save(fig,'operations')
fig,ax=plt.subplots(figsize=(8.7,3.3),layout='constrained')
ax.barh(['Phase 0: luminous efficiency','Phase 0: blackbody','Phase A: MeGun + radiometry'],[4200,5500,37000],color=['#8FA4B9','#6383A3','#315980'])
for y,n in enumerate([4200,5500,37000]):ax.text(n+450,y,f'{n:,}',va='center',fontsize=9)
ax.set(xlabel='Published predicted detections per nominal operational year',xlim=(0,42500))
ax.set_title('Model changes exceed the Phase A Monte Carlo scenario spread',fontsize=11)
save(fig,'published_yield')
# Independent quadrature/phase and dimensional sanity checks.
checks=[]
for row in temporal:
 T=row['integration_ms'];t=row['decay_ms'];a=t*math.log(2-math.exp(-T/t))
 integral0=t*(1-math.exp(-a/t))/T
 integral1=t*math.exp(-a/t)*(1-math.exp(-T/t))/T
 assert abs(integral0-integral1)<1e-12
 assert abs(integral0-row['peak_worst'])<1e-12
 assert 0 < row['peak_worst'] <= row['peak_best'] <= 1
assert abs(headline['annual_science_Gbit']-14.8)<1e-12
assert abs(headline['mass_total_using_printed_kg']-28.69)<1e-10
assert abs(headline['delta_v_table_sum_ms']-79.05)<1e-10
assert abs(headline['effective_whole_surface_years']-.15)<1e-12
assert geometry[0]['disc_deg']<6
(H/'calculation_validation.json').write_text(json.dumps({'status':'passed','checks':['20 analytic bin-phase extrema independently evaluated','tile product14.8Gbit','printed mass total28.69kg','delta-v79.05m/s','area-time0.15whole-surface-year','geometry dimensions and6deg closest-disc check'],'scope':result['scope']},indent=2)+'\n')
print(json.dumps(headline,indent=2))
