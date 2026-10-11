'use strict';
/* Pure query/contract tests. These do not open a browser or operate a device. */
const fs=require('fs'),assert=require('assert'),crypto=require('crypto'),C=require('./atlas_core.js');
const html=fs.readFileSync(process.argv[2]||__dirname+'/../Azeron_R8_Action_Atlas_HE.html','utf8');
const m=html.match(/<script id="atlas-data" type="application\/json">([\s\S]*?)<\/script>/);assert(m);
const D=JSON.parse(m[1]);let cases=0;const check=(name,fn)=>{fn();cases++;};
const digest=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');const before=digest(D.design);
check('maps and immutable hidden positions',()=>{
 for(const [family,v]of Object.entries(D.design.variants))for(const bank of Object.keys(v.maps)){
  const a=C.cells(D,family,bank,'skyrim-original','*');assert.equal(a.length,29);assert.equal(new Set(a.map(x=>x.nativeId)).size,29);
  assert(!a.some(x=>x.nativeId===19||x.nativeId===24));assert(a.some(x=>x.nativeId===36));assert(a.some(x=>x.nativeId===37));
  assert.equal(v.maps[bank].R3,'UNASSIGNED');
 }
});
check('game and search keep cell identity and output stable',()=>{
 for(const [f,v]of Object.entries(D.design.variants))for(const bank of Object.keys(v.maps)){
  const base=C.cells(D,f,bank,'skyrim-original','*').map(c=>[c.nativeId,c.position,c.key]);
  for(const g of D.actions.games)for(const ctx of ['*',...g.contexts]){
   const cells=C.cells(D,f,bank,g.id,ctx,'nothing-like-this','combat');
   assert.deepEqual(cells.map(c=>[c.nativeId,c.position,c.key]),base);
  }
 }
});
check('all source references and categories valid',()=>{
 const ids=new Set(D.actions.sources.map(x=>x.id));const games=new Set(D.actions.games.map(x=>x.id));
 assert.equal(new Set(D.actions.entries.map(x=>x.id)).size,D.actions.entries.length);
 for(const e of D.actions.entries){assert(ids.has(e.source_id));assert(games.has(e.game_id));assert(D.actions.categories[e.category]);assert(D.icons[e.icon]);assert.equal(e.effective_binding_verified,false);assert.equal(e.physical_tested,false);}
});
check('Skyrim scoped direct functions',()=>{
 assert(C.labels(D,'skyrim-original','*','Alt').some(e=>e.action==='Sprint'));
 assert(C.labels(D,'skyrim-original','*','Shift').some(e=>e.action==='Walk'));
 assert(C.labels(D,'skyrim-original','*','Slash').some(e=>e.action==='Skills menu'));
});
check('Tomb primary fire V additive discovery',()=>{assert(C.labels(D,'tombraider2013','combat','V').some(e=>e.action==='Primary fire'));});
check('Warframe versus Tomb E',()=>{
 assert(C.labels(D,'warframe','*','E').some(e=>e.action==='Melee attack'));
 assert(C.labels(D,'tombraider2013','*','E').some(e=>e.action==='Interact'));
});
check('Alien tracker is not jump',()=>{const a=C.labels(D,'alienisolation','*','Space');assert(a.some(e=>e.action==='Motion tracker'&&e.gesture==='hold'));assert(!a.some(e=>/jump/i.test(e.action)));});
check('held letter plus directions survives hidden joystick',()=>{
 const a=C.labels(D,'alienisolation','*','V');assert(a.some(e=>e.action==='Peek'));
 assert(C.requirements(a).all.includes('V + W'));assert(C.findAll(D,'CORE5','alienisolation','*','Peek','*').length);
});
check('Shift direction is annotated as a chord',()=>{const a=C.labels(D,'shadowtr','movement','Shift');assert(a.some(e=>e.action==='Sprint'));assert(C.requirements(a).all.includes('Shift + W'));});
check('context separates R weapon and menu roles',()=>{
 assert(C.labels(D,'skyrim-original','inventory','R').every(e=>e.action==='Drop item'));
 assert(C.labels(D,'skyrim-original','general gameplay','R').every(e=>e.action==='Ready/sheath'));
});
check('all-context mixed roles keep both labels',()=>{const a=C.labels(D,'skyrim-original','*','R');assert(a.some(e=>e.action==='Ready/sheath'));assert(a.some(e=>e.action==='Drop item'));});
check('FT context and held bank distinct',()=>{
 assert(C.labels(D,'fairytail2','field','Tab').some(e=>e.action==='Main menu'));
 assert(C.labels(D,'fairytail2','battle','Tab').some(e=>e.action==='Skill bank'&&e.gesture==='hold'));
});
check('FT Space+1 is not presented as unqualified 1',()=>{const a=C.labels(D,'fairytail2','battle','1');assert(C.requirements(a).all.includes('Space + 1'));assert(C.sameBank(D,'CORE5','BASIC',['Space','1']));assert(C.sameBank(D,'CORE5','NUMBERS',['Space','1']));});
check('XCOM range scope includes 0',()=>{assert(C.labels(D,'xcom2','Tactical','0').some(e=>e.action==='Ability slots'&&e.parsing_override));});
check('F2 OpenTTD displays full chord',()=>{const a=C.labels(D,'openttd','UI','F2');assert(C.requirements(a).all.includes('Shift + F2'));});
check('side distinction retained in source',()=>{const a=C.labels(D,'fairytail2','battle','Ctrl');assert(a.some(e=>e.matchingVariants.some(v=>v.includes('Left Ctrl'))));});
check('pending selected games remain unknown',()=>{for(const g of D.actions.games.filter(x=>x.status==='KEY_TABLE_PENDING'))assert(C.cells(D,'CORE5','BASIC',g.id,'*').every(c=>c.labels.length===0));});
check('unrecognized game is not inferred',()=>{assert(C.labels(D,'unseen','*','E').length===0);});
check('layer selector is not a game action',()=>{assert(C.labels(D,'warframe','*','LAYER:NUMBERS').length===0);assert(C.labels(D,'warframe','*','UNASSIGNED').length===0);});
check('layer targets display reciprocal base correctly',()=>{
 const a=C.cells(D,'SPARSE6','NAV','skyrim-original','*');assert.equal(a.find(x=>x.nativeId===28).layerTarget,'BASIC');
});
check('source-backed category and Hebrew search',()=>{const a=C.findAll(D,'CORE5','skyrim-original','*','קפיצה','movement');assert(a.some(c=>c.key==='Space'));assert(!C.findAll(D,'CORE5','skyrim-original','*','קפיצה','weapons').length);});
check('filters do not create bindings',()=>{assert.equal(C.cells(D,'SPARSE6','MENUS','skyrim-original','*','Invent','menus').length,29);});
check('required blanks remain source-disabled',()=>{for(const [bank,ids]of Object.entries(D.design.source_sensitive_mask)){const a=C.cells(D,'SPARSE6',bank,'skyrim-original','*');for(const id of ids)assert.equal(a.find(x=>x.nativeId===id).key,'UNASSIGNED');}});
check('no glyph without whitelist entry',()=>{for(const cat of Object.values(D.actions.categories))assert(D.icons[cat.icon]);});
check('JS query operations preserve native design byte semantics',()=>{assert.equal(digest(D.design),before);});
check('empty and unrelated searches',()=>{assert.equal(C.findAll(D,'CORE5','skyrim-original','*','impossible123','*').length,0);});
check('Bayonetta publisher scope count',()=>{assert.equal(D.actions.entries.filter(e=>e.game_id==='bayonetta-pc').length,29);});
check('Bayonetta Home depends on context',()=>{
 const m=C.labels(D,'bayonetta-pc','menus','Home'),g=C.labels(D,'bayonetta-pc','gameplay','Home');
 assert(m.some(e=>e.action==='Restore defaults'));assert(!g.some(e=>e.action==='Restore defaults'));assert(g.some(e=>e.action==='Camera up'));
});
check('Bayonetta lock-on is held',()=>{assert(C.labels(D,'bayonetta-pc','gameplay','Alt').some(e=>e.action==='Lock-on'&&e.gesture==='hold'));});
check('no invented Witch Time key',()=>{assert(!D.actions.entries.some(e=>e.game_id==='bayonetta-pc'&&e.action==='Witch Time'));});
check('category AND query match the same action',()=>{
 const ls=[{action:'Jump',context:'a',category:'movement',aliases:[]},{action:'Inventory',context:'b',category:'menus',aliases:[]}];
 assert(!C.matches(ls,'R','Jump','menus'));assert(C.matches(ls,'R','Jump','movement'));assert(C.matches(ls,'R','Inventory','menus'));
});
check('selected result only contains matched labels',()=>{
 const ls=[{action:'Jump',context:'a',category:'movement',aliases:[]},{action:'Inventory',context:'b',category:'menus',aliases:[]}];
 assert.deepEqual(C.eligibleLabels(ls,'R','Jump','movement').map(x=>x.action),['Jump']);
});
check('CORE number zero not moved to thumb',()=>{
 assert.equal(C.cells(D,'CORE5','NUMBERS','bayonetta-pc','gameplay').find(x=>x.nativeId===13).key,'0');
});
check('Ctrl Shift Space invariant all maps',()=>{
 for(const [family,v]of Object.entries(D.design.variants))for(const bank of Object.keys(v.maps)){
  const cs=C.cells(D,family,bank,'bayonetta-pc','gameplay');for(const [id,key]of [[5,'Ctrl'],[9,'Shift'],[14,'Space']])assert.equal(cs.find(c=>c.nativeId===id).key,key);
 }
});
check('SPARSE symbols bank retains return selector',()=>{assert.equal(C.cells(D,'SPARSE6','SYMBOLS','bayonetta-pc','menus').find(c=>c.nativeId===30).layerTarget,'BASIC');});
check('Alt no longer competes on thumb in Basic',()=>{for(const f of ['CORE5','SPARSE6'])assert.equal(C.cells(D,f,'BASIC','bayonetta-pc','gameplay').find(c=>c.nativeId===3).key,'Alt');});
check('source notes warn about menu reset',()=>{assert(C.labels(D,'bayonetta-pc','menus','Home')[0].notes.some(x=>/settings/.test(x)));});
const result={named_query_contract_tests:cases,design_semantic_hash_unchanged:true,game_targets:D.actions.games.length,source_game_samples:D.actions.games.filter(g=>g.status!=='KEY_TABLE_PENDING').length,reviewed_action_records:D.actions.entries.length,hidden_ids:[19,24],digital_controls_per_view:29,real_browser_tested:false,physical_tested:false,gameplay_tested:false};
fs.writeFileSync(__dirname+'/QA_ATLAS_R8.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
