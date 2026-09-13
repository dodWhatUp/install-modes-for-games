from pathlib import Path
import sys
from lupa import LuaRuntime
code=Path(__file__).with_name('init.lua').read_text(encoding='utf-8')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
events={}; hotkeys={}; files={}; written=0; tick=10000; player=true; reject=nil; inDraw=false
os.time=function() return tick end; os.clock=function() return .25 end
io.open=function(name,mode)
 if mode=='r' then if files[name]==nil then return nil end; return {read=function() return files[name] end,close=function() end} end
 return {write=function(self,...) local a={...}; for i,v in ipairs(a) do a[i]=tostring(v) end; files[name]=table.concat(a) end,close=function() end}
end
registerForEvent=function(name,callback) events[name]=callback end
registerHotkey=function(name,label,callback) hotkeys[name]=callback end
values={ResolutionScaling='DLSS',DLSS='Performance',DynamicResolutionScaling=false,DRS_TargetFPS=30,DRS_MinResolution=65,DRS_MaxResolution=85,DLSS_D=false,RayTracing=false,DLSSFrameGen=true,FrameGeneration='DLSS',DLSS_MultiFrameGeneration='x4'}
settings={GetVar=function(self,path,name)
 if values[name]==nil then return nil end
 return {GetValue=function() return values[name] end,SetValue=function(self,v)
   written=written+1
   if name==reject then error('injected rejection') end
   if name=='DRS_MinResolution' then assert(v<=values.DRS_MaxResolution) end
   if name=='DRS_MaxResolution' then assert(v>=values.DRS_MinResolution) end
   values[name]=v
 end}
end,ConfirmChanges=function() end}
Game={GetPlayer=function() return player and {} or nil end,GetSettingsSystem=function() return settings end}
ImGui={ToastType={Info=1,Warning=2},Toast={new=function(kind,ms,text) assert(inDraw); return {SetTitle=function() end} end},ShowToast=function() assert(inDraw) end}
function advance(seconds) tick=tick+seconds; events.onUpdate(seconds) end
''')
adapter=lua.execute(code)
g=lua.globals(); g.events.onInit()
assert g.written==0
def command(action,arg):
    g.advance(3)
    assert adapter.request(action,arg,'test')
    g.events.onUpdate(.1)
    g.advance(1)
command('quality','Quality')
assert g["values"].DLSS=='Quality'
command('scale','80')
assert g["values"].DRS_MinResolution==80 and g["values"].DRS_MaxResolution==80 and g["values"].DynamicResolutionScaling
command('quality','Balanced')
assert g["values"].DLSS=='Balanced' and not g["values"].DynamicResolutionScaling
before=g.written
command('scale','25'); assert g.written==before
command('rr','1'); assert not g["values"].DLSS_D
g["values"].RayTracing=True
command('rr','1'); assert g["values"].DLSS_D
command('fg','0'); assert not g["values"].DLSSFrameGen
g["values"].FrameGeneration='FSR3'
command('fg','1'); assert not g["values"].DLSSFrameGen
g["values"].FrameGeneration='DLSS'
g.player=False; before=g.written
command('quality','DLAA'); assert g.written==before
g.player=True
# Failure after an earlier field changed must restore that earlier field.
g["values"].DynamicResolutionScaling=True; g.reject='DLSS'
command('quality','Performance'); assert g["values"].DynamicResolutionScaling
g.reject=None
# A delayed engine rejection also rolls back the whole group.
g.advance(3); before=g["values"].DLSS
assert adapter.request('quality','DLAA','delayed')
g.events.onUpdate(.1); g["values"].DLSS='Performance'; g.advance(1)
assert g["values"].DLSS==before
# Stale sessions/expired commands cannot mutate settings.
g.advance(3); before=g.written
g.files['graphics-request.txt']='3|old-session|123|10000|quality|DLAA'
g.advance(1); assert g.written==before
status=g.files['graphics-status.txt'].split('|'); assert len(status)==18 and status[0]=='3'
token=status[1]
g.files['graphics-request.txt']=f'3|{token}|123|{int(g.tick)-10}|quality|DLAA'
g.advance(1); assert g.written==before
g.files['graphics-request.txt']=f'3|{token}|124|{int(g.tick)}|quality|DLAA'
g.events.onUpdate(.3); g.advance(1); assert g["values"].DLSS=='DLAA'
g.advance(3); before=g.written
g.files['graphics-request.txt']=f'3|{token}|124|{int(g.tick)}|quality|Performance'
g.advance(1); assert g.written==before
# A target must activate the engine controller without changing FG or the model.
command('quality','Performance')
fg_before=g["values"].DLSSFrameGen
command('dynamic','30,50,100')
assert g["values"].DynamicResolutionScaling and g["values"].DRS_TargetFPS==30
assert g["values"].DRS_MinResolution==50 and g["values"].DRS_MaxResolution==100
assert g["values"].DLSS=='Performance' and g["values"].DLSSFrameGen==fg_before
assert g.files['graphics-status.txt'].split('|')[17]=='30'
command('dynamic','45,90,100')
assert g["values"].DRS_TargetFPS==45 and g["values"].DRS_MinResolution==90
command('dynamic','30,50,60')
assert g["values"].DRS_MinResolution==50 and g["values"].DRS_MaxResolution==60
command('dynamic','30,90,100')
assert g["values"].DRS_MinResolution==90 and g["values"].DRS_MaxResolution==100
for invalid in ('9,50,100','241,50,100','30,49,100','30,50,101','30,80,60','30,75,75','NaN,50,100','30.5,50,100','30,50,100,90','-30,50,100'):
    before=g.written; command('dynamic',invalid); assert g.written==before
# Missing native target rejects the whole group before changing bounds.
g["values"].DRS_TargetFPS=None; before=g.written
command('dynamic','30,50,100'); assert g.written==before
g["values"].DRS_TargetFPS=30
# A rejected target restores both bounds, including crossings.
g.reject='DRS_TargetFPS'
command('dynamic','60,50,60')
assert g["values"].DRS_MinResolution==90 and g["values"].DRS_MaxResolution==100
g.reject=None
g.advance(3); assert adapter.request('dynamic','45,50,100','delayed-drs')
g.events.onUpdate(.1); g["values"].DRS_TargetFPS=30; g.advance(1)
assert g["values"].DRS_MinResolution==90 and g["values"].DRS_MaxResolution==100
assert g["values"].DRS_TargetFPS==30
command('dynamic','off'); assert not g["values"].DynamicResolutionScaling
command('dynamic','30,50,100'); command('cycle','')
assert not g["values"].DynamicResolutionScaling and g["values"].DLSS=='DLAA'
# Old protocol requests cannot reach the newer adapter.
g.advance(3); before=g.written
g.files['graphics-request.txt']=f'2|{token}|200|{int(g.tick)}|dynamic|30,50,100'
g.advance(1); assert g.written==before
g.inDraw=True; g.events.onDraw(); g.inDraw=False
print('PASS: live requests, dynamic target/bounds/crossing/rejection/rollback, F6 exit, FG/RR prerequisites, session/expiry/replay/version guards, no startup mutation, onDraw-only notifications')
