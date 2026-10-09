import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

// Reusable authoring source. All workbook creation uses @oai/artifact-tool.
const input = process.argv[2] || './catalogue_view.json';
const outputDir = process.argv[3] || './derived';
const d = JSON.parse(await fs.readFile(input, 'utf8'));
await fs.mkdir(outputDir, { recursive: true });
const wb = Workbook.create();
const names = ['Overview', 'Key Coverage', 'Games', 'Bindings', 'Alias Presence', 'Sources'];
const sheets = Object.fromEntries(names.map(n => [n, wb.worksheets.add(n)]));
const C = { ink:'#203247', navy:'#233D59', blue:'#DCE8F3', light:'#F3F6F9', accent:'#446B96', amber:'#FFF2CF', muted:'#576575', line:'#BACBDC' };
const safe = v => typeof v === 'string' && v.startsWith('=') ? "'" + v : v ?? '';
const text = v => Array.isArray(v) ? v.join('; ') : v && typeof v === 'object' ? JSON.stringify(v) : v ?? '';
const col = n => { let s=''; for(n++;n;n=Math.floor((n-1)/26)) s=String.fromCharCode(65+(n-1)%26)+s; return s; };
const games = [...d.games].sort((a,b)=>a.genre_family.localeCompare(b.genre_family)||a.title.localeCompare(b.title));
const gm = new Map(games.map(g=>[g.game_id,g]));
const genres = Object.keys(d.summary.game_counts_by_genre_family);
const evidence = Object.keys(d.summary.game_counts_by_evidence_family);
function base(s, lastRow, lastCol) {
  s.showGridLines = false;
  s.getRange(`A1:${col(lastCol-1)}${lastRow}`).format = {font:{name:'Arial',size:10,color:C.ink},verticalAlignment:'center'};
  s.getRange(`A1:${col(lastCol-1)}${lastRow}`).format.rowHeight=25;
}
function table(s, headers, rows, widths, tableName) {
  const end=rows.length+4;
  base(s,end,headers.length);
  s.getRange('A2').values=[[s.name]];
  s.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:C.navy};
  s.getRange(`A4:${col(headers.length-1)}${end}`).values=[headers,...rows].map(r=>r.map(safe));
  s.getRange(`A4:${col(headers.length-1)}4`).format={fill:C.navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};
  s.getRange(`A4:${col(headers.length-1)}4`).format.rowHeight=37;
  widths.forEach((w,i)=>s.getRange(`${col(i)}1:${col(i)}${end}`).format.columnWidth=w);
  const t=s.tables.add(`A4:${col(headers.length-1)}${end}`,true,tableName);
  t.style='TableStyleMedium2';
  t.showFilterButton=true;
  s.freezePanes.freezeRows(4);
  s.freezePanes.freezeColumns(1);
  return end;
}
const aliasMap = new Map();
for(const p of d.keyboard_key_presence){
  const k=p.game_id+'\u0000'+p.physical_alias;
  if(!aliasMap.has(k)) aliasMap.set(k,{game_id:p.game_id,alias:p.physical_alias,exact:new Set(),ids:new Set()});
  const a=aliasMap.get(k); a.exact.add(p.keyboard_key); p.binding_ids.forEach(id=>a.ids.add(id));
}
const aliases=[...new Set([...aliasMap.values()].map(a=>a.alias))];
const aliasCounts=new Map(aliases.map(a=>[a,[...aliasMap.values()].filter(p=>p.alias===a).length]));
aliases.sort((a,b)=>aliasCounts.get(b)-aliasCounts.get(a)||a.localeCompare(b));
const presence=[...aliasMap.values()].sort((a,b)=>a.alias.localeCompare(b.alias)||gm.get(a.game_id).title.localeCompare(gm.get(b.game_id).title));
const pend=table(sheets['Alias Presence'],['Game ID','Game / scoped edition','Genre family','Evidence family','Physical alias','Exact documented keys','Supporting binding IDs'],presence.map(p=>[p.game_id,gm.get(p.game_id).title,gm.get(p.game_id).genre_family,gm.get(p.game_id).evidence_family,p.alias,[...p.exact].sort().join('; '),[...p.ids].join('; ')]),[23,42,29,43,19,27,75],'AliasPresenceTable');
sheets['Alias Presence'].getRange('A3').values=[['One row per game and physical alias. Left/right modifier detail remains in the exact-key column.']];

const brows=d.bindings.map(b=>{
  const g=gm.get(b.game_id),o=b.observed,a=b.analyst_classification,p=b.parsed_key_presence;
  return [g.title,g.genre_family,b.game_id,o.action,o.key_expression,o.context,a.urgency_raw,a.held_or_repeat_raw,text(b.raw_binding.notes),p.status,text(p.keyboard_keys_exact),text(p.keyboard_physical_aliases),text(p.mouse_inputs),text(p.issues),text(p.transformations),b.source_id,'',o.source_url,b.binding_id,JSON.stringify(b.raw_binding)];
});
const bend=table(sheets.Bindings,['Game / scoped edition','Genre family','Game ID','Action','Original key expression','Context','Urgency — analyst','Hold / repeat — source or analyst','Original notes','Parser status','Exact keyboard keys','Physical aliases','Mouse inputs','Parser issues','Parser transformations','Source ID','','Source URL','Binding ID','Original binding JSON'],brows,[40,29,23,35,34,28,31,44,70,18,42,42,30,55,55,23,3,80,24,90],'BindingsTable');
sheets.Bindings.getRange('A3').values=[['Original expressions preserve chords, sequences and ranges. Urgency is judgment, not measured use.']];
sheets.Bindings.getRange(`A5:P${bend}`).format.wrapText=true;
sheets.Bindings.getRange(`A5:T${bend}`).format.rowHeight=46;
sheets.Bindings.getRange(`J5:J${bend}`).conditionalFormats.add('containsText',{text:'partial',format:{fill:C.amber}});
sheets.Bindings.getRange(`J5:J${bend}`).conditionalFormats.add('containsText',{text:'unparsed',format:{fill:'#FBE4DF'}});

const grows=games.map(g=>{const r=g.raw_metadata;return [g.title,g.genre_family,r.subgenre||'',g.evidence_family,0,r.platform_scope||r.coverage||'',r.source_snapshot_date||r.retrieval_date||'',r.evidence_note||'',text(g.source_ids),'',text(r.source_urls),g.game_id,JSON.stringify(r)];});
const gend=table(sheets.Games,['Game / scoped edition','Genre family','Subgenre','Evidence family','Binding rows','Edition / platform scope','Source / retrieval date','Evidence qualification','Source IDs','','Source URLs','Game ID','Original metadata JSON'],grows,[43,29,36,43,16,58,24,95,42,3,85,23,100],'GamesTable');
sheets.Games.getRange(`E5:E${gend}`).formulas=games.map((g,i)=>[`=COUNTIFS('Bindings'!$C$5:$C$${bend},$L${i+5})`]);
sheets.Games.getRange(`E5:E${gend}`).setNumberFormat('#,##0');
sheets.Games.getRange(`A5:M${gend}`).format.rowHeight=46;
sheets.Games.getRange(`A5:I${gend}`).format.wrapText=true;
sheets.Games.getRange('A3').values=[['Each row is a game or explicitly scoped edition. Published controls do not establish current installed defaults.']];

const srcRows=d.sources.map(s=>{const linked=games.filter(g=>g.source_ids.includes(s.source_id));return [s.source_id,linked.map(g=>g.title).join('; '),[...new Set(linked.map(g=>g.evidence_family))].join('; '),0,'',s.url];});
const send=table(sheets.Sources,['Source ID','Games using source','Game evidence families','Binding rows','','Source URL'],srcRows,[25,66,55,16,3,110],'SourcesTable');
sheets.Sources.getRange(`D5:D${send}`).formulas=srcRows.map((s,i)=>[`=COUNTIFS('Bindings'!$P$5:$P$${bend},$A${i+5})`]);
sheets.Sources.getRange(`B5:C${send}`).format.wrapText=true;
sheets.Sources.getRange(`A5:F${send}`).format.rowHeight=42;
sheets.Sources.getRange('A3').values=[['Sources are unique URLs; evidence classifications belong to each game record. A supporting URL can have zero binding rows.']];

const kc=sheets['Key Coverage'];
const kheaders=['Physical key alias','Games with key','Share of 74 games',...genres,...evidence];
const kend=table(kc,kheaders,aliases.map(a=>[a,...Array(kheaders.length-1).fill(0)]),[24,18,20,...genres.map(()=>23),...evidence.map(()=>29)],'KeyCoverageTable');
kc.tabColor=C.accent;
kc.getRange('A3').values=[['Documented constituent-key presence in this sample. Counts include modifiers in chords and do not measure press frequency.']];
kc.getRange('A4:O4').format.rowHeight=53;
const kformulas=aliases.map((a,i)=>{const r=i+5;return [
  `=COUNTIFS('Alias Presence'!$E$5:$E$${pend},$A${r})`,
  `=B${r}/'Overview'!$B$5`,
  ...genres.map((_,j)=>`=COUNTIFS('Alias Presence'!$E$5:$E$${pend},$A${r},'Alias Presence'!$C$5:$C$${pend},${col(j+3)}$4)`),
  ...evidence.map((_,j)=>`=COUNTIFS('Alias Presence'!$E$5:$E$${pend},$A${r},'Alias Presence'!$D$5:$D$${pend},${col(j+3+genres.length)}$4)`)
]});
kc.getRange(`B5:${col(kheaders.length-1)}${kend}`).formulas=kformulas;
kc.getRange(`B5:${col(kheaders.length-1)}${kend}`).setNumberFormat('#,##0');
kc.getRange(`C5:C${kend}`).setNumberFormat('0.0%');

const ov=sheets.Overview;
base(ov,47,9); ov.tabColor=C.navy;
[37,15,15,4,45,17,25,21,18].forEach((w,i)=>ov.getRange(`${col(i)}1:${col(i)}47`).format.columnWidth=w);
ov.getRange('A2').values=[['Azeron keyboard research']];
ov.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:C.navy};
ov.getRange('A3:I3').format.borders={bottom:{style:'thin',color:C.line}};
ov.getRange('A4:B4').values=[['Research scope','Count']];
ov.getRange('A5:A8').values=[['Games / scoped editions'],['Source binding rows'],['Registered supporting URLs'],['Physical aliases represented']];
ov.getRange('B5:B8').formulas=[
  [`=COUNTA('Games'!$L$5:$L$${gend})`],
  [`=COUNTA('Bindings'!$S$5:$S$${bend})`],
  [`=COUNTA('Sources'!$A$5:$A$${send})`],
  [`=COUNTA('Key Coverage'!$A$5:$A$${kend})`]
];
ov.getRange('B5:B8').setNumberFormat('#,##0');
ov.getRange('A9').values=[['Direct binding-source URLs']];
ov.getRange('B9').formulas=[[`=COUNTIFS('Sources'!$D$5:$D$${send},">0")`]];
ov.getRange('B9').setNumberFormat('#,##0');
ov.getRange('E4:F4').values=[['Evidence family','Games']];
ov.getRange('E5:E8').values=evidence.map(x=>[x]);
ov.getRange('F5:F8').formulas=evidence.map((_,i)=>[`=COUNTIFS('Games'!$D$5:$D$${gend},E${i+5})`]);
ov.getRange('A11:C11').values=[['Genre family','Games','Binding rows']];
ov.getRange('A12:A19').values=genres.map(x=>[x]);
ov.getRange('B12:C19').formulas=genres.map((_,i)=>[`=COUNTIFS('Games'!$B$5:$B$${gend},$A${i+12})`,`=COUNTIFS('Bindings'!$B$5:$B$${bend},$A${i+12})`]);
ov.getRange('A20').values=[['Total']];ov.getRange('B20:C20').formulas=[['=SUM(B12:B19)','=SUM(C12:C19)']];
ov.getRange('A20:C20').format={font:{bold:true},borders:{top:{style:'thin',color:C.line}}};
ov.getRange('E11:F11').values=[['Expression parser','Rows']];
ov.getRange('E12:E14').values=[['fully_parsed'],['partial'],['unparsed']];
ov.getRange('F12:F14').formulas=['fully_parsed','partial','unparsed'].map((_,i)=>[`=COUNTIFS('Bindings'!$J$5:$J$${bend},E${i+12})`]);
ov.getRange('E16').values=[['Key presence is a sample count.']];
ov.getRange('E17').values=[['It does not measure usage or urgency.']];
ov.getRange('E18').values=[['Editions and historical sources are labeled.']];
ov.getRange('E19').values=[['40 candidate records are excluded from counts.']];
ov.getRange('E16:I19').format.font={name:'Arial',size:10,color:C.muted};
ov.getRange('A23').values=[['Provisional four-layer concept']];
ov.getRange('A23').format.font={name:'Arial',size:14,bold:true,color:C.navy};
ov.getRange('A25:C25').values=[['Layer','Role','Priority']];
ov.getRange('A26:C29').values=[['Base','Fast / held','Direct'],['Numbers and symbols','Ordered keys','Deliberate'],['Menu letters','UI / menus','Deliberate'],['Function keys / navigation','Tools / UI','Check urgency']];
ov.getRange('E25').values=[['Conservative starting change']];
ov.getRange('E25').format.font={bold:true};
ov.getRange('E26').values=[['Move M / I / J / Home to their existing layers.']];
ov.getRange('E27').values=[['Use those four Base positions for 1 / 2 / 3 / 4.']];
ov.getRange('E28').values=[['Preserve 25 outputs, three selectors, two blanks.']];
ov.getRange('E29').values=[['Consider 5 / 6 after verifying physical comfort.']];
ov.getRange('A32').values=[['Rules that override grouping']];ov.getRange('A32').format.font={name:'Arial',size:14,bold:true,color:C.navy};
const notes=[
  'Urgency, simultaneous holds and reach take priority over frequency and keyboard category.',
  'Numbers, F keys and arrows can control combat. Provide direct access when the game requires it.',
  'Keep raw Shift / Ctrl / Alt, layer selector positions and joystick behavior consistent.',
  'A 150 ms V tap / hold selector is a historical preference; software v2 timing remains unverified.',
  'Four layers are a compact starting recommendation, not a proven universal minimum.',
  'Add a Hotbar or Grid base only for a demonstrated need. Those may be distinct alternatives.',
  'A layer emits the same raw F key. It does not prevent a game and graphics add-on both responding.',
  'Partial and unparsed expressions retain their original text. Constituent-key counts lose chord order.',
  'Left / right modifiers collapse only in the coverage view. Exact labels remain in Bindings and Alias Presence.',
  'The full JSON preserves the source structure. The workbook retains every one of the 1,747 original binding rows.'
];
ov.getRange('A34:A43').values=notes.map(n=>[n]);
ov.getRange('A34:I43').format.font={name:'Arial',size:10,color:C.muted};
for(const r of ['A4:B4','E4:F4','A11:C11','E11:F11','A25:C25']) ov.getRange(r).format={fill:C.navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center'};
ov.getRange('A26:C29').format.rowHeight=30;
ov.getRange('B5:B8').format.font={name:'Arial',size:14,bold:true,color:C.navy};

wb.recalculate();
const overviewCheck=await wb.inspect({kind:'table',range:'Overview!A4:F20',include:'values,formulas',tableMaxRows:17,tableMaxCols:6,maxChars:4500});
const keyCheck=await wb.inspect({kind:'table',range:'Key Coverage!A4:F11',include:'values,formulas',tableMaxRows:8,tableMaxCols:6,maxChars:3500});
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan',maxChars:1500});
console.log(overviewCheck.ndjson);console.log(keyCheck.ndjson);console.log(errors.ndjson);
const headline=ov.getRange('B5:B8').values.flat();
if(headline[0]!==74||headline[1]!==1747||headline[2]!==78||headline[3]!==aliases.length) throw new Error('Headline reconciliation failed: '+JSON.stringify(headline));
if(ov.getRange('B9').values[0][0]!==76) throw new Error('Direct source count reconciliation failed');
const calculated=kc.getRange(`B5:B${kend}`).values.flat();
calculated.forEach((v,i)=>{if(v!==aliasCounts.get(aliases[i])) throw new Error('Alias count mismatch for '+aliases[i]);});
const renders=[];
for(const [name,range,file] of [
  ['Overview','A1:I44','overview.png'],
  ['Key Coverage','A1:F11','key_coverage.png'],
  ['Games','A1:E9','games.png'],
  ['Bindings','A1:H9','bindings.png'],
  ['Alias Presence','A1:F9','alias_presence.png'],
  ['Sources','A1:D9','sources.png']
]){
  const preview=await wb.render({sheetName:name,range,scale:1.4,format:'png'});
  const path=`${outputDir}/${file}`;await fs.writeFile(path,new Uint8Array(await preview.arrayBuffer()));renders.push(path);
}
const output=await SpreadsheetFile.exportXlsx(wb);
const outputPath=`${outputDir}/Azeron_Game_Bindings_Step1.xlsx`;
await output.save(outputPath);
await fs.writeFile(`${outputDir}/workbook_verification.json`,JSON.stringify({outputPath,games:games.length,bindings:brows.length,sources:srcRows.length,aliasPresenceRows:presence.length,aliases:aliases.length,headline,allAliasCountsMatched:true,renderPaths:renders,formulaErrorScan:errors.ndjson,checks:[overviewCheck.ndjson,keyCheck.ndjson]},null,2));
console.log(JSON.stringify({outputPath,games:games.length,bindings:brows.length,aliases:aliases.length,aliasPresenceRows:presence.length,renders}));
