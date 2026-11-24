"""JPL CRTBP halo example: nominal, initial-error drift and 7-day targeting.

Dimensionless barycentric rotating axes; no calendar ephemeris realization.
This illustrative controller is not the flight LUMIO stationkeeping policy.
"""
from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/smd-disturbance-mpl')
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import root
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'data/disturbance_environment';FIG=ROOT/'figures/disturbance_environment'
raw=json.loads((ROOT/'tmp/disturbance_environment_research/sources/jpl_halo_C309.json').read_text())
assert raw['signature']['version']=='1.0'
orbits=np.array(raw['data'],dtype=float)
# Filter out the short-period branch also returned by the archive query.
subset=orbits[orbits[:,7]>2];row=subset[np.argmin(abs(subset[:,6]-3.09))]
mu=float(raw['system']['mass_ratio']); L=float(raw['system']['lunit'])*1000;TU=float(raw['system']['tunit']);D=86400/TU
y0=row[:6]
def rhs(t,y):
 x,yc,z,vx,vy,vz=y; r1=((x+mu)**2+yc*yc+z*z)**.5;r2=((x-1+mu)**2+yc*yc+z*z)**.5
 return [vx,vy,vz,2*vy+x-(1-mu)*(x+mu)/r1**3-mu*(x-1+mu)/r2**3,-2*vx+yc-(1-mu)*yc/r1**3-mu*yc/r2**3,-(1-mu)*z/r1**3-mu*z/r2**3]
def prop(a,b,y,rtol=2e-12):return solve_ivp(rhs,(a,b),y,method='DOP853',rtol=rtol,atol=1e-13,max_step=.02,dense_output=True)
def jac(y):
 x,yc,z,vx,vy,vz=y;r1=((x+mu)**2+yc*yc+z*z)**.5;r2=((x-1+mu)**2+yc*yc+z*z)**.5
 return x*x+yc*yc+2*(1-mu)/r1+2*mu/r2-vx*vx-vy*vy-vz*vz
nom=prop(0,60*D,y0); grid=np.linspace(0,30*D,1441);ref=nom.sol(grid).T
error=np.array([1000/L,0,0,0,.01*TU/L,0]);drift=prop(0,30*D,y0+error).sol(grid).T
state=y0+error;t0=0.;states=[];times=[];burns=[]
for day in range(0,30,7):
 t0=day*D;horizon=t0+14*D;target=nom.sol(horizon)[:3]
 def residual(dv):return prop(t0,horizon,state+np.r_[np.zeros(3),dv]).y[:3,-1]-target
 fit=root(residual,np.zeros(3),tol=1e-9)
 if np.linalg.norm(residual(fit.x))>1e-8:raise ValueError('targeting residual')
 dv=fit.x;burns.append({'day':day,'dv_m_s':float(np.linalg.norm(dv)*L/TU),'vector_m_s':(dv*L/TU).tolist()})
 state=state+np.r_[np.zeros(3),dv];end=min(day+7,30)*D;seg=prop(t0,end,state)
 tg=grid[(grid>=t0)&(grid<end)];times.extend(tg);states.extend(seg.sol(tg).T)
 state=seg.y[:,-1]
times.append(30*D);states.append(state);states=np.array(states);times=np.array(times)
matched=nom.sol(times).T
errdrift=np.linalg.norm(drift[:,:3]-ref[:,:3],axis=1)*L/1e3
errcontrol=np.linalg.norm(states[:,:3]-matched[:,:3],axis=1)*L/1e3
distance=np.linalg.norm(ref[:,:3]-[1-mu,0,0],axis=1)*L/1e3
period=row[7]*TU/86400
single=prop(0,row[7],y0)
# Finite-difference monodromy eigenvalues to cross-check the catalogue stability.
eps=1e-7; mon=np.column_stack([(prop(0,row[7],y0+np.eye(6)[i]*eps).y[:,-1]-prop(0,row[7],y0-np.eye(6)[i]*eps).y[:,-1])/(2*eps) for i in range(6)])
lam=float(np.max(abs(np.linalg.eigvals(mon)))); efold=period/np.log(lam)
out={'source':'NASA/JPL Three-Body Periodic Orbits API v1.0, northern L2 halo, long-period branch nearest C=3.09','state_nd':y0.tolist(),'jacobi':float(row[6]),'period_d':period,'catalogue_stability_index':float(row[8]),'length_unit_m':L,'time_unit_s':TU,'mass_ratio':mu,'range_km':[float(distance.min()),float(distance.max())],'Az_km':float(np.max(abs(ref[:,2]))*L/1e3),'initial_error':'1 km x plus 0.01 m/s vy; all other offsets zero','uncontrolled_day30_deviation_km':float(errdrift[-1]),'uncontrolled_max30_deviation_km':float(errdrift.max()),'ideal_targeting_max30_deviation_km':float(errcontrol.max()),'ideal_targeting_dv30_m_s':float(sum(x['dv_m_s'] for x in burns)),'burns':burns,'period_closure_position_m':float(np.linalg.norm(single.y[:3,-1]-y0[:3])*L),'period_closure_velocity_m_s':float(np.linalg.norm(single.y[3:,-1]-y0[3:])*L/TU),'jacobi_range_30d':float(np.ptp([jac(y) for y in ref])),'unstable_multiplier_fd':lam,'linear_efold_d':efold,'control_limits':'7-day burns target nominal position 14 days downstream; exact navigation and impulsive execution; no Sun, SRP, eccentricity or ephemeris error; no hard envelope guaranteed'}
(ROOT/'analysis/disturbance_environment_research/distant_results.json').write_text(json.dumps(out,indent=2))
(DATA/'distant_case.json').write_text(json.dumps(out,indent=2))
np.savetxt(DATA/'halo_nominal_and_drift.csv',np.c_[grid/D,ref,drift,errdrift,distance],delimiter=',',header='day,'+','.join('nominal_'+s for s in ['x','y','z','vx','vy','vz'])+','+','.join('drift_'+s for s in ['x','y','z','vx','vy','vz'])+',deviation_km,range_Moon_km',comments='')
np.savetxt(DATA/'halo_targeted.csv',np.c_[times/D,states,errcontrol],delimiter=',',header='day,x,y,z,vx,vy,vz,deviation_km',comments='')
fig,ax=plt.subplots(1,2,figsize=(10.8,4.3),layout='constrained')
ax[0].plot(grid/D,distance);ax[0].set(xlabel='Elapsed days',ylabel='Moon-centre range (km)',title=f'JPL northern L2 halo, C={row[6]:.6f}')
ax[1].plot(grid/D,errdrift,label='Uncontrolled initial error');ax[1].plot(times/D,errcontrol,label='Ideal 7-day targeting')
ax[1].set(yscale='log',xlabel='Elapsed days',ylabel='Deviation from reference (km)',title='CRTBP; 1 km + 0.01 m/s initial offsets');ax[1].legend(fontsize=9)
fig.savefig(FIG/'distant_halo_drift.png');fig.savefig(FIG/'distant_halo_drift.pdf')
print(json.dumps(out,indent=2))
