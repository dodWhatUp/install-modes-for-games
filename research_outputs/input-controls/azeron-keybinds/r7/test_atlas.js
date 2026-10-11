'use strict';
/* Pure query/contract tests. These do not open a browser or operate a device. */
const fs=require('fs'),assert=require('assert'),crypto=require('crypto'),C=require('./atlas_core.js');
const html=fs.readFileSync(process.argv[2]||__dirname+'/Azeron_R7_Action_Atlas_HE.html','utf8');
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
 assert(C.requirements(a).all.includes('V + W'));assert(C.findAll(D,'COMPACT','alienisolation','*','Peek','*').length);
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
check('FT Space+1 is not presented as unqualified 1',()=>{const a=C.labels(D,'fairytail2','battle','1');assert(C.requirements(a).all.includes('Space + 1'));assert(C.sameBank(D,'COMPACT','BASIC',['Space','1']));assert(!C.sameBank(D,'COMPACT','NUMBERS',['Space','1']));});
check('XCOM range scope includes 0',()=>{assert(C.labels(D,'xcom2','Tactical','0').some(e=>e.action==='Ability slots'&&e.parsing_override));});
check('F2 OpenTTD displays full chord',()=>{const a=C.labels(D,'openttd','UI','F2');assert(C.requirements(a).all.includes('Shift + F2'));});
check('side distinction retained in source',()=>{const a=C.labels(D,'fairytail2','battle','Ctrl');assert(a.some(e=>e.matchingVariants.some(v=>v.includes('Left Ctrl'))));});
check('pending selected games remain unknown',()=>{for(const g of D.actions.games.filter(x=>x.status==='KEY_TABLE_PENDING'))assert(C.cells(D,'COMPACT','BASIC',g.id,'*').every(c=>c.labels.length===0));});
check('unrecognized game is not inferred',()=>{assert(C.labels(D,'unseen','*','E').length===0);});
check('layer selector is not a game action',()=>{assert(C.labels(D,'warframe','*','LAYER:NUMBERS').length===0);assert(C.labels(D,'warframe','*','UNASSIGNED').length===0);});
check('layer targets display reciprocal base correctly',()=>{
 const a=C.cells(D,'SPARSE','NAV','skyrim-original','*');assert.equal(a.find(x=>x.nativeId===28).layerTarget,'BASIC');
});
check('source-backed category and Hebrew search',()=>{const a=C.findAll(D,'COMPACT','skyrim-original','*','קפיצה','movement');assert(a.some(c=>c.key==='Space'));assert(!C.findAll(D,'COMPACT','skyrim-original','*','קפיצה','weapons').length);});
check('filters do not create bindings',()=>{assert.equal(C.cells(D,'SPARSE','MENUS','skyrim-original','*','Invent','menus').length,29);});
check('required blanks remain source-disabled',()=>{for(const [bank,ids]of Object.entries(D.design.source_sensitive_mask)){const a=C.cells(D,'SPARSE',bank,'skyrim-original','*');for(const id of ids)assert.equal(a.find(x=>x.nativeId===id).key,'UNASSIGNED');}});
check('no glyph without whitelist entry',()=>{for(const cat of Object.values(D.actions.categories))assert(D.icons[cat.icon]);});
check('JS query operations preserve native design byte semantics',()=>{assert.equal(digest(D.design),before);});
check('empty and unrelated searches',()=>{assert.equal(C.findAll(D,'COMPACT','skyrim-original','*','impossible123','*').length,0);});
const result={named_query_contract_tests:cases,design_semantic_hash_unchanged:true,game_targets:D.actions.games.length,source_game_samples:D.actions.games.filter(g=>g.status!=='KEY_TABLE_PENDING').length,reviewed_action_records:D.actions.entries.length,hidden_ids:[19,24],digital_controls_per_view:29,real_browser_tested:false,physical_tested:false,gameplay_tested:false};
fs.writeFileSync(__dirname+'/QA_ATLAS_LOGIC_R7.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
