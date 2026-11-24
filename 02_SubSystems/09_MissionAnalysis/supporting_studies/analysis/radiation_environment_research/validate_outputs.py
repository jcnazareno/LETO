"""Independent saved-artifact checks. No workbook authoring or environment simulation."""
import csv
import json
import math
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote
import pdfplumber
from pypdf import PdfReader
from PIL import Image

H=Path(__file__).resolve().parent;ROOT=H.parents[1]
OUT=ROOT/'outputs/radiation_environment_research_2026-10-29'
TMP=ROOT/'tmp/radiation_environment_research'
R=json.loads((H/'model_results.json').read_text())
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
checks=[]
def check(name,ok,details=None):
    checks.append(dict(check=name,passed=bool(ok),details=details))
    if not ok:raise AssertionError(f'{name}: {details}')

book=OUT/'radiation_environment_research.xlsx'
with zipfile.ZipFile(book) as z:
    errors=[];formula_count=0;values={}
    for file in z.namelist():
        if re.match(r'xl/worksheets/sheet\d+\.xml$',file):
            doc=ET.fromstring(z.read(file));sheet={}
            for c in doc.findall('.//s:c',NS):
                v=c.find('s:v',NS);f=c.find('s:f',NS)
                if c.get('t')=='e':errors.append((file,c.get('r'),None if v is None else v.text))
                if f is not None:
                    formula_count+=1
                    if v is None or v.text is None:errors.append((file,c.get('r'),'missing formula cache'))
                if v is not None:sheet[c.get('r')]=v.text
            values[file]=sheet
    check('saved workbook error/cache scan',not errors,dict(formulas=formula_count,errors=errors))
    s2=values['xl/worksheets/sheet2.xml'];s3=values['xl/worksheets/sheet3.xml']
    for name,actual,expected in [
        ('TID tolerance',float(s2['H20']),R['headline']['dose_tolerance_with_example_margin_krad']),
        ('3mm exact cube mass',float(s3['E11']),((.106**3-.1**3)*2700)),
        ('5-day 0.1/day availability',float(s3['D41']),(1-5/365.25)/(1+.1*60/86400)),
        ('SEP S1 front-face rate',float(s3['C28']),math.pi*(1280*720*(4.86e-4)**2)*10),
        ('Moon100 visible sky',float(s3['E21']),(1+math.sqrt(1-(1737.4/1837.4)**2))/2),
        ('reading ratio 2.54mm',float(s2['C37']),R['headline']['ip_2_54_krad_year']/next(r['dose_krad_Si_year'] for r in R['dose_rows'] if r['case']=='LEO550_6' and r['shielding_mm']==2.54))]:
        check('saved cache '+name,math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-12),dict(actual=actual,expected=expected))
    root=ET.fromstring(z.read('xl/workbook.xml'));names=[s.get('name') for s in root.findall('s:sheets/s:sheet',NS)]
    check('seven named worksheets',len(names)==7,names)

pdf=OUT/'lunar_radiation_environment_report.pdf';reader=PdfReader(pdf)
check('seven A4 PDF pages',len(reader.pages)==7 and all(abs(float(p.mediabox.width)-595.2756)<.1 and abs(float(p.mediabox.height)-841.8898)<.1 for p in reader.pages),len(reader.pages))
with pdfplumber.open(pdf) as f:
    pages=[p.extract_text() or '' for p in f.pages]
check('PDF content and citations',all(len(p)>750 for p in pages) and '27.5' in pages[0] and 'RAD15' in pages[-1],list(map(len,pages)))
check('rendered PDF pages exist',len(list((TMP/'report_renders').glob('page-*.png')))==7)

figs=ROOT/'figures/radiation_environment'
pngs=sorted(figs.glob('*.png'));check('five scientific figure pairs',len(pngs)==5 and len(list(figs.glob('*.pdf')))==5)
for png in pngs:
    with Image.open(png) as im:check('figure resolution '+png.stem,im.width>=1000 and im.height>=500,list(im.size))

mds=[OUT/'README.md',OUT/'radiation_environment_research.md',H/'README.md',ROOT/'data/radiation_environment/README.md']
broken=[];count=0
for p in mds:
    text=p.read_text()
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
        target=unquote(target.split('#',1)[0].strip('<>'))
        count+=1
        destination=(p.parent/target).resolve()
        if destination==H/'validation_results.json':continue # Written by this validator after all checks pass.
        if not destination.exists():broken.append(dict(file=str(p.relative_to(ROOT)),target=target))
check('project-local links in study and touched notes',not broken,dict(count=count,broken=broken))

check('source IDs unique',len({e['id'] for e in json.loads((H/'research_data.json').read_text())['evidence']})==18)
cache_manifest=json.loads((TMP/'source_cache_manifest.json').read_text());check('seven public source PDFs cached',len(cache_manifest)==7,len(cache_manifest))
result=dict(status='passed',review_date='2026-10-29',checks=checks,
            visual_review='All seven report pages, every worksheet, engineering subviews and five scientific figures reviewed; plot caption spacing corrected.',
            native_excel='not executed; artifact-tool recalculation plus saved-cache checks only',
            radiation_model_execution='none; published figures and explicit arithmetic sensitivities only',
            scope='concept research complete; selected trajectory/device qualification and response remain TBR')
(H/'validation_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],checks=len(checks),formula_count=formula_count,pdf_pages=len(reader.pages),local_links=count),indent=2))
