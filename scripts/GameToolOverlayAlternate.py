"""Prepared alternate display looks; native/game input remains untouched."""
from __future__ import annotations
import copy
import os
from pathlib import Path
import tempfile
import GameToolOverlay as api
import GameToolOverlayAppearance as looks

VERSION = "0.1.0"
KEYS = {k:k for k in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') + [f'F{i}' for i in range(1,25)]}
KEYS.update({'Ctrl':'Ctrl','Shift':'Shift','Alt':'Alt','Right Ctrl':'RControl','Right Shift':'RShift','Right Alt':'RAlt',
             'Space':'Space','Tab':'Tab','Enter':'Enter','Esc':'Escape','Backspace':'Backspace','Delete':'Delete',
             'Insert':'Insert','Home':'Home','End':'End','Page Up':'PgUp','Page Down':'PgDn',
             'Up Arrow':'Up','Down Arrow':'Down','Left Arrow':'Left','Right Arrow':'Right',
             'Mouse Left':'LButton','Mouse Right':'RButton','Mouse Middle':'MButton','Mouse Back':'XButton1','Mouse Forward':'XButton2'})
KEYS.update({f'Numpad {i}':f'Numpad{i}' for i in range(10)})


def rule():
    return dict(enabled=True,double_press=True,window_ms=300,behavior='hold',chord=[],target=dict(kind='view',view='Combined'))


def defaults():
    return dict(schema_version=1,kind='overlay_alternate',global_rule=rule(),games={},prepared=[])


def validate_rule(value):
    api.fields(value,'enabled double_press window_ms behavior chord target')
    api.require(type(value['enabled']) is bool and type(value['double_press']) is bool,'Alternate enablement')
    api.require(type(value['window_ms']) is int and 150<=value['window_ms']<=600,'Double press must be 150–600 ms')
    api.require(value['behavior'] in {'hold','toggle'},'Choose hold or view toggle')
    keys=value['chord']
    api.require(type(keys) is list and len(keys) in {0,2,3,4} and all(type(k) is str and k in set(KEYS.values()) for k in keys) and len(set(keys))==len(keys),'Choose 2–4 different keyboard/mouse buttons, or clear the combination')
    target=value['target'];api.require(type(target) is dict,'Choose an alternate look')
    if target.get('kind')=='view':
        api.fields(target,'kind view');api.require(target['view'] in api.VIEWS,'Choose an alternate content view')
    else:
        api.fields(target,'kind name style');api.require(target['kind']=='preset','Choose a saved appearance preset')
        api.label(target['name']);looks.validate_style(target['style'])
    return value


def validate(value):
    api.fields(value,'schema_version kind global_rule games prepared')
    api.require(type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='overlay_alternate','Alternate settings schema')
    validate_rule(value['global_rule'])
    api.require(type(value['games']) is dict and len(value['games'])<=64,'Alternate game scope limit')
    for game,setting in value['games'].items():api.token(game);validate_rule(setting)
    api.require(type(value['prepared']) is list and len(value['prepared'])<=2048,'Alternate image limit')
    seen=set()
    for row in value['prepared']:
        api.fields(row,'game group layer context source_sha256 target_sha256 path sha256')
        for key in ('game','group','layer','context'):api.token(row[key])
        for key in ('source_sha256','target_sha256','sha256'):api.digest(row[key])
        api.require(row['path']=='overlay-alternate-assets/'+row['sha256']+'.png','Alternate image path')
        ident=tuple(row[k] for k in ('game','group','layer','context'))
        api.require(ident not in seen,'Duplicate alternate image');seen.add(ident)
    api.require(len(api.encode(value))<=1024*1024,'Alternate settings size limit')
    return value


def read(directory):
    path=api.no_links(Path(directory)/'overlay-alternate.json')
    raw=api.read(path,1024*1024) if path.exists() else None
    return validate(api.decode(raw)) if raw is not None else defaults(),raw


def effective(value,game):return copy.deepcopy(value['games'].get(game,value['global_rule']))


def target_hash(target):return api.sha(api.encode(target))


def save(store,candidate,expected,progress=lambda _:None,cancelled=lambda:False):
    """Prepare preset pixels off the polling thread, then atomically save settings.

    Registry and source hashes gate commit. The ordinary selected look and native
    profiles are never written. Snapshot presets remain independent of renaming.
    """
    import GameToolKeymapDocument as maps
    from GameToolKeymapBuilder import SourceLibrary,package
    validate(candidate);value,registry=store.load();index=api.validate_store(value)
    api.require(set(candidate['games'])<=set(index['games']),'Register the game before saving its alternate view')
    documents=SourceLibrary(store.directory).documents();source_hashes={g:maps.fingerprint(d) for g,d in documents.items()}
    result=copy.deepcopy(candidate);result['prepared']=[]
    root=api.no_links(store.directory);root.mkdir(parents=True,exist_ok=True)
    lock=api.no_links(root/'overlay-alternate.lock');fd=None;temp=None
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd);fd=None
    except FileExistsError as error:raise api.OverlayError('Alternate settings busy; inspect the owner before retrying') from error
    try:
        api.require(read(root)[1]==expected,'Alternate settings changed; reopen the editor')
        with tempfile.TemporaryDirectory(prefix='alternate-render-',dir=root) as folder:
            for game in index['games']:
                setting=effective(result,game);target=setting['target']
                if not setting['enabled'] or target['kind']!='preset':continue
                doc=documents.get(game)
                # Image-only/archived groups keep normal behavior. Never invent labels.
                if doc is None:continue
                package([doc],[index['keymaps'][doc['keymap_id']]])
                for group in index['groups'].values():
                    if group['game_id']!=game or group['keymap_id']!=doc['keymap_id']:continue
                    available={(index['assets'][aid]['layer'],index['assets'][aid]['context']) for aid in group['asset_ids']}
                    for n,mapping in enumerate(doc['maps']):
                        if (mapping['layer'],mapping['context']) not in available:continue
                        api.require(not cancelled(),'Alternate preparation cancelled; current settings retained')
                        progress('Preparing '+doc['title']+' / '+mapping['layer']+' / '+mapping['context'])
                        path=Path(folder)/(str(n)+'.png');maps.render(doc,mapping,path,target['style']['view'],target['style'])
                        raw=api.read(path,16*1024*1024);digest=api.sha(raw);relative='overlay-alternate-assets/'+digest+'.png'
                        destination=api.no_links(root/relative);destination.parent.mkdir(parents=True,exist_ok=True)
                        if destination.exists():api.require(api.read(destination)==raw,'Prepared image collision')
                        else:
                            with destination.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
                        result['prepared'].append(dict(game=game,group=group['id'],layer=mapping['layer'],context=mapping['context'],source_sha256=source_hashes[game],target_sha256=target_hash(target),path=relative,sha256=digest))
        validate(result)
        api.require(not cancelled(),'Alternate preparation cancelled; current settings retained')
        api.require(store.load()[1]==registry and read(root)[1]==expected,'Overlay settings changed during preparation; reopen the editor')
        api.require({g:maps.fingerprint(d) for g,d in SourceLibrary(root).documents().items()}==source_hashes,'Map sources changed during preparation; reopen the editor')
        raw=api.encode(result)
        if expected is not None:
            backup=api.no_links(root/('overlay-alternate-before-'+api.sha(expected)+'.json'))
            if backup.exists():api.require(api.read(backup,1024*1024)==expected,'Alternate recovery differs')
            else:backup.write_bytes(expected)
        fd,name=tempfile.mkstemp(prefix='alternate-settings-',dir=root);temp=Path(name)
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        api.require(read(root)[1]==expected and store.load()[1]==registry and not cancelled(),'Settings changed or preparation cancelled; reopen the editor')
        os.replace(temp,root/'overlay-alternate.json');temp=None
        api.require(read(root)[1]==raw,'Alternate settings readback differs')
        return read(root)
    finally:
        if temp is not None and temp.exists():temp.unlink()
        lock.unlink()


def relay_fields(store,index,result,asset):
    off={'AltEnabled':'0'}
    try:
        settings,_=read(store.directory);setting=effective(settings,result['game_id'])
        if not setting['enabled']:return off
        group=index['groups'][result['group_id']];target=setting['target'];style=group['rendering']
        if target['kind']=='view':
            matches=[index['assets'][aid] for aid in group['asset_ids'] if all(index['assets'][aid][k]==asset[k] for k in ('layer','context')) and index['assets'][aid]['view']==target['view']]
            if len(matches)!=1:return off
            alternate=matches[0];store.asset(alternate);path=alternate['path'];digest=alternate['sha256']
            warm=[index['assets'][aid] for aid in group['asset_ids'] if index['assets'][aid]['context']==asset['context'] and index['assets'][aid]['view']==target['view']][:8]
        else:
            from GameToolKeymapDocument import load,fingerprint
            doc=load(store.directory/'keymap-documents'/f"{result['game_id']}.json")
            matches=[r for r in settings['prepared'] if (r['game'],r['group'],r['layer'],r['context'],r['source_sha256'],r['target_sha256'])==(result['game_id'],group['id'],asset['layer'],asset['context'],fingerprint(doc),target_hash(target))]
            if len(matches)!=1:return off
            row=matches[0];path=row['path'];digest=row['sha256'];style=looks.rendering(target['style'])
            warm=[r for r in settings['prepared'] if r['game']==result['game_id'] and r['group']==group['id'] and r['context']==asset['context'] and r['source_sha256']==fingerprint(doc) and r['target_sha256']==target_hash(target)][:8]
            api.require(api.sha(api.read(api.no_links(store.directory/path),16*1024*1024))==digest,'Alternate prepared image changed')
        data=dict(AltEnabled='1',AltDouble=str(int(setting['double_press'])),AltWindowMs=str(setting['window_ms']),AltBehavior=setting['behavior'],AltChord=';'.join(setting['chord']),AltIdentity=api.sha(api.encode([result['game_id'],setting])),AltFile=str((store.directory/path).absolute()),AltSHA256=digest)
        data.update({'Alt_'+k:str(v) for k,v in style.items()})
        data['AltWarmCount']=str(len(warm))
        for n,hint in enumerate(warm,1):
            data['AltWarmFile'+str(n)]=str((store.directory/hint['path']).absolute());data['AltWarmSHA256'+str(n)]=hint['sha256']
        return data
    except (OSError,ValueError,KeyError):return off # A bad optional look cannot disable normal Hold.
