"""Option A pairs in 2.5 years (deterministic, nominal factors) for the confirmation curves measured on real pairs.
Usage: python real_pairs_yield.py   -> data/crater_injection_test/real_pairs_yield.json"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'analysis', 'flash_crater_models'))
import joint_model as jm                                                         # noqa: E402
from common import load_json                                                     # noqa: E402

s = json.load(open(os.path.join(ROOT, 'data', 'crater_injection_test', 'real_pairs_summary.json')))['injection_fit']
CASES = {'placeholder': (3.5, 0.15, 0.85),
         'well_registered_cmax0.85': (s['dark|well_registered']['k_pixels'], s['dark|well_registered']['width_lnD'], 0.85),
         'well_registered_cmax_fit': (s['dark|well_registered']['k_pixels'], s['dark|well_registered']['width_lnD'], s['dark|well_registered']['c_max']),
         'all_registered_fit': (s['dark|all_registered']['k_pixels'], s['dark|all_registered']['width_lnD'], s['dark|all_registered']['c_max'])}
pop = jm.population(400_000, jm.ALPHA * jm.S_NOM)
er = load_json('event_response.json')
out = {'cases': {k: dict(k_pixels=v[0], width_lnD=v[1], c_max=v[2]) for k, v in CASES.items()}, 'pairs_2p5yr': {}}
for sname in ('nominal', 'm636', 'pessimistic'):
    pf = jm.p_flash(pop, jm.DetTable(er, sname), sname)
    out['pairs_2p5yr'][sname] = {}
    for lab, (k, w, c) in CASES.items():
        jm.KW = w; jm.p_crater.__defaults__ = (3.5, 0.9, jm.CMAX, w)
        out['pairs_2p5yr'][sname][lab] = jm.yield_terms(pop, pf, k=k, cmax=c)['pairs'] * jm.YEARS
    print(sname, {k: round(v) for k, v in out['pairs_2p5yr'][sname].items()})
json.dump(out, open(os.path.join(ROOT, 'data', 'crater_injection_test', 'real_pairs_yield.json'), 'w'), indent=1)
