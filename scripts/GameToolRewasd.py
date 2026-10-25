"""Bounded reWASD config references; native files remain owned by reWASD.

Discovery/preview/save never apply anything. Native commands are available only
to the separate local review dialog, never profile activation or automatic ticks.
"""
from __future__ import annotations
import json, os, re, subprocess, time, uuid
from pathlib import Path
import GameToolOverlay as overlay

VERSION = "0.1.0"
MAX_CONFIG = 1024 * 1024

def native_root():
    return Path(os.environ.get('PUBLIC', 'C:/Users/Public'))/'Documents/reWASD/Profiles'

def program_root():
    return Path(os.environ.get('ProgramW6432', os.environ.get('ProgramFiles','C:/Program Files')))/'reWASD'

def config_file(path, root=None):
    root=overlay.no_links(root or native_root());path=overlay.no_links(path)
    overlay.require(path.is_relative_to(root) and path.suffix.lower()=='.rewasd','Choose a native .rewasd file in the reWASD Profiles folder')
    overlay.require(path.is_file(),'Native reWASD config is missing')
    return path

def inspect(path, root=None):
    path=config_file(path,root);raw=overlay.read(path,MAX_CONFIG);value=overlay.decode(raw)
    overlay.require(type(value)is dict and value.get('schemaVersion')==3,'Unsupported reWASD schema; open it in reWASD')
    devices=value.get('devices');overlay.require(type(devices)is dict,'Missing reWASD device definition')
    hardware=devices.get('hardware',[]);virtual=devices.get('virtual',{});config=value.get('config',{})
    overlay.require(type(hardware)is list and type(virtual)is dict and type(config)is dict,'Invalid reWASD devices/config')
    gamepads=virtual.get('gamepads',[]);overlay.require(type(gamepads)is list,'Invalid virtual gamepads')
    outputs=[str(x.get('type','unknown')) for x in gamepads if type(x)is dict]
    # Preserve every unknown native field as bytes. A summary is not a decoder
    # of physical button geometry, active Shift state, or licensed capabilities.
    return {'path':str(path),'sha256':overlay.sha(raw),'bytes':len(raw),
      'app_version':str(value.get('appVersion','unknown')),'schema':value['schemaVersion'],
      'profile':str(config.get('appName',path.parent.parent.name)),
      'outputs':outputs,'hardware_sections':len(hardware),'raw':raw}

def discover(root=None):
    root=overlay.no_links(root or native_root())
    if not root.exists():return []
    paths=[]
    for path in root.glob('*/*/*.rewasd'):
        overlay.require(len(paths)<128,'Too many reWASD configs; choose a specific native file')
        paths.append(path)
    rows=[]
    for path in sorted(paths):
        try:
            row=inspect(path,root);row.pop('raw');row['label']=str(path.relative_to(root).with_suffix(''));rows.append(row)
        except (ValueError,OSError)as error:
            rows.append({'path':str(path),'label':str(path.relative_to(root)), 'error':str(error)})
    return rows

def validate(v):
    overlay.fields(v,'config_path config_sha256 device_name device_id slot')
    overlay.label(v['device_name']);overlay.digest(v['config_sha256'])
    overlay.require(type(v['config_path'])is str and 0<len(v['config_path'])<=2048,'Invalid native path')
    overlay.require(type(v['device_id'])is str and (v['device_id']=='' or re.fullmatch(r'[0-9]{1,24}(;[0-9]{1,24}){0,7}',v['device_id'])),'Use Copy device ID in reWASD; hardware VID/PID is not a device ID')
    overlay.require(type(v['slot'])is int and 1<=v['slot']<=4,'Choose slot 1–4')
    return v

class Native:
    def __init__(self,directory,root=None,program=None):
        self.root=overlay.no_links(root or native_root());self.program=overlay.no_links(program or program_root())
        self.private=overlay.no_links(Path(directory)/'runtime-profiles/rewasd')
    def configs(self):return discover(self.root)
    def capture(self,path,device_name,device_id='',slot=1):
        row=inspect(path,self.root)
        v={'config_path':row['path'],'config_sha256':row['sha256'],'device_name':device_name,'device_id':device_id.strip(),'slot':slot};validate(v)
        self.backup(row)
        return v
    def backup(self,row):
        self.private.mkdir(parents=True,exist_ok=True)
        target=overlay.no_links(self.private/(row['sha256']+'.rewasd'))
        if not target.exists():
            with target.open('xb')as out:out.write(row['raw']);out.flush();os.fsync(out.fileno())
        overlay.require(overlay.sha(overlay.read(target,MAX_CONFIG))==row['sha256'],'Native recovery copy differs')
        return target
    def check(self,v):
        validate(v)
        row=inspect(v['config_path'],self.root)
        overlay.require(row['sha256']==v['config_sha256'],'Native config changed; review and update the saved profile')
        saved=overlay.no_links(self.private/(v['config_sha256']+'.rewasd'))
        overlay.require(overlay.sha(overlay.read(saved,MAX_CONFIG))==v['config_sha256'],'Native recovery copy missing or changed')
        return row
    def preview(self,v,action):
        validate(v);overlay.require(action in {'apply','off'},'Unsupported native action')
        # Remap Off remains available after the config changes or is deleted.
        if action=='apply':row=self.check(v)
        else:row=None
        overlay.require(bool(v['device_id']),'Device ID is not linked. In reWASD, right-click the device → Copy device ID, then update this profile.')
        exe=overlay.no_links(self.program/'reWASDCommandLine.exe')
        overlay.require(exe.is_file(),'reWASD command-line application is unavailable')
        args=[str(exe)]
        if action=='apply':args+=['apply','--id',v['device_id'],'--path',v['config_path'],'--slot','slot'+str(v['slot'])]
        else:args+=['remap','--id',v['device_id'],'--state','off']
        return {'action':action,'device':v['device_name'],'slot':v['slot'],
          'config':v['config_path'],'sha256':v['config_sha256'],'argv':args}
    def execute_reviewed(self,v,action,expected,*,confirmed=False):
        overlay.require(confirmed,'Review the exact native operation in the local dialog first')
        proposal=self.preview(v,action)
        overlay.require(proposal==expected,'Native operation changed; review again')
        if action=='apply':self.backup(self.check(v))
        # Structured argv, fixed executable and verbs; no imported shell text.
        self.private.mkdir(parents=True,exist_ok=True)
        receipt={'action':action,'config_sha256':v['config_sha256'],'at':int(time.time()),
          'returncode':None,'physical_acceptance':'unverified'}
        try:
            result=subprocess.run(proposal['argv'],cwd=self.program,capture_output=True,text=True,timeout=15,
              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            receipt['returncode']=result.returncode
        except subprocess.TimeoutExpired as error:
            receipt['outcome']='unknown'
            raise overlay.OverlayError('Native outcome unknown after timeout; check reWASD before retrying')from error
        finally:
            with (self.private/('operation-'+uuid.uuid4().hex+'.json')).open('x')as out:json.dump(receipt,out)
        overlay.require(result.returncode==0,'reWASD command failed (code '+str(result.returncode)+'); check reWASD before retrying')
        return receipt

def open_native():
    exe=overlay.no_links(program_root()/'reWASDUI.exe')
    overlay.require(os.name=='nt' and exe.is_file(),'reWASD is unavailable on this computer')
    return subprocess.Popen([str(exe)],cwd=exe.parent,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
