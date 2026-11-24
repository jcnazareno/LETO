# Orbit and attitude disturbance research for concept definition

Task created: **29 October 2026**. Status: **quantitative concept study completed 29 October 2026**. The brief below is retained; actual methods, reproduction and limits follow its completion criteria.

## Objective

Quantify the **orbital and attitude disturbance environment** of the lunar impact-flash/event-camera concept, compare it directly with representative Earth-observation orbits, and derive practical concept-design conclusions. Answer both user questions:

1. Through which effects can an orbit decay or become unsafe, and by how much in lunar versus Earth orbits?
2. Which attitude disturbances occur, how large are they, and how do they compare between lunar and Earth orbits?

Complete the research, calculations, and results. This brief is the starting point, not the deliverable. Keep the two analyses linked through spacecraft geometry, attitude, propulsion, observing interruptions, and mission lifetime.

Follow AGENTS.md in the mission reference: one primary science objective, entire-lunar-surface coverage, a proportionate four-person educational project, and a final mission-design report limited to 50 A4 pages. Study-case orbits, lifetimes, spacecraft properties, and control limits remain assumptions until contributors select them. This supporting research must not silently choose the mission architecture.

## Read first

1. `AGENTS.md` and `Concept_Description.md` in the mission reference.
2. Design-driving quantities in the mission reference, particularly D02–D06 and D09–D10, and open questions, particularly localization and coverage questions R5–R6. Preserve stable D/R identifiers and use AGENTS.md over stale scope statements.
3. Earth versus lunar observation report, especially attitude control, pointing, orbit maintenance and lifetime.
4. [D01–D04 research results](../../outputs/d01_d04_research_2026-10-28/d01_d04_research.md) and [source/model records](../d01_d04_research/README.md). Existing pointing allocations, optical examples, and observation ranges are conditional research fixtures, not demonstrated performance.
5. [Radiation research brief](../radiation_environment_research/README.md) and [its result index](../../outputs/radiation_environment_research_2026-10-29/README.md), to align comparison cases and file organization. This study can proceed independently; do not assume the radiation results are finished or change that task's files.
6. Supplied mission-design, LUMIO, and sensor references in `literature/`.

## Common comparison cases and spacecraft assumptions

Use a small, justified case set, approximately matching the radiation study where useful:

- **Earth:** a representative **400 km / 51.6° LEO** and a near-polar/Sun-synchronous EO case near **600 km / 98°**. Specify eccentricity and other initial conditions, atmospheric state, epoch and attitude. The values are comparison fixtures; do not claim an exact Sun-synchronous orbit from rounded inclination alone.
- **Low lunar orbit:** a representative near-circular **100 km polar orbit**, with **50 km** as a sensitivity case where useful. Compare with a sourced frozen or quasi-frozen candidate to establish how orbit design changes maintenance and surface-clearance risk. Do not assume every low lunar orbit decays at the same rate.
- **Distant lunar observation:** one defined Earth–Moon libration-region/distant-observer trajectory relevant to the existing roughly **50,000 km** observation-range examples. Use a documented trajectory or state and epoch where possible. A distance alone does not define a halo orbit, stationkeeping cost, or stability.
- Brief GEO/other Earth-orbit context is useful only to explain the limits of a LEO comparison. Transfer perturbations may be noted separately if they drive design; keep the main effort on the operational observation phase.

For the environmental comparison, use the **same explicitly defined reference spacecraft** across cases, or normalize with stated parameters. List mass, projected areas, drag/optical coefficients, area-to-mass ratios, surface orientation, inertia tensor, centre-of-pressure/centre-of-mass offsets, residual magnetic dipole, thermal-emission assumptions and propulsion geometry. Add a bounded sensitivity to size/area, asymmetry and offsets if materially important. Derive inertia from geometry or identify its evidence; keep assumptions distinct from selected hardware. Avoid comparing a large EO satellite with a small lunar spacecraft and attributing the whole difference to environment.

## Part A: Orbital disturbances, evolution and maintenance

### Distinguish what is changing

Define **dissipative orbital-energy loss**, osculating versus mean-element changes, secular precession, periodic eccentricity/periapsis excursions, resonance or libration-orbit instability, escape, and collision with terrain. A falling periapsis or changing two-body energy in a multi-body problem is not automatically atmospheric-style decay. State the central body, reference frame, altitude/reference radius, epoch and element definitions.

### Evaluate mechanisms

Quantify and rank the applicable effects, with omissions justified by numerical bounds or primary-source evidence:

- Atmospheric drag in Earth LEO: density and solar/geomagnetic variation, relative atmospheric motion, attitude/projected area, drag coefficient and ballistic coefficient. Bound any lunar-exosphere contribution rather than copying an Earth drag model or asserting an unsupported exact zero.
- Non-spherical Earth gravity versus lunar harmonics/mascons: include the importance of gravity-model degree/order, orbital orientation, eccentricity, terrain clearance and frozen-orbit choices. Do not use an Earth-style J2-only lunar model to certify lifetime.
- Third-body Earth/Sun/Moon perturbations as relevant to each case. Use differential third-body accelerations for a body-centred frame, and an appropriate multi-body model for libration trajectories.
- Direct solar-radiation pressure, eclipses and attitude-dependent optical response; reflected-light/thermal radiation forces where consequential. Include thermal recoil, outgassing/leaks, manoeuvre execution errors or rare impulses as bounded secondary effects where they matter, with environmental and spacecraft-generated sources distinguished.
- Conservative versus dissipative effects and their interaction. A large instantaneous perturbing acceleration need not produce monotonic altitude loss or a large correction budget.

### Quantities and outputs

Produce a side-by-side **force/acceleration budget** with explicit units, geometry, peak/typical/average convention, scaling and uncertainty. Translate the major effects into **time histories or sourced numerical evolution**, not just a list of accelerations:

- Semimajor axis/energy where meaningful; eccentricity; minimum terrain clearance/periapsis and apocentre; inclination, node and apsidal changes where well-defined; and relative trajectory/coverage drift for a distant observer.
- Rates such as km/day or degrees/day only over a stated applicable interval. Do not linearly extrapolate oscillations, drag at changing altitude, or chaotic/unstable growth into a universal annual rate.
- Use comparable **30-day** evolution plots or tables as a starting point; extend to **one year** or stop at a defined impact/escape/validity limit where justified. These are analysis horizons, not selected mission lifetimes. Establish actual altitude-loss/periapsis-excursion magnitudes for lunar and LEO cases.
- Explicit uncontrolled versus maintained cases. For maintenance, define the permitted orbit/coverage/clearance envelope, correction rule, manoeuvre timing, navigation knowledge and execution errors. Give cadence and **m/s per month/year** or an evidence-based range with limitations, and identify manoeuvre downtime and missed-correction recovery time.
- Lifetime/time-to-impact is conditional on the initial state, physical boundary and force model. A no-impact propagation only establishes survival over the propagated interval. Do not report a single universal lunar lifetime or stationkeeping number.

**Do not compute stationkeeping delta-v by multiplying the magnitude of a conservative disturbance acceleration by elapsed time.** Use an explicit control policy or an applicable published mission result, labelled with its orbit and operating assumptions. Separate nominal maintenance, navigation/dispersion recovery, momentum unloading, contingency and disposal allocations.

## Part B: Attitude disturbances and control consequences

### Quantify the environmental torque budget

For the same stated spacecraft and comparable attitudes, calculate or bound:

- Gravity-gradient torques from the relevant bodies, using the appropriate tidal gradient and inertia tensor. Check altitude/body-radius scaling; do not scale torque directly from the ratio of surface gravities.
- Aerodynamic torques in LEO, with projected area, relative velocity, density and pressure-centre offset; bound the lunar counterpart.
- Direct solar-radiation-pressure torques, including optical properties, offsets, eclipse transitions and any secular bias versus periodic variation.
- Reflected sunlight and planetary/lunar infrared pressure torques, with view/illumination geometry, and anisotropic spacecraft thermal recoil if significant.
- Residual magnetic dipole interacting with local fields: compare Earth with applicable lunar crustal fields, interplanetary field and magnetotail conditions. Quantify any proposed magnetic control authority from the actual environment; neither an assumed Earth-like lunar field nor an exact zero field is adequate.
- Solar-wind/charging/electrostatic/Lorentz effects and micrometeoroid impulses only to the depth needed to establish significance or defensible neglect. Keep continuous torques, stochastic inputs and rare impulses distinct; do not duplicate a full radiation or impact-population study.

Keep **spacecraft-generated disturbances** in a separate companion budget: wheel imbalance/bearing noise, mechanisms or array motion, structural/thermal changes, thruster impulses/misalignment, propellant motion and leaks as relevant. They may drive optical jitter even if environmental torques drive long-term momentum. Use actual component disturbance evidence or clearly bounded assumptions; missing spectral data must remain explicit.

Report **N·m** by axis or a clearly defined vector norm, along with peak/RMS/mean/bias conventions, direction, time/frequency dependence, uncertainty, and a matched lunar/LEO ratio where meaningful. Show dominant contributions rather than summing unrelated worst cases as if simultaneous. Distinguish physical pointing disturbances from attitude-sensor measurement errors, such as star-tracker stray light or gyro bias.

### Turn torques into design consequences

- Compute accumulated angular momentum and bounded periodic momentum excursions with consistent frames and vector dynamics. A periodic torque amplitude multiplied by the entire mission duration is not a valid wheel-storage requirement.
- Give an illustrative wheel torque/storage requirement and unloading cadence using declared usable wheel momentum, slew demands, initial state and margins. Use actual device data for any candidate wheel/thruster; retain the distinction between a class example and a selection.
- Assess detumbling, safe mode, momentum unloading and pointing without relying on unverified magnetic actuation in lunar space. Estimate unloading propellant/impulse, net orbit perturbation where applicable, and science interruption/settling. Account for thruster geometry rather than assuming every angular impulse produces the same translational delta-v.
- Translate torque into angular acceleration and, with stated assumptions, open-loop drift or a representative closed-loop pointing response. **Torque magnitude alone does not establish arcsecond pointing accuracy or jitter.** State controller bandwidth/transfer assumptions, sensor errors, structural response and any unavailable disturbance spectra.
- Relate image motion/boresight error to event-camera traffic, light-curve quality and D04 localization over the relevant observation windows. Distinguish line-of-sight stability, attitude knowledge, absolute pointing and orbit-position knowledge. Do not present the previous illustrative ADCS allocations as achieved hardware performance.

## Evidence, numerical modelling and checks

Browse primary literature, agency mission/flight-dynamics documentation, original gravity/atmosphere/ephemeris model documentation, and component datasheets/disturbance tests. Useful starting families include GRAIL-based lunar gravity; LRO/LADEE frozen-orbit and maintenance evidence; applicable distant lunar-observer mission design; and original EO disturbance/drag studies. Check versions and applicability rather than relying on source names. Trace important values to publication/version, URL/DOI, page/table/figure, spacecraft properties, initial state, frames, duration, force model and uncertainty.

Distinguish **flight measurements**, **published simulation/design results**, **this study's propagated results**, **analytical estimates**, **illustrative assumptions**, **proposed design allocations**, and **unresolved performance**. Published maintenance schedules or lifetime anecdotes are not transferable without their initial conditions and operational constraints.

Implement a modest reproducible numerical study appropriate to concept definition. Use available current-host tools and source-labelled physical inputs. State force-model fidelity, coefficients and normalization, frame/time conventions, ephemerides, integrator, tolerances, outputs and termination conditions. For a rotating lunar gravity field, handle orientation consistently. Apply convergence/sensitivity checks to the actual claims: numerical step/tolerance, gravity degree/order or documented truncation limits, starting geometry, area/mass and density uncertainty as appropriate.

Check central-body two-body conservation where valid, analytical drag and gravity-gradient limiting cases, torque scaling with offsets/inertia, units, and independent workbook calculations. Do not demand conservation of two-body energy in an explicitly time-dependent multi-body model. For nearly circular/equatorial cases, use nonsingular metrics where classical elements become ambiguous. Test an actual terrain/reference-surface crossing condition before reporting impact.

If a high-fidelity tool, coefficient set or trajectory cannot be obtained, use applicable published propagated results plus honest analytical bounds, and explain which claims cannot be made. A point-mass/J2 sketch must not be relabelled a validated lunar lifetime simulation. Never imply GMAT/Orekit/SPICE/STK or other tools ran without execution evidence. Keep progress autonomous rather than stopping the entire study for one inaccessible service.

Document dependencies, exact Linux/current-host reproduction commands, inputs/outputs, checks, access limitations and validation status here once code exists. Historical Windows paths are not current execution commands. Use the applicable spreadsheet/PDF skills and render exported reports/figures for visual review.

## Required concept conclusions

End with an evidence-linked decision table covering:

- Which orbital effects dominate each candidate class; how much altitude/periapsis/coverage changes; whether low maintenance is plausible and what conditions support it.
- Initial stationkeeping, momentum-unloading and disposal resource ranges, their assumptions, and the value of selecting a more favourable orbit.
- Dominant disturbance torques and whether wheel torque, stored momentum, unloading availability, pointing/jitter, or knowledge accuracy drives ADCS.
- Spacecraft symmetry, surface/array/radiator arrangement, pressure-centre alignment, magnetic cleanliness, structural/component choices and operational trade-offs.
- Consequences for event-camera observing efficiency and quality, D02–D06/D09–D10, navigation/coverage, propulsion, power, structure and science lifetime.
- What can be concluded at concept/SRR level, what still needs later simulation/qualification, and the minimum next work for this four-person project. Keep justified conservative allowances distinct from accepted mission requirements.

## File organization and deliverables

Paths are relative to the SMD root; follow the radiation research pattern.

| Location | Content |
| --- | --- |
| `outputs/disturbance_environment_research_2026-10-29/README.md` | Results index, actual status, main conclusions, limitations and reproduction links. |
| `outputs/disturbance_environment_research_2026-10-29/disturbance_environment_research.md` | Main findings: orbit evolution, force and torque comparisons, maintenance, pointing/momentum consequences, evidence and concept recommendations. |
| `outputs/disturbance_environment_research_2026-10-29/disturbance_environment_research.xlsx` | Inspectable case/input definitions, evidence register, orbital-force/evolution comparison, maintenance assumptions, torque budget, momentum/pointing calculations, decisions and open items. Use meaningful live formulas. |
| `outputs/disturbance_environment_research_2026-10-29/lunar_disturbance_environment_report.pdf` | Concise supporting report with readable matched comparisons and plots, suitable for concept/SRR use. |
| `analysis/disturbance_environment_research/` | This README, reviewed source records, inputs, propagation/torque/calculation scripts, builders, and numerical validation. Follow existing simple naming conventions, such as `research_data.mjs`, `model_inputs.json`, `model_results.json`, `calculate.py`, `build_workbook.mjs` and `build_report.py`, as useful. |
| `data/disturbance_environment/` | Source-labelled machine-readable case definitions/comparison data, propagated time histories where run, and a provenance README. Preserve original versus derived values. |
| `figures/disturbance_environment/` | Standalone scientific plots: orbital evolution/clearance, force/torque comparisons, and momentum/pointing responses where supported. Label units, cases, model fidelity and uncertainty. |
| `tmp/disturbance_environment_research/` | Research copies, extracted source text, model/ephemeris caches, workbook previews and PDF renders. |

Preserve supplied PDFs, earlier dated results and the radiation task's files. Keep code and intermediates out of the results folder. Use and validate relative links in project Markdown.


## Completion criteria

- Defensible numerical lunar–LEO comparisons of **both orbital evolution and attitude torques**, under explicit matched spacecraft/environment assumptions and units.
- At least one quantified lunar low-orbit evolution/clearance case compared with Earth LEO, plus a sourced treatment of the distinct distant/libration case; conservative geometry changes are separated from dissipative decay.
- Ranked environmental force/torque budgets, meaningful uncertainty/sensitivity, and supported stationkeeping, momentum/unloading and pointing consequences.
- Clear concept-design conclusions, with candidate decisions and open items traced to evidence and provisional assumptions.
- Reproducible data/calculations, a reviewed workbook/PDF, readable scientific plots, checked links and a current results index. State any limits on dynamical/closed-loop fidelity honestly; do not substitute an extensive work plan for the quantitative findings.

## Completed implementation and reproduction

The [results index](../../outputs/disturbance_environment_research_2026-10-29/README.md) links the findings, eight-sheet live-formula workbook and ten-page A4 supporting PDF. There are six scientific plot topics, nine low-lunar propagation cases, six Earth atmosphere/evolution cases and a JPL halo reference/drift/ideal-targeting comparison. Data provenance is [documented separately](../../data/disturbance_environment/README.md).

### Files and editable assumptions

- `calculate.py`: shared SI spacecraft fixture, normalized spherical-harmonic evaluator, actual SPICE ephemeris/orientation use, lunar propagation, actual NRLMSIS2.0 densities, circular averaged Earth decay, scalar torque/momentum/PD response and plots. Physical constants and spacecraft assumptions are grouped near the top. Orbital case definitions are in `main()`; atmospheric proxies are in `density_table()`. The area is an effective projected fixture, not a body-box face area.
- `distant_case.py`: chooses the long-period northern L2 JPL family branch nearest C=3.09, propagates CRTBP and initial offsets, then applies an explicit ideal weekly downstream-position targeting policy. Exact state/normalization and impulses are in `distant_results.json`.
- `supplement.py`: independent analytical force/torque bounds, mean-density aerodynamic torque, pressure-centre/thermal/magnetic sensitivities, propulsion/unloading geometry, measured historical wheel-imbalance scaling and image-motion calculations. Assumed values are directly visible next to each calculation.
- `evidence.json`: DE01-DE24, evidence type/date, direct URL, page/table/section and access/transfer limits. `download_sources.py` caches public models/sources and hashes. Manufacturer/university 403/404/timeouts are retained; a search extract is not represented as a downloaded PDF.
- `build_findings.py`, `build_workbook.mjs`, `build_report.py`: authoritative presentation builders from reviewed numerical outputs. `decisions.json` is generated by the findings builder. The workbook has editable analytical inputs and formulas; changing them **does not regenerate propagated histories**.
- `model_results.json`, `supplement_results.json`, `distant_results.json`: derived numerical outputs; `workbook_validation.json` and `validation.json`: actual checks. Do not edit calculated results to tune an input.

### Current Linux runtime

The bundled executables were located with `load_workspace_dependencies`. Numerical libraries were installed into the task-specific `/tmp/smd-disturbance-deps`; that directory is temporary and may need reinstallation after host cleanup. Document libraries (`reportlab`, `pypdf`, `openpyxl`) come from the bundled Python. This study did not modify shared dependency directories or the v2e environment.

From the SMD root:

```bash
SMD_PY=/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
SMD_NODE=/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node
"$SMD_PY" -m pip install --target /tmp/smd-disturbance-deps -r analysis/disturbance_environment_research/requirements.txt
export PYTHONPATH="/tmp/smd-disturbance-deps${PYTHONPATH:+:$PYTHONPATH}"
export NUMBA_CACHE_DIR=/tmp/smd-disturbance-numba
export MPLCONFIGDIR=/tmp/smd-disturbance-mpl
```

Network access is needed only for missing dependencies or source/model caches:

```bash
"$SMD_PY" analysis/disturbance_environment_research/download_sources.py --models-only
```

The model prefix preserves the original GRGM1200A header and degrees/orders through120, not the complete1200-degree file. Existing source-cache hashes and failed source access records are preserved in `tmp/disturbance_environment_research/sources/manifest.json`. A full optional literature-cache attempt is the same command without `--models-only`.

Reproduce numerical calculations and artifacts:

```bash
"$SMD_PY" analysis/disturbance_environment_research/calculate.py --fresh
"$SMD_PY" analysis/disturbance_environment_research/distant_case.py
"$SMD_PY" analysis/disturbance_environment_research/supplement.py
"$SMD_PY" analysis/disturbance_environment_research/build_findings.py
"$SMD_NODE" analysis/disturbance_environment_research/build_workbook.mjs
"$SMD_PY" analysis/disturbance_environment_research/build_report.py
"$SMD_PY" analysis/disturbance_environment_research/validate.py
pdftoppm -r 100 -png outputs/disturbance_environment_research_2026-10-29/lunar_disturbance_environment_report.pdf tmp/disturbance_environment_research/report_renders/page
```

The Node builder uses a symlink at `analysis/disturbance_environment_research/node_modules` to the bundled runtime's `dependencies/node/node_modules`. Recreate that symlink if paths move; do not use stale Windows junctions or install repo-local artifact libraries. Running `calculate.py` without `--fresh` reuses existing `Moon*_summary.json` and time histories while recalculating Earth/analytical checks and plots. **After changing lunar assumptions/model code, use `--fresh`**. Case outputs are overwritten intentionally only within this study; retain a dated copy before a new scientific scenario campaign. The original full computation and subsequent checks are logged under this task's `tmp/` directory.

### Executed fidelity and checks

- Low lunar epoch2026-10-29T00:00UTC; Moon-centred J2000 SI states. Elements use the epoch PA equator frozen inertially, with altitude above1738km. GRGM1200A label GM; 4π normalization, no Condon-Shortley phase. DOP853 rtol2e-9, atol1e-5, maxstep120s. Direct SRP and cylindrical Moon shadow; geometric DE440s Sun/Earth positions cubic-sampled at1h.
- Gravity is truncated to80×80, checked against40×40 and120×120. Available lunar orientation is DE421 PA whereas gravity declares DE430 PA: explicitly approximate, with a0.01deg orientation sensitivity. This is not an operational frame/terrain/lifetime model. Earth shadow, tides, gravity clones and DEM intersection are unmodelled.
- Nominal100km hp changes22m at day30 for80→120,2.5m for tightened integration and3.2m for the tested orientation offset (both at the level of run-to-run reproducibility; an independent 30 Oct rerun gave 3.2 m and 0.7 m). The50km degree change is0.283km at day30; degree120 was not extended to the day48 buffer crossing. Stop at11km radial height is an assumed screening buffer, not a geolocated terrain impact or validated safety envelope.
- Independent J2 sign/normalization error2.3e-16; potential-gradient finite-difference error1.3e-10; two-body30day relative energy range1.7e-12. Two-body conservation is not demanded for the time-dependent multi-body model.
- Earth model is a circular mean-a/J2-node ODE with NRLMSIS2.0 first-orbit mean profiles, corotating atmosphere and fixed solar/ap cases. Horizons365days or120km validity boundary. It does not predict e/apsis short-period behavior, weather history or terminal reentry. Third bodies are screened analytically for LEO; they are not included in its secular ODE.
- JPL halo uses actual catalogue v1.0 state/units; closure≈1e-5m and Jacobi variation7.1e-15. The finite-difference unstable multiplier340.8 gives catalogue index(λ+1/λ)/2≈170.405. Ideal targeting is a numerical control demonstration, not an annual propellant estimate.
- Torque bounds/scenarios do not constitute a simultaneous vector worst case. Periodic momentum integration is in a declared fixed inertial principal plane. Distant circular-surrogate momentum is not halo momentum. The scalar0.02Hz PD model has no structural/sensor/actuator uncertainty; no achieved jitter is asserted.
- Workbook calculations were independently compared with Python, recalculated with the pressure-arm input doubled and restored, then scanned for formula errors. Every sheet and all ten PDF pages were rendered and visually reviewed. The saved PDF was reopened, page-counted and text-checked; local Markdown links were checked. See `validation.json` for actual final results.

### Handoff

The concept conclusion is to trade a favourable low-lunar geometry against a maintained distant observer using **whole-surface usable exposure and characterized samples**, while retaining external thruster unloading and separate structural/jitter evidence. The0.05Nms wheel class,16-30m/s/year L2 maintenance sensitivity and30kg fixture remain provisional. For the100km polar candidate, maintenance cost is still TBR;30day survival is not a zero-cost argument. The minimum later design is one selected epoch/trajectory and explicit maintenance/navigation/execution envelope, CAD inertia/plate geometry, wheel/thruster-array sizing, knowledge/jitter budget and the integrated science-availability timeline. Detailed research stays in supporting files; carry only essential results into the final50pages.
