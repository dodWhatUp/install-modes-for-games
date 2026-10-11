'use strict';
/* Executes the authored UI handlers in a small DOM fixture, not a browser.
   This checks state/event logic only. No rendering, native app or input test. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const text=fs.readFileSync(process.argv[2]||__dirname+'/../Azeron_R8_Action_Atlas_HE.html','utf8');
const raw=JSON.parse(text.match(/<script id="atlas-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
class Element{
 constructor(tag='div',id=''){this.tagName=tag.toUpperCase();this.id=id;this.children=[];this.dataset={};this.attributes={};this._html='';this._text='';this._value='';this.className='';this.style={setProperty(k,v){this[k]=v}};this.checked=true;
 this.classList={toggle:(c,force)=>{let s=new Set(this.className.split(/\s+/).filter(Boolean));let yes=force===undefined?!s.has(c):force;if(yes)s.add(c);else s.delete(c);this.className=[...s].join(' ');return yes},add:c=>{let s=new Set(this.className.split(/\s+/).filter(Boolean));s.add(c);this.className=[...s].join(' ')},contains:c=>this.className.split(/\s+/).includes(c)};
 }
 set textContent(v){this._text=String(v);this._html='';this.children=[];}get textContent(){return this._text+(this._html?this._html.replace(/<[^>]*>/g,''):'')+this.children.map(x=>x.textContent).join('');}
 set innerHTML(s){this._html=String(s);this._text='';this.children=[];this._parsed=null;}get innerHTML(){return this._html;}
 append(x){this.children.push(x);}appendChild(x){this.append(x);return x;}replaceChildren(...x){this.children=x;this._html='';this._text='';if(this.tagName==='SELECT')this._value='';}
 set value(v){this._value=String(v);}get value(){return this.tagName==='SELECT'?(this._value||this.children[0]?.value||''):this._value;}
 setAttribute(k,v){this.attributes[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(v);}
 querySelectorAll(sel){
  if(sel==='button'&&this._html){
   if(!this._parsed)this._parsed=[...this._html.matchAll(/<button\b([^>]*)>/g)].map(m=>{let e=new Element('button');for(const a of m[1].matchAll(/([\w-]+)="([^"]*)"/g))e.setAttribute(a[1],a[2]);return e});return this._parsed;
  }
  const all=[];function walk(e){for(const c of e.children){all.push(c);walk(c)}}walk(this);
  if(sel==='.key:not(.layer):not(.empty) strong')return all.filter(e=>e.classList.contains('key')&&!e.classList.contains('layer')&&!e.classList.contains('empty')).map(e=>{if(!e._strong)e._strong=new Element('strong');return e._strong});
  throw new Error('Unsupported fixture selector: '+sel);
 }
}
const ids={};for(const id of [...text.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]))ids[id]=new Element(['family','game','context','bank','view','density'].includes(id)?'select':'div',id);
ids['atlas-data'].textContent=JSON.stringify(raw);ids.family.value='CORE5';ids.view.value='combined';ids.density.value='normal';ids.search.value='';
const board=ids.board;for(const k of ['fingers','side','thumb'])board.append(ids[k]);
const document={getElementById:id=>{if(!ids[id])throw new Error('Missing element '+id);return ids[id]},createElement:tag=>new Element(tag),body:new Element('body'),documentElement:new Element('html')};
const scope={document,console};scope.window=scope;scope.globalThis=scope;vm.createContext(scope);
for(const m of text.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)){if(m[0].includes('type="application/json"'))continue;vm.runInContext(m[1],scope,{timeout:5000});}
let passed=0;function check(name,fn){fn();passed++}
function controls(){return ['fingers','side','thumb'].flatMap(k=>ids[k].children)}
function select(id,val){ids[id].value=val;ids[id].onchange({target:ids[id]})}
check('startup chooses one Bayonetta context',()=>{assert.equal(ids.game.value,'bayonetta-pc');assert.equal(ids.context.value,'gameplay')});
check('all 29 nonreserved controls rendered',()=>{assert.equal(controls().length,29);assert(controls().some(x=>x.dataset.nativeId===36));assert(controls().some(x=>x.dataset.nativeId===37));assert(!controls().some(x=>x.dataset.nativeId===19||x.dataset.nativeId===24))});
check('family switch creates six banks',()=>{select('family','SPARSE6');assert.equal(ids.bank.children.length,6);assert.equal(controls().length,29)});
check('symbols selector can be selected only in display',()=>{select('bank','SYMBOLS');assert(ids.title.textContent.includes('SYMBOLS'));assert.equal(controls().find(x=>x.dataset.nativeId===30).dataset.output,'LAYER:SYMBOLS')});
check('clear stale detail when context changes',()=>{controls()[0].onclick();select('context','menus');assert(ids.detail.textContent.includes('בחר כפתור'))});
check('Home warning is context dependent',()=>{select('bank','NAV');let home=controls().find(x=>x.dataset.output==='Home');home.onclick();assert(ids.detail.innerHTML.includes('Restore defaults'));assert(ids.detail.innerHTML.includes('Changes game settings'));select('context','gameplay');home=controls().find(x=>x.dataset.output==='Home');home.onclick();assert(ids.detail.innerHTML.includes('Camera up'));assert(!ids.detail.innerHTML.includes('<b>Restore defaults</b>'))});
check('search routes results without remapping output',()=>{ids.search.value='Lock-on';ids.search.oninput();assert(ids.results.children.length>0);ids.results.children[0].onclick();assert.equal(ids.bank.value,'BASIC');assert.equal(controls().find(x=>x.dataset.nativeId===3).dataset.output,'Alt')});
check('filter mismatch produces no irrelevant result',()=>{let b=ids.legend.querySelectorAll('button').find(x=>x.dataset.cat==='menus');b.onclick();assert.equal(ids.results.children.length,0)});
check('clear restores controls in place',()=>{ids.clear.onclick();assert.equal(controls().length,29);assert(!controls().some(x=>x.classList.contains('dim')))});
check('pending game has no invented action',()=>{select('game','poe2');assert(ids.scope.textContent.includes('אין טבלת'));assert(controls().filter(x=>!x.classList.contains('layer')&&!x.classList.contains('empty')).every(x=>x.innerHTML.includes('לא אומת')))});
check('view switching reaches keys and actions modes',()=>{select('view','keys');assert(board.classList.contains('keys-view'));select('view','actions');assert(board.classList.contains('action-view'));select('view','combined');assert(!board.classList.contains('keys-view')&&!board.classList.contains('action-view'))});
check('density changes only geometry variable',()=>{const before=controls().map(x=>[x.dataset.nativeId,x.dataset.output]);select('density','compact');assert.equal(document.documentElement.style['--cell-h'],'98px');assert.deepEqual(controls().map(x=>[x.dataset.nativeId,x.dataset.output]),before)});
check('icons and colors can be disabled',()=>{ids.icons.checked=false;ids.icons.onchange({target:ids.icons});ids.colors.checked=false;ids.colors.onchange({target:ids.colors});assert(document.body.classList.contains('noicons'));assert(document.body.classList.contains('nocolor'))});
check('clean preview can return',()=>{ids.peek.onclick();assert(document.body.classList.contains('peek'));ids.peek.onclick();assert(!document.body.classList.contains('peek'))});
check('unknown search does not alter native cells',()=>{ids.search.value='not-a-known-action-89123';ids.search.oninput();assert.equal(controls().length,29);assert.equal(ids.results.children.length,0)});
check('switching to core while symbols selected falls back to basic',()=>{select('family','SPARSE6');select('bank','SYMBOLS');select('family','CORE5');assert.equal(ids.bank.value,'BASIC')});
const result={ui_event_assertions:passed,environment:'minimal DOM fixture, NOT browser rendering',actual_game_or_device:false,native_inputs_sent:false,external_network:false};
fs.writeFileSync(__dirname+'/QA_UI_EVENTS_R8.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
