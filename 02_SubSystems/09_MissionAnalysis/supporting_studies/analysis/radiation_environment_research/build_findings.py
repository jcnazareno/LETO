"""Generate the findings and flat source records without changing historical outputs."""
import csv
import json
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=H.parents[1]
OUT=ROOT/'outputs/radiation_environment_research_2026-10-29'
R=json.loads((H/'model_results.json').read_text())
S=json.loads((H/'research_data.json').read_text())
OUT.mkdir(parents=True,exist_ok=True)
def d(case,t): return next(r['dose_krad_Si_year'] for r in R['dose_rows'] if r['case']==case and r['shielding_mm']==t)
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x).replace('|','/') for x in r)+' |' for r in rows])

text='''# Radiation environment for the lunar event-camera concept

Research completed 29 October 2026. All orbit, duration, shielding and component examples below are study fixtures. No mission requirement or architecture has been selected.

## Conclusions for the concept

**Radiation does not presently rule out the event-camera mission, but its science performance needs a sensor-specific degradation and particle-confusion allowance.** Existing event-camera flight and beam evidence supports further concept design. It does not establish calibrated lunar capability for IMX636. A recoverable electronics chain, protected power, adequate shielding paths and retained diagnostic data are proportionate concept measures. Adding a second spacecraft or optical channel solely because radiation exists is not justified by these results.

The strongest direct numerical comparison comes from one NASA publication using the same silicon target, solid aluminium sphere geometry, solar maximum and stated 95% confidence. At 2.54 mm Al, its digitized annual doses are approximately **4.3 krad(Si) for interplanetary space, 2.6 krad(Si) for 550 km/6° LEO, and 5.5 krad(Si) for 800 km/98° LEO**. The distant lunar observer can use the interplanetary case as a provisional exposure proxy. The corresponding ratios are approximately **1.7 and 0.78**. These are specific matched published cases, not a universal lunar/LEO multiplier. Source model versions and full inputs are unavailable. [RAD01](https://ntrs.nasa.gov/api/citations/20250006822/downloads/TM-20250006822.pdf), printed p11, Fig10.

For an illustrative three-year mission, the distant proxy at 2.54 mm gives 12.8 krad operational dose by arithmetic scaling. Adding an **assumed 1 krad transfer allowance** and applying an **assumed factor-two design margin** gives **27.5 krad(Si)**. A **30 krad procurement screening class** is therefore a useful starting trade for electronics. It uses the central curve reading: preserving the same margin at the +15% reading requires **31.3 krad**, so compare available **50 krad parts** before selection. It is neither a qualified mission dose nor an IMX636 rating. At 1 mm Al the central-reading arithmetic approaches 65 krad including margin; life and enclosure assumptions matter. A duration-specific SEP calculation and actual transfer can change this conclusion.

## Cases, conventions and comparison limits

The original 400 km/51.6° and 600 km/98° LEO fixtures are retained as context. Matched quantitative dose evidence was obtained instead for 550 km/6° and 800 km/98°. Altitude and inclination cannot be interpolated independently through the radiation belts. **No dose or lunar/LEO ratio is assigned to the uncomputed original fixtures.** The exact LEO numbers are not estimates for ISS or for all Sun-synchronous missions.

'''+table(['ID','Case','Definition / evidence status'],[[c[0],c[1],c[4]+'; '+c[5]] for c in S['cases']])+'''

L2 is defined at **50,000 km lunar centre distance**, not altitude. Its nadir surface range is 48,262.6 km. If the mission instead fixes 50,000 km target range, centre distance is 51,737.4 km for a nadir target; neither definition specifies a halo orbit, its Earth-magnetotail residence or observing geometry. The primary isotropic Moon-blocked fraction at either distance is very small. Near the limb, target range differs from altitude.

Comparisons use absorbed dose in silicon: 1 rad(Si) = 0.01 Gy(Si), 1 krad(Si) = 10 Gy(Si); 1 Gy = 1 J/kg. Human effective dose in Sv weights tissue and radiation quality and cannot qualify silicon electronics. Earth-surface human background dose is therefore not used as an electronics comparator. Flux is per time; fluence is its time integral. An integral above an energy or LET threshold is not a differential spectrum. Angular intensity in particles/(cm² s sr), scalar omnidirectional flux in particles/(cm² s), and crossings of a planar face differ by angular integration.

## Cumulative dose and shielding

'''+table(['Al (mm)','Areal density (g/cm²)','LEO 550/6','LEO 800/98','Interplanetary / distant proxy','Lunar surface'],
[[f'{t:g}',f'{t*.27:.3f}',*[f'{d(c,t):.2g}' for c in ['LEO550_6','LEO800_98','Interplanetary','Lunar_surface']]] for t in [1,2,2.54,3,5]])+'''

Dose columns are **krad(Si)/year**, digitized from RAD01 Fig10. Each has a **±15% reading allowance**, chosen conservatively for raster extraction, separate from the source's stated 95% environment confidence. This allowance is not a probability distribution or a complete model error bound. At 2.54 mm, reading-only ratio intervals are about 1.22–2.24 (distant/550 km) and 0.57–1.05 (distant/800 km). Common model errors and covariance are unknown. The second comparison does not robustly establish which is larger.

![Matched dose-depth curves](../../figures/radiation_environment/matched_dose_depth.png)

The published environment/transport chain is SPENVIS SEP fluences, IRENE Earth belts and FASTRAD spherical dose. Its exact SEP model/version, dates, spectra and percentile construction are not given. Current public documentation identifies SPENVIS 4.6.14 and IRENE V1.58.001; these are **documentation checks, not the versions inferred for NASA's run**. No SPENVIS, IRENE, OMERE, CREME, FASTRAD or Geant4 calculation was executed here. [RAD10](https://www.spenvis.oma.be/), [RAD11](https://www.vdl.afrl.af.mil/programs/ae9ap9/index.php).

**Quiet GCR measurement is a different design case.** LRO's microdosimeter accumulated only 12.2 rad(Si) over its first 333 days in 2009–2010, approximately 13.4 rad/year if annualized. Space-facing minimum shielding was 2.28 g/cm² Al and lunar-facing minimum 0.89 g/cm², with nonuniform instrument geometry. The era lacked intense solar particle events. This value cannot replace a solar-event allowance or be divided by the RAD01 values as a matched ratio. Another CRaTER analysis reports 372 µGy(Si)/day, equivalent to 13.6 rad/year under its specific response assumptions. [RAD02](https://doi.org/10.1029/2010SW000641), abstract and paras16,22; [RAD03](https://doi.org/10.1002/2013SW000995), abstract.

GCR background is generally greatest near solar minimum. SEP occurrence and high-fluence risk increase with active solar conditions but individual events remain variable. A quiet-era observation and a conservative solar-maximum design case need not agree. The selected delivery date is not known; the mission must assess both states instead of assigning present solar conditions to a future launch.

One-to-three-year linear scaling is shown only as a sensitivity. GCR exposure can be integrated over a varying solar cycle; stochastic SEP confidence must be recomputed for mission duration. Multiplying a one-year 95% curve by three does **not** produce a three-year 95% quantile. Annealing, bias, temperature and dose-rate effects also prevent simple dose-to-performance scaling.

### Geometry, secondaries and transfer

For an opaque spherical body, an isotropic scalar primary field has visible fraction

`f = [1 + sqrt(1 - (R / (R + h))²)] / 2`.

This gives 0.500 at the lunar surface, **0.663 at 100 km** and **0.99970 at 50,000 km centre distance**. It illustrates why a 100 km orbiter does not receive half the free-space primary flux. Multiplying 4.25 krad/year by 0.663 gives 2.82 krad/year as a **primary-only isotropic geometric sensitivity**, not a lunar dose prediction. SEP directionality, optical orientation, body attenuation, lunar albedo/neutrons and spacecraft secondaries require transport. The same scalar calculation for Earth at 400 km gives about0.67, but it does not include geomagnetic exclusion or trapped particles and is not a LEO radiation model. LRO measured about30% lower quiet dose at50km than interplanetary, supporting the scale of the geometric effect, without validating the100km full environment. [RAD02](https://doi.org/10.1029/2010SW000641).

Earth operations include trapped protons/electrons, South Atlantic Anomaly passages and high-latitude access. The Moon has no analogous persistent global trapped belts. Lunar observers still encounter solar particles, GCR, secondary radiation and changing solar-wind/magnetotail plasma. MEO/GEO can be harsher than some LEO cases, so “Earth environment” alone is not a useful quantitative specification.

Keep a separate transfer ledger: `D_transfer = integral dose_rate_along_trajectory dt`. A6hour crossing at an **assumed**1krad/day is0.25krad;30days at that same hypothetical rate is30krad. These are time-scaling demonstrations, not belt predictions. Slow electric raising or extended parking can dominate the budget. Powering equipment down can reduce some functional interruptions and sometimes change susceptibility; it does not remove accumulated ionization/displacement damage or guarantee freedom from destructive SEE. The1krad allowance above is explicitly unvalidated and must be replaced if trajectory evidence exceeds it.

## Displacement damage, LET and single-event effects

Keep four outputs separate:

| Effect | Correct quantitative description | Result and implication |
| --- | --- | --- |
| TID | rad(Si) or krad(Si), shielded time integral | Matched published values above support enclosure/lifetime and component-class trades. |
| Displacement damage | `DDD = sum integral fluence(E) × NIEL(E) dE`, usually MeV/g(Si); or DDEF(particle,reference energy,material) | Compatible transmitted spectra and IMX636 response coefficients were not obtained. Mission DD and array degradation remain numerically TBR. |
| Direct-ionizing heavy-ion SEE | Device cross-section versus LET, geometry and bias, integrated with compatible differential LET spectrum | Environment scale available; no selected-device rate or destructive-event probability claimed. |
| Proton/neutron SEE | Cross-section versus energy and angular response, integrated with spectrum | Neutron camera morphology evidence cannot be used as lunar proton cross-section. |

For equivalent fluence, divide DDD by the NIEL coefficient for the stated reference particle/energy/material. TID cannot be converted to DD. The published DAVIS346 **64MeV proton exposure of1.498×10¹¹p/cm² at20krad(Si)** is a beam-test fluence comparator, not1MeV-neutron-equivalent fluence, a lunar lifetime or a failure threshold for IMX636. Its simultaneous ionizing and displacement effects were not separated. [RAD05](https://doi.org/10.1117/12.2634166), §3.4 Table3; [RAD12](https://www.spenvis.oma.be/ecss/e_st_10_12c/ecss_08_02_00.htm), §8.2.

NASA Fig8 provides integral flux above LET after2.54mm Al in silicon. At LET>10MeV·cm²/mg, order-of-magnitude readings are about **10⁻⁶cm⁻²s⁻¹ at GCR solar maximum,10⁻⁵ at GCR solar minimum**, and approximately **0.003,0.01,0.04** for the October1989 reference SEP's week, peak-day and peak-five-minute averages. A factor-two reading range is appropriate; the source does not specify enough angular detail for device-rate integration. The large burst/background difference supports a solar-event operating mode. This threshold excludes most low-LET particles and cannot estimate all detector hits. A historical event is not a universal “99% worst case” for every duration. [RAD01](https://ntrs.nasa.gov/api/citations/20250006822/downloads/TM-20250006822.pdf), printedp9 Fig8.

![LET environment scale](../../figures/radiation_environment/let_environment_scale.png)

Rate methodology: `lambda = integral sigma(E,LET,angle,bias,T) × differential_flux dE dLET dOmega`, with the cross-section's directional convention respected. For stationary Poisson events, `P(>=1)=1-exp(-lambda*T)`; for varying solar flux use the time-integrated rate. Memory rates also need the number of susceptible bits and multi-cell upset behavior. A tested LET ceiling or zero observed events gives an experiment-specific limit, not immunity at all fluxes. No compatible complete cross-section set for the selected sensor/readout/processor/memory/power chain was found, so a qualified SEE rate is not invented. [RAD13](https://creme.isde.vanderbilt.edu/CREME-MC/help/how-to-run-creme96).

## Event-camera consequences and bounded particle screening

**IMX636 is a conditional sensor example.** Its public manufacturer brief gives1280×720 pixels at4.86µm, an active-array footprint of **0.217678cm²**. That footprint is not a radiation-sensitive area measurement: charge collection can include surrounding circuitry and package secondaries. No applicable public IMX636 TID/DD/SEL/particle-to-event qualification was found. The evaluation kit, bare sensor, FPGA/readout and power circuitry require separate evidence. [RAD07](https://www.prophesee.ai/wp-content/uploads/2024/05/IMX636-Product-Brief-2024-v3.0.pdf).

Two useful evidence levels are available. DAVIS240C sensors on ISS showed limited deterioration across intermittent2022–2024 data, behind6.35mmAl with open lens apertures. This supports event-sensor technology maturity, without transferring its dose or faint-light performance. Separate tests on180nmPPS3MVCD andDAVIS346 found increasing background noise, functional issues above roughly30krad, and a recoverable proton-induced camera lock-up. A20krad proton-exposed DAVIS346 showed about70% higher dark current and23% higher dark event noise with filtering off. These are **comparator observations**, not degradation coefficients for IMX636; device count, dose rate, annealing and support-circuit ambiguity limit transfer. [RAD04](https://doi.org/10.3390/s25216599), §4.1; [RAD05](https://doi.org/10.1117/12.2634166), §§3.3–4.

Neutron tests on a different640×480 sensor produced compact clusters and tracks with roughly0.6–0.8msON bursts and8–10msOFF relaxation. Beam timing and sensor response both matter. Such timescales overlap the proposed flash observable: ON-then-OFF behavior alone cannot confirm an optical impact. Correlation filters or aggressive rate caps can also erase real faint flashes or bias early-to-total energy. Preserve morphology, time, bias, temperature, masks, buffer-loss counters and raw snippets around candidates and rejected samples. [RAD06](https://doi.org/10.1109/ACCESS.2021.3085136), §§III–IV,Figs11–13.

### Incident particles are not confirmed false flashes

For an isotropic directional intensity `j`, incidence on one unobstructed planar face is `pi × j × A`. Using NOAA's>=10MeV proton thresholds as **incident-field sensitivity cases**, and assuming isotropy at the Moon, gives:

'''+table(['Incident j (pfu)','Incident front-face particles/s','Max incident-to-confirmed fraction for assumed0.01false/h'],
[[f"{r['input_flux']:g}",f"{r['incident_rate_s']:.3g}",f"{r['required_incident_to_confirmed_fraction']:.2g}"] for r in R['sep_screening']])+'''

1pfu=1proton/(cm²s sr). These counts are **before optics, shielding, transmission, charge response and filtering**. They are not upper bounds on all physical hits or candidates: back/side incidence, secondary production and event multiplicity are omitted. The displayed rejection fractions are conditional on this incident population and a freely chosen false-alarm allocation; they establish no accepted D07 value. NOAA thresholds do not supply a spectrum or duration, and Earth-measured flux need not equal lunar flux. [RAD14](https://www.spaceweather.gov/noaa-scales-explanation).

Use `confirmed_false_rate = incident_rate × transmission × response_probability × false_confirmation_probability`, with multiplicity and other backgrounds handled explicitly. None of the unknown factors is silently set to1 in a performance claim. For a separate hypothetical4π scalar fluxF=1–10cm⁻²s⁻¹, a two-sided ideal plane gives `R=FA/2`=0.109–1.09crossings/s; this is an angular-convention sensitivity, **not a calibrated GCR forecast**. AtF=4, masking9pixels for20ms per crossing would remove only about8.5×10⁻⁸of array-area-time under uniform independent arrivals. Masking a whole frame would be much more costly; long hot pixels, bursts, real flash overlap and readout saturation can dominate instead.

## Electronics, protection and operations

Keep an independently recoverable supervisor, current-limited power domains, watchdogs and autonomous restart. A latch-up can be destructive unless interrupted within the device's safe energy/time limit. Recovery logic must survive an unavailable science processor. Preserve clock state or re-establish correlation and mark data after a reset. Distinguish SEU/SET data corruption, SEFI interruption, SEL and destructive power-device effects.

RTG4 provides a concrete radiation-tolerant FPGA class with>100krad(Si), hardened configuration and SECDED internal memory. This demonstrates an available engineering route; its GEO-rate example is not a lunar rate. ExternalDDR/NAND/eMMC controllers, boot memory, clock/interface chips and regulators need their own evidence. Compare a suitably assured commercial processor plus protected supervisor with a rad-tolerant processor/interface rather than automatically choosing the largest FPGA. UseECC/scrubbing, CRC, interleaving where useful, recoverable boot images and reset counters. Redundancy must address shared power, software and clock failures. [RAD09](https://ww1.microchip.com/downloads/en/DeviceDoc/00003023C.pdf),p8; [RAD16](https://www.nasa.gov/smallsat-institute/sst-soa/small-spacecraft-avionics/),§8.2.1.

TI'sTPS7H2201-SP is a concrete1.5–7V/6A protected-switch example, with100krad and tested DSEE LET75MeV·cm²/mg ratings; theSEP grade is50krad/43MeV·cm²/mg. Engineering-model parts carry different assurances. The specified maximum35mΩon-resistance at25°C and5V forCFP/KGD gives **0.14W at2A** byI²R; actual hot/end-of-life resistance and load current must enter the power/thermal budget. HTSSOP has a different resistance limit. The switch rating does not protect every downstream device automatically, and it does not cover higher-voltage buses. [RAD08](https://www.ti.com/lit/ds/symlink/tps7h2201-sp.pdf),§§1,4.

At2.70g/cm³,1,2,3,5mmAl correspond to0.27,0.54,0.81,1.35g/cm² and2.7,5.4,8.1,13.5kg/m². A closed10cm-internal-side cube has exact wall masses0.165,0.337,0.516,0.894kg respectively. These are **total walls**, before credit for existing structure, joints or penetrations. A1m²whole-bus skin at3mm costs8.1kg; local boxes are attractive if their smaller protected volume fits the electronics. Do not compare different protected volumes as equal whole-spacecraft shielding. Aluminium-equivalent thickness is spectrum dependent for composites/high-Z materials; a CAD sector map must retain the aperture and cable paths.

![Shield mass trade](../../figures/radiation_environment/shielding_mass.png)

More metal does not establish GCR/SEE immunity: energetic particles penetrate, fragments and neutrons can be generated, and electron shielding creates bremsstrahlung. The optical aperture prevents uniform enclosure protection. Avoid choosing a thick blanket shield before comparing local protection, exposure, tested parts and mission lifetime.

Use a solar-event degraded/safe mode based on actual instrument noise, current, loss counters and space-weather information. External alerts are useful input, not a required real-time dependency or guaranteed warning. Science pause/power-cycle thresholds and recovery hysteresis remain TBR. Record exclusions and resume calibration checks. Power-off does not undoTID/DD. A new radiation detector is optional; use existing health telemetry before adding a dedicated payload/support sensor.

### Charging and solar arrays

Surface/internal charging is a plasma/current-balance and dielectric problem, distinct from cumulative Si dose. NASA summarizes Lunar Prospector **spacecraft** potentials of-100to-300V during solar-particle conditions and-40to-80V in geotail conditions. The separately quoted-4.5kVconcerns the **lunar surface**, not this observer's bus. These are measured-case summaries, not design limits or voltages across a chosen connector. Use electrical bonding, conductive/controlled surfaces, dielectric placement and appropriate discharge protection; assess hot-plasma/magnetotail residence and transfer separately. LEO high-voltage-array guidance has latitude/voltage scope limits and does not establish polar or lunar suitability. [RAD15](https://ntrs.nasa.gov/api/citations/20200001582/downloads/20200001582.pdf),slides36–37; [RAD17](https://standards.nasa.gov/standard/NASA/NASA-STD-4005).

Solar-array end-of-life power requires the selected cell's radiation degradation curve, coverglass, temperature and transmitted electron/proton equivalent fluence. None was selected or simulated here. Retain the degradation factor explicitly in array sizing; do not infer a percentage power loss from spacecraftTID. A10%/20%power-degradation sensitivity may be used as an assumption if labeled; it is not an environment prediction.

## Science availability and driver implications

An assumed5radiation-exclusion days/year yields98.63%radiation-only availability. Combining that with an assumed0.1reset/day and60smean recovery yields98.62% in the simple renewal approximation `A=(1-days/365.25)/(1+lambda_day*t_recovery/86400)`. At30excluded days the storm-only factor is91.79%. These are planning sensitivities, not observed solar-event downtime. Apply the factor to usable region-by-region exposure and characterized sample yield, not the geometric coverage map. A1.4%uniform sample reduction increases simplePoissonflux uncertainty by onlyabout0.7%, but exclusions coinciding with a meteoroid stream or infrequently visible polar region can be much more important.

![Availability sensitivity](../../figures/radiation_environment/availability_sensitivity.png)

| Driver | Required radiation term in the coupled design |
| --- | --- |
| D01 | End-of-life background/dark activity,QE and masked-pixel sensitivity; separate detection and characterization thresholds. |
| D02 | Threshold/latency drift, particle tails, buffer loss and clock recovery. Fine timestamps remain insufficient evidence. |
| D03 | Bias/calibration drift, lost events and morphology filtering effects on peak and early-to-total energy. |
| D05 | Radiation exclusions integrated into surface-area-time by both hemispheres and poles; whole-surface requirement remains fixed. |
| D07 | Raw crossing,candidate and confirmed-false rates separately; true-flash rejection and event loss counted. |
| D08 | Temperature, illumination,bias and radiation state jointly define validity of recording-quality claims. |
| D09 | Separate permanent-failure probability, reset recovery, storm downtime and end-of-life measurement quality. |

## Proposed decisions and what would change them

'''+table(['ID','Proposed action','Quantitative / evidence basis','Status; consequence; revisit trigger'],
[[r[0],r[1],r[2],r[3]+'; '+r[4]+'; '+r[5]] for r in S['decisions']])+'''

The supported necessities are a radiation-aware parts chain, fault protection/recovery, calibrated end-of-life sensitivity bounds and a candidate-rejection/availability model. **2–3mmshielding,30kradclass,three-yearlife,1kradtransfer and5lost days are provisional trade assumptions.** A second optical channel, redundant spacecraft, active cooling or dedicated dosimeter needs a demonstrated science/reliability benefit before inclusion.

## Report-ready paragraph

The lunar observer loses geomagnetic protection but avoids persistent terrestrial radiation belts during its operational phase. In matched published solar-maximum cases behind2.54mmAl, annual Si doses are about4.3krad for an unocculted distant-lunar proxy,2.6krad for550km/6°LEO and5.5krad for800km/98°LEO. Radiation severity is therefore trajectory- and effect-dependent. The concept should provide local shielding, assured critical electronics, memory protection and autonomous recovery, and model radiation-induced detector activity separately from confirmed impacts. Existing event-camera flight and irradiation evidence supports conditional feasibility; selected-sensor degradation and false-confirmation response remain bounded uncertainties. Science exposure must include radiation exclusions without relaxing coverage of either hemisphere or the poles.

## Proportionate next work and validation status

For SRR, select the candidate lifetime and architecture together with useful sample yield; keep the quantitative dose-class and shield-mass trade and clearly state sensor uncertainty. Use vendor/existing test reports and first-principles response bounds to assess whether the one primary observable remains useful. A new hardware irradiation campaign is **not** a completion prerequisite for this educational concept. For an eventual flight programme, selected-lot/assembly radiation assurance and appropriate qualification are later obligations.

Before requirement baseline, replace the transfer allowance and interplanetary proxy with the selected mission timeline and shielding map, evaluate duration-specific SEP confidence, obtain or boundTID/DD/SEEresponses for all critical components, and propagate end-of-life noise and filtering into the scientific observable. Do not broaden the science to compensate for an unresolved sensor response.

'''+table(['Open item','Missing evidence','Next step'],[[r[0]+' '+r[1],r[2],r[3]] for r in S['open_items']])+'''

Executed here: raster digitization of publishedNASAcurves, unit/geometry/mass/rate-screening/availability arithmetic, independent numerical checks, workbook formulas and input-change checks, scientific-figure generation, report generation and rendering. Validation details and reproduction commands are in the[analysisREADME](../../analysis/radiation_environment_research/README.md) and[validation record](../../analysis/radiation_environment_research/validation_results.json). No environment/transport service, selected-sensor simulation, irradiation, hardware experiment or full-spacecraft reliability demonstration was performed.

## Evidence register

The workbook and[reviewed source records](../../analysis/radiation_environment_research/research_data.json) retain source kind, location,conditions,limits and access status. Original/downloaded sources remain in thecache; supplied literature and historical workbooks were preserved. Source dates are distinguished from the29October2026review date. Detailed numerical provenance is in[dataREADME](../../data/radiation_environment/README.md).

'''+ '\n\n'.join(f"**[{e['id']}] {e['title']}** ({e['date']}). {e['location']}. [{e['kind']}]({e['url']}). Access: {e['access']}." for e in S['evidence'])+'\n'

# Repair compact digit/word boundaries in authored shorthand without changing identifiers.
import re
def normalize_prose(value):
    # Keep links, identifiers and code literal while spacing authored prose and units.
    chunks=re.split(r'(\[[^\]]*\]\([^)]+\)|`[^`]+`|https?://\S+|10\.\d{4,9}/\S+|DAVIS\d+C?|PPS3MVCD|Geant4|IMX\d+|RTG4|\b\d+(?:\.\d+)?[eE][+-]?\d+\b)',value)
    for i in range(0,len(chunks),2):
        x=chunks[i]
        x=re.sub(r'(?<=[a-z])(?=\d)',' ',x)
        x=re.sub(r'(?<=\d)(?=[A-Za-zµ])',' ',x)
        x=re.sub(r'(\d (?:krad|MeV|mm|km|nm|µm|ms|us|pfu))(?=[A-Za-z])',r'\1 ',x)
        x=re.sub(r'(?<=[²³])(?=[A-Za-z])',' ',x)
        x=re.sub(r'(?<=[a-z])(?=(?:TBR|ON\b|OFF\b|Al\b|Si\b))',' ',x)
        x=re.sub(r',(?=[^\s\d])',', ',x)
        x=re.sub(r'\bA(?=\d)','A ',x)
        x=re.sub(r';(?=\S)','; ',x)
        x=re.sub(r'(?<=[a-z])(?=(?:DAVIS|RAD\d|NASA|TID\b|DD\b|DDEF\b|NIEL\b|TBR\b|LEO\b|SPE\b|SEE\b))',' ',x)
        for a,b in {'power-degradation':'power degradation','TID/DD/SEEresponses':'TID/DD/SEE responses','solarmax':'solar max','solarmin':'solar min','printedp':'printed p','4πscalar':'4π scalar','Poissonflux':'Poisson flux','Poissonerror':'Poisson error','1MeV-neutron':'1 MeV-neutron','raw-to-confirmed':'raw to confirmed','mmshielding':'mm shielding','kradclass':'krad class','daysof':'days of','nmPPS':'nm PPS'}.items():x=x.replace(a,b)
        chunks[i]=x
    result=''.join(chunks)
    for a,b in {'andDAVIS':'and DAVIS','forL1':'for L1','yearsin':'years in','rad iation':'radiation','nmPPS':'nm PPS','smean':'s mean','simplePoisson':'simple Poisson','onlyabout':'only about','%radiation':'% radiation','%uniform':'% uniform','NASAcurves':'NASA curves','three-yearlife':'three-year life','the[analysisREADME]':'the [analysis README]','and[validation':'and [validation'}.items(): result=result.replace(a,b)
    return result
text=normalize_prose(text)
(OUT/'radiation_environment_research.md').write_text(text,encoding='utf-8')
# Machine-readable source table: original source statements stay separate from calculated CSVs.
with (ROOT/'data/radiation_environment/source_register.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['id','title','date','kind','location','finding','conditions','limits','url','access'])
    w.writeheader();w.writerows({k:e[k] for k in w.fieldnames} for e in S['evidence'])
print('Wrote findings and source register')
