# GMAT lunar mission setup — 5 November 2026

**Option A setup and short-run verification.** Start with the brief [assumptions overview](ASSUMPTIONS.md).

**Documentation status, 11 November 2026 (Europe/Berlin):** generated inputs and summary JSON are now in `scripts/`, with histories in `runs/`. Numerical results below retain their 5 November evidence date. The existing ideal-maintenance full-mission history stops at 7.375 d of monitoring; no completed full-mission propagation is recorded. See [methods and current reproduction limits](../analysis/gmat_lunar_setup/README.md#recorded-and-new-runs) before running commands.

## Main files

| File | Purpose |
|---|---|
| [Natural-drift mission](scripts/option_a_natural.script) | 2.5-year monitoring, targeted lowering, six-month imaging; no maintenance |
| [Idealized maintenance mission](scripts/option_a_ideal_stationkeeping.script) | Same sequence, with explicit threshold-based circularization and Δv/fuel accounting |
| [Lowering validation](scripts/validation_transfer.script) | Two days monitoring, coast to apolune, solved lowering, two days imaging |
| [High-orbit validation](scripts/validation_high_30d.script) / [low-orbit validation](scripts/validation_low_30d.script) | Independent 30-day natural-drift cases |
| [Generator and methods](../analysis/gmat_lunar_setup/README.md) | Editable configuration, dependencies and reproduction commands |
| [Validation results](scripts/validation_all.json) / [sensitivity results](scripts/sensitivity_results.json) | Machine-readable checks and comparisons |
| [Analytical screens](scripts/analytical_screens.json) | Separate torque estimates and omitted lunar-radiation force screens |

The saved scripts and startup files preserve their delivery paths and hashes. Use the [generator and validation commands](../analysis/gmat_lunar_setup/README.md#recorded-and-new-runs) to run a fresh copy from this project. The full scripts request approximately three years of propagation.

## Executed verification

All **15 short cases** completed successfully in the installed GMAT console and passed the saved-output checks. The full mission scripts share the tested force model and sequence construction; their complete trajectories remain unverified. Both main scripts also passed a separate [GMAT API parse-only check](scripts/syntax_validation.json).

| Check | Recorded result |
|---|---|
| 3000 km natural drift, 30 d | Minimum **sampled** radius altitude 2996.65 km; maximum osculating eccentricity 0.000665 |
| 300 km natural drift, 30 d | Minimum **sampled** radius altitude 289.00 km; maximum osculating eccentricity 0.005545 |
| Compressed phase transition | Both targets converged; impulses **228.159 + 283.189 = 511.348 m/s**; final mass 128.887 kg, including 10.787 kg fuel |
| Artificial controller exercise, 3 d | Two corrections, 0.1943 m/s total; circularization and rocket-equation mass checks passed; not a nominal maintenance prediction |
| Low orbit, gravity 40→80 / 80→120 | Seven-day endpoint position differences **0.868 m / 0.0020 m** |
| Low orbit, tighter integration | 30 s maximum step and accuracy 10⁻¹²: seven-day endpoint difference **0.00014 m** from the nominal numerical settings |
| SRP low/high versus nominal | Seven-day endpoint position differences **12.93 / 24.25 m** at 3000 km; **3.85 / 7.21 m** at 300 km |

At 3000 km the tested gravity truncations produced identical reported endpoint values; this is not proof that omitted harmonics have zero effect. Truncation and integration comparisons check this scenario over seven days, not gravity-field uncertainty or three-year convergence. Histories in `runs/` are available as raw GMAT reports and CSV files with units. The periapsis/apoapsis columns are osculating two-body diagnostics, not terrain-clearance predictions. Reported inclination is relative to the J2000 lunar equator; initial polar orientation is separately checked against the instantaneous DE421 principal axis.

## Force-model basis and research

The propagated model includes lunar spherical harmonics and solid tides, third-body differential gravity, direct cannonball SRP with lunar and terrestrial occultation, and GMAT's relativistic correction. It omits atmospheric drag. The initial state is circular and polar relative to the Moon at the selected epoch, rather than assigning 90° in an Earth-equatorial frame.

| Primary source, checked 5 Nov 2026 | Application / limit |
|---|---|
| [PDS GRGM900C label, description](https://pds-geosciences.wustl.edu/grail/grail-l-lgrs-5-rdr-v1/grail_1001/shadr/gggrx_0900c_sha.lbl) | Matched μ, radius, full normalization, **DE421 PA** frame and k₂. The installed coefficient file is truncated at 360×360; the setup uses 80×80. |
| [Mastroianni et al., 2025, §§2, 4–5](https://arxiv.org/html/2505.09241v1) | Contemporary lunar dynamics at approximately 300–3000 km: nonspherical gravity, Earth's perturbation, initial geometry and secular resonances matter. Their analytical-model accuracy is not transferred to this GMAT setup. |
| [Mesarch, 2023, LRO long-term orbit operations](https://ntrs.nasa.gov/citations/20230010952) | Distinguishes maintained, frozen and drifting operation; motivates explicit control policy and eclipse considerations. No LRO maintenance rate is assigned to this spacecraft. |
| [NASA/GSFC GRGM1200A](https://pgda.gsfc.nasa.gov/products/50) and [GRGM1200B/1200L archive context](https://pds.nasa.gov/ds-view/pds/viewProfile.jsp?dsid=GRAIL-L-LGRS-5-RDR-V1.0) | Higher-resolution models exist, but the newer fields use DE430. They are not silently substituted into the installed DE421 orientation model. Short altitude-specific convergence is used for this initial setup. |
| [GMAT source: lunar orientation](https://github.com/nasa/GMAT/blob/main/src/base/solarsys/Moon.cpp) and [SRP](https://github.com/nasa/GMAT/blob/main/src/base/forcemodel/SolarRadiationPressure.cpp) | Defaults, extra shadow-body handling and the built-in shadow implementation; script compatibility was checked against the actual installed R2026a binary. |
| [Bertone et al., 2021, §2.2](https://doi.org/10.1029/2020EA001454) | Precision GRAIL orbit determination includes lunar albedo/IR and spacecraft geometry. Those forces cannot be declared absent or negligible merely because this GMAT setup lacks them. |
| [Diviner science team: lunar thermal environment](https://www.diviner.ucla.edu/science) | Motivates a separate illustrative hot-disk radiation screen. A uniform 400 K disk is an assumption, not a measured orbital radiance history or an absolute temperature maximum. |

The analytical screens use ΔI = 10 kg·m² and a 2 cm pressure-centre offset. Their arbitrary-attitude gravity-gradient envelopes are 6.91×10⁻⁷ N·m at 3000 km and 8.69×10⁻⁶ N·m at 300 km. They are **not** attitude propagation, achieved pointing, wheel sizing or simultaneous disturbance peaks.

The uniform 400 K lunar-disk screen gives an omitted IR acceleration of approximately **6.6×10⁻⁸ m/s² at 300 km**, comparable to the nominal sunlit direct-SRP acceleration in that case. It is deliberately separate from the propagated model. A surface-resolved lunar radiation model and spacecraft plate properties are needed before precision orbit/pointing claims; the present setup does not justify neglecting them at that accuracy.

## Evidence limits

The launch/capture state, initial plane orientation, optical properties, inertia and pressure-centre offset remain assumptions. Capture expenditure only sets the initial science mass. Lowering and maintenance use exact-state ideal impulses; finite thrust, navigation/execution errors and realistic operational control are absent. No clone-field ensemble, launch/arrival design, epoch/node sensitivity, actual spacecraft attitude dynamics, lunar topographic occultation, radiation-damage or coverage analysis was performed here. This setup does not close any TBR requirement or establish a maintenance allocation.

Inputs and their SHA-256 hashes are preserved in [model provenance](scripts/model_provenance.json) and each case manifest. Full source/configuration and generated-script hashes are listed in [deliverable hashes](scripts/deliverable_sha256.json). These are recorded hashes from delivery; their original paths predate the move into `scripts/`.
