"""Focused final artifact/data checks; read-only except the validation record."""
from pathlib import Path
import json,re,hashlib,math,csv
from urllib.parse import unquote
import numpy as np
from openpyxl import load_workbook
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;D=ROOT/'data/disturbance_environment';O=ROOT/'outputs/disturbance_environment_research_2026-10-29'
R=json.loads((A/'model_results.json').read_text());S=json.loads((A/'supplement_results.json').read_text());H=json.loads((A/'distant_results.json').read_text())
checks=[]
def close(name,a,b,rel=1e-8,absolute=1e-12):
 assert math.isclose(float(a),float(b),rel_tol=rel,abs_tol=absolute),(name,a,b)
 checks.append({'check':name,'result':'pass','value':float(a),'reference':float(b)})
paths=list(D.glob('Moon*.npz'))
for p in paths:
 z=np.load(p);t=z['time_s'];y=z['state_J2000_SI'];assert len(t)==len(y)>100 and np.all(np.diff(t)>0) and np.all(np.isfinite(y))
 assert y.shape[1]==6 and z['metrics'].shape==(len(t),8)
close('Moon50 radial screening crossing, metres',np.linalg.norm(np.load(D/'Moon50_N80.npz')['state_J2000_SI'][-1,:3]),1749000,absolute=.01)
checks.append({'check':'lunar state histories finite / monotonic / SI shape','result':'pass','cases':len(paths)})
assert len(paths)==9
with (D/'nrlmsis_density_profiles.csv').open() as f:
 rows=list(csv.DictReader(f));assert 'daily_ap'in rows[0] and 'F107a_sfu'in rows[0]
 assert all(float(x['rho_min_kg_m3'])>0 and float(x['rho_min_kg_m3'])<=float(x['rho_mean_kg_m3'])<=float(x['rho_max_kg_m3']) for x in rows)
checks.append({'check':'density profile units / field names / min-mean-max','result':'pass','rows':len(rows)})
wb=load_workbook(O/'disturbance_environment_research.xlsx',data_only=True)
form=load_workbook(O/'disturbance_environment_research.xlsx',data_only=False)
assert wb.sheetnames==['Results','Inputs','Orbit evolution','Forces','Torques','Momentum and pointing','Evidence','Validation']
error_cells=[]
for sh in wb:
 for row in sh:
  for cell in row:
   if cell.data_type=='e':error_cells.append(f'{sh.title}!{cell.coordinate}:{cell.value}')
assert not error_cells,error_cells
for row,t in enumerate(R['torques'],7):
 for c,k in [('D','GG_peak_Nm'),('E','GG_1deg_Nm'),('F','SRP_sunlit_bound_Nm'),('G','magnetic_30mAm2_bound_Nm'),('H','GG_periodic_H_amplitude_Nms'),('I','thermal_2W_10cm_bound_Nm')]:close(f'saved workbook {k} {t["case"]}',wb['Torques'][f'{c}{row}'].value,t[k])
for row,a in enumerate(S['aerodynamic'],28):close(f'aerodynamic torque {a["case"]}',wb['Torques'][f'D{row}'].value,a['aero_torque_Nm'])
for cell,key in [('B8','cadence_d'),('B10','dump_time_s'),('B11','impulse_per_dump_Ns'),('B12','prop_per_dump_g'),('B13','annual_impulse_Ns'),('B14','annual_prop_g'),('B15','science_loss_fraction_20min_dump'),('B16','net_dv_single_unbalanced_dump_m_s'),('B17','net_dv_pair_1pct_mismatch_m_s')]:close('saved momentum '+cell,wb['Momentum and pointing'][cell].value,S['unloading'][1][key])
close('PD steady error saved formula',wb['Momentum and pointing']['B23'].value,R['pointing']['PD_static_error_arcsec'],rel=1e-8)
close('slew torque saved formula',wb['Momentum and pointing']['B18'].value,R['pointing']['slew_10deg_60s_torque_Nm'])
close('saved arm input restored',wb['Inputs']['B11'].value,.02)
assert form['Torques']['F9'].data_type=='f' and form['Momentum and pointing']['B23'].data_type=='f'
wv=json.loads((A/'workbook_validation.json').read_text());assert wv['perturbationRelativeError']<1e-10 and 'matched 0 entries' in wv['formulaErrorScan']
checks.append({'check':'saved workbook formulas/caches and input perturbation','result':'pass','sheets':len(wb.sheetnames),'formula_errors':0})
reader=PdfReader(O/'lunar_disturbance_environment_report.pdf');assert len(reader.pages)==10
starts=['Lunar orbit','Matched cases','Low-lunar','Distant halo','Force comparison','Environmental torque','Momentum, unloading','Pointing, image','Decisions and verification','Source traceability']
for i,(pg,start)in enumerate(zip(reader.pages,starts)):
 text=pg.extract_text();assert start in text,(i+1,start);assert '■'not in text
 assert abs(float(pg.mediabox.width)-595.276)<.1 and abs(float(pg.mediabox.height)-841.89)<.1
checks.append({'check':'PDF reopened / ten A4 pages / expected sections / no replacement squares','result':'pass'})
mds=[O/'README.md',O/'disturbance_environment_research.md',A/'README.md',D/'README.md']
broken=[];nlinks=0
for p in mds:
 text=re.sub(r'```[\s\S]*?```','',p.read_text())
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if target.startswith(('https://','http://','#','mailto:')):continue
  nlinks+=1;relative=unquote(target.split('#')[0].strip('<>'))
  targetpath=(p.parent/relative).resolve()
  if targetpath==(A/'validation.json').resolve():continue # written after successful checks below
  if not targetpath.exists():broken.append([str(p.relative_to(ROOT)),target])
assert not broken,broken
checks.append({'check':'task Markdown local links','result':'pass','links':nlinks})
manifest=json.loads((ROOT/'tmp/disturbance_environment_research/sources/manifest.json').read_text());hashed=0
for item in manifest:
 if 'sha256'not in item:continue
 p=ROOT/'tmp/disturbance_environment_research/sources'/item['file'];assert p.exists()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];hashed+=1
checks.append({'check':'cached original model/source hashes','result':'pass','files':hashed})
assert R['checks']['J2_relative_acceleration_error']<1e-10
assert R['checks']['harmonic_potential_gradient_relative_error']<1e-6
assert R['checks']['two_body_30d_relative_energy_range']<1e-6
close('CRTBP stability index cross-check',(H['unstable_multiplier_fd']+1/H['unstable_multiplier_fd'])/2,H['catalogue_stability_index'],rel=3e-5)
for name in ['orbit_30day_comparison','orbit_extended','force_screening','torque_comparison','momentum_pointing','distant_halo_drift']:assert (ROOT/'figures/disturbance_environment'/f'{name}.png').stat().st_size>10000
checks.append({'check':'numerical limiting-case records / required plots','result':'pass'})
result={'date':'2026-10-29','status':'passed','checks':checks,'visual_review':'All eight workbook sheets, six plot topics and ten PDF pages rendered and reviewed; final changed views rechecked.','limits':['DE421 PA orientation approximates DE430 gravity frame','No local DEM impact or certified lifetime','50km screening-boundary time not converged at120deg','Fixed atmospheric fixtures are not weather forecasts','Ideal halo targeting is not annual stationkeeping prediction','No achieved structural/controller/sensor jitter performance','Workbook analytical formulas update; dynamical histories require script regeneration']}
(A/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':'passed','checks':len(checks),'workbook_sheets':len(wb.sheetnames),'PDF_pages':10,'local_links':nlinks,'source_hashes':hashed}))
