"""Shared constants and paths for the impact-energy-conversion study (30 October 2026).

All lengths in km unless a name says otherwise. Values that are assumptions are marked
in the README and in the report's assumption table.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'flash_crater_models'
FIG = ROOT / 'figures' / 'lunar_texture'
DATA.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

R_MOON = 1737.4            # km, same convention as the radiation/LUMIO/science studies
MU_MOON = 4902.800         # km^3/s^2
AREA_MOON = 4 * 3.141592653589793 * R_MOON**2   # km^2 (3.79e7)
SIDEREAL_DAY = 27.321661 * 86400.0             # s
YEAR_H = 8766.0            # h per Julian year

# Event-camera sensor (Sony IMX636 class, as in the earlier studies)
PIX = 4.86e-6              # m pixel pitch
NX, NY = 1280, 720


def _clean(o):
    # standard JSON: non-finite floats become null (review R36)
    import math
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


def save_json(name, obj):
    (DATA / name).write_text(json.dumps(_clean(obj), indent=2, allow_nan=False), encoding='utf-8')


def load_json(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))
