# Radiation and In-Orbit Evidence for the Event Camera

*Supporting note to the [event-stream results](event_stream_sim.md), 12 November 2026. Literature review of event-sensor flight and radiation tests, plus model stress runs. Simulations are predictions under their recorded configurations; the proposed items are for team decision (TBR).*

## 1. Summary

- **Flight heritage.** Two DAVIS240C event sensors operated outside the ISS (Falcon Neuro) from January 2022 until decommissioning in August 2025. No latch-up or burnout appeared in the data. The hot-pixel count stayed constant over the mission, although some hot pixels are attributed to radiation bit flips. One of 18 noise measures degraded: row/column bursts in the nadir camera. No IMX636 has published flight data or a published radiation test.
- **Dose.** Two 180 nm event sensors (DAVIS346, Prophesee PPS3MVCD) developed functional problems above about 30 krad(Si), with background activity rising with dose. After 20 krad(Si) of protons, a DAVIS346 showed +70% dark current and +23% dark event noise; one unit locked up and recovered after a power cycle. The project's dose study gives about 4.3 krad(Si)/year behind 2.54 mm Al for the distant-lunar case ([radiation study](../../supporting_studies/outputs/radiation_environment_research_2026-10-29/radiation_environment_research.md)), so 3 years is roughly 13 krad, or 26 krad with a factor-2 margin.
- **Particle hits are the main open risk for the false-alarm budget.** Neutron tests show real sensors respond to a hit with multi-pixel clusters (about 30 px at normal incidence on a 15 µm pitch), long streaks at grazing angles, and about 3 ON events per OFF event. The model deposits charge in the crossed pixels only. In the stress runs, spreading the charge sideways by 0.5–2 px made 1–2% of hits trigger, which scales to roughly 190–370 false candidates per array-hour at the GCR solar-minimum rate. Even with no spread, 0 triggers in 1070 simulated hits only bounds the rate below about 53 per array-hour (95%). An on-board particle veto (results-note item 5) is therefore needed unless the charge spread in the IMX636 is shown to be small.
- **End-of-life degradation has a modest effect in the model.** With dark current × 1.7 and background activity × 1.23 (the DAVIS346 20 krad result used as a stand-in), event rates rise by 13–19%. No false triggers appear, and the near-side energy rms rises from 0.33 to 0.42 ln with the beginning-of-life correction. Ten times more hot pixels change nothing, because the dark-calibration mask removes them.
- **Pixel parameters relevant to any operating point.** Published IMX636/EVK4 measurements suggest a longer refractory period (79 µs at default biases, camera-reported) and a higher true contrast threshold (about 0.35 ln at the 100% S-curve intercept) than the model's 10 µs and 0.25. One IMX636 unit had 5× the baseline dark current (5.55 fA). These change detection and energy results more than radiation does at the expected dose.

## 2. Sources

| Source | Sensor and conditions | Used here for |
|---|---|---|
| Falcon Neuro instrument paper (McHarg et al. 2022) and lightning paper (Frontiers in Remote Sensing 2024) | 2 × DAVIS240C (240 × 180 px, 18.5 µm, front-side illuminated, peak QE ≈ 7%), ISS exterior, 51.6° LEO | Operations: 921 kbit/s downlink limiting recordings to 1–3 min; on-board time 1–2 s off UTC when GPS time insertion failed; no on-board trigger in that design |
| Wilcox et al. 2025, *Sensors* 25, 6599 (Falcon Neuro lifetime degradation) | Same sensors, January 2022 – September 2024, standard biases, 60 s segments | Noise classes in orbit (hot, "boring" constant-rate, row/column bursts, isolated events, cold pixels); trends; single-event effects |
| Roffe et al. 2021, *IEEE Access* (arXiv 2102.00112) | VGA (640 × 480, 15 µm) time-encoding event sensor, LANSCE wide-spectrum neutrons (0.1 to > 600 MeV), lens capped | Particle-hit signatures in the event stream; recovery; no damage |
| USAF Academy / AFRL test abstracts (McMahon-Crabtree et al. 2022, SPIE 12233; Crowell et al.) | DAVIS346 and Prophesee PPS3MVCD (both 180 nm), gamma and proton dose | Dose thresholds, degradation factors, lock-up behaviour (abstract-level information only) |
| McReynolds et al. 2024, SPIE 12996 (arXiv 2404.07656) | Sony IMX636, S-curves 76 mlx – 300 lx, `bias_refr` −20 | Contrast threshold, dark current, threshold interpretation |
| Noise2Params (arXiv 2605.16317) | Prophesee EVK4 HD (IMX636), static uniform scenes, default biases | Refractory period, fitted threshold, leakage model |
| Not accessible here | Falcon ODIN pre-launch characterization (Prophesee Gen4, SPIE 13149, 2024); TUM EventSat thermal-chamber noise tests, −20 to +60 °C (IAC-25, B4.2.7) | Most directly relevant IMX636 data (background activity versus illumination, S-curves, low-light cutoff, temperature); worth obtaining |

The ISS orbit lies inside the magnetosphere: its galactic-cosmic-ray flux is reduced by geomagnetic shielding, and it adds trapped protons in the South Atlantic Anomaly. A 3000 km lunar orbit has the full GCR and solar-particle flux and no trapped belts. ISS single-event rates therefore do not transfer to the mission; the dose per year is of a similar order.

## 3. Radiation findings and what they mean for the model

### 3.1 Single-event latch-up, functional interrupts and bit flips

- **Evidence.** There was no latch-up or burnout in about 2.7 years of Falcon Neuro data. Bit flips are inferred from hot pixels that appear, but their number stayed constant. One DAVIS346 locked up under protons and recovered after a rest and a power cycle.
- **Implication.** Two design features are suggested. First, a current-limited power switch with autonomous power cycling. Second, periodic re-writing of bias and configuration registers, plus a repeat of the hot-pixel mask calibration. The simulator calibrates the mask once at the start (60 s dark). In flight it should be repeated after power cycles and at a set interval.

### 3.2 Total dose and displacement damage

- **Evidence.** Above about 30 krad(Si), the 180 nm sensors developed functional problems and background activity rose. At 20 krad(Si) of protons a DAVIS346 showed +70% dark current and +23% dark event noise. The IMX636 is a stacked back-side-illuminated sensor in a different process and has no published test.
- **Model run** (`data/radiation/radiation_stress_2026-11-12.json`):

| Case | Events per px per s | False triggers | Corrected energy median / rms [ln] |
|---|---|---|---|
| Near side, beginning of life | 0.045 | 0 | −0.07 / 0.33 |
| Near side, dark × 1.7, background activity × 1.23 | 0.051 | 0 | +0.03 / 0.42 |
| Far side, beginning of life | 0.039 | 0 | −0.05 / 0.27 |
| Far side, dark × 1.7, background activity × 1.23 | 0.046 | 0 | −0.04 / 0.24 |
| Far side, hot-pixel fraction × 10 | 0.039 | 0 | −0.05 / 0.27 |

  The trigger thresholds follow the degraded background because the on-board map is the true background. The table is not retuned for the higher background-activity rate; the correction keeps its beginning-of-life training.
- **Implication.** At the expected 13–26 krad the model predicts a modest loss of energy precision and no gross trigger failure. The 30 krad screening class in the dose study is about where 180 nm event sensors begin to fail, so an IMX636 dose test (gamma or protons to about 30–50 krad, measuring dark current, background activity and S-curves) belongs in the test plan. An end-of-life sensor profile and a recalibration of the energy correction in flight follow from this.

### 3.3 Particle-hit signatures and the trigger

- **Evidence (neutrons).**
  - Hits appear as clusters averaging about 30 px at normal incidence and as streaks up to about 300 px at grazing angles.
  - ON events outnumber OFF events about 3:1.
  - Each 625 µs beam macro-pulse gives an ON burst lasting about 1.6 ms (beam timing included), followed by an OFF tail of 8–10 ms.
  - The total event count does not depend on the angle of incidence.
  - In darkness, ON noise is about 1.5× higher than at about 500 lux.
  - The sensor recovered immediately and suffered no damage.
- **Evidence (orbit).** The Falcon Neuro degradation study defines no particle-hit class. Isolated events and row/column bursts are its closest categories.
- **The model.** GCR tracks cross a 3 µm layer, and each crossed pixel receives its charge as an exact photoreceptor jump. Optional lateral spreading (Gaussian, σ in px) and delayed collection are available as stresses. A single hit gives one ON event per pixel and a decay with OFF events, so the ON:OFF ratio and cluster size of the neutron data are not reproduced. Neutron clusters come largely from nuclear recoils and charge diffusion in a front-side-illuminated 15 µm pixel, so their size does not transfer directly to the 4.86 µm back-side-illuminated IMX636.
- **Stress runs** (GCR solar minimum × 100, 20 s crop, 102 hits of which 21 heavy, prompt collection):

| Lateral spread σ [px] | Particle triggers | Probability per hit | False candidates per array-hour (GCR solar min, 1.9×10⁴ hits/h) |
|---|---|---|---|
| 0 | 0 | < 2.9% (95%) | < 560 (95%) |
| 0.5 | 1 | ≈ 1% | ≈ 190 |
| 1 | 2 | ≈ 2% | ≈ 370 |
| 2 | 1 | ≈ 1% | ≈ 190 |
| 4 | 0 | — | — |

  Every particle trigger was in the 50 ms window. The probability peaks near 1 px: the charge then reaches 3–4 pixels of a group while each still crosses a threshold, whereas a 4 px spread dilutes it below threshold. Over all stored particle runs (1070 hits, no spread) there were no triggers, which bounds the rate below about 53 per array-hour (95%), still well above the 1 per hour budget. The counts are 0–2 per run, so each probability is uncertain by a factor of 2 or more.
- **Implication.** Particle false candidates can dominate the budget by two orders of magnitude unless (a) the IMX636's lateral charge spread is shown to be well below 0.5 px, or (b) the trigger rejects them. A veto is cheap because a particle hit is near-instantaneous: its ON events start together in a compact cluster and end within about 1–2 ms (neutron data), while a flash rises over ≥ 2 ms and keeps producing ON events for ≥ 30 ms. A particle beam or source test of the IMX636 measuring cluster size, events per hit and ON:OFF ratio would settle (a). The simulator should get a cluster-size and ON-burst model fitted to such data, and a veto option tested against the flash cohort.

### 3.4 Row and column bursts

- **Evidence.** Falcon Neuro shows bursts in which a whole row or column fires within a short time. They are the only noise measure with a statistically significant deterioration trend (nadir camera), and a dedicated change-point filter removes them on the ground.
- **The model.** Not simulated. In dark scenes the trigger needs at least 6 counts in a 3 × 3 group within the 50 ms window (more in longer windows), and a single burst gives at most one event in 3 pixels of a group. One burst therefore cannot trigger, but repeated bursts on the same row within a window could.
- **Implication.** Add a row/column-burst stress (rate and multiplicity as free parameters until IMX636 data exist), and an on-board burst filter, which is simple at the readout level.

## 4. General modelling improvements for a spacecraft sensor

1. **Refractory period.** EVK4 cameras report 79 µs at default biases (Noise2Params), and `bias_refr = −20` lengthens it further, whereas the model assumes 10 µs. Recalibrated at 79 µs, the model's corrected energy rms doubles from 0.25 to 0.49 ln (0.71 ln at 1–3 MJ), while detection is unchanged ([pixel-parameter sensitivity](event_stream_sim.md#pixel-parameter-sensitivity-refractory-period-and-contrast-threshold)). Read the dead time at the chosen biases from the camera API.
2. **Contrast threshold.** The 100% S-curve intercept for the IMX636 is about 0.35 ln (McReynolds et al. 2024), while a noise-model fit to an EVK4 gives 0.15 at default biases, and the model uses 0.25. The spread reflects measurement method and biases. Over 0.15–0.35 (trigger table re-tuned), lattice detection falls from 99.4% to 95.7% and the terminator event rate from 0.40 to 0.17 events per px per s, while energy precision changes little (same section).
3. **Dark current spread between units.** Two IMX636 units measured 1.1 and 5.55 fA. The `imx636_warm` profile (5.55 fA) covers the high case; the flight unit needs its own measurement.
4. **Noise physics.** Noise in these pixels is dominated by photon shot noise with an illumination-dependent bandwidth. The kernel simulates that directly; the additional background activity is a fixed additive rate. A leakage-current term that varies with illumination (fitted to EVK4 data) would replace the fixed rate.
5. **Temperature.** The EventSat thermal-chamber tests (−20 to +60 °C) should replace the generic dark-current doubling per 6.5 °C, and should set the thermal-control requirement for the heads.
6. **Operations.** Falcon Neuro's experience supports an on-board trigger with a small downlink, absolute time-tagging that does not depend on a single GPS insertion (flash–crater pairing needs times known to well under 1 s), and monitoring of noise classes in orbit as a health metric.

## 5. Proposed items (for team decision)

- **Particle veto in the trigger** (strengthens results-note item 5): mandatory unless an IMX636 particle test shows sub-0.5 px charge spread. Next simulator step: implement the veto and show that the flash cohort is unaffected.
- **Radiation test plan:** IMX636 total dose to about 30–50 krad(Si) (dark current, background activity, S-curves, latch-up current) and a particle test (cluster size, events per hit).
- **Electronics:** latch-up protection with autonomous power cycling; periodic bias/register refresh; hot-pixel mask recalibration in flight.
- **Model updates once data exist:** measured refractory period and threshold, end-of-life profile, cluster/burst particle model, row/column-burst stress, temperature law.

## Sources

- McHarg et al., "Falcon Neuro: an event-based sensor on the International Space Station", *Optical Engineering* 61(8) 085105 (2022), https://doi.org/10.1117/1.OE.61.8.085105
- Event-based vision sensor observations of lightning from the ISS: the Falcon Neuro mission, *Frontiers in Remote Sensing* (2024), https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2024.1436898/full
- Wilcox et al., "Event-Based Vision Sensor Lifetime Degradation in Low Earth Orbit", *Sensors* 25, 6599 (2025), https://www.mdpi.com/1424-8220/25/21/6599 (full text via Europe PMC, PMC12610280)
- Roffe et al., "Neutron-Induced, Single-Event Effects on Neuromorphic Event-based Vision Sensor", *IEEE Access* (2021), https://arxiv.org/abs/2102.00112
- McMahon-Crabtree et al., "Automated characterization techniques and testbeds for event-based cameras", *Proc. SPIE* 12233 (2022); DAVIS346 proton and gamma results as summarized in the SPIE abstract by R. Crowell et al., https://spiedigitallibrary.org/profile/Ryan.Crowell-4411878
- McReynolds, Graça, Kulesza, McMahon-Crabtree, "Re-interpreting the step-response probability curve to extract fundamental physical parameters of event-based vision sensors", *Proc. SPIE* 12996 (2024), https://arxiv.org/abs/2404.07656
- Noise2Params, EVK4 HD noise model, https://arxiv.org/abs/2605.16317
- Falcon ODIN payload and pre-launch characterization, *Proc. SPIE* 13149 (2024), https://doi.org/10.1117/12.3027694 and https://doi.org/10.1117/12.3026253 (not read)
- TUM EventSat, IAC-25 B4.2.7, https://mediatum.ub.tum.de/1833763 (not read)
- Hahmeyer 2025, EventSat bachelor thesis (TUM), `data/external/sensor_values/` (EVK4 dark rates: 2.6 kEv/s at default biases, 1.9–3.2 MEv/s at the low-light bias sets, monitor off)
