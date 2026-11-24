"""Seven-page concept/SRR report (prose restyled 2 November 2026; content unchanged). Run with the bundled PDF Python runtime."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether, CondPageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

H=Path(__file__).resolve().parent;ROOT=H.parents[1]
OUT=ROOT/'outputs/radiation_environment_research_2026-10-29'
S=json.loads((H/'research_data.json').read_text());R=json.loads((H/'model_results.json').read_text())
font='/usr/share/fonts/TTF/DejaVuSans.ttf'
if not Path(font).exists(): font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold=font.replace('DejaVuSans.ttf','DejaVuSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('Report',font));pdfmetrics.registerFont(TTFont('ReportBold',bold))
styles=getSampleStyleSheet()
for name,size,lead,color in [('Body',9.4,14,'#26384C'),('Small',7.6,11,'#4B5E72'),('TitleX',21,27,'#233E60'),('HeadX',13,18,'#294C72')]:
    styles.add(ParagraphStyle(name,fontName='Report',fontSize=size,leading=lead,textColor=colors.HexColor(color),spaceAfter=8))
styles['TitleX'].fontName='ReportBold';styles['HeadX'].fontName='ReportBold';styles['HeadX'].keepWithNext=1
styles.add(ParagraphStyle('Cell',fontName='Report',fontSize=8,leading=11,textColor=colors.HexColor('#26384C')))
styles.add(ParagraphStyle('TH',fontName='ReportBold',fontSize=8,leading=11,textColor=colors.white))
W=A4[0]-88;story=[]
def p(text,style='Body'): story.append(Paragraph(text,styles[style]))
def heading(n,title): p(f'{n}. {title}','HeadX')
def table(headers,rows,widths):
    data=[[Paragraph(escape(str(x)),styles['TH']) for x in headers]]+[[Paragraph(escape(str(x)),styles['Cell']) for x in r] for r in rows]
    t=Table(data,colWidths=[W*v/sum(widths) for v in widths],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#294C72')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F0F4F8')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([t,Spacer(1,10)])
def fig(name,width=W):
    path=ROOT/'figures/radiation_environment'/f'{name}.png'
    im=PILImage.open(path);story.append(Image(str(path),width=width,height=width*im.height/im.width));story.append(Spacer(1,8))
def page():story.append(Spacer(1,6))   # 2 Nov 2026 restyle: sections flow on; headings move to a new page when little room is left
def dose(c,t):return next(r['dose_krad_Si_year'] for r in R['dose_rows'] if r['case']==c and r['shielding_mm']==t)

p('Lunar radiation environment','TitleX')
p('Quantitative comparison and decisions for the SMD event-camera concept<br/>29 October 2026','Small')
heading(1,'What the team should do')
p('<b>We recommend continuing the concept with explicit radiation allowances.</b> At present, radiation does not cause a feasibility failure at mission level. The main uncertainty concerns the payload: it is not known whether a chosen sensor keeps a useful recording quality for faint flashes and whether it can reject artefacts caused by particles. The existing evidence on event cameras supports feasibility under these conditions, but the response of the selected device has not been qualified.')
table(['Matched published case','Dose at 2.54 mm Al','Distant / LEO'],[
 ['LEO 550 km / 6°',f"{dose('LEO550_6',2.54):.1f} krad(Si)/year",'1.7'],
 ['LEO 800 km / 98°',f"{dose('LEO800_98',2.54):.1f} krad(Si)/year",'0.78'],
 ['Interplanetary, distant lunar proxy',f"{dose('Interplanetary',2.54):.1f} krad(Si)/year",'Reference'],
 ],[2.1,1.5,1])
p('All three cases use the same silicon target, solid aluminium spheres, solar maximum and the 95% confidence level of the source. The values were digitized from NASA/TM-20250006822, Fig. 10, p. 11 [RAD01]. A reading allowance of ±15% should be added, separately from the uncertainty of the source model. The two low Earth orbit (LEO) cases do not represent every Earth orbit.','Small')
table(['Proposed concept action','Basis / status'],[
 ['Protect critical electronics and power independently','Use error correction with scrubbing, a watchdog, a recoverable boot, current protection and autonomous restart. The complete chain must be verified.'],
 ['Trade local shielding of 2-3 mm aluminium equivalent','3 mm of aluminium costs 8.1 kg/m². A 10 cm internal cube needs 0.516 kg for six closed walls, before any credit from the structure.'],
 ['Screen electronics of a 30 krad class','Three years at 4.25 krad plus an assumed 1 krad for the transfer gives 13.8 krad. With an assumed margin of 2 this becomes 27.5 krad. This is a trade, not a requirement.'],
 ['Carry terms for sensor drift, false candidates and downtime','No public radiation qualification of the IMX636 was found. Test tolerances and flight heritage of DAVIS or PPS3 sensors must not be transferred to it.'],
 ['Keep the focused science and coverage scope','No second channel or spacecraft is added for radiation alone. Exclusions are integrated into the exposure of both hemispheres and the poles.']
 ],[1.4,2.7])
p('The 30 krad class uses the central reading of the curve. Keeping a margin of two at the +15% reading gives 31.3 krad, so available 50 krad parts should be compared before a selection is made. No orbit, lifetime, shielding or sensor is baselined. New irradiation tests are not an educational prerequisite.','Small')
page()

heading(2,'Cases and physical effects')
table(['Fixture','Definition','Quantitative status'],[
 ['LEO context E1 / E2','400 km / 51.6°; 600 km / 98°','No matched shielded dose is available. Values must not be interpolated from other inclinations or altitudes.'],
 ['Published LEO E3 / E4','550 km / 6°; 800 km / 98°','These cases are matched to the evidence in RAD01 and are used for direct dose ratios.'],
 ['Low lunar L1','100 km polar orbit; distance from the lunar centre 1837.4 km','The isotropic primary sky fraction is 0.663. A full dose transport calculation was not run.'],
 ['Distant lunar L2','50,000 km from the lunar centre; nadir range 48,262.6 km','This case is a proxy for interplanetary exposure. No halo orbit or magnetotail timeline is selected.'],
 ['Transfer T1','Actual crossings of and residence in the Earth belts','This needs a separate dose ledger. The 1 krad value is only an arithmetic allowance.']
 ],[1,1.8,2.5])
p('A target range of 50,000 km to a nadir target would instead mean a distance of 51,737.4 km from the lunar centre. A range alone does not define a libration orbit, and the lunar surface should not be called an observing orbit of the spacecraft.')
table(['Effect','Earth LEO','Lunar observer'],[
 ['Trapped particles','Access to the South Atlantic Anomaly and the belts depends strongly on altitude and inclination.','There are no comparable persistent global belts at the Moon, but the exposure during the transfer from Earth remains.'],
 ['Galactic cosmic rays (GCR)','Geomagnetic access varies with latitude and rigidity.','A quiet, penetrating background that is typically larger near solar minimum.'],
 ['Solar energetic particles (SEP)','Geomagnetic shielding can reduce access, but the polar regions remain exposed.','Solar particles arrive unshielded with episodic high flux, so both solar states must be assessed.'],
 ['Body and secondary particles','Earth blocks directions, and the atmosphere and magnetic field add shielding.','The Moon blocks directions and produces secondary and albedo particles.'],
 ['Charging','The dense ionosphere, the array voltage and auroral access matter.','The solar wind, the lunar wake and the hot plasma of the magnetotail matter. Charging is separate from total ionizing dose (TID).']
 ],[.8,1.9,2])
p('For an opaque body in an isotropic primary field, the visible fraction of the sky is f = [1 + √(1 - (R/(R+h))²)] / 2. It is 0.5 at the lunar surface, 0.663 at 100 km altitude and 0.99970 at 50,000 km from the centre. Applying f to the primary flux only illustrates the geometry. It does not predict the dose when solar particles arrive anisotropically, when the aperture has a given orientation, or when secondary particles are produced.')
p('Absorbed dose in silicon is given in rad(Si) or krad(Si), with 1 krad = 10 Gy = 10 J/kg. The human effective dose in Sv includes a biological weighting and is not a component tolerance. A ratio to the terrestrial human background dose therefore cannot qualify spacecraft electronics.','Small')
page()

heading(3,'Dose, duration and model limits')
fig('matched_dose_depth')
table(['Al (mm)','550 km / 6°','800 km / 98°','Distant proxy'],[
 [f'{t:g}',*[f'{dose(c,t):.2g}' for c in ['LEO550_6','LEO800_98','Interplanetary']]] for t in [1,2,2.54,3,5]
 ],[1,1,1,1.2])
p('All dose columns are in krad(Si)/year, for the 95% confidence level of the source, solar maximum and uniform solid aluminium spheres [RAD01]. At 2.54 mm, the ratio ranges that follow from the reading alone are 1.22-2.24 against the 550 km LEO case and 0.57-1.05 against the 800 km LEO case. The model covariance and the full uncertainty are not available, so the second pair does not rank the two environments robustly.','Small')
p('<b>Quiet measurements cannot replace a design for solar storms.</b> LRO accumulated 12.2 rad(Si) during its first 333 days in the quiet period of 2009-2010, which corresponds to 13.4 rad/year. Its minimum aluminium paths were not uniform: 0.89 g/cm² towards the Moon and 2.28 g/cm² towards space. These are not the conditions of RAD01 [RAD02, abstract, paras 16, 22].')
p('The three-year calculation is a sensitivity to the mission duration. Multiplying a one-year curve at 95% confidence by three does not give a three-year 95% quantile for solar particle events. The 1 krad transfer allowance must be replaced by evidence from the actual trajectory. At an assumed 1 krad/day, an exposure of six hours gives 0.25 krad and an exposure of 30 days gives 30 krad. These are examples of time scaling, not predictions for the belts.')
p('NASA reports SEP inputs from SPENVIS, belts from IRENE and dose from FASTRAD, but without complete versions, epochs or spectra. The current documentation lists SPENVIS 4.6.14 and IRENE V1.58.001 [RAD10-11]. No environment or transport code was run in this study.','Small')
page()

heading(4,'Payload artefacts and degradation')
table(['Evidence','What it supports','What it does not establish'],[
 ['DAVIS240C on the ISS [RAD04]','Limited degradation in intermittent data from 2022-2024, in a 6.35 mm aluminium enclosure with open apertures.','The tolerance of the IMX636, lunar exposure, or a calibrated recording quality for faint flashes.'],
 ['PPS3MVCD / DAVIS346 [RAD05]','Background activity that grows with dose, functional problems above about 30 krad, and a proton-induced lock-up that could be recovered.','A universal failure threshold or a transferable degradation law. The support circuitry of the camera can make the cause of a failure unclear.'],
 ['DAVIS346 with 64 MeV protons [RAD05]','1.498×10¹¹ p/cm² at 20 krad, with a reported growth of about 70% in dark current and 23% in dark noise (filter off).','A separation of the TID and displacement damage responses, a 1 MeV neutron-equivalent fluence, or a mission lifetime for the IMX636.'],
 ['Neutron-tested event sensors [RAD06]','Compact clusters and tracks, with relaxation times of about 0.6-0.8 ms for ON and 8-10 ms for OFF events.','A lunar proton cross-section, or proof that ON/OFF tails uniquely identify optical flashes.']
 ],[1.15,1.75,2])
p('The IMX636 has a footprint of 1280×720×(4.86 µm)² = 0.217678 cm² [RAD07]. Its public product brief gives no radiation rating. The sensitive charge-collection region, the package response and the readout chain may differ from this geometric area.')
table(['Incident j ≥10 MeV','Front-face incidence','Interpretation'],[
 [f"{r['input_flux']:g} pfu",f"{r['incident_rate_s']:.3g} particles/s",'πjA, assuming an isotropic incident field'] for r in R['sep_screening']
 ],[1.1,1.2,2])
p('The NOAA thresholds S1, S3 and S5 provide flux conventions, not lunar spectra or durations [RAD14]. The counts apply before optics, shielding and the sensor response. They exclude back, side and secondary populations, and they are not upper bounds on total hits or false flashes. The unknown transmission, response probability, multiplicity and false confirmation must be carried explicitly.','Small')
p('The spacecraft should keep raw candidate snippets, rejected diagnostic samples, bias and temperature, masks and event-loss counters. Drift in threshold and latency, dark activity, quantum efficiency (QE) and losses caused by filtering should be modelled for end of life. Rejecting isolated events can also erase faint real flashes or bias the early-to-total energy. A particle crossing, a raw burst of events, a candidate and a confirmed false flash are different populations.')
p('Displacement damage dose (DDD) requires the spectrum multiplied by the non-ionizing energy loss (NIEL) in MeV/g(Si), or an explicitly referenced equivalent fluence [RAD12]. Compatible spectra and coefficients for the IMX636 were not obtained. Displacement damage and the degradation of the solar arrays therefore remain numerical gaps, and they are not inferred from TID.','Small')
page()

heading(5,'Electronics, shielding and charging')
fig('shielding_mass')
p('Local protection of the electronics should be traded against the mass of a full enclosure. The existing structure can only be credited as shielding once a map of directional paths exists. The optical aperture, the penetrations for boards and cables, and the production of secondary particles must be included. More aluminium cannot guarantee immunity to penetrating cosmic rays, destructive single-event effects (SEE) or camera artefacts.')
table(['Function','Proportionate design route'],[
 ['Processing and control','Parts selected with radiation in mind, an independent supervisor, a watchdog and recovery after reset. The RTG4 offers an available class above 100 krad with a hardened configuration and SECDED internal memory [RAD09]; its exact suitability and power are still to be confirmed.'],
 ['Memory, boot and timing','Error correction with scrubbing, CRC, a recoverable boot and suitable interleaving. External memory and its controller, as well as multi-bit and common-mode faults, need separate evidence. The validity of timing should be flagged after a reset.'],
 ['Power','Current-protected domains and autonomous restart. The TPS7H2201-SP covers 1.5-7 V and 6 A, is rated to 100 krad and was tested for destructive SEE up to an LET of 75. Its SEP grade differs. A maximum of 35 mΩ at 25°C and 5 V (CFP/KGD) gives 0.14 W at 2 A; sizing for hot and end-of-life conditions remains to be done [RAD08].'],
 ['Solar arrays','Select the cell and coverglass, compute the transmitted equivalent fluence and apply the manufacturer\'s degradation curves. No percentage of radiation loss is predicted here.']
 ],[1,3.6])
p('<b>Charging is independent of the dose in silicon.</b> NASA reports spacecraft potentials of -100 to -300 V under solar-particle conditions and of -40 to -80 V in the geotail. The value of -4.5 kV refers to the potential of the lunar surface, not to this spacecraft [RAD15, slide 37]. The design should use bonding, controlled surfaces, careful placement of dielectrics and protection against electrostatic discharge (ESD). The actual differential potentials, the currents and the residence in the magnetotail have not been modelled.')
p('Powering equipment down may reduce some functional interruptions, but it does not remove TID or displacement damage, and it does not prove freedom from destructive events. A rated switch also does not by itself protect the downstream load from latch-up: trip time, threshold, stored energy and restart must be sized for the actual load.','Small')
page()

heading(6,'SEE, availability and the primary observable')
fig('let_environment_scale')
p('Device rates should only be computed with compatible cross-sections as a function of energy, linear energy transfer (LET) and angle, at the device bias and temperature. The differential flux and the cross-section must be integrated with consistent angular conventions [RAD13]. No rate of SEE, SEFI or SEL for the selected chain and no qualified completion probability was obtained. For a known rate λ that varies in time, P(≥1) = 1 - exp(-∫λ dt). A tested LET ceiling alone does not provide λ.')
p('As a sensitivity on availability, five excluded days per year give an availability of 98.63% from radiation alone. Adding an assumed 0.1 resets per day with a recovery of 60 s gives 98.62%. Thirty excluded days give 91.79% availability from storms alone. These values are allocations, not predictions of downtime from solar events. All other observing losses are counted separately.')
table(['Driver','Radiation term to retain'],[
 ['D01-D03','End-of-life noise and QE, drift in contrast and latency, event loss and calibration bias in the useful characterized sample.'],
 ['D05 / D06','The usable area-time per region and the sample yield after exclusions, including both hemispheres and the poles. Unique flashes that are missed cannot be recovered by a later revisit.'],
 ['D07 / D08','The chain from particle crossing to candidate to confirmed false flash, the rejection of true flashes, and the envelope of temperature, background and bias in which the results are valid.'],
 ['D09','The probability of permanent failure, kept separate from reset recovery, storm exclusions and the science quality at end of life.']
 ],[1,3.9])
p('A uniform loss of 1.4% of the samples would increase the simple Poisson uncertainty of the flux by only about 0.7%. A storm that coincides with a meteoroid stream, or with scarce observing time at the poles, can have a much larger scientific effect. Exclusions should therefore be applied to the actual timeline rather than to a single coverage percentage.','Small')
p('Health telemetry and useful space-weather information should be used for a degraded or safe mode, with hysteresis before recovery and with calibration checks. External alerts are not a guaranteed warning service. A dedicated radiation monitor, a second optical channel or a redundant spacecraft remains optional until it resolves a demonstrated need of the mission.','Small')
page()

heading(7,'Evidence, remaining work and reproducibility')
p('<b>For the SRR,</b> the team should carry the trade between dose and shielding mass, an assured route for the critical electronics, an allowance for recovery and a bounded sensor response into the coupled calculation of payload, coverage and sample yield. The study should keep one primary observable and select the least demanding performance that still gives useful samples and added value.')
p('<b>Before a mission baseline,</b> the team must choose the orbit, lifetime and epoch, replace the transfer allowance, map the shielding paths and evaluate the SEP confidence for the actual duration. It must also obtain radiation evidence that applies to the chosen sensor and assembly, and propagate degradation, false confirmation and recovery into the selected science metric. A future flight programme would need appropriate assurance at component and assembly level. The educational report may use literature and first-principles bounds without a new irradiation campaign.')
table(['Evidence / assumption','Status'],[
 ['Published dose and LET curves','The RAD01 figures were read and digitized and the source confidence was retained. The input files and exact model versions are not available.'],
 ['Lunar measurements and event-camera data','RAD02-07 separate actual measurements, different devices and different test conditions. The McMahon author full text was accessible, but the PDF download returned error 403. No qualification of the IMX636 was found.'],
 ['Calculations executed','Raster digitization, unit conversion, body geometry, mass, incidence screening, and duration and availability arithmetic, together with live workbook formulas and independent checks.'],
 ['Not executed','SPENVIS, IRENE, CREME, FASTRAD, OMERE, Geant4, irradiation tests, a simulation of the selected sensor or a reliability model of the complete spacecraft.'],
 ['Open quantitative gaps','The exact dose for 400 km / 51.6° and 600 km / 98°, displacement damage for the selected trajectory, component rates, the conversion from particles to false flashes, solar-array loss, and the actual charging and transfer.']
 ],[1.3,3.6])
p('Selected source locations','HeadX')
selected=['RAD01','RAD02','RAD04','RAD05','RAD06','RAD07','RAD08','RAD09','RAD12','RAD13','RAD14','RAD15']
for e in S['evidence']:
    if e['id'] in selected:
        # Short source names make the reference list readable on one page.
        title=e['title'].split(',')[0]
        p(f"<b>{e['id']}</b> {escape(title)}. {escape(e['location'][:125])}. <link href='{escape(e['url'])}' color='#294C72'>Source</link>.",'Small')
p('The full findings, the evidence workbook, the CSV and JSON inputs and calculations, the source access log and the figure files accompany this report. This supporting report is seven A4 pages and does not enlarge the inclusive working budget of 50 pages for the final mission report.','Small')

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#C4CFDA'));canvas.line(44,43,A4[0]-44,43)
    canvas.setFont('Report',7.5);canvas.setFillColor(colors.HexColor('#52667A'))
    canvas.drawString(44,30,'SMD radiation environment | 29 October 2026 | Provisional concept study')
    canvas.drawRightString(A4[0]-44,30,str(doc.page))
doc=SimpleDocTemplate(str(OUT/'lunar_radiation_environment_report.pdf'),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=38,bottomMargin=54,
                      title='Lunar radiation environment for the SMD event-camera concept',author='SMD concept research')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Built lunar_radiation_environment_report.pdf')
