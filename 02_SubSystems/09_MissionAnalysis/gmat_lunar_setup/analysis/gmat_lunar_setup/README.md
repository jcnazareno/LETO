# GMAT lunar mission setup

Dependencies: the installed **GMAT R2026a** Linux distribution, its bundled DE421 ephemeris, lunar PA kernel and GRGM900C files, system Python 3.14, and the `gmat` / `gmat-console` launchers. The generator, runner and summary use only the Python standard library. No changes to the GMAT installation or existing mission studies are made.

User-facing files: [`outputs/`](../../outputs/README.md). The brief [`ASSUMPTIONS.md`](../../outputs/ASSUMPTIONS.md) and editable [`config.json`](config.json) identify the current scenario.

## Recorded and new runs

The [recorded delivery](../../outputs/README.md) has original GMAT scripts and manifests in `scripts/` and histories in `runs/`. Check the saved outputs without executing the scripts:

```bash
python3 analysis/gmat_lunar_setup/run_validation.py --suite all --inspect-only
```

For new runs, set `gmat_root` in [config.json](config.json) to your GMAT R2026a installation and ensure that `gmat-console` is on your PATH. Generate into an unused directory from this project root:

```bash
python3 analysis/gmat_lunar_setup/setup_mission.py --output tmp/gmat_lunar_setup/new_case
python3 analysis/gmat_lunar_setup/run_validation.py --folder tmp/gmat_lunar_setup/new_case --suite all --jobs 2
python3 analysis/gmat_lunar_setup/summarize.py --folder tmp/gmat_lunar_setup/new_case
```

The generator writes each new case's absolute report paths into its startup and mission files. The two full scripts request approximately three years of propagation. The recorded partial ideal-maintenance history reaches 7.375 days of monitoring.

## Modelling conventions

- Distances/velocities in GMAT: km and km/s; mass: kg; impulsive-burn components: km/s; reported cumulative delta-v: m/s. UTC is interpreted using the bundled leap-second tables; future leap seconds are not predicted.
- Gravity: fully normalized GRGM900C, matched DE421 lunar principal axes and GM; altitude: spherical 1738 km disturbance convention. `LunaICRF` is Moon-centred ICRF. Reported `LunarEquatorJ2000.INC` uses the Moon's **J2000** equator and therefore need not equal the initial instantaneous-PA polar inclination of 90°.
- Integrator targets use **absolute A1 modified Julian epochs**. The diagnostic elapsed-time parameters do not define repeated propagation durations.
- Monitoring/imaging durations exclude the coast to lowering apolune and the transfer coast. No spacecraft-state reset occurs between phases.
- The optional maintenance impulse removes radial velocity and sets circular speed at the current radius. In local VNB, +V is along velocity, +N along angular momentum, and +B = V×N. The two nonzero components are `Vcirc*Vt/Vmag - Vmag` and `-Vcirc*Vr/Vmag`. This does not restore the nominal orbital radius, node or inclination. Maintenance delta-v is summed from these impulses and is not inferred by integrating force magnitudes.
- Lowering is targeted from the actual end-of-monitoring state. Its two-body seed is not used as a substitute for achieved GMAT targets. The model uses ideal impulses and exact navigation/execution; finite-burn and operational control validation remain open.
- The phase-2 standalone test mass subtracts the ideal two-body lowering cost. The phase-transition test instead carries the actual propagated fuel from phase 1 through the solved burns.
- Hourly samples do not measure continuous minimum altitude. The 20 km radius guard is active during propagation, but does not include terrain. Natural drift or ideal control can still make a full reference mission fail; no mission feasibility statement is inferred from a generated file.

## Parse the full scripts without running them

```bash
LD_LIBRARY_PATH=/home/gordon/.local/opt/GMAT/R2026a/bin:/home/gordon/.local/opt/GMAT/R2026a/plugins:/home/gordon/.local/opt/GMAT/R2026a/lib:/home/gordon/.local/opt/GMAT/R2026a/lib/compat python analysis/gmat_lunar_setup/check_full_syntax.py "$PWD/tmp/gmat_lunar_setup/new_case" option_a_natural
```

Repeat with `option_a_ideal_stationkeeping`. The helper uses `gmatpy.LoadScript` and does not call `RunScript`.

No completed full mission, gravity-covariance clone ensemble, epoch/node sweep, radiometric performance, attitude-control simulation or coverage verification is claimed. Research provenance and remaining physical limits are in the output README.
