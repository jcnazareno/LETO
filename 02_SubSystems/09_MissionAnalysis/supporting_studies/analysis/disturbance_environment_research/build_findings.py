"""Build the dated research note from reviewed numerical outputs and evidence."""
from pathlib import Path
import json,math,re
ROOT=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent
O=ROOT/'outputs/disturbance_environment_research_2026-10-29'
R=json.loads((A/'model_results.json').read_text());S=json.loads((A/'supplement_results.json').read_text());H=json.loads((A/'distant_results.json').read_text());E=json.loads((A/'evidence.json').read_text())
lun={x['name']:x for x in R['lunar']};p=R['pointing'];im=S['image_motion']
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(str(v) for v in row)+' |\n' for row in rows)
def sci(x):return f'{x:.3g}'
leo=table(['Case / atmosphere','Mean density [kg/m³]','Initial loss [km/day]','Loss at day 30 [km]','Held-altitude drag makeup [m/s/year]','Extended horizon result'],[[x['name'],sci(x['rho_kg_m3']),f"{-x['initial_da_km_day']:.4f}",f"{x['h0_km']-x['h30_km']:.3f}",f"{x['drag_makeup_m_s_year_at_held_alt']:.2f}",f"{x['end_h_km']:.1f} km at {x['duration_d']:.1f} days"] for x in R['leo']])
lunar=table(['Initial case, degree/order 80','Day-30 hp / ha [km]','Minimum osculating hp [km]','Sampled a range [km]','Interval / stop'],[[x['name'],f"{x['day30'][2]:.2f} / {x['day30'][3]:.2f}",f"{x['min_osculating_hp_km']:.2f}",f"{x['a_range_km'][0]:.2f}–{x['a_range_km'][1]:.2f}",f"{x['duration_d']:.1f} days"+(' / 11 km radial buffer' if x['duration_d']<60 and x['name']=='Moon50_N80' else '')] for x in R['lunar'][:4]])
torque=table(['Matched case','GG arbitrary-attitude peak [N·m]','GG at 1° [N·m]','Sunlit SRP bound [N·m]','Magnetic scenario [N·m]','Body IR hot bound [N·m]'],[[x['case'],sci(x['GG_peak_Nm']),sci(x['GG_1deg_Nm']),sci(x['SRP_sunlit_bound_Nm']),sci(x['magnetic_30mAm2_bound_Nm']),sci(x['IR_envelope_Nm'])] for x in R['torques']])
unload=table(['Constant bias [N·m]','Cadence for 0.025 N·m·s [days]','Annual RCS impulse [N·s]','Annual propellant at 80 s Isp [g]','Lost time for 20 min/dump [%]'],[[sci(x['bias_Nm']),f"{x['cadence_d']:.2f}",f"{x['annual_impulse_Ns']:.2f}",f"{x['annual_prop_g']:.2f}",f"{100*x['science_loss_fraction_20min_dump']:.3f}"] for x in S['unloading']])
convergence=table(['Changed model','Δ day-30 osculating hp relative to matched degree-80 case [m]'],[[k.replace('_hp30_difference_km',''),f'{v*1000:.2f}'] for k,v in R['checks'].items() if k.endswith('_difference_km')])
decisions=[
 ['Orbit/lifetime','Keep polar or quasi-frozen low-lunar and distant observer as trade candidates. Do not baseline 50 km circular by default.','50 km reaches the screening buffer near day48; LRO flight maintenance143m/s/year versus <5 in frozen geometry.','D05–D06/D09; Mission Analysis/Propulsion'],
 ['Whole-surface coverage','Map both hemispheres and poles through the complete visibility/illumination timeline before selecting architecture.','A single L2 farside observer does not independently meet the entire-surface constraint. Frozen/low-maintenance does not imply adequate sample yield.','D05–D06; Payload/Mission Analysis'],
 ['Maintenance allocation','Use LRO143m/s/year only for its50±15km envelope. Screen a favourable frozen geometry near <5m/s/year. For an L2 study retain16–30m/s/year sensitivity until its navigation/control analysis.','Published flight/design comparators;100km maintenance remains TBR, not zero because a30-day run survived.','D05/D09; Propulsion/Operations'],
 ['Wheel class','Investigate approximately0.05Nms class wheels; include array mapping, bias reserve and a10deg/60s slew.','Environmental torque is sub-microNm, but slew requires0.121mNm and3.64mNms. CW0500 provides10mNm/50mNms per wheel at rated conditions.','Structure/Power/ADCS'],
 ['External unloading','Provide thruster unloading and detumbling. Use magnetic actuation only after proving local authority and three-axis operation.','A0.2Am2 torquer gives10microNm at50microT but only6nanoNm at30nT, below the illustrative30nanoNm bias.','D09; ADCS/Propulsion'],
 ['Geometry','Control pressure-centre offset and thermal asymmetry; prefer balanced arrays/radiators where feasible.','SRP torque scales as area×offset. Increasing the2cm offset to10cm multiplies torque, annual unloading impulse and propellant by5.','Structure/Thermal/Power/ADCS'],
 ['Pointing/localization','Keep knowledge, tracking error, interval stability and structural jitter separate. Do not claim sub-arcsecond hardware performance from this budget.','1arcsec at50000km is242m at nadir;0.2arcsec is0.10pixel in the prior optical fixture.','D02–D04; Payload/ADCS/ODH'],
 ['Observation windows','Schedule dumps, slews, burns and calibration outside high-value dark-surface windows; include settling/reacquisition in the timeline.','Dump-only loss0.048–0.480% under the bias sensitivity; navigation, occultations, power and stationkeeping add other losses.','D02–D06/D09–D10'],
 ['Component/control evidence','Obtain wheel exported force/torque spectra and evaluate the structural transfer before tightening jitter allocations.','Measured historic wheel imbalances differ from catalogue values and have speed-dependent resonances.','ADCS/Structure/Payload'],
 ['SRR effort','Carry a compact orbit/ADCS/propulsion comparison into2–3 of the final50pages. Keep this audit and time histories as supporting research.','One focused science objective and four-person capacity favour explicit bounds over a bespoke high-fidelity flight-dynamics toolchain.','All interfaces; no new coequal science objective']
]
(A/'decisions.json').write_text(json.dumps(decisions,indent=2))
decisiontable=table(['Topic','Provisional concept action','Quantitative basis','Affected drivers / areas'],decisions)
note=f'''# Orbital and attitude disturbance environment

Prepared **29 October 2026**. Quantitative supporting study for SMD concept/SRR work. **No orbit, spacecraft size, component, control allocation or numerical D requirement is approved by this note.**

## Findings that change the design

1. **Low lunar orbits usually become unsafe through changes in eccentricity/periapsis, rather than Earth-like drag decay.** The 100 km polar fixture reaches an osculating periapsis of **{lun['Moon100_N80']['min_osculating_hp_km']:.1f} km** in 30 days; its sampled semimajor axis spans only **{lun['Moon100_N80']['a_range_km'][1]-lun['Moon100_N80']['a_range_km'][0]:.2f} km**. The 50 km fixture crosses the assumed **11 km radial screening buffer at {lun['Moon50_N80']['duration_d']:.1f} days**. This is not a terrain-impact prediction or a universal lunar lifetime.
2. **Geometry can save more propellant than a small change in bus technology.** LRO flight operations report about **143 m/s/year** in the tightly maintained 50 km science orbit and **less than 5 m/s/year** after transition to frozen geometry. Those are different envelopes, not interchangeable maintenance rates. [DE05](https://ntrs.nasa.gov/api/citations/20230010952/downloads/Mesarch_LROLongTermOrbit_Preprint_20230727.pdf)
3. **Lunar gravity-gradient torque remains comparable to LEO.** At 100 km it is **61.7%** of the 400 km LEO value for the same inertia and attitude. Lunar magnetic torque is much smaller in the declared field scenarios, so a familiar LEO magnetic unloading strategy loses authority.
4. **Distant observation reduces central lunar gravity-gradient torque by roughly four orders of magnitude**, while direct solar pressure is almost unchanged. The reference halo spans **{H['range_km'][0]:,.0f}–{H['range_km'][1]:,.0f} km** from the Moon and is dynamically unstable. Distant location does not remove maintenance, navigation, range-dependent sensitivity or whole-surface coverage requirements.
5. **Wheel storage, geometry and jitter evidence matter more than environmental wheel torque capability in this fixture.** A 30 nN·m bias fills 0.025 N·m·s in **9.65 days**. Removing it over a year with the assumed balanced 15 cm thruster couple takes **6.31 N·s**, about **8.0 g** of propellant at 80 s Isp. Neither the torque budget nor the illustrative controller establishes the earlier sub-arcsecond pointing allocations.

## 1. Comparison contract

All local physical calculations use SI units internally. Lunar altitudes are above the **1738 km gravity reference sphere**, not the 1737.4 km volumetric mean radius or a local DEM. Earth radii use 6378.137 km. Differences in this convention must be retained when comparing published values.

| Parameter | Matched reference fixture | Status / sensitivity |
| --- | --- | --- |
| Spacecraft mass | 30 kg | Assumption; not a selected platform. Too small for the D01 200 mm illustrative optics and not the 30 Oct 80 kg / 16-head reference; recompute absolute torque, momentum and propellant for a selected spacecraft |
| Uniform box dimensions, x/y/z | 0.20 / 0.30 / 0.40 m | Inertia derived as m(b²+c²)/12; arrays/optics idealized into the fixture |
| Principal inertias, x/y/z | 0.625 / 0.500 / 0.325 kg·m² | Diagonal; ΔI=0.300 kg·m². Real appendages require CAD-derived inertia |
| Projected drag and radiation area | 0.30 m² | Effective area held equal for comparison; 0.10–0.60 m² gives one-third to twice area-driven force/torque |
| Cd / effective Cr | 2.2 / 1.5 | Provisional free-molecular / cannonball optical coefficients; Cr sensitivity1–2 |
| Aerodynamic and photon-pressure moment arm | 0.020 m perpendicular maximum | 0.005–0.10 m gives0.25–5 times torque. Directions and actual plate properties are unresolved |
| Residual magnetic dipole | 0.030 A·m² | Assumption; 0.003–0.30 gives0.1–10 times torque |
| Anisotropic thermal emission | 2 W at0.10 m, collimated upper recoil | Separate from incoming planetary IR; 0–10 W sensitivity |
| Earth magnetic scenario | 50 µT | Tens-of-µT LEO screening fixture, no WMM history [DE16](https://www.ncei.noaa.gov/products/world-magnetic-model) |
| Lunar external/crustal field scenarios | 5 / 30 / 100 nT | Sensitivities, not certified percentiles or a propagated magnetic model; no Earth-like dynamo [DE15](https://doi.org/10.1029/2010JE003650) |
| Thruster couple | Two opposing1 mN forces, each0.15 m from COM | Assumed independently commanded, balanced geometry. Actual module placement remains open |

The lunar epoch is **2026-10-29 00:00:00 UTC**, converted by SPICE to ET/TDB. States propagate in **Moon-centred J2000/ICRF**, with differential Earth/Sun forces. Initial Keplerian elements are referenced to the **epoch lunar PA equator, frozen inertially**; initial Ω=0°,i=90°,e=0,u=0° for circular cases. Ω=90° is the orientation sensitivity. The elliptical case has hp=30 km,ha=200 km,ω=270°,ν=0°,i=90°,Ω=0°. Nonsingular radius/eccentricity metrics drive the conclusions; argument of periapsis is undefined at exact circularity.

Earth fixtures start circular, i=51.6° at400 km and98° at600 km, Ω=u=0 in a simplified equatorial frame at the same UTC epoch. The rounded600 km inclination is **not an exact Sun-synchronous design**. The Earth model evolves mean circular a and J2 node, not a full Cartesian ephemeris; its e stays zero by construction and its uncomputed short-period elements must not be presented as predictions.

The JPL halo is a separate **autonomous circular restricted three-body problem (CRTBP)**, rotating barycentric x toward the Moon and z along Earth–Moon angular momentum. It has no unique calendar realization. Phase zero may be placed at the study epoch for plotting, but this is **not an ephemeris halo at that date**. Its normalized state and system constants are preserved in [distant results](../../analysis/disturbance_environment_research/distant_results.json).

## 2. What “decay” means in these cases

Drag removes mechanical orbital energy. For near-circular Earth motion, da/dt follows the atmospheric drag power; changing density as altitude falls accelerates the loss. J2 and mascons principally change node, apsis and eccentricity. In a rotating gravity field or a multi-body problem, two-body osculating energy can vary without an atmospheric-style sink. A low pericentre, resonance, unstable manifold departure or collision risk is therefore not a universal semimajor-axis decay rate.

At a libration orbit the Moon and Earth jointly define the motion. A Moon-centred Keplerian semimajor axis or an acceleration magnitude integrated over time is an unsuitable stationkeeping estimator. The local halo study instead propagates a reference state, an offset state and an explicit targeting policy.

### Earth LEO: actually executed atmosphere and averaged evolution

NRLMSIS2.0 was run through **pymsis0.13.0**, with96 positions/times over the first nominal orbit, spherical geocentric latitudes, Earth corotation, and a10 km altitude profile grid. F10.7 daily and81-day values are both **70 / 140 / 220 sfu**; daily ap is **4 / 15 / 100**, with the default daily-ap model. These cases are called quiet/moderate/active; holding an active state for a year is a stress fixture, not a predicted storm duration. The first-orbit mean density profile is held fixed in season, local-time distribution and orbital orientation while a changes. Geodetic/spherical differences, winds and actual weather histories are outside this model. [DE07](https://repository.library.noaa.gov/view/noaa/53074)

The drag power uses v_rel=v−ω_E×r, not inertial speed alone. The scalar ODE uses da/dt=−ρ Cd A/m × a²/µ × mean(|v_rel| v·v_rel). It stops at **120 km mean altitude**, where a circular secular drag model is no longer an adequate reentry solution. Reaching that boundary is not a modelled impact. No terminal reentry lifetime is claimed.

{leo}

The model gives J2 node rates **−5.002°/day** and **+1.012°/day** at the initial400/600 km radii. They are precession, not altitude decay; the98° fixture would need refinement to match the solar apparent motion. For a small5 km allowed drop, initial-rate trigger cadences are approximately **69/14/4.5 days at400 km**, and **2413/255/51 days at600 km**. A held-altitude compensation policy continuously replaces the computed drag power; the annual costs in the table belong to that ideal maintained case, not to uncontrolled falling altitude. Discrete burn targeting, thrust duty and density forecast error require a subsequent design.

### Low lunar orbit: actual rotating-harmonic propagation

The force model includes **GRGM1200A truncated at80×80**, with40×40 and120×120 checks; fully normalized4π coefficients, no Condon–Shortley phase; point-mass central gravity; geometric DE440s Earth/Sun vectors; direct cannonball SRP; and an instantaneous cylindrical lunar shadow. DOP853 uses relative tolerance2×10⁻⁹, absolute tolerance10⁻⁵ on SI state components and maximum step120s. Outputs are sampled at600s, and force norms at1h. Earth/Sun vectors are cubic-interpolated from1h SPICE samples. No tides, Earth shadow/penumbra, planetary radiation, drag, gravity clones, navigation/control or DEM are propagated. Their importance is bounded or left explicit below.

GRGM1200A specifies **DE430 PA**; the available binary orientation is **DE421 PA**. This is an approximation, not a claim that the frames are identical. A0.01° gravity-orientation offset is tested. The model uses the label GM; the archived coefficient header differs by1.5ppb, far smaller than other limits. Exact-frame/tidal/terrain reconstruction is required for operational orbit certification. [DE01](https://pds-geosciences.wustl.edu/grail/grail-l-lgrs-5-rdr-v1/grail_1001/shadr/gggrx_1200a_sha.lbl), [DE03](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf)

{lunar}

For the50 km case the minimum-hp column covers the full48-day run; the other cases cover30 days. Osculating hp is not the spacecraft's current radius, and can fall below the screening boundary before an actual radial crossing. The50 km integration terminates when **|r|=1738+11 km** on a descending passage. The assumed11 km buffer is a screening choice, **not a validated terrain-clearance envelope or local impact**. The48.2-day boundary time was computed at degree80; degree120 was checked to30 days only, so a converged time-to-boundary is unresolved.

The100 km Ω=90° fixture has minimum hp={lun['Moon100_RAAN90_N80']['min_osculating_hp_km']:.1f} km versus77.3 km atΩ=0°. These two phases do not bound every launch date/orientation. The30×200 km fixture yields hp≈18.7–38.6 km in this30-day run, but it is **not an optimized frozen orbit or one-year survival certificate**. It is a useful geometry comparator to the LRO quasi-frozen examples.

![Orbit comparison](../../figures/disturbance_environment/orbit_30day_comparison.png)

### Published maintained/uncontrolled low-lunar cases

LRO provides the stronger long-duration operational comparison: the50±15 km science envelope used paired apsis-rotation burns approximately every28 days, about11m/s per cycle; extended frozen geometries used much less maintenance. The2007 design examples reach a **12 km mountain screening envelope in about41 days at50 km and150 days at100 km**, under their initial geometry and older force model. Those values differ from this study's initial state and boundary. Do not fit a universal km/day decay rate to either set. LRO later allowed apses to drift rather than holding the tight early science envelope. [DE05](https://ntrs.nasa.gov/api/citations/20230010952/downloads/Mesarch_LROLongTermOrbit_Preprint_20230727.pdf), [DE06](https://ntrs.nasa.gov/api/citations/20070035736/downloads/20070035736.pdf)

LRO reports an observed inclination trend around0.4°/year and an estimated14m/s/year to suppress it. Its flight stationkeeping execution averaged2.7cm/s magnitude error (about0.5%), with individual errors within12cm/s in the reported set; these are flight comparator conditions, not assumptions established for a new small spacecraft. Navigation covariance and burn-error margins remain to be selected for SMD. Coverage must tolerate or control plane evolution explicitly. Neither the100 km30-day survival nor the published frozen comparator establishes this mission's polar exposure or one-year clearance.

### Distant observer: a defined and actually propagated halo

The JPL catalogue query returns multiple branches. The script selects a **long-period northern L2 halo** nearest C=3.09, with C={H['jacobi']:.12f}. Normalization is L={H['length_unit_m']/1000:,.6f} km and TU={H['time_unit_s']:.6f}s, mass ratio={H['mass_ratio']:.14f}. Initial state [x,y,z,vx,vy,vz] is approximately **[1.1589028132,0,0.1274150464,0,−0.2099714489,0]**. The exact numbers are retained in JSON. This is a nearby family comparator, not LUMIO's operational state. [DE08](https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html)

| Quantity | Actual CRTBP result |
| --- | --- |
| Period | {H['period_d']:.4f} days |
| Moon-centre range over30 days | {H['range_km'][0]:,.0f}–{H['range_km'][1]:,.0f} km |
| Out-of-plane amplitude | {H['Az_km']:,.0f} km |
| Initial error | +1km x and+0.01m/s vy; remaining offsets zero |
| Uncontrolled deviation from reference at30 days | {H['uncontrolled_day30_deviation_km']:,.0f} km |
| Unstable multiplier / local e-folding time | {H['unstable_multiplier_fd']:.1f} per period / {H['linear_efold_d']:.2f} days |
| Ideal7-day correction result | ≤{H['ideal_targeting_max30_deviation_km']:.2f}km deviation over30 days; total{H['ideal_targeting_dv30_m_s']:.4f}m/s |

The ideal controller targets reference **position14 days downstream**, applying velocity impulses every7 days with exact navigation/execution. It corrects only the initial error; it does not include continuous Sun/SRP/model errors or stochastic navigation errors. Its small correction cost **must not be annualized as stationkeeping demand**. The large uncontrolled departure is a nonlinear trajectory deviation, not a safe lunar-altitude loss rate or a certified escape.

For actual resource screening, the2024 LUMIO design gives annual mean **8.256m/s**,3σ **15.79m/s**, with a2-day planning cut-off; an earlier2018 study gives28.1m/s at3σ under different assumptions. Retaining **16–30m/s/year as a provisional L2 sensitivity** is defensible until an epoch/navigation/control design is selected. Earlier2022 results of1.86/4.34m/s were more optimistic; they should not silently replace the later result. The2026 transfer paper still uses Cj=3.09, while ESA reports Phase C and a possible2028 launch. These are design/schedule evidence, not flight performance. [DE09](https://re.public.polimi.it/bitstream/11311/1266785/1/TOPPF01-24.pdf), [DE10](https://re.public.polimi.it/bitstream/11311/1215727/1/FRANV02-22.pdf), [DE11](https://doi.org/10.3389/fspas.2018.00029), [DE12](https://doi.org/10.1007/s40295-026-00639-2), [DE13](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Shaping_the_Future/A_leap_forward_for_Lumio_Phase_C_officially_launched)

The2.48-day e-folding time is a local linear descriptor. Missing a7-day correction can grow an unstable-mode error by roughly exp(7/2.48)≈17 locally; phase and mode projection matter. Propagate a missed-burn case before setting a real recovery deadline. The ideal example cannot prove recovery after a navigation outage.

![Distant trajectory](../../figures/disturbance_environment/distant_halo_drift.png)

## 3. Force budget and neglected effects

Use vector differential third-body acceleration µ[(R−r)/|R−r|³−R/|R|³]. The following screening bounds are not simultaneous forces. At50,000km, the exact anti-Earth differential acceleration is preferable to the linear tidal approximation.

| Mechanism [m/s²] |400km LEO|100km lunar|50,000km Moon-centre example|Meaning / fidelity|
|---|---|---|---|---|
|Central gravity|8.68|1.45|1.96×10⁻³|Main acceleration, not a disturbance budget or maintenance demand|
|Non-spherical central gravity|J2 polar bound2.50×10⁻²|Actual80-degree norm RMS7.19×10⁻⁴; sampled max1.96×10⁻³|J2 bound≈1.4×10⁻⁹|Earth J2 analytic; lunar lifetime uses harmonics, not J2|
|Earth or Moon third body|Moon linear maximum1.17×10⁻⁶|Earth actual RMS1.79×10⁻⁵; sampled max3.12×10⁻⁵|Exact anti-Earth differential≈5.85×10⁻⁴|At distant orbit use full multi-body equations|
|Solar third body|Linear maximum5.37×10⁻⁷|Actual RMS1.13×10⁻⁷|Linear maximum3.96×10⁻⁶|Geometry-dependent conservative tide|
|Direct SRP|Sunlit6.81×10⁻⁸|Sunlit6.81×10⁻⁸; actual shadowed RMS5.43×10⁻⁸|Sunlit6.81×10⁻⁸|A/m=0.01m²/kg,Cr1.5,1AU; optical/area sensitivity|
|Earth atmospheric drag|Equivalent initial tangential≈4.7×10⁻⁷–7.3×10⁻⁶|Not an Earth atmosphere|Not an Earth atmosphere|Quiet-to-active400km range; see density table|
|Lunar ambient-exosphere screen|Not applicable|≤3.90×10⁻¹⁰ under the specified density screen|No orbit-wide density assumed|Screen below; no claimed exact zero|
|2W anisotropic thermal beam|2.22×10⁻¹⁰|2.22×10⁻¹⁰|2.22×10⁻¹⁰|Spacecraft-generated, geometry/time dependent|

The distant Earth number above is rounded; [the machine-readable bounds](../../data/disturbance_environment/analytical_bounds.json) preserve the exact evaluated value. SRP shadow transitions, orientation and eclipse season must be modelled in a maintained ephemeris trajectory. Incoming reflected/IR forces equal the torque estimates below divided by the assumed2cm arm and mass; they are below the dominant close-lunar gravity perturbations, but can matter for precise orbit determination. Tides and higher harmonics may shift longer-term clearance and are not certified negligible by a30-day run.

For an intentionally conservative **ambient-exosphere screen**, carry the surface upper estimate2×10⁵particles/cm³ to100km unchanged and assign every atom40u. This givesρ=1.33×10⁻¹⁴kg/m³ and only about **2.3m equivalent semimajor-axis loss over30 days**, under the circular, stationary-gas screen. It is not an altitude profile, excludes transient plumes/outgassing, and is not a bound on the operational gas environment of nearby landers. Its small nominal scale explains why mascon-driven periapsis evolution dominates the low-lunar case. [DE14](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html)

Other effects are screened conditionally, rather than declared absent:

- Solar wind fixture n=5cm⁻³,v=400km/s gives dynamic pressure1.34nPa and absorbing torque8×10⁻¹²N·m for0.30m²/2cm. Even a100×pressure sensitivity stays below direct SRP torque; this is not a solar-event percentile.
- A0.30m isolated-sphere capacitance at1000V gives charge3.34×10⁻⁸C. qvB is about1.3×10⁻⁸N in the7700m/s,50µT LEO fixture and2.0×10⁻¹²N at2000m/s,30nT. Net charge is not the same as differential surface charging; electrostatic stress and discharge remain a separate radiation/materials problem.
- A10⁻¹⁰kg/s leak at1000m/s gives10⁻⁷N and10⁻⁸N·m at10cm, comparable to the illustrative secular torque bias. Leak/outgassing specifications must come from selected hardware; this is an acceptance sensitivity, not an environmental measurement.
- A10⁻⁹kg grain at20km/s and20cm arm transfers4×10⁻⁶N·m·s if captured without ejecta amplification, changing a0.5kg·m² axis rate by1.65arcsec/s. This is an individual impulse, not a continuous torque. No encounter rate, damage probability or MEM result is claimed. [DE24](https://software.nasa.gov/software/MFS-32205-2)

![Force screening](../../figures/disturbance_environment/force_screening.png)

## 4. Matched environmental torque budget

Gravity gradient is **τ=3µ/r³ [rhat×(I rhat)]**. The norm envelope is1.5µ/r³(Imax−Imin), reached at45° between the extreme principal axes. At1° principal-axis misalignment multiply by sin2°. For a fixed inertial attitude with the radius rotating in one principal plane, the component is sinusoidal at2n and RMS=peak/√2. For a nadir-following attitude, ideal alignment makes the central-body torque zero; a constant bias angle can instead create a secular wheel momentum demand. These are different attitudes, not conflicting estimates.

{torque}

Aerodynamic torque must also be included in LEO. With the same2cm perpendicular arm, orbit-mean density times mean relative speed squared gives **0.283 / 1.44 / 4.37 µN·m at400km** and **0.0078 / 0.0739 / 0.366 µN·m at600km** for quiet/moderate/active cases. This is an attitude-dependent scalar estimate, not a vector/RMS torque history; density/velocity covariance is omitted. It can dominate the active400km case. The lunar100km ambient-exosphere screen gives only0.234nN·m under its stated assumptions. Drag, magnetic torque and arbitrary-attitude GG therefore change rank with altitude, weather and attitude.

Distant50k is a radius-based **screening point**, not a circular lunar orbit. Its listed central-Moon GG term needs the Earth's tidal tensor as well: at an anti-Earth distance50,000km the Earth GG envelope is about2.2×10⁻¹²N·m, plus a solar term≈1.8×10⁻¹⁴N·m. For the actual42,056–83,121km halo the lunar GG envelope varies strongly with range; a full tensor/attitude history is needed for precise allocation. The illustrative distant momentum plot uses a circular surrogate only to demonstrate cancellation; it does not model halo wheel storage.

Direct SRP uses τ≤P Cr A d, P=1361/c. Its sunlit scalar bound is40.9nN·m at2cm. Actual bias can be smaller, zero or change sign with attitude/illumination. Incoming Earth albedo uses a rounded0.30 and IR237W/m²; the view factor is(R/r)². Lunar reflected-light screening uses0.12 and the same geometric factor; this is a conservative rounded coefficient, not a claim that0.12 is the Bond albedo. The lunar hot-IR envelope uses1198W/m² from an idealized sunlit energy balance, spread over the apparent body to overbound hot emission. A95K nightside blackbody emits4.62W/m², giving about0.083nN·m at100km instead of21.4nN·m. Surface temperature maps, phase, cosine factors and real plate normals are required to predict mean/RMS torque. Reflected/IR extrema and sunlit-SRP extrema are **not summed as simultaneous peaks**. [DE14](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html), [DE23](https://ntrs.nasa.gov/api/citations/19740024206/downloads/19740024206.pdf)

For residual dipole, τ=m×B. The30nT lunar scenario gives0.90nN·m, versus1500nN·m in the50µT LEO fixture: a factor1667 for matched m and perpendicular geometry. The5/100nT sensitivities give0.15/3.0nN·m. A0.2A·m² magnetic torquer yields only6nN·m at30nT, with no authority parallel to B and no guaranteed field rotation. This cannot reliably unload the30nN·m bias example. A thruster-based lunar safe mode/unloading path should therefore be retained. No crustal-field or magnetotail model was run.

![Torque comparison](../../figures/disturbance_environment/torque_comparison.png)

### Internal disturbances and knowledge errors remain separate

Measured wheel tests show why a small environmental torque is insufficient evidence for optical stability. A historical BCT15 test unit had static imbalance0.38g·mm and dynamic imbalance27.59g·mm². At3000rpm these imply fundamental force≈0.0375N and dynamic torque≈0.00272N·m, using F=Usω² and T=Udω². With0.5kg·m² rigid-body inertia the direct50Hz dynamic-angle amplitude is0.011arcsec; structural amplification, bearing noise and harmonics are not included. These data belong to the tested BCT unit, **not** the candidate CubeWheel. Tests span50rpm increments and spectra to500Hz, with speed-dependent modes. [DE18](https://jossonline.com/storage/2021/08/Final-Shields-Characterization-of-CubeSat-Reaction-Wheel-Assemblies.pdf)

Mechanisms, array motion, thermoelastic alignment, thruster misalignment, slosh and flexible modes need a companion disturbance/transfer model once components are known. For example, a1mN thruster misaligned1° gives17.5µN transverse force; at15cm that is2.62µN·m, much larger than a nanoNm science-mode bias. Avoid propulsion/mechanism operation during calibrated flash windows unless the response is demonstrated.

Star-tracker noise/stray light, gyro bias, camera-to-star-tracker alignment, timing and orbit-knowledge errors belong in the measurement/knowledge covariance, not the physical torque sum. ASTERIA's0.5arcsec RMS flight result used a two-stage wheel/piezo system over20minutes; it does not validate this lunar bus or1–5ms interval stability. [DE19](https://ntrs.nasa.gov/citations/20210008536)

## 5. Momentum, propulsion and availability

Use **dH_inertial/dt=τ_ext,inertial** for total angular momentum. In body coordinates include ω×H; wheel demand also contains the commanded body angular momentum and wheel-array transformation. The scalar example holds the body inertially, with a fixed normal axis and diagonal inertia. For τ=T sin2nt+Tb andH(0)=0, H=T(1−cos2nt)/(2n)+Tb t. Thus the periodic amplitude isT/(2n), peak-to-peakT/n; it is not T times mission duration. The100km lunar periodic amplitude is0.200mN·m·s,400km LEO0.255mN·m·s, with zero long-term mean in that particular attitude.

The following **bias sensitivity** assumes0.025N·m·s usable per-axis headroom, two opposed1mN thrusters at0.15m lever arms,80s Isp, ideal balance, and20min loss per unloading including settling/reacquisition. It excludes extra manoeuvre, navigation, calibration and downlink gaps.

{unload}

Each full0.025N·m·s dump takes83.3s of simultaneous thrusting and0.167N·s summed impulse, or0.212g at80s Isp. A perfectly balanced couple has zero net Δv. A **single unbalanced thruster** instead produces5.56mm/s per full dump; a1% pair-thrust mismatch produces about0.028mm/s. Navigation must account for the actual pulse/geometry errors; angular impulse alone does not determine orbit Δv.

A10° rest-to-rest triangular60s slew requires approximately **0.121mN·m** and **3.64mN·m·s** peak body momentum for the0.625kg·m² axis. That is larger than periodic environmental momentum. Reserving it within0.025Nms headroom reduces the30nNm bias cadence from9.65 to8.24days. A1° persistent nadir tracking error could add12.4nNm central-Moon GG bias and further shorten cadence to6.82days before slew reserve. These examples require the appropriate attitude/frame convention; they are not all simultaneous loads.

For a provisional wheel class, the2025 CubeWheel CW0500 sheet specifies **50mN·m·s at6000rpm,10mN·m,322g,0.8W at2000rpm and15W peak at nominal torque**. Four wheels alone weigh1.29kg before mounting/electronics; four at the cited low-speed point consume3.2W. Actual power varies with speed/torque. Array geometry, bias speed, one-wheel failure, maximum speed and all-axis storage must be sized before accepting0.025Nms usable per axis. The smaller CW0162 has16.2mNms per wheel, so its usable reserve is materially tighter. Neither class is selected or qualified for SMD. [DE17](https://www.cubespace.co.za/uploads/14b7921b-25a8-4380-a291-f6062826548f.pdf)

The public CGP3 flyer reports four1mN cold-gas thrusters,40Ns total impulse and60–110s Isp; its live URL currently fails, so this remains a provisional catalogue comparator pending a current ICD. The annual6.31Ns bias-unloading demand would consume16% of40Ns before detumbling, slews, errors and reserves. At5°/s initial tipoff, the0.625kg·m² axis has0.0545Nms, exceeding the illustrative0.025Nms allocated headroom: detumbling cannot be assumed to fit without external control or an array analysis. [DE20](https://gomspace.com/UserFiles/Subsystems/flyer/gomspace_nanoprop_3U_flyer.pdf)

An actual alternative component illustrates the thrust/power trade: ENPULSION NANO R3 lists350µN,2500s Isp and45W nominal, with5300Ns total impulse. For30kg, delivering16–30m/s/year would require about **15.9–29.8days of thrusting per year** at nominal thrust, before EOL derating or geometry loss. A5.5m/s impulsive LRO-style burn would take5.5days: that policy cannot simply be implemented with this electric thruster. The1mN RCS comparator is also too slow for that impulsive policy. Select orbit, burn policy and propulsion together. [DE21](https://www.enpulsion.com/wp-content/uploads/DataSheet_Nano_20260317_V2.pdf)

For mass screening only, with30kg initial mass and **assumed220s chemical Isp**,5/16/30/143m/s require approximately0.069/0.222/0.414/1.92kg propellant by the rocket equation, excluding hardware, residuals and margin. Keep nominal maintenance, injection/navigation recovery, unloading, contingency and disposal separate. Published LUMIO disposal examples≈1–3m/s are trajectory-dependent comparators; low-orbit disposal must be separately targeted. No complete mission Δv allocation is approved here.

## 6. Pointing and the event-camera measurement

For a0.5kg·m² rigid axis and constant30nNm torque, open-loop drift is0.5τt²/I: **61.9arcsec after100s**. A demonstrative scalar PD loop with natural frequency0.02Hz and damping0.7 leaves **0.784arcsec static error** without integral action. Nominal tracking is assumed feedforward-cancelled, actuator saturation absent, and sensor/structural disturbances zero. This transfer example demonstrates the role of control; it does **not** predict integrated line-of-sight jitter. At1ms, the same torque's direct open-loop motion is only≈6×10⁻⁹arcsec; high-frequency wheel/structure response and sensor/clock effects can still dominate the measurement.

The prior4.86µm/0.5m focal-length fixture has **2.005arcsec/pixel**. A0.2arcsec displacement is0.100pixel;1arcsec knowledge error projects to242m at50000km nadir range and0.485m at100km. Off-nadir/limb/polar terrain geometry amplifies or rotates these errors. Range-dependent navigation uncertainty, frame alignment and boresight knowledge remain separate from stability.

At100km, nominal body nadir tracking is≈0.0509°/s; tracking a fixed nearby ground point can approach0.94°/s near overhead. A residual0.1°/s scene rate moves about **0.90pixel in5ms** or0.18pixel in1ms. For event sensing, d(logI)/dt=∇logI·v_image: terrain edges, jitter and slews can create traffic even without a flash. Event count/rate cannot be inferred from angular motion alone without the actual scene contrast, PSF, thresholds and losses. Use image-motion injections in the calibrated sensor model, not arbitrary v2e intensities, to test D02/D03/D07.

![Momentum and representative loop](../../figures/disturbance_environment/momentum_pointing.png)

## 7. Numerical checks, limits and reproducibility

| Check | Actual result | Interpretation |
|---|---|---|
|J2 normalization/sign limiting case|Relative acceleration error{R['checks']['J2_relative_acceleration_error']:.2g}|Analytical independent J2 matches harmonic evaluator|
|Harmonic potential finite-difference gradient|Relative error{R['checks']['harmonic_potential_gradient_relative_error']:.2g}|Checks force derivative implementation at a nonsingular test position|
|Two-body30-day energy range|Relative{R['checks']['two_body_30d_relative_energy_range']:.2g}|Numerical control; conservation is not demanded in the multi-body model|
|Halo period closure|{H['period_closure_position_m']:.2g}m position, {H['period_closure_velocity_m_s']:.2g}m/s velocity|Ideal CRTBP state/integrator check|
|Halo Jacobi variation over30days|{H['jacobi_range_30d']:.2g}|CRTBP numerical invariant|
|Halo unstable multiplier cross-check|{H['unstable_multiplier_fd']:.3f}; (λ+1/λ)/2≈170.405|Consistent with catalogue stability index|

{convergence}

At100km, moving80→120 changes day30hp by22m, while40→80 changes it by1.01km; this supports an80-degree **concept comparison**, not a flight lifetime certificate. The tighter step/tolerance changes hp by2.5m. The0.01° orientation offset changes hp by3.2m. At50km,80→120 changes day30hp by0.283km, so longer boundary-time convergence remains open. High-degree truncation, tides, uncertain state and frame errors dominate an exact impact-time claim. No covariance-clone ensemble or Monte Carlo low-orbit lifetime was run.

Orbit force statistics are sampled norms, not exact continuous maxima. Torque tables are analytical envelopes/scenarios, not a simultaneous vector Monte Carlo. The PD and momentum examples are deliberately restricted scalar dynamics. No sensor qualification, hardware test, calibrated event-camera response, precision navigation solution, MEM environment run or complete controller/structural simulation is implied.

Current-host commands, pinned libraries, source hashes, builders and data descriptions are in [the analysis README](../../analysis/disturbance_environment_research/README.md) and [data provenance](../../data/disturbance_environment/README.md). The workbook contains live analytical formulas; propagated histories remain labelled script outputs and must be regenerated for changed dynamical inputs. Source access failures are retained in [the evidence register](../../analysis/disturbance_environment_research/evidence.json) and download manifest.

## 8. Provisional concept decisions and minimum next work

{decisiontable}

For SRR, couple the candidate orbit to **usable surface-area-time and the selected characterization sample**, rather than optimizing propellant alone. The minimum next analyses are: (1) epoch/phase and whole-surface exposure trade; (2) one favourable low-lunar or distant maintained trajectory with navigation/error envelope and disposal; (3) CAD inertia/pressure-centre model and three-axis wheel/thruster geometry; (4) wheel spectra plus a simple structural/control transfer and knowledge covariance; (5) science-mode timeline including burns, unload/settle, thermal/power recovery, downlink and calibration. Limit the final report to the essential comparison and selected budgets; retain this supporting detail outside its50-page working budget.

## Evidence register

All sources accessed29October2026 unless a publication date is stated. “Published simulation/design” and “flight evidence” are deliberately distinct. Complete claims, locations and access limits are machine-readable in the analysis directory.

'''
for e in E:note+=f"- **{e['id']}** — [{e['title']}]({e['url']}). {e['date']}; {e['kind']}; {e['location']}. {e['limits']}\n"
O.mkdir(parents=True,exist_ok=True)
units=r'(?:km|kg|mN|nN|µN|W|m/s|ms\b|s\b|arcsec|cm|rpm|Hz|µT|nT|days?\b|m²|m³|m·|g\b)'
def spaced(s):
 s=re.sub(r'(?<=[A-Za-z])(?=\d+(?:\.\d+)?'+units+')',' ',s)
 return re.sub(r'(?<=\d)(?='+units+')',' ',s).replace('DE 440 s','DE440s')
# Preserve link targets verbatim while improving unit spacing in prose.
note=''.join(part if i%2 else spaced(part) for i,part in enumerate(re.split(r'(https?://[^\s)]+)',note)))
(O/'disturbance_environment_research.md').write_text(note)
print('Built findings',len(note),'characters')
