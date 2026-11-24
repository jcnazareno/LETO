# LUMIO comparison data

Reviewed on 29 October 2026. The source register, claims, requirements, timeline, conflicts, D01-D10 comparison and decisions are generated from [the curated input](../../analysis/lumio_comparison_research/research_data.py). The JSON preserves numeric versus textual values; CSV files are flat interchange copies.

- `sources.csv`: 19 reviewed primary sources. Source IDs are stable and need not be consecutive; L09-L11/L16 were investigated leads with incomplete local access, not adopted as essential evidence.
- `claims.csv`: 43 claims with subsystem/area, value, units, conditions, configuration epoch, evidence status, source/location, confidence and public gap.
- `criteria.csv`: 16 rows separating historical orbit acceptance, published system requirements and current public gaps.
- `timeline.csv`, `conflicts.csv`: 12 timeline entries and 13 configuration conflicts.
- `comparison.csv`, `decisions.csv`: D01-D10 implications and seven concept recommendations.
- `geometry.csv`, `exposure.csv`, `temporal.csv`, `statistics.csv`, `calculation_results.json`: this study's calculations, produced by [calculate.py](../../analysis/lumio_comparison_research/calculate.py) from [explicit inputs](../../analysis/lumio_comparison_research/model_inputs.json).

Dates, ranges, response, margins and detection conventions belong to their source epoch. A requirement, design value, published simulation and observed result are different evidence classes. No flight-qualified current LUMIO or calibrated SMD specification is implied. See [the findings](../../outputs/lumio_comparison_research_2026-10-29/lumio_comparison_research.md) and the source-access entries in the curated input. The historical `tmp/lumio_comparison_research/source_access_manifest.json` is absent as checked on 5 November 2026; it was not recreated or revalidated.

Derived conventions: spherical Moon radius 1737.4 km; Moon-centre distance distinguished from nadir range; 365.25-day year and 29.53059-day synodic month for conversions; decimal bit/byte prefixes. Exposure is rough source scaling, not a spatial map or completeness calculation. Bin integration is analytic and noise-free, with a deliberately assumed exponential light curve. Sample sizing uses explicit trial variance and independent-sample approximations.
