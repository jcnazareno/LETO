"""Build the supporting-studies explorer: python studies_data.py, then python build_studies_explorer.py
-> outputs/studies_explorer.html (self-contained page; same styles as the impact explorer)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
tpl = (Path(__file__).parent / 'studies_template.html').read_text(encoding='utf-8')
style = (Path(__file__).parent / 'studies.css').read_text(encoding='utf-8')
data = json.dumps(json.loads((ROOT / 'data' / 'studies_explorer' / 'studies_data.json').read_text(encoding='utf-8')), separators=(',', ':')).replace('</', '<\\/')
out = ROOT / 'outputs' / 'studies_explorer.html'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(tpl.replace('__CSS__', style).replace('__DATA__', data), encoding='utf-8')
print(out, out.stat().st_size // 1024, 'kB')
