"""Onset sweep: flat-cell lattice with a 2.5 s pre-roll so that long trigger windows contain pre-flash time."""
import sys, json, math, numpy as np, time
sys.path.insert(0,'.')
from eventsim import profiles, scenes, sim
from eventsim.radiometry import dark_e_s
seed=int(sys.argv[1]); out=sys.argv[2]
P=dict(sensor=profiles.load('imx636'),optics=profiles.load('optics_16mm_f1'),env=profiles.load('environment'))
S,O,E=P['sensor'],P['optics'],P['env']
calib=json.load(open('../../data/energy_calibration_imx636.json'))
CASES=[(1e4,0.1),(2e4,0.1),(2e4,0.3),(4e4,0.3),(4e4,1.0),(1e5,1.0),(2e5,1.0),(1e5,0.3)] if len(sys.argv)<4 else [(1e4,0.3),(1.5e4,0.3),(2e4,1.0),(3e4,1.0),(4e4,1.0),(6e4,1.0),(1.5e4,1.0),(1e4,0.1)]
ncx,ncy,cell=24,16,8; w,h=ncx*cell,ncy*cell; I0=13000.0; T_ON=2.5; DUR=7.0
rng=np.random.default_rng(seed)
photo=np.full((h,w),I0-dark_e_s(S['dark.current_fA'])); fl=[]
allow2=np.zeros((h,w),bool); allow3=np.zeros((h,w),bool)
for k in range(ncx*ncy):
    x0,y0=(k%ncx)*cell,(k//ncx)*cell; px,py=x0+2,y0+2
    allow2[y0+1:y0+cell-2,x0+1:x0+cell-2]=True; allow3[y0+1:y0+cell-3,x0+1:x0+cell-3]=True
    Ej,tau=CASES[rng.integers(len(CASES))]
    fl.append(dict(t_on=T_ON-rng.uniform(0,0.15),x=px+2+rng.uniform(-.5,.5),y=py+2+rng.uniform(-.5,.5),E_J=Ej,tau_s=tau,kind='exp',static=True,range_km=3750.0))
sc=scenes.FlatScene(w,h,photo,3750.0,E,label='onset')
s=sim.Simulation(sc,S,O,E,DUR,seed=seed,flashes=fl,particles=None,trigger_cfg=dict(mode='compute',allow2=allow2,allow3=allow3),log=lambda *a:None)
t=time.time(); s.run(); s.detect(calib=calib); sm=s.summary()
rows=[{k:r.get(k) for k in ('E_J','tau_s','detected','W','onset_err_s','ln_err_raw','ln_err_corr','lag_s','censored')} for r in sm['per_flash']]
json.dump(dict(seed=seed,n_false=sm['n_false'],rows=rows),open(out,'w'))
print('seed',seed,'det',sm['n_detected'],'/',sm['n_flashes'],'false',sm['n_false'],'wall',time.time()-t)
