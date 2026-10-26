"""Build a self-contained menu-order guide from observed menus and final maps."""
import argparse,base64,html,json
from pathlib import Path

def build(menu_path,document_path,output,images=None):
    data=json.loads(Path(menu_path).read_text(encoding='utf-8-sig'))
    doc=json.loads(Path(document_path).read_text(encoding='utf-8-sig'))
    esc=html.escape
    contexts={'Slayer':'gameplay','Atlan':'atlan','Dragon':'dragon','Menu':'menus','AutoMap':'automap'}
    normal={'Up':'Up Arrow','Down':'Down Arrow','Left':'Left Arrow','Right':'Right Arrow'}
    holders={'WEAPONS':2,'MENUS':1,'TOOLS':36,'NAV':28,'SYMBOLS':30}
    buttons={b['id']:b for b in doc['buttons']}
    def position(tab,row):
        if any(k in ('W','A','S','D')for k in row['keys']) and row['action']in ('Move Forward','Move Backwards','Move Left','Move Right','Pan Up','Pan Down','Pan Left','Pan Right','Up','Down','Left','Right'):
            return '#24 movement stick'
        if tab=='Turret':return 'Mouse; use the listed keyboard key for utility actions'
        context=contexts[tab];routes=[]
        for m in doc['maps']:
            if m['context']!=context:continue
            for cell in m['cells']:
                if cell['output']in [normal.get(k,k)for k in row['keys']]:
                    routes.append((m['layer'],cell['button_id']))
        routes.sort(key=lambda r:({'BASIC':0,'WEAPONS':1,'MENUS':2,'NAV':3,'TOOLS':4,'SYMBOLS':5}.get(r[0],6),r[1]))
        if not routes:return 'Mouse / keyboard'
        return '; '.join(layer+' #'+str(bid)+((' (hold #'+str(holders[layer])+')')if layer!='BASIC'else '')for layer,bid in routes)
    tabs=[]
    for tab in data['menus']:
        parts=[];section=None
        for row in tab['rows']:
            if row['section']!=section:
                section=row['section'];parts.append('<tr class="section"><th colspan="5">'+esc(section)+'</th></tr>')
            keys=' '.join('<kbd>'+esc(key)+'</kbd>'for key in row['keys'])
            change=('Was '+row['before']+' → saved')if row.get('changed')else 'Retained'
            parts.append('<tr class="binding" data-changed="'+str(bool(row.get('changed'))).lower()+'"><td>'+str(row['order'])+'</td><th scope="row">'+esc(row['action'])+'</th><td>'+keys+'</td><td>'+esc(position(tab['name'],row))+'</td><td>'+esc(change)+'</td></tr>')
        name=tab['name']
        tabs.append('<section id="'+name+'" class="menu"><h2>'+esc(name)+' <small>'+str(len(tab['rows']))+' rows</small></h2><div class="table-wrap"><table><thead><tr><th>#</th><th>Action in DOOM</th><th>Bind to</th><th>Azeron route / alternative</th><th>Status</th></tr></thead><tbody>'+''.join(parts)+'</tbody></table></div></section>')
    img=''
    if images:
        for layer in ('BASIC','WEAPONS'):
            path=Path(images)/('gameplay-'+layer+'-Combined.png')
            img+='<figure><figcaption>'+layer+' · gameplay · published map</figcaption><img alt="'+layer+' button outputs and game actions" src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"></figure>'
    nav=''.join('<a href="#'+t['name']+'">'+t['name']+'</a>'for t in data['menus'])
    notes=''.join('<li>'+esc(x)+'</li>'for x in data['notes'])
    styles=''.join('<tr><th scope="row">'+esc(k)+'</th><td>'+esc(v)+'</td></tr>'for k,v in data['styles'].items())
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DOOM · Binding guide R1</title>
<style>
:root{color-scheme:dark;--bg:#0c1420;--panel:#152235;--ink:#eef4ff;--muted:#b9c9de;--edge:#344c68;--accent:#7de0d4}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,Segoe UI,sans-serif}header{position:sticky;top:0;z-index:2;background:#0c1420f5;border-bottom:1px solid var(--edge);padding:10px 20px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}header strong{margin-right:auto}header label{display:flex;gap:7px;align-items:center}input[type=search]{width:26ch;max-width:100%;padding:8px;background:var(--panel);color:var(--ink);border:1px solid var(--edge);border-radius:6px;font:inherit}button{padding:8px 12px;background:var(--panel);color:var(--ink);border:1px solid var(--edge);border-radius:6px;font:inherit;cursor:pointer}a{color:var(--accent)}:focus-visible{outline:3px solid var(--accent);outline-offset:3px}main{max-width:1400px;margin:auto;padding:20px}h1{font-size:clamp(25px,4vw,38px);margin:0 0 6px}h2{margin:22px 0 10px;font-size:24px}h2 small{font-size:14px;font-weight:400;color:var(--muted);margin-left:10px}p{margin:7px 0 15px}.muted,small{color:var(--muted)}.status{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.status span,nav a{border:1px solid var(--edge);background:var(--panel);border-radius:6px;padding:6px 11px}nav{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 18px}nav a{text-decoration:none}details{border:1px solid var(--edge);background:var(--panel);border-radius:8px;padding:12px 15px;margin:12px 0}summary{cursor:pointer;font-weight:650}details p,details ul{margin:12px 0}li{margin:7px 0}.table-wrap{overflow-x:auto;border:1px solid var(--edge);border-radius:8px}table{border-collapse:collapse;width:100%;text-align:left}th,td{padding:10px 12px;border-bottom:1px solid var(--edge);vertical-align:top}thead{background:var(--panel)}tbody th{font-weight:550}td:first-child{width:42px;color:var(--muted)}td:nth-child(3){min-width:150px}td:nth-child(4){max-width:370px;font-size:14px;color:var(--muted)}td:last-child{font-size:14px;color:var(--muted);min-width:120px}.section th{background:#1c3046;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--accent)}tr[data-changed=true] th{color:var(--accent)}kbd{display:inline-block;background:#24374f;border:1px solid #57708e;border-bottom-width:3px;border-radius:5px;padding:2px 7px;font:650 15px/1.6 system-ui;margin:0 3px 3px 0;white-space:nowrap}figure{margin:18px 0}figcaption{font-weight:650;margin-bottom:8px}img{width:100%;height:auto;border-radius:6px}#count{min-width:80px;font-size:14px;color:var(--muted)}.empty{padding:24px;border:1px dashed var(--edge)}[hidden]{display:none!important}footer{padding:20px 0;color:var(--muted);font-size:14px}@media(max-width:680px){header{position:static;padding:10px 12px;gap:8px}header strong{width:100%}main{padding:14px}th,td{padding:9px}td:nth-child(4){min-width:190px}nav a{padding:8px 10px}html{scroll-padding-top:15px}}@media print{body{background:white;color:black;font-size:10pt}header,nav,.screen-only{display:none}main{max-width:none;padding:0}details{background:white;color:black}table{font-size:9pt}th,td{border-color:#bbb}thead,.section th{background:#eee;color:black}kbd{color:black;background:#eee}h2{break-after:avoid}.table-wrap{overflow:visible;border-color:#aaa}tr{break-inside:avoid}a{color:black}img{max-height:90vh;object-fit:contain}figure{break-inside:avoid}}
</style>
<header><strong>DOOM · R1</strong><label>Search <input id="search" type="search" placeholder="Action or key…" aria-label="Search actions or keys"></label><label><input id="changed" type="checkbox">Changed only</label><button id="clear">Clear</button><button id="print">Print all</button><span id="count" role="status" aria-live="polite"></span></header>
<main><h1>DOOM: The Dark Ages</h1><p class="muted">Your binding guide · Settings → Inputs · exact native menu order · 26 October 2026</p>
<div class="status"><span>10 actions changed and saved</span><span>96 menu rows</span><span>Restart verified</span><span>Combat feel needs your play check</span></div>
<p>The listed bindings are already saved in DOOM. The matching Overlay is published. Keep the existing <strong>COMBAT R2</strong> Azeron family active and Game Tools / Overlay running. No native Azeron or reWASD profile was rewritten.</p>
<nav aria-label="Input tabs">__NAV__<a href="#maps">Maps</a></nav>
<details><summary>How to use the Azeron layers and shared actions</summary><p><strong>#19:</strong> hold to show Overlay. <strong>#2:</strong> hold WEAPONS; release returns. #1 MENUS, #28 NAV, #36 TOOLS and #30 SYMBOLS also remain momentary. Movement stays on #24; Ctrl #5, Shift #9 and Space #14 are preserved.</p><p>Tap <kbd>L</kbd> for Quick Switch; hold for the Weapon Wheel (180 ms delay). <kbd>K</kbd> is Shield Throw or Meat Hook / Spear Ready according to weapon/context. Ready, Orbit and Block use press-and-hold; keyboard Stab and Slam use Single Input. <kbd>G</kbd> switches the off-hand weapon; <kbd>H</kbd> switches the class weapon. These are separate actions.</p><p>Ready #10 and Slam #9 share the middle finger; Jump #14 and held Wheel #15 share the index finger. Use Mouse3 for Ready when the combination is awkward, and #2 + the numeric weapon grid to avoid holding Wheel. Physical reach and combat behavior still need your play check.</p><p>The default Overlay context is gameplay. The saved menus / AutoMap / Atlan / Dragon contexts can be selected in Game Tools; engine-context detection was not verified. Turret has no separate published context in this existing map family.</p></details>
<div id="empty" class="empty" hidden>No matching actions. Clear the search or turn off Changed only.</div>
__TABS__
<details><summary>Preserved press / hold settings</summary><table><tbody>__STYLES__</tbody></table></details>
<details><summary>Menu details, file ownership and recovery</summary><ul>__NOTES__</ul><p>The seven registered CFG row changes were applied with the existing guarded binding service. The game’s native profile also needed menu edits; four selectors exist only there. A CFG replacement alone cannot reproduce all ten changes. Fresh pre-change and final backups are kept privately with verified hashes. Restore requires a reviewed, paired game-profile and CFG operation while DOOM and Steam are closed.</p><p>Search and filters affect this guide only. Opening this HTML does not change any setting. The guide uses no external resources.</p></details>
<details id="maps"><summary>Published BASIC and WEAPONS maps</summary>__IMAGES__</details>
<footer>Build 25755602 · All ten changed actions read back after normal exit and relaunch. Gameplay was not loaded by this verification. Duplicate selector rows are kept in their original menu positions.</footer></main>
<script>
const search=document.querySelector('#search'),changed=document.querySelector('#changed'),rows=[...document.querySelectorAll('.binding')],sections=[...document.querySelectorAll('.menu')];
function filter(){const q=search.value.trim().toLowerCase();let n=0;for(const r of rows){r.hidden=!(r.textContent.toLowerCase().includes(q)&&(!changed.checked||r.dataset.changed==='true'));if(!r.hidden)n++;}for(const s of sections){s.hidden=![...s.querySelectorAll('.binding')].some(r=>!r.hidden);for(const h of s.querySelectorAll('.section')){let r=h.nextElementSibling,shown=false;while(r&&!r.classList.contains('section')){if(!r.hidden)shown=true;r=r.nextElementSibling;}h.hidden=!shown;}}document.querySelector('#count').textContent=n+' / '+rows.length+' rows';document.querySelector('#empty').hidden=n>0;}
search.addEventListener('input',filter);changed.addEventListener('change',filter);document.querySelector('#clear').addEventListener('click',()=>{search.value='';changed.checked=false;filter();search.focus();});document.querySelector('#print').addEventListener('click',()=>window.print());
search.addEventListener('keydown',e=>{if(e.key==='Escape'){search.value='';filter();}});let printState;addEventListener('beforeprint',()=>{printState={query:search.value,changed:changed.checked,details:[...document.querySelectorAll('details')].map(d=>d.open)};search.value='';changed.checked=false;filter();document.querySelectorAll('details').forEach(d=>d.open=true);});addEventListener('afterprint',()=>{if(!printState)return;search.value=printState.query;changed.checked=printState.changed;document.querySelectorAll('details').forEach((d,i)=>d.open=printState.details[i]);filter();});filter();
</script></html>'''
    for key,value in {'NAV':nav,'TABS':''.join(tabs),'STYLES':styles,'NOTES':notes,'IMAGES':img}.items():page=page.replace('__'+key+'__',value)
    target=Path(output)
    with target.open('x',encoding='utf-8')as out:out.write(page)
    return {'rows':sum(len(t['rows'])for t in data['menus']),'bytes':target.stat().st_size,'output':str(target)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('menus');p.add_argument('document');p.add_argument('output');p.add_argument('--images');v=p.parse_args()
    print(json.dumps(build(v.menus,v.document,v.output,v.images)))
