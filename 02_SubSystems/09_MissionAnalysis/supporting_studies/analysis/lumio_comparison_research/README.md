# LUMIO mission comparison for concept definition

Task created and completed: **29 October 2026**. Status: **concept comparison complete; configuration conflicts and SMD feasibility work remain explicit**.

## Completed results and reproduction

Start with the [finished-results index](../../outputs/lumio_comparison_research_2026-10-29/README.md). The retained brief below records the commissioned scope. Results include 19 primary sources, 43 claims, 16 criteria/gap rows, 12 timeline entries, 13 conflicts, D01-D10 comparison, seven recommendations, a seven-sheet workbook, a ten-page supporting PDF and four PNG/PDF figure pairs.

### Inputs, scripts and actual methods

- `research_data.py`: curated sources, claims, criteria, timeline, conflicts and comparisons; exports JSON/CSV under `data/lumio_comparison/`.
- `model_inputs.json`: inspectable geometry, operations, integration, statistics, data-volume and source-budget inputs with units/provenance. Trial SMD bins, population variance and availability remain assumptions.
- `calculate.py`: spherical geometry, ideal exponential bin integration with onset-phase bounds, rough published exposure scaling, sample/data-volume sensitivities, source arithmetic and scientific plots. No ephemeris propagation, calibrated selected-sensor model or new LUMIO Monte Carlo.
- `build_workbook.mjs`: artifact-tool authoring, recalculation, input perturbation/restoration, preview rendering and XLSX export. Calculations remain live formulas.
- `build_report.py`: ReportLab PDF authoring from reviewed data and figures. `readable.py` formats compact prose while preserving URLs, IDs, scientific notation and component names.
- `fetch_sources.py`: public downloads, SHA-256 hashes and one-based PDF text extraction. `--offline` reuses originals; `--only L12,L19,L20` limits retrieval. HTTP403/timeouts remain recorded. Indexed primary PDF text review is recorded separately in `tmp/lumio_comparison_research/web_access_manifest.json`; snapshots are not original PDFs.
- `validate_outputs.py`: independent saved-XLSX caches/formulas, source IDs, CSV round trips, PDF A4/text bounds, figure resolution, supplied-PDF hashes and local links.

### Verified current-host commands

Run from the workspace root in Bash. Bundled Python supplies PDF/image libraries. It lacks matplotlib, so the installed system Python supplies NumPy/matplotlib for the calculation/plot script. Source downloads initially met sandbox DNS restrictions, then used authorized public network access. No installed dependency directory was modified.

```bash
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/lumio_comparison_research/fetch_sources.py --offline
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/lumio_comparison_research/research_data.py
MPLCONFIGDIR=/tmp/smd-lumio-matplotlib python3 analysis/lumio_comparison_research/calculate.py
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node analysis/lumio_comparison_research/build_workbook.mjs
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/lumio_comparison_research/build_report.py
pdftoppm -scale-to 1300 -png outputs/lumio_comparison_research_2026-10-29/lumio_mission_comparison_report.pdf tmp/lumio_comparison_research/pdf_renders/page
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/lumio_comparison_research/validate_outputs.py
```

The task-local `node_modules` symlink points to `/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules`; recreate only if missing. Builders overwrite only this study's artifacts. Do not run historical mission/D01-D04 builders to reproduce this comparison. The Markdown findings are a reviewed authored document and require a targeted manual update when evidence changes.

### Validation and next-agent handoff

See [validation.json](validation.json), `calculation_validation.json` and `workbook_validation.json`. Executed checks cover analytic bin-phase extrema, tile product 14.8 Gbit, delta-v sum 79.05 m/s, source mass/power discrepancies, live input changes, saved caches, PDF pages/text bounds and local links. All ten PDF pages, representative crops from all seven worksheets and all four figures were visually reviewed. Native Excel, hardware qualification, selected-sensor calibration, complete geographic exposure and useful yield were not tested.

Keep October 2024 78 ms full-frame integration and updated bands separate from the 66 ms/820 nm-split model. ESA 12U/12UXL and ASI 16U conflict remains unresolved. Dated March 2026 Phase C and potential 2028 launch are status/targets, not flight results. One year is a documented minimum and nominal operations interval; an optimization selecting exactly one year was not established. Historical count criteria 240/100/2 are not verified current thresholds.

The bounded next study couples one primary observable, realistic sensor/optics cases, minimum radiometric support, whole-surface exposure and useful characterized yield. Include pointing/motion, maintenance/unloading, calibration and end-of-life availability. Trial 100 useful events for 10% mean precision assumes CV=1; it is not a selected requirement. Preserve the educational evidence standard, both hemispheres/poles and the 50-page final-report limit. Radiation and disturbance outputs remain separate and intact.

## Objective

Produce a reliably sourced comparison of **LUMIO** and the **SMD lunar impact-flash/event-camera concept**. Answer the user's questions about LUMIO's mission statement and success criteria, orbit, mission-duration rationale, CubeSat choice, and satellite design. Explain which design lessons transfer to SMD and which scientific benefit SMD would still need to establish.

Complete the research and deliverables in this task. Preserve the scope in AGENTS.md in the mission reference: one primary science objective, an event-camera-centred mission, entire-lunar-surface coverage, only necessary supporting systems, and a proportionate four-person educational project with a final mission-design report limited to 50 A4 pages. LUMIO's choices are comparators, not automatically SMD requirements or a reason to change fixed proposal constraints.

## Read first

1. Mission reference files `AGENTS.md`, `Concept_Description.md`, design drivers, and open questions. Later scope clarifications override stale broad-objective or acceptance-evidence wording.
2. [D01–D04 results](../../outputs/d01_d04_research_2026-10-28/d01_d04_research.md) and [research source records](../d01_d04_research/research_data.mjs), especially E09–E11. Recheck original sources before reusing values. SMD's existing numerical examples are provisional assumptions, not achieved capabilities.
3. The supplied Cervone et al. LUMIO mission paper and Topputo et al. detection paper in `literature/`, and the Earth–lunar mission report.
4. [Radiation research index](../../outputs/radiation_environment_research_2026-10-29/README.md) and [disturbance research index](../../outputs/disturbance_environment_research_2026-10-29/README.md), for applicable completed findings or current scope. Do not wait for an unfinished task or change its files.

## Evidence versions and reliability

Establish a dated evidence timeline: original challenge/concept constraints; later feasibility/Phase-A design; subsequent payload/platform updates; and the best supported public configuration **as of 29 October 2026**. Separate design publication date, mission phase, event date, webpage update/access date, and future schedule targets. A newer webpage does not necessarily supersede a more detailed configuration-controlled technical source.

For each important claim, record publication/organization, URL/DOI, exact page/section/table/figure, design epoch, units/conditions, evidence type and confidence. Distinguish **formal requirement**, **stated objective**, **published design**, **measured/verified hardware result**, **planned activity**, **this study's calculation**, **engineering inference**, and **not established in reviewed public sources**. A generic component datasheet or vendor product is not proof that the component was selected or qualified for LUMIO.

An initial source conflict to investigate is **12U/12UXL versus 16U**: ESA's dated March 2026 update and its mission profile describe 12U-related configurations, while ASI's mission page lists 16U. Log these as conflicting public claims, not evidence by itself of a confirmed redesign. Also reconcile launch/Phase-C dates, transfer architecture, propulsion, payload channels and performance figures when sources disagree. Do not combine incompatible epochs into one supposedly current spacecraft budget. Leave unresolved conflicts visible with their consequences for the comparison.

## Questions to resolve

### 1. Mission statement, objectives and criteria

- Identify LUMIO's primary scientific question, mission statement, observable/data products and intended scientific contribution. Distinguish science, technology demonstration and future hazard-assessment applications.
- Recover published mission-level requirements and success criteria where available: detections/validated samples, spatial or temporal sampling, coverage/exposure, limiting signal, recording quality, localization, duration, autonomy or technology demonstrations. Trace the criteria to source versions; do not invent formal requirements from promotional aims.
- Explain minimum/full success if actually defined. If public documentation gives only goals or design targets, label them accordingly. Map objectives to measurable outputs and available verification evidence.
- Paraphrase mission statements accurately and label paraphrases. Any short verbatim excerpt must remain within the applicable per-source quotation limit across the deliverables; avoid reproducing long copyrighted passages.

### 2. Orbit and its rationale

- Identify the operative orbit family, relevant Earth–Moon Lagrange point, geometry, period, distance range, visibility and stability/maintenance characteristics that can be sourced. Define Moon-centre distance, surface/target range and coordinate frames rather than treating them interchangeably.
- Explain the documented orbit trade: useful dark-farside access, lunar phase/illumination, field of view and resolution, Earth visibility/communications, navigation, transfer access, eclipse/thermal environment, stationkeeping and disposal. A permanently visible disc is not continuously useful science exposure or coverage of the whole Moon.
- Distinguish current launch/delivery/transfer assumptions from historical carrier/deployer scenarios; identify which segments and delta-v costs belong to LUMIO versus a carrier. Describe uncertainty where no final opportunity is selected.
- Use published geometry/operations results and modest checks where useful. Do not duplicate the entire disturbance task or invent an ephemeris-level simulation.

### 3. Mission duration and why it was selected

- Separate development schedule, launch date, transfer/commissioning, nominal operations, actual science live time, engineering/navigation cycles, design life, possible extension and end-of-life. A Phase-C contract end date is not a science-mission end date.
- Find explicit rationale or source requirements for the nominal duration. Investigate scientific sample/statistical needs, meteoroid streams/seasonal sampling, usable illumination/exposure, propellant/consumables, hardware life/radiation, funding and programme constraints only to the extent supported.
- Quantify total versus usable monitoring time, cycles, sampled area-time and expected useful detections where evidence permits. State detection efficiency, energy band/range, false-confirmation assumptions, and uncertainty. Keep a paper's prediction distinct from an observed yield.
- If the literature states a duration without explaining its choice, say so. Provide any engineering/scientific explanation as an explicit inference or sensitivity calculation; do not assert a plausible rationale as the team's documented decision.

### 4. Why a CubeSat, and why this size?

- Establish whether CubeSat/form-factor constraints arose from the original call, programme, demonstration goals, deployment interfaces, cost/technology strategy, or an actual optimization. Separate an imposed constraint from a design trade or later accommodation change.
- Trace the form-factor and spacecraft mass/envelope history. Explain how the payload, optics/baffle, propulsion, deployables, communication hardware and power/thermal needs fit the sourced configuration. Distinguish wet/dry mass and margins, stowed/deployed dimensions, and unit variants.
- Assess the benefits and limits of miniaturization using documented budgets/technology decisions. Do not assume that CubeSat means inexpensive, propulsion-free, or a scientifically optimal platform. Report cost and schedule numbers only if adequately sourced and scoped.
- Explain which of these reasons apply to SMD, whose platform class is not fixed. Preserve the proposal's event camera and whole-surface requirement when drawing lessons.

### 5. Reliably sourced satellite design

Build a subsystem matrix using the report-guide categories. For each item list its value or architecture, units/conditions, role, source location, configuration epoch, status and confidence. Report genuine public gaps rather than filling a complete-looking design with assumptions.

| Subsystem / area | Details to investigate when publicly supported |
| --- | --- |
| Payload | Aperture, focal length/f-number, field of view, baffle, optical throughput, channel bandpasses, detector technology/array/pitch, cadence/exposure/readout gaps, synchronization, calibration, signal/noise and false-confirmation logic, localization and any temperature/energy inference. |
| Power | Array type/area/deployment or articulation, generation by condition/mode, battery energy, power budget and margins, eclipse/end-of-life assumptions and EPS architecture. |
| Thermal | Passive/active control, radiator/heater placement, sensor/component temperature limits and stability, environmental/operational design cases. |
| Structure | Form factor/envelope, layout and deployables, equipment/mass budget, wet/dry/propellant distinctions, interfaces and documented qualification status. |
| Propulsion | Propellant/system type, main/RCS thrusters, thrust/impulse/Isp or control authority, propellant and delta-v budgets, transfer/stationkeeping/unloading/disposal allocation, and design changes. |
| Telecommunication | Bands, transponder, antennas, data rates/ranges, ground support, direct-to-Earth versus relay/inter-satellite links and their availability assumptions. |
| Attitude Determination and Control | Sensors/actuators, pointing/knowledge/stability conventions, reaction-wheel momentum, external unloading method, navigation/attitude distinction, safe modes and alignment constraints. |
| On-board Data Handling | Flight/payload processing, event/flash selection, rejection/coincidence, image tiles/compression, storage/data volume, timing and autonomy/FDIR where documented. |
| Mission Analysis / Ground / Deployment | Orbit/transfer, operations/science cycles, optical/radiometric navigation, ground processing, carrier/launch interfaces, service dependencies, lifetime and end-of-life. |

Do not equate frame cadence with useful flash time resolution, pixel sampling with surface-location accuracy, a limiting magnitude with completeness, or a subsystem design number with flight-proven performance. Preserve definitions and measurement conventions.

## Comparison with SMD and decision conclusions

Create a side-by-side matrix of LUMIO's **specified design epoch** versus SMD's **proposal constraints, provisional studies and unknowns**. Map the comparison to D01–D10: sensitivity, temporal information, photometry, localization, entire-surface/usable exposure, useful samples, reliability, observing envelope, lifetime and delivery. Include architecture, subsystem effort and external dependencies where they affect a fair comparison.

Normalize numerical performance comparisons to stated range, aperture/throughput, spectral response, flash duration/spectrum, background, exposure/bin phase, detection/confirmation criteria and uncertainty. Keep measured, simulated and proposed cases distinct. Do not claim event-camera superiority merely from timestamp ticks, nor farside access as an SMD novelty. A newer LUMIO design may narrow a previously claimed advantage; make that explicit when supported.

Use simple reproducible calculations where they resolve decisions: angular footprint/FOV versus disc, exposure/cadence effects on common light curves, area-time/sample yield, or matched radiometric bounds. Label unavailable inputs and avoid forcing a quantitative ranking where the evidence is incompatible. A cost/performance comparison needs compatible cost scope and performance definitions.

End with clear conclusions: transferable design lessons; choices driven by LUMIO-specific programme constraints; SMD differences/risks; one or a small number of scientifically meaningful added-value hypotheses consistent with the current scope; minimum evidence and approximate samples needed to substantiate them; and what cannot yet be concluded. Do not silently baseline a new SMD mission statement, hardware selection, lifetime, orbit or requirement. If no substantiated advantage is established, say so and identify the smallest feasible next comparison.

## Starting primary-source leads

Recheck these leads and search for newer or more detailed sources; this is not a sufficient evidence set by itself.

- Cervone et al., 2022, supplied mission design: [DOI](https://doi.org/10.1016/j.actaastro.2022.03.032).
- Topputo et al., 2023, supplied radiometric/detection design: [DOI](https://doi.org/10.1016/j.icarus.2022.115213).
- Pancalli et al., 2024, payload design: [Politecnico author version](https://re.public.polimi.it/retrieve/f609816c-3cf5-4468-93bc-12ee09e38135/PANCM01-24.pdf).
- [ESA dated Phase-C update, 27 March 2026](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Shaping_the_Future/A_leap_forward_for_Lumio_Phase_C_officially_launched).
- [ESA mission profile](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Technology_CubeSats/LUMIO), with schedule/configuration statements requiring comparison against dated updates.
- [ASI mission page](https://www.asi.it/en/technologies-and-engineering/micro-and-nanosatellites/esa-gstp-fly-program/lumio/), including its conflicting form-factor entry.
- [Politecnico Phase-C project record](https://www.aero.polimi.it/en/research-projects/esa-lumio-lunar-meteoroid-impacts-observer--phase-c).

Prefer mission authors, agencies, the prime and actual subsystem providers for claims within their authority. Distinguish manufacturer descriptions of a delivered/selected LUMIO unit from generic product capability. Record paywalls, missing full text and inaccessible sources; do not pretend abstract-only access verified a detailed table or design rationale. Preserve originals in `literature/`; cache new research copies separately with provenance.

## Files and reproducibility

Follow the two preceding research tasks' organization:

| Location | Content |
| --- | --- |
| `outputs/lumio_comparison_research_2026-10-29/README.md` | Actual status, result index, key conclusions, limitations and reproduction links. |
| `outputs/lumio_comparison_research_2026-10-29/lumio_comparison_research.md` | Main source-backed findings answering all questions, subsystem matrix, version conflicts, SMD comparison and conclusions. |
| `outputs/lumio_comparison_research_2026-10-29/lumio_comparison_research.xlsx` | Evidence register, version timeline/conflict log, objectives/criteria, orbit/duration rationale, subsystem values, comparison calculations and conclusions. Use live formulas for meaningful calculations. |
| `outputs/lumio_comparison_research_2026-10-29/lumio_mission_comparison_report.pdf` | Concise supporting report, readable source-backed tables and relevant figures; distinct from the final mission-design report. |
| `analysis/lumio_comparison_research/` | This brief and future reproduction guide; reviewed source records; calculation inputs/scripts; builders and validation. Follow existing simple naming conventions where useful. |
| `data/lumio_comparison/` | Source-labelled claims/specifications/criteria and machine-readable comparison data, with provenance README. Preserve original versus derived values. |
| `figures/lumio_comparison/` | Readable design-history/operations diagrams or supported scientific comparison plots, with source attribution and units. Distinguish original schematics from source illustrations. |
| `tmp/lumio_comparison_research/` | Downloaded research copies, extracted texts, source-access manifest, workbook previews and PDF renders. |

Use applicable spreadsheet/PDF skills and configured current-host runtimes. Document actual dependencies, exact commands, inputs, outputs and numerical checks here when implemented. Verify unit conversions, derived comparisons, evidence IDs and local links; inspect the workbook and render/review the exported report and figures. Do not claim a model or test was run unless it was.

Preserve existing dated outputs and the other research tasks' files. Retain stable D/R identifiers and the distinction between proposal constraints and proposed design decisions.

## Completion criteria

- All user questions answered with primary-source locations, or an explicit account of what the reviewed public sources do not establish.
- A documented mission-statement/criteria comparison, orbit and duration rationale, CubeSat/form-factor rationale, and reliable subsystem design table.
- Version-specific evidence and an explicit conflict log, especially for form factor, schedule, transfer/propulsion and payload changes.
- Quantitative comparisons/calculations where compatible inputs exist, with no unsupported claim of SMD superiority or flight-proven LUMIO performance.
- Clear concept-design lessons and added-value conclusions, reproducible source/data/calculation records, reviewed workbook/PDF and an updated result index.
