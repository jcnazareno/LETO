"""Independent saved-artifact, provenance, unit/formula and local-link checks."""
import csv,hashlib,json,math,re,sys,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote
import pdfplumber
from pypdf import PdfReader
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
OUT=ROOT/'outputs/lumio_comparison_research_2026-10-29';TMP=ROOT/'tmp/lumio_comparison_research';DATA=ROOT/'data/lumio_comparison'
D=json.loads((DATA/'research_data.json').read_text());R=json.loads((DATA/'calculation_results.json').read_text());I=json.loads((H/'model_inputs.json').read_text())
checks=[]
def check(name,ok,detail=None):
 checks.append({'check':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(f'{name}: {detail}')
ids={r[0] for r in D['sources']};check('19 unique primary source records',len(ids)==len(D['sources'])==19)
for key,idx in [('claims',8),('criteria',5),('timeline',3),('conflicts',3),('comparison',5),('decisions',3)]:
 missing=[(r[0],sid) for r in D[key] for source in r[idx].split(',') if (sid:=source.strip()) not in ids]
 check('resolved source IDs '+key,not missing,missing)
check('claim IDs unique',len({r[0] for r in D['claims']})==len(D['claims'])==43)
check('stable D01-D10',set(r[0] for r in D['comparison'])=={f'D{i:02}' for i in range(1,11)})
check('historical count criteria',[(r[0],r[2]) for r in D['criteria'][1:4]]==[('EC.A.02',240),('EC.A.03',2),('EC.A.04',100)])
for key in ['sources','claims','criteria','timeline','conflicts','comparison','decisions']:
 with (DATA/f'{key}.csv').open() as f:rows=list(csv.reader(f))[1:]
 check('CSV/JSON round trip '+key,rows==[[str(v) for v in row] for row in D[key]])
N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(OUT/'lumio_comparison_research.xlsx') as z:
 errors=[];formula_count=0;values={}
 for name in z.namelist():
  if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name):
   doc=ET.fromstring(z.read(name));vmap={}
   for c in doc.findall('.//s:c',N):
    v=c.find('s:v',N);f=c.find('s:f',N)
    if c.get('t')=='e':errors.append((name,c.get('r'),v.text if v is not None else None))
    if f is not None:
     formula_count+=1
     if v is None or v.text is None:errors.append((name,c.get('r'),'missing formula cache'))
    if v is not None:vmap[c.get('r')]=v.text
   values[name]=vmap
 check('saved formula caches and no Excel errors',not errors,{'formula_count':formula_count,'errors':errors})
 check('meaningful live calculations',formula_count>=100,formula_count)
 x=values['xl/worksheets/sheet6.xml'];c=values['xl/worksheets/sheet1.xml']
 for label,cell,expected in [
  ('science hours','C45',4383),('annual Gbit','B90',14.8),('mean sample','B93',100),('two-group sample','B94',450),
  ('mass line sum','B111',23.28),('printed mass total','B112',28.69),('science headroom','B113',9.82),('margin difference','B114',3.23),
  ('delta-v sum','B117',79.05),('near-disc diameter','C36',2*math.asin(1737.4/36000)*180/math.pi),
  ('nadir sampling','E38',(86000-1737.4)*math.tan(math.radians(6/1024))),('first5ms fraction','E53',1-math.exp(-5/3))]:
  check('independent saved value '+label,math.isclose(float(x[cell]),expected,rel_tol=1e-10,abs_tol=1e-10),{'value':float(x[cell]),'expected':expected})
 check('summary references final calculation',math.isclose(float(c['B25']),79.05,abs_tol=1e-10))
 workbook=ET.fromstring(z.read('xl/workbook.xml'));names=[s.get('name') for s in workbook.findall('s:sheets/s:sheet',N)]
 check('seven named sheets',len(names)==7,names)
pdf=OUT/'lumio_mission_comparison_report.pdf';reader=PdfReader(pdf)
check('ten A4 pages',len(reader.pages)==10 and all(abs(float(p.mediabox.width)-595.2756)<.1 and abs(float(p.mediabox.height)-841.8898)<.1 for p in reader.pages),len(reader.pages))
with pdfplumber.open(pdf) as document:
 texts=[p.extract_text() or '' for p in document.pages]
 overflow=[]
 for j,p in enumerate(document.pages):
  for word in p.extract_words():
   if word['x0']<40 or word['x1']>p.width-36 or word['top']<30 or word['bottom']>p.height-17:overflow.append((j+1,word['text']))
 check('PDF text within printable bounds',not overflow,overflow[:10])
check('PDF content/source labels',all(len(t)>1100 for t in texts) and 'L23' in texts[-1] and '240' in texts[1],list(map(len,texts)))
check('no missing glyph/control tokens in deliverables',not any(any(t in p for t in ['\ufffd','\u25a0','\ue200']) for p in texts))
check('all PDF renders present',len(list((TMP/'pdf_renders').glob('page-*.png')))==10)
check('four scientific figure pairs',len(list((ROOT/'figures/lumio_comparison').glob('*.png')))==4 and len(list((ROOT/'figures/lumio_comparison').glob('*.pdf')))==4)
for p in (ROOT/'figures/lumio_comparison').glob('*.png'):
 with Image.open(p) as im:check('figure size '+p.stem,im.width>=1000 and im.height>=450,list(im.size))
check('all worksheet preview topics',len(list((TMP/'workbook_previews').glob('*.png')))>=10)
manifest=json.loads((TMP/'source_access_manifest.json').read_text())
for sid in ['L17','L18']:
 rec=next(r for r in manifest if r['id']==sid)
 check('supplied source byte integrity '+sid,hashlib.sha256((ROOT/rec['file']).read_bytes()).hexdigest()==rec['sha256'])
check('web access limitations recorded',(TMP/'web_access_manifest.json').exists())
mds=[OUT/'README.md',OUT/'lumio_comparison_research.md',H/'README.md',DATA/'README.md',ROOT/'figures/lumio_comparison/README.md']
broken=[];count=0
for p in mds:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
  path=(p.parent/unquote(target.split('#',1)[0].strip('<>'))).resolve();count+=1
  if path==H/'validation.json':continue
  if not path.exists():broken.append((str(p.relative_to(ROOT)),target))
check('local study/shared-note links',not broken,{'count':count,'broken':broken})
check('calculation run checks',json.loads((H/'calculation_validation.json').read_text())['status']=='passed')
check('workbook input-change checks',json.loads((H/'workbook_validation.json').read_text())['status']=='passed')
result={'status':'passed','date':'2026-10-29','checks':checks,'formula_count':formula_count,'PDF_pages':len(reader.pages),'local_links':count,'python':sys.executable,
 'visual_review':'Ten-page contact sheet and detailed PDF pages; representative crops from all seven worksheets plus calculation views; four figures. No original graphical review claimed for HTTP403 Polimi sources.',
 'limitations':['Native Excel not executed','No new ephemeris propagation or LUMIO yield Monte Carlo','No calibrated selected-sensor model or hardware/irradiation/qualification test','Source conflicts and current public gaps retained']}
(H/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','formula_count','PDF_pages','local_links']},indent=2))
