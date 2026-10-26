"""Game-specific controller draft maps over exact reWASD source references.

No native writer, live Overlay publication, device monitor or auto-remap. Native
control descriptions and directional crosswalks are saved configuration
evidence; they do not establish physical reach or runtime input acceptance.
"""
from __future__ import annotations
import copy, hashlib, html, json, os, re, tempfile, uuid
from pathlib import Path
import GameToolOverlay as overlay
import GameToolRewasd as rewasd
import GameToolControlsPlanner as planner

VERSION = '0.1.0'
ICONS = {'unknown': '?', 'none': '', 'move': '↔', 'jump': '↑', 'attack': '⚔', 'defend': '◇',
         'use': '✋', 'swap': '⇄', 'objective': '✦', 'magnify': '⊕', 'menu': '☰',
         'inventory': '▣', 'layer': '↳', 'weapon': '⌖'}
CONTEXTS = {'bindset-0': 'gameplay', 'bindset-1': 'atlan', 'bindset-2': 'turret',
            'bindset-3': 'dragon', 'bindset-4': 'automap', 'bindset-5': 'menus', 'bindset-6': 'viewer'}
DPAD = {33: ('DpadUp', 'JOY_DPAD_UP'), 34: ('DpadDown', 'JOY_DPAD_DOWN'),
        35: ('DpadLeft', 'JOY_DPAD_LEFT'), 36: ('DpadRight', 'JOY_DPAD_RIGHT')}


def encoded(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode('utf-8')
def fingerprint(value): return hashlib.sha256(encoded(value)).hexdigest()
def stable(prefix, value): return prefix+'-'+hashlib.sha256(value.encode()).hexdigest()[:20]
def require(ok, text): overlay.require(ok, text)
def bounded(value): planner.bounded_data(value); require(len(encoded(value)) <= 1024*1024, 'Controller draft exceeds 1 MiB')


def icon_for(label):
    text = label.casefold()
    for words, icon in [(('menu','radial','pause','tab','page'), 'menu'), (('magnify','zoom'), 'magnify'),
        (('objective','hint','ping'), 'objective'), (('swap','switch','class'), 'swap'), (('inventory','dossier'), 'inventory'),
        (('jump',), 'jump'), (('fire','attack','punch','melee','stab'), 'attack'), (('block','dash','dodge'), 'defend'),
        (('use','interact'), 'use'), (('layer',), 'layer'), (('move','look','pan','scroll'), 'move'), (('weapon','item'), 'weapon')]:
        if any(word in text for word in words): return icon
    return 'unknown'


def priority_text(value):
    if value.get('score') is not None:return str(value['score'])+' / 20'
    if value.get('range'):return '–'.join(str(x) for x in value['range'])+' / 20 · uncertain'
    return 'Not ranked'


def control_label(item):
    description = str(item.get('description', ''))
    match = re.search(r'Flydigi:\s*([^/]+)', description)
    return ('Flydigi '+match.group(1).strip()) if match else description or ('Button '+str(item.get('buttonId', '?')))


def _outputs(mapping, commands):
    result = []
    for step in mapping.get('macros', []):
        for kind in ('gamepad', 'keyboard', 'mouse', 'command'):
            if kind in step:
                value = step[kind]
                require(isinstance(value, dict), 'Unsupported native output shape')
                label = value.get('description') or commands.get(value.get('id'), {}).get('name') or str(value.get('buttonId', value.get('id', '?')))
                result.append({'kind': kind, 'label': str(label), 'native': copy.deepcopy(value)})
        if not any(k in step for k in ('gamepad','keyboard','mouse','command')):
            result.append({'kind': 'unknown', 'label': 'Native macro step; review required', 'native': copy.deepcopy(step)})
    if 'jumpToLayer' in mapping:
        result.append({'kind':'layer', 'label':'Base' if mapping['jumpToLayer']['layer']==0 else 'Shift '+str(mapping['jumpToLayer']['layer']), 'native':copy.deepcopy(mapping['jumpToLayer'])})
    if mapping.get('hardware', {}).get('unmap') is True:
        result.append({'kind':'unmap', 'label':'Native input muted', 'native':copy.deepcopy(mapping['hardware'])})
    if not result: result.append({'kind':'unknown', 'label':'Native operation not decoded', 'native':copy.deepcopy(mapping)})
    return result


def validate(draft):
    bounded(draft)
    require(draft.get('kind')=='controller_game_keymap_draft' and draft.get('schema_version')==1, 'Unsupported controller draft')
    for key in ('id','game_id'): overlay.token(draft[key])
    require(type(draft['revision']) is int and draft['revision']>=1, 'Invalid draft revision')
    require(draft['effect_state']=={'native':'unchanged','game':'unchanged','overlay':'not_published'}, 'Draft cannot claim applied effects')
    overlay.label(draft['title']); overlay.digest(draft['source']['sha256'])
    reference=draft['source']['config_reference']
    require(type(reference)is str and not Path(reference).is_absolute() and '..' not in Path(reference).parts and '\\' not in reference and reference.endswith('.rewasd'), 'Unsafe native reference')
    require(draft['device']['geometry_status']=='unverified_schematic' and draft['device']['physical_acceptance'] is False, 'Draft cannot certify device geometry')
    require(type(draft['presentation']['show_icons'])is bool, 'Invalid icon visibility')
    require(1<=len(draft['layers'])<=17 and 1<=len(draft['contexts'])<=16 and len(draft['bindings'])<=512, 'Draft count limit')
    layers={x['id'] for x in draft['layers']}; contexts=set(draft['contexts']); seen=set()
    require(len(layers)==len(draft['layers']) and len(contexts)==len(draft['contexts']), 'Duplicate layer/context')
    for binding in draft['bindings']:
        overlay.token(binding['id']); require(binding['id'] not in seen and binding['layer'] in layers, 'Duplicate or unknown native mapping'); seen.add(binding['id'])
        require(type(binding['native_index'])is int and binding['native_index']>=0 and isinstance(binding['native_mapping'],dict), 'Missing exact native mapping')
        require(len(binding['controls'])<=16 and len(binding['outputs'])<=64, 'Native mapping too complex for this draft')
        for control in binding['controls']:
            require(control['physical_verified'] is False and type(control['label'])is str and len(control['label'])<=1000, 'Invalid native control evidence')
        for context, annotation in binding['annotations'].items():
            require(context in contexts and annotation['icon'] in ICONS, 'Unknown action context/icon')
            require(annotation['evidence'] in {'unknown','saved_config','semantic_crosswalk','user_label','proposed'}, 'Unknown action evidence')
            require(type(annotation['label'])is str and len(annotation['label'])<=240 and not any(ord(x)<32 for x in annotation['label']), 'Invalid action label')
    return draft


def draft_from_profile(path, game_id, game_name, *, root=None, device_alias='flydigi-vader-5-pro', workbook=None):
    root=Path(root or rewasd.native_root()); info=rewasd.inspect(path,root); native=overlay.decode(info['raw'])
    overlay.token(game_id); overlay.token(device_alias); overlay.label(game_name)
    require(type(native.get('mappings'))is list and len(native['mappings'])<=512, 'Unsupported native mapping inventory')
    shifts=native.get('shifts',[]); masks=native.get('masks',[]); commands=native.get('commands',[])
    require(type(shifts)is list and len(shifts)<=16 and type(masks)is list and len(masks)<=512 and type(commands)is list, 'Native layer/mask limit')
    require(all(type(x)is dict and type(x.get('id'))is int for x in shifts+masks+commands), 'Invalid native index')
    require(len({x['id'] for x in shifts})==len(shifts) and len({x['id'] for x in masks})==len(masks) and len({x['id'] for x in commands})==len(commands), 'Duplicate native index')
    mask_lookup={x['id']:x for x in masks}; command_lookup={x['id']:x for x in commands}
    layers=[{'id':'base','native_shift_id':0,'label':'Base','native_type':'base'}]+[
        {'id':'shift-'+str(x['id']),'native_shift_id':x['id'],'label':x.get('description') or ('Shift '+str(x['id'])), 'native_type':x.get('type','unknown')} for x in shifts]
    records=[]
    for index,mapping in enumerate(native['mappings']):
        require(type(mapping)is dict and type(mapping.get('condition'))is dict and type(mapping.get('macros',[]))is list, 'Unknown native mapping shape')
        condition=mapping.get('condition',{}); mask=condition.get('mask',{}); mask_data=mask_lookup.get(mask.get('id'),{})
        require(type(mask)is dict and ('id' not in mask or mask['id'] in mask_lookup), 'Undefined native mask')
        controls=mask_data.get('set') or ([condition['hardware']] if 'hardware' in condition else [])
        require(type(controls)is list, 'Unknown native condition controls')
        controls=[{'id':'device-'+str(x.get('deviceId','unknown'))+'-button-'+str(x.get('buttonId','unknown')),
                   'label':control_label(x), 'native':copy.deepcopy(x), 'physical_verified':False} for x in controls]
        if not controls and mask_data.get('radialMenuSet'):
            require(type(mask_data['radialMenuSet'])is list and len(mask_data['radialMenuSet'])<=16,'Unsupported radial menu set')
            controls=[{'id':'radial-'+str(x['circleId'])+'-'+str(x['sectorId']),
                       'label':'reWASD radial circle '+str(x['circleId'])+' / sector '+str(x['sectorId']),
                       'native':copy.deepcopy(x),'physical_verified':False} for x in mask_data['radialMenuSet']]
        shift=condition.get('shiftId',0); layer='base' if shift==0 else 'shift-'+str(shift)
        require(layer in {x['id'] for x in layers}, 'Mapping refers to undefined native Shift')
        outputs=_outputs(mapping,command_lookup)
        annotations={}
        if outputs[0]['kind']=='layer':
            label=('Return to ' if outputs[0]['native']['layer']==0 else 'Enter ')+outputs[0]['label']
            annotations['gameplay']={'label':label,'icon':'layer','evidence':'saved_config','source':'Native jumpToLayer declaration; runtime transition unverified','action_ids':[]}
        records.append({'id':stable('binding',info['sha256']+'|'+str(index)), 'native_index':index, 'layer':layer,
                        'controls':controls, 'activation':copy.deepcopy(mask.get('activator',{'type':'unknown','mode':'unknown'})),
                        'outputs':outputs, 'annotations':annotations,'native_mapping':copy.deepcopy(mapping)})
    draft={'kind':'controller_game_keymap_draft','schema_version':1,'id':stable('controller-map',game_id+'|'+info['sha256']),
        'revision':1,'game_id':game_id,'title':game_name+' / controller draft',
        'device':{'alias':device_alias,'geometry_status':'unverified_schematic','physical_acceptance':False},
        'source':{'provider':'rewasd','config_reference':Path(path).relative_to(root).as_posix(),'sha256':info['sha256'],
                  'app_version':info['app_version'],'virtual_outputs':info['outputs'],'explicit_mappings_only':True},
        'layers':layers,'contexts':['gameplay'],'bindings':records,'action_catalog':[],
        'presentation':{'show_icons':True},'research_sources':[],
        'limitations':['Only explicit saved native mappings are decoded; implicit front-button/axis passthrough remains unknown.',
                      'Native Flydigi labels do not verify physical positions, Shift access or press/release behavior.',
                      'The neutral front/back schematic is not an enrolled physical layout.',
                      'Save, Preview and Export never apply reWASD/game bindings or publish a live Overlay.'],
        'effect_state':{'native':'unchanged','game':'unchanged','overlay':'not_published'}}
    # Native radial-menu commands describe reWASD's menu, never the game's.
    if any(x['native_type']=='radialMenu' for x in layers):
        draft['contexts'].append('rewasd-radial')
        for record in records:
            names=[x['label'] for x in record['outputs'] if x['kind']=='command']
            if names: record['annotations']['rewasd-radial']={'label':'reWASD: '+' / '.join(names),'icon':'menu','evidence':'saved_config','source':'Native reWASD command list; not a game action','action_ids':[]}
            elif any(x['id'].startswith('radial-') for x in record['controls']):
                record['annotations']['rewasd-radial']={'label':'reWASD selection → '+' / '.join(x['label'] for x in record['outputs']),'icon':'menu','evidence':'saved_config','source':'Native radial menu sector and emitted output; game action unverified','action_ids':[]}
    if workbook is not None: draft=seed_doom_actions(draft,workbook)
    return validate(draft)


def seed_doom_actions(draft,workbook):
    planner.validate(workbook); require(draft['game_id']==workbook['game_id']=='doom-the-dark-ages','DOOM action source belongs to another game')
    result=copy.deepcopy(draft); catalog=[]; by_key={}
    for action in workbook['actions']:
        if not action['output'].startswith('JOY'): continue
        context=CONTEXTS.get(action['context'])
        if not context: continue
        record={'id':action['id'],'label':action['label'],'icon':icon_for(action['label']),'context':context,
                'native_key':action['output'],'meaning':action['meaning'],'priority':planner.priority(action['urgency'],action['frequency']),
                'evidence':copy.deepcopy(action['evidence'])}
        catalog.append(record); by_key.setdefault((context,action['output']),[]).append(record)
        if context not in result['contexts']:result['contexts'].append(context)
    result['action_catalog']=catalog
    result['research_sources'].append({'kind':'game_controls_workbook','id':workbook['id'],'revision':workbook['revision'],
        'sha256':fingerprint(workbook),'scope':'Saved DOOM controller bindings and annotated meanings; no new physical acceptance'})
    for binding in result['bindings']:
        outputs=binding['outputs']
        if len(outputs)!=1 or outputs[0]['kind']!='gamepad':continue
        output=outputs[0]['native']; cross=DPAD.get(output.get('buttonId'))
        if not cross or output.get('description')!=cross[0]:continue
        for context in result['contexts']:
            actions=by_key.get((context,cross[1]),[])
            if actions:
                label=' / '.join(dict.fromkeys(a['label'] for a in actions))
                binding['annotations'][context]={'label':label[:240],'icon':icon_for(label),'evidence':'semantic_crosswalk',
                    'source':'Exact directional names: reWASD '+cross[0]+' → saved DOOM '+cross[1]+'. Configuration evidence; physical/runtime unverified.',
                    'action_ids':[a['id'] for a in actions]}
    result['limitations'].append('JOY1–JOY10 and trigger-number crosswalks are not assumed. Only exact named D-pad directions receive automatic action labels.')
    return validate(result)


def annotate(draft,binding_id,context,label,icon='unknown',*,evidence='user_label'):
    validate(draft); result=copy.deepcopy(draft)
    require(context in result['contexts'],'Choose an existing context')
    row=next((x for x in result['bindings'] if x['id']==binding_id),None); require(row is not None,'Choose a native mapping')
    row['annotations'][context]={'label':label.strip(),'icon':icon,'evidence':evidence,'source':'Explicit draft annotation; native/game outputs unchanged','action_ids':[]}
    result['revision']+=1
    return validate(result)


def source_status(draft,root=None):
    validate(draft)
    try:
        root=Path(root or rewasd.native_root()); path=root/draft['source']['config_reference']
        actual=rewasd.inspect(path,root)
        return {'state':'match' if actual['sha256']==draft['source']['sha256'] else 'changed','physical_verified':False}
    except (OSError,ValueError) as error:return {'state':'unavailable','reason':str(error),'physical_verified':False}


def verify_sources(draft,directory=None,root=None):
    """Read owners again; annotations never make stale source data current."""
    validate(draft)
    require(source_status(draft,root)['state']=='match','Native source changed or is missing; reread before saving or exporting')
    fresh=draft_from_profile(Path(root or rewasd.native_root())/draft['source']['config_reference'],draft['game_id'],draft['title'],root=root)
    native_fields=('id','native_index','layer','controls','activation','outputs','native_mapping')
    immutable=lambda value:[{key:row[key] for key in native_fields} for row in value['bindings']]
    require(immutable(fresh)==immutable(draft),'Draft native output inventory differs from its pinned source; reread the profile')
    if draft['research_sources']:
        require(directory is not None,'Game research needs its owning data directory for a fresh source check')
        from GameToolKeymapBuilder import SourceLibrary
        from game_keybind_ops.core import Service
        library=planner.WorkbookLibrary(SourceLibrary(directory))
        workbook=library.load(draft['game_id'])
        for source in draft['research_sources']:
            require(source['kind']=='game_controls_workbook' and source['id']==workbook['id'] and source['revision']==workbook['revision'] and source['sha256']==fingerprint(workbook),'Game research changed; reread the draft before saving or exporting')
        planner.check_sources(workbook,Service(directory))
    return True


class DraftLibrary:
    def __init__(self,directory,root=None):
        self.directory=overlay.no_links(Path(directory));self.root=overlay.no_links(self.directory/'controller-keymap-drafts'); self.native_root=Path(root or rewasd.native_root())
    def path(self,identity): overlay.token(identity);return overlay.no_links(self.root/(identity+'.json'))
    def load(self,identity):return validate(overlay.decode(overlay.read(self.path(identity))))
    def drafts(self):
        if not self.root.exists():return []
        paths=list(self.root.glob('controller-map-*.json'));require(len(paths)<=128,'Too many controller drafts')
        return [self.load(p.stem) for p in sorted(paths)]
    def save(self,draft,expected='absent'):
        verify_sources(draft,self.directory,self.native_root);self.root.mkdir(parents=True,exist_ok=True);target=self.path(draft['id'])
        lock=self.root/'edit.lock'
        with lock.open('xb'):pass
        temp=None
        try:
            prior=self.load(draft['id']) if target.exists() else None
            require((fingerprint(prior) if prior else 'absent')==expected,'Draft changed; refresh before saving')
            if prior:
                folder=self.root/'history'/draft['id'];folder.mkdir(parents=True,exist_ok=True)
                backup=folder/(fingerprint(prior)+'.json')
                if not backup.exists():
                    with backup.open('xb') as f:f.write(encoded(prior))
            temp=target.with_name(target.name+'.pending-'+uuid.uuid4().hex)
            with temp.open('xb') as f:f.write(encoded(draft));f.flush();os.fsync(f.fileno())
            os.replace(temp,target);temp=None
            require(self.load(draft['id'])==draft,'Controller draft readback mismatch')
            return fingerprint(draft)
        finally:
            if temp is not None and temp.exists():temp.unlink()
            lock.unlink()


def rows(draft,layer,context):
    validate(draft);require(layer in {x['id'] for x in draft['layers']} and context in draft['contexts'],'Unknown layer/context')
    result=[]
    for binding in draft['bindings']:
        if binding['layer']!=layer:continue
        annotation=binding['annotations'].get(context,{'label':'Game action not verified','icon':'unknown','evidence':'unknown'})
        result.append({'id':binding['id'],'control':' + '.join(x['label'] for x in binding['controls']) or 'Unknown control',
                       'output':' + '.join(x['label'] for x in binding['outputs']),
                       'action':annotation['label'],'icon':annotation['icon'],'evidence':annotation['evidence'],
                       'activation':binding['activation'].get('type','unknown')+' / '+binding['activation'].get('mode','unknown')})
    return result


def schematic_svg():
    """Neutral shapes only; rear labels are an inventory, not physical positions."""
    return '''<svg viewBox="0 0 900 260" role="img" aria-label="Neutral controller front and back; positions unverified" xmlns="http://www.w3.org/2000/svg">
<g fill="#203348" stroke="#82a2b7" stroke-width="3"><path d="M50 210 Q10 150 65 65 Q100 35 180 55 L300 55 Q380 30 420 85 Q465 170 420 215 L355 170 L115 170Z"/>
<path d="M500 210 Q460 150 515 65 Q550 35 630 55 L750 55 Q830 30 870 85 Q915 170 870 215 L805 170 L565 170Z"/></g>
<g fill="#eef5ff" font-family="sans-serif" text-anchor="middle"><text x="240" y="25">STANDARD FRONT · schematic</text><text x="690" y="25">REAR · positions unverified</text>
<text x="120" y="100">LS</text><text x="190" y="150">D-pad</text><text x="285" y="150">RS</text><text x="365" y="82">Y</text><text x="340" y="108">X</text><text x="390" y="108">B</text><text x="365" y="133">A</text>
<text x="690" y="100">Native labels: M1 · M2 · M3 · M4</text><text x="690" y="132">Exact rear placement not enrolled</text><text x="450" y="246">Outline is a reference; saved controls and game actions are listed below.</text></g></svg>'''


def preview_html(draft):
    validate(draft);e=html.escape
    sections=[]
    for layer in draft['layers']:
        for context in draft['contexts']:
            records=rows(draft,layer['id'],context)
            if not records:continue
            body=''.join('<tr><td>'+e(r['control'])+'</td><td>'+e(r['activation'])+'</td><td>'+e(r['output'])+'</td><td>'+e((ICONS[r['icon']]+' ') if draft['presentation']['show_icons'] else '')+e(r['action'])+'</td><td>'+e(r['evidence'])+'</td></tr>' for r in records)
            sections.append('<details open><summary>'+e(layer['label']+' / '+context)+'</summary><div class="table"><table><thead><tr><th>Native control</th><th>Press style</th><th>Emitted output</th><th>Game action</th><th>Evidence</th></tr></thead><tbody>'+body+'</tbody></table></div></details>')
    if draft['action_catalog']:
        body=''.join('<tr><td>'+e(a['context'])+'</td><td>'+e(a['native_key'])+'</td><td>'+e((ICONS[a['icon']]+' ') if draft['presentation']['show_icons'] else '')+e(a['label'])+'</td><td>'+e(priority_text(a['priority']))+'</td><td>'+e(a['meaning'])+'</td></tr>' for a in draft['action_catalog'])
        sections.insert(0,'<details><summary>Saved game action catalog ('+str(len(draft['action_catalog']))+' rows) · controller-button crosswalk incomplete</summary><div class="table"><table><thead><tr><th>Context</th><th>Saved input token</th><th>Action</th><th>A20 priority</th><th>Meaning / uncertainty</th></tr></thead><tbody>'+body+'</tbody></table></div></details>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+e(draft['title'])+'</title><style>body{font:16px system-ui;background:#101a26;color:#eef5ff;margin:20px;max-width:1250px}svg{max-height:300px;width:100%}input{font:inherit;padding:8px;max-width:28em;width:85%}summary{cursor:pointer;padding:12px}details{border:1px solid #58728a;margin:12px 0}.table{overflow:auto}table{border-collapse:collapse;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #30475a}p{line-height:1.5}small{color:#bed0e0}@media print{input{display:none}details{break-inside:avoid}}</style><h1>'+e(draft['title'])+'</h1><p><strong>DRAFT · not applied or published.</strong> Controller positions and live Shift state are unverified.</p>'+schematic_svg()+'<input id="search" aria-label="Search mappings" placeholder="Search action, output or native control"><p><small>'+e(' · '.join(draft['limitations']))+'</small></p>'+''.join(sections)+'<script>const s=document.getElementById("search");s.addEventListener("input",()=>{const q=s.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));});s.addEventListener("keydown",e=>{if(e.key==="Escape"){s.value="";s.dispatchEvent(new Event("input"));}});</script></html>'


def export_bundle(draft,destination,root=None,*,directory=None):
    verify_sources(draft,directory,root)
    out=overlay.no_links(destination);require(not out.exists(),'Export to a new folder; preserve previous exports')
    out.mkdir();
    with (out/'controller-draft.json').open('xb') as f:f.write(encoded(draft))
    with (out/'controller-preview.html').open('x',encoding='utf-8') as f:f.write(preview_html(draft))
    with (out/'controller-schematic.svg').open('x',encoding='utf-8') as f:f.write(schematic_svg())
    return {'directory':str(out),'draft_sha256':fingerprint(draft),'native_changed':False,'overlay_published':False,'geometry_verified':False}
