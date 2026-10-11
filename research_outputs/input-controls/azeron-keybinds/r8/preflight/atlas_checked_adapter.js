/* Adds a bounded review panel; selected game/bank never mutates native output. */
'use strict';
const originalSameBank=C.sameBank;
C.sameBank=function(data,family,bank,keys){return AtlasChecks.availability(data,family,bank,keys).allCodesPresent;};
const originalShowDetail=showDetail;
showDetail=function(cell,s){
 originalShowDetail(cell,s);
 const findings=AtlasChecks.review(D,s.family,s.bank,cell,$('toolHints').checked);
 if(!findings.length)return;
 const phrases={
  MISSING_CODE_OR_MODIFIER_SIDE:'קוד או צד מקש שינוי שחסר בשכבה: ',
  MODIFIER_SIDE_NOT_ESTABLISHED:'צד מקש השינוי לא אומת בקבצי הפרופיל: ',
  THUMB_SELECTOR:'המודל מקצה את האגודל להחזקת בורר השכבה. אין הבטחה לתנועה רציפה במקביל. כפתור ',
  T_ON_THUMB:'T נמצא על האגודל בכפתור 31. עצמאותו מתנועת הסטיק דורשת בדיקה. ',
  POSSIBLE_TOOL_OVERLAP_NOT_LIVE:'חפיפה אפשרית לפי הנחיות הכלים — לא זוהתה התקנה פעילה: '
 };
 const items=findings.map(f=>'<p>'+E(phrases[f.kind]||f.kind)+E(f.detail)+(f.action?' · '+E(f.action):'')+'</p>').join('');
 $('detail').innerHTML+='<aside class="flag" data-preflight-review="true"><b>בדיקות לפני שימוש — לא תוצאת משחק</b>'+items+'<p>לא בוצע שינוי בקובצי Azeron, במשחק או בקיצורי כלי הגרפיקה.</p></aside>';
};
$('toolHints').checked=false;
$('toolHints').onchange=()=>{render();};
