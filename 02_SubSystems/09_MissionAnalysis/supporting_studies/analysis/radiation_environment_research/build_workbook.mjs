import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
import {research} from './research_data.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../..');
const inputs=JSON.parse(await fs.readFile(path.join(here,'model_inputs.json'),'utf8'));
const results=JSON.parse(await fs.readFile(path.join(here,'model_results.json'),'utf8'));
const out=path.join(root,'outputs/radiation_environment_research_2026-10-29');
const previews=path.join(root,'tmp/radiation_environment_research/workbook_previews');
await fs.mkdir(previews,{recursive:true});
const wb=Workbook.create();
const names=['Conclusions','Dose comparison','Engineering','Cases','Components','Evidence','Open items'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const col=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const widths={};
function setup(name,w,title,note){
  widths[name]=w;
  const s=sheets[name],r=s.getRangeByIndexes(0,0,100,w.length);
  r.format.font={name:'Arial',size:10,color:'#23344B'};
  r.format.verticalAlignment='top';s.showGridLines=false;
  w.forEach((v,i)=>s.getRangeByIndexes(0,i,100,1).format.columnWidthPx=v);
  s.getRange('A2').values=[[title]];s.getRange('A2').format.font={name:'Arial',size:15,bold:true};
  s.getRange('A2').format.rowHeight=27;
  s.getRange(`A3:${col(w.length-1)}3`).format.borders={bottom:{style:'thin',color:'#294C72'}};
  s.getRange('A4').values=[[note]];s.getRange('A4').format.font={italic:true,size:10,color:'#536578'};
  s.freezePanes.freezeRows(7);s.freezePanes.freezeColumns(1);
  return s;
}
function table(s,row,headers,rows,name){
  const range=s.getRangeByIndexes(row-1,0,rows.length+1,headers.length);
  range.values=[headers,...rows];range.format.wrapText=true;
  const t=s.tables.add(`A${row}:${col(headers.length-1)}${row+rows.length}`,true,name);t.style='TableStyleMedium2';
  const h=s.getRangeByIndexes(row-1,0,1,headers.length);h.format.fill='#294C72';
  h.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};h.format.horizontalAlignment='center';
  h.format.verticalAlignment='center';h.format.rowHeight=38;
  const ws=widths[s.name];
  rows.forEach((r,i)=>{
    const lines=r.map((v,j)=>Math.ceil(String(v??'').length/Math.max(8,(ws[j]-15)/5.6)));
    s.getRangeByIndexes(row+i,0,1,headers.length).format.rowHeight=Math.max(30,Math.max(...lines)*13+12);
  });return t;
}
function n(s,r,fmt='0.00'){s.getRange(r).setNumberFormat(fmt);s.getRange(r).format.horizontalAlignment='right';}
function section(s,row,label,last='H'){
  s.getRange(`A${row}`).values=[[label]];s.getRange(`A${row}:${last}${row}`).format.fill='#EAF0F6';
  s.getRange(`A${row}:${last}${row}`).format.rowHeight=27;s.getRange(`A${row}`).format.font.bold=true;
}

const c=setup('Conclusions',[55,310,350,300,230,330],'Radiation conclusions for SMD','29 October 2026. Provisional study assumptions; selected-sensor qualification and mission rates remain TBR.');
c.tabColor='#294C72';
table(c,7,['ID','Proposed action','Quantitative / evidence basis','Status','Subsystem / drivers','Revisit trigger'],research.decisions,'ConclusionsTable');
section(c,21,'Headline calculations','F');
c.getRange('B23:E27').values=[['Quantity','Value','Unit','Meaning'],['Distant proxy, 2.54 mm',null,'krad(Si)/year','RAD01 solar max, source 95%; ±15% reading'],['Three years + transfer',null,'krad(Si)','Transfer allowance and duration scaling are assumptions'],['Tolerance with margin',null,'krad(Si)','Central reading: preliminary 30 krad class'],['Tolerance at +15% reading',null,'krad(Si)','Preserving margin 2 requires >30 krad; compare 50 krad parts']];
c.getRange('C24:C27').formulas=[["='Dose comparison'!C20"],["='Dose comparison'!G20"],["='Dose comparison'!H20"],["='Dose comparison'!H47"]];
c.getRange('B23:E27').format.wrapText=true;c.getRange('B23:E27').format.rowHeight=55;n(c,'C24:C27','0.0');

const d=setup('Dose comparison',[170,90,150,150,150,150,170,170,150],'Matched published dose cases','RAD01 Fig10. Si, solid Al sphere, solar maximum, source 95%. Reading allowance is not model uncertainty.');
d.getRange('A5:F5').values=[['Years (sensitivity)',3,'Transfer allowance (krad)',1,'Design margin',2]];
for(const cell of ['B5','D5','F5'])d.getRange(cell).format.fill='#FFF0CE';
table(d,7,['Case','Al (mm)','Source dose (krad/y)','Reading low (krad/y)','Reading high (krad/y)','Scaled mission (krad)','Plus transfer (krad)','Tolerance example (krad)','Source'],
  results.dose_rows.map(r=>[r.case,r.shielding_mm,r.dose_krad_Si_year,null,null,null,null,null,'RAD01 Fig10 p11']), 'DoseTable');
for(let i=0;i<20;i++){const r=8+i;d.getRange(`D${r}:H${r}`).formulas=[[`=C${r}*(1-${inputs.digitization_fraction})`,`=C${r}*(1+${inputs.digitization_fraction})`,`=C${r}*$B$5`,`=F${r}+$D$5`,`=G${r}*$F$5`]];}
n(d,'B8:B27','0.00');n(d,'C8:H27','0.00');
section(d,30,'Ratios: only genuinely matched published cases','I');
table(d,32,['Al (mm)','LEO comparator','Distant / LEO','Reading low','Reading high','Condition','Status','Interpretation','Source'],
  results.comparisons.map(r=>[r.shielding_mm,r.leo,null,null,null,'Same Si, solar max, 95%, sphere','Reading limits only','No ratio for 400/51.6 or 600/98','RAD01']), 'RatioTable');
for(let i=0;i<10;i++){
  const r=33+i,j=Math.floor(i/2),ip=18+j,leo=(i%2===0?8:13)+j;
  d.getRange(`C${r}:E${r}`).formulas=[[`=C${ip}/C${leo}`,`=D${ip}/E${leo}`,`=E${ip}/D${leo}`]];
}
n(d,'C33:E42','0.00');
d.getRange('A45').values=[['Three-year scaling is arithmetic, not a recomputed three-year 95% dose. Transfer 1 krad is unvalidated.']];
d.getRange('A47').values=[['Tolerance at +15% reading, same duration/transfer/margin (krad(Si))']];
d.getRange('H47').formulas=[['=(E20*$B$5+$D$5)*$F$5']];n(d,'H47','0.0');

const e=setup('Engineering',[240,140,140,160,180,180,210,310],'Engineering calculations','Inputs in amber are assumptions. Particle incidence and availability are screening calculations, not flight predictions.');
e.tabColor='#718AA4';
e.getRange('A5:F5').values=[['Al density (g/cm3)',2.7,'Sensor area (cm2)',results.headline.imx636_area_cm2,'Box inner side (m)',0.1]];
e.getRange('B5').format.fill='#FFF0CE';e.getRange('F5').format.fill='#FFF0CE';n(e,'D5','0.000000');
table(e,7,['Al (mm)','g/cm2','kg/m2','1 m2 skin (kg)','Exact 10 cm box (kg)','Thin-wall box (kg)','Status','Basis'],
 inputs.shield_mm.map(t=>[t,null,null,null,null,null,'Total wall mass','rho=2.7; six walls, no aperture']), 'MassTable');
for(let i=0;i<5;i++){const r=8+i;e.getRange(`B${r}:F${r}`).formulas=[[`=A${r}/10*$B$5`,`=A${r}*$B$5`,`=C${r}`,`=(($F$5+2*A${r}/1000)^3-$F$5^3)*$B$5*1000`,`=6*$F$5^2*A${r}/1000*$B$5*1000`]];}
n(e,'B8:F12','0.000');
section(e,15,'Body occultation: isotropic scalar primary field only');
table(e,17,['Case','Radius (km)','Altitude (km)','Centre (km)','Visible fraction','Blocked solid angle (sr)','Status','Limit'],
 results.geometry.map(r=>[r.case,r.radius_km,r.altitude_km,null,null,null,'Geometric calculation','No geomagnetic shielding / secondaries']), 'GeometryTable');
for(let i=0;i<5;i++){const r=18+i;e.getRange(`D${r}:F${r}`).formulas=[[`=B${r}+C${r}`,`=(1+SQRT(1-(B${r}/D${r})^2))/2`,`=4*PI()*(1-E${r})`]];}
n(e,'D18:D22','0.0');n(e,'E18:F22','0.00000');
section(e,25,'SEP incident front-face screening, before shielding and detector response');
table(e,27,['j >=10 MeV (pfu)','Area (cm2)','Incident /s','Incident /h','False budget (/h)','Max incident-to-confirmed','Status','Source'],
 results.sep_screening.map(r=>[r.input_flux,null,null,null,.01,null,'Isotropic incident-field sensitivity','RAD14 thresholds; RAD07 area']), 'SEPScreeningTable');
for(let i=0;i<3;i++){const r=28+i;e.getRange(`B${r}:D${r}`).formulas=[['=$D$5',`=PI()*A${r}*B${r}`,`=C${r}*3600`]];e.getRange(`F${r}`).formulas=[[`=E${r}/D${r}`]];}
n(e,'B28:D30','0.000');n(e,'F28:F30','0.00E+00');e.getRange('E28:E30').format.fill='#FFF0CE';
section(e,33,'Availability: assumed losses and recovery, all other mission losses excluded');
table(e,35,['Exclusion days/y','Resets/day','Recovery (s)','Availability','Sample multiplier','Poisson error multiplier','Status','Model'],
 results.availability.map(r=>[r.storm_days_year,r.reset_rate_day,r.recovery_s,null,null,null,'Allocation sensitivity','Stationary renewal; storm/reset overlap ignored']), 'AvailabilityTable');
for(let i=0;i<16;i++){const r=36+i;e.getRange(`D${r}:F${r}`).formulas=[[`=(1-A${r}/${inputs.year_days})/(1+B${r}*C${r}/86400)`,`=D${r}`,`=1/SQRT(E${r})`]];}
n(e,'D36:E51','0.00%');n(e,'F36:F51','0.0000');e.getRange('A36:C51').format.fill='#FFF0CE';
section(e,54,'Integral LET readings: environment scale, not a device-rate calculation');
table(e,56,['Case','LET > (MeV cm2/mg)','Al (mm)','Flux (cm-2 s-1)','Reading low','Reading high','Angular convention','Source'],
 Object.entries(inputs.nasa_fig8.integral_flux_cm2_s).map(([k,v])=>[k,10,2.54,v,null,null,'Not specified; no SEE-rate integration','RAD01 Fig8 printed p9; factor-two reading range']), 'LETTable');
for(let i=0;i<5;i++){const r=57+i;e.getRange(`E${r}:F${r}`).formulas=[[`=D${r}/2`,`=D${r}*2`]];}
n(e,'D57:F61','0.0E+00');
section(e,64,'Quiet-era measurement comparators: different conditions, no matched ratios');
table(e,66,['Source','Source value','Unit','Interval (days)','Annualized rad(Si)','Context','Status','Shield / response limit'],[
 ['RAD02 LRO',12.2,'rad(Si)',333,null,'First 333 days, 2009-2010','Measured quiet era; annualization only','Nonuniform 0.89 / 2.28 g/cm2 paths'],
 ['RAD03 CRaTER',372,'microGy(Si)/day',1,null,'Specific near-Moon response model','Published modeled rate; annualization only','Different geometry; no universal dose factor']
 ],'MeasurementTable');
e.getRange('E67').formulas=[[`=B67/D67*${inputs.year_days}`]];
e.getRange('E68').formulas=[[`=B68*0.000001*${inputs.year_days}/0.01`]];n(e,'E67:E68','0.00');

const cases=setup('Cases',[65,240,130,130,440,500],'Comparison case definitions','Uncomputed reference cases remain explicit gaps. No spacecraft trajectory has been selected.');
table(cases,7,['ID','Case','Altitude (km)','Inclination (deg)','Geometry','Evidence / status'],research.cases,'CasesTable');

const comp=setup('Components',[190,330,400,420,330],'Component evidence and assurance','Technology comparator evidence does not transfer qualification to a selected sensor, kit or board.');
table(comp,7,['Item','Applicable evidence','Consequence','Limit / selection needed','Source'],[
 ['IMX636','1280 x 720, 4.86 um; area 0.217678 cm2','Bound end-of-life response and particle confusion','Public radiation rating/cross-sections not found; exact lot and assembly TBR','RAD07'],
 ['DAVIS240C flight comparator','ISS Jan2022-Sep2024; mild deterioration; 6.35 mm Al enclosure','Supports technology feasibility','Different device/environment, intermittent acquisition; no faint-flash calibration qualification','RAD04'],
 ['DAVIS346 / PPS3MVCD tests','Functional issues above ~30 krad; recoverable proton lock-up; noise growth','Budget drift, saturation and independent power-cycle recovery','180 nm devices; sample/dose-rate/annealing and camera support-circuit ambiguity','RAD05'],
 ['Neutron-tested 640 x 480 EVS','0.1 to >600 MeV beam; 0.6-0.8 ms ON / 8-10 ms OFF','Particle morphology can overlap flash time history','Not IMX636; no lunar charged-particle cross-section inferred','RAD06'],
 ['RTG4 FPGA class','>100 krad; hardened config; SECDED internal memory','Feasible assured interface/processing option','Not selected. Exact grade, power, timing, interfaces, external memory still need sizing','RAD09'],
 ['TPS7H2201-SP class','100 krad; DSEE tested to LET75; 1.5-7 V / 6 A','35 mOhm max at25C/5V CFP/KGD: I2R=0.14 W at2A','Trip energy/time, hot R and downstream SEL tolerance unproven; SEP grade differs','RAD08'],
 ['Memory / processor / clock','Selected devices not yet defined','ECC, scrub, CRC, watchdog, recoverable boot and time correlation','Rates remain TBR; controller/SEFI/common-mode faults not covered by bit ECC alone','RAD13,RAD16'],
 ['Solar arrays','Cell/coverglass and equivalent fluence not selected','Carry explicit end-of-life power factor','No numeric radiation degradation inferred from TID','RAD12'],
 ['Charging','Lunar Prospector vehicle potential summaries -40 to -300 V','Bonding, surface conductivity, dielectric placement and ESD protection','Not a universal limit or voltage across connectors; lunar surface -4.5kV is separate','RAD15,RAD17']
 ],'ComponentsTable');

const ev=setup('Evidence',[75,320,120,220,400,430,470,430,440,370],'Evidence and source conditions','Reviewed 29 October 2026. Access limitations and excluded leads are retained beside each record.');
table(ev,7,['ID','Source','Date / version','Evidence kind','Exact location','Finding','Conditions','Limits','URL','Access'],research.evidence.map(r=>[r.id,r.title,r.date,r.kind,r.location,r.finding,r.conditions,r.limits,r.url,r.access]),'EvidenceTable');
const oi=setup('Open items',[65,290,480,520],'Remaining mission-specific evidence','Literature and bounded first-principles evidence can complete the educational concept; new irradiation is not a course gate.');
table(oi,7,['ID','Open item','Missing evidence','Proportionate next step'],research.open_items,'OpenItemsTable');

// Check that live inputs propagate; restore them before final recalc/export.
const original=d.getRange('G20').values[0][0];d.getRange('D5').values=[[2]];
const changed=d.getRange('G20').values[0][0];
if(Math.abs(changed-original-1)>1e-9)throw new Error('Transfer input propagation failed');
d.getRange('D5').values=[[1]];
e.getRange('A36').values=[[0]];e.getRange('B36').values=[[0]];
if(Math.abs(e.getRange('D36').values[0][0]-1)>1e-12)throw new Error('Availability zero-loss boundary failed');
e.getRange('A36').values=[[1]];e.getRange('B36').values=[[.01]];
wb.recalculate();
const audit=[];
for(const [range,expected] of [["'Dose comparison'!H20",results.headline.dose_tolerance_with_example_margin_krad],["Engineering!E11",results.mass[3].local_box_exact_kg]]){
 const match=range.match(/(?:'([^']+)'|([^!]+))!(.+)/),s=sheets[match[1]??match[2]];
 const actual=s.getRange(match[3]).values[0][0];if(Math.abs(actual-expected)>1e-8)throw new Error(`Mismatch ${range}`);
 audit.push({range,actual,expected});
}
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan'});
await fs.writeFile(path.join(previews,'formula_errors.ndjson'),errors.ndjson);
const inspect=await wb.inspect({kind:'table',range:"'Dose comparison'!A18:I22",include:'values,formulas',tableMaxRows:5,tableMaxCols:9});
await fs.writeFile(path.join(previews,'key_values.ndjson'),inspect.ndjson);
// A readable crop from every tab; additional Engineering crops cover all distinct calculations.
for(const [name,range] of names.map(n=>[n,n==='Evidence'?'A7:F10':n==='Conclusions'?'A7:F11':n==='Engineering'?'A5:H12':'A7:'+col(widths[n].length-1)+'12'])){
 const preview=await wb.render({sheetName:name,range,scale:1.3,format:'png'});
 await fs.writeFile(path.join(previews,name.replaceAll(' ','_')+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
for(const [key,range] of [['geometry','A15:H22'],['SEP','A25:H30'],['availability','A33:H42'],['LET','A54:H61'],['measurements','A64:H68'],['ratios','A30:I37']]){
 const preview=await wb.render({sheetName:key==='ratios'?'Dose comparison':'Engineering',range,scale:1.3,format:'png'});
 await fs.writeFile(path.join(previews,key+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
const summaryPreview=await wb.render({sheetName:'Conclusions',range:'B23:E27',scale:1.3,format:'png'});
await fs.writeFile(path.join(previews,'headline_summary.png'),new Uint8Array(await summaryPreview.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(out,'radiation_environment_research.xlsx'));
await fs.writeFile(path.join(here,'workbook_validation.json'),JSON.stringify({status:'passed',engine:'artifact-tool',audit,input_change:'Transfer 1 to2 to1 krad; zero-loss availability boundary restored',native_excel:'not tested',sheets:names},null,2)+'\n');
console.log(JSON.stringify({sheets:names.length,audit,export:'radiation_environment_research.xlsx'}));
