# LUMIO mission comparison research

Completed **29 October 2026** as a concept comparison. No SMD architecture or numerical requirement is baselined.

This study establishes LUMIO's mission statement and published criteria, orbit, duration and CubeSat rationale, satellite design, unresolved source conflicts and implications for SMD.

The retained brief, actual methods, current-host commands and handoff are in [the analysis README](../../analysis/lumio_comparison_research/README.md). Values retain their epoch and evidence status.

## Finished results

- [Research findings](lumio_comparison_research.md): mission rationale, subsystem details, source conflicts, D01-D10 comparison and conclusions.
- [Evidence and calculation workbook](lumio_comparison_research.xlsx): seven sheets, 19 primary sources, 43 claims, 16 criteria/gap rows, 12 timeline entries, 13 conflicts and live calculations.
- Ten-page A4 supporting report: concise review and scientific plots, separate from the final 50-page mission report.
- [Data/provenance](../../data/lumio_comparison/README.md), [four PNG/PDF figure pairs](../../figures/lumio_comparison/README.md), [validation record](../../analysis/lumio_comparison_research/validation.json).

## Consequential findings

- LUMIO combines science and small-spacecraft demonstration. Its 2018 orbit trade publishes at least 240 detections, including 100 lower-energy and two higher-energy impacts, plus a one-year minimum life. These are historical criteria, not verified current Phase-C thresholds.
- A maintained Earth-Moon L2 quasi-halo gives farside full-disc access. It does not establish SMD whole-surface exposure. The 2024 WSB budget sums 79.05 m/s for its particular release/error/margin assumptions.
- One nominal operational year alternates science and engineering cycles. Ideal half-cycle science allowance is 182.625 days / 4383 hours before extra losses. A documented optimization explaining exactly one year was not found.
- CubeSat origin is the ESA LUCE programme, miniaturization and piggyback demonstration. SMD is not constrained to 12U. No comparable total lifecycle cost was established.
- October 2024 payload design gives 50.8 mm pupil, 127 mm focal length, 6 deg field, two CCD201-20 EMCCDs, VIS 450-800 / NIR 850-950 nm and about 78 ms minimum full-frame integration. This differs from the older 66 ms / 15 fps and 820 nm-split model.
- Dated status: March 2026 Phase C, CDR planned 2027, potential launch 2028. ESA/prime 12U/12UXL conflicts with ASI 16U; no confirmed redesign explanation.
- Calibrated early-to-total flash energy is a focused SMD hypothesis, not demonstrated capability. Modern ground observations already have 4-5 ms cadence. Fine timestamps or farside access alone do not establish added value.

Exact primary-source locations and limits are retained in the findings/workbook. The predicted 37000 annual detections are model dependent and differ from useful early-flash samples. Public budget discrepancies remain visible.

## Verification and limits

Executed analytic geometry, ideal bin-phase integration, rough exposure scaling, sample/data-volume calculations and source arithmetic. Workbook formulas were recalculated, perturbed/restored and checked independently in the saved XLSX. The PDF was reopened, rendered and visually reviewed; all worksheets and figures received representative visual checks. Source IDs, CSV/JSON consistency, original supplied-PDF hashes and local links were checked.

No new trajectory propagation, LUMIO yield Monte Carlo, calibrated selected-sensor model, irradiation/hardware qualification or native Excel session was run. Several Polimi PDF downloads returned HTTP403; indexed primary PDF text was reviewed with access/visual limits recorded. Controlled current configuration, performance/false-rate curves, final launch/transfer, closed mode budgets, ground commitments, total cost and approved extension remain public gaps.

## Next concept step

Select one primary observable and uncertainty target; compare realistic event-sensor/optics cases and minimum radiometric support; couple whole-surface exposure with joint D01-D04 recovery and useful yield; close mode/resource interfaces. Use the radiation and disturbance studies where applicable. Trial 100 useful events for 10% mean precision assumes CV=1 and is not a requirement. Preserve both hemispheres, polar coverage, the educational evidence standard and the inclusive 50-page report budget.

## Project organization

- Code, inputs and validation: `analysis/lumio_comparison_research/`.
- Source-labelled data: `data/lumio_comparison/`.
- Figures: `figures/lumio_comparison/`.
- Source caches, extracts and previews: `tmp/lumio_comparison_research/`.

Earlier research outputs and supplied documents are preserved.
