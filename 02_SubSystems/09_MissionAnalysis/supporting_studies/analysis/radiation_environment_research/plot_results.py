"""Standalone scientific figures from reviewed calculations (system scientific Python)."""
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/smd-radiation-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
R=json.loads((HERE/'model_results.json').read_text())
OUT=ROOT/'figures/radiation_environment'
OUT.mkdir(exist_ok=True,parents=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
COLORS=['#3b7197','#ca8427','#6f459a','#6a747b']

def save(name):
    fig=plt.gcf()
    fig.subplots_adjust(bottom=.27)
    for footer in fig.texts:
        footer.set_y(.015)
    plt.savefig(OUT/(name+'.png'),bbox_inches='tight')
    plt.savefig(OUT/(name+'.pdf'),bbox_inches='tight')
    plt.close()

fig,ax=plt.subplots(figsize=(8,4.8))
for case,label,c in zip(['LEO550_6','LEO800_98','Interplanetary','Lunar_surface'],
                        ['LEO 550 km / 6°','LEO 800 km / 98°','Distant lunar proxy (interplanetary)','Lunar surface comparator'],COLORS):
    rows=[r for r in R['dose_rows'] if r['case']==case]
    x=np.array([r['shielding_mm'] for r in rows]);y=np.array([r['dose_krad_Si_year'] for r in rows])
    ax.plot(x,y,'o-',label=label,color=c)
    ax.fill_between(x,y*.85,y*1.15,color=c,alpha=.12)
ax.set(xlabel='Aluminium sphere shielding thickness (mm)',ylabel='Annual absorbed dose (krad(Si)/year)',yscale='log',
       title='Matched published dose cases')
ax.set_xticks([1,2,2.54,3,5]);ax.grid(axis='y',which='both',alpha=.2)
ax.legend(fontsize=9,loc='upper right')
fig.text(.04,-.02,'Source: NASA/TM-20250006822 (2025), Fig. 10, p. 11. Solar maximum, source 95% confidence.\nBands: ±15% digitization allowance only. No new radiation transport run; geometry is not an actual spacecraft.',fontsize=8)
save('matched_dose_depth')

fig,axs=plt.subplots(1,2,figsize=(9,4))
m=R['mass']
axs[0].plot([r['shield_mm'] for r in m],[r['bus_skin_kg'] for r in m],'o-',color=COLORS[0],label='1 m² skin area')
axs[0].set(xlabel='Aluminium thickness (mm)',ylabel='Added aluminium mass (kg)',title='Whole-bus skin example')
axs[1].plot([r['shield_mm'] for r in m],[r['local_box_exact_kg'] for r in m],'o-',color=COLORS[2])
axs[1].set(xlabel='Aluminium thickness (mm)',ylabel='Aluminium mass (kg)',title='10 cm internal cube, six walls')
for ax in axs: ax.grid(alpha=.2)
fig.tight_layout()
fig.text(.05,-.02,'This study: density 2.70 g/cm³; exact cube-shell volume. Total wall mass, before credit for existing structure.\nDifferent enclosed volumes: this is an accommodation trade, not equal protection of the whole spacecraft.',fontsize=8)
save('shielding_mass')

fig,ax=plt.subplots(figsize=(8,4))
for case,label,c in [('Interplanetary','Distant proxy',COLORS[2]),('LEO550_6','LEO 550 km / 6°',COLORS[0]),('LEO800_98','LEO 800 km / 98°',COLORS[1])]:
    d=next(r['dose_krad_Si_year'] for r in R['dose_rows'] if r['case']==case and r['shielding_mm']==2.54)
    t=np.array([1,2,3]);ax.plot(t,d*t,'o-',label=label,color=c)
    ax.fill_between(t,.85*d*t,1.15*d*t,color=c,alpha=.12)
ax.set(xlabel='Illustrative duration (years)',ylabel='Scaled operational dose (krad(Si))',title='Duration sensitivity at 2.54 mm Al')
ax.set_xticks([1,2,3]);ax.legend();ax.grid(alpha=.2)
fig.text(.04,-.02,'Annual source cases scaled arithmetically. Bands show reading allowance, not a three-year 95% prediction.\nNo transfer dose included. Solar-event statistics and solar-cycle changes require a duration-specific calculation.',fontsize=8)
save('duration_sensitivity')

fig,ax=plt.subplots(figsize=(8,4))
days=np.array([0,1,5,10,30]); ax.plot(days,(1-days/365.25)*100,'o-',color=COLORS[0],label='Storm exclusions only')
for rate,col in [(1,COLORS[1]),(10,COLORS[2])]:
    ax.plot(days,(1-days/365.25)/(1+rate*60/86400)*100,'o--',color=col,label=f'Plus {rate} reset(s)/day, 60 s recovery')
ax.set(xlabel='Assumed radiation exclusion (days/year)',ylabel='Radiation-only science availability (%)',title='Availability allocation sensitivity')
ax.grid(alpha=.2);ax.legend(fontsize=9)
fig.text(.04,-.02,'This study: assumed exclusions and reset rates, not a mission forecast. Other observation losses excluded.\nUse a regional exposure timeline: solar-event loss can coincide with meteoroid streams and cannot be repaired by revisit.',fontsize=8)
save('availability_sensitivity')

fig,ax=plt.subplots(figsize=(7.6,4))
names=['GCR solar max','GCR solar min','SEP peak week','SEP peak day','SEP peak 5 min']
vals=[1e-6,1e-5,.003,.01,.04]
ax.barh(names,vals,color=[COLORS[2],COLORS[0],COLORS[1],COLORS[1],COLORS[1]])
ax.errorbar(vals,range(5),xerr=[np.array(vals)*.5,np.array(vals)],fmt='none',ecolor='#25374a',capsize=3)
ax.set(xscale='log',xlabel='Integral flux above LET 10 MeV cm²/mg (cm⁻² s⁻¹)',title='Published LET environment scale after 2.54 mm Al')
ax.grid(axis='x',alpha=.2)
fig.text(.01,-.04,'Source: NASA/TM-20250006822, Fig. 8, p. 9. Order-of-magnitude readings; factor-two reading range.\nSEP: October 1989 reference; averaging intervals differ. Angular convention is not specified in source.\nNo device SEE rate inferred. Plot excludes low-LET particles and does not count all detector crossings.',fontsize=8)
save('let_environment_scale')
print('Created 5 PNG/PDF scientific figure pairs')
