# Event-stream simulator for lunar impact-flash monitoring

Simulates the event stream of one camera head of the impact-energy conversion monitor (3000 km circular polar orbit, six IMX636 heads with 16 mm f/1 lenses, 600–900 nm). It extends the S10 pixel model of `analysis/flash_response/event_response.py` from a 4 × 4 patch to a full head crop (default 320 × 180 px, full 1280 × 720 selectable). It adds a real drifting lunar scene, readout, on-chip filters, particles and hot pixels. The S10/S11 on-board trigger and event-only energy estimate run on the generated stream. S10 is reproduced as a special case (profile `imx636_s10nominal`).

This is a model, not a sensor characterisation. Its values for the IMX646 are surrogates. Results: [`event_stream_sim.md`](../../outputs/event_stream_sim.md).

**Documentation status, 12 November 2026:** code version `2026-11-11`. Every tagged scene run, stress run, calibration and validation (V1–V10), the jitter sweep (35 runs), the star runs, videos, page and `results_summary.json` were regenerated with it (`run_regenerate_parallel_2026-11-11.sh`). Tested with Python 3.14.9, NumPy 2.5.4, SciPy 1.18.1 and Numba 0.68.1 in a separate virtual environment.

## Install

Python ≥ 3.11 with NumPy ≥ 2.0 (`np.trapezoid`), SciPy, Numba (tested 0.68), Matplotlib, Pillow and h5py (`pip install --break-system-packages h5py`), plus `ffmpeg` with libx264 for the videos. Tested with Python 3.13.18, NumPy 2.5.3, SciPy 1.18.1 and Numba 0.68.1 on 2 cores. Numba compiles the kernels once per machine (about 10 s) and caches them in `eventsim/__pycache__`.

Input data (read-only):

| Data | Default location | Override |
|---|---|---|
| WAC Hapke-normalised 643 nm tiles E350N0450, E350N3150, E350S3150, and since 4 Nov 2026 E350S0450, E350N1350, E350S1350, E350S2250 (E350N2250 missing) | `data/external/ALBEDO_WAC_HAPKE_NORMALIZED_REFLECTANCE_643NM/` | `EVENTSIM_WAC_DIR` |
| LOLA LDEM_64 heights 70° S–70° N (int16, ×0.5 m) | crops in `data/lola_crops/` if present, else rows 1280–10239 read directly from `data/external/LOLA_DATA/ldem_64.img` (the crops are bit-identical slices of it) | `EVENTSIM_LOLA_DIR` (crops), `EVENTSIM_LOLA_FULL` (full file) |
| CRaTER reduced days (particles) | `data/crater/` | – |
| S10 thresholds, S13 observing samples and measured texture | `data/event_response.json`, `data/observed_background_samples.npz`, `data/texture_histograms.json` | – |

On the team computer no crops are needed: the reader takes the three longitude ranges (columns 0–5759, 17280–23039 and 5760–17279) from the full `ldem_64.img`. Set `EVENTSIM_LOLA_DIR` only to use separately cut crops.

The scene metadata records which LOLA source was used (`map_coverage.lola_source`).

## Commands

Run from this folder. Event files go to `data/`, videos and the page to `outputs/`, plots to `figures/`.

```bash
python run_sim.py run --scene nearside --sensor imx636 --crop 320x180 --duration 20 --flashes 8 --video
python run_sim.py run --scene farside --full-frame --duration 6 --flashes 6        # full 1280 x 720 frame (>= 5.1 s for complete energy records)
python run_sim.py run --scene particles --particles sep100 --duration 20 --video
python run_sim.py run --scene terminator --lit-limit 1e12 --tag terminator_nomask   # illumination mask off
python run_sim.py run --scene limb --set env.straylight.mode=ghost --video
python run_sim.py compare --scene nearside --sensors imx636,imx646 --duration 20    # three-panel video
python run_sim.py run --scene nearside --flash-spec "2e4:0.1,1e5:1.0:double" --I0-target 1.3e4
python run_sim.py calibrate --sensor imx636                                         # energy correction (S11 style)
python run_sim.py profiles                                                          # list profile files
python run_sim.py export-v2e --tag nearside_imx636                                 # upstream-v2e layout copy (/events N x 4)
python validate.py all                                                              # V1-V10 below
python build_page.py                                                                # interactive page from stored runs
./run_regenerate_2026-11-11.sh A|B|C                                               # every stored result (A scenes, B stress runs, C validations; about 3 h on 2 cores)
./run_regenerate_2026-11-11.sh A|B|C                                               # serial scene/stress/validation parts; current code version 11 Nov
./run_jitter_sweep_2026-11-11.sh [base|ext|all]                                    # pointing-jitter sweep (16 + 19 runs) + jitter_sweep.py
./run_regenerate_parallel_2026-11-11.sh                                            # everything above (and V2, jitter, star runs) on a job pool
python star_survey.py; python star_runs.py                                         # stars behind the limb: geometry survey, trigger effect
./run_pixel_sensitivity_2026-11-17.sh; python pixel_sensitivity.py                # refractory 79/200 us and C 0.15-0.35: own calibrations (calibrate --tag, --threshold-model), 4 scenes each
python run_sim.py run ... --calib-tag <tag>                                        # use energy_calibration_<tag>.json
```

Main options:

- `--scene` is `nearside`, `farside`, `particles`, `terminator`, `terminator_far` (far-side terminator, 4 Nov 2026) or `limb`. `--crop WxH` is placed at the head centre; `--full-frame` selects the whole sensor.
- `--sensor` takes a profile name, and `--set section.key=value` overrides any profile key (sections `sensor`, `optics`, `env`; values in JSON), for example `--set sensor.ba.rate_hz=0.3` or `--set env.straylight.mode=both`.
- `--flashes N` injects N flashes from a fixed E/τ cycle at random positions and times. `--flash-spec "E_J:tau_s[:exp|double|power],…"` gives them explicitly.
- `--particles` is `none`, `gcr` (default: CRaTER solar minimum, 4.05 cm⁻² s⁻¹), `gcr_min`, `gcr_max` (1.56), `gcr_min_x100`, `gcr_max_x100` (rate × 100 for statistics), `sep10`, `sep100` or `sep1000` (SEP cases keep the S10 parametric deposits).
- `--I0-target` scales the earthshine so that the crop-mean background (dark plus earthshine) equals the target, as S17 did.
- `--thresholds compute|stored`: `compute` (default) evaluates the S10 null model at the local background in 0.2-ln bins and caches it in `data/thresholds_cache.json` under a key that fingerprints the null-model parameters, `event_response.py` and the binning algorithm (stale entries are never reused); `stored` uses the `event_response.json` grid.
- `--threshold-model fixed|retuned`: `fixed` (default) uses the profile's S10 case as it is, as a fixed on-board table would; `retuned` replaces that case's **mapped** inputs (τ_ref including `I_ref`, C, background-activity rate and model, τ cap, law, mask fraction, aperture, dark current) with the run's profile values. Pixel parameters the S10 null model cannot represent (integrator, sub-steps, τ floor, second pole, high-pass, separate or differently spread ON/OFF thresholds, refractory period, event loss, initial reference, dark spread, hot pixels, calibrated mask, background-activity polarity/model, readout and on-chip filters) are reported as `unmapped_differences` in `<tag>_truth.json` (`trigger`) and kept as a fixed approximation in both modes. An empty `mapped_differences` therefore does not mean that the null model equals the simulated pixel; the baseline IMX636 profile has nine unmapped differences.
- `--group-bg hetero|max|geomean`: how a group with pixels in different background bins gets its threshold. `hetero` (default): from the pointwise maximum of the per-bin S10 pixel majorant PMFs over the group's bin range, a valid bound on the group tail under the declared null model (independent pixels, S10 majorants, assumed texture term; spatial and temporal correlations not covered). `max`: the brightest pixel's bin (a heuristic). `geomean`: the geometric mean. Per-bin PMFs are cached in `data/null_pmf_cache/`; `trigger.heterogeneous_groups` in the truth file counts mixed groups and how many thresholds the bound raised.
- `--map-shift DX,DY`, `--map-scale-err e`: the background/illumination map given to the on-board trigger and energy estimate is the truth shifted by (DX, DY) px and scaled by (1 + e) — a stress of the on-board map and pointing knowledge.
- `--energy-bg onset_chunk|run_mean` (background of the time chunk at the flash onset, default, or the run mean) and `--bg-err` (common background error, 5%).
- `--record-pad` (default 4.5 s): flash onsets (any number, one included) are drawn no later than `duration − record_pad`, so every 4 s energy record lies inside the stream. Records cut by the end of the stream are flagged `censored`, are not corrected and are left out of energy statistics.
- `--particle-diffusion-px`, `--particle-collection-tau`, `--particle-tail-fraction`: robustness stresses of the particle deposit (Gaussian lateral spread; delayed collection of the given fraction of the charge, exponential, in 8 pieces, the rest prompt). Prompt collection in silicon pixel sensors is of order ns–tens of ns (adjacent-device literature), i.e. instantaneous here; millisecond tails would need a specific trap, persistence or electronics mechanism.
- `--lit-limit` sets the background above which groups are excluded from the trigger (default 10⁵ e⁻/s).
- `--dt` sets the pixel step (default 0.5 ms; adaptive sub-steps resolve faster dynamics, see below; 0.25 and 0.1 ms tested). `--seed` sets the random seed (fixed default). `--no-h5` skips the HDF5 file.

## Model components

Every physical parameter is in a profile file (`profiles/*.json`) with value, unit, uncertainty, source and status (measured, datasheet, published, derived, assumed, surrogate, convention). Profiles can inherit from one another.

| Profile | Use |
|---|---|
| `sensor_imx636.json` | Baseline: measured IMX636 low-light values (McReynolds et al. 2025, S16 case m636) plus realistic additions (hot pixels, refractory period, finite prehistory, readout) |
| `sensor_imx646.json` | IMX646 surrogate: τ_ref halved and τ_min 8× longer, from Sony flyer latency maxima at unmatched illumination (0.3 lx for the IMX646, 5 lx for the IMX636; 1/I extrapolation assumed); everything else as the IMX636. Not a sensor-selection basis. |
| `sensor_imx636_s10nominal.json` | Exact S10 nominal case (validation) |
| `sensor_imx636_m636s10.json` | S16 m636 in S10 numerics (validation) |
| `sensor_imx636_pessimistic.json`, `_tuned.json`, `_warm.json` | Revision-5 pessimistic corner, tuned biases (C 0.10, 1 Hz), warm sensor (5.55 fA) |
| `optics_16mm_f1.json`, `optics_25mm_f1.json` | Lens, transmission, band, PSF, vignetting, distortion, mosaic |
| `environment.json` | Orbit, Moon, earthshine and solar levels, jitter, particles, stray light |

**Scene radiometry** (`eventsim/radiometry.py`, `scenes.py`, `lunar_maps.py`):

- **Extended sources.** A surface of reflectance ρ under band irradiance E gives L = ρ E f_band/π. The detected rate is L · A_ap · Ω_pix · T · QE / (hc/750 nm). This is the S13 chain: 1.85×10⁴ e⁻/s per pixel for a full Earth at zenith, with ρ = 0.13, 0.075 W/m² and f_band = 0.284. Full sunlight gives 3.4×10⁸ e⁻/s.
- **Near-side texture.** The WAC 643 nm albedo is normalised to the near-side mean (|lat| < 60°, three tiles), so the mean surface has ρ = 0.13 as in S13 and S17. Shading is Lunar-Lambert, LL = 2Lμ₀/(μ₀+μ) + (1−L)μ₀, from LOLA slopes, with L a function of the phase angle α per map point (since 11 Nov 2026, `surface.lunar_lambert_L = "mcewen"`): L(α) = 1 − 0.019α + 2.42×10⁻⁴α² − 1.46×10⁻⁶α³ (α in degrees; USGS ISIS `LunarLambertMcEwen`, A. McEwen 1995), clipped to [0, 1]. A number sets a fixed L (0.7, as in S17, corresponds to α ≈ 18°). Scene metadata records the phase-angle percentiles (`phase_angle_deg`). Shading is evaluated for the Earth at the sub-Earth point (0° N, 0° E) and the spacecraft direction at mid-run. The Earth's phase follows from the subsolar point (Lambert-sphere phase law, S13).
- **Sunlight.** It uses the same shading plus cast shadows: a horizon march along the solar azimuth on LOLA with lunar curvature, softened by the 0.53° solar disc.
- **Lens.** The PSF is a Gaussian (σ 0.5 px, S10) with an optional wide halo, applied on an oversampled grid (2 × 2 rays per pixel for crops) before pixel integration. Vignetting of the scene is cos⁴θ (assumed natural fall-off), and radial distortion k₁ is 0 by default (no lens data). Flashes are point sources and get only the pupil foreshortening cos θ (since 10 Nov 2026; before, they were also scaled by cos⁴θ, up to 7% too faint at the frame corner).
- **Stray light** (assumption): an exponential gradient from one field edge of the sensor array (frame size from the sensor profile), an annular ghost, or both, each with a linear ramp in time.
- **Stars** (`stars.py`, since 11 Nov 2026): Yale Bright Star Catalogue stars (BSC5, V ≤ 6.5, `data/external/BSC5/`) as point sources fixed in inertial space, visible only where the ray misses the Moon (so only the limb scene is affected). Band rate = solar band irradiance × 10^(−0.4(V + 26.76)) × colour term (V_sun from Willmer 2018; black body at T(B−V) from Ballesteros 2012, relative to the Sun at B−V = 0.65); V = 0 gives 1.7×10⁶ e⁻/s. PSF and cos θ gain as for flashes. The Moon-fixed frame's orientation needs the season (`stars.sun_ecliptic_lon_deg`, assumed 0°); `stars.test_mags` adds test stars of given V at random sky pixels. `star_survey.py` maps which stars cross the limb crop over the year.

**Geometry and motion** (`geometry.py`):

- **Orbit.** Circular polar 3000 km orbit; the node drifts with the Moon's sidereal rotation.
- **Heads.** Nadir pointing with the image 'up' along the flight direction. Each head is a pinhole camera tilted by the `coverage.py` mosaic offsets (±10.4° cross-track, 0 and ±11.9° along track).
- **Ray casting.** Rays hit the 1737.4 km sphere, which gives slant range, emission angle, drift and the limb. Scene drift at a head centre is 0.37 px/s (0.41 px/s at nadir, S17).
- **Jitter.** First-order Gauss–Markov, 0.2″ rms per axis, 0.5 s correlation (assumed); `--jitter-seed` (default 11) selects the path.
- **Sub-pixel motion.** Keyframes are ray-cast every 50 ms (0.02 px of drift) and interpolated linearly in time.
- **Flashes.** They are fixed on the ground, so they drift with the scene; their PSF fraction is refreshed every 10 ms.

**Pixel front end** (`pixel_kernel.py`, Numba, parallel over rows, per-pixel xoroshiro128+ generators so results do not depend on the thread count):

- **Photo-electrons.** Poisson draws of (background + dark_i + flash) · dt, using inversion below λ = 30 and PTRS rejection above. Dark current has a lognormal spread between pixels and a temperature scaling of 2^(ΔT/6.5 °C) (generic, assumed).
- **Photoreceptor.** First-order low-pass with τ = τ_ref (I_ref/J)^g (g = 1 linear, 0.5 sqrt), clipped to [τ_min, τ_cap]. The default is an exponential update with τ frozen over the (sub-)step; `euler_s10` reproduces S10 (Euler, τ clipped at dt). An optional second pole (source follower) acts on ln J, and an optional first-order high-pass (`photoreceptor.hpf_tau_s`, off by default) on the change-detector input as a stand-in for `bias_hpf` in sensitivity studies.
- **Adaptive sub-steps.** A 0.5 ms step is split into m equal sub-steps when the photoreceptor is faster than the step (h ≤ 0.5 τ) or ln J would change by more than 0.1 in it, down to h = 5 µs. Each sub-step draws its own photons (so the photon-noise bandwidth follows τ), re-evaluates the flash light curve and runs the comparator on its own segment. Dim pixels keep m = 1, identical to the earlier kernel. This makes bright-flash energies independent of the global step (V5). The sub-step count is chosen from the optical rate before particle deposits are added; V10 tests particle pulses at 0.5 and 0.1 ms.
- **Charge impulses** (since 11 Nov 2026, `photoreceptor.deposit_model = impulse`). A particle deposit Q is applied as the exact response of the photoreceptor to an instantaneous charge: ∫τ(J) dJ = Q from J₀ to J₁, i.e. Δln J = Q/K (K = τ_ref I_ref = 2025 e⁻) between the τ clips, ΔJ = Q/τ_min above them (checked against a numerical ODE solution to 5×10⁻¹⁰ in ln J). The comparator sees the jump at the deposit time, so one jump gives one ON event per refractory period, independent of the step; the decay follows with the adaptive sub-steps. `step_current` reproduces the earlier kernel (charge added to the step's mean current), and `euler_s10` ignores the setting.
- **Change detector.**
  - Separate ON and OFF thresholds per pixel, N(C, σ_C) clipped at 0.08, either correlated (S10) or independent.
  - Events carry crossing times interpolated within the step, not only the step boundary.
  - Refractory period with reset of the reference to the current level at its end. With a zero refractory period this equals S10's `ref += C`.
  - Event loss of 1%.
  - The initial reference is either uniform within one threshold of the level (finite prehistory, S11 test g) or at the level (S10).
- **Background activity.**
  - `poisson_additive` (S10): ON events (ON fraction configurable) at per-pixel lognormal rates, optionally in bursts or with telegraph switching. They do not move the reference.
  - `leak_drift` (v2e-like): the reference drifts down at r · C.
  - A separate hot-pixel population: default fraction 1.1×10⁻⁵ (Hahmeyer 2025, Sect. 3.2 p. 17 / Fig. 3.2a–b p. 18, EVK4 at room temperature; recording duration unstated); the tuned profile retains 2%. Median rate 1 Hz and σ_ln 1 remain assumptions. The noisiest fraction is masked using a simulated 60 s dark calibration. These profiles do not establish flight/end-of-life hot-pixel rates.
- **Particles.**
  - Poisson hits over the crop, plus tracks entering it from outside (since 11 Nov 2026, `particles.entering_tracks`: entry points in a ring of up to 400 px, bounded by the sensor edges in map scenes; a separate random stream keeps the in-crop hits unchanged). GCR (since 4 Nov 2026, `particles.model = let_spectrum`, `eventsim/particles.py`): rate and LET spectrum from LRO CRaTER (`derive_crater_particles.py`), cos-weighted isotropic tracks through a 3 µm sensitive layer, charge = LET × chord / 3.6 eV × lognormal straggling. SEP cases use the radiation study's screening rates with the S10 parametric deposits below.
  - Parametric model (S10, SEP presets): straight tracks of 1–5 px. Deposits are minimum-ionising (lognormal around 300 e⁻) or, for 5% of hits, log-uniform 2×10³–10⁵ e⁻ per pixel, applied as charge impulses (above).

**Readout and ESP** (`readout.py`):

- **Arbiter.** A single-server queue at the sensor peak rate (1.066 Geps, Finateu et al. 2020), scaled to the crop's share of the array, with FIFO drops. Time stamps are the readout times at 1 µs resolution. S10 mode switches the queue off.
- **On-chip filters** (off by default, all switchable):
  - Event Rate Controller: random drop above target × 200 µs.
  - Anti-flicker: 4 × 4 blocks, 50–500 Hz. This is a simplified functional model, not Sony's circuit.
  - STC/trail filter: `stc_cut_trail`, `stc_keep_trail` or `trail`, 1–100 ms.

**On-board trigger and energy** (`trigger.py`):

- **Trigger rule.** The S10 rule runs on the stream: every 2 × 2 and 3 × 3 group, windows 0.05/0.2/0.8/2.0 s every W/5, at most one ON event per pixel per 0.5 ms step, at least 3 contributing pixels.
- **Thresholds.** n_min(W, size) comes from `event_response.thresholds` for the profile's S10 case at each pixel's background bin, per 0.5 s chunk; mixed groups use the `--group-bg` rule (default: the pointwise-max majorant bound). Groups above the lit-surface limit are excluded. Trigger windows are evaluated only while they end inside the observed stream.
- **Clustering.** Triggers within 4 px and 4 s are merged into one detection.
- **Energy.**
  - The S10 decoder runs on a 4 × 4 patch centred on the ON-event centroid within 9 × 9 px of the triggering group, using calibrated thresholds with 5% error and the background of the time chunk at the onset with a 5% common error. Decoded electrons are divided by the electrons per joule at the slant range and by the patch's field gain (the vignetting the scene applied to the point source), so E_L is the emitted energy at any field position.
  - The record ends when the patch is back at its pre-flash level, after 4 s, or at the end of the stream; in the last case the record is `censored` (integrated over the observed part only, not corrected, excluded from statistics).
  - The S11 quadratic correction is trained on this simulator by `calibrate`: lattices of flashes on flat cells, with E_L, τ, range and earthshine drawn as in S11. It is applied with its five base features clipped to the training range (`feature_range` in the calibration file); detections outside it are flagged `outside_training_range`.
- **Matching.** Each detection is labelled `flash`, `particle` or `false` against the ground truth. A flash claims only its first detection, and only within 2.5 s of its onset (longest window + 0.5 s); any other detection near a flash stays `false` and carries `near_flash` (counted in `n_false_near_flash`).

**Outputs** (`io_out.py`), per run `<tag>`:

- **`<tag>.h5`**:
  - `/events/t` (int64, µs), `/events/x`, `/events/y` (uint16, crop px; `crop_x0/y0` attributes give the sensor offset) and `/events/p` (uint8, 1 = ON, 0 = OFF).
  - `/events_v2e` (N × 4 uint32 `[t_us, x, y, p]`, p ∈ {0, 1}): the **row layout** of v2e `--dvs_h5`, under a different name (upstream v2e writes the matrix as the root dataset `/events`, which here is a group). `run_sim.py export-v2e --tag <tag>` writes an upstream-layout copy `<tag>_v2e.h5`. uint32 microseconds wrap above 4295 s; the matrix is then omitted (and the page packer refuses).
  - `/truth/*` (flashes, particle deposits, hot and masked maps) and JSON attributes with the full configuration and profiles.
- **`<tag>_events.npz`**: the same events with p = ±1, the source (0 = comparator, 1 = background activity), the pixel time before readout, and maps (dark, BA rate, C_on/C_off, mask, hot, mean background, range).
- **`<tag>_truth.json`**: configuration, scene metadata, every flash and particle hit, every detection with its energy estimate, the summary, and run times.
- **`<tag>_keyframes.npz`**: log₁₀ input rate every 2.5 s (for the page).

## Validation

`python validate.py all` writes `data/validation_*.json` and `figures/validation_*.png`. The results are in the results note.

- **V1 (`s10`).** S10 Table 8 (nominal, 6.5×10³ and 1.3×10⁴ e⁻/s) and S16 Table 3 (m636, 1.3×10⁴ e⁻/s) in S10 numerics: 144 flashes per case on lattices, groups restricted to each flash's 4 × 4 patch, stored thresholds.
- **V1b (`realistic`).** The same grids with the realistic IMX636 and IMX646 profiles, with groups restricted to the patch or open over the whole cell.
- **V2 (`ba`).** Configured versus simulated background-activity rates, Fano factor, share in hot pixels, masking efficiency, and comparator noise events.
- **V3 (`texture`).** Measured near-side texture at 1.3×10⁴ e⁻/s (S17 condition): false detections, and texture counts per 2 × 2 group and 2 s window against μ = S/C (S17), including the variance ratio and tail shares.
- **V5 (`substep`).** Faint and bright (to 3 MJ) flashes at 0.5, 0.25 and 0.1 ms, with the fixed-step kernel, adaptive sub-steps and tighter sub-step tolerances; raw and corrected energy with bootstrap errors; plus the reviewer's 3 MJ diagnostic.
- **V6 (`refractory`).** Raw and corrected energy error against the refractory period (0, 10, 50, 200 µs), with the correction retrained for each setting.
- **V7 (`sensitivity`).** High-pass corner 0.1–1.6 Hz (bias_hpf stand-in) and the leak-drift background-activity model, with the default correction.
- **V7b (`hpf_retrained`).** The same high-pass corners with the correction retrained per setting, against the default correction on the same held-out flashes (information loss versus estimator mismatch).
- **V8 (`field_gain`).** Point sources at a generic field gain of 0.908 against the centre, with the no-gain-division counterfactual evaluated through the correction. This reproduces the pre-10 November corner-gain test, not the current map-scene corner point-source gain (cos θ = 0.976).
- **V9 (`shadow`).** Analytic ridge 30 km outside the map region against the horizon march.
- **V10 (`particle_timestep`).** Particle pulses (prompt, 10% tail over 1 ms, extreme all-delayed with diffusion) at 0.5 and 0.1 ms steps: comparator events per hit and particle triggers.

Energy statistics in the lattice validations use one cohort of complete records for raw and corrected errors; censored records are counted (`n_censored`) and kept only as a labelled partial-record diagnostic.

## Pointing-jitter sweep (11 November 2026)

`run_jitter_sweep_2026-11-11.sh` runs the terminator and near-side scenes (320 × 180 crop, 20 s, 8 flashes, default seeds) at `env.attitude.jitter_rms_arcsec` = 0.2, 2, 5, 10, 20 and 60″ (τc = 0.5 s), plus τc = 0.1 s and 2 s at 10″; tags `<scene>_imx636_jitter<rms>[_tc<τc>]`, truth/event files moved to `data/jitter/`, logs in `data/logs/jitter/`. Three runs at a time (`PAR`, `NUMBA_NUM_THREADS`) need about 50 min on 20 cores. `jitter_sweep.py` then reads the truth and event files and writes:

- `data/jitter/jitter_sweep_2026-11-11.json`: per run detections, false triggers (with location and local background), raw trigger rows, event rates split into trigger-active (run-mean background below the lit limit) and lit pixels, per-flash energy errors and record features, and the realised jitter rms and 50 ms angular rate.
- `figures/jitter/jitter_sweep.png` (six-panel summary) and `jitter_sweep_timeseries.png` (event rate over time with the jitter rate).

The jitter generator draws one Gauss-Markov path (seed 11), so every amplitude scales the same path; the scene is ray-cast every 50 ms keyframe and interpolated, so τc = 0.1 s is only coarsely resolved. Results: results note, section on pointing jitter.

## Performance

The kernel needs about 27–35 ns per pixel-step on 2 cores, so 320 × 180 px for 20 s at 0.5 ms (2.3×10⁹ pixel-steps) takes about 70 s. A full frame for 2 s takes about 2 min. Memory is dominated by the keyframes (P × K × 8 bytes per 0.5 s chunk) and the threshold maps; peak RSS was about 1.1 GB for a crop, most of it memory-mapped WAC pages. Each new 0.2-ln background bin costs about 3.6 s of threshold computation once, after which it is cached. Measured run times are in each `_truth.json` (`stats`) and in the results note.

## Code changes of 10–11 November 2026

All stored results use the code with these changes (see the component descriptions above for details).

- **Point-source field gain** (10 Nov): flashes and the energy estimate use cos θ instead of the extended-source cos⁴θ.
- **Initial reference** (10 Nov): with `events.initial_reference = random`, the start offset lies inside the dead band of the matching comparator; bit-identical for every shipped profile.
- **Charge impulses** (11 Nov, handoff 3.3): exact photoreceptor response to each deposit at its own time (V10 step-converged). Bit-identical for runs without particles; `deposit_model = step_current` reproduces the earlier kernel.
- **Lunar-Lambert L(α)** (11 Nov): McEwen phase polynomial instead of L = 0.7. Mean background +0.8% on the near side, −10% at the limb, −16% on sunlit terminator terrain.
- **Stars beyond the limb** (11 Nov, handoff 3.4): BSC5 point sources; only the limb scene has sky.
- **Entering particle tracks, stray-light frame size, `match()`** (11 Nov, handoff 3.6).
- **`--jitter-seed`** (11 Nov): selects the attitude-jitter path (default 11, unchanged).

Regression guard: a 7 s, 160 × 90 far-side run with `--flashes 3 --set 'optics.vignetting.model="none"'` gives 5342 events with the 5, 10 and 11 November code (identical event arrays).

## Assumptions and limits

- **Sensor.** The pixel is first order (second pole optional, off). Every low-light value comes from one published IMX636 unit at an unreported temperature. The refractory period (10 µs, tested provisional setting), the hot-pixel activity distribution beyond its source-derived default fraction, the dark-current spread, the ON fraction of background activity and the readout FIFO depth are assumptions. The IMX646 values are surrogates. The physical IMX636 high-pass response is uncharacterised here: `bias_hpf` defaults to 0, the minimum of its 0–120 range, and decreasing it widens the bandwidth, so the default is the widest selectable setting (inferred from the Prophesee bias table); its corner frequency is not published. An optional first-order stand-in is available and was stressed in V7 and V7b.
- **Background activity.** In the default `poisson_additive` mode it does not interact with the comparator (S10 convention).
- **Geometry.** A smooth sphere with no terrain parallax; no libration; Earth fixed at the sub-Earth point; lunar spin axis taken as the ecliptic pole for the star field. Earth shadows are not cast (only solar shadows). The Lunar-Lambert view direction is fixed at mid-run.
- **Map data.** WAC and LOLA cover 70° S–70° N at all longitudes, except the WAC tile 0–70° N, 180–270° E (filled with the mean albedo, flagged). The near-side albedo normalisation uses the three original near-side tiles. No polar maps. Cast-shadow rays march 150 km on terrain sampled beyond the region in the Sun's direction; rays that meet missing terrain (|lat| > 70°) are counted in the scene metadata (`cast_shadow`).
- **Particles.** GCR rates and LET come from two quiet CRaTER days per solar epoch; the sensitive depth, straggling and SEP rates are assumptions, deposits are instantaneous by default (diffusion and delayed collection are available as robustness stresses, not expected flight behaviour), and there is no delta-ray structure, persistence or electronics upset. GCR presets inject their configured particle populations.
- **Readout.** The queue scales the full-sensor rate to the crop, assuming uniform activity elsewhere. Sony publishes the interface types and formats, but their end-to-end limit and the processor are not modelled here.
- **Trigger thresholds and masks.** They come from the S10 declared null model, evaluated at the TRUE simulated background (optionally shifted/scaled with `--map-shift`/`--map-scale-err`); the on-board estimation of that background from events is not implemented. The simulator's realistic noise (hot pixels, prehistory, texture) is not part of the null model, nor are spatial or temporal correlations between pixels; the texture term (contrast-2 edge in 1% of groups) is an assumption. The false-trigger counts show only gross differences.
- **Statistics.** A 320 × 180 crop is 1/96 of the six-head array area, so a 20 s crop run is 5.8×10⁻⁵ array-hours. Zero false triggers in one run gives a one-sided 95% upper limit of about 5.2×10⁴ per array-hour; one expected alert at the 1 per hour budget needs about 1.7×10⁴ runs and a 95% demonstration with zero alerts about 5.2×10⁴.

## Options needing additional data

See the same section in the results note. Each item states what is missing, where to get it, where to put it, and what to rerun.
