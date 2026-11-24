# Radiation-environment research for concept definition

Task created and concept study completed: **29 October 2026**. Status: **findings, workbook, seven-page PDF and calculations completed; mission-specific qualification gaps retained**. The commissioned brief below is preserved. [Finished results](../../outputs/radiation_environment_research_2026-10-29/README.md).

## Objective

Quantify the radiation environment relevant to the lunar impact-flash/event-camera concept, compare it directly with representative Earth-observation environments, and turn the evidence into clear concept-design conclusions. Establish what can be sized now, which component choices or mitigations are justified, and which uncertainties need later qualification. Complete the research rather than returning only a plan.

Follow the current educational scope in AGENTS.md in the mission reference. Keep the event camera central, retain entire-lunar-surface coverage, and do not add science objectives or silently select an orbit, lifetime, platform, or numerical requirement. Scope the work to useful concept/SRR decisions for a four-person team and a final mission report limited to 50 A4 pages.

## Read first

1. `AGENTS.md` and `Concept_Description.md` in the mission reference.
2. Design drivers in the mission reference, especially D01–D03, D05, D07–D09, and open questions, especially R8. AGENTS.md and later user instructions override stale unresolved-question wording.
3. Earth versus lunar observation report, especially radiation, detector artefacts, autonomy, and materials.
4. [D01–D04 results](../../outputs/d01_d04_research_2026-10-28/d01_d04_research.md), the associated workbook/PDF, and [analysis source records](../d01_d04_research/research_data.mjs). Conditional sensor examples and performance targets are not baselines.
5. The supplied mission, LUMIO, and event-camera references in `literature/`. 

## Required comparison and quantification

### Define the environments before comparing numbers

Use a small, explicit set of **illustrative comparison cases**, adjusting them if a better evidence-matched case is justified:

- Earth observation: a LEO case near **400 km / 51.6°** and a polar or Sun-synchronous EO case near **600 km / 98°**. These are comparison fixtures, not selected mission orbits. Briefly explain why their results cannot represent every Earth orbit; MEO/GEO may be mentioned as context without creating a separate full study.
- Lunar observation: a low polar lunar-orbit case near **100 km altitude**, and a distant lunar-observer/libration-region case relevant to the existing approximately **50,000 km** observation-range examples. Define altitude, centre distance, target range, and trajectory assumptions consistently; a range alone does not define a libration orbit or radiation exposure history.
- Transfer: treat Earth radiation-belt passage and any extended residence separately from the lunar operational phase. Do not turn a short crossing into a full year of belt exposure.
- Keep an Earth-surface comparison separate and optional. Human effective dose in Sv/mSv is not a substitute for absorbed dose in silicon, detector displacement damage, or a component upset rate.

State comparable durations, shielding geometry/material, solar conditions, confidence or percentile, model versions, and particle/energy definitions. Prefer a common **one-year** comparison, with **three-year** scaling or sensitivity where justified; these are research assumptions. Examine representative shielding, for example **1, 2, 3, and 5 mm aluminium equivalent**, where source/model coverage supports it. Report unsupported combinations as gaps, rather than filling a complete-looking table with invented numbers. Distinguish simple planar/spherical shielding calculations from the actual spacecraft geometry and optical aperture.

### Separate the physical effects

- Galactic cosmic rays: quiet-background spectra or fluxes and solar-cycle dependence.
- Solar energetic particles: event and cumulative fluence, uncertainty/confidence, and credible design-event treatment. Separate average background from episodic solar events.
- Trapped electrons/protons: relevant Earth-orbit and transfer exposure; do not assume a lunar trapped-belt analogue.
- Geometrical shielding by Earth or Moon, plus secondary particles/lunar albedo where consequential. Do not apply a universal hemispherical reduction factor to all trajectories and effects.
- Total ionizing dose **TID**, using a defined material such as **rad(Si)/krad(Si)** and duration/shielding.
- Displacement damage, with a defined dose or equivalent-fluence convention and material/reference energy.
- Single-event effects **SEE**: distinguish upsets/transients/functional interruptions from latch-up and other destructive effects. Include LET spectra when relevant and available.
- Plasma/surface or internal charging: discuss separately from dose and energetic-particle SEE, with quantitative inputs where applicable evidence exists.

Provide side-by-side values or defensible bounds, absolute units, and lunar/LEO ratios **only for genuinely comparable cases**. Record flux versus fluence, differential versus integral spectra, angular conventions, energy thresholds, and uncertainty. Explain mechanisms behind differences; avoid a single unsupported statement that lunar radiation is a fixed multiple of Earth radiation.

## Translate the environment into this concept

1. **Payload:** assess event-sensor TID/displacement-damage sensitivity, hot pixels/dark activity, contrast/latency/bandwidth or calibration drift, particle-induced transient candidates, and possible loss of useful light-curve data. Check IMX636 and other actually relevant sensor evidence without treating a prior simulator profile as a selected or space-qualified detector. Separate sensor, readout, FPGA/SoC, and development-kit evidence.
2. **Detector artefacts:** where the evidence permits, estimate particle-hit/candidate rates from a stated spectrum/flux, sensitive area, angular response, shielding, and detector response. A particle crossing is not automatically an event-camera output, and one affected pixel is not necessarily one false confirmed flash. If response evidence is missing, provide bounded screening calculations and identify the unknown conversion factors.
3. **Avionics and power:** assess candidate component classes for processing, memory, storage, power switching/conversion, and solar-array degradation where material. Distinguish radiation hardness from generic flight heritage, and commercial parts from qualified assemblies.
4. **Protection:** evaluate targeted versus whole-spacecraft shielding, mass/area implications, optical-aperture exposure, ECC/scrubbing, watchdog/reset recovery, latch-up protection, redundancy where justified, and solar-event operating modes. Explain what shielding cannot establish by itself.
5. **Reliability and science:** where device cross-sections exist, calculate SEE rates using compatible spectra and cross-sections, and translate rates into interruption/loss probabilities. If cross-sections are absent, do not invent a qualified rate. Show how downtime, false events, degradation, and mitigation affect D01–D03, D05, D07–D09 and the selected primary observable.
6. **Decisions:** finish with an evidence-linked conclusion table: proposed concept decision or design allowance; quantitative basis; confidence/status; subsystem consequences; and what would change the conclusion. Identify implications for architecture/lifetime and any genuine feasibility risk. Retain TBR items when evidence is insufficient; do not call every issue unresolved if a defensible concept decision is possible.

A useful conclusion must say what the team should do about the evidence. Separate supported necessities, conservative study assumptions, optional measures, and qualification still needed. Preserve the educational allowance for literature/first-principles payload evidence; do not make new hardware irradiation experiments a prerequisite for completing this concept study.

## Evidence, modelling, and reproducibility

Browse current primary literature, agency mission/environment documentation, original model documentation, radiation-test reports, and manufacturer evidence. Start with relevant lunar measurements (for example LRO/CRaTER and applicable lunar particle measurements), accepted environment models, and actual device studies. Check scope and current versions instead of relying on source names alone.

Trace every consequential value to URL/DOI, publication/version, page/table/figure, units, geometry, shielding, solar state, duration/confidence, and access status. Label **measured**, **published model result**, **this study's calculation**, **design assumption**, **proposed allocation**, and **unknown device behaviour** separately. Do not transfer human dose or a different semiconductor technology's test result directly to the selected hardware.

Use reproducible calculations for unit conversions, matched-case comparisons, shield mass, and rate/probability estimates. For environment/transport tools, record actual inputs, versions, outputs, and execution status. If a tool requires unavailable accounts/data or cannot run locally, use applicable published calculations or bounded estimates and disclose the limitation. Never imply SPENVIS, OMERE, transport simulation, or irradiation tests were run when they were not. Do not stop the entire study solely because one service or source is inaccessible.

Record dependencies, exact current-host commands, input/output files, numerical checks, and limitations here when the implementation exists. Historical Windows runtime paths are not current Linux execution commands. Validate units, duration scaling and its limitations, rate integrations where used, and workbook results against independent calculations. Use applicable spreadsheet/PDF skills and render exported figures/reports for visual review.

## File organization and expected deliverables

Follow the existing separation of results, code, data, plots, and temporary files. Paths below are relative to the SMD root.

| Location | Content |
| --- | --- |
| `outputs/radiation_environment_research_2026-10-29/README.md` | Deliverable index, status, scope, and reproduction links. Update after the research. |
| `outputs/radiation_environment_research_2026-10-29/radiation_environment_research.md` | Main research findings, matched comparison, clear concept conclusions, assumptions, limitations, and linked evidence. |
| `outputs/radiation_environment_research_2026-10-29/radiation_environment_research.xlsx` | Inspectable evidence, cases/inputs, comparison quantities, calculations, component evidence, conclusions, and open items. Use live formulas where meaningful. |
| `outputs/radiation_environment_research_2026-10-29/lunar_radiation_environment_report.pdf` | Concise supporting report with readable comparison tables, relevant plots, and conclusions suitable for concept/SRR use. This is not the final mission report. |
| `analysis/radiation_environment_research/` | This README, reviewed evidence/source records, calculation inputs and scripts, builders, and validation results. Use existing naming conventions such as `research_data.mjs`, `model_inputs.json`, `model_results.json`, `calculate.py`, `build_workbook.mjs`, and `build_report.py` where appropriate. Avoid an unnecessary framework. |
| `data/radiation_environment/` | Source-labelled machine-readable environment/comparison data and provenance README. Preserve original versus derived values. |
| `figures/radiation_environment/` | Standalone scientific plots, with explicit units, cases, uncertainty and source attribution; PNG/PDF as useful. Plot only supported comparisons. |
| `tmp/radiation_environment_research/` | Downloaded research copies, extracted source text, model caches, workbook previews, PDF renders and other intermediates. |

Preserve supplied documents in `literature/` and prior dated research outputs. Keep download caches and build intermediates out of the results folder. Use relative links in project Markdown and check them after generation.

Retain stable D/R identifiers and clearly mark provisional design decisions. Do not rewrite the proposal, broaden the science objective, or overwrite historical workbooks.

## Completion criteria

- At least one defensible numerical lunar-versus-LEO comparison for the same stated metric, shielding, duration, solar conditions, and uncertainty; explain remaining case coverage and avoid false equivalence.
- Quantified cumulative and single-event concerns where evidence supports them, with explicit separation of environment knowledge from detector/component tolerance.
- Clear payload, electronics, protection, availability, and concept-feasibility conclusions with traceable numerical bases or explicitly bounded unknowns.
- Reproducible calculations/data, reviewed workbook and PDF, meaningful scientific plots, and an updated deliverable index with limitations and verification status.
- A short report-ready conclusions summary and proportionate next steps for the SRR/full concept.

## Implemented calculations and reproduction

Executed 29 October 2026 on Linux. No SPENVIS, IRENE, OMERE, CREME, FASTRAD, Geant4 or irradiation was run. The quantitative dose comparison uses NASA/TM-20250006822 Fig 10, digitized from its original embedded raster. Original 400 km/51.6° and 600 km/98° cases remain gaps; published 550 km/6° and 800 km/98° cases supply matching Si/Al-sphere/solar-maximum/source-95% comparisons.

Files: `model_inputs.json` (assumptions and raster axes/colors), `research_data.json` / `.mjs` (reviewed sources, cases, decisions), `calculate.py` (standard-library/Pillow arithmetic and digitization), `plot_results.py` (scientific plots), `build_findings.py`, `build_workbook.mjs`, `build_report.py`, and `validate_outputs.py`. Outputs are under the prescribed results/data/figure/cache directories. Validation records are `calculation_validation.json`, `workbook_validation.json` and `validation_results.json`.

Bundled runtime paths were obtained from Codex `load_workspace_dependencies`, version 26.1025.11240. Python 3.12.14 includes NumPy 2.3.5, Pillow 12.3.0, ReportLab 4.4.9, pdfplumber 0.11.9 and pypdf 6.10.0. Bundled Node and `@oai/artifact-tool` author the workbook. Bundled Python lacks Matplotlib; plots use the existing system Python 3.14.8, NumPy 2.5.4 and Matplotlib 3.11.2 only. No dependency directory was modified. The local `node_modules` symlink points to bundled packages and is not a distributable dependency copy.

From the SMD root, after source cache/raster extraction:

```bash
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/radiation_environment_research/calculate.py
MPLCONFIGDIR=/tmp/smd-radiation-matplotlib python3 analysis/radiation_environment_research/plot_results.py
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/radiation_environment_research/build_findings.py
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node analysis/radiation_environment_research/build_workbook.mjs
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/radiation_environment_research/build_report.py
pdftoppm -r 100 -png outputs/radiation_environment_research_2026-10-29/lunar_radiation_environment_report.pdf tmp/radiation_environment_research/report_renders/page
/home/gordon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 analysis/radiation_environment_research/validate_outputs.py
```

The builder overwrites only this study's deliverables. Source PDFs are cached from public URLs in the evidence register. [Dataset provenance](../../data/radiation_environment/README.md) gives `pdfimages` commands and pixel-axis conventions. `tmp/radiation_environment_research/source_cache_manifest.json` records cache sizes and SHA256. Full downloads succeeded for NASA2025, ISS2025, neutronEVS2021, IMX636, TI, RTG4 and charging 2020 PDFs. McMahon author text was read via web; PDF download 403. PREDICCS publisher PDF/HTML403; no numerical value used from it. The direct unprivileged download initially failed due to sandbox DNS; public downloads succeeded through approved network execution.

Numerical checks cover dimensional conversions, IMX636 area, occultation limits, NASA's printed 2.17 krad lunar-surface point, ratio reading ranges and availability. Workbook checks include transfer 1→2→1 propagation, zero-loss availability, independent expected values, formula-error inspection and saved-cache verification; native Excel was not tested. Seven PDF pages and every workbook sheet were rendered and reviewed. Plot captions were spaced after visual QA. Local links were checked within this study and the shared notes updated by it. Main unknowns remain exact trajectory/shield paths, mission DD, selected-device SEE rates, particle-to-confirmed-flash response, solar-array degradation and actual downtime/charging.
