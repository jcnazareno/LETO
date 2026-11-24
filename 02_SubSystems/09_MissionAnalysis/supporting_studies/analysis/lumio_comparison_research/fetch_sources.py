"""Cache public primary sources and extract PDF text with 1-based page markers."""
import concurrent.futures, hashlib, json, pathlib, urllib.request, sys
from html.parser import HTMLParser
from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / 'tmp/lumio_comparison_research/sources'
CACHE.mkdir(parents=True, exist_ok=True)
SOURCES = [
('L01','https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Shaping_the_Future/A_leap_forward_for_Lumio_Phase_C_officially_launched','html'),
('L02','https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Technology_CubeSats/LUMIO','html'),
('L03','https://www.asi.it/en/technologies-and-engineering/micro-and-nanosatellites/esa-gstp-fly-program/lumio/','html'),
('L04','https://www.aero.polimi.it/en/research-projects/esa-lumio-lunar-meteoroid-impacts-observer--phase-c','html'),
('L05','https://re.public.polimi.it/bitstream/11311/1266785/1/TOPPF01-24.pdf','pdf'),
('L06','https://re.public.polimi.it/retrieve/f609816c-3cf5-4468-93bc-12ee09e38135/PANCM01-24.pdf','pdf'),
('L07','https://www.asi.it/wp-content/uploads/2024/07/04.07_2_5_PoliMi.pdf','pdf'),
('L08','https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CubeSats_for_hunting_secrets_in_lunar_darkness','html'),
('L09','https://repository.tudelft.nl/file/File_21709ebf-3a9c-4b8e-ad4b-1c76bc0d7ab7','pdf'),
('L10','https://re.public.polimi.it/bitstream/11311/1055455/1/SPERS01-18.pdf','pdf'),
('L11','https://re.public.polimi.it/bitstream/11311/1066328/1/DEITD02-18.pdf','pdf'),
('L12','https://meetingorganizer.copernicus.org/EPSC-DPS2025/EPSC-DPS2025-1514.html','html'),
('L13','https://www.aero.polimi.it/en/magazine/lumio-consolidation-review','html'),
('L14','https://www.aero.polimi.it/en/magazine/daer-hosts-the-annual-esa-lumio-science-team-meeting','html'),
('L15','https://www.argotecgroup.com/missions/lumio','html'),
('L16','https://pure.tudelft.nl/ws/portalfiles/portal/101552527/IAC_21_C2.6.5.pdf','pdf'),
('L19','https://icubesat.org/wp-content/uploads/2017/05/2017-a-1-2-20170530-luce.pdf','pdf'),
('L20','https://www.frontiersin.org/journals/astronomy-and-space-sciences/articles/10.3389/fspas.2018.00029/full','html'),
('L21','https://re.public.polimi.it/retrieve/4942c6ab-bb8c-4e47-ac67-766418a0c2e5/PANIP01-24.pdf','pdf'),
]

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.ignore=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.ignore+=1
        if tag in ('p','h1','h2','h3','li','tr','div'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.ignore=max(0,self.ignore-1)
    def handle_data(self,data):
        if not self.ignore: self.parts.append(data)

def extract(path, identifier):
    r = PdfReader(path)
    (CACHE / f'{identifier}.txt').write_text('\n'.join(f'\n=== PDF PAGE {i+1} ===\n'+(p.extract_text() or '') for i,p in enumerate(r.pages)), encoding='utf-8')
    return len(r.pages)

def fetch(item):
    identifier, url, ext = item
    p = CACHE / f'{identifier}.{ext}'
    rec = {'id':identifier, 'url':url, 'access_date':'2026-10-29','file':str(p.relative_to(ROOT))}
    try:
        if not p.exists():
            if '--offline' in sys.argv: raise RuntimeError('Original file not cached; see web_access_manifest.json for browser verification')
            req = urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research source retrieval)'})
            with urllib.request.urlopen(req,timeout=45) as response:
                content = response.read()
                rec['resolved_url'] = response.url
            p.write_bytes(content)
        rec.update(status='cached',bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        if ext == 'pdf': rec['pages']=extract(p,identifier)
        else:
            parser=TextParser(); parser.feed(p.read_text(encoding='utf-8',errors='replace'))
            (CACHE / f'{identifier}.txt').write_text(''.join(parser.parts),encoding='utf-8')
    except Exception as exc:
        rec.update(status='access_failed',error=str(exc))
    return rec

if __name__ == '__main__':
    selected = SOURCES
    if '--only' in sys.argv:
        selected=[s for s in SOURCES if s[0] in sys.argv[sys.argv.index('--only')+1].split(',')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        records=list(executor.map(fetch,selected))
    manifest=CACHE.parent/'source_access_manifest.json'
    if manifest.exists() and selected != SOURCES:
        old=json.loads(manifest.read_text())
        records += [r for r in old if r['id'] not in {x['id'] for x in records} and r['id'] not in ('L17','L18')]
    for identifier, filename, doi in [
        ('L17','LUMIO - A CubeSat for observing and characterizing micro-meteroid impacts on the Lunar fas side.pdf','https://doi.org/10.1016/j.actaastro.2022.03.032'),
        ('L18','Meteoroids detection with the LUMIO lunar CubeSat.pdf','https://doi.org/10.1016/j.icarus.2022.115213')]:
        p=ROOT/'literature'/filename
        records.append({'id':identifier,'url':doi,'file':str(p.relative_to(ROOT)),'access_date':'2026-10-29','status':'supplied PDF inspected','pages':extract(p,identifier),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest.write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k in ('id','status','pages','error','bytes')} for r in records],indent=2))
