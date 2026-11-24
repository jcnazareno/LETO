# Orbit and attitude disturbance research

Completed **29 October 2026** as a quantitative concept study. Assumptions, published comparators, actual local model outputs and unresolved flight performance remain distinct; no mission architecture or D01-D10 threshold is approved.

This study quantifies orbital evolution/decay and attitude disturbances for lunar observation, compares them with representative Earth-observation cases, and derives propulsion, ADCS, pointing, availability and lifetime consequences.

The retained brief, actual methods, exact current-host commands and handoff are in [the analysis README](../../analysis/disturbance_environment_research/README.md).

## Deliverables

- [Research findings](disturbance_environment_research.md): quantified comparisons, evidence, limitations and provisional concept decisions.
- [Calculation/evidence workbook](disturbance_environment_research.xlsx): eight sheets, editable analytical inputs and live formulas, propagated snapshots, source register and checks.
- Ten-page supporting PDF: concise A4 comparison and scientific plots. Supporting research, not the final 50-page mission report.
- [Data provenance/time histories](../../data/disturbance_environment/README.md), [scientific plots](../../figures/disturbance_environment/), [evidence register](../../analysis/disturbance_environment_research/evidence.json), [validation record](../../analysis/disturbance_environment_research/validation.json).

## Consequential numerical findings

| Comparison | Conditional result | Design consequence |
| --- | --- | --- |
| Matched 30 kg, 0.30 m² spacecraft in Earth LEO | NRLMSIS quiet-to-active fixtures lose 2.2–45.2 km in 30 days at 400 km; 0.062–2.962 km at 600 km | Atmospheric state, altitude and area/mass strongly change drag. Fixed proxy states are not a weather forecast. |
| Initial 100 km circular polar lunar case | Minimum osculating periapsis 77.3 km over 30 days; sampled semimajor-axis span 1.79 km | Conservative orbit-shape changes dominate; 30-day survival is not a lifetime or zero-maintenance proof. |
| Initial 50 km circular polar lunar case | Actual radial crossing of an assumed 11 km screening buffer near day 48 | Conditional hazard screen, not a local terrain impact or universal lunar decay rate. Boundary time not converged at degree 120. |
| Matched gravity-gradient torque | Moon100 / LEO400 = 0.617; lunar arbitrary-attitude peak 3.55×10⁻⁷ N·m | Close-lunar gravity-gradient torque remains substantial; alignment changes it. |
| Aerodynamic torque, 2 cm arm | Quiet/moderate/active 400 km: 0.283/1.44/4.37 µN·m; 600 km: 0.0078/0.0739/0.366 µN·m | LEO drag can dominate; these are mean-density scalar estimates, not vector/RMS histories. |
| Defined JPL near-C=3.09 halo | 42,056–83,121 km lunar range; 14.455-day period; local e-folding time 2.48 days | Navigation and an explicit maintenance policy are necessary; distance alone does not define stability. |
| Secular momentum sensitivity | 30 nN·m fills 0.025 N·m·s in 9.65 days; balanced 15 cm couple needs 6.31 N·s/year, about 8 g at 80 s Isp | Pressure-centre alignment, usable wheel storage and external unloading matter; torque magnitude does not establish jitter. |

Published LRO flight operations contrast about **143 m/s/year** in its 50±15 km science envelope with **less than 5 m/s/year** after transition to frozen geometry. Published LUMIO design results support a **provisional 16–30 m/s/year L2 stationkeeping sensitivity**, pending a dated trajectory/navigation/control design. These are orbit-specific comparators, not SMD allocations; see DE05/DE09/DE11 and page locations in the evidence register.

## Actual execution and checks

- NRLMSIS2.0 evaluations and averaged Earth drag/J2-node ODEs to one year or the 120 km validity boundary.
- Nine lunar Cartesian propagation variants with GRGM1200A degrees40/80/120, DE440s Sun/Earth and explicitly approximate DE421 PA orientation.
- Actual JPL-catalogue CRTBP reference/error propagation, ideal weekly targeting and stability/invariant checks.
- Analytical forces/torques, aerodynamic estimates, momentum/unloading, component imbalance and image motion; scalar PD response integration.
- Independent J2, potential-gradient and two-body checks; gravity/integration/orientation sensitivity; workbook recalculation/input perturbation/error scan and numerical cross-checks; all eight sheets, six plot topics and ten PDF pages visually reviewed; PDF reopened and local Markdown links checked.

At 100 km, degree80→120 changes day-30 periapsis by 22 m and tighter integration changes it by 2.5 m. At 50 km, degree80→120 changes it by 0.283 km. No local DEM impact, operational lifetime certification, gravity-clone ensemble, structural/controller jitter qualification or calibrated event-sensor test is claimed. The ideal halo correction cost is not an annual propellant prediction. Some university/manufacturer downloads failed; access limits are recorded.

## Next design step

Select the primary observable, then compare favourable low-lunar geometry with a maintained distant observer through **whole-surface usable exposure and characterized samples**, including both hemispheres and poles. Build one dated maintained trajectory with navigation/execution errors, CAD inertia/plate geometry, wheel/thruster-array sizing and an integrated science-availability/knowledge/jitter budget before baselining requirements.

## Project organization

- Code, inputs and validation: `analysis/disturbance_environment_research/`.
- Source-labelled data and time histories: `data/disturbance_environment/`.
- Scientific plots: `figures/disturbance_environment/`.
- Source/model caches and previews: `tmp/disturbance_environment_research/`.

The previous dated outputs and parallel radiation/LUMIO studies are preserved.
