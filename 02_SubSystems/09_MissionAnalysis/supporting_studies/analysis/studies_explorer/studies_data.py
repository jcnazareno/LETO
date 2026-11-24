"""Data for the supporting-studies explorer (outputs/studies_explorer.html).

Collects the stored results of the four supporting studies into one JSON that the page embeds. Nothing is rerun;
the page recombines these results with the studies' own closed-form relations (stated in the page).
  * radiation environment (29 Oct 2026): digitised dose-depth curves, body occultation, shield mass, inputs;
  * orbit and attitude disturbances (29 Oct 2026): LEO and low-lunar-orbit histories (downsampled), NRLMSIS
    density profiles, spacecraft constants, halo drift, unloading constants;
  * LUMIO comparison (29 Oct 2026): model inputs, timeline and driver comparison;
  * D01-D04 research (28 Oct 2026): photon-budget and localisation inputs and results, NELIOTA energies;
Usage: python studies_data.py   -> data/studies_explorer/studies_data.json
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data'; A = ROOT / 'analysis'


def rcsv(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        v = float(x)
        return v
    except (TypeError, ValueError):
        return x


def rows(p, keys=None):
    return [{k: num(v) for k, v in r.items() if keys is None or k in keys} for r in rcsv(p)]


def thin(rs, n=220):
    step = max(1, len(rs) // n)
    out = rs[::step]
    if out[-1] is not rs[-1]:
        out.append(rs[-1])
    return out


def main():
    out = {'model': __doc__}
    # --- radiation
    rad_in = json.loads((A / 'radiation_environment_research' / 'model_inputs.json').read_text())
    rad_res = json.loads((A / 'radiation_environment_research' / 'model_results.json').read_text())
    out['radiation'] = dict(
        dose=rows(D / 'radiation_environment' / 'nasa_fig10_digitized.csv', ('case', 'shielding_mm', 'dose_krad_Si_year')),
        occultation=rows(D / 'radiation_environment' / 'body_occultation.csv', ('case', 'radius_km', 'altitude_km', 'visible_fraction')),
        measured=rows(D / 'radiation_environment' / 'measurement_comparators.csv', ('source', 'derived_rad_year', 'limit')),
        proton_test=rows(D / 'radiation_environment' / 'proton_test_comparator.csv'),
        inputs={k: rad_in[k] for k in ('year_days', 'al_density_g_cm3', 'moon_radius_km', 'earth_radius_km', 'dose_margin_example',
                                       'transfer_allowance_krad', 'local_box_inner_side_m', 'reset_recovery_s_assumed', 'digitization_fraction')},
        headline=rad_res['headline'], let=rad_res['let'])
    # --- disturbances
    dist = D / 'disturbance_environment'
    cr = json.loads((dist / 'case_results.json').read_text())
    leo = {}
    for r in cr['leo']:
        ts = rows(dist / f"{r['name']}.csv")
        leo[r['name']] = dict(summary={k: r[k] for k in ('h0_km', 'i_deg', 'activity', 'rho_kg_m3', 'drag_makeup_m_s_year_at_held_alt', 'duration_d', 'end_h_km')},
                              t=[round(x['day'], 2) for x in thin(ts)], h=[round(x['mean_alt_km'], 2) for x in thin(ts)])
    lunar = {}
    for r in cr['lunar']:
        p = dist / f"{r['name']}.csv"
        if not p.exists():
            continue
        ts = rows(p)
        lunar[r['name']] = dict(summary={k: r.get(k) for k in ('N', 'duration_d', 'min_osculating_hp_km', 'max_e', 'boundary')},
                                t=[round(x['day'], 3) for x in thin(ts)], hp=[round(x['hp_sphere_km'], 2) for x in thin(ts)],
                                h=[round(x['height_sphere_km'], 2) for x in thin(ts)])
    prof = rows(dist / 'nrlmsis_density_profiles.csv', ('case_alt_km', 'inc_deg', 'activity', 'F107_sfu', 'profile_alt_km', 'rho_mean_kg_m3'))
    halo_n = rows(dist / 'halo_nominal_and_drift.csv', ('day', 'deviation_km', 'range_Moon_km'))
    halo_t = rows(dist / 'halo_targeted.csv', ('day', 'deviation_km'))
    out['disturbance'] = dict(spacecraft=cr['spacecraft'], leo=leo, lunar=lunar, density=prof,
                              halo=dict(t=[x['day'] for x in thin(halo_n, 150)], free=[x['deviation_km'] for x in thin(halo_n, 150)],
                                        targeted=[x['deviation_km'] for x in thin(halo_t, 150)],
                                        summary=json.loads((dist / 'distant_case.json').read_text())),
                              unloading=dict(lever_m=0.15, thrust_N=0.001, Isp_s=80.0, headroom_Nms=0.025, mass_kg=cr['spacecraft']['mass_kg']))
    for k in ('period_closure_position_m', 'period_closure_velocity_m_s', 'state_nd', 'burns'):
        out['disturbance']['halo']['summary'].pop(k, None)
    # --- LUMIO
    lum_in = json.loads((A / 'lumio_comparison_research' / 'model_inputs.json').read_text())
    lum_res = json.loads((D / 'lumio_comparison' / 'calculation_results.json').read_text())
    out['lumio'] = dict(inputs={k: v for k, v in lum_in.items() if k != 'input_provenance'}, results=lum_res,
                        timeline=rows(D / 'lumio_comparison' / 'timeline.csv', ('date', 'phase', 'configuration', 'status')),
                        comparison=rows(D / 'lumio_comparison' / 'comparison.csv', ('driver', 'lumio_comparator', 'smd_status', 'consequence')))
    # --- D01-D04
    dm = json.loads((A / 'd01_d04_research' / 'model_results.json').read_text())
    ed = json.loads((A / 'd01_d04_research' / 'energy_distribution_results.json').read_text())
    nel = rows(D / 'lunar_impact_energy' / 'neliota_192_validated_energy_catalogue.csv', ('event_id', 'stream', 'R_plus_I_energy_J'))
    out['d01d04'] = dict(inputs=dm['inputs'], base=dm['base_photon_budget'], results={k: v for k, v in dm.items() if k not in ('inputs',)},
                         neliota=[dict(id=int(r['event_id']), stream=r['stream'], E=r['R_plus_I_energy_J']) for r in nel],
                         eta=dict(nominal=ed['eta_nominal'], scenarios=ed['eta_scenarios']), quantiles=ed['optical_quantiles_J'])
    p = D / 'studies_explorer' / 'studies_data.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, separators=(',', ':')), encoding='utf-8')
    print(p, p.stat().st_size // 1024, 'kB')


if __name__ == '__main__':
    main()
