"""Bounded, read-only controller inventory and explicit XInput hold sampling.

Local identifiers are private machine references. They are not hardware
attestation, public fingerprints, physical button maps or accepted game routes.
No remap, rumble, input injection, device disable or reconnection API exists.
"""
from __future__ import annotations
import ctypes
import datetime
import hashlib
import itertools
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path, PureWindowsPath

VERSION = "0.1.0"
MAX_BYTES = 2 * 1024 * 1024
MAX_DEVICES = 256
MAX_RELATION_FILES = 8
DEFAULT_REWASD = Path("C:/ProgramData/Disc-Soft/reWASD")
BUTTONS = {1:"DPAD_UP",2:"DPAD_DOWN",4:"DPAD_LEFT",8:"DPAD_RIGHT",16:"START",32:"BACK",
           64:"LEFT_THUMB",128:"RIGHT_THUMB",256:"LEFT_SHOULDER",512:"RIGHT_SHOULDER",
           4096:"A",8192:"B",16384:"X",32768:"Y"}

# Fixed system query: no supplied path, profile, label or command is interpolated.
PNP_QUERY = r"""$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
$rows=@(Get-PnpDevice -PresentOnly | Where-Object {
 $_.Class -in @('Xbox360Peripheral','XnaComposite','XboxComposite','XUSB') -or
 ($_.Class -in @('HIDClass','USB') -and $_.FriendlyName -match 'Vader|Flydigi|Azeron|gamepad|game controller|joystick')
} | Select-Object -First 257 | ForEach-Object {
 $p=@(Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName @(
 'DEVPKEY_Device_Parent','DEVPKEY_Device_ContainerId','DEVPKEY_Device_EnumeratorName') -ErrorAction SilentlyContinue)
 $fields=@{};foreach($v in $p){$fields[$v.KeyName]=$v.Data}
 [pscustomobject]@{InstanceId=$_.InstanceId;Label=$_.FriendlyName;Class=$_.Class;Status=$_.Status;
 Parent=$fields['DEVPKEY_Device_Parent'];ContainerId=[string]$fields['DEVPKEY_Device_ContainerId'];
 Enumerator=$fields['DEVPKEY_Device_EnumeratorName']}
})
[pscustomobject]@{user_sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value;devices=$rows} |
 ConvertTo-Json -Depth 4 -Compress
"""

def _stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _id(kind, value):
    # Kept only in private machine data. Never publish these identifier hashes.
    text = "GameTools.ControllerInventory.v1\0" + kind + "\0" + str(value).strip().casefold()
    return kind + "-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]

def _label(value, default="Controller"):
    value = re.sub(r"[\x00-\x1f\x7f]", " ", str(value or default))
    value = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "", value, flags=re.I)
    value = re.sub(r"\b[0-9a-f]{12,}\b", "", value, flags=re.I)
    if re.search(r"[a-z]:[\\/]|\\\\|(?:HID|USB)\\",value,re.I):return default
    return " ".join(value.split())[:120] or default

def _container(value):
    value = str(value or "").strip().strip("{}").casefold()
    if re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}",value) and value != "00000000-0000-0000-0000-000000000000":
        return value
    return None

def _read_json(path):
    path=Path(path)
    for p in (path,*path.parents):
        if p.is_symlink() or getattr(p,"is_junction",lambda:False)():
            raise ValueError("Linked native metadata is not read")
    with path.open("rb") as f: raw=f.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError("Native metadata exceeds the read budget")
    return json.loads(raw.decode("utf-8-sig"))

def _system_directory():
    buffer=ctypes.create_unicode_buffer(32768)
    get_directory=ctypes.WinDLL("kernel32.dll").GetSystemDirectoryW
    get_directory.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32];get_directory.restype=ctypes.c_uint32
    count=get_directory(buffer,len(buffer))
    if not count or count>=len(buffer):raise ValueError("Windows system directory unavailable")
    return Path(buffer.value)

def windows_pnp():
    if os.name != "nt":return {"devices":[],"warnings":["Windows PnP inventory is unavailable on this platform"]}
    exe=_system_directory()/"WindowsPowerShell/v1.0/powershell.exe"
    result=subprocess.run([str(exe),"-NoProfile","-NonInteractive","-Command",PNP_QUERY],
        capture_output=True,timeout=15,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if result.returncode:raise ValueError("Windows PnP inventory query failed")
    if len(result.stdout)>MAX_BYTES:raise ValueError("Windows inventory exceeds the read budget")
    value=json.loads(result.stdout.decode("utf-8-sig"))
    if not isinstance(value,dict):raise ValueError("Unsupported Windows inventory response")
    return value

class _Gamepad(ctypes.Structure):
    _fields_=[("buttons",ctypes.c_uint16),("left_trigger",ctypes.c_uint8),("right_trigger",ctypes.c_uint8),
              ("left_x",ctypes.c_int16),("left_y",ctypes.c_int16),("right_x",ctypes.c_int16),("right_y",ctypes.c_int16)]
class _State(ctypes.Structure):
    _fields_=[("packet",ctypes.c_uint32),("gamepad",_Gamepad)]
class _Vibration(ctypes.Structure):
    _fields_=[("left",ctypes.c_uint16),("right",ctypes.c_uint16)]
class _Capabilities(ctypes.Structure):
    _fields_=[("type",ctypes.c_uint8),("subtype",ctypes.c_uint8),("flags",ctypes.c_uint16),
              ("gamepad",_Gamepad),("vibration",_Vibration)]

class XInput:
    """Only documented GetCapabilities/GetState; never obtain an output function."""
    def __init__(self):self.dll=None;self.api=None
    def _load(self):
        if self.dll is not None:return
        if os.name!="nt":raise ValueError("XInput is unavailable on this platform")
        for name in ("xinput1_4.dll","xinput9_1_0.dll"):
            try:self.dll=ctypes.WinDLL(str(_system_directory()/name));self.api=name;break
            except OSError:continue
        if self.dll is None:raise ValueError("No supported Windows XInput library")
        self.dll.XInputGetCapabilities.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(_Capabilities)]
        self.dll.XInputGetCapabilities.restype=ctypes.c_uint32
        self.dll.XInputGetState.argtypes=[ctypes.c_uint32,ctypes.POINTER(_State)]
        self.dll.XInputGetState.restype=ctypes.c_uint32
    def read(self,include_state=False):
        self._load();rows=[]
        for index in range(4):
            c=_Capabilities();code=int(self.dll.XInputGetCapabilities(index,0,ctypes.byref(c)))
            row={"index":index,"present":code==0,"error_code":code,"device_id":None,
                 "identity_status":"XInput index is a session slot, not a physical identity","api":self.api}
            if code==0:
                row["capabilities"]={"type":int(c.type),"subtype":int(c.subtype),"flags":int(c.flags)}
                if include_state:
                    s=_State();state_code=int(self.dll.XInputGetState(index,ctypes.byref(s)))
                    if state_code==0:
                        row["state"]={name:int(getattr(s.gamepad,name)) for name,_ in _Gamepad._fields_}
                    else:row.update(present=False,error_code=state_code)
            rows.append(row)
        return rows

def _kind(row):
    text=" ".join(str(row.get(x,"")) for x in ("InstanceId","Parent","Enumerator","Label"))
    if re.search(r"vigem|rewasd|rwr[dv]|virtual",text,re.I):return "virtual","inferred from software-device metadata"
    if str(row.get("Enumerator","")).upper() in {"USB","BTH","BTHLE"}:
        return "physical","inferred from enumerator; virtual USB hubs can resemble physical endpoints"
    return "unknown","not established by the available metadata"

def _controller_evidence(row):
    if str(row.get("Class","")).casefold() in {"xbox360peripheral","xnacomposite","xboxcomposite","xusb"}:
        return "Windows controller class"
    if re.search(r"game controller|gamepad|joystick|vader|flydigi|azeron",str(row.get("Label","")),re.I):
        return "Controller description; verify actual physical source"
    return None

def _controls(state,axis_threshold=8000):
    if not isinstance(state,dict):return frozenset()
    bits=int(state.get("buttons",0));result={name for mask,name in BUTTONS.items() if bits&mask}
    for name in ("left_trigger","right_trigger"):
        if int(state.get(name,0))>=32:result.add(name.upper())
    for name in ("left_x","left_y","right_x","right_y"):
        v=int(state.get(name,0))
        if abs(v)>=axis_threshold:result.add(name.upper()+("+" if v>0 else "-"))
    return frozenset(result)

class Inventory:
    def __init__(self,*,pnp_provider=None,xinput_provider=None,rewasd_root=None,monotonic=None,sleep=None):
        self.pnp_provider=pnp_provider or windows_pnp
        self.xinput_provider=xinput_provider or XInput().read
        self.rewasd_root=Path(rewasd_root) if rewasd_root is not None else DEFAULT_REWASD
        self.monotonic=monotonic or time.monotonic;self.sleep=sleep or time.sleep

    def _rewasd(self,user_sid,devices,relationships,warnings,containers):
        result={"available":False,"state_basis":"saved_metadata_not_live","devices":[],"relations":[],"warnings":[]}
        try:
            collection=_read_json(self.rewasd_root/"GamepadCollection.json")
            if not isinstance(collection,list) or len(collection)>MAX_DEVICES:raise ValueError("Unsupported reWASD collection")
        except FileNotFoundError:return result
        except (ValueError,OSError)as error:
            result["warnings"].append("Native collection could not be read ("+type(error).__name__+")");return result
        result["available"]=True;guid_map={}
        for group in collection:
            if not isinstance(group,dict):continue
            members=[group] if group.get("DataType")=="Controller" else group.get("Controllers",[])
            if not isinstance(members,list) or len(members)>32:
                result["warnings"].append("Unsupported reWASD member collection");continue
            for member in members:
                if not isinstance(member,dict):continue
                identity=member.get("Guid") or group.get("Guid")
                if not identity:continue
                info=member.get("ManufacturerInfo",{})
                if not isinstance(info,dict):info={}
                label=info.get("ContainerDescription") or info.get("ProductName") or info.get("Description") or member.get("ControllerType")
                cid=_container(member.get("ContainerId") or group.get("ContainerId"))
                identifier=_id("rw-device",identity)
                if len(devices)>=MAX_DEVICES:
                    result["warnings"].append("Combined device count budget reached");return result
                d={"id":identifier,"label":_label(label),"kind":"unknown","present":None,
                   "source":"rewasd_saved_collection","identity_status":"saved source identity; present state not established",
                   "controller_type":_label(member.get("ControllerType"),"Unknown"),
                   "connection_mode":_label(member.get("ConnectionType"),"Unknown"),
                   "exclusive_access_supported":member.get("IsExclusiveAccessSupported"),
                   "exclusive_access_failed":member.get("IsExclusiveAccessFailed")}
                controller_type=str(member.get("ControllerType", ""))
                eligible=bool(controller_type and not re.search(r"keyboard|mouse|consumer|system|sendinput|unknown",controller_type,re.I))
                d["eligible_primary"]=eligible
                d["controller_evidence"]="Saved native controller family; presence unverified" if eligible else "Saved feeder/interface only"
                if cid:d["group_id"]=_id("container",cid)
                for k,n in (("VendorId","vid"),("ProductId","pid")):
                    if type(info.get(k))is int and 0<=info[k]<=65535:d[n]=format(info[k],"04x")
                devices.append(d);result["devices"].append(identifier)
                guid_map[str(identity).casefold()]=identifier
                guid_map.setdefault(str(group.get("Guid",identity)).casefold(),identifier)
                if cid in containers:
                    relationships.append({"source_id":identifier,"target_id":containers[cid],"status":"observed",
                        "kind":"same-container","basis":"Exact saved reWASD and current PnP ContainerId equality; not a physical output test"})
        if not user_sid:
            result["warnings"].append("Current user identity unavailable; per-user assignment files were not read")
            return result
        paths=list(itertools.islice(self.rewasd_root.glob("GamepadProfileUserRelations_*.json"),MAX_RELATION_FILES+1))
        if len(paths)>MAX_RELATION_FILES:
            result["warnings"].append("Too many per-user relation files; none read");return result
        encoded=str(user_sid).replace("-","")
        paths=[p for p in paths if p.name=="GamepadProfileUserRelations_"+encoded+".json"]
        if len(paths)!=1:
            result["warnings"].append("No unique current-user native assignment file");return result
        try:
            value=_read_json(paths[0])
            if not isinstance(value,dict) or len(value)>MAX_DEVICES:raise ValueError("Unsupported reWASD assignments")
            for raw_id,row in value.items():
                if not isinstance(row,dict):continue
                source_id=guid_map.get(str(raw_id).casefold())
                if source_id is None:continue
                slots=row.get("SlotProfiles",{})
                if not isinstance(slots,dict) or len(slots)>4:continue
                for slot,entry in slots.items():
                    if slot not in {"Slot1","Slot2","Slot3","Slot4"} or not isinstance(entry,dict):continue
                    path=entry.get("ConfigPath")
                    if not isinstance(path,str) or len(path)>2048:continue
                    result["relations"].append({"source_id":source_id,"config_id":_id("rw-config",path),
                        "config_label":_label(PureWindowsPath(path).stem),"slot":slot,
                        "saved_remap_on":row.get("IsRemapToggled") if type(row.get("IsRemapToggled"))is bool else None,
                        "status":"observed","basis":"Current-user saved assignment; no live remap or output acceptance"})
        except (ValueError,OSError)as error:result["warnings"].append("Native assignments could not be read ("+type(error).__name__+")")
        return result

    def snapshot(self,include_state=False):
        if type(include_state)is not bool:raise ValueError("include_state is a boolean")
        warnings=[];devices=[];relationships=[];containers={};raw_to_safe={};user_sid=None
        try:
            raw=self.pnp_provider()
            if not isinstance(raw,dict):raise ValueError("Unsupported PnP response")
            rows=raw.get("devices",[]);user_sid=raw.get("user_sid")
            if not isinstance(rows,list) or len(rows)>MAX_DEVICES:raise ValueError("PnP device count exceeds budget")
            warnings.extend(_label(x) for x in raw.get("warnings",[])[:16])
            for row in rows:
                if not isinstance(row,dict) or not isinstance(row.get("InstanceId"),str):continue
                identifier=_id("pnp",row["InstanceId"]);raw_to_safe[row["InstanceId"].casefold()]=identifier
                cid=_container(row.get("ContainerId"));kind,reason=_kind(row)
                d={"id":identifier,"label":_label(row.get("Label")),"kind":kind,"present":True,
                   "class":_label(row.get("Class"),"Unknown"),"source":"windows_pnp",
                   "identity_status":"inferred","classification_reason":reason,
                   "status":_label(row.get("Status"),"Unknown"),
                   "eligible_primary":bool(_controller_evidence(row)),"controller_evidence":_controller_evidence(row)}
                ids=re.search(r"VID_([0-9a-f]{4}).*PID_([0-9a-f]{4})",row["InstanceId"],re.I)
                if ids:d.update(vid=ids[1].lower(),pid=ids[2].lower())
                if cid:
                    d["group_id"]=_id("container",cid)
                    if cid in containers:
                        relationships.append({"source_id":identifier,"target_id":containers[cid],"status":"observed",
                            "kind":"same-container","basis":"Equal current PnP ContainerId; not an input routing test"})
                    else:containers[cid]=identifier
                devices.append(d)
            for row in rows:
                parent=row.get("Parent") if isinstance(row,dict) else None
                if isinstance(parent,str) and parent.casefold() in raw_to_safe:
                    relationships.append({"source_id":raw_to_safe[row["InstanceId"].casefold()],
                        "target_id":raw_to_safe[parent.casefold()],"status":"observed","kind":"pnp-parent","basis":"Current PnP parent metadata"})
        except (ValueError,OSError,subprocess.SubprocessError)as error:warnings.append("PnP unavailable ("+type(error).__name__+")")
        try:xinput=self.xinput_provider(include_state=include_state)
        except (ValueError,OSError)as error:xinput=[];warnings.append("XInput unavailable ("+type(error).__name__+")")
        rewasd=self._rewasd(user_sid,devices,relationships,warnings,containers)
        return {"schema_version":1,"captured_utc":_stamp(),"identity_scope":"private_machine_data_only",
                "devices":devices,"xinput":xinput,"rewasd":rewasd,"relationships":relationships,
                "capabilities":{"read_only":True,"hold_sampling":True,"disconnect":False,"reconnect":False,
                                "native_remap":False,"physical_slot_association":False},"warnings":warnings}

    def sample_hold(self,duration=3,*,interval=0.05,min_hold=0.3,cancel=None):
        if type(duration)not in (int,float) or not math.isfinite(duration) or not 0.3<=duration<=5:raise ValueError("Hold window is 0.3–5 seconds")
        if type(interval)not in (int,float) or not math.isfinite(interval) or not 0.05<=interval<=0.25:raise ValueError("Sampling interval is 50–250 ms")
        if type(min_hold)not in (int,float) or not math.isfinite(min_hold) or not 0.15<=min_hold<=duration:raise ValueError("Use a bounded sustained hold")
        start=self.monotonic();neutral={};active={};best={};prior=None;interrupted=set();cancelled=False;frames=0
        for _ in range(math.ceil(duration/interval)+2):
            now=self.monotonic();elapsed=now-start
            if elapsed>duration+0.000001:break
            if cancel is not None and cancel():cancelled=True;break
            rows=self.xinput_provider(include_state=True)
            if not isinstance(rows,list) or len(rows)>4:raise ValueError("Unsupported XInput sample")
            present={r['index'] for r in rows if r.get('present') and type(r.get('index'))is int and 0<=r['index']<=3}
            if prior is not None:interrupted.update(present^prior)
            prior=present;frames+=1
            for row in rows:
                index=row.get('index')
                if index not in present:continue
                controls=_controls(row.get('state'))
                if not controls:
                    if index in active:
                        controls0,at=active.pop(index);held=elapsed-at
                        if held>=min_hold:best[index]={"index":index,"controls":sorted(controls0),"held_seconds":round(held,3),"release_observed":True}
                    neutral[index]=True
                elif neutral.get(index):
                    if index not in active or active[index][0]!=controls:active[index]=(controls,elapsed)
                    held=elapsed-active[index][1]
                    if held>=min_hold:best[index]={"index":index,"controls":sorted(controls),"held_seconds":round(held,3),"release_observed":False}
            self.sleep(interval)
        candidates=[best[i] for i in sorted(best) if i not in interrupted]
        ambiguous=len(candidates)>1
        status="cancelled" if cancelled else "interrupted" if interrupted else "ambiguous" if ambiguous else "candidate" if candidates else "no_candidate"
        return {"schema_version":1,"captured_utc":_stamp(),"status":status,"candidates":candidates,
                "ambiguous":ambiguous,"interrupted_indices":sorted(interrupted),"frames":frames,
                "duration_seconds":duration,"baseline_required":"neutral before sustained hold",
                "selected_device_id":None,"physical_identity_verified":False,
                "explanation":"XInput slots cannot prove a physical source; mirrored or multiple candidates are not automatically selected.",
                "state_saved":False,"input_injected":False}

def export_summary(snapshot):
    """Sanitized report with no local identifier hashes, paths or relationships."""
    return {"schema_version":1,"captured_utc":snapshot.get("captured_utc"),
        "devices":[{k:d.get(k) for k in ("label","kind","present","class","source","identity_status","classification_reason") if k in d}
                   for d in snapshot.get("devices",[])],
        "xinput":[{"index":x.get("index"),"present":x.get("present"),"identity_status":"Session slot only"} for x in snapshot.get("xinput",[])],
        "native_metadata_available":snapshot.get("rewasd",{}).get("available",False),
        "notes":["Local device/group/config identifiers and native assignments omitted.","Input state and user identities omitted."]}
