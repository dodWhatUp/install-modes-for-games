"""Local, read-only location suggestions. Selection belongs to the native UI.

No drive crawl, executable launch, registration, binding or write permission.
Ranks express evidence strength, not a statistical probability or compatibility.
"""
from __future__ import annotations
import os,re
from pathlib import Path
from game_mod_ops.safety import ModError,contained,no_links,read_json,require,object_hash
from game_keybind_ops.core import snapshot,sha
from game_keybind_ops.documents import Document
from game_keybind_ops.store_discovery import steam_installations

ROOT=Path(__file__).resolve().parents[1]
IDENTITIES=ROOT/'examples/game-tool-hub/game-support/discovery/identities.json'

def local_path(value):
    p=Path(value)
    require(p.is_absolute() and not str(p).startswith(('//','\\\\')),'DISCOVERY_PATH','Use a local absolute folder.')
    return no_links(p)

def key(path):return os.path.normcase(str(local_path(path)))
def normal(value):return re.sub(r'[^a-z0-9]','',value.casefold())

def stamp(path,*,metadata=True):
    p=local_path(path);s=p.stat()
    result={'path':str(p),'size':s.st_size,'mtime_ns':s.st_mtime_ns,'inode':s.st_ino}
    if metadata:result['sha256']=sha(snapshot(p))
    return result

def kv(path,section):
    raw=snapshot(path);values={}
    for c in Document(raw,'keyvalues').cells:
        chain=c.selector['kv_path']
        if len(chain)==2 and chain[0][0].casefold()==section.casefold():
            name=chain[1][0].casefold()
            require(name not in values,'STORE_AMBIGUOUS','Duplicate store metadata key.')
            values[name]=c.value
    return values

def steam_roots():
    """Known Steam owner locations only; never scan drives or user data."""
    roots=[]
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam') as handle:
                roots.append(Path(winreg.QueryValueEx(handle,'SteamPath')[0]))
        except OSError:pass
        if os.environ.get('ProgramFiles(x86)'):roots.append(Path(os.environ['ProgramFiles(x86)'])/'Steam')
    else:roots.extend([Path.home()/'.local/share/Steam',Path.home()/'.steam/steam'])
    return roots

class ModDiscovery:
    def __init__(self,controls,*,stores=None,prepared=None):
        self.controls=controls
        self.stores=steam_roots() if stores is None else stores
        self.prepared=[controls.data_dir.parent,Path.home()/'GameTools-Private'] if prepared is None else prepared

    def definition(self,game_id):
        row=next((r for r in self.controls.games()['games'] if r['game_id']==game_id),None)
        require(row is not None,'SELECTION_REQUIRED','Choose a known game.')
        return row,self.controls.instances._definition(game_id)[0]

    def candidate(self,game_id,folder,*,reason,score,stamps=(),instance=None,workspace=None,signal=None):
        row,definition=self.definition(game_id);game=local_path(folder)
        require(game.is_dir(),'GAME_MISSING','Game folder is missing.')
        exes=[contained(game,name) for name in definition['executable_any']]
        found=[p for p in exes if p.is_file()]
        require(found,'GAME_EXECUTABLE_MISSING','Expected game executable was not found.')
        marks=list(stamps)+[stamp(p,metadata=False) for p in found]
        return {'game_id':game_id,'name':row['name'],'game_dir':str(game),'executables':[str(p) for p in found],
            'workspace':str(workspace) if workspace else None,'instance_id':instance,'score':score,
            'reasons':[reason,'Expected executable found: '+found[0].name],
            'stamps':marks,'issues':[],'selectable':True,'signals':[signal or ('prepared' if workspace else 'registered' if instance else 'game')]}

    def prepared_candidate(self,game_id,workspace):
        require(game_id=='no-rest-for-the-wicked','ADAPTER_UNAVAILABLE','No reviewed prepared-controller detector for this game.')
        from GameToolWickedControls import WickedControls
        p=local_path(workspace);meta=p/'deployment.json';data=read_json(meta,1048576)
        require(type(data) is dict and type(data.get('game_root')) is str,'DISCOVERY_MANIFEST','Prepared controller has no game folder.')
        game=local_path(data['game_root']);engine=WickedControls(p,game);observed=engine.read()
        marks=[stamp(meta)]+[stamp(p/'app'/name) for name in ('switcher.py','mod_options.py')]
        result=self.candidate(game_id,game,reason='Prepared controller matches the reviewed adapter and game folder.',score=92,stamps=marks,workspace=p)
        result['issues']=observed['blocked']
        result['reasons'].append('Reviewed controls available; runtime compatibility is not established by discovery.')
        return result

    def _steam(self,game_id,name,warnings):
        identities=read_json(IDENTITIES,65536).get('games',{}).get(game_id,{})
        exact=identities.get('steam_app_id');results=[];seen=set()
        for source in self.stores[:8]:
            try:
                root=local_path(source)
                if not root.is_dir() or key(root) in seen:continue
                seen.add(key(root));ids=[exact] if exact else []
                # For games without a curated AppID, compare bounded AppState
                # names. Exact executable validation still gates selection.
                if not exact:
                    libs=[root];vdf=root/'steamapps/libraryfolders.vdf'
                    if vdf.is_file():
                        for cell in Document(snapshot(vdf),'keyvalues').cells:
                            chain=cell.selector['kv_path']
                            if len(chain)==3 and chain[0][0].casefold()=='libraryfolders' and str(chain[1][0]).isdigit() and chain[2][0]=='path':libs.append(local_path(cell.value))
                    require(len(libs)<=32,'DISCOVERY_LIMIT','Too many Steam libraries; use manual selection.')
                    for lib in dict.fromkeys(libs):
                        parent=lib/'steamapps'
                        if not parent.is_dir():continue
                        for index,path in enumerate(parent.glob('appmanifest_*.acf')):
                            require(index<4096,'DISCOVERY_LIMIT','Steam manifest inspection limit reached.')
                            try:
                                state=kv(path,'AppState');identity=state.get('appid','')
                                if normal(state.get('name',''))==normal(name) and re.fullmatch(r'\d{1,12}',identity):ids.append(identity)
                            except (ModError,OSError,ValueError):continue
                    require(len(set(ids))<=16,'DISCOVERY_LIMIT','Too many matching Steam records.')
                for app_id in dict.fromkeys(ids):
                    data=steam_installations(root,app_id)
                    for found in data['candidates']:
                        try:
                            game=local_path(found['install_root']);manifest=game.parent.parent/('appmanifest_'+app_id+'.acf')
                            marks=[stamp(manifest)]
                            if (root/'steamapps/libraryfolders.vdf').is_file():marks.append(stamp(root/'steamapps/libraryfolders.vdf'))
                            results.append(self.candidate(game_id,game,score=87 if exact else 78,stamps=marks,signal='steam',
                                reason=('Exact Steam AppID '+app_id if exact else 'Steam title matches '+name)+', installation record and executable agree.'))
                        except (ModError,OSError,ValueError) as e:warnings.append('Steam match needs manual review: '+str(e))
            except (ModError,OSError,ValueError) as e:warnings.append('Steam source could not be inspected: '+str(e))
        return results

    def scan(self,game_id):
        row,_=self.definition(game_id);out=[];warnings=[]
        registered=self.controls.instances.list_public(limit=64)['instances']
        prepared=[]
        for record in registered:
            if record['game_id']!=game_id:continue
            try:
                private=self.controls.instances._read(record['instance_id'])
                out.append(self.candidate(game_id,private['body']['game_dir'],reason='Previously selected locally in this app.',score=82,instance=record['instance_id']))
                binding=self.controls.binding_path(record['instance_id'])
                if binding.is_file():
                    b=read_json(binding,131072)
                    if b.get('workspace'):prepared.append(local_path(b['workspace']))
            except (ModError,OSError,ValueError) as e:warnings.append('Existing connection needs review: '+str(e))
        out.extend(self._steam(game_id,row['name'],warnings))
        if game_id=='no-rest-for-the-wicked':
            seen=set()
            for source in self.prepared[:8]:
                try:
                    root=local_path(source)
                    if key(root) in seen or not root.is_dir():continue
                    seen.add(key(root))
                    for index,p in enumerate(root.iterdir()):
                        if index>=512:warnings.append('Prepared-folder limit reached; use Browse if your folder is absent.');break
                        if normal(game_id) not in normal(p.name):continue
                        if p.is_dir() and (p/'deployment.json').is_file():prepared.append(p)
                except (ModError,OSError,ValueError) as e:warnings.append('Prepared source could not be inspected: '+str(e))
            for p in dict.fromkeys(prepared):
                try:out.append(self.prepared_candidate(game_id,p))
                except (ModError,OSError,ValueError,KeyError) as e:warnings.append('Prepared match needs manual review: '+str(e))
        merged={}
        for c in out:
            ident=key(c['game_dir'])
            if ident not in merged:merged[ident]=c;continue
            old=merged[ident]
            # Multiple valid prepared workspaces remain separate selectable
            # choices, never silently replace one controller with another.
            if old['workspace'] and c['workspace'] and key(old['workspace'])!=key(c['workspace']):
                ident+='|'+key(c['workspace']);merged[ident]=c;continue
            for field in ('reasons','stamps','issues','signals'):
                for value in c[field]:
                    if value not in old[field]:old[field].append(value)
            old['instance_id']=old['instance_id'] or c['instance_id'];old['workspace']=old['workspace'] or c['workspace']
            old['score']=max(old['score'],c['score'])
        for c in merged.values():
            c['score']=min(99,c['score']+(6 if 'prepared' in c['signals'] and 'steam' in c['signals'] else 0)+(2 if 'registered' in c['signals'] and len(c['signals'])>1 else 0))
        results=sorted(merged.values(),key=lambda c:(-c['score'],c['game_dir'],c['workspace'] or ''))
        for c in results:
            c['confidence']='High' if c['score']>=85 else 'Medium' if c['score']>=65 else 'Low'
            c['kind']='Prepared mod setup' if c['workspace'] else 'Game installation'
            c['revision']=object_hash(c['stamps'])
        return {'game_id':game_id,'candidates':results,'warnings':list(dict.fromkeys(warnings))[:24],
            'files_modified':False,'private_paths_included':True,
            'scope':'Known Steam metadata, existing app connections and shallow private controller folders. No full-drive search.',
            'ranking':'Evidence score, not a probability or mod compatibility rating.'}

    def revalidate(self,candidate):
        require(candidate.get('selectable') is True,'SELECTION_REQUIRED','Select a valid location.')
        fresh=[stamp(Path(s['path']),metadata='sha256' in s) for s in candidate['stamps']]
        require(object_hash(fresh)==candidate['revision'],'DISCOVERY_STALE','Location evidence changed. Refresh the results and select again.')
        self.candidate(candidate['game_id'],candidate['game_dir'],reason='Rechecked',score=0)
        if candidate.get('workspace'):self.prepared_candidate(candidate['game_id'],candidate['workspace'])
        return candidate
