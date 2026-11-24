"""Profile loading: sensor, optics and environment parameters with value/unit/uncertainty/source/status.

A profile file is JSON with a "params" map {key: {value, unit, uncertainty, source, status}} and an optional
"inherits" (file name in the same folder). `load(name)` returns a Profile whose `.v` dict holds the plain
values; `.meta` keeps the full records for documentation. Overrides use dotted keys ("ba.rate_hz=0.3").
"""
from __future__ import annotations
import json
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parents[1] / 'profiles'


class Profile:
    def __init__(self, name, description, params, s10_case=None, files=()):
        self.name = name
        self.description = description
        self.meta = params
        self.v = {k: r['value'] for k, r in params.items()}
        self.s10_case = s10_case
        self.files = list(files)

    def __getitem__(self, k):
        return self.v[k]

    def get(self, k, default=None):
        return self.v.get(k, default)

    def set(self, key, value, note='CLI override'):
        rec = dict(self.meta.get(key, {'unit': '?', 'uncertainty': '-', 'source': '-', 'status': 'assumed'}))
        rec['value'] = value
        rec['override'] = note
        self.meta[key] = rec
        self.v[key] = value

    def to_dict(self):
        return dict(name=self.name, description=self.description, s10_case=self.s10_case, files=self.files,
                    params=self.meta)


def _resolve(name):
    p = Path(name)
    if p.suffix != '.json':
        for cand in (PROFILE_DIR / f'{name}.json', PROFILE_DIR / f'sensor_{name}.json', PROFILE_DIR / f'optics_{name}.json'):
            if cand.exists():
                return cand
    if not p.is_absolute():
        p = PROFILE_DIR / p
    if not p.exists():
        raise FileNotFoundError(f'profile {name} not found in {PROFILE_DIR}')
    return p


def load(name) -> Profile:
    path = _resolve(name)
    d = json.loads(path.read_text(encoding='utf-8'))
    files = [path.name]
    params = {}
    s10 = None
    if 'inherits' in d:
        base = load(d['inherits'])
        params.update(base.meta)
        files = base.files + files
        s10 = base.s10_case
    params.update(d.get('params', {}))
    return Profile(d.get('name', path.stem), d.get('description', ''), params, d.get('s10_case', s10), files)


def parse_value(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return s


def apply_overrides(profiles: dict, sets):
    """sets: list of 'section.key=value' where section is sensor|optics|env, e.g. sensor.ba.rate_hz=0.3."""
    for item in sets or []:
        k, val = item.split('=', 1)
        sec, key = k.split('.', 1)
        if sec not in profiles:
            raise KeyError(f'unknown profile section {sec} (use sensor., optics. or env.)')
        profiles[sec].set(key, parse_value(val))


def list_profiles():
    return sorted(p.stem for p in PROFILE_DIR.glob('*.json'))
