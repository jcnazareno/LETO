---
title: "Simulations Behind the Impact-Energy Conversion Proposal"
subtitle: "Methods, assumptions and results, revision 5 (2 November 2026; updated 4 November 2026), short version"
---

> **LETO SRR applicability, 22 November 2026.** This summary describes the stored revision-5 calculations. Verify the SRR requirements against their own conditions, including the separate 260 km power fixture and the 229.8 kg forward mass case. [SRR and requirements](../../leto_srr.md)

> This report describes the simulations behind the [mission proposal](../impact_energy_conversion_proposal.md). For each one it states the question, the model, the main assumptions and the result. The scripts are in [`analysis/impact_energy_conversion/`](../../analysis/impact_energy_conversion/README.md) and their outputs in `data/impact_energy_conversion/`. The full version with every intermediate table is the [main simulation report](simulation.md). These are screening models for a concept decision. They are not a maintained trajectory, a calibrated sensor model or a cost estimate.

# 1. Introduction

The proposal rests on four questions. How much of the dark Moon can the cameras watch? Can the event cameras detect and measure faint, slow impact flashes? How many flash–crater pairs does that give? And how precisely can the flash-to-crater relation then be measured? Table 1 lists the simulations that answer them. The report includes three follow-up studies (S16–S18, Section 11). They test the detector and crater assumptions with measured data: an event-sensor trade, the measured lunar texture, and crater tests on real LRO images. The revision-5 results are not rerun.

Table: Simulations and calculations used in the proposal.

| ID | Name | Script | Question |
|---|---|---|---|
| S1 | Coverage | `coverage.py` | How much dark surface-time does a camera mosaic watch? |
| S2, S3 | Orbit stability | `orbit_stability.py`, `orbit_trades.py` | Do the circular and elliptical orbits stay usable, and at what cost? |
| S4 | Imaging access | `imaging_access_check.py` | Which flash sites can the crater camera photograph? |
| S5 | Camera count | `orbit_trades.py` | How many cameras, with which lens? |
| S10 | Event-camera detector | `event_response.py` | Which flashes are detected without false alarms? |
| S11 | Energy calibration | `photometry_calibration.py` | How well is the flash energy measured from events? |
| S13 | Observed background | `observed_background.py` | Which earthshine, range and latitude do the cameras see? |
| S14 | Joint model | `joint_model.py` | How many pairs, and how precise is the fitted relation? |
| S6, S7 | Comparators and analytic check | `science_model.py` | Yields of the ground-based alternatives; analytic precision |
| S8, S9, S15 | Supporting calculations | `science_model.py`, `transfer.py`, `system_budget.py` | Localization, image quality, capture and spacecraft budget |
| S16 | Event-sensor trade | `sensor_trade.py` | Which sensor, settings, head size and cooling, from measured IMX636 data? |
| S17 | Measured lunar texture | `texture_map.py`, `texture_measured.py` | Does the real near-side texture stay within the false-alarm budget? |
| S18 | Crater tests on real LRO images | `crater_injection_test/` | Does the crater-confirmation curve hold on real images and real new craters? |

All simulations use a spherical Moon of radius 1737.4 km. The flash energy E_L is the light received in the 600–900 nm band, converted to the energy emitted into the hemisphere above the surface. For real flash spectra of 2000–4500 K this conversion changes by about ±4%, which is carried in the calibration budget. Position errors are given as the semi-major axis of the 95% error ellipse. All random seeds are fixed, so every result can be reproduced exactly.

# 2. Coverage (S1)

The coverage simulation determines what share of the Moon's surface-time a mosaic of downward-looking cameras observes in darkness. The spacecraft flies a circular polar orbit, the Moon rotates beneath it, and the Sun moves around the Moon once per year with the small tilt that gives the poles their seasons. A surface point counts as observed when it lies inside a camera's field, is seen at less than 65° from its local vertical, is in darkness, and the Sun is far enough from the camera's line of sight or hidden behind the Moon. The points form an equal-area grid, plus rings at high latitudes and the two exact poles.

The model was checked against an independent earlier calculation for a 625 km orbit and agrees to within 2% (21.4 against 21.1 hours per year). Table 2 shows how the watched share grows with altitude. At 3000 km, the chosen mosaic of six 16 mm cameras watches 6.4% of the surface-time, which is 96% of what a mosaic filling the whole usable view would achieve. Every latitude band is watched for at least 306 hours per year, and every high-latitude probe, including both poles, for at least 933 hours. The model does not include terrain shadows or stray light.

Table: Watched share of dark surface-time against altitude, for mosaics of 16 mm cameras that fill the usable view.

| Altitude | Cameras needed | Watched share | Position error at the edge |
|---|---|---|---|
| 625 km | 32 | 2.0% | 0.5 km |
| 1000 km | 24 | 3.3% | 0.6 km |
| 2000 km | 15 | 5.4% | 0.9 km |
| 3000 km | 8 | 6.6% | 1.3 km |
| 5000 km | 6 | 8.1% | 2.0 km |

# 3. Orbit Stability (S2, S3)

Earth's gravity slowly stretches high lunar orbits into ellipses. To estimate how much correction this needs, we propagated circular polar orbits at 1000–5000 km for three years, with the Moon's main gravity terms and Earth as a third body. Whenever the orbit became too elliptical, it was made circular again by a single burn, and the burns were added up. At 3000 km this cost 0–9 m/s per year depending on the orbit's orientation, and at 5000 km 7–13 m/s per year. The proposal allocates 30 m/s per year, because the model leaves out the Sun, the finer gravity field and navigation errors. Maintenance therefore does not decide the altitude. Position error and the diminishing gain in coverage do (Section 2).

The same model was used for an elliptical 300 × 3000 km orbit. Without control, its low point drops below the surface within 3–20 months. A simple controller that corrects at the next high point could not hold the low point between 250 and 350 km in any of four orientations, and in one case the low point still crossed the surface. The elliptical orbit is rejected mainly because it watches less than half as much as the circular orbit (2.7% instead of 6.4%), but the failed control is a further reason.

# 4. Imaging Access (S4)

After 2.5 years of watching, Option A lowers its orbit to 300 km and photographs the flash sites for six months. A site can be photographed when the spacecraft passes below 350 km, within 20° off-nadir as seen from the spacecraft, while the Sun stands at a suitable elevation. We tested a normal mode with the Sun 20–70° above the horizon and a low-Sun mode at 5–20°, and recorded for each site whether at least one usable pass occurs.

All equal-area sites up to 66° latitude are reachable in the normal mode (Table 3). Higher up it fails quickly, because above about 71.5° the Sun never rises 20° above the horizon. The low-Sun mode reaches every probe site up to 85° latitude, but not the poles, where the Sun never rises 5° above the horizon. Whether 3 m craters can be found under such long shadows has not been tested, so the yield counts only the normal mode. The joint model (S14) uses this access by latitude, interpolated between the rings and multiplied by a scheduling factor of 0.90 (0.80–0.95).

Table: Share of probe sites at each latitude with at least one usable imaging pass in six months at 300 km.

| Latitude | Normal mode (Sun 20–70°) | Low-Sun mode (Sun 5–20°) |
|---|---|---|
| up to 66° | 100% | 100% |
| 70° | 88% | 100% |
| 72–85° | 0% | 100% |
| 89° and the poles | 0% | 0% |

For the elliptical orbit, 49% of all sites are never reachable, including every site above 60° latitude.

# 5. Camera Count (S5)

A shorter lens sees a wider area but collects less light, because at f/1 the opening equals the focal length. We compared mosaics of 8–25 mm lenses at 3000 km using the coverage model and a fixed detection threshold that scales with the collected light. Six 16 mm cameras give the reference yield. Two 8 mm cameras would see the same area but miss the faint flashes from small craters, and give only 40% of the pairs. Four 16 mm cameras give about 70%, and fifteen 25 mm cameras slightly more than six 16 mm cameras in this simple comparison. This screen has not been rerun with the detailed detector. With that detector, the extra light of the 25 mm cameras matters much more than the screen suggests (Section 8).

# 6. Event-Camera Detector (S10)

## 6.1 Detection problem

An event camera reports brightness changes above a contrast threshold. Faint flashes must be distinguished from noise across six 921,600-pixel sensors (5,529,600 pixels in total). Detection and energy quality depend on the low-light pixel response, noise statistics, background and trigger rule.

## 6.2 Model

The model follows each pixel in steps of 0.5 ms. Photons from the background and from the flash arrive at random. The pixel converts the light into a signal that follows brightness changes with a delay, and this delay grows as the light gets fainter, up to a cap of about one second near the dark limit. Whenever the signal has changed by the contrast threshold, the pixel emits an event. In addition, each pixel produces random noise events. The flash light is spread over a small patch of pixels, with its centre at a random position.

The nominal response time of 1 ms at 5 lx is set equal to the latency McReynolds et al. (2024) measured for the IMX636. A latency is not the same as a time constant: depending on the unpublished size of the light step in that measurement, a 1 ms latency allows time constants from about 1 ms to about 30 ms. We simulated 3 ms and 10 ms; 30 ms was not simulated. The sensor has not been characterized at these light levels, so we simulated 16 sensor cases (Table 4). They bound the behaviour rather than predict it.

Table: Simulated sensor cases. Unless stated, a case keeps the nominal values.

| Case | Description |
|---|---|
| Nominal | 1 ms response at 5 lx, threshold 0.25, dark current 1 fA (cooled), random noise 0.3 events per pixel per second |
| Optimistic | 0.3 ms, threshold 0.20, 0.3 fA, 0.03 per second |
| Pessimistic | 3 ms, threshold 0.30, 5.55 fA (measured, temperature not reported), 1 per second |
| Single changes | threshold 0.30; noise 1 or 3 per second; response 3× or 10× slower; dark limit 3 s; square-root response law; dark current 5.55 fA |
| Non-standard noise | noise in bursts of about 3 events; noise that switches to ten times its rate for 10% of the time; noise rate spread between pixels by a factor of e (one standard deviation in ln) |
| 25 mm cameras | nominal and pessimistic, with fifteen 25 mm cameras in the false-alarm budget |

The on-board trigger counts events in every group of 2 × 2 and 3 × 3 neighbouring pixels over time windows of 0.05 to 2 s. A trigger requires a minimum number of events from at least three pixels, and counts at most one event per pixel per 0.5 ms step. Six full sensors evaluated this way perform about 5.3×10¹² tests per hour, so each test may produce a false trigger with a probability of only 1.9×10⁻¹³. The minimum event count for each window is computed from an upper envelope of the noise of single pixels: the simulated photon noise, at least as wide as a Poisson law at 1.5 times its mean, combined with the exact count distribution of the declared noise model at 1.5 times its rate. This gives a bound on false triggers **if** the physical noise follows the declared model with at most 1.5 times the assumed rate and the pixels are independent; it is not a bound on the physical sensor. The thresholds also allow for a moving albedo edge under earthshine in 1% of all groups, because the lunar surface drifts through the view by 0.41 pixel per second. Hot pixels are masked by a rule that was not simulated.

## 6.3 Results

Table 5 shows the result for the nominal sensor at the edge of the view, at two backgrounds. The lower one holds for 55% of the observed time, the higher one for 83%. Short flashes are detected down to about 2×10⁴ J, but flashes that fade over one second need about 10⁵ J. A long, faint flash produces only a few events per pixel spread over a long time, while noise events keep accumulating, so faint long flashes are lost first under brighter earthshine. In the pessimistic case only flashes of at least 10⁵ J that fade within 0.03 s are reliably detected at high background; in the optimistic case, everything above 2×10⁴ J. The most damaging single property is a spread of the noise rate between pixels, which forces much higher thresholds.

Table: Detections out of 40 simulated flashes for the nominal sensor at 3750 km. 40/40 corresponds to at least 91% with 95% confidence, 39/40 to at least 87%.

| Flash light energy, fading time | Background 6.5×10³ e⁻/s | Background 1.3×10⁴ e⁻/s | Background 2.5×10⁴ e⁻/s |
|---|---|---|---|
| 10⁴ J, 0.03 s | 15 | 3 | 1 |
| 2×10⁴ J, 0.03 s | 40 | 40 | 40 |
| 2×10⁴ J, 0.1 s | 39 | 29 | 2 |
| 4×10⁴ J, 0.1 s | 40 | 40 | 40 |
| 4×10⁴ J, 0.3 s | 40 | 36 | 10 |
| 10⁵ J, 1 s | 40 | 39 | 8 |
| 3×10⁵ J, 1 s | 40 | 40 | 40 |

Three further checks bound the false-alarm figure:

- **Particles.** Of 600 simulated particle hits, none triggered with the one-event-per-step rule, in every sensor case; without it, 0.5–31% did (52–62% with the square-root law). An upper bound for an assumed particle flux gives at most 0.13 false triggers per hour in most cases (0.32 for fifteen 25 mm cameras at low background), but 2.6 per hour for noise in bursts, which exceeds the budget.
- **Moving texture.** For a strong albedo edge in 1% of the groups, the expected false triggers are 0.05–0.7 per hour. If 10% of the groups contain such an edge, they rise to 0.7–7 per hour at 1.3×10⁴ e⁻/s (3.4 for the nominal sensor). A texture map of the real near side (S17) gives 0.09–0.12 per hour for the nominal sensor, within the budget.
- **Noise-only runs.** 400 noise-only pixel patches produced no false trigger, and no detection occurred before a flash started. These runs cannot test a 10⁻¹³ tail directly.

The trigger fires 7–166 ms after the true flash start (median, longest for faint one-second flashes), but the flash start itself is estimated from the first event of the triggering group with a median error of 0.7–24 ms and a 90th percentile of at most 30 ms. A constant background light inside the camera, used for calibration, reduced detection in every sensor case, so it is used only for short calibration steps. The main limitations of the model are the simple pixel without a refractory period, noise events that are positive only, independent pixels, and assumed particle rates. Texture statistics are now checked with measured maps (S17). A trigger that also uses the dimming events at the end of a flash, and thresholds set from per-pixel noise maps, were not tested.

# 7. Energy Calibration (S11)

The flash energy is reconstructed from the events alone. The flash start is taken as the first event of the triggering group, the end as the moment when all pixels have returned to their earlier level, and the background level is measured with an error of 5%. This raw estimate is biased, and the bias depends on the flash duration. We therefore learned a correction from 1800 simulated flashes, each drawn with its own range and earthshine from the actual observing opportunities, using only quantities that can be measured in each flash. We then tested it on conditions it had not seen (Table 6).

Table: Energy error of detected flashes after correction.

| Test case | Bias | Random error |
|---|---|---|
| Same kind of flashes as in training | 0% | 21% |
| Flash with a fast and a slow part (not trained) | −2% | 19% |
| Flash with a long tail (not trained) | 0% | 20% |
| Bright earthshine only | 0% | 24% |
| Pixel twice as slow, threshold higher, thresholds adapted (not trained) | −2% | 20% |
| Same, with the nominal thresholds (undetected drift) | −2% | 19% |
| Random pixel history before the flash | 0% | 22% |
| Warm sensor, nominal correction | −14% | 33% |
| Warm sensor, correction retrained | +1% | 32% |
| Noise that also produces dimming events, nominal correction | +20% | 22% |
| Same, correction retrained | −1% | 14% |

The correction is robust to flash shapes, a mismatched or drifting sensor and the pixels' history: the bias stays within about 2% and the random error near 20%. Bright earthshine raises the error to 24%. Sorted by flash duration and background, the bias is close to zero except for flashes longer than 0.3 s under bright earthshine, which are overestimated by about 11%; this condition table is passed to the fit (S14). A warm sensor has a larger error even after retraining, so its scatter is physical. Noise that also produces dimming events biases the correction by about 20% unless it is retrained for that noise. The correction must therefore be trained on the sensor's measured state in flight. The 10–11% of revision 3 came from a test that used the true flash start and duration and is withdrawn.

# 8. Observed Background (S13)

On the near side, earthshine adds a natural background to the night-side view. We computed it from the reflected sunlight of a full Earth (about 0.075 W/m², following Glenar et al. 2019), the share of sunlight in the 600–900 nm band, the reflectance of the lunar surface and the camera's light collection. A full Earth gives about 1.85×10⁴ electrons per second in each pixel, roughly three times the dark current of a cooled sensor. The background was then recorded along every actual observing opportunity of the coverage model. Half of the observed dark time is on the near side. The earthshine exceeds 10⁴ electrons per second in only 9% of the observed time, and its 99th percentile is 1.6×10⁴. Near-side nights do not always come with a full Earth: the Earth phase angle at observed near-side points ranges from 9° to 125° (10th to 90th percentile). The viewing range lies between 3080 and 3650 km for 80% of the observations. These distributions are used directly in the energy calibration and the joint model.

# 9. Joint Model: Yield and Precision (S14)

## 9.1 One population for yield and fit

The yield and the scientific precision are computed from the same simulated population of 400,000 impacts. Flash energies follow a power law whose slope makes the crater sizes follow the same distribution as LRO's crater count. Crater sizes follow the assumed relation, with a slope of 0.30 and a scatter of 0.25 in log size. Flash durations lie between 0.03 and 1 s. Range, latitude and earthshine are drawn together from the observing opportunities of Section 8. The population is scaled so that it produces 184 new craters larger than 10 m per year over the whole Moon, the count of Speyerer et al. (2016) as re-derived by Cheng & Scolnic (2026). The scaling is now computed analytically; Every impact then passes through the same selection in yield and fit:

- its flash must be detected (Section 6);
- its crater must be confirmed, with a probability that reaches at most 85% and is 42.5%, half of that maximum, at 3.15 m. The tests on real images (S18) confirm the 3.15 m point; the maximum depends on image registration;
- its site must lie in the image (95%), be reachable at its latitude (Section 4) and have a suitable archive image (80%);
- its error region must contain exactly one confirmable new crater.

The last step is the association rule. Unrelated confirmable craters form at about 2×10⁻⁴ per km² per year, accumulated over a 20-year archive. A true pair is lost when a second candidate lies in the error region. A site whose own crater is too small but which happens to contain one unrelated crater becomes a false pair. A Monte Carlo varies the uncertain factors 4000 times. The sensor cases are run as separate scenarios, because we have no basis to assign them probabilities. A stress test moves all non-sensor factors together to show the effect of correlated errors. Because the factor ranges lean towards the unfavourable side, the median lies below the yield at nominal factors (294 pairs for the nominal sensor); all quoted yields are medians.

## 9.2 Yield

Table 7 shows the Option A yield for every sensor case. For the nominal sensor, the cameras detect 62% of the flashes from confirmable craters, and the median is 210 pairs in 2.5 years. Every case has a median above the minimum of 30 pairs; the pessimistic case reaches it with a probability of 0.98. Fifteen 25 mm cameras, simulated with their own false-alarm thresholds, raise the nominal median to 272 pairs and the pessimistic one to 142. Imaging from 150 km instead of 300 km would give about 1.7 times more pairs for the nominal sensor (1.0–4.6 across the cases), because many of the extra small craters come with flashes that are too faint to detect.

Table: Option A pairs in 2.5 years by sensor case (medians).

| Sensor case | Flashes detected (confirmable craters) | Median pairs | 10th percentile | Chance of ≥80 |
|---|---|---|---|---|
| Square-root response law | 93% | 284 | 150 | 0.99 |
| Optimistic | 93% | 284 | 147 | 0.99 |
| Noise in bursts | 67% | 219 | 122 | 0.98 |
| Nominal | 62% | 210 | 117 | 0.98 |
| Dark limit 3 s | 62% | 209 | 119 | 0.98 |
| Threshold 0.30 | 57% | 194 | 111 | 0.97 |
| Switching noise | 54% | 183 | 107 | 0.97 |
| Noise 1 per second | 52% | 177 | 102 | 0.96 |
| Response 3× slower | 50% | 170 | 97 | 0.95 |
| Response 10× slower | 48% | 165 | 95 | 0.95 |
| Dark current 5.55 fA | 47% | 163 | 95 | 0.95 |
| Noise 3 per second | 44% | 153 | 89 | 0.93 |
| Noise spread between pixels | 30% | 108 | 64 | 0.78 |
| Pessimistic | 20% | 75 | 45 | 0.43 |

For the nominal sensor, Option C gives 55, 140 and 224 pairs if 20, 50 and 80% of the sites can be imaged externally, and 51 pairs at 50% for the pessimistic sensor. The elliptical orbit gives 59 pairs. Watching for only 1.5 years gives 125 pairs. When all factors move together, the median is 222 but the 10th percentile drops to 56 pairs; with the pessimistic sensor as well, the median is 78, the 10th percentile 26, and the chance of at least 30 pairs 0.88. If every factor sits at its worst value at once, 6–28 pairs remain, depending on the sensor and the assumed crater rate. About 0.7% of the pairs (about 2) are false associations for the nominal sensor. The pairs lie 48% on the near side and 52% on the far side, and 17% above 60° latitude. The mission would also catalogue about 1200 detected flashes and locate about 730 crater-forming sites (about 220 and 210 for the pessimistic sensor). Bootstraps over the population and over the detection tables change the yield by at most 2.6%.

## 9.3 Precision of the fitted relation

We fitted 60–120 simulated samples each of 30, 80 and 240 pairs with a likelihood that describes how the sample was selected. For each pair it accounts for the unknown true flash energy, the probability that this flash was detected at its range and measured duration and background, the crater confirmation and the measurement errors. The energy errors follow the condition table of S11, plus 5% per camera and 10% common to the mission. The fit includes the small fraction of false pairs, and the detected flashes that are not paired constrain the distribution of flash energies. We also fitted an adverse scenario with the pessimistic sensor, a 33% energy error and the long-flash bias. The results are shown in Table 8.

Table: Recovery of the relation in simulated samples (true slope 0.30, true scatter 0.252). Sizes and conversions are multiplicative 1σ ranges.

| Scenario | Pairs | Slope (mean ± spread) | Scatter (mean ± spread) | Mean crater size at 30 kJ | Crater-rate conversion at 10 kJ |
|---|---|---|---|---|---|
| Nominal | 30 | 0.286 ± 0.054 | 0.236 ± 0.052 | +11/−10% | +60/−38% |
| Nominal | 80 | 0.304 ± 0.029 | 0.254 ± 0.034 | +7/−6% | +34/−25% |
| Nominal | 240 | 0.299 ± 0.015 | 0.252 ± 0.018 | ±4% | +19/−16% |
| Adverse | 30 | 0.299 ± 0.050 | 0.238 ± 0.051 | +14/−12% | +78/−44% |
| Adverse | 75 | 0.297 ± 0.032 | 0.239 ± 0.029 | +9/−8% | +45/−31% |

The fit recovers the slope with a bias of at most 0.004 at 80 and 240 pairs and −0.014 at 30 pairs. Leaving out the detection probability would bias the slope by +0.07, to about 0.37, so this term is essential; leaving out the false pairs changes the bias only to −0.008. The uncertainty that the fit reports for itself is too small for 30 pairs (it contains the true value in only 50% of samples, instead of 68%) and conservative for 240 pairs. A real analysis must therefore calibrate its uncertainties by simulation, and the proposal quotes the spread over samples. The value at 10 kJ is an extrapolation below the paired sample. Revision 4 had quoted symmetric ranges that were in fact the upper deviations.

Two further results are used in the proposal. First, the analytic precision formulas used for Figure 4 of the proposal agree with an unselected simulation to within 3% (S7). Second, within ten years an unrelated new crater large enough to confirm appears inside our 1.3 km error region with a probability of only 1%, against 75% inside a 15 km ground-based search region.

# 10. Supporting Calculations (S6, S8, S9, S15)

**Ground-based alternatives (S6).** The ground-based yields use a simpler chain of factors. Ground telescopes with LRO give about 0.24 pairs per year, about three times lower than the historical rate, so this comparison is, if anything, unfavourable to the ground. An imaging orbiter that follows up ground flashes gives about 5 per year. A forward-looking scenario of several ground networks in 2031–2035 that locate flashes to 3 km and buy 0.9 m-class images for half of the sites gives about 2.5 (1.2–5.1) pairs per year. Its inputs are our assumptions, not a forecast.

**Localization (S8).** The position error combines a centroid error of 0.1 pixel, an attitude knowledge of 48 µrad and an orbit error of 150 m. From 3000 km this gives 0.56 km straight below the spacecraft and 1.28 km at the edge of the view (95%). A clock error of 10 ms and the estimated flash start (at most 30 ms off for 90% of flashes) add at most 0.02 km.

**Crater camera (S8).** At 300 km the ground moves at 1.32 km/s, so an exposure of at most 0.34 ms keeps image smear below half a pixel. For sunlit lunar soil at 20–30° Sun elevation this gives about 250–370 electrons per pixel, a signal-to-noise ratio of about 15–20. This is comparable to the camera's design case in Earth orbit. A full image-quality analysis is still to be done.

**Capture (S9).** For an arrival speed of 0.8 km/s, capture into the 3000 km orbit costs 629 m/s. Split into two burns via a 10,000 km ellipse, the first burn of 432 m/s takes about 15 minutes with 88 N of total thrust and loses about 1.7 m/s to steering. A single 22 N engine would need an hour and lose about 29 m/s, so about 90 N of thrust is required.

**Spacecraft budget (S15).** A first bottom-up estimate gives a dry mass of 118 kg for Option A and 77 kg for Option C, or about 190 and 102 kg at launch with bipropellant propulsion. Average power is about 91 W while watching and 99 W while imaging. In the 300 km imaging orbit the Moon shadows the spacecraft for up to 45 minutes of each 138-minute orbit, so this phase sizes the solar array at about 190 W (0.72 m²), against 130 W for the watching phase alone; array, battery and power unit come to about 8.6 kg, within the 13 kg allocation. The battery of about 250 Wh is sized by a four-hour lunar eclipse. Background noise alone sends about 0.7–22 MB/s of raw events into the on-board processor, but only short flash records are stored. For the phase-2 images we size for 880 sites (about 730 are predicted for the nominal sensor): 176 GB in six months, or about 90 kbit/s on average. A 5 W X-band link with a 0.3 m antenna reaches about 2.4 Mbit/s while in contact, so this needs about 0.9 hours of contact per day before overheads. All values are allocations, not a subsystem design.

# 11. Follow-up Tests with Measured Data (S16–S18)

**Event-sensor trade (S16).** Five new sensor cases are built from published IMX636 measurements (McReynolds et al., AMOS 2025):

- dark current 1.1 fA;
- a fast photoreceptor (τ_ref ≈ 0.27 ms);
- 0.03 noise events per pixel per second at default settings;
- the noisiest 2% of pixels masked.

On one Monte Carlo stream, the measured IMX636 detects 81% of the flashes from confirmable craters, against 62% for the revision-5 nominal sensor. Its median is about 260 pairs, against 205; with fifteen 25 mm cameras it reaches 296. The trade recommends:

- the IMX636 with default settings;
- a cooling requirement of a dark current of at most 1.5 fA (to be confirmed);
- six 16 mm cameras.

The revision-5 numbers stay the reference; the trade shows that they are conservative.

**Measured lunar texture (S17).** A texture map of the near side was built from the LRO WAC 643 nm albedo mosaic and LOLA topography. The map has 0.9 km pixels lit by earthshine and drifting at 0.41 pixels per second. A slow, smooth brightening makes a pixel fire almost deterministically: a pixel-model simulation gives a count variance of 0.08–0.27 times the mean, far below Poisson. With the adopted thresholds the measured texture gives 0.09–0.12 false triggers per hour for the nominal sensor and up to 0.95 for the measured IMX636 under the brightest earthshine. Only the IMX636 with tuned biases exceeds the budget, at 9.6 per hour, and needs higher 2 s thresholds. Raising thresholds where needed costs no simulated detections and leaves the yield unchanged.

**Crater tests on real LRO images (S18).**

- **Injected craters.** Synthetic fresh craters were injected into four real NAC tiles and degraded to the crater camera. 50% are found at 3.58 pixels (3.2 m); the diameter error is about 0.46 pixels divided by the crater size in pixels.
- **Real new craters.** The 3.2, 4.0 and 6.2 m craters, in their real before/after image pairs, were found every time when the pair was registered to about 0.1 NAC pixel. Where registration was poorer, the false-alarm threshold doubled.
- **Dark halos.** Four of the five located craters have dark halos. A detector for reflectance changes of either sign finds them; the original bowl-shading filter does not.
- **Injection with dark halos.** Craters of this type, injected into the real pairs, reach 50% at 3.63 pixels (3.3 m), with a width of 0.21. The plateau is 1.0 in well-registered pairs and 0.68 over all usable pairs. This changes the nominal yield by −6% to −31%.

The placeholder curve is kept, and registration to about 0.1 NAC pixel becomes a pipeline requirement.

**Secondary objectives.** The proposal's secondary objectives, the whole-Moon flash-energy rate and the leading/trailing asymmetry, are not yet simulated. A first estimate gives the asymmetry at about 2.4σ with the nominal catalogue of about 1200 flashes and about 3.8σ with the measured IMX636.

# 12. Limitations

The simulations share several limitations. The Moon is a smooth sphere without terrain shadows or libration. The orbit runs include only the Moon's main gravity terms and Earth, with ideal burns. The event-sensor model is a first-order description with bounded parameters, not a calibrated model of a real sensor, and its false-alarm figure holds for a declared noise model and independent pixels. The flash population, the crater scatter, the confirmation limit and the extrapolation of the crater count below 10 m are assumptions with stated ranges. The fit's own error bars are not yet calibrated, and the calibration offsets are not fitted as separate parameters. Subsystem designs, mission reliability and cost were not simulated, and the crater-detection pipeline only in a first form. The two assumptions with the largest effect on the results, the low-light behaviour of the sensor and the confirmation of 3 m craters, have now been tested in a first form with published sensor data and real LRO images (S16, S18). Neither replaces a flight characterization or a test with the actual crater camera.

# 13. Reproduction

All scripts run from `analysis/impact_energy_conversion/` and write to `data/impact_energy_conversion/` and `figures/impact_energy_conversion/`. The order is:

1. `coverage.py`, `orbit_stability.py`, `orbit_trades.py` and `imaging_access_check.py --one-season` (geometry and orbits, about 1.5 hours in total);
2. `observed_background.py`, `event_response.py`, `photometry_calibration.py` and `joint_model.py` (detector and joint model, about 3.5 hours on one core; the detector can run in parallel parts);
3. `science_model.py`, `system_budget.py` and `transfer.py` (figures and budgets, about one minute);
4. `build_report.py` with no argument, `simulation`, `comments`, `comments1`, `comments2`, `summary` or `simsummary` (PDFs; needs pandoc and XeLaTeX);
5. for S16–S18: `sensor_trade.py`, `texture_map.py` (on the team computer) with `texture_measured.py`, and the crater-test kit's `real_tiles/` and `real_pairs/` scripts (see the full report).


