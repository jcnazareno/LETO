# Disturbance study data and provenance

Produced 29 October 2026. Values are conditional study fixtures, actual local model outputs, or explicitly identified analytical estimates. None are selected mission requirements.

| File / family | Provenance and meaning |
| --- | --- |
| `nrlmsis_density_profiles.csv` | **Actual NRLMSIS2.0 runs**, pymsis0.13.0, DE07. Each row is a profile altitude for one 400/600 km case and quiet/moderate/active proxy state. Density columns are min/mean/max over 96 first-orbit positions/times. Daily and 81-day F10.7 [sfu] and daily ap are separate columns. |
| `LEO*.csv` | **Actual averaged ODE integrations** of circular mean altitude and J2 node change. Earth corotation included in drag power. Fixed first-orbit density profiles; no seasonal/weather timeline or full Cartesian short-period elements. Stop at365days or120km validity boundary. |
| `Moon*.csv` | **Actual Cartesian propagation** with GRGM1200A truncated harmonics, geometric DE440s Sun/Earth and direct shadowed SRP. Columns: elapsed day; osculating a/e; hp/ha above1738km; inclination/node/argument relative to epoch PA inertial axes; instantaneous radial height. Circular argument of periapsis is singular and must not be interpreted initially. |
| `Moon*.npz` | Matching time in seconds, Moon-centred J2000 state in metres/metres per second, and the same metric array as CSV. Includes the actual initial state. |
| `Moon*_summary.json` | Force norm RMS/sampled maxima, extrema, integrations and stop descriptions. Force samples1h; state metrics600s. Extrema are sampled, not exact continuous maxima. Moon50_N80 ends at an actual11km radial buffer crossing, **not a local terrain impact**. Other lunar histories end at30days. |
| `halo_nominal_and_drift.csv` | **Actual CRTBP propagation** from the retrieved JPL state DE08. Normalized barycentric rotating state and a1km x,+0.01m/s vy initial-error case. Range/deviation in km. No calendar ephemeris trajectory, Sun or SRP. |
| `halo_targeted.csv` | Ideal7-day impulses targeting reference position14days downstream, exact navigation/execution. A single initial-error demonstration, **not annual stationkeeping prediction**. |
| `distant_case.json` | Exact JPL initial state, units, source, correction impulses, closure/invariant checks, departure and stability metrics. |
| `momentum_*.csv` | Analytical fixed-inertial-axis periodic gravity-gradient torque plus30nNm bias, sampled60s. The distant case uses a circular surrogate solely to illustrate cancellation, **not a halo momentum history**. |
| `pointing_PD_example.csv` | Actual scalar rigid-body controller integration:0.02Hz natural frequency,0.7 damping,0.5kgm²,30nNm bias. No sensor/structural noise; not a pointing or jitter qualification. |
| `analytical_bounds.json` | Independent force/torque, aerodynamic, momentum/unloading, wheel-imbalance, conditional secondary-effect and optical-motion calculations. Distinguishes assumed screening inputs from measured component evidence. |
| `case_results.json` | Consolidated derived results used by the workbook and report. Not a raw observation catalogue. |

Epoch for Earth/low lunar cases:2026-10-29 00:00UTC. Lunar radii above1738km, Earth above6378.137km. GRGM1200A specifies DE430 PA; propagation uses available DE421 PA orientation as an approximation, with0.01deg sensitivity. The halo is autonomous CRTBP and has no unique calendar realization. See [the analysis README](../../analysis/disturbance_environment_research/README.md) for exact commands, checks, fidelity and source hashes, and [the findings](../../outputs/disturbance_environment_research_2026-10-29/disturbance_environment_research.md) for interpretation.

Source values: [evidence register](../../analysis/disturbance_environment_research/evidence.json), source/model downloads and SHA256 hashes under `tmp/disturbance_environment_research/sources/manifest.json`. Original external files are cached separately from these derived tables. No supplied literature PDFs were altered.
