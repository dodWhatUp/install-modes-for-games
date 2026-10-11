/* Read-only checks over exact native-file projections. No input events or network. */
(function(root){
'use strict';
const SIDES={'Left Ctrl':'ControlLeft','Right Ctrl':'ControlRight','Left Shift':'ShiftLeft','Right Shift':'ShiftRight','Left Alt':'AltLeft','Right Alt':'AltRight'};
function availability(data,family,bank,keys){
 const map=data.design.variants[family].maps[bank],projection=data.nativeRealizations?.[family]?.[bank];
 const outputs=new Set([...Object.values(map),'W','A','S','D']);
 const missing=[],unknown=[];
 for(const key of keys){
  if(key.startsWith('Mouse '))continue; // Delegation to the other hand is not physical verification.
  if(SIDES[key]){
   if(!projection)unknown.push(key);
   else if(!Object.values(projection).some(p=>p.types[0]==='1'&&p.meta.includes(SIDES[key])))missing.push(key);
  }else if(!outputs.has(key))missing.push(key);
 }
 return {missing,sideUnknown:unknown,allCodesPresent:missing.length===0&&unknown.length===0,runtimeVerified:false};
}
function review(data,family,bank,cell,includeTools=false){
 const findings=[];
 for(const e of cell.labels)for(const v of e.matchingVariants){
  const a=availability(data,family,bank,v);
  if(a.missing.length)findings.push({kind:'MISSING_CODE_OR_MODIFIER_SIDE',detail:a.missing.join(' + '),action:e.action});
  if(a.sideUnknown.length)findings.push({kind:'MODIFIER_SIDE_NOT_ESTABLISHED',detail:a.sideUnknown.join(' + '),action:e.action});
 }
 const selector=data.design.variants[family].selectors[bank];
 if(bank!=='BASIC'&&[28,30].includes(selector))findings.push({kind:'THUMB_SELECTOR',detail:String(selector)});
 if(cell.nativeId===31&&cell.key==='T')findings.push({kind:'T_ON_THUMB',detail:'31'});
 if(includeTools&&data.graphicsPolicy?.possibleOwners?.[cell.key]){
  findings.push({kind:'POSSIBLE_TOOL_OVERLAP_NOT_LIVE',detail:data.graphicsPolicy.possibleOwners[cell.key],source:data.graphicsPolicy.source});
 }
 return findings;
}
root.AtlasChecks={availability,review};
if(typeof module!=='undefined')module.exports=root.AtlasChecks;
})(typeof window!=='undefined'?window:globalThis);
