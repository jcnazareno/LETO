"""Independent analytical force/torque bounds and resource sensitivities."""
from pathlib import Path
import json,math,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/smd-disturbance-mpl')
import numpy as np
ROOT=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;D=ROOT/'data/disturbance_environment'
M=30.;Ar=.3;Cd=2.2;Cr=1.5;l=.02;c=299792458.;AU=149597870700.;P=1361/c
muE=3.986004418e14;muM=4.90280011526323e12;muS=1.32712440018e20;RE=6378137.;RM=1738000.
forces=[]
for label,mu,r,body in [('LEO400',muE,RE+400e3,RE),('LEO600',muE,RE+600e3,RE),('Moon100',muM,RM+100e3,RM),('Moon50',muM,RM+50e3,RM),('Distant50k',muM,50e6,RM)]:
 earth=label.startswith('LEO');q={'case':label,'r_m':r,'central_g_m_s2':mu/r**2,'SRP_sunlit_m_s2':P*Cr*Ar/M,'solar_tide_linear_max_m_s2':2*muS*r/AU**3,'body_J2_polar_max_m_s2':3*(1.08262668e-3 if earth else 202.7e-6)*mu*body**2/r**4,'third_body_linear_max_m_s2':2*(muM if earth else muE)*r/(384400e3)**3,'thermal_2W_beam_m_s2':2/(c*M)}
 if not earth:
  # Exact differential Earth tide at illustrative anti-Earth collinear distant location.
  q['Earth_tide_exact_antiEarth_m_s2']=muE*(1/(384400e3)**2-1/(384400e3+r)**2)
  # Very conservative ambient screening: surface upper count carried to orbit, all argon.
  rho=2e11*40*1.66053906660e-27;v=math.sqrt(mu/r)
  q['exosphere_screen_rho_kg_m3']=rho;q['exosphere_drag_screen_m_s2']=.5*rho*Cd*Ar/M*v*v
  q['exosphere_da_screen_km_30d']=2*r/v*q['exosphere_drag_screen_m_s2']*30*86400/1000
  q['exosphere_torque_screen_Nm']=q['exosphere_drag_screen_m_s2']*M*l
 forces.append(q)
unloads=[]
for bias in [1e-8,3e-8,1e-7]:
 h=.025;lever=.15;F=.001;Isp=80.;year=365*86400
 unloads.append({'bias_Nm':bias,'headroom_Nms':h,'cadence_d':h/bias/86400,'dump_time_s':h/(2*lever*F),'impulse_per_dump_Ns':h/lever,'prop_per_dump_g':h/lever/(Isp*9.80665)*1000,'annual_impulse_Ns':bias*year/lever,'annual_prop_g':bias*year/lever/(Isp*9.80665)*1000,'science_loss_fraction_20min_dump':1200*bias/h,'net_dv_single_unbalanced_dump_m_s':h/(lever*M),'net_dv_pair_1pct_mismatch_m_s':.01*h/(2*lever*M)})
speed=3000*2*math.pi/60;Us=.38e-6;Ud=27.59e-9
wheel={'source':'DE18 BCT15 historical unit, Table1','rpm':3000,'frequency_Hz':50,'static_kg_m':Us,'dynamic_kg_m2':Ud,'radial_force_N':Us*speed**2,'dynamic_torque_Nm':Ud*speed**2,'force_lever02m_torque_Nm':Us*speed**2*.02,'rigid_body_dynamic_angle_arcsec':Ud/.5*206264.806,'limitations':'No bearings/harmonics/structural transfer; not the candidate CW0500.'}
secondary={'solar_wind_density_m3':5e6,'solar_wind_speed_m_s':400e3,'solar_wind_pressure_Pa':5e6*1.672621924e-27*(400e3)**2,'solar_wind_absorbing_torque_Nm':5e6*1.672621924e-27*(400e3)**2*Ar*l,'charging_potential_V':1000,'capacitance_radius_m':.3,'net_charge_C':4*math.pi*8.8541878128e-12*.3*1000,'lorentz_400km_50uT_force_N':4*math.pi*8.8541878128e-12*.3*1000*7700*50e-6,'Lorentz_lunar_30nT_2kms_force_N':4*math.pi*8.8541878128e-12*.3*1000*2000*30e-9,'leak_mass_flow_kg_s':1e-10,'leak_speed_m_s':1000,'leak_force_N':1e-7,'leak_10cm_torque_Nm':1e-8,'impact_mass_kg':1e-9,'impact_speed_m_s':20000,'impact_arm_m':.2,'impact_H_Nms':1e-9*20000*.2,'impact_delta_rate_arcsec_s':1e-9*20000*.2/.5*206264.806,'status':'Conditional screening inputs, not measured environment percentiles, leak specification or impact frequency.'}
image={'pixel_pitch_um':4.86,'focal_m':.5,'pixel_arcsec':4.86e-6/.5*206264.806,'jitter_arcsec':.2,'jitter_pixels':.2/(4.86e-6/.5*206264.806),'localization_1arcsec_at50kkm_m':50e6/206264.806,'localization_1arcsec_at100km_m':100e3/206264.806,'low_lunar_nadir_tracking_deg_s':math.sqrt(muM/(RM+100e3)**3)*180/math.pi,'translation_fixed_ground_LOS_100km_deg_s':math.sqrt(muM/(RM+100e3))/100e3*180/math.pi,'residual_rate_point1deg_s_motion_5ms_pix':.1*3600*.005/(4.86e-6/.5*206264.806),'residual_rate_point1deg_s_motion_1ms_pix':.1*3600*.001/(4.86e-6/.5*206264.806),'notes':'Small-angle nadir mapping only. Pole/limb requires ray/terrain geometry. Example optics only; body tracking removes nominal motion, residual rate drives event traffic.'}
aero=[]
for x in json.loads((A/'model_results.json').read_text())['leo']:
 r=RE+x['h0_km']*1000;v=math.sqrt(muE/r);inc=math.radians(x['i_deg'])
 vr2=v*v+(7.292115e-5*r)**2*(1-.5*math.sin(inc)**2)-2*v*7.292115e-5*r*math.cos(inc)
 force=.5*x['rho_kg_m3']*Cd*Ar*vr2
 aero.append({'case':x['name'],'rho_kg_m3':x['rho_kg_m3'],'mean_vrel_squared_m2_s2':vr2,'drag_force_N':force,'aero_torque_Nm':force*l,'convention':'Orbit mean density times orbit mean vrel², fixed2cm perpendicular arm; density/velocity covariance and vector attitude history omitted.'})
out={'forces':forces,'unloading':unloads,'wheel_internal':wheel,'secondary':secondary,'image_motion':image,'aerodynamic':aero}
(A/'supplement_results.json').write_text(json.dumps(out,indent=2));(D/'analytical_bounds.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(10,4.6),layout='constrained');x=np.arange(len(forces))
for k,(field,label) in enumerate([('body_J2_polar_max_m_s2','Central-body J2 polar bound'),('third_body_linear_max_m_s2','Earth or Moon tidal bound (linear)'),('solar_tide_linear_max_m_s2','Solar tidal bound (linear)'),('SRP_sunlit_m_s2','Direct SRP, sunlit')]):
 ax.scatter(x+(k-1.5)*.15,[r[field] for r in forces],label=label)
ax.set(yscale='log',xticks=x,xticklabels=[r['case'] for r in forces],ylabel='Perturbing acceleration (m/s²)',title='Analytical screening bounds; Moon mascons need the harmonic runs')
ax.legend(fontsize=8,ncol=2);fig.savefig(ROOT/'figures/disturbance_environment/force_screening.png');plt.close(fig)
