"""Reviewed claims. Facts retain source, location, design epoch and evidence status.

This is a curated research input, not an automatic scrape or flight database.
"""
import csv, json
from readable import text
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/lumio_comparison'
DATE='2026-10-29'

# id, title, publication/event date, configuration epoch, location, evidence, URL, limitation
sources=[
['L01','ESA: Phase C officially launched','2026-03-27','March 2026 Phase C','In brief; What is next; What is on board','Dated agency status','https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Shaping_the_Future/A_leap_forward_for_Lumio_Phase_C_officially_launched','Potential 2028 launch and 2027 CDR are targets; no final budgets'],
['L02','ESA: LUMIO mission profile','Undated, accessed 2026-10-29','Mixed: operations concept and older status','Mission description; phases; mission status','Agency mission profile','https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Technology_CubeSats/LUMIO','28-day cycle is approximate; Phase C March 2025 conflicts with dated records'],
['L03','ASI: LUMIO mission page','Undated, accessed 2026-10-29','Phase C public summary','Form factor; status; team','National agency status','https://www.asi.it/en/technologies-and-engineering/micro-and-nanosatellites/esa-gstp-fly-program/lumio/','16U conflicts with ESA/prime 12U; page does not document a change decision'],
['L04','Polimi: LUMIO Phase C project','2026-03-02 to 2027-09-30 project interval','Phase C','Start/End; project description','Prime project record','https://www.aero.polimi.it/en/research-projects/esa-lumio-lunar-meteoroid-impacts-observer--phase-c','Project end is not science operations end; Delta PDR May 2025'],
['L05','Topputo et al.: Current status and lessons learnt','4S Symposium 2024; repository bibliographic year 2025','Phase B / pre-Phase C','pp5-14, Tables 3-1 to 6-4; sections 3-6','Mission-author design and requirements','https://re.public.polimi.it/bitstream/11311/1266785/1/TOPPF01-24.pdf','Web PDF text inspected, local PDF HTTP403; internal budget inconsistencies retained'],
['L06','Pancalli et al.: Payload design for lunar meteoroids impact detection','IAC 14-18 October 2024','Consolidated Phase B payload','pp2-6 Tables1-5; sections 3-6','Payload developer design and analysis','https://re.public.polimi.it/retrieve/f609816c-3cf5-4468-93bc-12ee09e38135/PANCM01-24.pdf','Web PDF text inspected; local HTTP403; design values exclude manufacturing/alignment error'],
['L07','Topputo and LUMIO team: Phase B design','ASI workshop 2-4 July 2024','Phase B / Delta B roadmap','slides5-11','Mission-team presentation','https://www.asi.it/wp-content/uploads/2024/07/04.07_2_5_PoliMi.pdf','Slide-level rounded numbers; dated roadmap superseded'],
['L08','ESA: CubeSats for hunting secrets in lunar darkness','2018-01-23','LUCE challenge winners','Challenge and lunar impact detector sections','Programme rationale','https://www.esa.int/Enabling_Support/Space_Engineering_Technology/CubeSats_for_hunting_secrets_in_lunar_darkness','Concept announcement, not approved flight performance'],
['L12','Ferrari et al.: ESA LUMIO mission, EPSC-DPS2025-1514','2025; abstract updated 2025-07-09','Post-Phase B science plan','Abstract and mission overview','Mission-author science conference abstract','https://doi.org/10.5194/epsc-dps2025-1514','Potential Apophis 2029 observations are a study opportunity, not guaranteed operations'],
['L13','Polimi: LUMIO consolidation review','Published 2026-06-26; meeting 10-11 June 2026','Phase C','Review description','Prime milestone report','https://www.aero.polimi.it/en/magazine/lumio-consolidation-review','Reports consolidation, not final CDR or flight qualification'],
['L14','Polimi: annual ESA LUMIO science meeting','Published 2026-07-29; meeting 16-17 July 2026','Phase C','Meeting report and working groups','Prime science status','https://www.aero.polimi.it/en/magazine/daer-hosts-the-annual-esa-lumio-science-team-meeting','Science partnerships do not establish payload performance'],
['L15','Argotec: LUMIO','Undated, accessed 2026-10-29','Platform public summary','Mission and processing description','Platform provider mission page','https://www.argotecgroup.com/missions/lumio','12U; lunar-orbit transfer wording differs from WSB baseline; page is not configuration controlled'],
['L17','Cervone et al.: LUMIO spacecraft design','2022, Acta Astronautica 195,309-317','Phase A, completed 2021','pp311-317; Tables1-3; sections3-4','Mission-author design evolution','https://doi.org/10.1016/j.actaastro.2022.03.032','Supplied full PDF; Phase A options cannot be treated as Phase C selections'],
['L18','Topputo et al.: Meteoroids detection with LUMIO','2023 issue; DOI 2022','Phase A model, assumed 2024-2025 operations','pp3-5,10-18; Tables1-4,8-9; sections5-6','Published radiometry and Monte Carlo prediction','https://doi.org/10.1016/j.icarus.2022.115213','Supplied full PDF; 1000 scenarios do not encompass environment/flash-model systematic uncertainty'],
['L19','Walker, Vennekens et al.: LUCE mission concept studies','Workshop 2017-05-30; footer 2017-05-04','Original LUCE programme','slides3-6','Original ESA programme constraints','https://icubesat.org/wp-content/uploads/2017/05/2017-a-1-2-20170530-luce.pdf','Programme presentation, not complete signed call; strict less-than signs as printed'],
['L20','Cipriano et al.: Orbit design for LUMIO','2018-09-19','Phase 0','sections2.1,3.1-3.3; Tables7,11-12','Published numerical acceptance criteria and orbit trade','https://doi.org/10.3389/fspas.2018.00029','Criteria and risk acceptance are historical; no controlled current minimum/full success definition'],
['L21','Panicucci et al.: Vision-based navigation for LUMIO','AAS 24-152, 2024','Post-PDR navigation experiment','pp2-3; p8 Table1; simulation results','Mission-author navigation simulation','https://re.public.polimi.it/bitstream/11311/1260531/1/PANIP01-24.pdf','Web full text accessible; simulations and assumed error budget, not flown autonomous navigation'],
['L22','Giancono et al.: High-speed observations of lunar impact flashes','2026-05-29 journal; author v1 2026-06-05','Observed 200/250 fps ground comparator','sections II-V; Table II; Figs5-6','Observed light curves, four events','https://arxiv.org/html/2606.07177v1','Small selected sample, two saturated; timing cadence is not universal faint-flash calibrated bandwidth'],
['L23','Liakos et al.: NELIOTA after 6.5 years','2024, A&A687 A14; author v1 2024-03-28','Observations 2017-August2023','sections2,4,6-8; Table2','Observed two-band survey','https://arxiv.org/html/2403.19613v1','192-event snapshot, not current archive count or intrinsic complete population'],
]

# claim id, subsystem/area, parameter, value/architecture, units, conditions,
# epoch, evidence status, source, exact location, confidence, public gap
claims=[]
def claim(area,param,value,unit,condition,epoch,source,location,gap='',status='Published design',confidence='High for this epoch'):
    claims.append([f'LC{len(claims)+1:03}',area,param,value,unit,condition,epoch,status,source,location,confidence,gap])

claim('Mission','Primary science question','Spatial and temporal distribution of lunar meteoroid impacts','qualitative','Flash observations constrain cislunar meteoroid models','Phase A','L17','p311 section2','No guaranteed flux precision')
claim('Mission','Science products','Flux, magnitudes, luminous energies, inferred sizes and surface locations','catalogue','Two-band confirmation and equivalent blackbody temperature','2023-2026','L02,L18','L02 objectives; L18 pp3-4','Kinetic energy/mass need luminous-efficiency, speed and emission assumptions',status='Stated objectives')
claim('Mission','Demonstration','Autonomous optical navigation, trajectory control, miniaturized payload/propulsion and onboard processing','qualitative','Science plus technology demonstration under GSTP Fly','2023-2026','L02,L18','L18 Tables1-3 p3; L02 objectives','Optical navigation is experiment alongside nominal radio navigation',status='Stated objectives')
claim('Mission Analysis','Orbit','Earth-Moon L2 quasi-periodic halo; Cj=3.09','dimensionless seed Cj','CRTBP seed refined in ephemeris model; not a Keplerian lunar altitude orbit','Phase 0/B','L05,L20','L05 section4.1 p7; L20 section3.3.4','No final Phase C state vector/kernel released in reviewed evidence')
claim('Mission Analysis','Moon and Earth range','Moon 36000-86000; Earth 380000-470000','km centre distance','Published reference trajectory for 21 March 2024-21 March 2025','Phase A radiometry','L18','section2.2 p4; Fig5 p5','2026 ESA rounds vantage to 40000-80000 km; not a new exact orbit')
claim('Mission Analysis','Period and operations cycle','About 14-day halo motion; about half a synodic month science','days','Quasi-periodic motion; the cycle is an approximation, not an exact resonance','Phase 0/B','L20,L21','L20 section3.3.3; L21 p2','Do not equate 28-day shorthand with 29.53-day synodic month')
claim('Mission Analysis','WSB reference transfer','Release 0.5 d after TLI; baseline DSMs near apogee then halo insertion','sequence','2027 week20 case: DSM4 at44.85d, approximately50d more to halo; up to8 DSMs','2024 Phase B','L05','section4.2 pp7-8','Study case, not booked 2027 carrier; carrier Layer1 delta-v excluded from CubeSat')
claim('Mission Analysis','Transfer delta-v budget',79.05,'m/s','LUMIO Layer2 incl transfer, stochastic corrections,1y stationkeeping,disposal and stated margins','2024 Phase B','L05','Table4-1 p8','Do not mix with 201.8m/s Phase A Artemis2 scenario')
claim('Mission Analysis','Stationkeeping','Mean8.256; published 3-sigma15.79','m/s per year','Target points method;2-day cutoff; injection/tracking/execution errors','2024 Phase B','L05','section4.3 p8','Published Monte Carlo; study not rerun here; not universally stable/maintenance-free',status='Published calculation')
claim('Operations','Nominal operations',1,'year','Science and navigation/engineering cycles alternate','2026 profile','L02','Operations phase','Not one year of continuous science; extension not approved publicly',status='Stated operations plan')
claim('Operations','Design life',1.5,'year','More than1y lunar environment; transfer/commissioning allowance','2024 Phase B','L07','slide8','No reason established for exactly1y versus alternatives; no validated end-of-life reliability')
claim('Operations','Commissioning plus transfer','About150','days','Navigation paper example; differs from roughly95d selected trajectory example','2024 post-PDR','L21','p2 mission timeline','Mission cases differ; not final booked transfer time')
claim('Structure','Form factor','12U /12UXL ESA and prime versus16U ASI','CubeSat units','Agency pages conflict on29 October2026','2026 public','L01,L02,L03,L15','L01 overview; L02 platform; L03 form factor','Unresolved; no confirmed redesign history',status='Conflicting public claims',confidence='High that conflict exists')
claim('Structure','Total mass','About30','kg','ESA dated overview, no dry/wet/margin convention supplied','March2026','L01','What will LUMIO do','Do not insert into historical budget as a controlled mass')
claim('Structure','Mass budget','23.41 dry subtotal;2.34 system margin;1.17 harness;1.77 propellant;28.69 total','kg','Table6-3; printed rounded line items sum to28.69','2024 Phase B','L05','p14 Table6-3','28kg SYS-01 and payload mass lines conflict internally; no final compliant mass proven')
claim('Structure','Primary/secondary structure','Custom Argotec Al7075 T7351; lateral protrusions; rails/frames/ribs and radiator panels','material/layout','Not fully compliant with ordinary12U envelope','2024 Phase B','L05','section6.5 p13','No final stowed/deployed dimension or launcher load qualification in reviewed sources')
claim('Payload','Aperture/focal length/FOV','50.8;127;6 total','mm;mm;deg','f/2.5, seven-lens Phase B optical layout, two orthogonal focal planes','October2024','L06','Table3 p3','No measured 2026 throughput/PSF or end-to-end faint-flash detection curve')
claim('Payload','Detectors','Two Teledyne e2v CCD201-20 EMCCD,1024x1024,13um square','pixels/pitch','Full-frame synchronized acquisition; multiplication gain variable','October2024','L06','p2 Table2','Not an event camera; older sources round pitch13.3um')
claim('Payload','Channels','VIS450-800;NIR850-950','nm','Phase B passbands;800-850 transition/gap retained','October2024','L06','p2 Table1','2023 model uses ideal820nm split; cannot blend photon budgets')
claim('Payload','Exposure','Approximately78 minimum full-frame;13fps','ms;fps','1024x1024 full matrix; interchannel sync negligible relative to exposure, no absolute timing bound','October2024','L06','p2 section3 and Table2','Earlier15fps/66ms model not supersession-proof for Phase C flight mode')
claim('Payload','Optics transmission','VIS78%;NIR84%','fraction','Design optics only, including30krad load on first two lenses; excludes manufacturing/alignment errors','October2024','L06','p3 Table3 and glass discussion','Not total photon detection efficiency or qualified camera dose')
claim('Payload','Baffle/version','150 Phase A;100 on July2024 slide','mm','Out-of-field solar straylight;2023 model Sun exclusion20deg','2023/July2024','L18,L07','L18 p5 Table4; L07 slide5','October2024 design does not establish same final baffle length')
claim('Payload','Mass and power detail','3.12 unmargined/3.85 margined;27.8 worst-case incl heaters','kg;W','2x3W heaters,75% DC/DC efficiency,15MHz detector','4S2024 payload budget','L05','p6 Table3-3 and section3.5','System table uses4/4.8kg and19W; do not assume these are reconciled')
claim('Thermal Control System','Camera thermal performance','Optics14-26;detectors0-10','degC','Performance ranges, distinct from all-camera operation -20 to40 and survival -30 to50','October2024','L06','p6 Table5; p3 Table3','Broad platform limits do not guarantee radiometric performance')
claim('Thermal Control System','Thermal architecture','Heaters,thermistors,detector straps to spacecraft radiator;active barrel stabilization','architecture','Titanium barrel,Al6082 baffle,isostatic/bipod mounting','October2024','L06','pp3-6 sections electrical/thermomechanical','Steady hot/cold design analysis;hot cases still require optimization; no hardware qualification claimed')
claim('Power Subsystem','Arrays/drive','Two deployable arrays,IMT microSADA,thermal-cutter release,slip ring','architecture','Solar tracking while camera points Moon;three foils per array','2024 Phase B','L05,L07','L05 section6.3 pp12-13; L07 slides8-9','Panel area and final end-of-life generation not established here')
claim('Power Subsystem','Generation and modes','~110 generation;98.76 max available in mode table;88.94 margined science','W','Different source conventions;192.27 maneuver and186.49 desaturation draw on storage','2024 Phase B','L05,L07','L05 Table6-4 p14; L07 slide8','No complete pulse duration/battery SOC analysis; printed power-margin row does not reconcile by subtraction')
claim('Power Subsystem','Battery/PCDU','ABSL124Wh7S2P Li-ion;~28V;reworked Argotec Volta','Wh;V','MPPT,BCR,protected rails,retriggerable current limiters','2024 Phase B','L05','section6.3 pp12-13','124Wh nameplate is not usable energy; heritage of parts not LUMIO flight proof')
claim('Propulsion','Main system','LMP-103S/helium blowdown;one ECAPS1N HPGP engine','N / propellant','Bradford Phase B;LMO detailed development Phase C/D','2024 Phase B','L05','section6.1 pp10-11','Change of propulsion triggered DeltaPDR;final Phase C Isp/tank/propellant budget not confirmed')
claim('Propulsion','Reaction control','R134a two-phase cold-gas system,four thrusters','architecture','Vaporizer/vapor tank;wheel unloading and main-thrust torque compensation','2024 Phase B','L05','section6.1 p11','Requirement110Ns vs text170s total impulse is inconsistent;unit/capability unresolved')
claim('Propulsion','Current provider roles','LMO propulsion/RCS;ECAPS main thruster','architecture','Dated ESA partnership confirms roles','March2026','L01','What is on board','Does not confirm every2024 propulsion number or a measured delivered system')
claim('Telecommunication Subsystem','Link/radio','Direct-to-Earth X-band;IMT C-DST;two patch antennas','architecture','TC,science downlink,ranging and tracking;one station to limit cost,more possible','2024 Phase B','L05','section6.4 p13','Station booking,data rate,link margin and latency service not established as current')
claim('Telecommunication Subsystem','RF output',2,'W','Mission-team technology slide,not total electrical demand','July2024','L07','slide9','Historical Phase A0.5-2kbit/s is not confirmed Phase C rate')
claim('Attitude Determination and Control Subsystem','Sensors/controller','BCT XACT-100,two star trackers,Sun sensors,gyroscopes','architecture','Second external star tracker mitigates a single-point failure','2024 Phase B','L05','section6.2 pp11-12','No chosen SMD ADCS;predicted pointing not localization')
claim('Attitude Determination and Control Subsystem','Wheel storage','Three RWp100 at100mNms;one tilted RWp050 at50mNms','mN m s','Body-axis triple plus tilted wheel to fit available volume;RCS unloading','2024 Phase B','L05','section6.2 pp11-12','Storage capacity is not torque;no closed-loop event-image motion test run')
claim('Attitude Determination and Control Subsystem','Pointing requirements','APE<0.18deg half-cone;RPE<5arcsec over66.7ms;max slew0.5deg/s','mixed','Table6-1 published requirements','2024 Phase B','L05','p10 Table6-1','Control error,knowledge,alignment and surface error differ;no confidence on APE stated',status='Published requirement')
claim('On-board Data Handling','Platform computer','Reworked Argotec Fermi CPU/FPGA,CAN transceiver,MRAM boot','architecture','Radiation-hardened CPU/FPGA hybrid','2024 Phase B','L05','section6.6 p13','Exact flight CPU,FPGA,memory capacities,software qualification not established')
claim('On-board Data Handling','Science reduction','Detect/confirm in two channels;save50x50tiles,5 frames,event,2channels,16bit/pixel','pixels/encoding','2023 scientific product assumption;onboard selection,S&T payload processing','Phase A/2026 roles','L18,L01','L18 section2.3 p4; L01 team','0.4Mbit per event before overhead/compression;burst loss and rejection efficiency unknown')
claim('On-board Data Handling','Published annual volume',15,'Gbit','Approximate science product prediction for1year under2023 yield assumptions','Phase A model','L18','p4 section2.3','Not a final data-volume cap or real-time alert requirement')
claim('Navigation','Nominal and experimental navigation','Ground radiometric DTE nominal;limb-based optical experiment and EKF','architecture','Simulation0.2pixel limb precision;J2000 Earth-Moon barycentric filter','2024/2026','L05,L21,L02','L05 section5 pp8-10; L21 pp4-8; L02 operations','Optical line-of-sight depth less accurate;not a1km surface-localization guarantee')
claim('Ground Segment and Operations','Coordination','Polimi prime/science/optical-nav;Nautilus flight dynamics;ground design under consolidation','roles','Current roles from ESA;historic paper assigns ground/ops to Nautilus','2024/2026','L01,L21','L01 Phase C activities; L21 p2','Final sites,staffing,cost,availability and delivered products schedule not public here')
claim('Launch and Deployment','Launch opportunity','Potential2028;WSB piggyback or lunar delivery alternatives','year/architecture','2026 ESA date;2024 cases are trade inputs','March2026','L01,L02','L01 In brief; L02 mission status','No selected launch contract/precise insertion state established',status='Planned activity')
claim('Operations','End of life','Targeted lunar impact after decommissioning','architecture','Current ESA compliance statement;older papers contemplated heliocentric disposal','2024/2026','L02,L05','L02 end-of-life phase; L05 section4 p6','No final target date/location or complete disposal assurance established')

# Published numerical criteria are paraphrased, not verbatim quotations.
# id, metric, value, unit, epoch/status, source, location, interpretation
criteria=[
['EC.A.01','Earth-equivalent kinetic-energy envelope','1e-6 to1e-1','kton TNT','2018 orbit acceptance','L20','section2.1','Not band-limited emitted optical energy'],
['EC.A.02','Total detectable impacts',240,'count minimum','2018 orbit acceptance','L20','section2.1','Reference sample scale linked to Suggs2014;not verified Phase C threshold'],
['EC.A.03','High-energy detectable impacts',2,'count minimum','2018 orbit acceptance','L20','section2.1','Earth-equivalent1e-4 to1e-1ktonTNT'],
['EC.A.04','Lower-energy detectable impacts',100,'count minimum','2018 orbit acceptance','L20','section2.1','Earth-equivalent1e-6 to1e-4ktonTNT'],
['EC.A.05','Night-farside monitoring','Required','qualitative','2018 orbit acceptance','L20','section2.1','Not whole-surface independent coverage'],
['EC.A.06/07','Minimum life / total delta-v','>=1 / <=200','year / m/s','2018 orbit acceptance','L20','section2.1','Includes access;historical24kg constraint'],
['EC.S.01-03','Trade goals','Maximize count and full-disc time;minimize delta-v','qualitative','2018 selection criteria','L20','section2.1','Trade goals rather than separate numerical success gates'],
['SYS-01/02/03','Mass / volume / lunar life','<=28 /12U />=1','kg / unit / year','2024 published system requirements','L05','Table6-1 p10','28.69kg printed budget conflicts;current mass about30kg'],
['PLD.001/002','Detection envelope','1e-6 to1e-4;450-950','ktonTNT;nm','2024 published payload requirements','L05','Table3-1 p5','Energy kind insufficiently explicit in table;do not label as optical energy'],
['PLD.003','Integration time','>=30','ms','2024 published payload requirement','L05','Table3-1 p5','At least sign retained;not <=30ms temporal resolution'],
['PLD.004-006','Payload allocation','<=4.5 / <=20 /10x10x30','kg / W / cm','2024 published payload requirements','L05','Table3-1 p5','27.8W worst-case vs20W allocation;requires reconciliation'],
['PLDP-01/02','Payload processing','>=15 / >5','images/s / dB','2024 published requirements','L05','Table6-1 p10','Processing capacity not achieved cadence;dB convention must be reconciled with2023 radiometry'],
['ADCS-01/02','Moon-pointing control','<0.18 / <5 over66.7','deg half-cone / arcsec over ms','2024 published requirements','L05','Table6-1 p10','Not boresight calibration or surface-location confidence'],
['COM-01/02/03','Command/telemetry coverage and radio navigation','>95% orientation /1','fraction / km3sigma','2024 published requirements','L05','Table6-1 p10','Not a95% science availability requirement'],
['PROP-01/04','Propulsion and RCS allocation','>=80 /110','m/s / Ns','2024 published requirements','L05','Table6-1 p10','RCS narrative170s unit inconsistent;not a confirmed110Ns capability'],
['CURRENT-GAP','Minimum/full success definitions','Not established','public gap','As of29October2026','L01,L02,L03','Status and objectives','Reviewed sources do not publish current controlled pass/fail matrix or formal minimum/full success taxonomy'],
]

timeline=[
['2016-2017','LUCE programme','Small autonomous lunar payloads;12U/24kg-class constraints,relay architecture','L19','slides3-6','Call heritage,not present SMD constraint'],
['2018','Phase0/CDF','12U;single CCD grows to two-channel camera;reliability added;L2 trade','L08,L17,L20','L17 Table2 pp313-315;L20 section3','Original~21kg versusCDF22.8kg'],
['2020-2021;published2022','Phase A','28.69kg margined;119.5m/s CLPS versus201.8m/s Artemis2 cases','L17','pp312-316 Tables1-3','Flight opportunity unselected'],
['2023 issue','Radiometry/POE model','15fps/66ms,820nm ideal split;37000detections/year model','L18','Tables4,8-9','AssumedMarch2024-March2025 observation dates,not a flown year'],
['December2023','PDR completed','PhaseB review milestone','L04','Project description','Later confirmed by prime'],
['May/July2024;repository2025','PhaseB design','79.05m/s WSB case;124Wh;XACT100;Fermi/Volta;~110W generation','L05,L07','L05 sections4-6;L07 slides8-9','Design targets,not hardware validation'],
['October2024','Consolidated payload','78ms/13fps full-frame;450-800/850-950nm;seven lenses','L06','pp2-3 Tables1-3','More detailed payload source than early2024 summaries'],
['May2025','DeltaPDR','Prime records completed DeltaPDR inMay2025','L04','Project description','ESA undated profile had plannedFeb2025'],
['2025','Science plan','Launchforeseen2028;Apophis2029opportunity studied','L12','Mission overview','Does not approve extended life or guarantee encounter data'],
['March2026','PhaseC kickoff','Prime project begins2March;ESA announcement27March;CDR2027,targetlaunch2028','L01,L04','Dated announcement;project interval','Supersedes profileMarch2025 kickoff as most credible dated status'],
['10-11June2026','Consolidationreview','Architecture and design maturity reviewed','L13','Review report published26June','No final public configuration budget supplied'],
['16-17July2026','Science teammeeting','Platform,camera,processing,ground progress discussed','L14','Published29July','ContinuesPhaseC;no flight demonstration'],
]
conflicts=[
['CF01','Size','ESA12U/12UXL vs ASI16U','L01,L02,L03,L15','Unresolved','Do not call16U a proven redesign or derive a current envelope'],
['CF02','PhaseC/launch','ProfileMarch2025/2027+ vs datedMarch2026/potential2028','L01,L02,L04,L12','Dated2026status preferred','Future launch is a target;CDR2027 does not imply launch2027'],
['CF03','DeltaPDR','ProfileFeb2025 planned vs primeMay2025 completed','L02,L04','Record both,prefer completion record','Propulsion change occurred in study,details not fully public'],
['CF04','Payload cadence','66ms/15fps model vs78ms/13fps consolidated full-frame','L18,L06,L07','Version-specific;current flight mode unknown','Useboth inSMD sensitivity;do not overwrite model assumptions'],
['CF05','Spectral/optical layout','820nm split/five lenses vs450-800+850-950nm/seven lenses','L18,L05,L06','UseOct2024 forpayload design','OlderMonteCarlo not recomputed fornewbandpass'],
['CF06','Transfer/propulsion','Lunarparking+UHF relay vsWSB+DTE;154/202m/s vs79m/s','L17,L20,L05,L02','Distinct cases/epochs','CarrierTLIcost doesnotbelong toCubeSatdelta-v'],
['CF07','Mass','SYS<=28kg vsbudget28.69kg;ESAabout30kg','L05,L01','Not publicly reconciled','Table6-3dry/propellant/margin conventions preserved'],
['CF08','Payload power/mass','20Wallocation/19Wsystem vs27.8Wworstcase;3.85vs4.8kgmargined','L05,L07','Internal scope/rounding/configuration ambiguity','Do not invent a compliant finalbudget'],
['CF09','EPS','53.8Waverage/68Wpeak requirement vs89Wscience/192Wmaneuver;98.76Wtable vs~110Wslide','L05,L07','Requirements vsmode/design conventions unresolved','Battery can supply transients,not proof of energyclosure;printedmargin row inconsistent'],
['CF10','RCS','110Nsrequirement vs170s totalimpulse narrative','L05','Source unit/value error unresolved','No silent170Ns correction or finalcapability claim'],
['CF11','Life/operations','1yoperations;1.5ydesign;~95dselected vs~150dtransfer timeline','L02,L05,L07,L21','Different definitions and transfer cases','Not a selected flight schedule or guaranteed extension'],
['CF12','Yield','2018~4200/5500 vs2023~37000;Geminidstext>250 vsconclusion>6000/day','L20,L18','Model dependence andinternal peak-rate conflict','UseTable9annualmodel only;do not baseline shower peak'],
['CF13','Disposal','Earlierheliocentricescape vs2024/2026lunarimpact','L17,L02,L05','Laterplanpreferslunarimpact','Disposal cost/standard areepoch-specific'],
]

# driver, LUMIO comparator, SMD status, consequential comparison, next evidence, source
comparison=[
['D01','50.8mm;two-band EMCCD;published noise/straylight model','1000J detection fixture,600-900nm at50000km is provisional','No matched sensitivity ranking;kinetic/optical energy andbandpass differ','Use a common incident spectral light curve,range,PSF/background, jointconfirmation andPd/false rate','L06,L18'],
['D02','66ms model;78ms minimum full-frame PhaseB','1ms/10000J or5ms/3000J candidates;calibratedsensorbandwidth unknown','Earlyshape information may improve;modern ground already4-5ms','Recover first5msenergyfraction andrise/decay across onsetphase;bound response/latency/loss','L06,L18,L22'],
['D03','Two synchronizedbands;opticalenergy,temperature intent;no current public accuracy budget','10%energy,20%binnedpeak,5%bias candidates','Fine time samples cannot guarantee absolute photometry or unique mass','Choose minimum radiometric reference;propagate spectral/background/calibration andmissing-tail covariance','L06,L18,L23'],
['D04','About21arcsec/pixel;APE/RPE published separately','5kmterrain or1kmcrater95%ellipse candidates','Sampling is not localization;no comparable current LUMIO95%surfaceellipse found','Ray/DEM propagation withboresight,attitudeknowledge,orbit,clock andlimb/poles','L05,L06'],
['D05','Farside full-disc geometry;darksciencepart oflunation;groundcomplement','EntireMooninclbothhemispheres/polesfixed;architectureTBR','One L2observer doesnotdemonstrate independent whole-surface exposure','Time-resolvedsurfacearea-energydependentexposure;resolvecooperative allocation A2 fromproposal','L02,L18,L20'],
['D06','Historical>=240criteria;~37000model detections,notusefulfastlightcurves','PrimaryobservableandsampleTBR','Detectionyield isnot characterizationyield;smallPoissonerror excludesmodelsystematics','JointD01-D04recovery;pilot populationvariance;atleast~100independentusefulevents fortrial10%meanprecision ifCV=1','L18,L20,L22'],
['D07','Dualchannelspatial/temporalcoincidence,tiles retained','Falsecandidate/confirmedfalse/eventlossTBR','Two channels help particle rejection;publiccompletechainfalse rate notestablished','Modelparticles/hotpixels/glints/motion;blindinjectionsandretainedpre/posthistory','L06,L18'],
['D08','450-800/850-950nmPhaseB;thermalperformance ranges;20degSunangleoldmodel','600-900nmfixture;dynamicrange/backgroundenvelopeTBR','A gapandtemperaturedependence change photons andusableprofiles','Sensitivitygridinspectrum,background,temperature,energy,durationandlocation','L06,L18'],
['D09','1yoperations;1.5ydesign;maintainedhalo,DTE,powerandpropulsiondependencies','Lifetimeandavailabilityunselected','Needmissionusefulsampleswithoutages/degradation;no100%scienceavailabilityclaim','Coupletransfer/shielding,maintenance/unloading,SOCandend-of-lifesensorresponse','L02,L05,L07'],
['D10','Batchdownlinknextengineeringcycle;historical15Gbit/year;Xband','Noalertserviceorlatencyrequirementselected','Publishedspacecraft isnotarealtimehazardwarningbenchmark','Sizebursts,bufferandcontacts;selectminimumcataloguedeliverylatencyneededbyprimaryscience','L05,L18'],
]

decisions=[
['C01','Use versioned LUMIO comparator','2024 payload design plus2026 status;retainolder model separately','L01,L05,L06','Do not claim a final current configuration'],
['C02','Prioritize calibrated early-to-total flash energy as one hypothesis','Trial first5msfraction plus tailintegral,not timestamp tick or temperature ascoequal goal','L22,L06','Hypothesis only;no SMD capability established'],
['C03','Close useful sample yield before tightening faint limit','Targetusefulcount depends onvariance,classification,recoveryandregionalexposure','L18,L20','100events for10%meanprecision only ifCV=1 andbiascontrolled'],
['C04','Treat full-disc and whole-surface as separate requirements','LUMIOplusgroundglobalinformation doesnotproveSMDwhole-surfacecompliance','L02,L20','Maintainbothhemispheresandpolarsurfaceconstraint'],
['C05','Size platform from payload and mission interfaces','LUMIO12Uheritageisprogramme-driven;customoptics,propulsion,SADAandprocessingneeded','L19,L05,L06','SMDnotrestrictedtoCubeSat;noquantifiedcostsuperiorityestablished'],
['C06','Carry coupled budgets and engineering cycles','ArraysmusttrackSun,imagingpointsMoon,DTE/maintenanceunloadinguseoperations','L05,L07','Do notpaste componentnumbers withoutmode/durationclosure'],
['C07','Compare at credible delivery date','PotentialLUMIO2028andobserved2026highspeedgroundarebaselinesforlaterSMDresults','L01,L22','RefreshcompetitorperformancebeforeSRRbaseline;noapprovedSMDlaunchdate'],
]

# Reader-facing wording for the comparison and unresolved configuration issues.
comparison=[
['D01','50.8 mm, two-band EMCCD; published noise and straylight model','1000 J detection fixture in 600-900 nm at 50000 km remains provisional','No matched sensitivity ranking; kinetic/optical energy and passbands differ','Common incident spectral light curve, range, PSF, background, confirmation rule and detection probability','L06,L18'],
['D02','66 ms model; 78 ms full-frame Phase B integration','1 ms at 10000 J or 5 ms at 3000 J candidates; sensor bandwidth unknown','Early shape information may improve; modern ground already demonstrates 4-5 ms cadence','Recover first-5-ms energy fraction, rise/decay and onset phase; bound latency and event loss','L06,L18,L22'],
['D03','Synchronized bands; energy and temperature objectives; public current accuracy budget missing','10% energy, 20% binned peak and 5% bias candidates','Fine time samples alone do not establish absolute photometry or unique mass','Minimum radiometric reference; spectral, background, calibration and missing-tail covariance','L06,L18,L23'],
['D04','About 21 arcsec/pixel; separate pointing control requirements','5 km terrain or 1 km crater-search 95% ellipse candidates','Sampling differs from localization; no current LUMIO 95% surface ellipse found','Ray/DEM uncertainty propagation with boresight, attitude knowledge, orbit, timing and limb/poles','L05,L06'],
['D05','Farside full-disc geometry; dark science windows; ground complement','Entire Moon including both hemispheres and poles is fixed; architecture TBR','One L2 observer does not demonstrate independent whole-surface exposure','Time-resolved, energy-dependent surface exposure; resolve cooperative allocation A2 from proposal','L02,L18,L20'],
['D06','Historical minimum 240; about 37000 predicted annual detections','Primary observable and useful sample count TBR','Detection yield differs from characterization yield; model uncertainty exceeds counting error','Joint D01-D04 recovery and population variance; trial 100 useful events for 10% mean precision if CV=1','L18,L20,L22'],
['D07','Two-channel coincidence and retained image tiles','False candidates, confirmed false flashes and event loss TBR','Two channels help particle rejection; complete-chain false rate not established','Particles, hot pixels, glints and motion; blind recovery and retained pre/post history','L06,L18'],
['D08','Phase B 450-800 / 850-950 nm and defined thermal performance ranges','600-900 nm fixture; dynamic range and background envelope TBR','Spectral gap and temperature change photons and usable profiles','Response grid in spectrum, background, temperature, energy, duration and position','L06,L18'],
['D09','One-year operations, 1.5-year design life, maintained halo','Lifetime and availability unselected','Useful samples depend on outages, degradation and maintenance','Transfer/shielding, unloading, state of charge and end-of-life sensor response','L02,L05,L07'],
['D10','Batch downlink in engineering cycles; historical 15 Gbit/year; X-band','No alert service or latency selected','LUMIO is not a demonstrated real-time hazard warning service','Burst traffic, buffering and contacts; choose latency needed by primary science','L05,L18'],
]
conflicts=[
['CF01','Size','ESA 12U/12UXL versus ASI 16U','L01,L02,L03,L15','Unresolved','No proven redesign or current physical envelope'],
['CF02','Phase C / launch','Profile March 2025 / 2027+ versus dated March 2026 / potential 2028','L01,L02,L04,L12','Prefer dated 2026 status','Future launch target; CDR 2027 does not imply launch 2027'],
['CF03','Delta PDR','Profile planned February 2025 versus prime completed May 2025','L02,L04','Prefer completion record','Propulsion change prompted review; final details remain incomplete'],
['CF04','Cadence','66 ms / 15 fps model versus 78 ms / 13 fps full frame','L18,L06,L07','Version-specific','Use both in sensitivity; current flight mode unknown'],
['CF05','Passband / optics','Ideal 820 nm split and five lenses versus updated bands and seven lenses','L18,L05,L06','Use October 2024 payload design','Old yield model not recomputed for updated response'],
['CF06','Transfer / propulsion','Lunar parking and relay versus WSB and DTE; 154/202 versus 79 m/s','L17,L20,L05,L02','Different epochs and cases','Carrier TLI cost is separate from CubeSat delta-v'],
['CF07','Mass','28 kg requirement, 28.69 kg table, about 30 kg current overview','L05,L01','Unreconciled','Subsystem lines sum 23.28 kg versus printed dry 23.41 kg; preserve source'],
['CF08','Payload budgets','20 W allocation / 19 W system versus 27.8 W worst case; 3.85 versus 4.8 kg margined; 4.8 kg exceeds the PLD.004 4.5 kg limit','L05,L07','Scope/configuration unresolved','No invented compliant final budget'],
['CF09','EPS','53.8 W average / 68 W peak requirement versus 89 W science / 192 W maneuver','L05,L07','Definitions/configuration unresolved','Battery can cover transients only with duration/SOC closure; printed margin differs from subtraction'],
['CF10','RCS impulse','110 N s requirement versus text 170 s total impulse','L05','Unit and value unresolved','Do not silently correct to 170 N s or claim capability'],
['CF11','Life / transfer','One-year operations, 1.5-year design; about 95-day case versus 150-day timeline','L02,L05,L07,L21','Different definitions/cases','No selected flight schedule or guaranteed extension'],
['CF12','Yield','4200/5500 versus 37000; text >250 versus conclusion >6000 impacts/day at Geminids','L20,L18','Model dependence; peak-rate conflict','Use annual Table 9 only; no adopted shower-peak rate'],
['CF13','Disposal','Earlier heliocentric escape versus later lunar impact','L17,L02,L05','Later lunar-impact plan','Disposal cost and mitigation rules are epoch-specific'],
]
decisions=[
['C01','Use a versioned LUMIO comparator','2024 payload design and 2026 status; keep older model separate','L01,L05,L06','No final current configuration claimed'],
['C02','Test early-to-total optical energy as one science hypothesis','First-5-ms fraction and tail integral, compared with current ground and LUMIO','L22,L06','Hypothesis; no demonstrated SMD capability'],
['C03','Close useful sample yield before tightening the faint limit','Population variance, recovery and regional exposure determine counts','L18,L20','100 events for 10% mean precision only if CV=1 and bias controlled'],
['C04','Separate full disc visibility from whole-surface coverage','LUMIO plus ground aims at global information','L02,L20','SMD still requires both hemispheres and polar coverage'],
['C05','Size the platform from payload and interfaces','LUMIO inherits CubeSat programme constraints and needs custom deep-space systems','L19,L05,L06','SMD is not restricted to CubeSat; no comparable total-cost evidence'],
['C06','Close mode budgets and engineering cycles','Sun tracking, Moon imaging, DTE and unloading interact','L05,L07','Copied component figures do not close power, momentum or availability'],
['C07','Compare performance at a credible delivery date','Potential LUMIO 2028 and demonstrated 2026 high-speed ground results','L01,L22','Refresh before science baseline; SMD launch date remains unselected'],
]

def export():
    DATA.mkdir(parents=True,exist_ok=True)
    obj={'as_of':DATE,'sources':sources,'claims':claims,'criteria':criteria,'timeline':timeline,'conflicts':conflicts,'comparison':comparison,'decisions':decisions}
    for key,rows in obj.items():
        if isinstance(rows,list):obj[key]=[[text(v) for v in row] for row in rows]
    (DATA/'research_data.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    headers={
      'sources':['source_id','title','publication_event_date','configuration_epoch','location','evidence_type','url','limitation'],
      'claims':['claim_id','area','parameter','value','unit','conditions','configuration_epoch','evidence_status','source_ids','location','confidence','public_gap'],
      'criteria':['criterion_id','metric','value','unit','epoch_status','source_ids','location','interpretation'],
      'timeline':['date','phase','configuration','source_ids','location','status'],
      'conflicts':['conflict_id','subject','claims','source_ids','resolution_status','consequence'],
      'comparison':['driver','lumio_comparator','smd_status','consequence','next_evidence','source_ids'],
      'decisions':['id','action','basis','source_ids','limit']}
    for key,head in headers.items():
        with (DATA/f'{key}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(head);w.writerows(obj[key])
    return obj
if __name__=='__main__':
    obj=export();print({k:len(v) for k,v in obj.items() if isinstance(v,list)})
