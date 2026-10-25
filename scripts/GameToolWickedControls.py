"""Reviewed adapter over the original Wicked switcher and preference transaction."""
import importlib.util
import json
from pathlib import Path
import sys
from game_mod_ops.safety import require,digest,object_hash,no_links

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'examples/no-rest-for-the-wicked-controls'
TARGETS={'loader':'version.dll','build-liberator':'Mods/BuildLiberator.dll',
         'rune-details':'Mods/RuneDetails.dll','wicked-menu':'Mods/WickedMenu.dll'}
PREFERENCES={
 'bl-runes':('build-liberator','FreelySwitchRunes'),
 'bl-gems':('build-liberator','FreelySwitchGems'),
 'rd-enabled':('rune-details','Enabled'),
 'rd-mode':('rune-details','Mode'),
 'rd-menu-row':('rune-details','AddSettingsRows'),
 'wm-hotkey':('wicked-menu','MenuHotkey')}

def module(name):
    package='_game_tools_reviewed_wicked'
    if package not in sys.modules:
        spec=importlib.util.spec_from_file_location(package,SOURCE/'__init__.py',submodule_search_locations=[str(SOURCE)])
        value=importlib.util.module_from_spec(spec);sys.modules[package]=value;spec.loader.exec_module(value)
    full=package+'.'+name
    if full not in sys.modules:
        spec=importlib.util.spec_from_file_location(full,SOURCE/(name+'.py'))
        value=importlib.util.module_from_spec(spec);sys.modules[full]=value;spec.loader.exec_module(value)
    return sys.modules[full]

def schema():
    result=[{'id':key,'label':name,'type':'bool'} for key,name in (
        ('loader','MelonLoader'),('build-liberator','Build Liberator'),('rune-details','Rune Details'),('wicked-menu','Wicked Menu'))]
    preferences=module('mod_options')
    for ident,(mod,key) in PREFERENCES.items():
        field=next(f for f in preferences.SCHEMAS[mod]['fields'] if f['key']==key)
        row={'id':ident,'label':field['label'],'type':field['type']}
        if field['type']=='enum':row['choices']=list(field['choices'])
        result.append(row)
    return result

def catalog():
    details=json.loads((SOURCE/'mod_details.json').read_text(encoding='utf-8'))['mods'];rows=[]
    for ident in TARGETS:
        row=dict(details[ident],id=ident,name={'loader':'MelonLoader','build-liberator':'Build Liberator','rune-details':'Rune Details','wicked-menu':'Wicked Menu'}[ident],
            layer='game-mods',mechanism='loader' if ident=='loader' else 'engine-plugin',enabled_field=ident,
            settings=[key for key,pair in PREFERENCES.items() if pair[0]==ident],
            requires=[] if ident=='loader' else ['loader'],claims=[('proxy:' if ident=='loader' else 'file:')+TARGETS[ident]])
        rows.append(row)
        if ident=='wicked-menu':row['hotkey_field']='wm-hotkey'
    return rows

class WickedControls:
    def __init__(self,workspace,game,*,process_check=None):
        self.workspace=no_links(Path(workspace));self.game=no_links(Path(game))
        for name in ('switcher.py','mod_options.py'):
            require(digest(self.workspace/'app'/name)==digest(SOURCE/name),'UNREVIEWED_CONTROLLER','The prepared Wicked controller needs the reviewed app update before connecting.')
        kwargs={} if process_check is None else {'process_check':process_check}
        self.switcher=module('switcher').Switcher(self.workspace,**kwargs)
        require(self.switcher.game==self.game,'GAME_MISMATCH','Prepared controls belong to a different installation.')
        require({c['id'] for c in self.switcher.components}==set(TARGETS),'UNREVIEWED_CONTROLLER','Expected the four reviewed Wicked components.')
        for c in self.switcher.components:
            require(len(c['files'])==1 and c['files'][0]['target']==TARGETS[c['id']],'UNREVIEWED_CONTROLLER','Unexpected component target in the prepared manifest.')
        self.options=module('mod_options').ModOptions(self.switcher)
    def read(self):
        state=self.switcher.inspect();values={r['id']:r['state']=='on' for r in state['components']}
        options={ident:self.options.read(ident) for ident in module('mod_options').SCHEMAS}
        for ident,(mod,key) in PREFERENCES.items():values[ident]=options[mod]['values'][key]
        hashes={target:digest(self.game/target) if (self.game/target).is_file() else None for target in TARGETS.values()}
        hashes['UserData/MelonPreferences.cfg']=options['wicked-menu']['revision']
        revision=object_hash({'files':state['revision'],'options':options['wicked-menu']['revision'],'values':values})
        return {'values':values,'hashes':hashes,'revision':revision,'state':state,
            'options_revision':options['wicked-menu']['revision'],
            'raws':{'preferences':self.options.path.read_bytes() if self.options.path.is_file() else b''},
            'blocked':[r['id']+': '+r['state'] for r in state['components'] if r['state'] in {'partial','conflict'}]}
    def apply(self,desired,native):
        current=self.read();require(current['revision']==native['revision'],'CONCURRENT_CHANGE','Wicked files or options changed; refresh and review again.')
        changes={}
        for ident,(mod,key) in PREFERENCES.items():
            if desired[ident]!=current['values'][ident]:changes.setdefault(mod,{})[key]=desired[ident]
        result=self.switcher.apply_with_options({k:desired[k] for k in TARGETS},native['state']['revision'],changes,native['options_revision'])
        require(self.read()['values']==desired,'CONTROL_VERIFY','Wicked settings did not match the reviewed selection.')
        return result
