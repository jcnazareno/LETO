"""Download public primary-source caches; no supplied files are modified."""
from pathlib import Path
import urllib.request, hashlib, json, concurrent.futures, sys
ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT/'tmp/disturbance_environment_research/sources'
BASE='https://naif.jpl.nasa.gov/pub/naif/generic_kernels/'
SOURCES={
 'jpl_halo_C309.json':'https://ssd-api.jpl.nasa.gov/periodic_orbits.api?sys=earth-moon&family=halo&libr=2&branch=N&jacobimin=3.089&jacobimax=3.091',
 'lumio_2024.pdf':'https://re.public.polimi.it/bitstream/11311/1266785/1/TOPPF01-24.pdf',
 'lumio_2022_status.pdf':'https://re.public.polimi.it/bitstream/11311/1215727/1/FRANV02-22.pdf',
 'shields_2017.pdf':'https://jossonline.com/storage/2021/08/Final-Shields-Characterization-of-CubeSat-Reaction-Wheel-Assemblies.pdf',
 'gomspace_cgp3.pdf':'https://gomspace.com/UserFiles/Subsystems/flyer/gomspace_nanoprop_3U_flyer.pdf',
 'naif0012.tls':BASE+'lsk/naif0012.tls',
 'de440s.bsp':BASE+'spk/planets/de440s.bsp',
 'moon_pa_de421_1900-2050.bpc':BASE+'pck/moon_pa_de421_1900-2050.bpc',
 'moon_080317.tf':BASE+'fk/satellites/moon_080317.tf',
 'pck00011.tpc':BASE+'pck/pck00011.tpc',
 'grgm1200a.lbl':'https://pds-geosciences.wustl.edu/grail/grail-l-lgrs-5-rdr-v1/grail_1001/shadr/gggrx_1200a_sha.lbl',
 'lro_2023.pdf':'https://ntrs.nasa.gov/api/citations/20230010952/downloads/Mesarch_LROLongTermOrbit_Preprint_20230727.pdf',
 'lro_2007.pdf':'https://ntrs.nasa.gov/api/citations/20070035736/downloads/20070035736.pdf',
 'lumio_2024_costa.pdf':'https://www.politesi.polimi.it/retrieve/3b6d39ed-b080-4fef-974a-597213733a85/2024_04_Costa_executive_summary.pdf',
 'lumio_2022.pdf':'https://repository.tudelft.nl/file/File_26c2fb63-077e-4dfc-bec7-1b891a8f2b1d',
 'cubewheel_2025.pdf':'https://www.cubespace.co.za/uploads/14b7921b-25a8-4380-a291-f6062826548f.pdf',
 'bct_wheels.pdf':'https://www.bluecanyontech.com/wp-content/uploads/Reaction-Wheels-Full-Line.pdf',
 'enpulsion_2026.pdf':'https://www.enpulsion.com/wp-content/uploads/DataSheet_Nano_20260317_V2.pdf',
 'nrlmsis_2021.pdf':'https://repository.library.noaa.gov/view/noaa/53074/noaa_53074_DS1.pdf',
}
def fetch(item):
 name,url=item; p=DEST/name
 try:
  if not p.exists():
   with urllib.request.urlopen(url,timeout=120) as r: p.write_bytes(r.read())
  return {'file':name,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'accessed':'2026-10-29'}
 except Exception as e: return {'file':name,'url':url,'error':str(e)}
def main():
 DEST.mkdir(parents=True,exist_ok=True)
 selected=SOURCES if '--models-only' not in sys.argv else {k:v for k,v in SOURCES.items() if not k.endswith('.pdf')}
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: records=list(pool.map(fetch,selected.items()))
 # Preserve a documented prefix, not a misleading copy of the full 1200-degree model.
 name='grgm1200a_degree120_prefix.tab'; p=DEST/name
 url='https://pds-geosciences.wustl.edu/grail/grail-l-lgrs-5-rdr-v1/grail_1001/shadr/gggrx_1200a_sha.tab'
 if not p.exists():
  lines=[]
  with urllib.request.urlopen(url,timeout=120) as r:
   for j,line in enumerate(r):
    if j>0:
     try: n=int(line.split(b',')[0])
     except ValueError: n=int(line.split()[0])
     if n>120: break
    lines.append(line)
  p.write_bytes(b''.join(lines))
 records.append({'file':name,'url':url,'subset':'header and degrees 1-120 only; original model degree/order 1200','bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'accessed':'2026-10-29'})
 previous=json.loads((DEST/'manifest.json').read_text()) if (DEST/'manifest.json').exists() else []
 merged={x['file']:x for x in previous};merged.update({x['file']:x for x in records})
 (DEST/'manifest.json').write_text(json.dumps(list(merged.values()),indent=2))
 for x in records: print(x['file'],x.get('bytes',x.get('error')))
if __name__=='__main__':main()
