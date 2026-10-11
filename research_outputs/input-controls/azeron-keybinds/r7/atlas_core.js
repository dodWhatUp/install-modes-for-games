/* Pure data queries for the display-only Action Atlas. No native input/storage. */
(function (root) {
'use strict';
const MOD=['Ctrl','Shift','Alt'], DIR=['W','A','S','D','Up Arrow','Down Arrow','Left Arrow','Right Arrow'];
function logical(k){return k.replace(/^(Left|Right) (Ctrl|Shift|Alt)$/,'$2');}
function anchor(v){
 const ks=v.map(logical);if(ks.length===1)return ks[0];
 // A held ordinary letter + direction belongs on that held letter; the stick is not drawn.
 const command=ks.filter(k=>!MOD.includes(k)&&!DIR.includes(k)&&!k.startsWith('Mouse '));
 if(command.length)return command[command.length-1];
 const modifier=ks.filter(k=>MOD.includes(k));if(modifier.length)return modifier[modifier.length-1];
 return ks[ks.length-1];
}
function labels(data,game,ctx,key){
 if(key==='UNASSIGNED'||key.startsWith('LAYER:'))return [];
 return data.actions.entries.filter(e=>e.game_id===game&&(ctx==='*'||e.context===ctx)).flatMap(e=>{
  const vs=e.variants.filter(v=>anchor(v)===key);
  return vs.length?[{...e,matchingVariants:vs}]:[];
 });
}
function categoryKey(ls){const c=[...new Set(ls.map(x=>x.category))];return c.length===1?c[0]:'unknown';}
function matches(ls,key,q,cat){
 if(cat!=='*'&&!ls.some(x=>x.category===cat))return false;
 const term=q.trim().toLocaleLowerCase();if(!term)return true;
 return [key,...ls.flatMap(e=>[e.action,e.context,e.category,(e.aliases||[]).join(' ')])].join(' ').toLocaleLowerCase().includes(term);
}
function cells(data,family,bank,game,ctx,q='',cat='*'){
 const map=data.design.variants[family].maps[bank];
 return Object.entries(map).filter(([p])=>data.design.position_map[p]!==19).map(([p,key])=>{
  const ls=labels(data,game,ctx,key),isLayer=key.startsWith('LAYER:');
  return {position:p,nativeId:data.design.position_map[p],key,labels:ls,
   category:isLayer?'system':categoryKey(ls),match:matches(ls,key,q,cat),
   layerTarget:isLayer?(bank==='BASIC'?key.slice(6):'BASIC'):null};
 });
}
function findAll(data,family,game,ctx,q,cat){
 return Object.keys(data.design.variants[family].maps).flatMap(bank=>cells(data,family,bank,game,ctx,q,cat)
  .filter(c=>c.match&&c.labels.length).map(c=>({...c,bank})));
}
function sameBank(data,family,bank,keys){
 const outs=new Set([...Object.values(data.design.variants[family].maps[bank]),'W','A','S','D']);
 return keys.every(k=>k.startsWith('Mouse ')||outs.has(logical(k)));
}
function requirements(ls){
 const chords=[...new Set(ls.flatMap(e=>e.matchingVariants.filter(v=>v.length>1).map(v=>v.join(' + '))))];
 return {all:chords,short:chords.slice(0,2).join(' / ')+(chords.length>2?' …':'')};
}
root.AtlasCore={logical,anchor,labels,matches,cells,findAll,sameBank,requirements};
if(typeof module!=='undefined')module.exports=root.AtlasCore;
})(typeof window!=='undefined'?window:globalThis);
