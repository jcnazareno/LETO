# Radiation-environment research

Completed **29 October 2026** as a concept/SRR evidence study. Numerical requirements, orbit, life, shielding and components remain unselected.

At 2.54 mm Al, matched published solar-maximum/source-95% Si doses are about **4.3 krad/year for the distant-lunar interplanetary proxy**, **2.6 for 550 km/6° LEO**, and **5.5 for 800 km/98° LEO**, with a separate±15% reading allowance. A universal lunar/LEO multiplier is unsupported. Original 400 km/51.6° and 600 km/98° cases remain explicit gaps.

Three-year scaling plus an **assumed 1 krad transfer allowance** and **factor-two margin** suggests a provisional **30 krad electronics screening class** behind 2.54 mm Al. Trade local 2–3 mm protection against mass:3 mm costs 8.1 kg/m² or 0.516 kg around a 10 cm internal cube. The 30 krad class uses the central reading; preserving the same margin at the +15% reading requires 31.3 krad, so compare 50 krad parts. These are assumptions, not requirements. Existing event-camera evidence supports conditional feasibility; IMX636-specific degradation, selected-chain SEE and particle-to-confirmed-false response remain unqualified.

## Finished results

- [Main findings and decisions](radiation_environment_research.md): comparisons, dose/shield trades, payload, electronics, charging and driver implications.
- [Evidence and calculation workbook](radiation_environment_research.xlsx): seven sheets, live formulas,18 source/access records, ten decisions and eight open items.
- Seven-page A4 report: supporting research; it does not enlarge the final 50-page mission report budget.
- [Scientific figures](../../figures/radiation_environment/): five PNG/PDF pairs.
- [Data provenance](../../data/radiation_environment/README.md), [reproduction instructions](../../analysis/radiation_environment_research/README.md), [validation record](../../analysis/radiation_environment_research/validation_results.json).

## Verification and limits

Arithmetic/dimensional checks, workbook recalculation/input changes, formula-cache checks, local-link checks and visual review of all sheets/seven PDF pages passed. Native Excel was not tested. No SPENVIS, IRENE, CREME, FASTRAD, OMERE or Geant4 run, selected-sensor simulation, irradiation or complete-spacecraft reliability demonstration was performed. Complete source-model inputs are unavailable. McMahon author text was read but PDF download 403; PREDICCS publisher 403 and excluded numerically. New irradiation is not an educational completion gate.

## Project organization

- Reproducible code and inputs: `analysis/radiation_environment_research/`.
- Source-labelled datasets: `data/radiation_environment/`.
- Scientific plots: `figures/radiation_environment/`.
- Source caches and previews: `tmp/radiation_environment_research/`.

