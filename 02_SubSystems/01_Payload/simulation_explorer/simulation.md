---
title: "Simulations behind the impact-energy conversion proposal"
subtitle: "Methods, assumptions and verification, revision 5 (2 November 2026; documentation updated 11 November 2026; full version)"
date: "11 November 2026"
---

> **LETO SRR applicability, 22 November 2026.** Use these saved simulations as evidence under their recorded conditions. The current requirement IDs, SRR sizing inputs and data/verification decisions are in the SRR guide. The 3,000/300 km, six-head model and its pair-yield results retain their original inputs. [SRR and requirements](../../leto_srr.md)

> Current models, assumptions and results for the [proposal](../impact_energy_conversion_proposal.md). [Methods and dependencies](../../analysis/impact_energy_conversion/README.md). These are concept screens, not maintained trajectories, calibrated sensor performance or priced designs.

> **Current-status note, 19 November 2026 (Europe/Berlin):** the numerical tables retain their recorded inputs. The [14 November crater-population note](../orbit_trade_explorer/crater_size_distribution_review.md) recommends wider slope sensitivity; its indicative rescalings and the orbit explorer do not replace S14's stored joint-model distribution. Section 20 identifies newer event-stream evidence separately. No scientific dataset or PDF was regenerated for this documentation review.

# 1. Overview

Table 1 lists the simulations.

Table: Simulations and calculations used in the proposal.

| ID | Name | Script | Answers | Used in proposal |
|---|---|---|---|---|
| S1 | Dark-surface coverage | `coverage.py` | How much dark surface-time a camera mosaic watches, versus altitude; poles included | §4.2, Fig. 1, Table 5 |
| S2 | Circular-orbit stability | `orbit_stability.py` | Do high circular polar orbits stay near-circular, and what does control cost? | §4.2, Table 5 |
| S3 | Elliptical-orbit screen | `orbit_trades.py` | Can a 300 × 3000 km ellipse keep its low point, and what does it watch? | §5.1, Table 5 |
| S4 | Imaging access | `imaging_access_check.py` | Which sites can be photographed, at which latitudes and Sun elevations? | §5.1, §7 |
| S5 | Camera-count trade | `orbit_trades.py` | How many cameras, with which lens? | §4.3, Table 3 |
| S6 | Scalar yield chain | `science_model.py` | Pairs per year for the ground comparators (event-camera options now in S14) | §3, §7 |
| S7 | Analytic precision model | `science_model.py` | How precise are the products for N pairs (unselected sample)? | §8, Table 9, Fig. 4 |
| S8 | Supporting calculations | `science_model.py`, `transfer.py` | Focal-plane light, position error, budgets, rate cross-check, association, terrain test, image SNR | §§4–10 |
| S9 | Lunar arrival and capture | `transfer.py` | Capture cost for different transfers; split capture; burn-length loss | §5.3, Table 7 |
| S10 | Event-camera response and detector (rev. 5) | `event_response.py` | Detection probability, false-alarm thresholds and raw energy error across the sensor envelope | §4.4, §10 |
| S11 | Event-only flash-energy calibration (rev. 5) | `photometry_calibration.py` | Energy error after calibration, on held-out conditions | §4.4, D03 |
| S13 | Observed background (rev. 4) | `observed_background.py` | Spectral earthshine, range and latitude along actual observing opportunities | §4.4, §7 |
| S14 | Joint population, yield and fit (rev. 5) | `joint_model.py` | Pairs per year and science precision from one selected population | §§4.3–8 |
| S15 | Coarse system budget (rev. 5) | `system_budget.py` | Mass, power, data and link for Options A and C | §5.1, §10 |
| S16 | Event-sensor trade (3 Nov 2026) | `event_response.py` (version 4), `sensor_trade.py` | Yield for sensor cases built from measured IMX636 data; head size; cooling | §4.3, §11 |
| S17 | Measured lunar texture (3–4 Nov 2026) | `texture_map.py`, `texture_measured.py` | False triggers from the real near-side texture at the adopted thresholds | §4.4, §10 |
| S18 | Crater tests on real LRO images (3 Nov 2026) | `crater_injection_test/` (`real_tiles/`, `real_pairs/`) | Confirmation curve and diameter error on real terrain and real new craters | §4.5, §7, §11 |
| S19 | Whole-scene event streams (5–11 Nov evidence) | `analysis/event_stream_sim/` | Masks, noise, deadtime, energy recovery, onset and pointing jitter | §4.6, D01–D04 |
| S20 | GMAT short orbit checks (5 Nov evidence) | `analysis/gmat_lunar_setup/` | Force-model setup, drift, ideal lowering and numerical sensitivity | §5.4 |

The common conventions are:

- **Moon:** sphere of radius 1737.4 km, with μ = 4902.8 km³/s². The gravity terms in S2 and S3 use a 1738 km reference radius.
- **Time:** sidereal lunar day of 27.3217 d; Julian year of 8766 h.
- **Sensor:** IMX636-class event camera, 1280 × 720 pixels at 4.86 µm.
- **Flash energy E_L:** energy in the 600–900 nm band, converted to emitted energy assuming uniform emission into the hemisphere above the surface (2π sr). Detected photons are counted at an effective 750 nm. For 2000–4500 K spectra the photon-weighted effective wavelength is 744–792 nm, a ±4% conversion term carried in the common calibration allocation.
- **Position errors:** quoted as 95% error-ellipse semi-major axes.
- **Random seeds:** fixed in each script, so all runs are reproducible.

# 2. S1: Dark-surface coverage

**Question.** What share of the Moon's surface-time does a downward-looking camera mosaic observe in darkness, and is every region covered, including the exact poles?

**Model.**

- **Orbit:** circular polar orbit, fixed in inertial space. The Moon rotates beneath it once per sidereal day.
- **Sun:** circles the Moon once per year with a latitude of ±1.54°, which produces seasons at the poles.
- **Surface grid:** 24 × 48 equal-area points (used for averages), plus probe rings at ±72, 75, 80, 85, 88 and 89.9° latitude (12 longitudes each) and the two exact poles (used for minima).
- **Cameras:** a rectangular mosaic of identical heads pointed at nadir, each with field 2·atan(sensor size / 2f) and 5% overlap.
- **Time step:** min(600 s, period/60), over 365.25 days.

A point counts as observed when all four conditions hold:

1. it is inside a head's field;
2. its **emission angle** (local vertical to line of sight) is ≤65°;
3. the Sun is below its horizon;
4. the Sun is more than 40° from the boresight, or hidden behind the Moon.

The exposure fraction Φ is the mean over the equal-area points divided by 8766 h. Availability losses (70%) are applied in S6.

**Assumptions and limits.** The Moon is treated as a smooth sphere, so terrain shadows and libration are not included. Earthshine is treated in S13, not here, and the orbit is ideal.

**Verification.** The 30 October design (625 km, 4 × 4 mosaic of 25 mm heads) was recomputed: a median of 21.4 h/yr against 21.1 h/yr in the earlier study (1.6%).

**Results.** Table 2 shows the altitude scan.

Table: Exposure versus altitude for cap-filling 16 mm mosaics (geometric, before availability).

| Altitude [km] | Heads needed | Φ | Lowest latitude-band exposure [h/yr] | 95% position error at 65° emission [km] |
|---|---|---|---|---|
| 625 | 32 | 0.020 | 110 | 0.5 |
| 1000 | 24 | 0.033 | 183 | 0.6 |
| 2000 | 15 | 0.054 | 270 | 0.9 |
| 3000 | 8 | 0.066 | 326 | 1.3 |
| 5000 | 6 | 0.081 | 411 | 2.0 |

The chosen 2 × 3 mosaic of 16 mm heads at 3000 km gives Φ = 0.064, about 96% of the cap-filling value (the mosaic clips the 38.8° circle along its short side). It gives at least 306 h/yr in every latitude band and at least 933 h/yr at every high-latitude probe, including both exact poles.

# 3. S2: Circular-orbit stability

**Question.** Does Earth's gravity make high circular polar orbits eccentric, and what does it cost to keep them circular?

**Model.**

- **Equations of motion:** Moon point mass plus J2 = 2.0323×10⁻⁴ in a non-rotating lunar-equatorial frame. Earth is a point mass on a circular orbit of 384,400 km, inclined 6.68° to the lunar equator, with direct and indirect terms.
- **Integrator:** DOP853 (relative tolerance 10⁻¹⁰), in 5-day segments over 3 years.
- **Initial state:** circular polar orbits at 1000–5000 km, with the node at 0°, 45° and 90° from Earth's orbital node.
- **Control:** if the osculating eccentricity exceeds 0.03 at the end of a segment, the orbit is circularized impulsively at its current radius, and the velocity change is summed.

**Assumptions and limits.** The Sun, the C22 and higher gravity terms, Earth's orbital eccentricity, solar pressure, and navigation and burn errors are all omitted. Starting at exactly e = 0 is optimistic. The results are therefore screens, and the proposal allocates 30 m/s/yr rather than the computed values.

**Results.** At 1000 and 2000 km the eccentricity stays below 0.004 over 3 years.

At 3000 km, e reaches 0.04–0.06 after 3 years for nodes at 0° and 45° (e-folding time about 205 days), and stays at 0.002 for 90°. With control, one impulse is needed in 3 years, i.e. **0–9 m/s/yr** depending on orientation.

At 5000 km, the uncontrolled eccentricity reaches 0.74–0.77. In two orientations the sampled *osculating periapsis* falls below the surface after 835–870 days; this is a screening failure, not a simulated terrain impact. With control, one or two impulses are needed in 3 years, **7–13 m/s/yr**. The case against 5000 km is therefore the position error and the diminishing exposure gain (S1), not the maintenance cost.

# 4. S3: Elliptical-orbit screen

**Question.** Can a 300 × 3000 km polar ellipse keep its low point, and what does it watch?

**Model.**

- Dynamics as in S2, with 2-day segments.
- Periapsis 300 km and apoapsis 3000 km (a = 3387 km, e = 0.399). Nodes at 0° and 90°; periapsis over the equator (ω = 0°) or over the pole (ω = 90°).
- **Control policy:** when a segment ends with the periapsis outside 250–350 km, the run continues to the next apoapsis. There the along-track speed is reset so that the periapsis returns to 300 km.
- **Exposure:** as in S1 along the propagated track (first year, 120 s sampling). The result is scaled by the ratio of equal-area to coarse-grid exposure for the circular 3000 km orbit (0.0639/0.0736).

**Results.** Without control, the osculating periapsis falls below the surface within about 3–20 months in all four orientations.

With control, the policy does *not* keep the periapsis within 250–350 km (Table 3). It reacts one half-orbit late, and in one case the osculating periapsis still falls below the surface. The velocity-change rates are therefore not the cost of a successfully maintained orbit.

The exposure is Φ ≈ 0.027, 42% of the circular 3000 km orbit, and the spacecraft spends 4.7% of the time below 350 km.

Table: Controlled ellipse cases (3 years).

| Node / ω | Δv [m/s/yr] | Burns | Periapsis range [km] | Outcome |
|---|---|---|---|---|
| 90° / 0° (reference) | 104 | 45 | 224–351 | outside the band, no surface crossing |
| 0° / 0° | 221 | 95 | 187–303 | outside the band |
| 0° / 90° | 510 | 198 | 98–530 | outside the band |
| 90° / 90° | 407 | 143 | −53–303 | **failure** (osculating periapsis below the surface) |

The ellipse is rejected on watching time and imaging access (S4). The control results are a further reason, but an event-driven controller was not tested, and other eccentric designs were not studied.

# 5. S4: Imaging access

**Question.** Which flash sites can the crater camera photograph, and at which latitudes and Sun elevations?

**Model.** A site is photographable at an instant when three conditions hold:

1. the spacecraft is below 350 km;
2. the site is within 20° off-nadir as seen from the spacecraft (converted to a surface central angle with a flat-surface approximation, arctan(h·tan 20°/R): 3.59° at 300 km against 3.65° exactly, slightly conservative);
3. the Sun is within the chosen elevation range.

Two illumination modes are tested:

- **normal:** Sun elevation 20–70° (incidence 20–70°);
- **low-Sun:** Sun elevation 5–20°.

The site sets are 12 × 24 equal-area points plus rings at ±66, 70, 72, 75, 80, 85 and 89° (12 longitudes) and the exact poles. The circular 300 km orbit is propagated for 6 months with 30 s sampling. The statistic is the share of sites with **at least one usable pass within the 6-month phase**. This is not a flash-to-image waiting time; flashes from the whole watching phase are imaged during this one phase.

On a sphere with 1.54° obliquity, the Sun never rises 20° above the horizon at latitudes above 71.5° (5.15% of the surface area). The normal mode cannot reach these sites.

**Results.** Table 4 gives the share at each ring. Table: Share of probe sites at each latitude ring (24 sites per ring, both hemispheres) with at least one usable imaging pass in a 6-month circular 300 km phase.

| Site set | Normal mode (Sun 20–70°) | Low-Sun mode (Sun 5–20°) |
|---|---|---|
| Equal-area grid (all latitudes up to ±66.4°) | 100% | 100% |
| Ring at 66° | 100% | 100% |
| Ring at 70° | 88% | 100% |
| Rings at 72°, 75°, 80° and 85° | 0% | 100% |
| Ring at 89° and the exact poles | 0% | 0% |

Above about 86.5° latitude the Sun never rises 5° above the horizon, so even the low-Sun mode cannot reach the polar caps.

For the **ellipse** (stored result of the controlled reference case; flashes uniform over 2.5 years, operations 3 years, equal-area points only), 49% of sites are never reachable: 29% at 0–30° latitude, 53% at 30–60° and 100% above 60°. Unreachable waits are stored as `null`.

**Use in S6 and S14:**

- S6 (ground comparators and historical scalar chain): p_img = 0.85 for the circular phase (range 0.75–0.90), including the 5% of area above 71.5° and losses from scheduling, slews and data.
- S14 (event-camera options, revision 5): the per-ring access by latitude, times a scheduling factor of 0.90 (0.80–0.95).
- p_img = 0.51 for the ellipse.
- The low-Sun mode is *not* counted in the yield, because crater detection under long shadows is not yet demonstrated.

**Limits.** Terrain shadows are ignored. The image-acquisition schedule, slews, data volume and smear are not modelled; S8 gives a first signal-to-noise estimate.

# 6. S5: Camera-count trade

**Question.** How many event cameras, and with which lens?

**Model.**

- **Exposure:** S1 runs at 3000 km for 8 mm 1 × 2, 12 mm 1 × 2 and 2 × 2, 16 mm 1 × 1, 2 × 2 and 2 × 3, and 25 mm 3 × 5.
- **Detection threshold:** with f/1 lenses the collected light scales with f², so the threshold is $E_{det}=2\times10^4\,\mathrm{J}\,(16\,\mathrm{mm}/f)^2$.
- **Smallest crater whose flash is detected:** $D_{det}=4.3\,\mathrm{m}\,(E_{det}/8.49\times10^4\,\mathrm{J})^{0.30}$ (assumed slope 0.30, see S8). The effective limit is $D_{eff}=\max(3.15\,\mathrm{m},D_{det})$.
- **Relative pairs:** $(\Phi/\Phi_{ref})(D_{eff}/D_{eff,ref})^{-3.25}$.

**Results** (proposal, Table 3): 15%, 40%, 59%, 68%, 77%, **100%** (six 16 mm heads) and 104%.

**Limits.** This is a deterministic screen. The population-level detection efficiency of the chosen design comes from S10/S14.

# 7. S6: Pair-yield model and Monte Carlo

**Question.** How many confirmed flash–crater pairs per year does each option deliver?

The event-camera options A/B/C use the joint population in S14. This section gives the scalar-chain method for ground comparators.

**Model.**
$$Y = N_c(\ge D_{min})\;\Phi_{eff}\;p_{flash}\,p_{loc}\,p_{img}\,f_{before}\,p_{det},\qquad N_c(\ge D)=N_{10}\,(D/10\,\mathrm{m})^{-s}$$

- $N_{10}$ = 184 ± 46 new craters ≥10 m per year (Speyerer et al. 2016, as re-derived by Cheng & Scolnic 2026).
- s = 3.25 (range 2.8–3.6). This is an extrapolation from 10 m down to about 3 m.
- $\Phi_{eff}$ = Φ × availability.
- $D_{min}$ = k × 0.9 m (3 µrad camera at 300 km).

Table 5 lists the chain factors.

Table: Chain factors: nominal, pessimistic and optimistic values.

| Factor | Nominal | Pessimistic | Optimistic | Basis |
|---|---|---|---|---|
| availability | 0.70 | 0.60 | 0.80 | as in the 30 Oct study |
| p_loc | 0.95 | 0.90 | 0.98 | error ellipse inside the 8.4 × 6.3 km frame |
| **p_img** (circular) | **0.85** | **0.75** | **0.90** | S4, including the >71.5° loss and scheduling |
| **f_before** | **0.80** | **0.60** | **0.90** | LROC 2026 coverage by Sun-angle bin (86–94%), less a margin for resolution and lighting direction |
| p_det | 0.80 | 0.60 | 0.90 | targeted before/after comparison (assumed) |
| k = D_min / pixel | 3.5 | 5.0 | 3.0 | smallest published flash crater ≈3.5 pixels |
| s | 3.25 | 2.8 | 3.6 | Brown et al. 2002 index / gravity-regime scaling |
| N₁₀ [yr⁻¹] | 184 | 138 | 230 | Speyerer et al. 2016 |

Ground-comparator inputs:

- **Ground + LRO:** Φ = 2×10⁻³, D_min = 7 m, p_img = 0.48, p_det = 0.5, p_flash = 1.
- **Imaging orbiter with ground flashes:** p_loc = 0.9, p_flash = 1.
- **Future ground networks with purchased imaging (2031–2035 scenario, revision 5):** Φ = 3×10⁻³ (1.5×10⁻³–6×10⁻³) for several networks; flashes located to 3 km (95%), so p_loc = 0.9; purchased 0.9 m-class images for half of the sites (p_img = 0.5); half of the crater-forming flashes detected from the ground (p_flash = 0.5, for sky, phase and earthshine limits); D_min from the purchased images as for the mission. These inputs are assumptions, not a forecast.

**Monte Carlo.** 20,000 draws:

- each factor is triangular (pessimistic, nominal, optimistic);
- N₁₀ is normal (184, 46), clipped at 50;
- the 2.5-year total is a Poisson count with mean 2.5·Y.

**Results.** Table 6 gives the yields.

Table: Pair yield (Monte Carlo; conditional on the model and its ranges).

| Option | Median per year (P10–P90) | Median in 2.5 yr (P10) | P(≥30) | P(≥80) | P(≥150) |
|---|---|---|---|---|---|
| Imaging orbiter + ground flashes | 4.9 (2.3–9.5) | 12 | 0.05 | 0 | 0 |
| Future ground networks + purchased imaging (scenario) | 2.5 (1.2–5.1) | 6 (2) | 0.00 | 0 | 0 |
| Ground + LRO | 0.24 (0.11–0.49) | 0 | 0 | 0 | 0 |

**Further results.**

- **Sensitivity to k** (other factors nominal): k = 3, 4 and 5 multiply the yield by 1.65, 0.65 and 0.31.
- **Ground model versus history:** the ground model gives 0.24/yr against a historical 0.6–1/yr, so it is pessimistic by about a factor of 3. The historical pairs came from selected long-duration flashes and dense LRO coverage.

**Limits.**

- The factors are independent; in reality illumination links access, archive matching and detection.
- No shower seasonality and no geographic clustering are modelled.
- Spacecraft reliability is not included.

# 8. S7: Analytic precision model

**Question.** For N pairs, how precisely are the relation's normalization, slope and scatter determined, and what follows for η?

**Model.** $\ln D = a + \alpha\ln(E_L/E_0) + \varepsilon$. The per-pair scatter combines (in ln D):

- impact angle 0.167 (from p(θ) = sin 2θ);
- sporadic speed 0.067;
- soil 0.15;
- intrinsic η variation α × 0.30;
- random photometry α × 0.158 (mission) or α × 0.70 (mixed ground data);
- diameter measurement 0.08.

This gives σ_ε = 0.27 for the mission and 0.34 for ground data, with **α = 0.30 assumed**. The two published anchors (4.3 m at 8.49×10⁴ J, 23.8 m at 1.3×10⁷ J) give a two-point slope of 0.34. With α = 0.30, a 3.15 m crater corresponds to 30 kJ (34 kJ with 0.34).

The formulas are:
$$\sigma(a)=\sqrt{\frac{\sigma_\varepsilon^2}{N}+(\alpha\,\sigma_{E,common})^2},\quad \sigma(\alpha)=\frac{\sigma_\varepsilon}{\sqrt N\,S_{\ln E}},\quad \sigma_{\ln\eta}=\sqrt{\sigma_{rule}^2+\frac{(\sigma_\varepsilon/\alpha)^2}{N}+\sigma_{E,common}^2}$$

- $S_{\ln E}$ = 1/b = 1.11, from a power-law energy distribution with b = 0.9.
- $\sigma_{E,common}$ = 0.10 is the mission-common photometric allocation.
- $\sigma_{rule}$ = 0.3, 0.5 or 0.8 is the *assumed* crater-rule uncertainty; it is not derived.
- The conversion term for a 10 kJ flash catalogue is $s\sqrt{\sigma(a)^2+(\Delta\ln E\,\sigma(\alpha))^2}$, with Δln E = ln(10⁴/10⁵).

**Synthetic check.** 400 samples of 300 pairs each, with *no* selection cut and with one mission-common energy offset (σ = 0.10) drawn per sample. The check now reproduces σ(α) (0.0140 against 0.0139) and σ(a) (0.0345 against 0.0337) to within 3%, with a 2% low bias in α from the energy errors. This verifies the formulas for an unselected sample only. The selected-sample precisions come from S14.

**Terrain test** (illustrative). Pairs are split by surface share (16% mare, 84% highland) with equal scatter. The standard deviation of the difference in mean ln D is σ_ε√(1/n₁+1/n₂): 0.081 at N = 80 and 0.047 at N = 240. A 30% light difference shifts ln D by 0.30 × ln 1.3 = 0.079, so it is seen at about 1.0σ and 1.7σ. Terrain-dependent soil strength produces the same signature.

**Empirical check.** Three published pairs scatter by about 0.2 in ln D around a common fit. This is *consistent with* σ_ε = 0.27 but does not validate it: three points leave almost no degrees of freedom.

# 9. S8: Supporting calculations

**Focal-plane illuminance** (used only for orientation; S10 supersedes it):
$$E_v = \frac{E_L/\tau}{2\pi d^2}\cdot\frac{\pi D_{ap}^2/4}{4\,p^2}\cdot T\cdot 30.3\ \mathrm{lm/W}$$

This uses τ = 0.1 s as a peak-power time scale and an optical transmission T = 0.6. A 10⁴ J flash gives 0.04–0.07 lx; a 10⁶ J flash gives 4.4–6.8 lx.

**Flash position error.** The angular error combines 0.1-pixel centroiding and 48 µrad of attitude and boresight knowledge in quadrature, multiplied by the slant range and stretched by 1/cos(emission) along the view. A 150 m orbit error is added in quadrature, and the 95% semi-major axis is 2.45σ. The results are 0.56 km at nadir and 1.28 km at 65° emission from 3000 km.

Additional terms:

- **Timing:** 10 ms × 0.373 km/s ground-track speed = 4 m; the onset-estimate error (≤30 ms, 90th percentile, S10) adds ≤11 m.
- **Terrain:** a height error h shifts the position by h·tan(emission). For LOLA-class heights (tens of metres), this is about 0.1 km at 65°.

**Crater-rate cross-check.** NASA's flash rate (1.03×10⁻⁷ km⁻² h⁻¹ above 1.05×10⁷ J kinetic energy; Suggs et al. 2014) is converted to light with their η at an assumed 24 km/s, then scaled with an energy slope of 0.90. Crater sizes then follow from the assumed relation. The result is 2.2–2.8 times more crater-forming events than the crater-based estimate. This depends on the uncertain η and band conversion, so it shows a disagreement between the two records, not that the crater-based estimate is conservative.

**Chance association.** This is now computed in S14 with a size window; see the association rule there.

**Manoeuvre and mass budget.** All burns are treated as instantaneous:

- capture 629 m/s;
- orbit keeping at 3000 km, 75 m/s (30 m/s/yr × 2.5 yr);
- lowering 512 m/s (burns of 228 and 283 m/s);
- keeping the 300 km orbit, 15 m/s;
- course corrections and disposal, 40 m/s;
- 10% margin.

The total is 1.40 km/s. The payload is 20.5 kg (6 × 0.9 kg heads, 3 kg processing and bias source, 12.1 kg camera) with 20% margin, and is assumed to be 20% of the dry mass, giving 123 kg dry. Launch mass is then 193 kg at 315 s (bipropellant), 198 kg at 300 s and 235 kg at 220 s (hydrazine).

**Option C** drops the camera, the lowering and the low-orbit keeping (Δv = 0.82 km/s). Three mass estimates bracket it:

- **Option A's bus kept, camera removed:** 108 kg dry, 143 kg at 300 s;
- **bottom-up resized bus (S15):** 77 kg dry, 102 kg at 300 s.

The proposal uses the bottom-up value. For Option A, S15 gives 118 kg dry and 190 kg at 300 s, close to the payload-fraction result (123 kg, 198 kg).

**Crater-camera signal-to-noise** (hand calculation, first estimate). The sunlit surface radiance in a 100 nm visible band is L ≈ ρ E_⊙ sin(e)/π. With ρ = 0.12, E_⊙ = 185 W/m² in the band and Sun elevation e = 20–30°, L ≈ 2.4–3.5 W m⁻² sr⁻¹. The signal per pixel is:

$$N_e = \frac{L\,A_{ap}\,\Omega_{pix}\,t\,\lambda}{hc}\,\tau QE$$

with A_ap = π(0.1 m)² (assumed 0.2 m aperture), Ω_pix = (3 µrad)², t = 0.34 ms (half-pixel smear at 1.32 km/s), λ = 550 nm and τQE = 0.4. This gives about 250–370 electrons per pixel, a signal-to-noise ratio of about 15–20 (shot noise only). The camera's design case in low Earth orbit (about 0.1 ms exposure at 7 km/s over a brighter surface) gives a comparable photon count. A full image-quality budget (MTF, read noise, colour sampling, pointing) is scheduled work.

**Raw event-data rate.** Six 1280 × 720 sensors at an *assumed* 0.1–10 events per pixel per second and 4 bytes per event give 2.2–221 MB/s before on-board filtering. The S10 noise envelope (0.03–1 Hz per pixel) corresponds to 0.7–22 MB/s from background activity alone; moving scene texture, calibration steps and particle hits are not included (3 Hz, a sensitivity case of S10, would give 66 MB/s). These are planning bounds, not measured rates.

# 10. S9: Lunar arrival and capture

**Question.** How much braking is needed to enter the 3000 km polar orbit, and does splitting the capture cost extra?

**Model.**

- **Approach:** patched-conic hyperbolic approach; all burns are instantaneous at closest approach.
- **Direct capture:** $\Delta v=\sqrt{v_\infty^2+2\mu/r}-\sqrt{\mu/r}$.
- **Split capture:** first into an ellipse with apoapsis $r_a$, then lower the apoapsis.
- **Steering loss:** $\Delta v(\omega t)^2/24$, with 200 kg and 88 N total thrust (4 × 22 N) at 220 s (hydrazine) or 315 s (bipropellant).

**Results.**

- **Direct capture into 3000 km:** 421, 476, 629 and 735 m/s for v∞ = 0, 0.4, 0.8 and 1.0 km/s. Into 100 km: 677–884 m/s.
- **Split capture via a 10,000 km apoapsis (18.6 h period):** 432 + 197 m/s. Via 20,000 km: 343 + 286 m/s. Both total 629 m/s.
- **Steering loss:**
  - about 5 m/s for a single 21-minute burn;
  - for the 432 m/s first burn of the 10,000 km split: 14.8 minutes and 1.7 m/s with hydrazine, 15.3 minutes and 1.8 m/s with bipropellant;
  - a single 22 N engine would take 61 minutes and lose 29 m/s.

  **Limits.** There is no launch-provider departure state and no Sun or Earth perturbation during the transfer. Low-energy values are rough bounds.

# 11. S10: Event-camera response and detector (revision 5)

**Question.** With which probability does the event camera detect a slow, faint flash without exceeding one false trigger per hour, and how well can its energy be measured from events alone?


**Pixel model** (per pixel, 0.5 ms steps):

1. **Photocurrent.** I = I₀ + flash, where I₀ = dark current + earthshine (+ bias light, if used), all in detected e⁻/s. Poisson electrons are drawn each step.
2. **Photoreceptor.** A first-order low-pass of the photocurrent with a current-dependent time constant, τ = τ_ref · I_ref / J (linear law) or τ = τ_ref · (I_ref / J)^0.5 (square-root law), capped at τ_cap. Here J is the filtered current, and I_ref = 7.5×10⁶ e⁻/s is the 5 lx level of this project's 30 October red-band bias fixture, not a spectrally matched calibration of the cited experiment. The nominal τ_ref = 1 ms is set equal to the 1 ms latency at 5 lx reported by McReynolds et al. (2024). **Latency is not the time constant.** For a first-order filter, the time to the first event after a step from I₀ to R·I₀ is t = −τ ln[1 − (e^C − 1)/(R − 1)], which for C = 0.25 is 0.84 τ for R = 1.5 but 0.032 τ for R = 10. A 1 ms latency therefore allows τ_ref from about 1.2 ms to about 30 ms, depending on the unpublished step size. Cases with 3 ms and 10 ms are simulated; 30 ms is not. Near the dark limit τ is set by the cap (1 s nominal, 3 s in one case), which corresponds to a corner of order 1 Hz, as McReynolds et al. suggest.
3. **Change detector.** ON/OFF events when ln J moves by the pixel's threshold C_i ~ N(C, 0.03), with 1% event loss.
4. **Background activity (BA).** Extra ON events per pixel: Poisson at rate r_BA (nominal); or in bursts with a mean size of 3 events; or with telegraph switching, where a pixel spends 10% of the time at ten times its low rate (mean dwell 1 s); or with a static lognormal spread of the rate between pixels (σ = 1 in ln). The decoder cannot tell these events from signal.
5. **Flash.** Light energy E_L at range d is converted with the 16 mm (or 25 mm) f/1 aperture, T = 0.6 and QE = 0.5 at 750 nm. It is spread by a Gaussian PSF (σ = 0.5 pixel) with a random sub-pixel centre over a simulated 4 × 4 patch. The profile is (1 − e^{−t/2 ms}) · e^{−t/τ_f}; held-out profiles are tested in S11.

**Sensor envelope.** Table 7 lists the 16 simulated cases. No IMX636 or IMX646 data exist at this light level, so the cases bound, not predict.

Table: Event-sensor cases. Unless stated, a case keeps the nominal values (τ_ref 1 ms, cap 1 s, linear law, C 0.25, dark current 1 fA, Poisson BA at 0.3 Hz, six 16 mm heads).

| Case | Change from nominal |
|---|---|
| nominal | — |
| optimistic | τ_ref 0.3 ms, C 0.20, dark current 0.3 fA, BA 0.03 Hz |
| pessimistic | τ_ref 3 ms, C 0.30, dark current 5.55 fA (3.5×10⁴ e⁻/s), BA 1 Hz |
| threshold 0.30 | C 0.30 |
| noise 1 Hz / 3 Hz | BA 1 Hz / 3 Hz |
| response 3× / 10× slower | τ_ref 3 ms / 10 ms |
| dark limit 3 s | τ_cap 3 s |
| square-root law | τ = τ_ref (I_ref/J)^0.5 |
| dark current 5.55 fA | 5.55 fA |
| noise in bursts | BA in bursts of mean size 3 |
| telegraph noise | 10% of the time at 10× the low rate, 1 s dwell |
| noise spread per pixel | lognormal BA rate, σ = 1 |
| nominal / pessimistic, fifteen 25 mm heads | 25 mm aperture; 15 heads in the false-alarm budget |

The bases for the values are:

- **Threshold:** 0.25 follows the ON threshold McReynolds et al. infer for the IMX636.
- **Dark current:** 5.55 fA is their measured value, at an unreported temperature. The nominal 1 fA assumes a cooled sensor. The often-quoted halving of dark current per 6–7 °C is generic and is not an IMX636 calibration, so the cooling requirement is a proposal pending data.
- **Background activity:** no published value exists at this light level, so the cases span 0.03–3 Hz and three non-Poisson forms.

**On-board trigger.**

- **Groups and windows.** Every 2 × 2 and 3 × 3 pixel group is evaluated over sliding windows of W = 0.05, 0.2, 0.8 and 2.0 s, every W/5. A trigger needs the group's count ≥ n_min(W, size) and at least 3 contributing pixels.
- **One count per pixel per step.** At most one ON event per pixel per 0.5 ms step is counted. A particle deposit raises the photocurrent within one step, so it contributes at most one count per hit pixel; a flash rises through the photoreceptor over several steps. All events are still kept for the energy estimate.
- **False-alarm budget.** Counting every overlapping group of both sizes on six full sensors, every window and every evaluation step gives 5.3×10¹² tests per hour (1.3×10¹³ for fifteen heads), so each test must have a false-alarm probability below 1.9×10⁻¹³ (7.5×10⁻¹⁴).
- **Null model.** The per-pixel count distribution in each window is the convolution of two parts. The first is the shot-noise event count from noise-only simulations with BA switched off (1008 pixels, 20 s after a 0.5 s warm-up), floored by a Poisson law at 1.5 times its mean. The second is the exact count distribution of the declared BA model at 1.5 times its rate. Both parts are unnormalised upper envelopes. The upper-envelope construction relies on the declared noise model and pixel independence.
- **Moving texture.** At 3000 km a nadir scene moves by 0.41 pixel/s. Where earthshine is present, a moving albedo edge of contrast 2 adds counts in proportion to its log contrast. The thresholds are set so that the budget also holds if such an edge lies in 1% of all groups, which raises the long-window thresholds under earthshine (at 1.3×10⁴ e⁻/s for 2 s: 31 and 48 counts instead of 25 and 37). The prevalence of 1% is an assumption. S17 checks it against the measured near-side texture and finds the adopted thresholds sufficient for every revision-5 case.
- **Thresholds.** For the nominal case at 6.5×10³ e⁻/s, n_min is 8, 12, 18 and 25 (2 × 2) and 10, 15, 24 and 37 (3 × 3) for the four windows.

**Particle and texture checks.**

- **Particles.** 600 deposits of 10²–10⁵ electrons per pixel (log-uniform) along straight tracks of 1–5 pixels, at backgrounds of 6.5×10³ and 1.3×10⁴ e⁻/s (4×10⁴ for warm sensors), without a flash. Without the one-count rule 0.5–31% triggered depending on the case (31% for noise in bursts), and 52–62% with the square-root law; with the rule none did, in every case. A union bound assumes that each hit adds its maximum (3 counts in a 2 × 2 and 5 in a 3 × 3 group) to every group and window containing it. It uses a flux of 5 particles cm⁻² s⁻¹, of which 5% deposit enough charge to fire a pixel (an assumption; a minimum-ionising particle deposits only a few hundred electrons, while about 2×10³ are needed at nominal background). The bound is ≤0.13 false triggers per hour in most cases, 0.32 for fifteen heads at low background, and **2.6 per hour for noise in bursts** at 6.5×10³ e⁻/s, which exceeds the budget.
- **Texture.** With the adopted thresholds, the expected false triggers from moving edges are 0.05–0.7 per hour for a contrast-2 edge in 1% of the groups, but **0.7–7 per hour** at 1.3×10⁴ e⁻/s if 10% of the groups contain such an edge (3.4 for the nominal sensor), and up to 28 per hour for a weak edge (contrast 1.2) in every group in the case with noise spread between pixels. These are stress cases of the assumed edge model. With the measured texture (S17), the nominal sensor gives 0.09–0.12 false triggers per hour at the adopted thresholds.

**Bias light.** A sweep with bias light at 0, 0.002 and 0.01 lx (0, 3×10³ and 1.5×10⁴ e⁻/s) showed lower detection with more bias in every tested sensor case. The grid therefore uses dark current plus earthshine only, and the bias source is reserved for calibration steps. This is a result for the assumed current-dependent pixel and the tested sweep, not a general law for either sensor.

**Energy estimate (event only).**

- The onset is the first ON event of the triggering group within the trigger window.
- The record ends when all 16 patch pixels return to their pre-flash decoded level, or after 4 s.
- Each pixel's intensity is decoded from all its events with its calibrated threshold (5% error) and the measured background (5% common error per flash).

**Grid.** Each of the 16 sensor cases is run at total backgrounds of 2×10³–6×10⁴ e⁻/s (those above its dark current). Decay times are 0.03, 0.1, 0.3 and 1 s, and E_L runs from 2×10³ to 3×10⁶ J at 3750 km, with 40 trials per energy. Each result is stored as k detections out of n with a Wilson 95% interval.

**Results.** Table 8 gives the nominal-case detections; all cases are in `event_response.json`.

Table: Detections out of 40 for nominal sensor assumptions at 3750 km. 40/40 has a Wilson 95% interval of 0.91–1.00, 39/40 of 0.87–1.00.

| E_L, decay time | 6.5×10³ e⁻/s | 1.3×10⁴ e⁻/s | 2.5×10⁴ e⁻/s |
|---|---|---|---|
| 1×10⁴ J, 0.03 s | 15 | 3 | 1 |
| 2×10⁴ J, 0.03 s | 40 | 40 | 40 |
| 2×10⁴ J, 0.1 s | 39 | 29 | 2 |
| 4×10⁴ J, 0.1 s | 40 | 40 | 40 |
| 4×10⁴ J, 0.3 s | 40 | 36 | 10 |
| 10⁵ J, 0.3 s | 40 | 40 | 40 |
| 10⁵ J, 1 s | 40 | 39 | 8 |
| 3×10⁵ J, 1 s | 40 | 40 | 40 |

**Faint long flashes fail first.** Long faint flashes reach too few ON events within any window before background activity accumulates, so detection depends strongly on duration and, through the texture-aware thresholds, on earthshine.

**Corners and single cases.** In the pessimistic corner only flashes of ≥10⁵ J with τ_f ≤ 0.03 s are reliably detected at high background; in the optimistic corner every flash of ≥2×10⁴ J is detected. The case with noise spread between pixels forces much higher thresholds (2 s window disabled), so even 2×10⁴ J flashes of 0.03 s are detected only 12–15% of the time. Per-group thresholds from flight noise maps would recover part of this; they are not simulated.

**Timing.** The **trigger lag** (trigger time minus true onset) has a median of 7–166 ms, the longest for faint 1 s flashes. The **onset-estimate error** (first ON event of the triggering group minus true onset) has a median of 0.7–24 ms and a 90th percentile of ≤30 ms for nominal assumptions. Trigger lag and onset error are reported separately.

**Verification.** In the patch-level null tests, 400 noise-only 4 × 4 patches of 4.4 s produced no trigger for the nominal, noise-1-Hz and pessimistic cases, and in a signal run none of 201 detections came before the true onset. These runs cannot test a 10⁻¹³ tail directly; that rests on the exact convolution of the declared null model and on the independence assumption.

**Limits.** The pixel model is first order, with no refractory period or readout limits. Background activity is modelled as ON-only noise; S11 tests a symmetric form for the energy estimate. Hot pixels are masked by an unsimulated rule; particle rates and end-of-life changes are assumptions. Real scene texture is checked in S17 at 0.9 km resolution. Better trigger statistics (ON plus OFF events, PSF matching) and per-pixel thresholds were not evaluated.

# 12. S11: Event-only flash-energy calibration (revision 5)

**Question.** After a calibration learned on simulated flashes, how large are the energy errors when the conditions differ from the training set?

**Model.**

- **Training flashes:** 1800 flashes of the nominal sensor with exponential profiles. E_L is log-uniform over 10⁴–3×10⁶ J and τ_f log-uniform over 0.03–1 s. Range and earthshine are drawn **together for each flash** from the same observing opportunity of S13. Flashes are grouped into 10% background bins for simulation, so 1586 detected training flashes cover the full background distribution.
- **Thresholds:** the S10 thresholds for each background bin.
- **Correction:** a quadratic regression of ln(E_true/E_raw) on ln E_raw, ln(active duration), peak decoded level, number of pixels with events and ln(measured background).

**Results.** Table 9 gives the errors for detected flashes, in ln E.

Table: Energy error for detected flashes, in ln E (corrected values; 0.21 in ln E is about 21%).

| Test set | Corrected bias | Corrected sd | Flashes |
|---|---|---|---|
| a. same family, new draws | 0.000 | 0.21 | 624 |
| b. two-component profile (held out) | −0.016 | 0.19 | 420 |
| b. power-law tail (held out) | +0.002 | 0.20 | 413 |
| c. bright earthshine only (>10⁴ e⁻/s) | −0.002 | 0.24 | 391 |
| d1. response mismatch (τ_ref ×2, C +0.03), thresholds adapted | −0.024 | 0.20 | 366 |
| d2. same mismatch, nominal thresholds (undetected drift) | −0.016 | 0.19 | 363 |
| e1. warm dark current, nominal correction | −0.152 | 0.33 | 358 |
| e2. warm dark current, retrained correction | +0.013 | 0.32 | 358 |
| g. random pixel prehistory (reference offset within one threshold) | +0.001 | 0.22 | 402 |
| h. BA split equally into ON and OFF, nominal correction (median, robust sd) | +0.185 | 0.22 | 406 |
| h. same, correction retrained for symmetric BA (median, robust sd) | −0.011 | 0.14 | 406 |

**Typical error.** About 20% per flash and robust to held-out profiles, a response mismatch and an undetected drift (biases ≤2.4%).

**Conditions.** By decay time and background, the corrected bias and scatter are −0.002 and 0.19 (τ_f ≤ 0.3 s, background ≤10⁴ e⁻/s), −0.056 and 0.25 (short, bright), +0.023 and 0.18 (long, dark) and **+0.107 and 0.20 (long flashes under bright earthshine)**. This table is passed to the joint fit (S14).

**Training on the flight state.** A warm sensor degrades to 33% with the nominal correction and stays at 32% when retrained, so its larger scatter is physical, not a calibration artefact. With symmetric background activity the ON-only correction is biased by about +20% and 1% of the flashes are grossly wrong; retrained for that noise the bias vanishes. The correction must therefore be trained on the measured flight noise statistics.


**Limits.** No refractory period or readout saturation, so bright-end losses are conditional; no decoder resets within long records.

**Use.** The joint fit (S14) draws energy errors with the condition-dependent bias and scatter above, plus 0.05 per head and 0.10 common. The adverse case uses a scatter of 0.33 and a +10% bias for long flashes under bright earthshine.

# 14. S13: Observed background 

**Question.** What earthshine background, range and latitude do the cameras actually see when they observe?

**Model.**

- **Observing opportunities:** every one in the S1 coverage model (six 16 mm heads, 3000 km, one year, 24 × 48 equal-area points) is recorded with its latitude, hemisphere, slant range, emission angle and Earth phase angle.
- **Earthshine, spectral and first order:**
  - reflected-sunlight irradiance from a full Earth of 0.075 W/m² (Glenar et al. 2019: about 0.15 W/m² broadband with comparable reflected and thermal parts), bounded at 0.05–0.12 W/m²;
  - 28.4% of the solar spectrum in 600–900 nm, with a flat Earth albedo and a Lambert phase law;
  - lunar reflectance 0.13;
  - detected e⁻/s = L·A_ap·Ω_pix·T·QE/(hc/750 nm).


**Results.** Under a full Earth the background is 1.85×10⁴ e⁻/s per pixel (1.2–3.0×10⁴). Of the observed dark time, 50% lies on the near side. The earthshine exceeds 10³ e⁻/s for 39% of the observed time, 3×10³ for 30% and 10⁴ for 9%, and its 90th and 99th percentiles are 9.5×10³ and 1.6×10⁴.

At observed near-side points the Earth phase angle is 9°, 54° and 125° at the 10th, 50th and 90th percentiles, so crescent-Earth nights do occur (review N06). The range is 3080, 3370 and 3650 km at the same percentiles. The samples are spread over all latitude bands (15–19% each), and the 90th percentile of the earthshine is about 1.25×10⁴ e⁻/s at low latitudes and 4.9×10³ above 60°.


**Limits.** Libration and terrain are not included, and the lunar phase function is Lambertian only. Earth's albedo is taken as flat across the band, although the vegetation red edge and clouds vary it by tens of percent.

# 15. S14: Joint population, yield and fit (revision 5)

**Question.** With one population and one selection applied to both, how many pairs does each option deliver, and how precisely does a fit that models that selection recover the relation?

**Population** (400,000 impacts, reweighted for parameter changes):

- **Flash energy:** ln E above ln 300 J, far below any detection, with a power-law index b = α·s chosen so that the crater-size slope equals the anchor slope s: b = 0.975 for s = 3.25, with s varied 2.8–3.6 by importance weights.
- **Crater size:** ln D = ln 4.3 m + 0.30 ln(E/84.9 kJ) + N(0, 0.252).
- **Flash duration:** τ_f log-uniform 0.03–1 s.
- **Viewing conditions:** range, latitude and earthshine drawn jointly from S13 observing opportunities.
- **Normalisation:** impacts with D ≥ 10 m equal N₁₀ (184 ± 46 per year, the Speyerer et al. 2016 result as re-derived by Cheng & Scolnic 2026). The fraction of impacts with D ≥ 10 m is computed by numerical integration of the population (3.664e-04 for s = 3.25). **Selection** (identical in yield and fit):

- **Flash detection:** P_det(E·(3750/d)², τ_f, background), interpolated from S10 for each sensor case. Monotonicity in E is enforced by isotonic regression of each 40-trial row.
- **Crater confirmation:** c_max·Φ((ln D − ln(k·GSD))/0.15), with c_max = 0.85 and k = 3.5. At 3.15 m this is 42.5%, half of its maximum. S18 tests this curve on real LRO images:
  - k is confirmed (3.58–3.63 px);
  - the width measures 0.10–0.21;
  - c_max depends on before/after registration (0.68–1.0).

  The placeholder is kept here.
- **Imaging access:** the per-ring result of S4 (100% to 66° latitude, 87.5% at 70°, none from 72°, linear in between) times a scheduling factor p_sched of 0.90 (0.80–0.95). 
- **Scalar factors:** availability 0.70, p_loc 0.95 and f_before 0.80, as in S6.
- **Association** (review F07). A site is accepted if exactly one confirmable new crater lies inside the 95% error region, treated as a circle of the semi-major axis, which grows from 0.56 km at 3000 km to 1.28 km at 3750 km range. Unrelated confirmable craters arrive at 1.98e-04 per km² per year (the crater anchor weighted by the confirmation curve) over an archive age of 20 years. True pairs are lost when a second candidate exists (factor e^(−λ)). Imaged sites (located flashes above 2.03×10⁴ J, which predict 2.8 m on the prior relation) whose own crater is not confirmed but which contain exactly one unrelated crater become false pairs. There is no size window.

**Yield Monte Carlo.** 4000 draws of availability, p_loc, p_sched, f_before, c_max (0.65–0.95), k (3–5), s (2.8–3.6) and N₁₀, with Poisson counts.

- **Independent mode:** each factor is drawn separately.
- **Dependence stress (review N11):** all non-sensor factors and N₁₀ sit at the same quantile q, with k at 1 − q. It is run with the nominal and with the pessimistic sensor.

Sensor cases are run as separate scenarios rather than given invented probabilities. Because the factor ranges are skewed towards the unfavourable side (above all k), the Monte Carlo median lies below the deterministic value at nominal factors (for the nominal sensor 294 pairs in 2.5 years); all quoted yields are medians.

**Results.** Table 10 gives the Option A yields by sensor case.

Table: Option A pairs in 2.5 years by sensor case (Monte Carlo medians; the last column uses the case's own thresholds for fifteen 25 mm heads).

| Sensor case | Flash share (confirmable craters) | Median | P10 | P(≥30) | P(≥80) | 150 km / 300 km | 15 × 25 mm heads (median) |
|---|---|---|---|---|---|---|---|
| square-root law | 0.93 | 284 | 150 | 1.00 | 0.99 | 4.6 | — |
| optimistic | 0.93 | 284 | 147 | 1.00 | 0.99 | 4.2 | — |
| noise in bursts | 0.67 | 219 | 122 | 1.00 | 0.98 | 1.9 | — |
| nominal | 0.62 | 210 | 117 | 1.00 | 0.98 | 1.7 | 272 |
| dark limit 3 s | 0.62 | 209 | 119 | 1.00 | 0.98 | 1.7 | — |
| threshold 0.30 | 0.57 | 194 | 111 | 1.00 | 0.97 | 1.6 | — |
| telegraph noise | 0.54 | 183 | 107 | 1.00 | 0.97 | 1.5 | — |
| noise 1 Hz | 0.52 | 177 | 102 | 1.00 | 0.96 | 1.5 | — |
| response 3× slower | 0.50 | 170 | 97 | 1.00 | 0.95 | 1.5 | — |
| response 10× slower | 0.48 | 165 | 95 | 1.00 | 0.95 | 1.5 | — |
| dark current 5.55 fA | 0.47 | 163 | 95 | 1.00 | 0.95 | 1.5 | — |
| noise 3 Hz | 0.44 | 153 | 89 | 1.00 | 0.93 | 1.4 | — |
| noise spread per pixel | 0.30 | 108 | 64 | 1.00 | 0.78 | 1.2 | — |
| pessimistic | 0.20 | 75 | 45 | 0.98 | 0.43 | 1.0 | 142 |

For the nominal sensor, Option C gives 55, 140 and 224 pairs at 20, 50 and 80% access, and 51 pairs at 50% access in the pessimistic corner. The ellipse gives 59 pairs. With only 1.5 years of watching, Option A gives 125 pairs, with P(≥80) = 0.85.

The dependence stress test gives a median of 222, P10 56, P(≥80) = 0.84 and P(≥30) = 0.97. With the pessimistic sensor it gives a median of 78, P10 26, P(≥80) = 0.49 and P(≥30) = 0.88. The all-pessimistic corners give 28 and 10 pairs for the nominal sensor (anchors of 138 and 50 per year, the latter the Monte Carlo floor) and 16 and 6 for the pessimistic sensor. The detected flash shares are 0.61 on the near side and 0.64 on the far side.

**Where the pairs are** (nominal, deterministic shares): near side 48%, far side 52%; |latitude| below 30° 37%, 30–60° 46%, above 60° 17%. The population has no terrain map, so no mare/highland split is available.

**Association and catalogue.** For the nominal sensor the false-pair fraction is 0.7% (about 2 false pairs in 2.5 years), and 0.3% for the pessimistic sensor. The catalogue holds about 1199 detected flashes and 732 located sites above the imaging cut; 217 and 206 in the pessimistic corner.

**Numerical checks** (review F08). A bootstrap over the population gives a Monte Carlo error of 1.3% of the deterministic yield. A binomial bootstrap of the 40-trial detection tables gives 0.4% (nominal) and 2.6% (pessimistic). Both are small against the physical uncertainties and are not added to the quoted probabilities.

**Fit.**

- **Likelihood:** a structural likelihood with free a, α, σ and b. The latent true energy sits on a 260-point grid with the power-law prior. For each pair the integrand contains the flash-detection probability evaluated at the pair's range and *measured* duration (true value with a 0.3 error in ln) and *measured* background (5% error), the crater scatter, the probit confirmation and both measurement errors. The normalisation integrates the same selection. A mixture term with the known contamination fraction represents false pairs, with an unrelated crater's size drawn from the production slope times the confirmation curve and its flash energy from the detected-flash distribution.
- **Catalogue term:** the detected flashes that are **not** in the paired sample enter through their own selection-normalised likelihood to constrain b. Its size is the predicted catalogue for the sensor case minus the pairs, so no energy measurement is used twice.
- **Errors:** energy errors drawn with the condition-dependent bias and scatter of S11, plus 0.05 per head and 0.10 common. The likelihood uses the condition-dependent scatter but not the bias. Diameter error hypot(0.03, 0.35 px/(D/GSD)). The per-head and common offsets are not fitted as explicit nuisance parameters.
- **Scenarios and samples:** nominal (sensor nominal) at N = 30, 80 and 240 with 120, 100 and 60 samples; and adverse (pessimistic sensor, its own catalogue, energy scatter scaled to 0.33, +10% bias for long flashes under bright earthshine) at N = 30 and at its median of 75 pairs, with 100 and 80 samples. Fifty-sample ensembles proved too small: the 30-pair slope spread moved between 0.033 and 0.055 between runs, so revision 5 uses larger ensembles.

Table: Fit recovery (true slope 0.30, scatter 0.252, b = 0.975). "Size at 30 kJ" is the error of the fitted mean ln D against the physical relation, including the common offset. The 10 kJ column gives the multiplicative 1σ range of the crater-count conversion term, exp(±3.25·σ) − 1.

| Scenario | N | Catalogue | Slope bias | Slope spread | 1σ coverage (slope) | Scatter (mean ± sd) | Size at 30 kJ (bias, sd) | 10 kJ conversion term |
|---|---|---|---|---|---|---|---|---|
| nominal | 30 | 1169 | -0.014 | 0.054 | 50% | 0.236 ± 0.052 | +0.026, 0.100 | +60/−38% |
| nominal | 80 | 1119 | +0.004 | 0.029 | 80% | 0.254 ± 0.034 | +0.002, 0.065 | +34/−25% |
| nominal | 240 | 959 | -0.001 | 0.015 | 97% | 0.252 ± 0.018 | +0.007, 0.042 | +19/−16% |
| nominal, contamination not modelled | 80 | 1119 | -0.008 | 0.025 | 83% | 0.247 ± 0.035 | +0.002, 0.067 | +33/−25% |
| nominal, flash selection omitted | 80 | 1119 | +0.072 | 0.048 | 5% | 0.267 ± 0.037 | -0.102, 0.114 | +69/−41% |
| adverse | 30 | 187 | -0.001 | 0.050 | 44% | 0.238 ± 0.051 | +0.015, 0.129 | +78/−44% |
| adverse | 75 | 142 | -0.003 | 0.032 | 57% | 0.239 ± 0.029 | +0.019, 0.082 | +45/−31% |

**Flash selection is essential.** Omitting the detection term from the likelihood biases the slope by +0.07. With it, the bias is at most 0.004 at 80 and 240 pairs and −0.014 at 30 pairs.

**Contamination.** Without the mixture term the slope bias at 80 pairs is -0.008 instead of +0.004, about a third of the spread.

**Fitted uncertainties** are too small at N = 30 (50% nominal and 44% adverse coverage against 68% ideal) and conservative at N = 240 (97%). Curvature-based uncertainty estimates are unreliable in some adverse cases. Interval calibration by simulation is required; the proposal quotes ensemble spreads.

**Energy distribution:** b is recovered as 0.99–1.01 ± 0.07–0.10.

**Conversion term:** for a 10 kJ catalogue the 1σ range is exp(±3.25·sd(ln D at 10 kJ)) − 1. **Limits.** Population parameters (α, scatter, duration distribution independent of energy) are assumptions. The confirmation curve remains the placeholder. Its 50% point is supported by S18; its width and plateau are not yet replaced, pending TriScape200-to-NAC pairs and more real craters. Sensor cases are scenarios, not probabilities. The 10 kJ term is an extrapolation below the paired sample. Imaging access uses the smooth-sphere ring result times a scalar scheduling factor, not a target schedule.

# 16. S15: Coarse system budget (revision 5)

**Question.** Do the payload, operations and propulsion fit a plausible bus, and what does Option C weigh with its own bus?

**Model.** Generic small-spacecraft allocations by subsystem, with 20% margin on the payload and 10% on the bus. These are assumptions, not selected components.

**Mass (dry).** Table 13 gives the breakdown.

Table: Bottom-up dry-mass allocation (S15).

| Item | Option A | Option C |
|---|---|---|
| Payload | 20.5 kg | 8.4 kg |
| Propulsion (dry) | 15 kg | 9 kg |
| ADCS | 10 kg | 8 kg |
| Power | 13 kg | 10 kg |
| Data handling | 4 kg | 4 kg |
| Telecom | 6 kg | 6 kg |
| Thermal | 5 kg | 4 kg |
| Harness | 6 kg | 4 kg |
| Structure | 26 kg | 16 kg |
| **Dry, with margins** | **118 kg** | **77 kg** |

At Δv = 1.40 and 0.82 km/s this gives:

- **Option A:** 186, 190 and 226 kg wet at 315, 300 and 220 s;

**Power** (both orbit phases, review F11):

- **Average loads:** about 91 W while watching, with 20% margin (event heads 9 W, processor 10 W, ADCS 15 W, telecom 11 W, heaters 12 W, other); 99 W while imaging.
- **Eclipses:** at 3000 km the period is 8.1 h and the longest orbit eclipse 58 min (12% of the orbit). At 300 km the period is 138 min and the longest eclipse 45 min (32.5%).
- **Array:** recharge during the sunlit arc at 90% efficiency plus a 25% end-of-life margin gives 130 W for the watch phase and **190 W for the imaging phase**, which sizes Option A's array. For a deployed, one-axis Sun-tracking array with 28% cells, 0.85 packing, 0.90 end-of-life and 0.90 pointing factors (262 W/m²), this is 0.72 m². Option C keeps 130 W (0.50 m²).
- **Battery:** 250 Wh, set by a 4 h lunar eclipse at 45 W survival load; the orbit eclipses need 137 Wh (300 km) and 163 Wh (3000 km) at 60% depth of discharge.
- **Mass check:** array, battery and power unit come to about 8.6 kg bottom-up (3.5 kg/m² plus 1 kg mechanism, 120 Wh/kg, 3 kg PCDU), within the 13 kg allocation.

**Data:**

- **Into the processor:** 0.7–22 MB/s raw events at 0.03–1 Hz background activity alone; moving texture, calibration steps and particle hits are not included.
- **Stored:** about 1.6 MB/day of flash records (≤1 false trigger per hour plus detections, 50 kB each).
- **Phase-2 imaging:** the joint model predicts 732 located sites above the imaging cut for the nominal sensor, which would need 146 GB and 74.5 kbit/s over 182 days. We size for a conservative allocation of **880 sites** (about 1.2× nominal, and at least the count of every sensor case within 0.3%): 176 GB and **89.5 kbit/s**. **Link.** X-band, 5 W RF, 0.3 m antenna (25.8 dBi), to a 13 m-class station (G/T 37 dB/K), with 4 dB losses, coded E_b/N₀ 4.5 dB and 3 dB margin: 2.41 Mbit/s **while in contact**. The 880-site allocation therefore needs 3.7% contact duty (0.89 h per day) before overheads, occultations, pointing and station scheduling.

**Limits.** Every value is an allocation. Deployment and orientation of the array, end-of-life degradation and the communications schedule are stated assumptions. A component-level design is full-concept work.

# 17. S16: Event-sensor trade (3 November 2026)

**Question.** Which event sensor, with which settings, head size and cooling, should the payload use, given published measurements instead of the S10 envelope alone?

**Model.** Version 4 of `event_response.py` adds five cases built from measured IMX636 data (McReynolds et al., AMOS 2025):

- dark current 1.1 fA;
- photoreceptor corner frequencies that imply τ_ref ≈ 0.27 ms on the linear law;
- default-bias background activity of 0.03 Hz with a lognormal spread of σ = 0.5 between pixels;
- the noisiest 2% of pixels masked.

The cases are the measured IMX636, tuned biases (C = 0.10, 1 Hz), a warm sensor (5.55 fA), fifteen 25 mm heads, and an IMX646 surrogate. The surrogate halves τ_ref; it is not a measurement. `sensor_trade.py` rebuilds the S14 population identically and evaluates all cases on one Monte Carlo stream. `joint_model.py` is pinned to the 16 revision-5 cases, so its results do not change.

Table: Option A pairs in 2.5 years for the sensor-trade cases (one Monte Carlo stream; the nominal median on this stream is 205 instead of 210).

| Sensor case | Flash share (confirmable craters) | Pairs at nominal factors | Median | P10 | P(≥80) |
|---|---|---|---|---|---|
| Nominal (revision 5) | 0.62 | 294 | 205 | 118 | 0.98 |
| Pessimistic (revision 5) | 0.20 | 93 | 74 | 46 | 0.41 |
| Measured IMX636 | 0.81 | 384 | 260 | 139 | 0.99 |
| IMX636, tuned biases | 0.89 | 422 | 273 | 144 | 0.99 |
| IMX636, warm (5.55 fA) | 0.74 | 352 | 237 | 129 | 0.99 |
| IMX636, fifteen 25 mm heads | 0.93 | 458 | 296 | 151 | 0.99 |
| IMX646 surrogate | 0.86 | 411 | 274 | 143 | 0.99 |

**Recommendations** ([sensor trade](../sensor_trade/sensor_trade.md)):

- the IMX636 as baseline, with the IMX646 as an option (no low-light data);
- default biases;
- a cooling requirement of dark current ≤1.5 fA (TBC). The yield loss when warm is small, but a warm sensor lets the particle false-trigger bound reach about 10 per hour;
- six 16 mm heads, because the 25 mm heads add only 14% with the measured sensor.

The revision-5 cases remain the reference in the proposal; the trade shows that they are conservative.

**Limits.** The measured values come from one published characterisation at an unreported temperature. The pixel-to-pixel spread of the background activity is assumed, and the tuned-bias case needs higher 2 s thresholds under bright earthshine (S17).

# 18. S17: Measured lunar texture (3–4 November 2026)

**Question.** Do albedo contrast and slopes of the real near side, moving through the view under earthshine, keep the S10 thresholds within the one-per-hour false-alarm budget?

**Texture model** (`texture_map.py`, run on the team computer):

- **Inputs.** The LROC WAC Hapke-normalised 643 nm mosaic (399 m pixels; tiles E350N0450, E350N3150 and E350S3150, together 70° S–70° N over 270–90° E) and LOLA LDEM_64 (474 m).
- **Background.** Both maps are resampled to the 0.9 km event pixel. The background of each pixel is dark current plus earthshine × albedo × Lunar-Lambert shading for the Earth at the sub-Earth point (Earth more than 10° above the horizon, |latitude| < 60°; 13 million pixels).
- **Histogram.** For each window W the script records the clipped log-brightness rise max(0, ±∇ln B · 0.41 px/s · W) summed over every 2×2 and 3×3 group, for backgrounds of 1.3×10⁴ and 2.5×10⁴ e⁻/s (dark current 1.0 and 1.1 fA) and 4×10⁴ and 6×10⁴ e⁻/s (5.55 fA). The brightest earthshine in the S13 population gives about 2.5×10⁴ e⁻/s.

**Count model** (`texture_measured.py`). A group with summed rise S gains about μ = S/C events.

- **Pixel-model check.** In a simulation of the S10 pixel model under a log-linear ramp (2 s window, 2×2 groups, nominal and measured IMX636 at 2.5×10⁴ e⁻/s), the added count variance was **0.08–0.27 × μ**, far below Poisson.
- **Adopted model.** A per-pixel binomial with variance about 0.35 μ, in which every pixel can fire one event more than its share. A Poisson count is kept as a bound, and a phase-only model as a lower bound.
- **Trigger rule.** It is applied exactly: the group sum must be at least n_min, with at least three pixels contributing.

Table: False triggers per hour over six heads with the adopted S10 thresholds.

| Sensor | Background [e⁻/s] | Assumed edge (S10) | Measured texture | Poisson bound |
|---|---|---|---|---|
| Nominal | 1.3×10⁴ | 0.39 | 0.09 | 0.43 |
| Nominal | 2.5×10⁴ | 0.20 | 0.12 | 21.9 |
| Measured IMX636 | 1.3×10⁴ | 0.18 | <0.001 | 2.0 |
| Measured IMX636 | 2.5×10⁴ | 0.35 | 0.95 | 125 |
| IMX636, tuned biases | 2.5×10⁴ | 0.39 | **9.6** | 61 |
| Pessimistic | 6×10⁴ | 0.18 | 0.16 | 0.17 |
| IMX636, warm | 6×10⁴ | 0.25 | 0.002 | 1.5 |

At the 99.9th percentile the measured texture is close to the assumed edge. For the nominal sensor at 2.5×10⁴ e⁻/s in the 2 s window, 0.1% of 2×2 groups receive more than 4.8 counts, against 4.5 counts in 1% of groups for the edge. The distribution then ends steeply: 0.01% exceed 7.5 counts, and none exceed 16.

**Texture-aware thresholds and yield.** The stored S10 flashes were simulated again with their original seeds, which reproduce the stored detections exactly, and were detected with three new threshold sets:

- **raise only:** max(adopted, texture-aware);
- **Poisson bound, raise only;**
- **texture-aware:** both raised and lowered.

The tuned-bias IMX636 needs 2 s thresholds of 77/134 instead of 70/116. In the Poisson bound, masking 0.04% of the trigger groups restores the budget at the adopted thresholds. The Option A yield with one population and one Monte Carlo stream is unchanged when thresholds are only raised, even to the Poisson bound: nominal 294 (median 208), pessimistic 93 (74), measured IMX636 384 (257). With the full texture-aware set it rises by 0 to 4%: 297, 93 and 400.

**Limits.**

- The model resolves 0.9 km and has earthshine only: no change of the Earth's phase within a window and no scattered light.
- It is limited to |latitude| < 60°; the far side has no earthshine.
- The 25 mm cases (smaller pixels, faster drift) are not computed.
- The energy grid (steps of ×2–2.5) cannot resolve small threshold shifts.

Results: [LROC/LOLA follow-up](../../../supporting_studies/outputs/lroc_lola_update/lroc_lola_update.md), section 2; data in `texture_histograms.json` and `texture_measured.json`.

# 19. S18: Crater tests on real LRO images (3 November 2026)

**Question.** Does the S14 confirmation curve (k = 3.5 px, w = 0.15, c_max = 0.85) hold on real lunar images, and how well are diameters measured?

**Camera model** (`crater_test.py`):

- **Resampling and noise.** NAC images are resampled to the TriScape200 at 300 km: 0.9 m pixels, 0.6-pixel blur, shot and read noise for 300 e⁻ at 65° incidence scaled with cos i, and RGB Bayer sampling with demosaicking.
- **Detection.** The threshold is set for 0.01 false candidates per km², from null runs extrapolated with an exponential tail.

**Test 1: same image, injected craters** (`real_tiles/`):

- **Images.** Four real NAC tiles from the CraterDANet dataset, with native pixels of 0.60–0.84 m and Sun incidence of 62–82°. Before and after are the same tile apart from noise.
- **Craters.** 1800 craters of 1.8–8 m, detected with the kit's matched filter (bowl shading plus a bright halo).
- **Result** for depth/diameter 0.14: 50% at **3.58 px (3.2 m)**, width 0.10, plateau 0.99 (an upper bound). The diameter error is 0.46 px/D_px with a +3% bias. For depth/diameter 0.20 and 0.10, k is 3.26 and 4.19 px.

**Test 2: real new craters** (`real_pairs/`):

- **Selection.** Eight LROC new craters of 2.5–9.8 m with their real before/after NAC pairs. The two images of each pair have incidences within 2.5° of each other, between 27° and 52°.
- **Registration.** A global affine fit to image features, then a cubic residual shift field from sub-pixel correlation of 192-pixel tiles. Residual shifts fell from 0.45–2.4 px to 0.06–0.10 px (C3, C5, C7), to 0.12–0.16 px (C1, C4), and only to 0.44–0.95 px (C2, C6, C8; not used).
- **Detectors.** Thresholds come from each pair itself, with 120 m around the crater masked. Two detectors were used: the kit's bowl filter, and a new reflectance-anomaly detector (a multi-scale Laplacian of Gaussian of the locally gain-matched difference, both signs).
- **Located real craters** (found out of 4 noise repeats, anomaly detector): C1 (2.5 m, 0.16 px) 0, C3 (3.2 m, 0.10 px) 4, C4 (3.5 m, 0.12 px) 1, C5 (4.0 m, 0.06 px) 4 and C7 (6.2 m, 0.06 px) 4. The anomaly thresholds were 6.6–8.2 in the well-registered pairs, close to the bowl filter's noise-only level of 5.8–6.5, and 12–13 in the two poorer pairs. The bowl filter found only C5 and C7.
- **Reflectance profiles.** C1, C3, C4 and C7 have dark halos of −6 to −12% within 0.5 D, still about −2 to −3% at 2–4 D. C5 has a bright core of +23% that vanishes by 1.5 D.
- **Injection into the real pairs.** 60 craters per diameter (1.8–6.5 m, depth/diameter 0.14) were injected with four halo models and detected with the anomaly detector:

Table: Confirmation curve fitted to craters injected into real NAC pairs (anomaly detector).

| Halo model | Pairs | k | 50% diameter | Width w | c_max |
|---|---|---|---|---|---|
| Dark (−8%, to 6 R; measured type) | C3, C5, C7 (well registered) | 3.63 px | 3.3 m | 0.21 | 1.00 |
| Dark (−8%, to 6 R) | all five | 3.85 px | 3.5 m | 0.26 | 0.68 |
| Weak dark (−4%, to 4 R) | well registered | 5.35 px | 4.8 m | 0.12 | 0.73 |
| Bright (+7.5%, to 3 R; kit model) | well registered | 5.20 px | 4.7 m | 0.14 | 0.61 |
| None | well registered | 5.41 px | 4.9 m | 0.11 | 0.61 |

**Yield** at nominal factors for these curves (`real_pairs_yield.py`):

| Sensor | Placeholder | Well registered, c_max 0.85 | Well registered, fitted c_max 1.0 | All five, c_max 0.68 |
|---|---|---|---|---|
| Nominal | 294 | 277 | 325 | 202 |
| Measured IMX636 | 384 | 367 | 431 | 267 |
| Pessimistic | 93 | 89 | 104 | 68 |

**Consequences for S14 and the pipeline.**

- **k is confirmed.**
- **c_max is set by registration quality.** The Monte Carlo range of 0.65–0.95 covers the measured 0.68–1.0 except at its top.
- **Proposed requirements, awaiting team adoption:** about 0.1 NAC pixel registration after orthorectification and a reflectance-anomaly search.

**Limits.**

- Five located craters, three in well-registered pairs. The located craters may be the more visible ones.
- NAC–NAC pairs rather than TriScape200–NAC pairs.
- The craters were 2–8 years old in their after images.
- Thresholds are extrapolated from 3–9 km² of null area per pair.
- No diameter error was measured on real pairs.

Results: [crater test](../../../supporting_studies/outputs/crater_test/crater_test_results.md) and [LROC/LOLA follow-up](../../../supporting_studies/outputs/lroc_lola_update/lroc_lola_update.md), section 3; data in `data/crater_injection_test/`.

# 20. S19: Whole-scene event streams (5–11 November evidence)

> **Current-status note, 19 November 2026:** the following tables and paragraphs preserve the 5–11 November snapshot. Use the [12 November regeneration and 18 November sensitivity](../../../event_stream_simulator/outputs/event_stream_sim.md) for current scene results: unmasked terminator counts 420/184 (near/far), +3 px count 8, corrected limb rms 0.79 ln, and step-converged prompt-deposit V10. The jitter data are now at `data/event_stream_sim/jitter/jitter_sweep_2026-11-11.json` (35 runs, five paths); ≈90″/s rms is proposed, TBR, instead of the earlier ≈60″/s below. Limb/full-frame reruns are complete. S14's stored yield distribution remains conditional and unchanged; this review ran no simulation.

**Question and method.** Do patch-level detection and energy estimates transfer to a moving lunar scene? The [event-stream methods](../../../event_stream_simulator/analysis/event_stream_sim/README.md) propagate WAC albedo, LOLA shading, field/range maps, PSF, first-order pixels, photon/dark noise, background activity, hot pixels, refractory time and charge-deposit stresses into events, group triggers and energy records. Crops are normally 320 × 180 px; one 6 s case uses all 1280 × 720 pixels. Numerical adaptive substeps are checked for selected exponential flashes, not all particle/light-curve cases. The [results note](../../../event_stream_simulator/outputs/event_stream_sim.md) gives the recorded configurations and full tables.

| Test | Recorded result | Interpretation |
|---|---|---|
| Terminator masks, 20 s | Near/far false candidates 431/188 without the margin, zero with it; +3 px map shift restores 9 | Mask margin and on-board map/pointing knowledge are coupled; local disabled-group fractions ≈7–17% are not global completeness |
| Energy correction in scenes | Corrected rms ln(E_est/E_true) 0.30 at the terminator, 0.91 at the limb | Static-flash calibration does not qualify scene-level D03; ln-rms is not fractional 1σ |
| Deadtime, retrained exponential cohort | 566/576 detections at 10 and 50 µs; corrected rms 0.26 and 0.51 ln | Energy information can degrade without a detection loss; 10 µs is provisional |
| High-pass, retrained | At model corners 0.1/0.5 Hz, corrected rms 0.30/0.48 ln | Calibration mismatch is partly recoverable; lost detections of faint long flashes are not |
| Particle stresses | No prompt candidate among 1055 hits with masking; 1–4 among 102 in delayed/spread cases | Delayed-charge occurrence is unknown; these are vulnerability tests, not flight rates |
| Particle step sensitivity (V10) | Prompt ON events per heavy hit 3.8 at 0.5 ms versus 2.4 at 0.1 ms | Prompt-hit event output is not converged; the per-pixel trigger count cap reduces sensitivity of the trigger outcome |

Zero false candidates in a 20 s crop give only 5.8×10⁻⁵ array-hours and a 95% upper rate of ≈5.2×10⁴ per array-hour. The six-head, one-per-hour target therefore still rests on the declared null model; spatial/temporal correlations, achievable background knowledge and rare tails remain open. S17 mean texture counts are checked locally, without establishing its extreme-tail conservatism. Dark-disc rates of about 4×10⁴ events/s per head are input-volume estimates; processor/readout feasibility is not demonstrated.

**Onset sweep, 11 November.** `data/event_stream_sim/onset_sweep_2026-11-11.json` records 2688 exponential flashes at 3750 km, background 1.3×10⁴ e⁻/s and 2.35–2.5 s of prehistory. Of 2184 detections, 1996 use 50 ms and 188 use 200 ms; neither long window contributes. Twenty-four detections (1.1%) have an onset more than 10 ms early, with a minimum of −80 ms. Their corrected errors remain inside the scatter of the other records. This bounds the concern only for this flat-scene background/cohort, not all mission conditions.

**Jitter sweep, 11 November.** `data/event_stream_sim/jitter_sweep_2026-11-11.json` contains sixteen 20 s runs, two crops and eight flashes per run. The jitter is a first-order Gauss–Markov process, one path scaled in amplitude, with 0.5 s baseline correlation time and 0.1/2 s variants. Angular rates below are rms over the 50 ms scene keyframes.

| Terminator rms angular rate [arcsec/s] | False candidates in 20 s | Flashes detected | Complete flash records with absolute ln error >1 |
|---|---|---|---|
| 125 | 0 | 8/8 | 0 |
| 249 | 2 | 8/8 | 1 |
| 254 (0.1 s correlation time) | 2 | 8/8 | 0 |
| 747 | 53 | 8/8 | 2 |

The near-side crop gives no false candidates across the tested range. Comparable rates at different amplitudes/correlation times have similar effects: an rms-angle specification alone is inadequate. Near lit terrain the correction can become severely biased even while all flashes remain detected. About 60 arcsec/s is a proposed margin for study; it is not a qualified limit. Reaction-wheel tones, other scenes and finer resolution of the 0.1 s process remain untested.

![Current pointing-jitter sensitivity: 35 stored runs with the 11 November code, including five jitter paths. The plotted results supersede the earlier table above and remain conditional crop tests, not a mission false-alarm measurement.](../../../event_stream_simulator/figures/jitter/jitter_sweep.png)

**Evidence versions and science consequence.** Main scene runs retain the 5 November code; the onset/jitter sweeps use the 10 November code. The current model applies cos θ to flash point-source gain, versus cos⁴θ for the extended scene. Limb/full-frame reruns are outstanding; the IMX646 is still a surrogate. The energy correction needs training/validation in drifting scenes and a condition-dependent uncertainty/selection model. Mask losses and those errors have not been propagated into S14: its ≈210/≈75 nominal/pessimistic medians are unchanged conditional baseline outputs, not qualified yields from these scenes.

# 21. S20: GMAT short-case verification (5 November evidence)

The [GMAT study](../../../gmat_lunar_setup/outputs/README.md) supplies a provisional 2031 Option A setup. The propagated model uses lunar gravity at 80 × 80, solid tides, third-body gravity, direct cannonball SRP with occultations and relativistic correction. Spacecraft properties, optical coefficients and arrival/plane geometry are assumptions. Fifteen saved short cases have status `passed` in `outputs/gmat_lunar_setup_2026-11-05/scripts/validation_all.json`.

| Check | Saved result |
|---|---|
| 3000 km natural drift, 30 d | Minimum sampled radius altitude 2996.65 km; maximum osculating eccentricity 0.000665 |
| 300 km natural drift, 30 d | Minimum sampled radius altitude 289.00 km; maximum osculating eccentricity 0.005545 |
| Compressed lowering | 228.159 + 283.189 = 511.348 m/s; 10.787 kg fuel and final mass 128.887 kg for the provisional study mass/Isp |
| Artificial controller exercise, 3 d | Two corrections, 0.1943 m/s total; verifies controller bookkeeping, not a maintenance allocation |
| Gravity truncation, low orbit, 7 d | Endpoint position differences 0.868 m (40→80) and 0.0020 m (80→120) |
| Tighter integration, low orbit, 7 d | Endpoint difference 0.00014 m from nominal settings |
| SRP low/high versus nominal, 7 d | Endpoint differences 12.93/24.25 m at 3000 km; 3.85/7.21 m at 300 km |

These are sampled geometric-altitude and osculating diagnostics, not terrain-clearance guarantees. Short numerical convergence is not gravity-field uncertainty or three-year convergence. The recorded maintenance history covers only 7.375 d; no full-mission trajectory, coverage or maintenance-budget closure is available. Control is exact-state and impulsive, without finite thrust or navigation/execution errors. A separate uniform 400 K disk screen gives lunar IR acceleration ≈6.6×10⁻⁸ m/s² at 300 km, comparable to direct SRP in that case; lunar radiation and spacecraft geometry require further modelling. The study supports setup consistency and the lowering budget, not Option A adoption or S14's yield.

# 22. Overall limitations

1. **Geometry.** The yield/coverage model uses a smooth sphere. S19 adds terrain shading for selected crops, without whole-Moon terrain-aware completeness, parallax or libration. Polar imaging remains unverified.
2. **Orbits.** S2/S3 contain only J2 and Earth, with ideal burns. S20 adds a higher-fidelity short-case GMAT model, but no maintained full-mission trajectory or coverage verification. The ellipse controller in S3 does not maintain its target periapsis.
3. **Sensor.** S10 and S11 bound an unmeasured low-light response with a first-order pixel model and 16 parameter cases; S16 adds cases built from one published IMX636 characterisation. The false-alarm result holds for a declared noise model and independent pixels; S17 checks the texture term with measured maps. S19 adds refractory/high-pass and scene stresses; these do not qualify the mission false-alarm tail or scene-level energy precision. Literature-grounded bounded models remain acceptable for this concept, with explicit uncertainty.
4. **Science model.** The scatter terms, the crater-rule uncertainty and the confirmation curve are assumptions with ranges. The 50% point of the confirmation curve is supported by S18; its width and plateau are not yet replaced. The crater rate is extrapolated below 10 m, the fit intervals are not calibrated, and the calibration offsets are not fitted as explicit nuisance parameters.
5. **Not simulated.** We did not simulate subsystem designs beyond S15, image quality beyond a first signal-to-noise (SNR) estimate, reliability or cost. The crater-detection pipeline is tested in S18 only in a first form, on NAC–NAC pairs.
6. **Secondary objectives.** The proposal's secondary objectives (§8.1) are not yet simulated:
   - S1, the whole-Moon flash-energy rate, reuses the exposure and detection-efficiency results of S1, S10 and S14;
   - S2, the leading/trailing asymmetry, has only a first sample-size estimate. A fit of 1 + A cos β to N flashes gives σ(A) ≈ √(3/N), so A ≈ 0.12 needs about 2000 flashes above a common threshold for 3σ. The S14 catalogue holds about 1200 flashes (nominal), 3000 (measured IMX636, S16) and 220 (pessimistic).

# 23. Reproduction

From `analysis/impact_energy_conversion/`, run in this order. Outputs go to `../../data/impact_energy_conversion/` and `../../figures/impact_energy_conversion/`.

1. `python coverage.py` (about 3 min)
2. `python orbit_stability.py` (about 15 min)
3. `python orbit_trades.py` (about 60 min)
4. `python imaging_access_check.py --one-season` (about 5 min; without the flag, four seasons; add `--ellipse` to recompute the stored ellipse result)
5. `python observed_background.py` (about 10 s)
6. `python event_response.py` (about 150 min on one core for the 16 cases). Alternatively, use two parallel parts and merge after both finish (Bash example):

    ```bash
    group1=nominal,pessimistic,optimistic,warm_dark
    group1+=,high_C,slow,noisy,nominal_25mm
    group2=slow10,cap3,law_sqrt,noise3,ba_burst,ba_telegraph
    group2+=,ba_hetero,pessimistic_25mm
    python event_response.py 1 "$group1" &
    python event_response.py 2 "$group2" &
    wait
    python event_response.py merge
    ```
7. `python photometry_calibration.py` (about 15 min)
8. `python joint_model.py` (about 40 min; `python joint_model.py yields` recomputes the yields and keeps the fits, `python joint_model.py fits=30,80` reruns selected fits, `python joint_model.py assoc` recomputes only the association table)
9. `python science_model.py` (under 1 min; reads steps 1–8)
10. `python system_budget.py` (seconds; reads step 9)
11. `python transfer.py` (seconds)
12. Export the full proposal with `python build_report.py`, the short proposal with `python build_report.py summary`, and this report with `python build_report.py simulation` (needs pandoc and XeLaTeX). See the methods README for other documents; avoid `all` when historical review Markdown sources are absent.

Follow-up studies (3–4 November 2026):

13. Sensor trade (S16; about 60 min on two cores):

    ```bash
    python event_response.py 5 m636,m636_tuned,m636_warm
    python event_response.py 6 m636_25mm,m646_surrogate
    python event_response.py merge_add
    python sensor_trade.py
    ```
14. On the team computer, with the WAC and LOLA files in `data/external/`: `python texture_map.py <tile> <tag> <name:dark:I0> ...` for the three tiles, merged into `texture_histograms.json`. Then `python texture_measured.py` (about 40 min) and `python texture_figures.py` (S17).
15. From `analysis/crater_injection_test/` (S18):
    - `real_tiles/real_tiles_run.py` for the tile data (data cloned separately; run with `python -I`);
    - on the team computer, `real_pairs/cut_windows.py`;
    - `python -I real_pairs/real_pairs_run.py` (about 1–2 hours);
    - `real_pairs/real_pairs_figures.py` and `real_pairs/real_pairs_yield.py`.


Recorded core revision-5 run environment: Python 3.13.18, NumPy 2.5.3, SciPy 1.18.1, Matplotlib 3.11.2.

Supporting-study reproduction: see the [event-stream methods](../../../event_stream_simulator/analysis/event_stream_sim/README.md), [remaining simulator work](../../../event_stream_simulator/outputs/event_stream_sim.md#5-options-needing-additional-data) and [GMAT methods and reproduction limits](../../../gmat_lunar_setup/analysis/gmat_lunar_setup/README.md). This export uses recorded results; no simulation data were regenerated.
