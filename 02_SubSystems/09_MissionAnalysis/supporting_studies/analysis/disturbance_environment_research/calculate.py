"""Concept-level matched orbit and attitude study. SI throughout unless labelled.

Actual lunar propagation: GRGM1200A truncated harmonics, SPICE DE440s Sun/Earth,
DE421 PA orientation approximation (explicit sensitivity), cannonball SRP and
cylindrical lunar shadow. This is not an operational lifetime certification.
"""
from pathlib import Path
import os, json, math, csv, time, sys
os.environ.setdefault('MPLCONFIGDIR','/tmp/smd-disturbance-mpl')
import numpy as np
from scipy.integrate import solve_ivp, cumulative_trapezoid
from scipy.interpolate import CubicSpline
from numba import njit
import spiceypy as sp
import pymsis
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'tmp/disturbance_environment_research/sources'
DATA=ROOT/'data/disturbance_environment'
FIG=ROOT/'figures/disturbance_environment'
ANA=Path(__file__).resolve().parent
DAY=86400.; MU=4.90280011526323e12; RM=1738e3
MUE=3.986004418e14; RE=6378.137e3; MUS=1.32712440018e20
AU=149597870700.; C_LIGHT=299792458.; P0=1361/C_LIGHT
MASS=30.; AREA=.30; CD=2.2; CR=1.5; ARM=.02
I=np.array([.625,.5,.325]) # 30 kg uniform .2 x .3 x .4 m box
EPOCH='2026-10-29T00:00:00'

@njit(cache=True)
def harmonic(x,C,S,N,aa,bb):
 """Non-central acceleration and potential; geodesy 4pi, no Condon phase."""
 r=np.sqrt(np.dot(x,x)); lon=np.arctan2(x[1],x[0]); s=x[2]/r
 co=np.sqrt(max(1e-24,1-s*s))
 P=np.zeros((N+1,N+1)); D=np.zeros_like(P); P[0,0]=1.
 if N:
  P[1,0]=np.sqrt(3.)*s; D[1,0]=np.sqrt(3.)*co
  P[1,1]=np.sqrt(3.)*co; D[1,1]=-np.sqrt(3.)*s
 for m in range(2,N+1):
  k=np.sqrt((2*m+1.)/(2*m)); P[m,m]=k*co*P[m-1,m-1]
  D[m,m]=k*(-s*P[m-1,m-1]+co*D[m-1,m-1])
 for m in range(0,N):
  if m>=1:
   k=np.sqrt(2*m+3.); P[m+1,m]=k*s*P[m,m]
   D[m+1,m]=k*(co*P[m,m]+s*D[m,m])
  for n in range(m+2,N+1):
   P[n,m]=aa[n,m]*s*P[n-1,m]-bb[n,m]*P[n-2,m]
   D[n,m]=aa[n,m]*(co*P[n-1,m]+s*D[n-1,m])-bb[n,m]*D[n-2,m]
 ar=0.; ap=0.; al=0.; U=0.; q=RM/r; qn=q
 cmarr=np.cos(np.arange(N+1)*lon); smarr=np.sin(np.arange(N+1)*lon)
 for n in range(1,N+1):
  sn=0.; spn=0.; sln=0.
  for m in range(n+1):
   cm=cmarr[m]; sm=smarr[m]; v=C[n,m]*cm+S[n,m]*sm
   sn+=P[n,m]*v; spn+=D[n,m]*v
   sln+=m*P[n,m]*(-C[n,m]*sm+S[n,m]*cm)
  ar-=(n+1)*qn*sn; ap+=qn*spn; al+=qn*sln/co; U+=qn*sn
  qn*=q
 cl=np.cos(lon); sl=np.sin(lon)
 a=MU/r**2*np.array([ar*co*cl-ap*s*cl-al*sl,ar*co*sl-ap*s*sl+al*cl,ar*s+ap*co])
 return a,MU/r*U

def coefficients():
 lines=(SRC/'grgm1200a_degree120_prefix.tab').read_text().splitlines()
 c=np.zeros((121,121)); s=c.copy(); a=c.copy(); b=c.copy()
 for line in lines[1:]:
  v=line.replace(',',' ').split()
  if len(v)<4: continue
  n,m=int(v[0]),int(v[1])
  if n<=120: c[n,m],s[n,m]=float(v[2]),float(v[3])
 for n in range(2,121):
  for m in range(n-1):
   a[n,m]=math.sqrt((2*n+1)*(2*n-1)/((n-m)*(n+m)))
   b[n,m]=math.sqrt((2*n+1)*(n+m-1)*(n-m-1)/((n-m)*(n+m)*(2*n-3)))
 return c,s,a,b

def elements(y,mu=MU,rad=RM):
 r=y[:3]; v=y[3:]; rn=np.linalg.norm(r); h=np.cross(r,v); hn=np.linalg.norm(h)
 ev=np.cross(v,h)/mu-r/rn; e=np.linalg.norm(ev)
 a=1/(2/rn-np.dot(v,v)/mu); node=np.cross([0.,0.,1.],h)
 nn=np.linalg.norm(node); inc=np.arccos(np.clip(h[2]/hn,-1,1))
 om=np.arctan2(node[1],node[0])
 arg=np.arctan2(np.dot(np.cross(node,ev),h)/(max(nn*e*hn,1e-30)),np.dot(node,ev)/max(nn*e,1e-30))
 return np.array([a/1e3,e,(a*(1-e)-rad)/1e3,(a*(1+e)-rad)/1e3,inc*180/np.pi,om*180/np.pi,arg*180/np.pi,(rn-rad)/1e3])

def initial(h=100.,inc=90.,raan=0.,hp=None,ha=None,arg=0.,nu=0.):
 if hp is None: hp=ha=h
 a=RM+(hp+ha)*500.; e=(ha-hp)*500./a
 w,O,i,f=np.radians([arg,raan,inc,nu]); p=a*(1-e*e)
 rp=p/(1+e*np.cos(f))*np.array([np.cos(f),np.sin(f),0.])
 vp=math.sqrt(MU/p)*np.array([-np.sin(f),e+np.cos(f),0.])
 rz=lambda t:np.array([[np.cos(t),-np.sin(t),0.],[np.sin(t),np.cos(t),0.],[0.,0.,1.]])
 rx=np.array([[1.,0.,0.],[0.,np.cos(i),-np.sin(i)],[0.,np.sin(i),np.cos(i)]])
 R=rz(O)@rx@rz(w)
 # Elements referenced to lunar PA axes frozen inertially at the epoch.
 Q=sp.pxform('MOON_PA_DE421','J2000',ET0)
 return np.r_[Q@R@rp,Q@R@vp]

def third(r,R,mu):
 d=R-r
 return mu*(d/np.linalg.norm(d)**3-R/np.linalg.norm(R)**3)

class Lunar:
 def __init__(self,N=80,thirdbody=True,srp=True,offset=0.,rtol=2e-9,maxstep=120.):
  self.N=N; self.tb=thirdbody; self.srp=srp; self.offset=np.radians(offset)
  self.rtol=rtol;self.maxstep=maxstep;self.lastday=-10;self.calls=0
 def parts(self,t,y):
  r=y[:3]; rn=np.linalg.norm(r); Q=sp.pxform('J2000','MOON_PA_DE421',ET0+t)
  if self.offset:
   a=self.offset; Q=np.array([[np.cos(a),-np.sin(a),0.],[np.sin(a),np.cos(a),0.],[0.,0.,1.]])@Q
  ag=Q.T@harmonic(Q@r,CO,SI,self.N,AA,BB)[0]
  ae=third(r,EARTH(t),MUE) if self.tb else np.zeros(3)
  ass=third(r,SUN(t),MUS) if self.tb else np.zeros(3)
  sr=SUN(t)-r; su=sr/np.linalg.norm(sr)
  shadow=(np.dot(r,su)<0 and np.linalg.norm(np.cross(r,su))<RM)
  ap=-P0*CR*AREA/MASS*(AU/np.linalg.norm(sr))**2*su if self.srp and not shadow else np.zeros(3)
  return ag,ae,ass,ap
 def rhs(self,t,y):
  self.calls+=1
  if t/DAY>=self.lastday+10:
   self.lastday=int(t/DAY);print('progress N',self.N,'day',self.lastday,'calls',self.calls,flush=True)
  r=y[:3]; ag,ae,ass,ap=self.parts(t,y)
  return np.r_[y[3:],-MU*r/np.linalg.norm(r)**3+ag+ae+ass+ap]
 def integrate(self,y0,days=30.):
  def stop(t,y):return np.linalg.norm(y[:3])-(RM+11e3)
  stop.terminal=True;stop.direction=-1
  return solve_ivp(self.rhs,(0,days*DAY),y0,method='DOP853',rtol=self.rtol,atol=1e-5,max_step=self.maxstep,dense_output=True,events=stop)

def save_lunar(name,model,y0,days=30.):
 start=time.time(); sol=model.integrate(y0,days)
 times=np.unique(np.r_[np.arange(0,sol.t[-1],600.),sol.t[-1]])
 states=sol.sol(times).T
 metrics=np.array([elements(y) for y in states])
 # Express inclination/node relative to the epoch PA inertial equator for comparison.
 Q=sp.pxform('J2000','MOON_PA_DE421',ET0)
 for k,y in enumerate(states):metrics[k,4:7]=elements(np.r_[Q@y[:3],Q@y[3:]])[4:7]
 budget=np.array([[np.linalg.norm(v) for v in model.parts(t,y)] for t,y in zip(times[::6],states[::6])])
 np.savez_compressed(DATA/f'{name}.npz',time_s=times,state_J2000_SI=states,metrics=metrics)
 headers=['day','a_km','e','hp_sphere_km','ha_sphere_km','inc_epochPA_deg','raan_epochPA_deg','argp_epochPA_deg','height_sphere_km']
 np.savetxt(DATA/f'{name}.csv',np.c_[times/DAY,metrics],delimiter=',',header=','.join(headers),comments='')
 def at(day):return metrics[np.argmin(abs(times-day*DAY))].tolist() if day<=times[-1]/DAY else None
 out={'name':name,'N':model.N,'duration_d':times[-1]/DAY,'boundary':'stop at 11 km above 1738 km sphere; assumed screening buffer, not DEM impact or validated safe envelope',
      'min_sample_height_km':float(metrics[:,7].min()),'min_osculating_hp_km':float(metrics[:,2].min()),'max_e':float(metrics[:,1].max()),'a_range_km':[float(metrics[:,0].min()),float(metrics[:,0].max())],
      'hp_range_km':[float(metrics[:,2].min()),float(metrics[:,2].max())],'ha_range_km':[float(metrics[:,3].min()),float(metrics[:,3].max())],
      'initial':metrics[0].tolist(),'day30':at(30),'end':metrics[-1].tolist(),'force_rms_m_s2':np.sqrt(np.mean(budget**2,axis=0)).tolist(),'force_max_m_s2':budget.max(axis=0).tolist(),'nfev':sol.nfev,'wall_s':time.time()-start}
 print(name,json.dumps(out),flush=True)
 return out

def density_table():
 """Orbit-average climatological profiles, not a forecast; fixed daily F107/ap."""
 rows=[]; profiles={}
 for h0,inc in [(400.,51.6),(600.,98.)]:
  T=2*np.pi*np.sqrt((RE+h0*1e3)**3/MUE); u=np.arange(0,2*np.pi,2*np.pi/96)
  lat=np.degrees(np.arcsin(np.sin(np.radians(inc))*np.sin(u)))
  lon=np.degrees(np.arctan2(np.cos(np.radians(inc))*np.sin(u),np.cos(u)))-np.degrees(7.292115e-5*u*T/(2*np.pi))
  dates=np.datetime64(EPOCH)+np.round(u*T/(2*np.pi)).astype('timedelta64[s]')
  for label,f,ap in [('quiet',70.,4.),('moderate',140.,15.),('active',220.,100.)]:
   hs=np.arange(120.,h0+101.,10.); dens=[]
   for alt in hs:
    out=pymsis.calculate(dates,lon,lat,np.full(96,alt),f107s=np.full(96,f),f107as=np.full(96,f),aps=np.full((96,7),ap),version=2.0)
    rho=out[:,0];dens.append(float(rho.mean()))
    rows.append([h0,inc,label,f,f,ap,alt,float(rho.min()),float(rho.mean()),float(rho.max())])
   profiles[(h0,label)]=(hs,np.array(dens))
 np.savetxt(DATA/'nrlmsis_density_profiles.csv',np.array(rows,dtype=object),delimiter=',',fmt='%s',header='case_alt_km,inc_deg,activity,F107_sfu,F107a_sfu,daily_ap,profile_alt_km,rho_min_kg_m3,rho_mean_kg_m3,rho_max_kg_m3',comments='')
 return profiles,rows

def leo(profiles):
 out=[]
 for h0,inc in [(400.,51.6),(600.,98.)]:
  for label in ['quiet','moderate','active']:
   hs,ds=profiles[h0,label]; logr=CubicSpline(hs,np.log(ds)); angle=np.radians(inc)
   def rates(t,z):
    a=z[0]; alt=(a-RE)/1e3;rho=np.exp(logr(alt));v=np.sqrt(MUE/a)
    # Average relative speed and v.vrel drag power over a circular inclined orbit.
    u=np.linspace(0,2*np.pi,64,endpoint=False)
    rel2=v*v+(7.292115e-5*a)**2*(1-np.sin(angle)**2*np.sin(u)**2)-2*v*7.292115e-5*a*np.cos(angle)
    da=-rho*CD*AREA/MASS*a*a/MUE*np.mean(np.sqrt(rel2)*(v*v-v*7.292115e-5*a*np.cos(angle)))
    n=np.sqrt(MUE/a**3);j=1.08262668e-3
    node=-1.5*j*n*(RE/a)**2*np.cos(angle)
    return [da,node]
   def stop(t,z):return z[0]-(RE+120e3)
   stop.terminal=True;stop.direction=-1
   sol=solve_ivp(rates,(0,365*DAY),[RE+h0*1e3,0.],events=stop,rtol=1e-9,atol=1e-5,dense_output=True,max_step=DAY/4)
   t=np.unique(np.r_[np.arange(0,sol.t[-1],DAY/4),sol.t[-1]])
   z=sol.sol(t);rho0=float(np.exp(logr(h0))); da0=rates(0,[RE+h0*1e3,0])[0]
   dvday=-da0*np.sqrt(MUE/(RE+h0*1e3))/(2*(RE+h0*1e3))*DAY
   entry={'name':f'LEO{int(h0)}_{label}','h0_km':h0,'i_deg':inc,'activity':label,'rho_kg_m3':rho0,'initial_da_km_day':da0*DAY/1e3,'drag_makeup_m_s_year_at_held_alt':dvday*365,'duration_d':sol.t[-1]/DAY,'end_h_km':(z[0,-1]-RE)/1e3,'h30_km':float((sol.sol(30*DAY)[0]-RE)/1e3) if sol.t[-1]>=30*DAY else None,'raan_deg_day':rates(0,[RE+h0*1e3,0])[1]*DAY*180/np.pi}
   np.savetxt(DATA/f"{entry['name']}.csv",np.c_[t/DAY,(z[0]-RE)/1e3,z[1]*180/np.pi],delimiter=',',header='day,mean_alt_km,mean_RAAN_change_deg',comments='')
   out.append(entry);print(entry,flush=True)
 return out

def attitude():
 results=[]
 for name,mu,r,B,rho in [('LEO400',MUE,RE+400e3,50e-6,0),('LEO600',MUE,RE+600e3,50e-6,0),('Moon100',MU,RM+100e3,30e-9,0),('Moon50',MU,RM+50e3,30e-9,0),('Distant50k',MU,50e6,30e-9,0)]:
  n=np.sqrt(mu/r**3); peak=1.5*mu/r**3*(I.max()-I.min());v=np.sqrt(mu/r)
  sun=P0*CR*AREA*ARM
  # Planetary irradiance envelope, 1/r^2 view scaling. Not simultaneous peaks.
  bodyr=RE if name.startswith('LEO') else RM
  albedo=.30 if name.startswith('LEO') else .12
  ir=237. if name.startswith('LEO') else 1361*.88
  alb=1361*albedo*(bodyr/r)**2/C_LIGHT*CR*AREA*ARM
  infrared=ir*(bodyr/r)**2/C_LIGHT*AREA*ARM
  results.append({'case':name,'r_m':r,'period_s':2*np.pi/n,'GG_peak_Nm':peak,'GG_1deg_Nm':peak*np.sin(np.radians(2)),'GG_periodic_H_amplitude_Nms':peak/(2*n),'GG_RMS_Nm_inertial':peak/np.sqrt(2),'SRP_sunlit_bound_Nm':sun,'albedo_envelope_Nm':alb,'IR_envelope_Nm':infrared,'magnetic_30mAm2_bound_Nm':.03*B,'thermal_2W_10cm_bound_Nm':2*.1/C_LIGHT})
 # Exact scalar y-axis example in a declared common inertial plane: r=(cos nt,0,sin nt), diagonal I.
 # Then GG torque about fixed inertial y is sinusoidal; solar+thermal bias about y is constant.
 for row in results:
  n=2*np.pi/row['period_s']; t=np.arange(0,7*DAY+60,60.)
  bias=3e-8 # specified envelope example, not inferred mean of SRP peaks
  T=row['GG_peak_Nm']*np.sin(2*n*t)+bias
  H=row['GG_peak_Nm']/(2*n)*(1-np.cos(2*n*t))+bias*t
  np.savetxt(DATA/f"momentum_{row['case']}.csv",np.c_[t/DAY,T,H],delimiter=',',header='day,inertial_y_torque_Nm,inertial_y_momentum_Nms',comments='')
 # Scalar rigid-body PD transfer; feedforward nominal tracking, no sensor/structure claims.
 Iaxis=.5; wn=2*np.pi*.02;zeta=.7; tau=3e-8
 t=np.linspace(0,300,1201)
 sol=solve_ivp(lambda t,z:[z[1],(tau-2*zeta*wn*Iaxis*z[1]-Iaxis*wn**2*z[0])/Iaxis],(0,300),[0.,0.],t_eval=t,rtol=1e-10,atol=1e-13)
 np.savetxt(DATA/'pointing_PD_example.csv',np.c_[t,sol.y[0]*206264.806,.5*tau/Iaxis*t*t*206264.806],delimiter=',',header='time_s,PD_error_arcsec,open_loop_arcsec',comments='')
 return results,{'I_kg_m2':Iaxis,'bandwidth_Hz':.02,'zeta':zeta,'bias_Nm':tau,'PD_static_error_arcsec':tau/(Iaxis*wn**2)*206264.806,'open_loop_100s_arcsec':.5*tau/Iaxis*100**2*206264.806,'slew_10deg_60s_torque_Nm':4*.625*np.radians(10)/60**2,'slew_peak_H_Nms':.625*2*np.radians(10)/60}

def checks():
 checks={}; zero=np.zeros_like(CO); c=zero.copy();c[2,0]=-1.08262668e-3/np.sqrt(5)
 x=np.array([2.1e6,1.3e6,.8e6]); r=np.linalg.norm(x);z=x[2]
 # Same mu/R as harmonic but arbitrary J2 to verify normalization and sign.
 aj=1.5*1.08262668e-3*MU*RM**2/r**5*np.array([x[0]*(5*z*z/r**2-1),x[1]*(5*z*z/r**2-1),z*(5*z*z/r**2-3)])
 ah=harmonic(x,c,zero,2,AA,BB)[0]
 checks['J2_relative_acceleration_error']=float(np.linalg.norm(aj-ah)/np.linalg.norm(aj))
 h=1.; grad=np.array([(harmonic(x+np.eye(3)[j]*h,CO,SI,80,AA,BB)[1]-harmonic(x-np.eye(3)[j]*h,CO,SI,80,AA,BB)[1])/(2*h) for j in range(3)])
 checks['harmonic_potential_gradient_relative_error']=float(np.linalg.norm(grad-harmonic(x,CO,SI,80,AA,BB)[0])/np.linalg.norm(grad))
 y=initial();sol=solve_ivp(lambda t,y:np.r_[y[3:],-MU*y[:3]/np.linalg.norm(y[:3])**3],(0,30*DAY),y,method='DOP853',rtol=2e-11,atol=1e-6,max_step=120)
 es=np.sum(sol.y[3:]**2,axis=0)/2-MU/np.linalg.norm(sol.y[:3],axis=0)
 checks['two_body_30d_relative_energy_range']=float(np.ptp(es)/abs(es[0]))
 checks['GG_Moon100_to_LEO400_ratio']=float((MU/(RM+100e3)**3)/(MUE/(RE+400e3)**3))
 assert checks['J2_relative_acceleration_error']<1e-10
 assert checks['harmonic_potential_gradient_relative_error']<1e-6
 assert checks['two_body_30d_relative_energy_range']<1e-6
 return checks

def plots(lunar,leos,torques):
 plt.rcParams.update({'font.size':10,'axes.spines.right':False,'axes.spines.top':False,'figure.dpi':130})
 fig,ax=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
 for row in leos:
  d=np.genfromtxt(DATA/f"{row['name']}.csv",delimiter=',',names=True)
  ax[0].plot(d['day'],d['mean_alt_km'],label=row['name'].replace('_',' '))
 ax[0].set(xlim=(0,30),xlabel='Elapsed days',ylabel='Mean altitude (km)',title='Earth: averaged drag + J2 node model');ax[0].legend(fontsize=8)
 for name in ['Moon100_N80','Moon50_N80','Moon100_RAAN90_N80','Moon30x200_N80']:
  if not (DATA/f'{name}.csv').exists():continue
  d=np.genfromtxt(DATA/f'{name}.csv',delimiter=',',names=True)
  ax[1].plot(d['day'],d['hp_sphere_km'],label=name.replace('_N80',''))
 ax[1].axhline(11,color='k',ls='--',lw=1,label='11 km screening buffer')
 ax[1].set(xlim=(0,30),xlabel='Elapsed days',ylabel='Osculating periapsis above 1738 km (km)',title='Moon: rotating harmonics + third bodies + SRP');ax[1].legend(fontsize=8)
 fig.savefig(FIG/'orbit_30day_comparison.png');fig.savefig(FIG/'orbit_30day_comparison.pdf');plt.close(fig)
 fig,ax=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
 for name in ['Moon100_N80','Moon50_N80','Moon100_RAAN90_N80','Moon30x200_N80']:
  if not (DATA/f'{name}.csv').exists():continue
  d=np.genfromtxt(DATA/f'{name}.csv',delimiter=',',names=True)
  ax[0].plot(d['day'],d['hp_sphere_km'],label=name.replace('_N80',''))
 ax[0].axhline(11,c='k',ls='--');ax[0].set(xlabel='Elapsed days',ylabel='Osculating periapsis (km)',title='Conditional low-lunar clearance');ax[0].legend(fontsize=8)
 for row in leos:
  d=np.genfromtxt(DATA/f"{row['name']}.csv",delimiter=',',names=True)
  ax[1].plot(d['day'],d['mean_alt_km'],label=row['name'].replace('_',' '))
 ax[1].set(xlabel='Elapsed days',ylabel='Mean altitude (km)',title='Fixed solar/ap states; validity stops at 120 km');ax[1].legend(fontsize=8)
 fig.savefig(FIG/'orbit_extended.png');plt.close(fig)
 names=[r['case'] for r in torques]; x=np.arange(len(names)); fig,ax=plt.subplots(figsize=(10,4.6),layout='constrained')
 for k,(key,label) in enumerate([('GG_peak_Nm','GG arbitrary-attitude peak'),('GG_1deg_Nm','GG at 1 deg misalignment'),('SRP_sunlit_bound_Nm','Direct SRP bound'),('magnetic_30mAm2_bound_Nm','Residual dipole bound'),('IR_envelope_Nm','Body IR hot envelope')]):
  ax.scatter(x+(k-2)*.13,[r[key] for r in torques],label=label,s=40)
 ax.set(yscale='log',xticks=x,xticklabels=names,ylabel='Torque (N m)',title='Matched 30 kg spacecraft; bounds are not simultaneous');ax.legend(fontsize=8,ncol=2)
 fig.savefig(FIG/'torque_comparison.png');fig.savefig(FIG/'torque_comparison.pdf');plt.close(fig)
 fig,ax=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
 for name in ['LEO400','Moon100','Distant50k']:
  d=np.genfromtxt(DATA/f'momentum_{name}.csv',delimiter=',',names=True)
  ax[0].plot(d['day'],d['inertial_y_momentum_Nms'],label=name)
 ax[0].axhline(.025,c='k',ls='--',label='25 mN m s illustrative headroom')
 ax[0].set(xlabel='Elapsed days',ylabel='Wheel momentum demand (N m s)',title='Fixed-axis periodic GG + 30 nN m bias');ax[0].legend(fontsize=8)
 d=np.genfromtxt(DATA/'pointing_PD_example.csv',delimiter=',',names=True)
 ax[1].plot(d['time_s'],d['PD_error_arcsec'],label='PD rigid-body model')
 ax[1].set(xlabel='Elapsed seconds',ylabel='Attitude error (arcsec)',title='0.02 Hz, damping 0.7; no sensor or structural noise');ax[1].legend(fontsize=8)
 fig.savefig(FIG/'momentum_pointing.png');plt.close(fig)

def main():
 global ET0,EARTH,SUN,CO,SI,AA,BB
 DATA.mkdir(exist_ok=True,parents=True);FIG.mkdir(exist_ok=True,parents=True)
 for name in ['naif0012.tls','de440s.bsp','moon_pa_de421_1900-2050.bpc','moon_080317.tf','pck00011.tpc']:sp.furnsh(str(SRC/name))
 ET0=sp.str2et(EPOCH); ts=np.arange(0,92*DAY+3600,3600.)
 EARTH=CubicSpline(ts,np.array([sp.spkpos('EARTH',ET0+t,'J2000','NONE','MOON')[0]*1000 for t in ts]))
 SUN=CubicSpline(ts,np.array([sp.spkpos('SUN',ET0+t,'J2000','NONE','MOON')[0]*1000 for t in ts]))
 CO,SI,AA,BB=coefficients()
 test=checks();print('checks',test,flush=True)
 prof,dens=density_table();leos=leo(prof);torques,pointing=attitude()
 cases=[('Moon100_N80',Lunar(80),initial(),30.),('Moon50_N80',Lunar(80),initial(50),60.),('Moon100_RAAN90_N80',Lunar(80),initial(100,raan=90),30.),('Moon30x200_N80',Lunar(80),initial(hp=30,ha=200,arg=270),30.),('Moon100_N40',Lunar(40),initial(),30.),('Moon100_N120',Lunar(120),initial(),30.),('Moon50_N120',Lunar(120),initial(50),30.),('Moon100_tight',Lunar(80,rtol=2e-10,maxstep=60),initial(),30.),('Moon100_frame001',Lunar(80,offset=.01),initial(),30.)]
 lunar=[]
 for name,model,y0,days in cases:
  p=DATA/f'{name}_summary.json'
  if p.exists() and '--fresh' not in sys.argv:
   entry=json.loads(p.read_text());entry['boundary']='stop at 11 km above 1738 km sphere; assumed screening buffer, not DEM impact or validated safe envelope';p.write_text(json.dumps(entry,indent=2));print('reuse',name,flush=True)
  else:entry=save_lunar(name,model,y0,days);p.write_text(json.dumps(entry,indent=2))
  lunar.append(entry)
 ref=lunar[0]
 for e in lunar[4:]:
  match=lunar[1] if e['name'].startswith('Moon50') else ref
  if e['day30'] is not None and match['day30'] is not None:test[e['name']+'_hp30_difference_km']=e['day30'][2]-match['day30'][2]
 out={'epoch_UTC':EPOCH,'spacecraft':{'mass_kg':MASS,'area_m2':AREA,'Cd':CD,'Cr':CR,'offset_m':ARM,'I_kg_m2':I.tolist(),'residual_dipole_Am2':.03},'checks':test,'leo':leos,'lunar':lunar,'torques':torques,'pointing':pointing}
 (ANA/'model_results.json').write_text(json.dumps(out,indent=2))
 (DATA/'case_results.json').write_text(json.dumps(out,indent=2))
 plots(lunar,leos,torques)
 print('COMPLETE',flush=True)
if __name__=='__main__':main()
