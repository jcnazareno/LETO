# Event-Stream Simulation of One Camera Head

*Supporting event-stream model, 5 November 2026; results regenerated 12 November 2026 with the 11 November code.*

> **Status, 12 November 2026 (Europe/Berlin):** every scene run, stress run, calibration and validation (V1–V10) below was regenerated with the 11 November code (`code_version = 2026-11-11`). Relative to the 5 November model it applies flash field gain cos θ; exact charge impulses for particle deposits; a phase-angle-dependent Lunar-Lambert L; stars beyond the limb; particle tracks entering the crop; and a flash–detection match that no longer hides false triggers next to flashes. No detection or particle-trigger count changed against the first 11 November rerun; false-trigger counts fell slightly in the unmasked and map-shift terminator stresses (dimmer sunlit terrain). Calibrations are unchanged. Per-run comparisons: `data/rerun_comparison_2026-11-11.json` (5 Nov code) and `rerun_comparison_2026-11-11b.json` (first 11 Nov rerun). The pointing-jitter sweep and the star runs (Section 2) are new.

This note gives the results of the full event-stream simulator (`analysis/event_stream_sim/`). The simulator generates the event output of one camera head as it watches a drifting lunar scene. It then runs the on-board trigger and the energy estimate on that stream.

Patch models S10, S11, S16 and S17 use a 4 × 4 pixel patch. This one covers a head crop of 320 × 180 px by default, and the full 1280 × 720 frame is available as an option. The IMX636 is the baseline. The IMX646 is available as a profile, but its values are surrogates.

**It is a model, not a sensor characterisation.** All low-light values come from one published IMX636 unit (McReynolds et al. 2025) and from S10. The revision-5 baseline numbers have not been edited by this note. That does **not** mean the effects found here leave them unchanged. Section 7 lists what the team needs to decide.


## 1. What the simulator models

| Stage | Model | Source / status |
|---|---|---|
| Scene | Lunar-Lambert surface with L falling with phase angle (McEwen polynomial, USGS ISIS), WAC 643 nm Hapke albedo and LOLA LDEM_64 terrain shading with cast solar shadows. Horizon rays march 150 km on terrain sampled beyond the map region; rays that meet missing terrain are counted. The cases are the earthshine near side, the dark far side, the terminator, the far-side terminator, the limb with sky (BSC5 stars as moving point sources, occulted by the Moon) and Earth stray light, and particle hits. | WAC/LOLA team downloads; 70° S–70° N, all longitudes except 0–70° N, 180–270° E |
| Geometry | 3000 km circular polar orbit, drift across the field (0.37 px/s in the near-side run), pointing jitter, range per pixel | Proposal Section 5 |
| Optics | 16 mm f/1 lens, 600–900 nm, Gaussian PSF σ 0.5 px with an optional halo; cos⁴ vignetting for the extended scene, cos θ field gain for flashes (point sources), also divided out of the energy estimate; optional stray-light gradient or ghost | S10; stray light assumed |
| Flashes | Exponential, two-component (30% at τ/10 plus 70% at τ from a common onset; not a delayed second peak) and power-law light curves, 2 ms rise, 10 kJ–3 MJ, 30 ms–1 s. E_L is the light emitted within 4 s of the onset (a τ = 1 s power-law flash emits a further 9% after that). | S10/S11 |
| Pixel | Photon and dark-current shot noise; a low-pass photoreceptor whose time constant scales with brightness, with **adaptive sub-steps** when it is faster than the 0.5 ms step; per-pixel ON/OFF threshold mismatch; 10 µs refractory period; crossing times interpolated within the sub-step; particle deposits as exact photoreceptor responses to instantaneous charge (one jump at the deposit time); optional high-pass stand-in for `bias_hpf` (off by default) | S10 v4, S16 measured IMX636 |
| Noise | Background activity at a per-pixel lognormal rate (ON only, independent of the comparator by default; leak-drift selectable), hot pixels (1.1×10⁻⁵ at default biases, 2% at tuned biases) with a mask from a simulated 60 s dark calibration | S16, Hahmeyer 2025, McReynolds et al. 2025; rates per hot pixel assumed |
| Particles | GCR tracks from the CRaTER LET spectrum through a 3 µm layer, including tracks entering the crop from outside; deposits instantaneous by default (diffusion and delayed collection selectable as stresses); SEP cases keep the S10 parametric deposits | CRaTER Level-2; depth, timing and SEP rates assumed |
| Readout | Arbiter queue at the sensor peak rate scaled to the crop, 1 µs timestamps, FIFO drops; optional Sony on-chip filters (functional models, off) | Finateu et al. 2020 |
| On board | S10 trigger (2 × 2 and 3 × 3 groups, 0.05–2 s windows, ≤ 1 event per pixel per 0.5 ms, ≥ 3 pixels). Thresholds come from the S10 null model at each pixel's background bin. For a group mixing several bins they come from the pointwise maximum of the pixel majorant PMFs over those bins, a bound on the group tail under the declared null model. The background map used is the **true** map; on-board estimation of that map is not modelled, and map errors can be imposed. Windows are evaluated only while they end inside the observed stream. Illumination margin mask of 2 px. S10 energy decoder with onset-time background, field gain and censoring at the stream end, and an S11-style correction trained on flat lattices and clipped to its training range. | S10/S11 |
| Output | NPZ and HDF5 event files (`/events/*`, plus `/events_v2e` with the v2e row layout; `export-v2e` writes the upstream `/events` layout), ground-truth JSON, MP4 videos, interactive page | — |

All sensor and environment values live in profile files (`analysis/event_stream_sim/profiles/*.json`). Each value records its source, its uncertainty and whether it is measured, assumed or a surrogate.

## 2. Scene runs

These are 20 s crop runs (320 × 180 px) with the IMX636 profile, unless stated otherwise. Injected flashes run from 10 kJ to 300 kJ (1 MJ–3 MJ are covered by the lattice tests in Section 3). Flash onsets lie at least 4.5 s before the end, so every energy record is complete; no record in any run is censored.

"False" counts detections that match neither a flash nor a particle. On board, a particle trigger is also a false candidate. Energy errors are from 4–8 flashes per run and illustrate the scene; the precision figures are in Section 3. Run times were measured on 20 cores (Numba threads) with up to seven runs sharing the machine; they are not comparable with the 2-core figures quoted elsewhere.

| Run | Events per px per s | Flashes detected | False / particle triggers | Corrected energy error, median / rms [ln] | Run time [s] |
|---|---|---|---|---|---|
| Near side in earthshine (Copernicus) | 0.045 | 8/8 | 0 / 0 | −0.07 / 0.33 | 441 |
| Far side, dark | 0.039 | 8/8 | 0 / 0 | −0.05 / 0.27 | 360 |
| Particles, SEP 100 pfu (79 hits), hot pixels masked | 0.039 | 4/4 | 0 / 0 | −0.02 / 0.12 | 379 |
| Same, no mask, 2% hot pixels | 0.075 | 4/4 | **141** / 1 | +0.00 / 0.28 | 313 |
| Particles, CRaTER GCR solar min × 100 (102 hits), masked | 0.039 | 4/4 | 0 / 0 | −0.02 / 0.12 | 365 |
| Same, no mask, 2% hot pixels | 0.075 | 4/4 | **141** / 1 | +0.00 / 0.28 | 335 |
| Same, no mask, measured hot fraction 1.1×10⁻⁵ | 0.040 | 4/4 | 0 / 0 | +0.01 / 0.27 | 340 |
| Particles, CRaTER GCR solar max × 100 (37 hits), masked | 0.039 | 4/4 | 0 / 0 | −0.02 / 0.12 | 346 |
| Terminator, lit-surface margin mask | 0.227 | 8/8 | 0 / 0 | −0.11 / 0.29 | 744 |
| Terminator, no mask | 0.227 | 8/8 | **420** / 0 | −0.11 / 0.30 | 757 |
| Far-side terminator (Tsiolkovsky), mask | 0.119 | 8/8 | 0 / 0 | −0.05 / 0.27 | 586 |
| Far-side terminator, no mask | 0.119 | 8/8 | **184** / 0 | −0.13 / 0.23 | 666 |
| Limb with stray light | 0.041 | 6/6 | 0 / 0 | +0.07 / 0.79 | 460 |
| Same near-side scene, IMX636 | 0.045 | 7/8 | 0 / 0 | −0.10 / 0.41 | 390 |
| Same near-side scene, IMX646 surrogate | 0.050 | 7/8 | 0 / 0 | −0.07 / 0.36 | 468 |
| Full 1280 × 720 frame, near side, 6 s (7 GCR hits) | 0.063 | 6/6 | 0 / 0 | +0.11 / 0.58 | 1898 |

Stress runs. Each is the scene above with one change:

| Run | Flashes | False / particle triggers | Corrected energy, median / rms [ln] |
|---|---|---|---|
| Terminator, illumination/background map shifted +3 px (pointing error) | 8/8 | **8** / 0 | −0.00 / 0.33 |
| Terminator, map shifted −3 px | 8/8 | 1 / 0 | −0.10 / 0.29 |
| Near side, background map +20% | 8/8 | 0 / 0 | +0.14 / 0.37 |
| Near side, background map −20% | 8/8 | 0 / 0 | −0.32 / 0.45 |
| Near side, group threshold at geometric-mean background | 8/8 | 0 / 0 | −0.07 / 0.33 |
| Near side, background activity 0.3 Hz, thresholds fixed (0.03 Hz table) | 8/8 | 0 / 0 | +0.66 / 0.97 |
| Same, thresholds re-tuned to 0.3 Hz (n_min 2 s: 24 → 34) | 8/8 | 0 / 0 | +0.66 / 0.97 |
| GCR solar min × 100, 0.5 px charge diffusion | 4/4 | 0 / **1** of 102 | +0.04 / 0.05 |
| Same plus 1 ms delayed collection | 4/4 | 0 / **4** of 102 | +0.10 / 0.11 |
| GCR solar min × 100, 5 ms delayed collection | 4/4 | 0 / **3** of 102 | +0.04 / 0.05 |
| SEP 1000 pfu (845 hits, instantaneous) | 4/4 | 0 / 0 | −0.02 / 0.12 |

What the runs show:

- **Both masks are needed.** Without the hot-pixel mask (at the 2% tuned-bias hot population) or the lit-surface margin, false triggers run into the hundreds in 20 s. That fails the 1 per hour budget by orders of magnitude.
- **The lit-surface margin must cover the on-board map error.** With a perfect map the 2 px margin removes every terminator false trigger. With the map misregistered by 3 px, 8 come back. The margin, and the pointing and map knowledge behind it, need to be specified together. In the terminator crop the mask disables 17% of the 2 × 2 and 18% of the 3 × 3 groups, and 16% of the pixels lie in no enabled group in any window (far-side terminator: 7%, 8% and 6.5%). These are crop- and geometry-specific; turning them into condition-dependent completeness belongs in the yield model.
- **Particle rejection depends on how fast the charge arrives.** Instantaneous deposits never trigger with the mask (0 of 1070 hits, including 845 at SEP 1000 pfu), because the one-event-per-pixel-per-step rule clips them. Prompt collection in silicon pixel sensors takes nanoseconds to tens of nanoseconds (adjacent-device literature, not an IMX636 measurement), which is instantaneous at this time resolution. The stress cases, 0.5 px charge spread and all charge collected over 1–5 ms, are deliberate robustness extremes: 1–4 of 102 GCR hits then trigger, all heavy ions and all in the 50 ms window. They reveal a vulnerability, not an expected flight rate. A millisecond tail would need a specific trap, persistence or electronics mechanism, and its occurrence rate is unknown.
- **Mixed-background groups.** 56–97% of the group evaluations in the scenes mix pixels from 2 to 16 background bins. The pointwise-maximum bound raised none of their thresholds above the brightest bin's value, so in these scenes the brightest-pixel threshold is itself a bound under the declared null model.
- **What zero false triggers means.** A masked 20 s crop run with no false triggers is 5.8×10⁻⁵ array-hours. Zero events then bounds the rate to below about 5.2×10⁴ per array-hour (95%). These runs therefore do not test the 1 per hour budget. They show only that no gross failure remains.
- **Energies in drifting scenes are worse than on flat lattices.** Texture drift and ON-only background activity keep every scene record open for the full 4 s. As a result, faint, short flashes on bright backgrounds come out high after correction (limb +1.8 ln at 10 kJ; full frame +1.2 ln), and near-side backgrounds above 2.6×10⁴ e⁻/s lie outside the calibration's range. A ±20% background error shifts the energy by about ±0.25 ln. Ten times more background activity biases energies by +0.7 ln whether or not the thresholds are re-tuned, because the correction is fixed.
- **Trigger latency.** From onset to trigger, the median is 11–13 ms in most runs and 23 ms in the IMX636 comparison scene (range 6–43 ms). The onset estimate is late by a median of 2–5 ms. One flash in the full frame was 19 ms early.
- **Data rate.** About 0.04–0.05 events per pixel per second on the dark disc (≈ 4×10⁴ per second for a full head), 0.23 at the terminator (0.04 in the limb crop). There are no readout drops in any run. This is a local input-volume estimate, not a verified processor or interface budget.
- **IMX636 and IMX646** both detect 7 of 8 flashes on the same scene. The IMX646 values are surrogates.

### Pointing-jitter sensitivity

The baseline jitter, 0.2″ rms per axis with a 0.5 s correlation time, is an assumption (`environment.json`); one pixel is 62.7″. The sweep reruns the terminator and near-side scenes (320 × 180 px, 20 s, 8 flashes) at 0.2–60″ rms (τc = 0.5 s), with τc = 0.1 s and 2 s at 10″, extra terminator amplitudes 12, 14 and 17″, and four more jitter paths (seeds) at 5, 10, 14 and 20″: 35 runs. Data: `data/jitter/jitter_sweep_2026-11-11.json`. Figures: `figures/jitter/jitter_sweep.png` (summary) and `jitter_sweep_timeseries.png` (event rate over time). "Trigger-active" pixels have a run-mean background below the 10⁵ e⁻/s lit limit (87% of the terminator crop, all of the near-side crop). The jitter rate is the rms angular rate over 50 ms, the scene keyframe step.

| Scene | Jitter rms [″] / τc [s] | Jitter paths | rms jitter rate [″/s] | Events per px per s, all / trigger-active | False triggers per run | Flashes with \|ln error\| > 1 |
|---|---|---|---|---|---|---|
| Terminator | 0.2 / 0.5 | 1 | 2.5 | 0.23 / 0.030 | 0 | 0 |
| Terminator | 2 / 0.5 | 1 | 25 | 0.23 / 0.031 | 0 | 0 |
| Terminator | 5 / 0.5 | 5 | 61–63 | 0.30 / 0.039 | 0 (all paths) | 0 |
| Terminator | 10 / 2.0 | 1 | 63 | 0.30 / 0.040 | 0 | 0 |
| Terminator | 10 / 0.5 | 5 | 122–126 | 0.56 / 0.061 | 0 (all paths) | 0 |
| Terminator | 12 / 0.5 | 1 | 149 | 0.69 / 0.073 | 0 | 0 |
| Terminator | 14 / 0.5 | 5 | 171–176 | 0.82 / 0.081 | 0 (all paths) | 0 |
| Terminator | 17 / 0.5 | 1 | 212 | 1.04 / 0.095 | **1** | 0 |
| Terminator | 20 / 0.5 | 5 | 245–252 | 1.26 / 0.112 | **0–5 (mean 2.8; 4 of 5 paths)** | **1 in 2 of 5 paths** |
| Terminator | 10 / 0.1 | 1 | 254 | 1.19 / 0.104 | **1** | 0 |
| Terminator | 60 / 0.5 | 1 | 747 | 4.19 / 0.216 | **63** | **2** |
| Near side | 0.2–60 / 0.5, 10 / 0.1 and 2.0 | 1 | 2.5–747 | 0.04–0.05 / 0.016–0.018 | 0 | 0 |

Event rates for multi-path rows are for jitter path 11. All flashes were detected in every run.

- **The angular rate, not the amplitude, sets the effect.** At equal rms rate, 10″ at τc = 2 s matches 5″ at 0.5 s, and 10″ at 0.1 s matches 20″ at 0.5 s, in event rate and false triggers. A jitter specification therefore needs a rate (or a power spectrum), not only an rms angle.
- **Only lit/dark edges respond.** On the near side in earthshine the event rate rises by at most 10% even at 60″ (≈ 1 px), and nothing else changes. At the terminator, events in trigger-active pixels double at 125″/s and rise 3.7-fold at 250″/s; most extra events come from lit pixels, which the mask already excludes.
- **False triggers begin between about 175 and 210″/s rms (≈ 2.8–3.4 px/s).** No path gave a false trigger at ≤ 174″/s (14″); one appeared at 212″/s, and at 250″/s four of five paths gave 2–5. At 210–254″/s, 12 of the 16 false triggers lie within 4 px of lit terrain (> 10⁵ e⁻/s), all in the 2 s and 0.8 s windows: the jitter carries lit pixels across the 2 px margin mask, the same mechanism as the +3 px map-shift stress. At 750″/s there are 63 per run, in every window.
- **Energy records near lit terrain degrade first.** At 250″/s, in two of five paths, a 40 kJ flash next to lit terrain had its record's active time cut from 4.0 s to 1.9–2.3 s. Inside the training range, the quadratic correction then returned ln errors of −4.5 and −5.6 (raw +0.08 and +0.02). Flashes away from lit terrain keep their scatter (rms 0.2–0.4 ln) at every setting.
- **The 0.2″ baseline is far inside the safe region.** Up to 174″/s rms (14″ at τc = 0.5 s) no run shows a false trigger or a corrupted record. These are model predictions for two crops, five jitter paths at most and 8 flashes per run, and the statistics of this section apply (zero false triggers does not test the 1 per hour budget). The τc = 0.1 s case is only coarsely resolved by the 50 ms keyframes. A first-order Gauss–Markov process has no reaction-wheel or other tonal components.

### Stars beyond the limb

Stars are taken from the Yale Bright Star Catalogue (BSC5, V ≤ 6.5). Each is a point source fixed in inertial space, with 600–900 nm brightness scaled from the Sun: V = 0 gives 1.7×10⁶ e⁻/s. Stars are hidden by the Moon and seen only in sky pixels, so only the limb scene is affected. Which stars lie behind the limb depends on the season, which is an assumption (Sun ecliptic longitude 0° by default). Relative to the limb, stars drift at about 0.34 px/s, so they rise and set there continuously. Data: `data/stars/` (`star_survey_limb.json`, `star_runs_2026-11-11.json`). Figures: `figures/stars/`.

- **Geometry (all seasons).** In the limb crop (41% sky), a median of 1 catalogue star (maximum 8) crosses the sky part during a 20 s run. A star brighter than V = 3 appears in one of 72 seasons, and one brighter than V = 4 in five. At the default season, one V = 5.05 star (1.7×10⁴ e⁻/s) is in view.
- **Trigger, stars in open sky.** Test stars of V = 1–5 at random sky pixels gave no false triggers and changed no flash detection. Events per sky pixel rose from 0.0096 to 0.0117 s⁻¹ (V = 1).
- **Trigger, stars crossing the limb.** A test star placed so that it rises over the limb mid-run gave one false trigger at V = 3, in the 200 ms window, 0.16 s after the star appeared and at its position. It gave none at V = 1, 2, 4 or 5. Brighter stars raise the on-board background and thresholds in their pixels, because the on-board map here contains the true star, and V ≥ 4 is too faint. A rising star of about V = 3 therefore looks like a flash onset. One run per magnitude is a demonstration, not a rate.

### Pixel-parameter sensitivity: refractory period and contrast threshold

Two IMX636 parameters are uncertain. The refractory period is assumed to be 10 µs, whereas EVK4 cameras report 79 µs at default biases (Noise2Params, arXiv 2605.16317). The contrast threshold is 0.25 in the model, against published IMX636 estimates of 0.15–0.35 depending on method (see the [radiation and in-orbit evidence](radiation_in_orbit_evidence_2026-11-12.md)). Each variant below has its own energy calibration (2400 training flashes, held-out tests). The threshold variants also have the trigger table re-tuned to their C. Each variant ran four 20 s scenes (near side, far side, terminator, particles GCR × 100). Data: `data/pixel_sensitivity/pixel_sensitivity_2026-11-17.json`. Figure: `figures/pixel_sensitivity/pixel_sensitivity.png`.

| Variant | Lattice detection, exponential / two-component [%] | Corrected energy rms, exponential: all / 1–3 MJ [ln] | Corrected energy rms, two-component [ln] | Scene events per px per s, near side / terminator |
|---|---|---|---|---|
| C = 0.15 | 99.4 / 100 | 0.26 / 0.38 | 0.54 | 0.062 / 0.40 |
| C = 0.20 | 99.3 / 100 | 0.24 / 0.33 | 0.48 | 0.050 / 0.28 |
| **C = 0.25, 10 µs (baseline)** | 98.4 / 99.8 | 0.25 / 0.30 | 0.58 | 0.045 / 0.23 |
| C = 0.30 | 98.0 / 99.1 | 0.31 / 0.29 | 0.42 | 0.042 / 0.19 |
| C = 0.35 | 95.7 / 97.8 | 0.26 / 0.25 | 0.40 | 0.040 / 0.17 |
| Refractory 79 µs | 98.3 / 99.8 | 0.49 / 0.71 | 0.77 | 0.045 / 0.23 |
| Refractory 200 µs | 98.3 / 100 | 0.60 / 0.84 | 0.86 | 0.045 / 0.23 |

- **The refractory period drives energy precision.** At the camera-reported 79 µs, the corrected rms doubles (0.25 → 0.49 ln) and bright flashes (1–3 MJ) reach 0.71 ln. A long dead time most likely caps the event rate of bright, fast-rising flashes, which the event-count estimate cannot recover. Detection is unchanged. In the scene runs (flashes of 10–300 kJ only) the effect is smaller and within the scatter of 4–8 flashes.
- **The contrast threshold drives detection and data volume.** Raising C from 0.25 to 0.35 loses 2.7 percentage points of the lattice flashes (10 kJ – 3 MJ test set); lowering it to 0.15 gains 1.0 point but raises the terminator event rate by 75% (0.23 → 0.40 events per px per s). With the trigger table re-tuned, no variant produced a false trigger, and all scene flashes were detected. Energy precision depends only weakly on C.
- **Consequence.** The refractory period at the flight biases is the single most important unmeasured pixel parameter for the energy-error budget. The threshold matters for the faint-end yield and the data rate.

## 3. Validation

| Test | Result |
|---|---|
| **V1, S10 reproduction** (S10 numerics, 144 flashes per case) | Detection counts agree with S10 Table 8 and S16 Table 3 within binomial errors; the minimum Fisher p is 0.217. Examples: 8/144 vs 3/40 at 10 kJ, 30 ms; 109/144 vs 29/40 at 20 kJ, 0.1 s. Raw energy bias on complete records agrees with S10 (1.56 vs 1.57 ln at 20 kJ, 30 ms; 0.33 vs 0.30 at 300 kJ, 1 s); 0–27 records per case (up to 19%) end beyond the 4.4 s lattice and are excluded from energy statistics. Agreement with S10 is consistency with an inherited model, not sensor validation. |
| **V1b, realistic profiles** | With groups over the whole cell, the IMX636 detects 114–144 of 144 per case; the weakest is 40 kJ, 1 s. The IMX646 surrogate detects 142–144 of 144. |
| **Energy correction** (2400 training flashes; held-out tests; censored records excluded; features clipped to the training range) | IMX636 test rms: 0.25 (S11 family), 0.58 (two-component), 0.30 (power-law). Below 1 MJ: 0.24 / 0.29–0.30 / 0.27. At 1–3 MJ: 0.30 / 1.12 / 0.41. IMX646 surrogate: 0.27 / 0.54 / 0.35; features are clipped to the training range. |
| **V2, background activity** | Simulated rates match the configured ones (0.030 Hz, Fano 1.00). At the measured hot-pixel fraction, the 160 × 90 px test contains no hot pixel. The earlier masking figures (hot pixels carry 52% of events, 96% masked) apply to the 2% tuned-bias population. |
| **V3, measured texture** (S17 condition, 1.3×10⁴ e⁻/s, 30 s drift) | No false detections. Texture counts per 2 × 2 group in 2 s are 0.36–0.67 × the S17 prediction μ = S/C, with variance/mean 0.69–1.00. With the S10 numerics and a random start reference: 0.29–0.39 ×. This is a local mean-count comparison in one crop. It does not show that S17's extreme tail is conservative at the 10¹² tests per hour behind the thresholds. |
| **V5, time step** (exponential flashes, 48 per case, bootstrap errors, complete records) | With adaptive sub-steps, 0.5, 0.25 and 0.1 ms agree within the tested statistical precision for the tested exponential cases, 10 kJ–3 MJ at 1.3×10⁴ e⁻/s. At 3 MJ, 30 ms: raw −1.29 / −1.28 / −1.30 ±0.03; tighter tolerances give −1.27. The fixed-step kernel drifts (−0.83 / −0.98 / −1.15). A 16-flash 3 MJ diagnostic: fixed step −0.877 / −1.206, adaptive −1.317 / −1.317. Faint cases differ by ≤ 0.1 ln across steps (1–2σ). The corrected median stays at −0.70 ln for 3 MJ, 30 ms. Two-component, high-pass and particle cases are not covered by this test (particles: V10). |
| **V6, refractory period** (correction retrained for each setting; 1152 training and 576 test exponential flashes) | Detection in this cohort: 566/576 at every setting. Corrected rms overall: 0.22 / 0.26 / 0.51 / 0.67 ln at 0 / 10 / 50 / 200 µs. At 1–3 MJ: 0.20 / 0.33 / 0.68 / 0.91, with median −0.04 / −0.08 / −0.42 / −0.65. With no refractory period the raw bright-end bias disappears (+0.05), so the deadtime causes it. |
| **V7, high-pass and background-activity model** (default correction) | High-pass corner 0.1 / 0.5 / 1.6 Hz: corrected bias for 100 kJ, 1 s flashes −1.0 / −1.8 / −2.2 ln; 40 kJ, 1 s detected 29 / 4 / 0 of 48 (without high-pass: 39). Leak-drift background activity changes energies by ≤ 0.12 ln; this does not bound other noise physics (e.g. feedback-transistor noise). |
| **V7b, high-pass with retrained correction** (1152 training, 576 test exponential flashes per corner) | Detected 566 / 563 / 550 / 537 of 576 for no high-pass and corners 0.1 / 0.5 / 1.6 Hz. Corrected rms with the correction retrained for the corner: 0.28 / 0.30 / 0.48 / 0.66 ln; with the default correction: 0.28 / 1.83 / 2.34 / 2.63. Long flashes (τ > 0.3 s) remain the worst: retrained median −0.12 / −0.38 / −0.63, rms 0.30 / 0.56 / 0.81. Most of the energy damage is therefore estimator mismatch that a correction trained at the actual corner removes; the rest, and the detection loss, is information lost to the filter. |
| **V8, field gain** (96 flashes per case) | Corner (gain 0.908) minus centre, corrected median: +0.007 / +0.051 / −0.022 ln at 20 kJ / 100 kJ / 1 MJ, with combined median standard errors 0.072 / 0.037 / 0.044, i.e. within about 1.4σ. Reconstructing the same corner records without the gain division and passing them through the correction gives −0.118 / −0.063 / −0.116 ln; the raw shift alone would be ln 0.908 = −0.097. The 0.908 gain is a generic test value kept from the earlier extended-source model; the current point-source gain at the corner of a map scene is cos θ = 0.976. |
| **V9, cast shadow** | Ridge 3 km high, 30 km outside the map region: analytic 30.3% of the row in shadow; extended march 29.6% (max lit-fraction difference 0.03); with the terrain outside the region missing, 0%. All terminator scenes: no rays meet missing terrain. Polar and missing-terrain cases are not validated. |
| **V10, particle pulses versus time step** (dark 160 × 90 px, 20 s, GCR × 1000: 281 hits, 38 heavy) | Comparator ON events per heavy hit at 0.5 / 0.1 ms: prompt deposit 1.79 / 1.79; 10% of the charge over 1 ms 2.11 / 2.16; extreme stress (0.5 px diffusion, all charge over 1 ms) 12.0 / 12.1. Particle triggers 0 / 0, 1 / 1 and 18 / 18. Each deposit is applied as the photoreceptor's exact response to an instantaneous charge, at its own time, so the results no longer depend on the step. |

Validation data: `data/validation_*.json`. Plots: `figures/validation_s10_detection.png`, `validation_ba_rates.png`, `validation_texture_counts.png`.

## 4. Visual outputs

- **Videos** (this folder): `nearside_imx636.mp4`, `farside_imx636.mp4`, `particles_imx636.mp4`, `particles_gcrmin_x100_imx636.mp4`, `terminator_imx636.mp4`, `terminator_far_imx636.mp4`, `limb_imx636.mp4`, `nearside_imx636_full.mp4` (6 s) and `compare_nearside_imx636_vs_imx646.mp4`. `test_nearside.mp4` is the first development run with an earlier code version, kept for reference.
- **Interactive page** `event_stream_sim.html` (9 MB) replays the stored runs. Long streams are cut in time, as labelled. The flash, particle and false labels come from the simulation's ground truth, not from an on-board classifier.
- **Stills**: `figures/still_*.png`.

## 5. Options needing additional data

1. **Missing WAC tile E350N2250** (0–70° N, 180–270° E). Download it from the LROC `WAC_HAPKE` product as `WAC_HAPKE_643NM_E350N2250.IMG` and add it to `WAC_TILES`. Until then that quadrant is filled with the mean albedo; no current scene uses it.
2. **Polar terrain and albedo** (poleward of 70°). This needs a polar reader for `LDEM_75S/N` and the polar WAC mosaics. Cast shadows near ±70° are flagged where rays meet missing terrain.
3. **IMX646 low-light measurements.** Dark current, background activity, photoreceptor corner and hot pixels. Enter them in `profiles/sensor_imx646.json`, then rerun the calibration, the comparison and `validate.py realistic`.
4. **IMX636 at flight temperature and our biases.** The low-light values, the FIFO depth and, most important, the **dead time** at the chosen `bias_refr`. The vendor API returns an estimated pixel dead time in microseconds (`I_Monitoring::get_pixel_dead_time()`); bias values are not times, and the estimate is a diagnostic rather than a full characterisation of the temperature-dependent pixel response. Update `profiles/sensor_imx636.json` and rerun `validate.py refractory` at the measured value.
5. **The high-pass filter `bias_hpf`.** The IMX636 default (0) is the minimum of its 0–120 range, and decreasing the bias widens the bandwidth, so the default is the widest selectable setting (inferred from the vendor's bias table); its corner frequency is not published. V7 shows that a corner of 0.1 Hz or above matters for long flashes. Needed: a step-response measurement at the flight biases and light level. Enter its time constant as `photoreceptor.hpf_tau_s` (or a better transfer function in `pixel_kernel.py`) and recalibrate.
6. **Particle deposit timing.** The charge-collection time, any delayed (trap, persistence or electronics) tail and its occurrence rate, and the lateral spread in the IMX636 pixel, from a source or beam test or from the literature. Use them with `--particle-diffusion-px`, `--particle-collection-tau` and `--particle-tail-fraction`. SEP spectra are still open.
7. **Lens stray light and ghosts.** Measured or ray-traced data for `optics_16mm_f1.json` / `environment.json`.
8. **False-alarm rate.** One expected alert at the 1 per hour budget needs about 1.7×10⁴ crop runs, and a 95% demonstration with zero alerts about 5.2×10⁴ (about 1200 core-hours). This is not practical by brute force. Matched tail statistics, importance sampling or the S10/S17 group statistics are the route.

## 6. Limitations

- **Geometry:** a smooth sphere with terrain shading but no parallax, no libration, a fixed Earth, and no Earth shadows. For the star field the lunar spin axis is taken as the ecliptic pole, and the season is assumed.
- **On-board knowledge:** thresholds, masks and the energy background come from the true simulated background, optionally shifted or scaled. The ±20% and ±3 px stresses are sensitivity cases, not demonstrated on-board accuracy. How the background is known on board (maps, an absolute illumination reference, event statistics) and how dark current is calibrated are not modelled.
- **Trigger null model:** the thresholds bound the false-trigger rate only under the declared S10 null model (independent pixels, the S10 majorants, an assumed texture term of a contrast-2 edge in 1% of groups). Spatial and temporal correlations are not covered. Nine pixel parameters of the baseline profile cannot be represented in it at all (integrator, sub-steps, τ floor, refractory period, initial reference, dark spread, hot pixels, calibrated mask, readout); the thresholds treat them as a fixed approximation.
- **Exposure:** the mask losses are per crop and geometry, not a whole-Moon completeness map.
- **Energy correction:** trained on static flashes on flat cells. Drifting texture, high background activity and backgrounds above about 2.6×10⁴ e⁻/s are outside it.
- **Sensor:** a first-order pixel. The default background activity is ON only and does not move the comparator reference. The high-pass filter is a first-order stand-in. Temperature dependence is generic.
- **Particles:** deposits are instantaneous by default. There are no delta rays, persistence or electronics upsets. The CRaTER D2 LET tail is an upper bound for a 3 µm layer. Deposits are exact impulse responses of the first-order photoreceptor (V10 step-converged); with no second pole or bandwidth limit, a large deposit gives one ON event, so per-hit event counts depend on that idealisation.
- **Interfaces:** the sensor interface and the processor are not modelled. The readout queue is crop-scaled.
- **Statistics:** few flashes per scene and one crop per geometry; see Section 2 for what zero false triggers means.

The model description and every command are in `analysis/event_stream_sim/README.md`.

## 7. Proposed consequences for the proposal (for team decision)

1. **Lit-surface margin mask in the trigger** (S10/S11, proposal Section 4.4). Specify it together with the pointing and illumination-map accuracy: 2 px suffices only for map errors well below 3 px. Carry the masked area (7–17% of groups near the terminator) into qualified exposure.
2. **Refractory period:** keep **10 µs as the tested provisional setting**, not a hard requirement. Energy precision degrades with the refractory period: on the exponential test cohort the corrected rms rises from 0.25 ln (10 µs) to 0.49 ln (79 µs, the EVK4 default-bias value reported by the camera) and 0.60 ln (200 µs), and to 0.71–0.84 ln for 1–3 MJ flashes (pixel-parameter sensitivity, Section 2). Detection is unaffected. An acceptable limit needs the allocated energy-error and selection budget, held-out light-curve performance and the effect on the fitted energy–crater relation. **Measure the dead time at the chosen biases** (Section 5.4; the camera API reports it). The tuned low-light bias set (`bias_refr = −20`) lengthens it further.
3. **Bright-flash energy precision:** above about 1 MJ, the event-only estimate with the S11-style correction gives about 0.3 ln (exponential) to 1.1 ln (two-component) at 10 µs refractory. This is worse than the 21–25% assumed so far. Options: a correction resolved in energy and light-curve shape, a shorter dead time, or accepting larger errors for the rare bright flashes in D02–D04.
4. **High-pass filter:** add a `bias_hpf` characterisation to the sensor test plan. A correction trained at the actual corner recovers most of the energy precision (V7b: 0.30 ln at 0.1 Hz, 0.48 ln at 0.5 Hz), so the corner must be known rather than merely small. Detection of long, faint flashes is lost to the filter itself (V7: 40 kJ, 1 s from 39 to 29 of 48 at 0.1 Hz). Treat the long-flash figures as conditional on the measured corner.
5. **Particle false candidates:** the S10 union bound for particles assumes prompt deposits, which are consistent with nanosecond charge collection in silicon. Delayed tails are a robustness question, not a predicted rate: a specified trap, persistence or electronics mechanism with an occurrence rate is needed before multiplying the stress results by the hit rate. A trigger veto (for example, rejecting candidates whose events all start within one or two 0.5 ms steps in a compact cluster) would remove the vulnerability. Particle triggers count as false candidates on board. Stress runs with 0.5–2 px lateral charge spread give 1–2% triggering hits, about 190–370 false candidates per array-hour at the GCR solar-minimum rate, and neutron tests on another event sensor show multi-pixel clusters; see [radiation and in-orbit evidence](radiation_in_orbit_evidence_2026-11-12.md). The veto is therefore needed unless an IMX636 particle test shows a small spread.
6. **S17 texture result:** report only that local mean texture counts were 0.35–0.69 × the S17 model in one crop. Make no claim of tail conservatism.

   **Documentation correction, 19 November 2026:** the current V3 table in Section 3 and `data/validation_texture.json` give **0.36–0.67 ×** for the IMX636 crop; 0.35–0.69 above is an older summary. This is a correction from saved results, not a rerun, and does not establish extreme-tail conservatism. Likewise, unchanged detection in V6 applies to its 576-flash exponential cohort; the separate pixel-sensitivity table records 98.4% at 10 µs and 98.3% at 79/200 µs for its exponential test set. Its detection effect is small rather than exactly zero.
7. **Event data rate:** about 4×10⁴ events per second per head on the dark disc, 0.23 events per pixel per second at the terminator. This is an input-volume estimate for S15. The interface and processor limits are not verified.
8. **Energy correction:** the correction is clipped to its training range; that prevents extrapolation of each feature but does not validate feature combinations inside the range or give out-of-range estimates an uncertainty. Train on scenes with drift, texture and the full background range before quoting scene-level precision.
9. **Particle environment:** 4.05 / 1.56 hits cm⁻² s⁻¹ at solar minimum / maximum, unchanged. The D01 particle term should be recomputed with these rates and with item 5.
10. **Pointing stability (ADCS input, proposed, TBR):** state the jitter requirement as an angular rate. In the sweep, terminator false triggers and corrupted energy records appear between about 175 and 210″/s rms over 50 ms (2.8–3.4 px/s; five jitter paths); the near side is insensitive up to 750″/s. A provisional limit of about 90″/s rms (1.4 px/s, half the last clean rate) leaves margin. It must be confirmed with the ADCS jitter spectrum, including reaction-wheel tones, and folded into the lit-surface margin of item 1.
11. **Star rises at the limb (proposed):** a star of about V = 3 rising over the limb produced a false trigger in the limb crop. Star positions are known, so the on-board trigger can veto candidates within a few pixels of a catalogue star near the limb, or such stars can be added to the illumination mask. That needs pointing knowledge at the pixel level and a star list to V ≈ 4–5.

## 8. Particle derivation (4 November 2026)

See `derive_crater_particles.py` for the method and `data/crater_particles.json` for all values. Rates: D2 singles divided by the 9.62 cm² detector area (35 mm diameter; Spence et al. 2010, Sect. 3.1.4) give the crossing rate of a flat detector. The D2·D4·D6 telescope (geometry of D1·D6, 0.569 cm² sr, Table 5) gives a lower value for penetrating particles. The thin-detector flags are set on every event in these files, so coincidences use the thick detectors only. Primary-record counts equal the GOOD counter (no telemetry loss), and the hourly singles vary by ±2% (no solar-particle event). Figure: `figures/crater_particles.png`.

## 9. Reproduction

From `analysis/event_stream_sim/`, run `./run_regenerate_parallel_2026-11-11.sh`. It runs the calibrations and the validations that do not need them first, then all scene, stress, star and jitter runs and the remaining validations on a job pool, then the v2e export, page and summaries. Tested with Python 3.14.9, NumPy 2.5.4, SciPy 1.18.1 and Numba 0.68.1 on 20 cores (seven jobs of three threads). `run_regenerate_2026-11-11.sh A|B|C` runs the same scene, stress and validation commands in three serial parts, and `run_regenerate_2026-11-05.sh` records the 5 November run. `compare_rerun_2026-11-11.py --old <dir>` compares a rerun with a backup. The star catalogue is `data/external/BSC5/` (CDS V/50, downloaded 11 November 2026 from the VizieR mirror at vizier.cfa.harvard.edu). The summary table is `data/results_summary.json`.

The LOLA heights are read from `data/external/LOLA_DATA/ldem_64.img` unless separately cut crops are supplied (`EVENTSIM_LOLA_DIR`). The CRaTER inputs are the reduced files in `data/crater/`; `python derive_crater_particles.py` converts them. The script that reduced them from the Level-2 files is no longer in the workspace.
