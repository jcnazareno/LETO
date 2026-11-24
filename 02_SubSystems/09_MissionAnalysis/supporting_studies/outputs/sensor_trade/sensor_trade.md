---
title: "Event-Sensor Trade: IMX636 versus IMX646, Cooling and Camera Heads"
subtitle: "Pre-SRR work item 1 for the impact-energy conversion proposal (3 November 2026)"
---

> This study closes the first pre-SRR work item of the flash–crater proposal (section 11, risk 2) as far as published data allow. It builds new sensor cases from measured IMX636 low-light data, runs them through the same detector and yield models as revision 5 (simulation report, S10 and S14), and derives the sensor choice, a cooling requirement and the camera-head decision. Scripts: `analysis/impact_energy_conversion/event_response.py` (version 4 cases) and `sensor_trade.py`; data: `data/impact_energy_conversion/event_response.json` and `sensor_trade.json`. The revision-5 results are unchanged: `joint_model.py` is pinned to its 16 cases, and the trade reproduces its deterministic yields exactly.

# 1. Summary

The revision-5 sensor envelope was built from assumed parameters, because no low-light data had been included. A 2025 laboratory characterisation of the IMX636 (McReynolds et al., AMOS 2025) now provides its dark current, the photoreceptor's corner frequency at two light levels, the background noise at default biases and the distribution of hot pixels. With these values the event cameras detect **81% of the flashes from confirmable craters, against 62% in the revision-5 nominal case**. The median yield of Option A rises from about 205 to **about 260 pairs** in 2.5 years (same Monte Carlo stream).

Recommendations:

1. **Sensor: IMX636 as the baseline, IMX646 as a characterised option.** The IMX636 is the only one of the two with published data at our light level. The IMX646 is specified to darker scenes, but no low-light data exist; a surrogate case gains only about 5%. Both have the same package, pixel array, supplies and interfaces on their data sheets, so the choice can be revisited without changing the camera design.
2. **Operating point: default biases.** Lowering the thresholds ("tuned" biases) adds about 5% to the yield but multiplies the noise events by about 30 and the detected-flash catalogue by 1.7. It remains an in-flight option.
3. **Cooling: a requirement of dark current ≤1.5 fA (TBC), met by a passive radiator.** A warm sensor (5.55 fA) costs only 9% of the yield with the measured pixel speed. However, it lowers the trigger thresholds enough that the upper bound on particle-induced false triggers reaches about 10 per hour, ten times the budget. Cooling therefore protects the false-alarm budget more than the yield. A particle veto would be the alternative.
4. **Camera heads: six 16 mm heads.** Fifteen 25 mm heads add only 14% with the measured sensor (296 against 260 pairs). That gain does not justify about 8 kg, 13 W and nine more heads to calibrate. Keep the 25 mm design as the fallback if the flight sensor's characterisation lands near the revision-5 pessimistic case.

**Effect on the proposal.** We recommend keeping the revision-5 numbers as the reference. The new cases rest on one sensor unit measured at an unreported temperature and on a unit conversion (section 2.1). The trade shows that the revision-5 nominal case is conservative and that the sensor part of the stop rule is likely to be met: every measured-sensor case has a median above 230 pairs and a 10th percentile above 55 pairs, even with the dependence stress. The stop rule as a whole still needs the crater-injection test.

# 2. Evidence

Table 1 lists the published values used. None of them is a full characterisation at our light level (a few thousand electrons per second per pixel), and the temperature of the laboratory measurements is not reported.

Table: Published event-sensor values used in this trade.

| Quantity | IMX636 | IMX646 | Source |
|---|---|---|---|
| Pixel, format | 1280 × 720, 4.86 µm | 1280 × 720, 4.86 µm | Sony flyers (2025) |
| Contrast threshold, default | 25% typical, non-uniformity ≤6% (1000 lx) | 25% typical, ≤6% (1000 lx) | Sony flyers |
| Latency (maximum) | 100 µs at 1000 lx; 1 ms at 5 lx | 800 µs at 1000 lx; 9 ms at 0.3 lx | Sony flyers |
| Background rate (maximum) | 0.1 Hz at 1000 lx; 10 Hz at 5 lx | 0.1 Hz at 1000 lx; 5 Hz at 0.3 lx | Sony flyers |
| Lowest specified illumination | 5 lx | 0.3 lx (dynamic range >110 dB, 30 mlux–100 klux) | Sony flyers; Prophesee IMX646 page |
| Dark current | 5.55 fA (2024); 1.1 ± 0.5 fA (2025) | not published | McReynolds et al. 2024; 2025 |
| Photoreceptor corner frequency | 6.49 Hz at 13.3 fA photocurrent; 0.55 ± 0.2 Hz at the dark limit | not published | McReynolds et al. 2025 |
| Background activity, default biases | ≈0.03 Hz per pixel (scene below the dark limit) | not published | McReynolds et al. 2025 |
| Background activity, tuned biases | ≈1 Hz per pixel, with ON thresholds 0.05–0.15 | not published | McReynolds et al. 2025 |
| Hot pixels | ≈2% of pixels carry >99% of the excess events (tuned biases) | not published | McReynolds et al. 2025 |
| Space heritage | an IMX636-class payload (Falcon ODIN) was planned for the ISS in late 2024; no on-orbit results found | none found | Prophesee; SPIE 2024 |

The related DAVIS 240C sensors have operated on the ISS (Falcon Neuro) since January 2022; by September 2024 only one of 18 measures showed a convincing degradation trend (Wilcox et al. 2025). This is a different sensor generation. It shows that event sensors can survive low Earth orbit, not how the IMX636 will age.

## 2.1 What the evidence changes

1. **Response speed.** A first-order pixel with corner frequency f has the time constant τ = 1/(2πf). The two measured corners (6.49 Hz at 13.3 fA, 0.55 Hz at 1.1 fA) scale with the photocurrent almost exactly: a ratio of 11.8 for a current ratio of 12.1. This supports the **linear current law** of our nominal model. Scaled to our reference current (7.5×10⁶ e⁻/s), they give **τ_ref ≈ 0.27 ms**, about four times faster than our nominal 1 ms and close to our optimistic 0.3 ms. At the dark limit the measured corner gives τ ≈ 0.29 s, so our 1 s cap is not reached. The conversion assumes that the photocurrent quoted by McReynolds et al. corresponds to our electron rates (13.3 fA = 8.3×10⁴ e⁻/s). It is the main uncertainty of the new cases.
2. **Dark current.** The 2025 measurement (1.1 ± 0.5 fA) supports our nominal 1 fA. The 2024 value (5.55 fA) remains possible for a warmer sensor or another unit. Neither measurement reports the temperature.
3. **Background activity.** At default biases the measured rate (0.03 Hz) equals our optimistic value. Lower thresholds (tuned biases) raise the sensitivity but also the noise, to about 1 Hz.
4. **Noise between pixels.** The measured noise is concentrated in a few hot pixels. Our most damaging revision-5 case (a lognormal spread over all pixels, σ = 1) puts only about 15% of the noise in the top 2% of pixels, so it describes a different and less treatable situation. With a hot-pixel mask the remaining pixels are far more uniform. The spread that remains is not published: we assume a lognormal σ = 0.5 and mask the noisiest 2%. Masked pixels deliver no events, which also costs a little signal.
5. **IMX646.** No low-light characterisation is published. Its data sheet is specified to a 17 times lower illumination than the IMX636's, with a lower maximum background rate there. This suggests a pixel tuned for darkness at the cost of speed in bright light. Our flashes last 30 ms or longer, so the slower bright-light latency does not matter. We represent it only by a **surrogate** case with half the IMX636's time constant; this is an illustration, not a measurement.

# 3. Cases

Table 2 lists the five new cases. Everything not listed is as in revision 5: six heads with 16 mm f/1 lenses, the same trigger, false-alarm budget, texture allowance and joint model.

Table: Sensor-trade cases (event_response.py, version 4).

| Case | τ_ref | Threshold C | Dark current | Background activity | Pixels | Heads |
|---|---|---|---|---|---|---|
| m636 (measured IMX636) | 0.27 ms | 0.25 | 1.1 fA | 0.03 Hz, σ 0.5, 2% masked | as revision 5 | 6 × 16 mm |
| m636_tuned | 0.27 ms | 0.10 | 1.1 fA | 1 Hz, σ 0.5, 2% masked | | 6 × 16 mm |
| m636_warm | 0.27 ms | 0.25 | 5.55 fA | 0.03 Hz, σ 0.5, 2% masked | | 6 × 16 mm |
| m636_25mm | 0.27 ms | 0.25 | 1.1 fA | 0.03 Hz, σ 0.5, 2% masked | | 15 × 25 mm |
| m646_surrogate | 0.135 ms | 0.25 | 1.1 fA | 0.03 Hz, σ 0.5, 2% masked | | 6 × 16 mm |

One modelling simplification is conservative. With 1.1 fA the dark level (6.9×10³ e⁻/s) lies above the lowest grid background (6.5×10³ e⁻/s), so the darkest conditions, mostly the far side, are evaluated at the next grid point (1.3×10⁴ e⁻/s). The warm case starts at 4×10⁴ e⁻/s for the same reason.

# 4. Results

## 4.1 Detection

Table 3 compares the detections with the revision-5 nominal case at the two grid backgrounds that matter most. The measured IMX636 detects nearly everything above 2×10⁴ J that fades within 0.3 s at 1.3×10⁴ e⁻/s, where the nominal case lost the slow flashes. It still loses faint flashes lasting a second (4×10⁴ J, 1 s) under brighter earthshine.

Table: Detections out of 40 at 3750 km.

| Flash light energy, fading time | nominal 1.3×10⁴ | m636 1.3×10⁴ | m636 2.5×10⁴ | m636_tuned 2.5×10⁴ | m646_surrogate 2.5×10⁴ | m636_25mm 2.5×10⁴ |
|---|---|---|---|---|---|---|
| 10⁴ J, 0.03 s | 3 | 40 | 40 | 40 | 40 | 40 |
| 2×10⁴ J, 0.1 s | 29 | 40 | 40 | 40 | 40 | 40 |
| 2×10⁴ J, 0.3 s | 0 | 40 | 14 | 40 | 39 | 40 |
| 4×10⁴ J, 0.3 s | 36 | 40 | 40 | 40 | 40 | 40 |
| 4×10⁴ J, 1 s | 0 | 33 | 0 | 30 | 6 | 38 |
| 10⁵ J, 1 s | 39 | 40 | 39 | 40 | 40 | 40 |

The trigger thresholds fall with the lower noise, for the measured IMX636 at 1.3×10⁴ e⁻/s to 7, 10, 15 and 22 counts (2 × 2 groups) for the four windows, against 9, 12, 20 and 31 nominally. The tuned biases need much higher thresholds (12–64), because their noise is 30 times larger, and still detect more. The onset-time error stays within D02 for all new cases: median 0.6–17 ms, 90th percentile at most 27 ms.

## 4.2 False-alarm checks

The checks of revision 5 were repeated for each new case (Table 4). The one-event-per-step rule again rejected all 600 simulated particle hits in every case.

Table: False-alarm checks (expected false triggers per hour over all heads; budget below 1).

| Case, background | Particle upper bound | Texture, edge in 1% of groups | Texture, edge in 10% of groups |
|---|---|---|---|
| nominal (revision 5), 1.3×10⁴ | 0.13 | 0.39 | 3.4 |
| m636, 1.3×10⁴ | <0.001 | 0.18 | 1.8 |
| m636_tuned, 1.3×10⁴ | <0.001 | 0.14 | 1.1 |
| m636_25mm, 1.3×10⁴ | 0.001 | 0.26 | 2.6 |
| m646_surrogate, 1.3×10⁴ | <0.001 | 0.18 | 1.8 |
| **m636_warm, 4×10⁴** | **10** | 0.10 | 1.0 |

The warm case exceeds the budget. Its higher dark current shortens the pixel time constant (linear law) and smooths the shot noise. That lowers the thresholds to 6–15 counts, and the upper bound assumes that every particle hit adds its maximum count to every group and window it touches. The bound is pessimistic, but it cannot be dismissed without a better particle model. Two remedies exist: cooling, or a veto on groups whose pixels all turn on in the same 0.5 ms step (a particle deposit is instantaneous, while a flash rises through the photoreceptor over several steps). The veto is not yet simulated.

## 4.3 Yield

Table 5 gives the Option A yields. All cases use one Monte Carlo stream, so the revision-5 cases differ from the proposal by up to 2–3% (for example 205 instead of 210 nominal). Their deterministic yields agree with `joint_model.json` exactly.

Table: Option A pairs in 2.5 years (medians; stress: all non-sensor factors moving together).

| Case | Flashes detected (confirmable craters) | Median | 10th percentile | Chance of ≥80 | Stress median | Stress 10th percentile | Located sites |
|---|---|---|---|---|---|---|---|
| nominal (revision 5) | 62% | 205 | 118 | 0.98 | 222 | 55 | 732 |
| pessimistic (revision 5) | 20% | 74 | 46 | 0.41 | 82 | 27 | 206 |
| warm_dark (revision 5) | 47% | 161 | 94 | 0.95 | 177 | 47 | 558 |
| noise spread per pixel (revision 5) | 30% | 109 | 66 | 0.79 | 120 | 34 | 350 |
| nominal, 15 × 25 mm (revision 5) | 82% | 274 | 145 | 0.99 | 291 | 68 | 882 |
| **m636** | **81%** | **260** | **139** | **0.99** | **285** | **62** | 835 |
| m636_tuned | 88% | 273 | 144 | 0.99 | 296 | 66 | 855 |
| m636_warm | 74% | 237 | 129 | 0.99 | 256 | 58 | 769 |
| m636_25mm | 92% | 296 | 151 | 0.99 | 323 | 72 | 903 |
| m646_surrogate | 86% | 274 | 143 | 0.99 | 295 | 67 | 841 |

The gains are smaller in pairs than in detected flashes, because the yield is limited mostly by crater confirmation, imaging access and the archive, not by the cameras. The catalogue of detected flashes grows more, from about 1,200 (nominal) to about 3,000 (m636) and 5,100 (tuned). All six-head cases stay within the 880-site downlink allocation; the 25 mm variant (903 sites) would exceed it by about 3%.

# 5. Decisions

## 5.1 IMX636 or IMX646

The IMX636 is the baseline. It is the only candidate with published data at our light level, and with those data the concept gains margin. The IMX646 could be better in darkness, but its advantage is unquantified, and the surrogate's +5% lies inside the uncertainty of the IMX636 cases. Since both sensors share the package, array and interfaces on their data sheets, the choice does not constrain the camera design. A low-light characterisation of the IMX646 (dark current, corner frequency, background activity) would decide whether to switch.

## 5.2 Cooling requirement

We propose: **"The event sensors shall operate at a temperature at which the dark current is ≤1.5 fA (TBC)."** The value is the measured 1.1 fA plus about one standard deviation of that measurement.

- **Why.** A warm sensor costs about 9% of the yield (237 against 260 pairs). It also pushes the particle false-trigger bound to about 10 per hour, unless a coincident-onset veto is added.
- **How.** The temperature behind 1.1 fA is not reported, and the often-quoted halving of dark current for every 6–7 °C is not an IMX636 calibration. The requirement is therefore stated as a dark current, to be converted into a temperature once a temperature series exists. A passive radiator on the camera bracket, away from the Sun and the Moon's thermal emission, is the intended design; no thermal analysis has been done yet.
- **Status.** This replaces the revision-5 wording (dark current ≤1 fA, pending data). The requirement keeps margin; it is not a feasibility gate, which agrees with our review pushback P2.

## 5.3 Six 16 mm or fifteen 25 mm heads

Six 16 mm heads remain the baseline. With the measured sensor the 25 mm heads add 14% (296 against 260 pairs), compared with 34% in the revision-5 nominal case and 91% in the pessimistic one. Against that stand about 8 kg, 13 W, nine more heads to align and calibrate, and a site count above the downlink allocation. **Decision rule:** switch to the 25 mm design if the characterisation of the flight sensor gives a six-head median below about 150 pairs or a chance of ≥80 pairs below 0.9. That point lies between the revision-5 warm case (161 pairs, 0.95) and its noise-spread case (109 pairs, 0.79). In revision 5 the 25 mm heads added 34% to the nominal case and 91% to the pessimistic one.

## 5.4 Bias settings

Default biases are the baseline. Tuned biases improve detection of faint slow flashes (Table 3) and add about 5% of pairs. The price is 30 times more noise events into the processor (about 20–25 MB/s of raw events for six sensors at 1 Hz) and 1.7 times more flash records. They remain an in-flight option, which the camera can select without hardware changes.

# 6. Limitations

- **One unit, unknown temperature.** The measured values come from one IMX636 in one laboratory set-up, with an unreported temperature.
- **Unit conversion.** The photocurrent-to-electron conversion behind τ_ref = 0.27 ms is an assumption.
- **Pixel spread.** The noise spread among the unmasked pixels (σ = 0.5) is assumed.
- **IMX646.** The IMX646 case is a surrogate, not a measurement.
- **Model scope.** All results use the revision-5 detector, trigger and joint model, with their own limitations (simulation report, S10 and S14).
- **Conservative grid.** The grid evaluates the darkest backgrounds at 1.3×10⁴ e⁻/s, which is conservative for the measured sensor.
- **Not simulated.** The coincident-onset particle veto, per-pixel thresholds from flight noise maps and radiation ageing of the dark current and hot pixels.

**Next steps.**

1. Ask the authors of the 2025 characterisation, or the vendor, for the measurement temperature and for a dark-current temperature series.
2. Characterise the IMX646 at our light level, or obtain its data.
3. Add the coincident-onset veto to the trigger model and recompute the warm case.
4. Re-baseline the proposal's sensor envelope once the flight sensor's characterisation exists.

# References

- McReynolds B. et al. (2024), *Re-interpreting the step-response probability curve to extract fundamental physical parameters of event-based vision sensors*. [arXiv:2404.07656](https://arxiv.org/abs/2404.07656)
- McReynolds B. et al. (2025), *Bias and denoising techniques to improve dim RSO detection with event-based sensors*, AMOS 2025. [PDF](https://amostech.com/TechnicalPapers/2025/SDA_Systems-and-Instrumentation/McReynolds1.pdf)
- Sony Semiconductor Solutions (2025), [IMX636-AAMR-C flyer](https://www.sony-semicon.com/files/62/flyer_industry/IMX636-AAMR-Flyer.pdf) and [IMX646-AAMR-C flyer](https://www.sony-semicon.com/files/62/flyer_industry/IMX646-AAMR-Flyer.pdf)
- Prophesee, [IMX646 sensor page](https://prophesee.ai/event-based-sensor-imx646-sony-prophesee)
- Wilcox Z. et al. (2025), *Event-based vision sensor lifetime degradation in low Earth orbit*, Sensors 25(21), 6599. [Record](https://researchers.westernsydney.edu.au/en/publications/event-based-vsion-sensor-lifetime-degradation-in-low-earth-orbit/)
- Falcon ODIN payload description, [Prophesee](https://www.prophesee.ai/2025/02/20/falcon-odin-an-event-based-camera-payload/) and [SPIE 2024](https://electronicimaging.spiedigitallibrary.org/conference-proceedings-of-spie/13149/1314914/Falcon-ODIN-an-event-based-camera-payload/10.1117/12.3027694.full)
