import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
import { reviewDate, candidates, comparators, evidence, decisions, validation, searchLog,
  flashCases, curveFindings, reconstructionInputs, reconstructionBenchmarks, curveTargets,
  energyFindings, energyTargets } from './research_data.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const inputs = JSON.parse(await fs.readFile(path.join(here,'model_inputs.json'),'utf8'));
const results = JSON.parse(await fs.readFile(path.join(here,'model_results.json'),'utf8'));
const curveResults = JSON.parse(await fs.readFile(path.join(here,'lightcurve_results.json'),'utf8'));
const energyResults = JSON.parse(await fs.readFile(path.join(here,'energy_distribution_results.json'),'utf8'));
// JSON companion preserves source tokens and page provenance; CSV is the archival flat table.
const energyCatalogue = JSON.parse(await fs.readFile(path.join(root,'data/lunar_impact_energy/neliota_192_validated_energy_catalogue.json'),'utf8'));
const outputDir = path.join(root,'outputs','d01_d04_research_2026-10-28');
const previewDir = path.join(root,'tmp','d01_d04_research','workbook_previews');
await fs.mkdir(outputDir,{recursive:true});
await fs.mkdir(previewDir,{recursive:true});
const wb = Workbook.create();
const names = ['Candidate values','Photon budget','Localization','Comparators','Evidence','Decisions','Light curves','Reconstruction','Energy distribution','Energy catalogue'];
const sheets = Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const colName = n => { let s=''; for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s; return s; };
const color = {ink:'#23344B', navy:'#263F62', light:'#EEF2F7', input:'#FFF2D4', warn:'#FFF1DE', green:'#DDEDE8'};

function setup(name,widths,title,context,rowCount=120){
  const s=sheets[name];
  const used=s.getRangeByIndexes(0,0,rowCount,widths.length);
  used.format.font={name:'Arial',size:10,color:color.ink};
  used.format.verticalAlignment='top';
  widths.forEach((w,j)=>s.getRangeByIndexes(0,j,rowCount,1).format.columnWidthPx=w);
  s.showGridLines=false;
  s.getRange('A2').values=[[title]];
  s.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:color.ink};
  s.getRange('A2').format.rowHeight=25;
  s.getRange(`A3:${colName(widths.length-1)}3`).format.borders={bottom:{style:'thin',color:color.navy}};
  s.getRange('A4').values=[[context]];
  s.getRange('A4').format.font={italic:true,size:10,color:'#526176'};
  s.getRange('A4').format.wrapText=false;
  s.getRange('A4').format.rowHeight=22;
  return s;
}

function table(s,row,col,headers,rows,widths,name){
  const r=s.getRangeByIndexes(row-1,col,rows.length+1,headers.length);
  r.values=[headers,...rows];
  r.format.wrapText=true;
  const t=s.tables.add(`${colName(col)}${row}:${colName(col+headers.length-1)}${row+rows.length}`,true,name);
  t.style='TableStyleMedium2';
  t.showFilterButton=true;
  const h=s.getRangeByIndexes(row-1,col,1,headers.length);
  h.format.fill=color.navy;
  h.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
  h.format.horizontalAlignment='center';
  h.format.verticalAlignment='center';
  h.format.rowHeight=32;
  rows.forEach((record,i)=>{
    const lines=record.map((v,j)=>{
      const capacity=Math.max(8,Math.floor((widths[j]-16)/6.2));
      return String(v??'').split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/capacity)),0);
    });
    s.getRangeByIndexes(row+i,col,1,headers.length).format.rowHeight=Math.max(28,Math.max(...lines)*13.5+14);
  });
  return t;
}
function section(s,row,text,last='D'){
  s.getRange(`A${row}`).values=[[text]];
  s.getRange(`A${row}:${last}${row}`).format.fill=color.light;
  s.getRange(`A${row}:${last}${row}`).format.font.bold=true;
  s.getRange(`A${row}:${last}${row}`).format.rowHeight=24;
}
function numeric(s,address,format='0.00'){s.getRange(address).setNumberFormat(format);s.getRange(address).format.horizontalAlignment='right';}

// Physical inputs and photon-counting bounds. The model deliberately excludes unmeasured event-pixel noise.
const pWidths=[285,150,120,430,26,100,95,145,95,145,125,150];
const p=setup('Photon budget',pWidths,'Photon budget and sensitivity','Editable study inputs. This is an ideal charge-counting bound; event-camera performance must be measured.');
p.tabColor='#69829E';
const pRows={}; let next=7;
function input(key,label,value,unit,basis){
  pRows[key]=next;
  p.getRange(`A${next}:D${next}`).values=[[label,value,unit,basis]];
  p.getRange(`B${next}`).format.fill=color.input;
  p.getRange(`A${next}:D${next}`).format.rowHeight=Math.max(30,Math.ceil(basis.length/65)*13.5+10);
  p.getRange(`D${next}`).format.wrapText=true;
  next++;
}
p.getRange('A6:D6').values=[['Input / assumption','Value','Unit','Meaning / provenance']];
p.getRange('A6:D6').format.fill=color.navy;p.getRange('A6:D6').format.font={bold:true,color:'#FFFFFF'};
input('bandLo','Band lower edge',inputs.band_min_nm,'nm','Study top-hat; actual passband remains open (DP3).');
input('bandHi','Band upper edge',inputs.band_max_nm,'nm','Study top-hat; both signal and background are band integrated.');
input('temperature','Flash temperature',inputs.temperature_K,'K','Constant blackbody used only in this bound; E03/E20 motivate the test envelope.');
input('photonFactor','Signal photons per radiant joule',results.base_photon_budget.photons_per_J,'photons/J','Planck integral from calculate.py; rerun builder after changing band or temperature.');
input('range','Flash-to-spacecraft slant range',inputs.range_km,'km','Reference distance, not an orbit selection.');
input('aperture','Entrance-pupil diameter',inputs.aperture_m,'m','Illustrative payload, not a selected telescope.');
input('focal','Focal length',inputs.focal_length_m,'m','Illustrative optics; aperture/focal length jointly determine f-number.');
input('pitch','Pixel pitch',inputs.pixel_pitch_um,'µm','E15, Sony flyer p2. Geometry example only; no device selection.');
input('width','Sensor width',inputs.sensor_width_px,'pixels','E15, Sony flyer p2.');
input('height','Sensor height',inputs.sensor_height_px,'pixels','E15, Sony flyer p2.');
input('efficiency','Effective photon detection fraction',inputs.effective_photon_detection_fraction,'fraction','Assumed optics × QE × ensquared-energy × any split. Not measured IMX636 QE.');
input('nea','Noise-equivalent footprint',inputs.noise_equivalent_pixels,'pixels','Assumed ROI/PSF support; background summed over this solid angle.');
input('radiance','Background band radiance',inputs.background_band_radiance_W_m2_sr,'W/m²/sr','Study envelope; not a measured R/I conversion of earthshine E21.');
input('bgLambda','Background effective wavelength',inputs.background_effective_wavelength_nm,'nm','Independent photon conversion assumption for background.');
input('detectE','Detection equivalent energy',inputs.detection_energy_2pi_J,'J','Candidate; E_2π=2πr²H_B, not true total emission without an angular model.');
input('charE','Physics characterization energy',inputs.characterization_energy_2pi_J,'J','Open science option, DP2.');
input('tau','Exponential decay constant',inputs.decay_constant_ms,'ms','Instantaneous onset; not a model of the recoverable rise or all real flashes.');
input('window','Detection integration window',inputs.detection_window_ms,'ms','100 ms captures 63.2% for τ=100 ms; total input energy includes the rest.');
input('bin','Physics peak averaging interval',inputs.peak_bin_ms,'ms','First bin aligned to onset for this optimistic bound. Test bin-phase errors separately.');
input('bgReference','Background reference interval',inputs.background_reference_ms,'ms','Independent baseline measurement; its estimation variance is included.');
input('sigma','Gaussian trigger threshold',inputs.false_alarm_sigma,'σ','Illustrative trials calculation; not a real event-data false-alarm model.');
input('z90','Normal quantile for 90% recovery',1.2815515655446,'σ','Mathematical constant Φ^−1(0.9). Proxy expected SNR is threshold + this term.');
input('optical','Optical transmission for lux bound',inputs.optical_transmission_for_lux_bound,'fraction','Separate assumed pre-detector transmission; not a calibration of the effective detection fraction.');
input('h','Planck constant',6.62607015e-34,'J·s','SI exact.');
input('c','Speed of light',299792458,'m/s','SI exact.');
input('maxLm','Maximum photopic efficacy',683,'lm/W','Upper bound; actual 600–900 nm spectrum has lower efficacy.');
input('surveyE','Survey characterization energy',3000,'J','Alternative retained with no priority selection (DP2).');
input('surveyBin','Survey peak averaging interval',5,'ms','Alternative retained with no priority selection (DP2).');
input('energyPhoton','Energy photon/background uncertainty',0.07,'fraction','Proposed standard-uncertainty allocation, not a measurement.');
input('energyCal','Energy absolute-responsivity uncertainty',0.05,'fraction','Proposed standard-uncertainty allocation.');
input('energyReconstruction','Energy reconstruction uncertainty',0.04,'fraction','Proposed standard-uncertainty allocation; must include threshold/loss effects.');
input('energyDrift','Energy drift/background residual',0.02,'fraction','Proposed standard-uncertainty allocation.');
input('energyRange','Energy range-conversion uncertainty',0.01,'fraction','Proposed allocation; angular emission is excluded from equivalent-energy accuracy.');
input('peakPhoton','Peak photon/background uncertainty',0.16,'fraction','Proposed peak-flux standard-uncertainty allocation.');
input('peakReconstruction','Peak reconstruction uncertainty',0.10,'fraction','Proposed peak-flux response/loss allocation; unmeasured.');
numeric(p,`B7:B${next-1}`,'0.000');
for(const k of ['h','photonFactor','radiance']) numeric(p,`B${pRows[k]}`,'0.000E+00');
for(const k of ['bandLo','bandHi','temperature','range','width','height','detectE','charE','surveyE','window','tau','bgReference','c'])numeric(p,`B${pRows[k]}`,'#,##0');
for(const k of ['efficiency','optical','energyPhoton','energyCal','energyReconstruction','energyDrift','energyRange','peakPhoton','peakReconstruction'])numeric(p,`B${pRows[k]}`,'0.0%');
const pr=k=>`$B$${pRows[k]}`;
p.getRange(`B${pRows.photonFactor}`).formulas=[[`=IF(AND(${pr('bandLo')}=${inputs.band_min_nm},${pr('bandHi')}=${inputs.band_max_nm},${pr('temperature')}=${inputs.temperature_K}),${results.base_photon_budget.photons_per_J},NA())`]];
p.getRange(`B${pRows.photonFactor}`).format.fill=color.light;
p.getRange('F45').values=[['If band/temperature changes, rerun calculate.py and this builder; the spectral factor becomes unavailable.']];
next+=2; section(p,next++,'Derived values');
function derive(key,label,formula,unit,meaning,format='0.00'){
  pRows[key]=next;
  p.getRange(`A${next}:D${next}`).values=[[label,null,unit,meaning]];
  p.getRange(`B${next}`).formulas=[[formula]];
  p.getRange(`A${next}:D${next}`).format.rowHeight=Math.max(33,Math.ceil(meaning.length/65)*13.5+10);
  p.getRange(`D${next}`).format.wrapText=true;
  numeric(p,`B${next}`,format);next++;
}
derive('area','Collecting area',`=PI()*${pr('aperture')}^2/4`,'m²','Unobscured circular aperture.','0.0000');
derive('theta','Pixel angular pitch',`=${pr('pitch')}*1E-6/${pr('focal')}`,'rad/pixel','Small-angle focal-plane geometry.','0.000E+00');
derive('fluence','Detection radiant exposure',`=${pr('detectE')}/(2*PI()*(${pr('range')}*1000)^2)`,'J/m²','Equivalent energy converted to received radiant exposure.','0.000E+00');
derive('total','Total detected charge equivalent',`=${pr('fluence')}*${pr('area')}*${pr('efficiency')}*${pr('photonFactor')}`,'photoelectrons','Ideal photon conversion; these are not DVS event counts.','#,##0.0');
derive('sigWindow','Signal inside detection window',`=${pr('total')}*(1-EXP(-${pr('window')}/${pr('tau')}))`,'photoelectrons','Exponential fraction captured by the window.','#,##0.0');
derive('bgCoefficient','Background conversion coefficient',`=${pr('area')}*${pr('nea')}*${pr('theta')}^2*${pr('efficiency')}*${pr('bgLambda')}*1E-9/(${pr('h')}*${pr('c')})`,'e⁻·m²·sr/J','Converts background band radiance to the footprint charge-equivalent rate.','0.000E+00');
derive('bgRate','Background charge-equivalent rate',`=${pr('radiance')}*${pr('bgCoefficient')}`,'photoelectrons/s','Radiance × étendue × throughput × photons/J.','#,##0.0');
derive('bgWin','Background inside detection window',`=${pr('bgRate')}*${pr('window')}/1000`,'photoelectrons','Photon shot noise remains after mean-background subtraction.','#,##0.0');
derive('bgVar','Baseline-estimation variance',`=${pr('bgRate')}*(${pr('window')}/1000)^2/(${pr('bgReference')}/1000)`,'photoelectrons²','Independent Poisson baseline-reference uncertainty.','#,##0.0');
derive('snr','Detection SNR bound',`=${pr('sigWindow')}/SQRT(${pr('sigWindow')}+${pr('bgWin')}+${pr('bgVar')})`,'ratio','No event threshold, low-light bandwidth, dark current or readout loss included.');
derive('requiredSnr','Expected SNR proxy for Pd=90%',`=${pr('sigma')}+${pr('z90')}`,'ratio','Gaussian approximation only; blind event injections remain mandatory.');
derive('proxyThreshold','Photon-only threshold-energy proxy',`=(${pr('requiredSnr')}^2+SQRT(${pr('requiredSnr')}^4+4*${pr('requiredSnr')}^2*(${pr('bgWin')}+${pr('bgVar')})))/2/${pr('sigWindow')}*${pr('detectE')}`,'J','Optimistic bound, not a new mission threshold.');
derive('peak','Physics-option peak-bin signal',`=${pr('total')}*${pr('charE')}/${pr('detectE')}*(1-EXP(-${pr('bin')}/${pr('tau')}))`,'photoelectrons','Onset-aligned 1 ms bin in the default example.');
derive('peakSNR','Physics-option peak-bin SNR',`=${pr('peak')}/SQRT(${pr('peak')}+${pr('bgRate')}*${pr('bin')}/1000+${pr('bgRate')}*(${pr('bin')}/1000)^2/(${pr('bgReference')}/1000))`,'ratio','Photon + background + baseline statistics only.');
derive('peakStat','Physics-option statistical peak error',`=1/${pr('peakSNR')}`,'fraction','Lower bound; excludes calibration/reconstruction errors.','0.0%');
derive('surveyPeak','Survey-option peak-bin signal',`=${pr('total')}*${pr('surveyE')}/${pr('detectE')}*(1-EXP(-${pr('surveyBin')}/${pr('tau')}))`,'photoelectrons','Default 3000 J, 5 ms option.');
derive('surveySNR','Survey-option peak-bin SNR',`=${pr('surveyPeak')}/SQRT(${pr('surveyPeak')}+${pr('bgRate')}*${pr('surveyBin')}/1000+${pr('bgRate')}*(${pr('surveyBin')}/1000)^2/(${pr('bgReference')}/1000))`,'ratio','Same photon-statistics assumptions as physics option.');
derive('light','One-way spacecraft light time',`=${pr('range')}*1000/${pr('c')}`,'s','Subtract from calibrated reception time to obtain lunar emission epoch.','0.000000');
derive('fno','Optical f-number',`=${pr('focal')}/${pr('aperture')}`,'ratio','The illustrative optics are f/2.5.');
derive('hfov','Horizontal FoV',`=2*ATAN(${pr('width')}*${pr('pitch')}*1E-6/(2*${pr('focal')}))*180/PI()`,'deg','Partial lunar field; do not infer whole-disk coverage.','0.000');
derive('vfov','Vertical FoV',`=2*ATAN(${pr('height')}*${pr('pitch')}*1E-6/(2*${pr('focal')}))*180/PI()`,'deg','Coverage / constellation remains a separate D05 trade.','0.000');
derive('lux','Peak single-pixel illuminance upper bound',`=${pr('maxLm')}*(${pr('charE')}/(2*PI()*(${pr('range')}*1000)^2)/(${pr('tau')}/1000)*${pr('area')}*${pr('optical')}/(${pr('pitch')}*1E-6)^2+${pr('radiance')}*${pr('theta')}^2*${pr('area')}*${pr('optical')}/(${pr('pitch')}*1E-6)^2)`,'lx','All flash light in one pixel, 683 lm/W maximum. Real PSF/red spectrum lower this; E15/E16 specs do not certify this regime.');
derive('energyRss','Combined energy uncertainty allocation',`=SQRT(SUMSQ(${pr('energyPhoton')}:${pr('energyRange')}))`,'fraction','Independent standard-uncertainty allocation only. Correlated bias is assessed separately.','0.0%');
derive('peakRss','Combined peak uncertainty allocation',`=SQRT(${pr('peakPhoton')}^2+${pr('energyCal')}^2+${pr('peakReconstruction')}^2+${pr('energyDrift')}^2+${pr('energyRange')}^2)`,'fraction','Peak-flux standard-uncertainty allocation; independent terms assumed.','0.0%');

const sweep=[];
for(const range of [10000,50000,80000])for(const aperture of [0.05,0.1,0.2])for(const background of [1e-5,1e-3,1e-2]){
  sweep.push([range,aperture,background,null,null,null,null]);
}
const swWidths=pWidths.slice(5);
table(p,6,5,['Range (km)','Pupil (m)','L_B (W/m²/sr)','Signal charge','Bg variance','SNR at D01','E proxy (J)'],sweep,swWidths,'PhotonSweep');
for(let i=0;i<sweep.length;i++){
  const r=7+i;
  p.getRange(`I${r}`).formulas=[[`=${pr('sigWindow')}*(G${r}/${pr('aperture')})^2*(${pr('range')}/F${r})^2`]];
  p.getRange(`J${r}`).formulas=[[`=${pr('bgCoefficient')}*(${pr('window')}/1000+(${pr('window')}/1000)^2/(${pr('bgReference')}/1000))*(G${r}/${pr('aperture')})^2*H${r}`]];
  p.getRange(`K${r}`).formulas=[[`=I${r}/SQRT(I${r}+J${r})`]];
  p.getRange(`L${r}`).formulas=[[`=(${pr('requiredSnr')}^2+SQRT(${pr('requiredSnr')}^4+4*${pr('requiredSnr')}^2*J${r}))/2/I${r}*${pr('detectE')}`]];
}
numeric(p,'F7:F33','#,##0');numeric(p,'G7:G33','0.00');numeric(p,'H7:H33','0.0E+00');numeric(p,'I7:J33','#,##0.0');numeric(p,'K7:K33','0.00');numeric(p,'L7:L33','#,##0');
p.getRange('K7:K33').conditionalFormats.add('cellIs',{operator:'lessThan',formula:9.2815515655446,format:{fill:'#FBE2D5'}});
p.getRange('F36').values=[['Sweep holds profile/window, pixel solid angle and throughput fixed.']];
p.getRange('F37').values=[['Background radiance is an independent assumed input, not a function of slant range.']];
p.getRange('F38').values=[['SNR below 9.28 misses even this optimistic Gaussian proxy.']];
p.getRange('F40').values=[['Absolute photometry alternatives (A1)']];p.getRange('F40').format.font.bold=true;
p.getRange('F41').values=[['Event-only: absolute-scale transfer is unproven at lunar millisecond flux.']];
p.getRange('F42').values=[['Ground: preflight/stars/coobserved flashes help; unobserved farside flashes lack a direct reference.']];
p.getRange('F43').values=[['Onboard: intensity samples/reference arm only if needed; include split loss and alignment.']];
p.freezePanes.freezeRows(6);

// Local linear surface covariance, independent of the photon model apart from geometry/range.
const l=setup('Localization',[300,145,130,525,25,125,130,130,140],'Surface localization','95% ellipse semimajor is the requirement convention. All error allocations below are illustrative 1σ values.');
const lRows={};let lr=7;
l.getRange('A6:D6').values=[['Allocation / quantity','Value','Unit','Definition / condition']];
l.getRange('A6:D6').format.fill=color.navy;l.getRange('A6:D6').format.font={bold:true,color:'#FFFFFF'};
function li(key,label,value,unit,meaning,formula=false){
 lRows[key]=lr;l.getRange(`A${lr}:D${lr}`).values=[[label,formula?null:value,unit,meaning]];
 if(formula)l.getRange(`B${lr}`).formulas=[[value]];else l.getRange(`B${lr}`).format.fill=color.input;
 l.getRange(`A${lr}:D${lr}`).format.rowHeight=36;l.getRange(`D${lr}`).format.wrapText=true;numeric(l,`B${lr}`);lr++;
}
const lp=k=>`$B$${lRows[k]}`;
li('range','Reference slant range',`='Photon budget'!B${pRows.range}`,'km','Linked to the optical reference model.',true);
li('pixel','Angular pitch',`='Photon budget'!B${pRows.theta}*180*3600/PI()`,'arcsec/pixel','Sampling is one contributor to accuracy, not the accuracy itself.',true);
li('centroid','Centroid error',inputs.centroid_sigma_px,'pixel','Assumed subpixel error; characterize versus flux, PSF and pixel response.');
li('attitude','Attitude knowledge error',inputs.attitude_sigma_arcsec,'arcsec','Postprocessed per-axis allocation; requires demonstrated estimation / image registration.');
li('boresight','Boresight / distortion residual',inputs.boresight_sigma_arcsec,'arcsec','Calibrated line-of-sight alignment allocation.');
li('jitter','Residual uncorrected jitter',inputs.residual_jitter_sigma_arcsec,'arcsec','Residual knowledge/smear contribution; not a wheel-control requirement by itself.');
li('orbit','Horizontal orbit error',inputs.orbit_horizontal_sigma_km,'km','Isotropic local allocation; full orbit/attitude covariance still needed.');
li('map','Horizontal map registration error',inputs.map_horizontal_sigma_km,'km','Independent local map error allocation.');
li('height','Topographic height error',inputs.topography_height_sigma_km,'km','Surface-normal error maps to horizontal shift via tan(emission).');
li('confidence','Horizontal confidence',inputs.horizontal_confidence,'fraction','Two-dimensional Gaussian confidence, not a one-dimensional 1.96σ interval.');
li('k95','2D confidence multiplier',`=SQRT(-2*LN(1-${lp('confidence')}))`,'ratio','sqrt[−2 ln(1−0.95)] = 2.4477.',true);
li('sigmaAngle','Combined angular standard deviation',`=SQRT((${lp('centroid')}*${lp('pixel')})^2+SUMSQ(${lp('attitude')}:${lp('jitter')}))`,'arcsec','Independent per-axis contributors; systematic offsets cannot simply be averaged down.',true);
li('ground','Angular ground error at nadir',`=${lp('range')}*${lp('sigmaAngle')}*PI()/(180*3600)`,'km','Slant range × angular error.',true);
li('terrain','Terrain ellipse semimajor candidate',5,'km','Retained alternative. Classify only if ≥95% of confidence-region area is one terrain.');
li('crater','Crater-search semimajor candidate',1,'km','Retained alternative. Actual before/after imaging remains necessary.');
li('terrainArea','Maximum enclosing terrain search area',`=PI()*${lp('terrain')}^2`,'km²','Upper bound for a circle enclosing an ellipse of this semimajor.',true);
li('craterArea','Maximum enclosing crater search area',`=PI()*${lp('crater')}^2`,'km²','A search area, not a predicted crater size.',true);
li('coordArc','Arc subtended by 0.5° on Moon',`=${inputs.moon_radius_km}*0.5*PI()/180`,'km','E03 coordinate-error scale only; no equivalent 95% covariance is specified.',true);
numeric(l,`B${lRows.confidence}`,'0.0%');numeric(l,`B${lRows.range}`,'#,##0');
const projections=[0,30,60,70,80].map(x=>[x,null,null,null]);
table(l,6,5,['Emission (deg)','a95 (km)','b95 (km)','Area95 (km²)'],projections,[125,130,130,140],'LocalProjection');
for(let i=0;i<projections.length;i++){
 const r=7+i;
 l.getRange(`G${r}`).formulas=[[`=${lp('k95')}*SQRT((${lp('ground')}^2+${lp('orbit')}^2)/COS(F${r}*PI()/180)^2+${lp('map')}^2+(${lp('height')}*TAN(F${r}*PI()/180))^2)`]];
 l.getRange(`H${r}`).formulas=[[`=${lp('k95')}*SQRT(${lp('ground')}^2+${lp('orbit')}^2+${lp('map')}^2)`]];
 l.getRange(`I${r}`).formulas=[[`=PI()*G${r}*H${r}`]];
}
numeric(l,'F7:F11','0');numeric(l,'G7:I11','0.000');
l.getRange('G7:G11').conditionalFormats.add('cellIs',{operator:'greaterThan',formula:1,format:{fill:'#FBE2D5'}});
l.getRange('F14').values=[['Poles: use local surface east/north coordinates; longitude is singular at the pole.']];
l.getRange('F16').values=[['Limb: the linear secant model eventually fails; use full ray/DEM intersections.']];
l.getRange('F18').values=[['Timing: include image motion and spacecraft state at corrected reception time.']];
l.getRange('F20').values=[['Covariance: correlations, occultation and non-Gaussian tails need Monte Carlo validation.']];
l.freezePanes.freezeRows(6);

const cWidths=[90,250,145,115,300,390,300,300,420,150];
const c=setup('Candidate values',cWidths,'D01–D04 candidate mission values','28 October 2026. Both scientific priorities and both localization outcomes remain open. No numerical requirement is baselined.');
c.tabColor=color.navy;
table(c,6,0,['Driver','Measure','Candidate value','Unit','Criterion','Reference conditions','Scientific rationale','Status / uncertainty','Validation and subsystem consequence','Evidence IDs'],candidates,cWidths,'CandidateDrivers');
for(let i=0;i<candidates.length;i++)numeric(c,`C${7+i}`,'0.0');
for(const r of [8,9,10])numeric(c,`C${r}`,'#,##0');
numeric(c,'C7','0.00E+00');for(const r of [16,17,18])numeric(c,`C${r}`,'0.0%');
numeric(c,'C19:C20','0');
c.getRange('C7').formulas=[[`='Photon budget'!B${pRows.fluence}`]];
c.getRange('C8').formulas=[[`='Photon budget'!B${pRows.detectE}`]];
c.getRange('C9').formulas=[[`='Photon budget'!B${pRows.surveyE}`]];
c.getRange('C10').formulas=[[`='Photon budget'!B${pRows.charE}`]];
c.getRange('C11').formulas=[[`='Photon budget'!B${pRows.bin}`]];
c.getRange('C13').formulas=[[`='Photon budget'!B${pRows.surveyBin}`]];
c.getRange('C19').formulas=[[`='Localization'!B${lRows.terrain}`]];
c.getRange('C20').formulas=[[`='Localization'!B${lRows.crater}`]];
c.freezePanes.freezeRows(6);c.freezePanes.freezeColumns(2);

const compWidths=[200,160,270,145,170,310,380,410,420,160];
const comp=setup('Comparators',compWidths,'Published comparators and transfer limits','Observed data, manufacturer tests and planned performance retain their original conditions. No cross-band sensitivity ranking is claimed.');
table(comp,6,0,['System / case','Evidence status','Band / variable','Published value','Unit / convention','Temporal condition','Measurement conditions','Limitation','Fair-comparison implication','Evidence IDs'],comparators,compWidths,'PublishedComparators');
numeric(comp,'D7:D9','0.0');numeric(comp,'D10:D11','0');numeric(comp,'D12','0.0');numeric(comp,'D13:D14','0');numeric(comp,'D15','0.0%');comp.freezePanes.freezeRows(6);comp.freezePanes.freezeColumns(1);

const eWidths=[80,150,330,220,175,450,450,405,390,310,125];
const e=setup('Evidence',eWidths,'Evidence register and review method',`E01–E${evidence.length} are this study’s evidence IDs. Dates/versions and source access limits remain explicit.`);
const eRows=evidence.map(r=>[...r,new Date('2026-10-28T12:00:00Z')]);
table(e,6,0,['ID','Published / version','Source','Evidence type','Drivers','Finding','Conditions / uncertainty','Page / table / section','Source URL','Access / verification','Access date'],eRows,eWidths,'DriverEvidence');
numeric(e,`K7:K${6+eRows.length}`,'yyyy-mm-dd');
e.freezePanes.freezeRows(6);e.freezePanes.freezeColumns(1);
const searchRow=10+eRows.length;section(e,searchRow,'Search scope and limitations','D');
table(e,searchRow+2,0,['Area','Search / selection focus','Outcome / method'],searchLog,eWidths.slice(0,3),'ResearchSearchLog');

const dWidths=[90,295,250,500,525,490];
const d=setup('Decisions',dWidths,'Decisions and required validation','User decisions recorded on 28 October 2026. Open choices are preserved; no unanswered question is treated as approval.');
table(d,6,0,['ID','Decision point','Status','User response / study treatment','Design consequence','Next step'],decisions,dWidths,'ResearchDecisions');
d.freezePanes.freezeRows(6);d.freezePanes.freezeColumns(1);
section(d,18,'Validation needed before claiming attainable performance','F');
table(d,20,0,['ID','Drivers','Analysis / test','Acceptance evidence','Qualification / limitation'],validation,dWidths.slice(0,5),'DriverValidation');

// New source records and reconstruction questions. The original photon/geometry calculations remain intact.
const lcWidths=[120,135,155,145,155,125,290,430,240];
const lc=setup('Light curves',lcWidths,'Observed lunar flash light curves','Published source records, not a newly reduced dataset. Z-E4 and Z-E4 slow are the same impact; durations depend on sensitivity and sampling.');
table(lc,6,0,['Case','Interval (ms)','Observed duration (ms)','Peak mag','Quoted sigma (mag)','Saturated?','Effective band','Shape / qualification','Evidence'],flashCases,lcWidths,'ObservedFlashCases');
numeric(lc,'B7:C11','0');numeric(lc,'D7:E11','0.00');
section(lc,14,'Cooling, spectral and duration evidence','H');
const cfWidths=lcWidths.slice(0,8);
table(lc,16,0,['ID','Measure','Value','Unit','Conditions / errors','Science implication','Limitation','Evidence'],curveFindings,cfWidths,'CurveMorphology');
numeric(lc,`C17:C${16+curveFindings.length}`,'0.0');
lc.freezePanes.freezeRows(6);lc.freezePanes.freezeColumns(1);

const reWidths=[100,300,140,125,430,430,220];
const re=setup('Reconstruction',reWidths,'Light-curve reconstruction and tests','Inputs, measured comparators and reproducible analytic examples. Proposed tests do not change the D01–D04 requirements status.');
const riRows=reconstructionInputs.map(r=>[r[0],r[1],r[2],r[5].replaceAll(',',', '),r[3],r[4]]);
table(re,6,0,['ID','Input','Needed for','Evidence','Recovery method','Consequence if missing'],riRows,reWidths.slice(0,6),'ReconstructionInputs');
const benchmarkSection=10+riRows.length;
section(re,benchmarkSection,'Published accuracy and transfer limits','G');
const benchmarkRows=reconstructionBenchmarks.map((r,i)=>[`RB${String(i+1).padStart(2,'0')}`,r[0],r[1],r[2],r[3],`${r[4]} ${r[5]}`,r[6]]);
const benchmarkHeader=benchmarkSection+2;
table(re,benchmarkHeader,0,['ID','Published case','Value','Unit / metric','Protocol','Interpretation and limitation','Evidence'],benchmarkRows,reWidths,'ReconstructionBenchmarks');
numeric(re,`C${benchmarkHeader+1}:C${benchmarkHeader+benchmarkRows.length}`,'0.00');
const analyticSection=benchmarkHeader+benchmarkRows.length+4;
section(re,analyticSection,'Analytic illustrations from calculate_lightcurves.py','G');
const a=curveResults.exponential_interpretation_only, ev=curveResults.ideal_event_example;
const analyticRows=[
 ['LA01','Illustrative exponential decline constant',a.decay_constant_ms,'ms','1.5 magnitude fall in 4 ms, interpreted as a pure exponential.','Not a fit to raw observations or a universal flash template.','E05; lightcurve_inputs.json'],
 ...a.averaged_peak_fractions.map((x,i)=>[`LA${String(i+2).padStart(2,'0')}`,`Mean / initial peak, ${x.bin_ms} ms bin`,x.mean_over_initial_peak,'fraction','Bin starts exactly at onset; exponential τ=2.895 ms.','Unknown bin phase, multi-component profiles and background alter the answer.','calculate_lightcurves.py']),
 ['LA09','Longest bin for ≤5% averaging loss',a.max_bin_ms_for_5pct_averaging_loss,'ms','Same ideal exponential and onset alignment.','A brighter-subset stretch study, not a selected output resolution.','Analytic derivation'],
 ['LA10','Ideal events for a 10:1 rise',ev.events_for_tenfold_rise,'events/pixel','12% ON contrast; ideal log increments.','A real integer sequence, initial phase, noise and losses require a forward model.','E14; analytic derivation'],
 ['LA11','Refractory ceiling for the example rise',ev.max_refractory_us_for_log_uniform_rise,'µs','10:1 log-uniform rise in 1 ms.','A necessary illustrative rate condition, not sufficient recovery evidence.','Analytic derivation'],
 ['LA12','One missed ON event: total-intensity loss',ev.one_missed_on_event_total_intensity_underestimate_fraction,'fraction','12% ON contrast; missing one increment before background subtraction.','Flash-only relative error can be larger when background is significant.','Analytic derivation'],
 ['LA13','Coherent threshold error giving 5% intensity bias',ev.coherent_relative_threshold_error_for_5pct_intensity_bias,'relative fraction','10:1 rise; no other error contributors.','Illustrative calibration sensitivity; full budget must be tighter if errors combine.','Analytic derivation'],
 ['LA14','Corner for ≤5% attenuation at 1 kHz',ev.corner_Hz_for_5pct_sinusoidal_gain_loss_at_1kHz,'Hz','First-order low-pass sinusoidal example.','Test at actual irradiance. A 1 kHz sine is not a 1 ms pulse.','E14; analytic derivation'],
 ['LA15','Colour-ratio error at 0.1 ms offset',a.relative_colour_ratio_error_at_offset,'fraction','Both bands share the same illustrative 2.895 ms exponential.','Independent spectral evolution and sensor latency require more modelling.','Analytic derivation'],
 ['LA16','Energy captured by five exponential constants',a.tail_capture_fraction_at_five_tau,'fraction','Exactly exponential, integrated from onset to 5τ.','E04 cooling parameters do not guarantee this energy fraction.','Analytic derivation'],
];
const analyticHeader=analyticSection+2;
table(re,analyticHeader,0,['ID','Calculated quantity','Value','Unit','Assumptions','Interpretation / limit','Basis'],analyticRows,reWidths,'LightCurveExamples');
numeric(re,`C${analyticHeader+1}:C${analyticHeader+analyticRows.length}`,'0.0000');
const targetSection=analyticHeader+analyticRows.length+4;
section(re,targetSection,'Further-analysis targets and retained open choices','F');
const targetRows=curveTargets.map(r=>[r[0],r[1],r[0]==='LCT01'?'Retained candidate':'Proposed / derived',r[5].replaceAll(',',', '),`${r[2]} ${r[3]}`,r[4]]);
const targetHeader=targetSection+2;
table(re,targetHeader,0,['ID','Investigation','Status','Evidence','Criterion and basis','Verification'],targetRows,reWidths.slice(0,6),'CurveInvestigationTargets');
re.freezePanes.freezeRows(6);re.freezePanes.freezeColumns(2);

// Energy population: primary optical measurements remain separate from kinetic scenarios.
const enWidths=[145,260,160,230,350,390,350,150];
const en=setup('Energy distribution',enWidths,'Impact-energy distribution and missing populations',
  '192 validated NELIOTA records; uncorrected observed sample. η changes kinetic inference, not measured optical energy.');
en.getRange('A6:D8').values=[
 ['Scenario input','Value','Unit','Interpretation'],
 ['Nominal efficiency',energyResults.eta_nominal,'fraction','Editable illustrative conversion for R+I energy; not selected for the mission 600–900 nm band.'],
 ['Source sample size',192,'validated events','2017–August2023; not a complete lunar population or energy interval.']
];
en.getRange('A6:D6').format.fill=color.navy;en.getRange('A6:D6').format.font={bold:true,color:'#FFFFFF'};
en.getRange('B7').format.fill=color.input;numeric(en,'B7','0.0000');
en.getRange('A6:D8').format.wrapText=true;en.getRange('A7:D8').format.rowHeight=60;
section(en,10,'Observed optical energy bins; unequal bin widths, no completeness correction','F');
const histRows=energyResults.histogram.map((r,i)=>[r.lower_J_inclusive,r.upper_J_exclusive,r.count,r.fraction,r.poisson_fractional_sigma??'—','R+I hemispheric-equivalent energy; counts are selected observations.']);
table(en,12,0,['Lower inclusive [J]','Upper exclusive [J]','Count','Sample fraction','Poisson relative σ','Interpretation'],histRows,enWidths.slice(0,6),'ObservedEnergyBins');
for(let i=0;i<histRows.length;i++){
 const row=13+i;
 en.getRange(`C${row}`).formulas=[[`=COUNTIFS('Energy catalogue'!$G$7:$G$198,">="&A${row},'Energy catalogue'!$G$7:$G$198,"<"&B${row})`]];
 en.getRange(`D${row}`).formulas=[[`=C${row}/$B$8`]];
 en.getRange(`E${row}`).formulas=[[`=IF(C${row}=0,"—",1/SQRT(C${row}))`]];
}
numeric(en,'A13:B18','#,##0');numeric(en,'C13:C18','0');numeric(en,'D13:E18','0.0%');
section(en,21,'Consequential values and limits','H');
table(en,23,0,['ID','Finding','Value','Unit','Reference conditions','Explanation','Status / uncertainty','Evidence'],energyFindings,enWidths,'EnergyFindings');
numeric(en,`C24:C${23+energyFindings.length}`,'0.000E+00');
const energyTargetSection=27+energyFindings.length;
section(en,energyTargetSection,'Further-analysis targets, not baselined requirements','F');
table(en,energyTargetSection+2,0,['ID','Investigation','Proposed value / output','Reference conditions','Acceptance or use','Status'],energyTargets,enWidths.slice(0,6),'EnergyInvestigationTargets');
en.freezePanes.freezeRows(6);en.freezePanes.freezeColumns(2);

const catWidths=[85,100,130,130,130,130,150,160,160,165,165,150,100,420];
const cat=setup('Energy catalogue',catWidths,'Published validated NELIOTA energy catalogue',
 "Source: 2020 v1 Tables4–5 +2024 v1 TableA.2. C–G/I–K: source values; H: inference using 'Energy distribution'!B7. Full tokens/SHA in data/lunar_impact_energy/.",205);
const catRows=energyCatalogue.map(r=>[r.event_id,r.stream,r.R_energy_J,r.R_quoted_error_J,r.I_energy_J,r.I_quoted_error_J,r.R_plus_I_energy_J,
 r.KE_eta_0p0015_from_rounded_optical_J,r.KE_eta_0p0015_published_J,r.KE_eta_0p005_published_J,r.KE_eta_0p0005_published_J,r.source_table,r.source_pdf_page,
 `https://arxiv.org/pdf/${r.source_id==='liakos_2020'?'1911.06101v1':'2403.19613v1'}#page=${r.source_pdf_page}`]);
table(cat,6,0,['Event ID','Stream','R energy [J]','R quoted ± [J]','I energy [J]','I quoted ± [J]','R+I energy [J]','Inferred KE [J], study η','Published KE [J], η=.0015','Published KE [J], η=.005','Published KE [J], η=.0005','Source table','PDF page','Source URL'],catRows,catWidths,'ValidatedEnergyCatalogue');
for(let i=0;i<catRows.length;i++){
 const row=7+i;
 cat.getRange(`G${row}`).formulas=[[`=C${row}+E${row}`]];
 cat.getRange(`H${row}`).formulas=[[`=G${row}/'Energy distribution'!$B$7`]];
}
numeric(cat,'C7:K198','#,##0');numeric(cat,'A7:A198','0');numeric(cat,'M7:M198','0');
cat.freezePanes.freezeRows(6);cat.freezePanes.freezeColumns(2);

// Recalculate, compare against an independent Python implementation, and test a representative edit then restore it.
wb.recalculate();
function value(s,cell){return s.getRange(cell).values[0][0];}
const tolerance=(actual,expected,label)=>{if(typeof actual!=='number'||Math.abs(actual-expected)>1e-7*Math.max(1,Math.abs(expected)))throw new Error(`${label}: ${actual} != ${expected}`);};
tolerance(value(p,`B${pRows.snr}`),results.base_photon_budget.snr_detection,'Detection SNR');
tolerance(value(p,`B${pRows.peakSNR}`),results.base_photon_budget.snr_characterization_peak_bin,'Peak SNR');
tolerance(value(p,`B${pRows.proxyThreshold}`),results.base_photon_budget.proxy_threshold_energy_J,'Threshold proxy');
tolerance(value(p,`B${pRows.energyRss}`),results.energy_rss_fraction,'Energy RSS');
tolerance(value(p,`B${pRows.peakRss}`),results.peak_rss_fraction,'Peak RSS');
tolerance(value(l,'G9'),results.localization[2].major95_km,'Off-nadir ellipse');
tolerance(value(cat,'G7'),energyCatalogue[0].R_plus_I_energy_J,'Catalogue R+I');
tolerance(value(cat,'H7'),energyCatalogue[0].KE_eta_0p0015_from_rounded_optical_J,'Catalogue nominal KE');
const nominalEta=value(en,'B7'), nominalKE=value(cat,'H7');
en.getRange('B7').values=[[nominalEta*2]];wb.recalculate();
tolerance(value(cat,'H7'),nominalKE/2,'Energy inference changes with eta');
en.getRange('B7').values=[[nominalEta]];wb.recalculate();
tolerance(value(cat,'H7'),nominalKE,'Restored nominal eta');
const original=value(p,`B${pRows.aperture}`), originalSNR=value(p,`B${pRows.snr}`);
p.getRange(`B${pRows.aperture}`).values=[[original*0.5]];wb.recalculate();
tolerance(value(p,`B${pRows.snr}`),originalSNR*0.5,'Aperture edit recalculation');
p.getRange(`B${pRows.aperture}`).values=[[original]];wb.recalculate();
tolerance(value(p,`B${pRows.snr}`),originalSNR,'Restored aperture');
const originalBackground=value(p,`B${pRows.radiance}`);
p.getRange(`B${pRows.radiance}`).values=[[0]];wb.recalculate();
tolerance(value(p,`B${pRows.snr}`),Math.sqrt(value(p,`B${pRows.sigWindow}`)),'Zero-background Poisson limit');
p.getRange(`B${pRows.radiance}`).values=[[originalBackground]];wb.recalculate();
tolerance(value(p,`B${pRows.snr}`),originalSNR,'Restored background');
const errorScan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:1800});
await fs.writeFile(path.join(previewDir,'formula_error_scan.ndjson'),errorScan.ndjson,'utf8');
console.log(errorScan.ndjson);
const inspection=await wb.inspect({kind:'sheet',include:'id,name',maxChars:2200});console.log(inspection.ndjson);
const mapping={photon:pRows,localization:lRows};await fs.writeFile(path.join(here,'workbook_cells.json'),JSON.stringify(mapping,null,2));
const checks={reviewDate,sheets:names,evidenceCount:evidence.length,candidateMetrics:candidates.length,
  detectionSNR:value(p,`B${pRows.snr}`),peakSNR:value(p,`B${pRows.peakSNR}`),surveyPeakSNR:value(p,`B${pRows.surveySNR}`),
  ellipse60Major95_km:value(l,'G9'),inputChangeRecalculation:'Aperture halved, SNR halved; zero background gives sqrt(signal); restored',
  sourceLimitations:'See Evidence; model excludes unmeasured event response',nativeExcelApplicationTest:'Not performed',
  flashCaseRows:flashCases.length,curveFindingRows:curveFindings.length,reconstructionInputRows:riRows.length,
  reconstructionBenchmarkRows:benchmarkRows.length,analyticExampleRows:analyticRows.length,investigationTargetRows:targetRows.length,
  energyCatalogueRows:catRows.length,energySourceChecks:'192 unique IDs; all three published KE scenarios consistent with R/I rounding; two source-summary discrepancies retained',
  etaRecalculation:'Doubled η halves inferred KE; restored'};
await fs.writeFile(path.join(previewDir,'verification.json'),JSON.stringify(checks,null,2));
// Normal-zoom bounded renders cover each worksheet and both parts of the larger calculation views.
const affectedOnly=process.argv.includes('--affected-only');
const selectedPreviews=(process.argv.find(x=>x.startsWith('--preview-names='))?.split('=')[1]??'').split(',').filter(Boolean);
for(const [sheetName,range,file] of [
 ['Candidate values','A1:F10','candidates_values'],['Candidate values','G6:J14','candidates_conditions'],
 ['Candidate values','A11:F20','candidates_quality'],
 ['Photon budget','A1:D21','photon_inputs'],['Photon budget',`A${pRows.area-1}:D${pRows.peakRss}`,'photon_results'],
 ['Photon budget','F6:L16','photon_sweep'],['Localization','A1:D17','localization_inputs'],['Localization','F6:I11','localization_projection'],
 ['Comparators','A1:F10','comparators'],['Comparators','G6:J10','comparator_limits'],
 ['Evidence','A1:G10','evidence_findings'],['Evidence','H6:K12','evidence_sources'],
 ['Evidence',`A${searchRow}:C${searchRow+2+searchLog.length}`,'search_scope'],
 ['Decisions','A1:D10','decisions'],['Decisions','A18:E27','validation'],
 ['Evidence','A11:G11','updated_zadko_evidence'],['Evidence',`A33:G${6+eRows.length}`,'lightcurve_evidence'],
 ['Evidence',`H33:K${6+eRows.length}`,'lightcurve_sources'],
 ['Decisions',`A${6+decisions.length}:F${6+decisions.length}`,'spectral_decision'],
 ['Light curves','A1:I11','observed_lightcurves'],['Light curves',`A14:H${16+curveFindings.length}`,'curve_shapes'],
 ['Reconstruction',`A1:F${6+riRows.length}`,'reconstruction_inputs'],
 ['Reconstruction',`A${benchmarkSection}:G${benchmarkHeader+benchmarkRows.length}`,'reconstruction_accuracy'],
 ['Reconstruction',`A${analyticSection}:G${analyticHeader+7}`,'lightcurve_averaging'],
 ['Reconstruction',`A${analyticHeader+8}:G${analyticHeader+analyticRows.length}`,'event_reconstruction_examples'],
 ['Reconstruction',`A${targetSection}:F${targetHeader+targetRows.length}`,'curve_targets'],
 ['Energy distribution','A1:F18','energy_distribution'],['Energy distribution','A21:H28','energy_ranges'],
 ['Energy distribution','A29:H32','energy_limits'],
 ['Energy distribution',`A${energyTargetSection}:F${energyTargetSection+2+energyTargets.length}`,'energy_targets'],
 ['Energy catalogue','A1:H12','energy_catalogue'],['Energy catalogue','I6:N12','energy_catalogue_sources'],
 ['Energy catalogue','A79:K85','energy_catalogue_minimum'],
 ['Evidence','A39:G45','energy_evidence'],['Evidence','H39:K45','energy_sources']
]){
 if(affectedOnly && !['Comparators','Evidence','Decisions','Light curves','Reconstruction','Energy distribution','Energy catalogue'].includes(sheetName))continue;
 if(selectedPreviews.length && !selectedPreviews.includes(file))continue;
 const png=await wb.render({sheetName,range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(previewDir,`${file}.png`),new Uint8Array(await png.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);
const target=path.join(outputDir,'d01_d04_research.xlsx');
await output.save(target);
console.log(JSON.stringify({output:target,...checks}));
