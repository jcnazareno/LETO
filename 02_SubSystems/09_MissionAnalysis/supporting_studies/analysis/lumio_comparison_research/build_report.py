"""Build the concise supporting PDF from reviewed research data and calculations (prose restyled 2 November 2026; content unchanged)."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
from readable import text,markup
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
OUT=ROOT/'outputs/lumio_comparison_research_2026-10-29'
D=json.loads((ROOT/'data/lumio_comparison/research_data.json').read_text());R=json.loads((ROOT/'data/lumio_comparison/calculation_results.json').read_text())
font=Path('/usr/share/fonts/TTF/DejaVuSans.ttf')
if not font.exists():font=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('Report',str(font)));pdfmetrics.registerFont(TTFont('ReportBold',str(font).replace('DejaVuSans.ttf','DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('Report',normal='Report',bold='ReportBold',italic='Report',boldItalic='ReportBold')
S=getSampleStyleSheet()
for n,size,lead,color in [('Body',9.3,13.3,'#26394E'),('SmallX',7.8,10.8,'#52677C'),('TitleX',21,26,'#294C72'),('HeadX',13.4,18,'#294C72'),('CellX',8.1,11,'#26394E'),('HeaderX',8.2,11,'#FFFFFF')]:
 S.add(ParagraphStyle(n,fontName='ReportBold' if n in ['TitleX','HeadX','HeaderX'] else 'Report',fontSize=size,leading=lead,textColor=colors.HexColor(color),spaceAfter=7 if n not in ['CellX','HeaderX'] else 0))
W=A4[0]-88;story=[]
def p(t,style='Body'):story.append(Paragraph(markup(t),S[style]))
def head(t):p(t,'HeadX')
def table(headers,rows,widths):
 data=[[Paragraph(escape(text(str(c))),S['HeaderX']) for c in headers]]+[[Paragraph(escape(text(str(c))),S['CellX']) for c in row] for row in rows]
 t=Table(data,colWidths=[W*w/sum(widths) for w in widths],repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#294C72')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#EFF3F7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([t,Spacer(1,10)])
def fig(name,w=W):
 path=ROOT/'figures/lumio_comparison'/f'{name}.png';im=PILImage.open(path)
 story.append(Image(str(path),width=w,height=w*im.height/im.width));story.append(Spacer(1,9))
def page(title):story.append(PageBreak());head(title)

p('LUMIO and the SMD concept','TitleX')
p('Mission comparison, design evidence and science implications<br/>Research completed 29 October 2026','SmallX')
p('<b>LUMIO (Lunar Meteoroid Impacts Observer) is a comparator for both science and technology demonstration, and its public design depends on the version.</b> Its two-band camera, onboard flash confirmation and data reduction, maintained orbit around the Earth-Moon L2 point and extended windows on the dark farside already address much of the broad science case. SMD therefore needs an advantage in a measured outcome that goes beyond farside access or finer timestamp ticks. [L02, L06, L18]')
table(['Question','Evidence-backed answer'],[
 ['Mission purpose','LUMIO observes and characterizes farside impact flashes, complements ground monitoring and improves lunar meteoroid models. It also demonstrates autonomous technologies for small spacecraft.'],
 ['Success criteria','The historical orbit acceptance of 2018 required at least 240 detections, including 100 lower-energy and two higher-energy impacts, and a lifetime of at least one year. We did not find current definitions of minimum or full success.'],
 ['Orbit','A quasi-periodic halo orbit around Earth-Moon L2 with a motion of approximately two weeks. Visibility of the full disc differs from usable dark exposure and from the whole-surface coverage that SMD needs.'],
 ['Duration','One year of nominal operations, divided between science windows and navigation or engineering windows. The minimum is documented, but we did not find an optimization that establishes exactly one year.'],
 ['Why CubeSat','The choice follows the original constraints of the ESA LUCE programme and a demonstration or piggyback strategy. Later accommodation of hardware led to larger envelopes and more mass, so the form factor is not an unrestricted optimum.'],
 ['Current status','Phase C since March 2026; Critical Design Review (CDR) planned for 2027; potential launch in 2028. ESA and the prime contractor state 12U/12UXL, which conflicts with the 16U given by ASI. No confirmed explanation of a redesign exists.']
],[1,3.5])
head('Implication for SMD')
p('We should test one focused hypothesis: recover a calibrated measure of the early optical energy relative to the total, in useful samples, beyond what LUMIO and modern ground monitoring can do. The event sensor remains central. The design must preserve access to the entire lunar surface, including the poles and both hemispheres. This study selects no SMD hardware, orbit, lifetime or numerical requirement.')
p('Evidence: L01-L04, L06, L19-L20. This supporting report is separate from the inclusive 50-page mission-design report. The detailed claims and exact source locations are given in the companion workbook and the Markdown findings.','SmallX')

page('1. Science, products and published criteria')
p('The underlying science question concerns the spatial and temporal characteristics of meteoroids that hit the Moon. LUMIO measures optical flashes. Luminous energy and equivalent blackbody temperature are closer to this observable than kinetic energy or the mass or size of the impactor, which require additional physical assumptions. Hazard modelling is a downstream application, not a demonstrated warning service. [L17 p311; L18 pp3-4; L02]')
table(['Layer','Documented content','Status'],[
 ['Science','Flux, magnitudes, luminous energies, inferred sizes and locations; temperature inferred from the two bands','Stated objectives'],
 ['Complementarity','Improve spatial, temporal and measurement access beyond nearside ground observations','Objective; global information does not guarantee access to every surface region'],
 ['Technology','Autonomous optical navigation, trajectory control, miniaturized payload, propulsion and platform technology, and onboard processing','Separate demonstrations; nominal radio navigation remains'],
 ['Verification','Design and simulation evidence exists; Phase C plans engineering models and further verification','No LUMIO flight demonstration established']
],[1,3,1.6])
head('Historical numerical acceptance, 2018')
table(['Criterion','Paraphrased numerical content'],[
 ['EC.A.01','Envelope of Earth-equivalent kinetic energy from 10^-6 to 10^-1 kton TNT.'],
 ['EC.A.02','At least 240 detected impacts during the mission life.'],
 ['EC.A.03','At least two impacts in 10^-4 to 10^-1 kton TNT.'],
 ['EC.A.04','At least 100 impacts in 10^-6 to 10^-4 kton TNT.'],
 ['EC.A.05-07','Monitoring of the night farside; a minimum life of one year; access and maintenance within the historical total budget of 200 m/s.']
],[1,4])
p('Source: L20 section 2.1. The total-count criterion was motivated by the size of ground-monitoring samples. The selection criteria maximize the count and the full-disc time and minimize the delta-v. These are published acceptance criteria of the orbit trade, not verified contractual thresholds of the current Phase C. We could not establish a controlled current taxonomy of minimum and full success.','SmallX')
p('The 2024 payload requirement states an integration time of <b>at least 30 ms</b>. This must not be turned into an upper bound of 30 ms on the temporal resolution. Likewise, a processor capacity of 15 images/s does not establish the camera cadence. [L05 p5 Table 3-1; p10 Table 6-1]')

page('2. Orbit geometry and transfer rationale')
p('A halo seed in the circular restricted three-body problem (CRTBP) with Cj = 3.09 is refined into a quasi-periodic ephemeris trajectory. Cj, the Jacobi constant, is not conserved in that full model. The orbit trade couples science yield, access to the dark farside, full-disc navigation images, safety, and the costs of transfer and maintenance. [L20 sections 2.1, 3; L05 section 4.1]')
fig('geometry')
table(['Geometry quantity','Result','Interpretation'],[
 ['Moon-centre range','36000-86000 km','Historical L18 trajectory; ESA 2026 rounds this to 40000-80000 km'],
 ['Earth-centre range','380000-470000 km','L18 section 2.2 and Fig 5'],
 ['Visible surface cap','47.6-49.0% instantaneously','Sphere calculation; a full disc is not the full surface'],
 ['Near/far signal factor','6.05 at nadir','Same source, inverse-square range only; the centre-range shortcut gives 5.71']
],[1.4,1.3,2.6])
p('The sampling uses a spherical Moon of radius 1737.4 km and a nominal angular pitch of 6 deg/1024. It excludes errors in attitude knowledge, boresight, orbit, timing and terrain, so it is not a localization accuracy. Sampling at the limb is worse. We ran no new simulation of geographic coverage.')
head('Keep transfer budgets tied to their release conditions')
p('Release into a lunar parking orbit in 2018 gives a whole-mission budget of 154.4 m/s at 1 sigma, including one year of stationkeeping and disposal. The Phase-A cases of 2022 give 119.5 m/s for CLPS against 201.8 m/s for Artemis 2, both with margin. The 2024 table for the weak-stability-boundary (WSB) transfer, Layer 2, sums to 79.05 m/s. The costs of the carrier\'s trans-lunar injection (TLI) from Earth do not belong in the CubeSat budget. These are alternatives from different design epochs. [L20 Table 12; L17 Table 1; L05 Table 4-1]')
p('The Phase-B stationkeeping result is a mean of 8.256 m/s/year and 15.79 m/s at its stated 3-sigma budget, with a tracking cutoff of 2 days. It is a published Monte Carlo result that we did not rerun. Halo motion requires maintenance. Visibility of the full disc or the Earth and an eclipse-free reference geometry do not remove the exclusions for illumination, stray light, the radio link or operations. [L05 pp7-8; L07 slides 6-7]','SmallX')

page('3. Duration, exposure and expected samples')
p('<b>One nominal year is not one year of continuous science.</b> The current concept alternates science windows of roughly half a lunation with navigation, communications, stationkeeping and wheel unloading. A platform slide from 2024 gives a design life of 1.5 years. Examples for transfer and commissioning range from about 95 days for one chosen trajectory to about 150 days in a navigation timeline; these are different study cases. [L02; L05 pp7-8; L07 slide 8; L21 p2]')
fig('operations')
table(['Calculation','Value','Limit'],[
 ['Lunations per 365.25 days','12.37','Conversion with a 29.53059-day convention, not an exact halo resonance'],
 ['Ideal half-cycle science','182.625 days / 4383 h','Before losses to stray light, calibration, recovery and availability'],
 ['With a further 90% / 70% availability','3944.7 h / 3068.1 h','Assumed sensitivities, not a predicted delivered time'],
 ['Rough source area-time','4.99e10 km2 h','3/8 dark surface x half a year x 0.8 obstruction; not a regional map']
],[1.6,1.6,2.8])
head('Why exactly one year?')
p('The original trade explicitly sets a minimum of one year and links more detections and a longer life to better meteoroid models. A lower delta-v can save resources for an extension. The reviewed sources do not show an optimization that chose exactly one year, nor do they prove that radiation, funding or propellant exhaustion alone set it. Sampling a full annual cycle of seasons is a plausible inference, but useful illumination at every shower peak is not guaranteed. [L20 section 2.1; L17 p312]')
head('Yield is not a success threshold')
p('The 2023 paper attributes about 4200/5500 detections to the methods of 2018 (the 2018 paper itself gives a range of 10^3-10^4). The 2023 model gives 37000 detections with a scenario standard deviation of 830, using 1000 scenarios, the old camera and the 2024-2025 timeline. Its spread of 2.24% excludes major systematic uncertainty in the model. Alternative flux laws for sources near the threshold differ by about 13.7. The paper contains conflicting statements on the peak rate of the Geminids, so we adopt no shower peak. [L18 Table 9 p14, section 6, conclusion]')
p('We found no approved duration for an extension. The 2025 study of the Apophis opportunity does not itself change the nominal life. The end of the Phase-C project in September 2027 is a development milestone, not the end of science operations. [L12; L04]','SmallX')

page('4. Why CubeSat, and the payload that must fit')
p('The original ESA LUCE programme set the small-spacecraft boundary. Slide 5 of its 2017 presentation lists an individual mass below 24 kg and a volume below 12U, a total below 60 kg, deployment and relay by a lunar orbiter, about one hour of contact per day and 10 days of autonomy. This is programme heritage, not evidence that 12U is the scientific optimum. SMD has no CubeSat requirement. [L19 slides 3-6; L08]')
p('The published design grows from about 21 kg through 22.8 kg to 28.69 kg as the transfer, redundancy and margins evolve. Accommodating a long baffle motivates the consideration of 12UXL, and the 2024 structure has lateral protrusions. On the July 2024 slide the camera alone occupies roughly 3U plus 1U of proximity electronics. We could not establish a compatible total lifecycle cost. [L17 pp312-316; L05 p13; L07 slide 5]')
table(['Payload / thermal quantity','Published detail','Epoch / source'],[
 ['Optics','50.8 mm pupil; 127 mm focal length; f/2.5; total field of 6 deg; seven lenses','October 2024, L06 Table 3 p3'],
 ['Detectors','Two 1024x1024 CCD201-20 electron-multiplying CCDs (EMCCDs) with 13 um square pixels','L06 Table 2 p2'],
 ['Channels','VIS 450-800 nm; NIR 850-950 nm','L06 Table 1 p2; not the ideal 820 nm split'],
 ['Acquisition','Minimum of about 78 ms per full frame / 13 fps; the synchronization between channels is small relative to the exposure','L06 p2; the older 66 ms model remains separate'],
 ['Transmission','78% VIS / 84% NIR for the design optics, including a 30 krad load on the first two lenses','L06 p3; not the total detector efficiency'],
 ['Temperature for performance','Optics 14-26 degC; detectors 0-10 degC','L06 Table 5 p6'],
 ['Thermal architecture','Heaters, thermistors and detector straps to the platform radiator; stabilization of the barrel','L06 pp3-6'],
 ['Mechanical interface','Titanium barrel and Al6082 baffle; compliant, isostatic support','L06 pp4-5']
],[1.4,2.6,1.8])
p('L06 explicitly labels its optical figures as design-level and excludes manufacturing and alignment errors. Its Phase-B thermal study uses steady hot and cold cases, and the hot case still needs optimization. The operating range of the whole camera (-20 to 40 degC) and its survival range (-30 to 50 degC) are distinct from the performance ranges. We infer no camera qualification and no calibrated capability for faint flashes.','SmallX')

page('5. Platform and subsystem design evidence')
table(['Subsystem','Source-backed Phase-B design','Public limitation'],[
 ['Power','Two deployable IMT microSADA solar arrays; Volta power conditioning and distribution unit (PCDU) with MPPT/BCR and protected rails; ABSL 124 Wh 7S2P battery at about 28 V','Mode durations, state of charge (SOC), reserve and final end-of-life (EOL) power are not closed here'],
 ['Thermal Control','Mostly passive platform with heaters; radiator, heater and strap interfaces for the payload','No final transient thermal model from Phase C and no verified optical stability'],
 ['Structure','Custom Argotec primary and secondary structure in Al7075 T7351, with protrusions','No final controlled envelope and no load or qualification record'],
 ['Propulsion','LMP-103S with helium blowdown; one ECAPS 1N engine; R134a cold gas with four reaction-control (RCS) thrusters','The 2024 baseline is subject to change; the details after the Delta PDR are incomplete'],
 ['Telecommunication','Direct-to-Earth (DTE) X-band; IMT C-DST transponder with two patch antennas; 2 W RF on the mission slide','No final data rate, station schedule or link margin'],
 ['ADCS','XACT-100, star trackers, gyros and Sun sensors; three 100 mNms wheels plus one 50 mNms wheel; RCS unloading','Momentum storage is not torque; pointing control is not surface accuracy'],
 ['On-board Data Handling','Reworked Argotec Fermi CPU/FPGA, CAN interface and MRAM boot; payload processing by S&T','The exact current memory, software, clock and throughput of the complete chain are not established']
],[1.1,3,2.2])
p('Sources: L05 sections 6.1-6.6, pp10-13; L07 slides 8-9. The ESA update of 2026 confirms the roles of the organizations, but not every component number from 2024. Generic product capability from a vendor is not proof that LUMIO selected or qualified the product.','SmallX')
head('Operations, navigation and interfaces')
p('Nominal radio navigation is direct to Earth. The optical navigation experiment extracts the lit lunar limb and estimates the state with an extended Kalman filter (EKF). Subpixel precision on the limb and poorer accuracy in depth along the line of sight do not imply an impact-location ellipse of 1 km. Polimi leads, Nautilus supports flight dynamics, and the ground design is being consolidated. Current ESA planning targets disposal by lunar impact. [L02; L05 section 5; L21 pp4-8; L01]')
head('Why onboard science reduction is necessary')
p('Five tiles of 50x50 pixels x 2 channels x 16 bit/pixel give 0.4 Mbit per flash. For the 37000 model events this gives 14.8 Gbit/year before overhead and compression, consistent with the approximate 15 Gbit quoted. A continuous two-channel stream of 1024-square frames at 16 bit and 15 fps would instead need 503.3 Mbit/s, or 5.44 TB/day (decimal). These are encoding calculations, not a measured interface or a final storage budget. [L18 p4]')

page('6. Configuration conflicts and budget checks')
table(['Issue','Conflicting evidence','Treatment'],[
 ['Form factor','ESA/prime 12U/12UXL; ASI 16U','Unresolved; no confirmed redesign'],
 ['Dates','Profile: kickoff in March 2025 and launch in 2027 or later; dated record: kickoff in March 2026 and potential launch in 2028','Prefer the dated 2026 status; future targets remain uncertain'],
 ['Camera','66 ms / 15 fps and an 820 nm split, versus 78 ms / 13 fps and updated bands','Keep the model and design epochs separate'],
 ['Transfer','Lunar parking or relay with higher budgets, versus WSB, DTE and 79.05 m/s','Do not add the carrier TLI or blend propulsion epochs'],
 ['Mass','28 kg requirement; 28.69 kg table; about 30 kg in the overview','The subsystem lines sum to 23.28 kg against the printed 23.41 kg dry'],
 ['Payload budget','20 W allocation / 19 W mode versus 27.8 W worst case; 3.85 versus 4.8 kg with margin','No invented compliance or corrected budget'],
 ['Power','98.76 W available minus 88.94 W for science gives 9.82 W, not the printed 6.59 W','The inconsistency in definition or source is retained'],
 ['RCS impulse','Requirement of 110 N s versus a total impulse of 170 s in the text','Unit and value unresolved'],
 ['Disposal/life','Earlier escape versus later lunar impact; 1 y of operations versus 1.5 y design life','Use the later plan; do not equate the definitions']
],[1,2.5,2.5])
p('Sources: L01-L05, L06, L07, L17, L18. The full conflict log with 13 cases is in the workbook, with exact locations for each claim. These public inconsistencies do not prove that the flight design is infeasible, but they prevent us from treating the tables as a closed current design.','SmallX')
head('Reproducible arithmetic results')
p('The printed mass subtotal of 23.41 kg plus 2.34 kg system margin, 1.17 kg harness and 1.77 kg propellant does equal 28.69 kg. The displayed delta-v entries sum to 79.05 m/s, which is 0.95 m/s below the PROP-01 requirement of 80 m/s. The payload line of 4.8 kg also exceeds PLD.004 (4.5 kg). These successful sums coexist with the discrepancy in the dry subsystems. [L05 Tables 4-1, 6-3]')
p('The margined manoeuvre demand of 192.27 W exceeds the array availability of 98.76 W by 93.51 W. Dividing the 124 Wh nameplate capacity by that deficit gives 79.6 minutes as an ideal upper allowance. Usable SOC, efficiency, reserve, heater timing and degradation reduce it. This is not a demonstrated closure of the battery or of the propulsion mode. [L05 Table 6-4 and section 6.3]')

page('7. Normalized comparison and one science hypothesis')
p('A fair comparison starts from the same incident spectral flash, emission geometry and range. It then models the aperture, the throughput and quantum efficiency (QE), the point-spread function (PSF) and background, stray light, the time integration or event response, losses, confirmation and selection. No compatible, calibrated end-to-end detection curves for SMD and LUMIO were available, so this study makes no ranking of limiting energy. [L06; L18]')
fig('temporal_integration')
p('For F(t) = F0 exp(-t/tau), t >= 0, and contiguous bins without gaps, the best ratio of the largest-bin mean to the true peak is (tau/T)(1 - exp(-T/tau)); the worst onset phase divides this by (2 - exp(-T/tau)). We checked the extrema independently. At tau = 10 ms the best values are 0.952/0.787/0.151/0.128 for bins of 1/5/66/78 ms. The total energy remains recoverable if every ideal bin is retained. Noise, sensor bandwidth and readout loss are excluded. An ideal 1 ms bin is an assumption, not demonstrated event-sensor performance.')
head('Hypothesis: early energy relative to total optical energy')
p('We propose to test the relation between the energy in the first 5 ms and the total band-limited energy for a defined class of impacts. The 2026 ground sample already resolves four events at 200/250 fps with complex shapes and suggests that the early intensity need not follow the total energy. That sample is too small to establish a population law. SMD should add calibrated samples in the time domain, with a bounded tail and a recovered onset, and not simply a finer clock. [L22 sections IV-V]')
p('For independent sample means, the relative error is approximately CV/sqrt(N), where CV is the coefficient of variation. A trial CV of 1 gives 100 useful events for a mean precision of 10%; two groups need about 450 events each to detect a 20% difference in the mean at 3 sigma. These are sensitivities, not accepted requirements. Variance, covariance and selection bias should be estimated before a count is adopted. Coupled recovery must meet the temporal, photometric and location cuts together.')

page('8. D01-D10 conclusions and next work')
table(['Driver','Consequence for SMD'],[
 ['D01','Recover radiometric detection and characterization jointly; no sensitivity gain is established from photons or timestamp ticks alone.'],
 ['D02','Compare the recovery of early energy and profile against the 66/78 ms of LUMIO and the observed 4-5 ms ground acquisition, including onset phase and sensor bandwidth.'],
 ['D03','Close the absolute, background and tail information and its uncertainty; use the minimum supporting reference needed.'],
 ['D04','Propagate pointing knowledge, boresight, orbit, timing and the digital elevation model (DEM) into 95% surface regions, including limb and polar cases.'],
 ['D05','Preserve both hemispheres and the poles; full-disc framing from L2 plus a ground complement does not prove exposure of the entire surface.'],
 ['D06','Predict useful characterized samples with recovery of energy, profile and position; do not copy model detections or catalogue minima.'],
 ['D07','Separate particle and raw candidates, confirmed false flashes and loss of true signal; keep the reduction diagnostics and the pre- and post-event history.'],
 ['D08','Select the bandpass, background, temperature, dynamic range and duration envelope consistently with the payload and thermal design.'],
 ['D09','Derive the lifetime from useful samples, seasonal opportunities, maintenance, availability and end-of-life performance.'],
 ['D10','Size burst buffers and downlink contacts; require rapid delivery only if it serves the selected primary science.']
],[.6,5])
p('Evidence mapping: L06/L18 for D01-D03 and D08; L05/L06 for D04; L02/L20 for D05; L18/L20/L22 for D06; L06/L18 for D07; L02/L05/L07 for D09; L05/L18 for D10. The companion comparison table keeps the individual sources and the next evidence needed.','SmallX')
head('Bounded next analysis')
p('The next analysis should choose one observable and an uncertainty target, and compare two or three realistic cases of event sensor and optics with the minimum radiometric support. It should compute the usable exposure of the whole surface and the joint sample yield, and close the interfaces between modes and resources. Radiation and disturbance results should be used where they apply. First-principles payload evidence with bounded unknowns meets the educational standard; new hardware experiments are not mandatory.')
p('The comparator and the essential justification of the gain should take roughly 2-3 pages of the final report, with the detail kept in these supporting records. This recommendation does not expand the inclusive budget of 50 pages. LUMIO performance and schedule should be refreshed at the SMD decision date, because the potential delivery in 2028 and the ground evidence of 2026 are already relevant competitors.')

page('9. Sources, access and verification limits')
for rec in D['sources']:
 sid,title,date,epoch,loc,kind,url,limit=rec
 p(f'<b>{sid}</b> <link href="{escape(url)}" color="#294C72">{escape(title)}</link>. {escape(date)}. {escape(loc)}.','SmallX')
p('<b>Access:</b> the supplied PDFs from 2022 and 2023 were retained, and the ESA, ASI and prime-contractor pages and the original challenge material were cached. Some PDF downloads from Polimi returned HTTP 403. We reviewed and cached the publicly indexed full text of these PDFs and recorded the failed download and visual-page access. No inaccessible table was treated as visually verified.','SmallX')
p('<b>Executed:</b> analytic geometry, rough exposure, bin integration, source arithmetic and checks of sample and data volume; live workbook formulas and checks of input changes; PDF text and layout checks and visual renders. <b>Not executed:</b> trajectory propagation, a new LUMIO Monte Carlo, calibration of the selected sensor, irradiation, hardware qualification, native Excel operation or a complete SMD yield simulation.','SmallX')

def footer(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#C7D2DE'));canvas.line(44,39,A4[0]-44,39)
 canvas.setFont('Report',7.5);canvas.setFillColor(colors.HexColor('#5B6C80'))
 canvas.drawString(44,26,'SMD supporting research | 29 October 2026 | Design targets remain version-specific')
 canvas.drawRightString(A4[0]-44,26,str(doc.page))
doc=SimpleDocTemplate(str(OUT/'lumio_mission_comparison_report.pdf'),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=42,bottomMargin=52,title='LUMIO and SMD: mission comparison',author='SMD research')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Built lumio_mission_comparison_report.pdf')
