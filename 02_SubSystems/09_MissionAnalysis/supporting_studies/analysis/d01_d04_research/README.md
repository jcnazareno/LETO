# D01–D04 research reproduction

Review snapshot: **28 October 2026, extended for light curves, reconstruction and impact energies**. The concise result is [D01–D04 findings](../../outputs/d01_d04_research_2026-10-28/d01_d04_research.md). The workbook and report are in `outputs/d01_d04_research_2026-10-28/`. The historical mission-statement workbook is now in `outputs/oudated proposals/mission_definition_2026-10-27/` and is not overwritten by this builder.

## Inputs and dependencies

- `research_data.mjs`: reviewed paraphrases, source locators/access limitations, candidate definitions, user decisions and validation plan. It does not refresh literature automatically.
- `model_inputs.json`: explicit illustrative assumptions with units in field names. They do not select an architecture, detector or accepted requirement.
- `calculate.py`: Python **standard library only**. Deterministic trapezoidal Planck integration (1200 steps), Poisson photon/background bounds and a local linear Gaussian geometric budget.
- `lightcurve_inputs.json`, `calculate_lightcurves.py`, `lightcurve_results.json`: source-labelled assumptions and analytic examples of exposure averaging, event thresholds/loss, refractory limits, first-order bandwidth and timing. Standard-library calculations; no raw telescope or event data are reconstructed. `--figures` additionally uses pypdf and pdftoppm to crop cited source plots into `figures/d01_d04_lightcurves/`; its manifest records page, figure and crop coordinates. No data points are digitized or changed.
- `collect_sources.py`: Python with **pypdf** and network access. Reads supplied PDFs intact, caches public PDFs/text under `tmp/d01_d04_research/sources/` and records SHA-256/access failures in `manifest.json`. `--remote-only` skips re-extracting supplied PDFs. Some publisher PDFs are unavailable; web-indexed/HTML access limits are recorded in the evidence register.
- `calculate_energy_distribution.py`: uses the existing `analysis/v2e/.conda/python.exe` with **NumPy 1.26.4 / Matplotlib 3.10.9**, as an analysis/plotting environment only. It reads pypdf's page-marked source text cache, checks 192 unique validated rows and all three η conversions against source rounding, and writes CSV/JSON, an analytic summary and a standalone PNG/PDF figure. It does not run v2e or change its environment. [Data definitions and audit](../../data/lunar_impact_energy/README.md) retain units, source tokens, versions and discrepancies.
- `build_workbook.mjs`: Node.js and **@oai/artifact-tool** from the configured bundled runtime. The local `node_modules` junction points to that runtime; do not distribute it or modify the dependency target.
- Visual PDF checks use bundled **pdftoppm**. Workbook previews use Artifact Tool. No simulator execution or new hardware measurements are included.

## Commands

From the workspace root in PowerShell:

```powershell
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' analysis/d01_d04_research/calculate.py
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' analysis/d01_d04_research/calculate_lightcurves.py --figures
& 'C:/Users/gordo/Desktop/SMD/analysis/v2e/.conda/python.exe' -X utf8 analysis/d01_d04_research/calculate_energy_distribution.py
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' analysis/d01_d04_research/build_workbook.mjs
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' analysis/d01_d04_research/validate_outputs.py
```

Optional source-cache reproduction (network access needed):

```powershell
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' analysis/d01_d04_research/collect_sources.py
```

If the project junction is absent:

```powershell
New-Item -ItemType Junction -Path 'analysis/d01_d04_research/node_modules' -Target 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
```

Expected generated outputs:

- `model_results.json`, `parameter_sweep.csv`: reproducible physical bounds; 54 sweep rows vary range, aperture, radiance and exponential decay time.
- `workbook_cells.json`: cell map for verification, not a scientific result.
- `outputs/d01_d04_research_2026-10-28/d01_d04_research.xlsx`: ten worksheets. The original photon/range/geometry formulas remain live. Light curves and Reconstruction add published records, methods and targets. Energy catalogue adds 192 source rows with optical sums and η-dependent inference formulas; Energy distribution adds histogram counts, quantitative evidence and test targets. Its yellow η input changes the inferred kinetic column and leaves source optical/published values intact. Other curve examples are documented Python results, not an editable Excel transient-response simulation.
- `data/lunar_impact_energy/neliota_192_validated_energy_catalogue.csv` and `.json`: equivalent published records with source tokens, quoted errors, units, PDF page and SHA-256. `energy_distribution_results.json` records quantiles, histogram, exposure assumptions and source discrepancies. `figures/lunar_impact_energy/` contains standalone PNG/PDF plots.
- `tmp/d01_d04_research/workbook_previews/`: rendered checks, formula scan and `verification.json`.

The workbook uses the 100 ms reference decay/window in its compact sweep; the CSV also varies decay between 10 and 100 ms. Band/temperature determine a Python-integrated spectral factor. Changing either in Excel produces intentional `#N/A` in that factor: edit JSON, rerun calculation and builder instead of using stale spectral weights. Other model inputs recalculate in the workbook. Candidate text describes the default reference case.

## Equations and interpretation

For band-integrated received exposure `H_B`, equivalent emitted energy is `E_2pi = 2*pi*r^2*H_B`. Total charge equivalent is `S = H_B*A*q*integral[B_lambda*lambda/(h*c)]/integral[B_lambda]`. All integrations use metres; `q=0.3` is a proposed effective optics/QE/ensquared-energy/split fraction, **not a measured event-sensor efficiency**. Event count is never equated to photon count.

The noise footprint is `Omega = n_eff*(pitch/focal_length)^2`. Band-integrated background charge rate is `L_B*A*Omega*q*lambda_bg/(h*c)`. For a window `t` and independently observed baseline `t_ref`, the SNR bound is `S_t/sqrt(S_t + B_rate*t + B_rate*t^2/t_ref)`. Exponential signal fraction is `1-exp(-t/tau)`. The input energy is total profile energy, not just window energy. The peak bin is optimistically onset-aligned. Real PSFs, subpixel response, thresholding, low-light bandwidth, dark current, particle hits and loss/reconstruction errors need measured models.

The illustrative 8σ trigger plus normal quantile 1.28155 gives expected SNR 9.28155 for 90% recovery under an ideal Gaussian approximation. It is **not** a certified mission detector. At 921,600 pixels and one trial per millisecond there are ~3.32e12 trials/h: 5σ alone can produce ~9.51e5 Gaussian threshold crossings/h, and 8σ ~0.0021/h, before duration/PSF banks and non-Gaussian sources. The proposed 0.01 false confirmed/h is a study allocation. Zero false events in ~300 h gives an approximate one-sided 95% Poisson upper bound of that rate, only for a representative tested regime.

For geometry, independent per-axis angular terms and horizontal orbit error project by `sec(emission)` along the foreshortened direction; height error adds `sigma_h*tan(emission)`. The 95% 2D multiplier is `sqrt[-2*ln(0.05)] = 2.4477`. Local east/north coordinates avoid the polar longitude singularity. Correlation, visibility, rough topography and near-limb nonlinearity require full ray/DEM Monte Carlo; the linear budget is not a flight-achieved covariance.

The lux calculation is a conservative upper bound using 683 lm/W, all flash light concentrated into one pixel and 70% optical transmission. It only demonstrates why manufacturer illuminance-specific specifications cannot establish the faint-flash performance; use the actual spectrum and PSF for sensor calibration.

## Verification performed

The builder compares key Excel results to the independent Python implementation, halves/restores aperture, checks the zero-background limit and doubles/restores η to verify inverse energy scaling. It scans formula errors, renders affected views and exports the workbook. `--preview-names=energy_distribution,energy_catalogue` selects bounded previews. `validate_outputs.py` checks saved formula caches, zero error cells, ten freeze panes, all 192 energy rows and histogram counts, 54 original sweep rows and local links. It compares substantive cells/styles/columns/panes of the unchanged Candidate values, Photon budget and Localization sheets with the earlier snapshot. Native Excel behavior and sensor performance are not established. Source PDFs and rendered pages were checked for consequential values.

## Internal PDF report

`build_report.py` uses ReportLab and pypdf from the bundled Python. It reads the three results JSON files and prepared figures, and writes `outputs/d01_d04_research_2026-10-28/lunar_impact_d01_d04_report.pdf`. Introduction §§1.3–1.4 cover light curves/reconstruction; §§1.5–1.6 add energy distributions, missed impacts and temporal/spatial uncertainty. The prose is a manually reviewed snapshot; recheck it if inputs change. Open science priorities are preserved; no new hardware result is introduced.

From the workspace root:

```powershell
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' analysis/d01_d04_research/build_report.py
pdftoppm -r 130 -png 'outputs/d01_d04_research_2026-10-28/lunar_impact_d01_d04_report.pdf' 'tmp/pdfs/d01_d04_report/page'
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' analysis/d01_d04_research/verify_report.py
```

Review every rendered page before final verification. The verifier checks the reviewed 14-page layout, navigation, boundaries, key energy/curve values and original statement quotes against the unchanged historical workbook. Update pagination expectations after further changes. Checks are stored under `tmp/pdfs/d01_d04_report/`. The energy mission-objective assessment retains all three statements and refines their verification plan. Supplied PDFs and the historical mission-statement workbook are preserved.

## Light-curve extension and source access

E01–E26 identifiers remain stable; E05 now records verified PASA publication/full-publisher access. E27–E32 add complementary/Kalman reconstruction, an exceptional long flash, initial two-component spectral evidence and historical shape diversity. Some references are abstract/preview-only; those limits remain in Evidence. To cache only the newly used public PDFs without retrying unrelated sources:

```powershell
& 'C:/Users/gordo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' analysis/d01_d04_research/collect_sources.py --remote-only --only scheerlinck_2018 wang_akf_2021 madiedo_2014
```

The collector retains other manifest records. Internet access is required. Figure excerpts come from the already cached Giancono author-v1 p7/Fig5 and Athanasopoulos author-v3 p3/Fig3, with attribution in the report. Analytic tests check small-bin limits, exponential energy closure and log-event-ratio closure. None validates reconstructed lunar radiometry.
