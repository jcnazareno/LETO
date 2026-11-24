import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const H=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(H,'../..');
const D=JSON.parse(await fs.readFile(path.join(ROOT,'data/lumio_comparison/research_data.json'),'utf8'));
const I=JSON.parse(await fs.readFile(path.join(H,'model_inputs.json'),'utf8'));
const R=JSON.parse(await fs.readFile(path.join(ROOT,'data/lumio_comparison/calculation_results.json'),'utf8'));
const OUT=path.join(ROOT,'outputs/lumio_comparison_research_2026-10-29');
const PRE=path.join(ROOT,'tmp/lumio_comparison_research/workbook_previews');
await fs.mkdir(PRE,{recursive:true});
const wb=Workbook.create();
const names=['Conclusions','Mission criteria','Design history','Subsystems','SMD comparison','Calculations','Evidence'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const widths={};
const col=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
function setup(name,w,title,note){
 const s=sheets[name];widths[name]=w;s.showGridLines=false;
 const f=s.getRangeByIndexes(0,0,165,w.length).format;
 f.font={name:'Arial',size:10,color:'#24374D'};f.verticalAlignment='top';
 w.forEach((v,j)=>s.getRangeByIndexes(0,j,165,1).format.columnWidthPx=v);
 s.getRange('A2').values=[[title]];s.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:'#294C72'};
 s.getRange('A2').format.rowHeight=29;
 s.getRange(`A3:${col(w.length-1)}3`).format.borders={bottom:{style:'thin',color:'#294C72'}};
 s.getRange('A4').values=[[note]];s.getRange('A4').format.font={size:10,italic:true,color:'#5B6C80'};
 s.freezePanes.freezeRows(7);s.freezePanes.freezeColumns(1);return s;
}
function table(s,row,head,rows,name){
 const range=s.getRangeByIndexes(row-1,0,rows.length+1,head.length);range.values=[head,...rows];range.format.wrapText=true;
 s.tables.add(`A${row}:${col(head.length-1)}${row+rows.length}`,true,name).style='TableStyleMedium2';
 const h=s.getRangeByIndexes(row-1,0,1,head.length);h.format.fill='#294C72';h.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
 h.format.horizontalAlignment='center';h.format.verticalAlignment='center';h.format.rowHeight=34;
 rows.forEach((r,i)=>{
  const lines=r.map((v,j)=>String(v??'').split('\n').reduce((a,t)=>a+Math.max(1,Math.ceil(t.length/Math.max(8,(widths[s.name][j]-16)/5.4))),0));
  s.getRangeByIndexes(row+i,0,1,head.length).format.rowHeight=Math.max(30,Math.max(...lines)*13+11);
 });
}
function section(s,r,title,last='H'){
 s.getRange(`A${r}:${last}${r}`).format.fill='#EAF0F6';s.getRange(`A${r}:${last}${r}`).format.rowHeight=25;
 s.getRange(`A${r}`).values=[[title]];s.getRange(`A${r}`).format.font.bold=true;
}
function fmt(s,r,f='0.00'){s.getRange(r).setNumberFormat(f);s.getRange(r).format.horizontalAlignment='right';}

const c=setup('Conclusions',[65,300,400,130,370],'LUMIO comparison: decisions for SMD','29 October 2026. Versioned comparator; SMD choices and performance remain provisional.');
c.tabColor='#294C72';
table(c,7,['ID','Action','Basis','Sources','Limit'],D.decisions,'ConclusionsTable');
section(c,18,'Calculated comparison results','E');
table(c,20,['Quantity','Result','Unit','Status','Interpretation'],[
 ['Ideal science windows',null,'h/year','Calculation','Half-cycle allowance before additional exclusions'],
 ['Published model data volume',null,'Gbit/year','Calculation','Tile assumptions and 37000 predicted detections'],
 ['Trial useful sample',null,'events','Planning sensitivity','10% mean precision if population CV=1; not a requirement'],
 ['Angular sampling',null,'arcsec/pixel','Geometry','Not surface localization accuracy'],
 ['Phase B delta-v table',null,'m/s','Source audit','Line sums reproduce 79.05; flight case not selected']
],'HeadlineTable');
c.getRange('B21:B25').formulas=[["='Calculations'!C45"],["='Calculations'!B90"],["='Calculations'!B93"],["='Calculations'!D35"],["='Calculations'!B118"]];fmt(c,'B21:B25','0.00');

const m=setup('Mission criteria',[115,240,240,150,230,100,200,380],'Mission objectives and published criteria','2018 orbit acceptance and 2024 requirements retain their epoch. Current minimum/full success is not public here.');
table(m,7,['ID','Metric','Value','Unit','Epoch / status','Sources','Location','Interpretation'],D.criteria,'CriteriaTable');

const h=setup('Design history',[185,190,530,130,250,370],'Configuration history and conflicts','Publication, event and design dates differ. A newer overview does not reconcile an older detailed budget.');
table(h,7,['Date','Phase','Configuration / event','Sources','Location','Status'],D.timeline,'TimelineTable');
section(h,23,'Conflicting claims: preserve the unresolved differences','F');
table(h,25,['ID','Subject','Conflicting claims','Sources','Treatment','Consequence'],D.conflicts,'ConflictsTable');

const s=setup('Subsystems',[75,240,180,400,140,400,180,180,125,250,190,420],'Source-labelled satellite design','Published design and requirement values are not demonstrated LUMIO flight performance.');
table(s,7,['Claim','Area','Parameter','Value / architecture','Unit','Conditions','Epoch','Evidence status','Sources','Location','Confidence','Public gap'],D.claims,'ClaimsTable');

const sm=setup('SMD comparison',[75,360,340,370,440,135],'LUMIO and SMD across D01-D10','SMD whole-surface coverage and event-camera premise are fixed; numerical choices remain TBR.');
table(sm,7,['Driver','LUMIO comparator','SMD status','Consequence','Next evidence','Sources'],D.comparison,'ComparisonTable');

const x=setup('Calculations',[210,160,180,210,230,220,230,220],'Analytic comparison and source budget audit','Amber inputs are editable. Geometry, ideal integration and arithmetic only; no new trajectory or calibrated sensor model.');
x.tabColor='#738CA6';
const inputs=[
 ['Moon radius',I.moon_radius_km,'km','Spherical calculation convention'],
 ['Camera field',I.field_of_view_deg,'deg total','L06 Table3'],
 ['Pixels per side',I.pixels_per_side,'pixels','L06 Table2'],
 ['Year convention',I.year_days,'days','Declared conversion'],
 ['Synodic month convention',I.synodic_month_days,'days','Declared conversion, not halo period'],
 ['Science window fraction',I.science_duty_fraction,'fraction','Ideal half-cycle L02/L21'],
 ['Mean dark area / surface',I.published_mean_dark_surface_fraction,'fraction','L18 p14 footnote21'],
 ['Terrain obstruction',I.published_obstruction_fraction,'fraction','L18 p14 assumption'],
 ['Frames per flash',I.frames_per_flash,'count','L18 p4'],
 ['Channels',I.channels,'count','L18 p4'],
 ['Tile side',I.tile_side_pixels,'pixels','L18 p4'],
 ['Bits per pixel',I.bits_per_pixel,'bit','L18 p4'],
 ['Annual model count',I.model_annual_detections,'count','L18 Table9, not observed'],
 ['Trial decay time',10,'ms','Illustration; table below also varies tau'],
 ['Trial population CV',I.trial_population_cv,'ratio','Study assumption'],
 ['Mean relative error',I.trial_mean_relative_error,'fraction','Planning example'],
 ['Two-group difference',I.trial_two_group_effect,'fraction of mean','Planning example'],
 ['Two-group sigma',I.trial_two_group_sigma,'sigma','Large-sample approximation'],
 ['Available array power',I.power_available_W,'W','L05 Table6-4'],
 ['Science power, margined',I.power_science_margined_W,'W','L05 Table6-4'],
 ['Printed science margin',I.power_science_printed_margin_W,'W','L05 Table6-4, not reconciled'],
 ['Maneuver power',I.power_maneuver_margined_W,'W','L05 Table6-4'],
 ['Battery nameplate',I.battery_nameplate_Wh,'Wh','L05 section6.3, usable capacity unknown'],
 ['Early integration window',I.early_window_ms,'ms','Study observable, not selected requirement']
];
table(x,7,['Input','Value','Unit','Basis'],inputs,'InputsTable');x.getRange('B8:B31').format.fill='#FFF0CE';fmt(x,'B8:B31','0.000');
section(x,32,'Geometry: centre distance and target range remain distinct');
table(x,34,['Centre (km)','Nadir range (km)','Disc (deg)','Sampling (arcsec/pix)','Nadir (km/pix)','Visible fraction','Model','Source'],R.geometry.map(r=>[r.centre_km,null,null,null,null,null,'Sphere; near nadir only','L06/L18; radius convention']),'GeometryTable');
for(let r=35;r<=38;r++)x.getRange(`B${r}:F${r}`).formulas=[[`=A${r}-$B$8`,`=2*ASIN($B$8/A${r})*180/PI()`,`=$B$9/$B$10*3600`,`=B${r}*TAN($B$9/$B$10*PI()/180)`,`=(1-$B$8/A${r})/2`]];
fmt(x,'A35:B38','0.0');fmt(x,'C35:E38','0.000');fmt(x,'F35:F38','0.00%');
section(x,42,'Operations and rough exposure: not a coverage or completeness map');
table(x,44,['Additional availability','Lunations / year','Science windows (h)','Dark area (km2)','Area-time (km2 h)','Whole-surface-years','Interpretation','Source'],R.exposure.map(r=>[r.additional_availability,null,null,null,null,null,'Obstruction applied once; no Pd','L18 p14; half-cycle plan']),'ExposureTable');
for(let r=45;r<=47;r++)x.getRange(`B${r}:F${r}`).formulas=[[`=$B$11/$B$12`,`=$B$11*24*$B$13*A${r}`,`=4*PI()*$B$8^2*$B$14`,`=C${r}*D${r}*(1-$B$15)`,`=E${r}/(4*PI()*$B$8^2*$B$11*24)`]];
fmt(x,'A45:A47','0%');fmt(x,'B45:C47','0.00');fmt(x,'D45:E47','0.00E+00');fmt(x,'F45:F47','0.000');x.getRange('A45:A47').format.fill='#FFF0CE';
section(x,50,'Exponential integration at identical incident signal: no noise or sensor response');
table(x,52,['Decay tau (ms)','Integration T (ms)','Peak best / true','Peak worst / true','First 5 ms fraction','Total energy','Status','Basis'],R.temporal.map(r=>[r.decay_ms,r.integration_ms,null,null,null,'Preserved if all no-gap bins kept','SMD 1/5 ms bins are assumptions','Analytic exponential; L06/L18 windows']),'TemporalTable');
for(let r=53;r<=72;r++)x.getRange(`C${r}:E${r}`).formulas=[[`=A${r}/B${r}*(1-EXP(-B${r}/A${r}))`,`=C${r}/(2-EXP(-B${r}/A${r}))`,`=1-EXP(-$B$31/A${r})`]];
fmt(x,'C53:E72','0.0000');
section(x,75,'Counting uncertainty: systematic and selection uncertainty excluded');
table(x,77,['Count','Poisson relative error','Meaning','Source'],R.statistics.map(r=>[r.count,null,'Independent Poisson counts only','L20 criteria / L18 predictions']),'StatisticsTable');
for(let r=78;r<=83;r++)x.getRange(`B${r}`).formulas=[[`=1/SQRT(A${r})`]];fmt(x,'B78:B83','0.00%');
section(x,86,'Data volume and illustrative sample sizing');
table(x,88,['Quantity','Result','Unit','Interpretation'],[
 ['Tile product',null,'bit/flash','No headers/compression; L18 p4'],
 ['Annual retained science',null,'Gbit/year','Model count only; no overhead'],
 ['Two-channel raw stream',null,'Mbit/s at 15 fps','Encoding assumption, not measured interface'],
 ['Two-channel raw stream',null,'TB/day decimal','Assumes continuous full frames'],
 ['Trial sample mean',null,'useful events','CV / sqrt(N), not mission criterion'],
 ['Trial two-group mean',null,'events per group','20% effect at 3 sigma if CV=1'],
 ['Range signal factor',null,'near / far','Same source at sub-spacecraft point'],
 ['Trial onset-aligned peak',null,'ratio','66 ms integration; uses trial decay input']
],'DerivedTable');
x.getRange('B89:B96').formulas=[['=$B$18^2*$B$16*$B$17*$B$19'],['=B89*$B$20/10^9'],['=$B$10^2*$B$17*$B$19*15/10^6'],['=B91*10^6/8*86400/10^12'],['=ROUNDUP(($B$22/$B$23)^2,0)'],['=ROUNDUP(2*($B$25*$B$22/$B$24)^2,0)'],['=(B38/B36)^2'],['=$B$21/66*(1-EXP(-66/$B$21))']];fmt(x,'B89:B96','0.000');
section(x,99,'Source arithmetic diagnostics: discrepancies do not prove flight infeasibility');
table(x,101,['Quantity','Value','Unit','Source / condition'],[
 ['PL margined',4.8,'kg','L05 Table6-3'],['OBPDP',.25,'kg','L05 Table6-3'],['COMM',1.43,'kg','L05 Table6-3'],['EPS',4.27,'kg','L05 Table6-3'],['OBC',.56,'kg','L05 Table6-3'],['ADCS',2.13,'kg','L05 Table6-3'],['PS',5.34,'kg','L05 Table6-3'],['TCS',.21,'kg','L05 Table6-3'],['Structure',4.29,'kg','L05 Table6-3'],
 ['Sum subsystem lines',null,'kg','Does not equal printed 23.41 kg subtotal'],
 ['Printed total components',null,'kg','23.41 + 2.34 + 1.17 + 1.77'],
 ['Science headroom',null,'W','Available less science margined load'],
 ['Difference to printed margin',null,'W','Headroom less printed 6.59 W'],
 ['Maneuver shortfall',null,'W','Transient deficit; no duration/SOC closure'],
 ['Ideal battery at shortfall',null,'minutes','Nameplate only; no reserve/loss/EOL'],
 ['Delta-v deterministic + stochastic + margins',null,'m/s','L05 Table4-1; reproduced line sum']
],'AuditTable');
x.getRange('B111:B116').formulas=[['=SUM(B102:B110)'],['=23.41+2.34+1.17+1.77'],['=$B$26-$B$27'],['=B113-$B$28'],['=$B$29-$B$26'],['=$B$30/B115*60']];
x.getRange('B117').formulas=[['=SUM(40.85,10.22,2.55,7.08,0.35,0.32,0.06,0.02,15.79,0.79,0.97,0.05)']];
// Visible original budget inputs, kept separate from the audit results.
section(x,120,'Original Phase-B delta-v table: L05 Table4-1 p8');
table(x,122,['Maneuver','Deterministic (m/s)','Stochastic 3-sigma (m/s)','Margin (m/s)'],I.delta_v_budget_rows_ms.map((r,i)=>[['DSM1-8','TCM1-7','HIM','1-year stationkeeping','Disposal'][i],...r]),'DeltaVInputs');
x.getRange('B117').formulas=[['=SUM(B123:D127)']];
x.getRange('F102:G106').values=[['Printed mass inputs (kg)',null],['Dry subtotal',I.mass_printed_dry_subtotal_kg],['System margin',I.mass_system_margin_kg],['Harness',I.mass_harness_kg],['Propellant',I.mass_propellant_kg]];
x.getRange('F102:G106').format.wrapText=true;x.getRange('F102:G106').format.rowHeight=35;
x.getRange('B112').formulas=[['=SUM(G103:G106)']];
// Source data rows above end at 117; headline follows the actual delta-v result.
c.getRange('B25').formulas=[["='Calculations'!B117"]];fmt(x,'B102:B117','0.000');

const ev=setup('Evidence',[80,340,250,220,350,300,520,440],'Primary evidence and access limitations','All reviewed 29 October 2026. URLs and exact claim locations are retained; generic vendor capability is not mission selection.');
table(ev,7,['ID','Source','Publication / event date','Configuration epoch','Location','Evidence type','URL / DOI','Limitation'],D.sources,'EvidenceTable');

wb.recalculate();
const checks=[];
function check(name,actual,expected,tol=1e-8){if(typeof actual!=='number'||Math.abs(actual-expected)>tol)throw Error(`${name}: ${actual} != ${expected}`);checks.push({name,actual,expected});}
check('science hours',x.getRange('C45').values[0][0],R.headline.ideal_science_hours);
check('annual Gbit',x.getRange('B90').values[0][0],14.8);
check('trial mean N',x.getRange('B93').values[0][0],100);
check('trial group N',x.getRange('B94').values[0][0],450);
check('delta-v',x.getRange('B117').values[0][0],79.05);
check('mass lines',x.getRange('B111').values[0][0],23.28);
check('power headroom',x.getRange('B113').values[0][0],9.82);
for(let i=0;i<R.geometry.length;i++)check(`disc ${i}`,x.getRange(`C${35+i}`).values[0][0],R.geometry[i].disc_deg);
x.getRange('B13').values=[[.4]];wb.recalculate();check('duty input change',x.getRange('C45').values[0][0],3506.4);
x.getRange('B13').values=[[.5]];wb.recalculate();check('duty restored',x.getRange('C45').values[0][0],4383);
x.getRange('B21').values=[[20]];wb.recalculate();check('decay input change',x.getRange('B96').values[0][0],20/66*(1-Math.exp(-66/20)));
x.getRange('B21').values=[[10]];wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A',options:{useRegex:true,maxResults:100},maxChars:5000});
await fs.writeFile(path.join(PRE,'formula_error_scan.ndjson'),errors.ndjson);
const inspect=await wb.inspect({kind:'region',sheetId:'Calculations',range:'A88:D96',maxChars:5000,tableMaxRows:9,tableMaxCols:4});
await fs.writeFile(path.join(PRE,'key_calculations.ndjson'),inspect.ndjson);
for(const [name,range] of [['Conclusions','A7:E14'],['Mission criteria','A7:H12'],['Design history','A25:F31'],['Subsystems','A7:F12'],['SMD comparison','A7:F11'],['Calculations','A32:H38'],['Evidence','A7:F11'],['Calculations','A50:H57'],['Calculations','A86:D96'],['Calculations','A110:D117']]){
 const preview=await wb.render({sheetName:name,range,scale:1.1,format:'png'});
 const key=name.replaceAll(' ','_')+'_'+range.split(':')[0];
 await fs.writeFile(path.join(PRE,key+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
await(await SpreadsheetFile.exportXlsx(wb)).save(path.join(OUT,'lumio_comparison_research.xlsx'));
await fs.writeFile(path.join(H,'workbook_validation.json'),JSON.stringify({status:'passed',engine:'artifact-tool',sheets:names,checks,native_excel:'Not tested',visual_review:'See preview images and final validation record'},null,2)+'\n');
console.log(JSON.stringify({sheets:names.length,checks:checks.length,output:'lumio_comparison_research.xlsx'}));
