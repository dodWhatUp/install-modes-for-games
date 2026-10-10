#!/usr/bin/env python3
"""Compile four separately named Cyborg II Software v2 profiles from a real backup.

Only reads source files. Writes new candidate profile files
and an optional augmented *full backup*. Delivery packaging is separate. It never installs or imports anything.
"""
import argparse, copy, datetime, hashlib, json, pathlib, re, uuid, zipfile

NAMES = {"BASIC": "SHARED R5 - BASIC", "NUMBERS": "SHARED R5 - NUMBERS",
         "LETTERS": "SHARED R5 - LETTERS", "TOOLS": "SHARED R5 - TOOLS"}
MAP_BLOB = "b689507023491d7eafb28dd886a18923dbf2ae08"
SPECIAL = {"Esc":"Escape", "Space":"Space", "Enter":"Enter", "Tab":"Tab",
 "Backspace":"Backspace", "Caps Lock":"CapsLock", "Page Up":"PageUp",
 "Page Down":"PageDown", "Home":"Home", "End":"End", "Insert":"Insert",
 "Delete":"Delete", "Up Arrow":"ArrowUp", "Down Arrow":"ArrowDown",
 "Left Arrow":"ArrowLeft", "Right Arrow":"ArrowRight", "Minus":"Minus",
 "Equals":"Equal", "Backtick":"Backquote", "Left Bracket":"BracketLeft",
 "Right Bracket":"BracketRight", "Comma":"Comma", "Period":"Period",
 "Slash":"Slash", "Backslash":"Backslash", "Semicolon":"Semicolon",
 "Apostrophe":"Quote"}
MODIFIERS = {"Ctrl":"ControlLeft", "Shift":"ShiftLeft", "Alt":"AltLeft"}
def dump(x): return (json.dumps(x, ensure_ascii=False, indent=2)+"\n").encode("utf-8")
def sha(x): return hashlib.sha256(x).hexdigest()
def blob(x): return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def load(data): return json.loads(data.decode("utf-8-sig"))
def code(key):
    if key in SPECIAL: return SPECIAL[key]
    if re.fullmatch("[A-Z]",key): return "Key"+key
    if re.fullmatch("[0-9]",key): return "Digit"+key
    if re.fullmatch(r"F(?:[1-9]|1[0-2])",key): return key
    raise ValueError("Unmapped logical output: "+key)
def safe_members(z):
    infos=z.infolist()
    if sum(i.file_size for i in infos)>30_000_000: raise ValueError("Backup exceeds intake budget")
    for i in infos:
        p=pathlib.PurePosixPath(i.filename)
        if p.is_absolute() or ".." in p.parts or i.flag_bits&1: raise ValueError("Unsafe/encrypted ZIP member")
    if len({i.filename for i in infos})!=len(infos): raise ValueError("Duplicate ZIP members")
    return infos
def main(source, designpath, output):
    output.mkdir(parents=True,exist_ok=False)
    src=source.read_bytes(); rawdesign=designpath.read_bytes()
    if blob(rawdesign)!=MAP_BLOB: raise ValueError("Expected the reviewed R3 design, not an unknown revision")
    design=load(rawdesign)
    with zipfile.ZipFile(source) as z:
        infos=safe_members(z)
        original={i.filename:z.read(i) for i in infos}
    backup=load(original["backup-data.json"])
    if backup["version"]!="2.0.2": raise ValueError("A different app version needs a fresh schema review")
    storekey="sw-profile-store:sw-profile-store"
    sw=load(backup["stores"][storekey].encode())
    pid=str(sw["state"]["activeDevicePid"])
    dd=sw["state"]["deviceData"][pid]
    tags={t["id"]:t["label"] for t in dd["profileTagData"]}
    pref="storage/DevicesStorage/"+pid+"/ProfileStorage/"
    ps={load(b)["id"]:load(b) for n,b in original.items() if n.startswith(pref+"profile_") and n.endswith(".json")}
    bases=[p for p in ps.values() if p["name"]=="LAYER - 1 BASIC" and any(tags.get(t)=="layered 1" for t in p["profileTags"])]
    if len(bases)!=1: raise ValueError("Ambiguous current user-authored base")
    base=bases[0]
    byid={b["id"]:b for b in base["inputs"]}
    ui=load(backup["stores"]["ui-button-mapper:azeron-ui-button-mapper"].encode())
    area=ui["state"]["mapperAreas"][str(base["metaData"]["device"])]
    grid=[list(map(int,re.findall(r"b(\d+)",row))) for row in area.splitlines() if '"' in row]
    pos={f"R{r}C{c}":grid[r][c] for r in range(1,6) for c in range(1,5)}
    pos.update({"L3":grid[3][0],"R3":grid[3][5],"TH_U":grid[0][7],"TH_L":grid[1][6],
      "TH_C":grid[1][7],"TH_R":grid[1][8],"TH_D":grid[2][7],
      "ST_RU":grid[3][8],"ST_RD":grid[4][8],"ST_D":grid[5][6]})
    if len(set(pos.values()))!=30 or not set(pos.values()).issubset(byid): raise ValueError("Unexpected geometry")
    # Cross-check recognizable source outputs rather than trusting a shape alone.
    if [pos[x] for x in ("R4C2","R4C3","R4C4","L3","R3C1","R4C1")] != [5,9,14,36,2,1]:
        raise ValueError("Unexpected Cyborg II visual/native correspondence")
    for key,num,target in [("L3",36,"LAYER - 1 MOD KEYS"),("R3C1",2,"LAYER - 1 NUMBER"),("R4C1",1,"LAYER - 1 MENU")]:
        b=byid[num]
        if b["types"]!=["24","11","11"] or b.get("isBelkin") or not b.get("isToggleOnHold"):
            raise ValueError("Current user layer gesture differs from this reviewed candidate")
        if ps[b["layeringProfileId"]]["name"]!=target: raise ValueError("Unexpected current layer target")
    ids={bank:str(uuid.uuid4()) for bank in NAMES}
    assert not set(ids.values())&set(ps)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
    # The native fields createdBy/softwareVersion are compatibility version labels,
    # not an assertion that the official application generated these candidates.
    template=copy.deepcopy(byid[23])
    selectors={"NUMBERS":2,"LETTERS":1,"TOOLS":36}
    def clean_input(nativeid):
        k=copy.deepcopy(template)
        for field in ("id","pinOne","pinTwo"): k[field]=byid[nativeid][field]
        k["types"]=["11","11","11"]; k["label"]=""
        for suffix in ("","Long","Double"):
            k["keyValues"+suffix]=["0"]*4; k["metaValues"+suffix]=["0"]*3
            k["layeringProfileId"+suffix]=""
            k["isBelkin"+suffix]=False; k["isToggleOnHold"+suffix]=False
            k["isHold"+suffix]=False; k["holdTime"+suffix]=0
            k["isTurbo"+suffix]=False; k["turboInterval"+suffix]=0
        for f in ("macro","longMacro","doubleMacro"): k[f]={"repeat":False,"steps":[],"v":1}
        k["sequenceTriggerSettings"]={"sequenceSteps":[],"isPingPongLoop":False}
        return k
    candidates={}; emitted={}; links=[]; deviations=[]
    for bank in NAMES:
        p=copy.deepcopy(base);p["id"]=ids[bank];p["name"]=NAMES[bank]
        p["isFavorite"]=False;p["isSoftware"]=True
        # Tags are global-store objects, not embedded tag definitions in a single
        # profile. Plain JSON candidates use no unresolved tag references.
        p["profileTags"]=[];p["systemTags"]=["LAYERING"]
        p["metaData"]={"schemeName":base["metaData"]["schemeName"],"device":base["metaData"]["device"],
          "createdAt":stamp,"createdBy":"2.0.2",
          "changedLogs":[{"timestampt":stamp,"softwareVersion":"2.0.2","type":"created"}]}
        newbyid={x["id"]:copy.deepcopy(x) for x in p["inputs"]}
        emitted[bank]={}
        for visual,key in design["maps"][bank].items():
            nativeid=pos[visual]; b=clean_input(nativeid);emitted[bank][visual]=key
            if key.startswith("LAYER:"):
                target=key[6:]
                if bank=="BASIC" or nativeid==selectors[bank]:
                    actual=target if bank=="BASIC" else "BASIC"
                    b.update(types=["24","11","11"],layeringProfileId=ids[actual],
                             isBelkin=False,isToggleOnHold=True,
                             label=(actual+" - HOLD") if bank=="BASIC" else "RETURN TO BASIC")
                    links.append({"bank":bank,"button_id":nativeid,"target":actual})
                else:
                    # No nested momentary layers in this first import candidate.
                    deviations.append({"bank":bank,"button_id":nativeid,"visual":visual,
                      "design":key,"native":"UNASSIGNED","reason":"Release the active layer selector before selecting another bank."})
                    emitted[bank][visual]="UNASSIGNED"
            elif key!="UNASSIGNED":
                b["types"]=["1","11","11"];b["label"]=key
                if key in MODIFIERS:b["metaValues"][0]=MODIFIERS[key]
                else:b["keyValues"][0]=code(key)
            newbyid[nativeid]=b
        # Preserve the complete original BASIC joystick input, not just WASD labels.
        assert newbyid[24]==byid[24]
        p["inputs"]=[newbyid[x["id"]] for x in base["inputs"]]
        candidates[bank]=p
    # Validate all actively referenced layer IDs; no dependency on original profiles.
    for bank,p in candidates.items():
        assert len(p["inputs"])==len(base["inputs"])==43
        assert len({b["id"] for b in p["inputs"]})==43
        for b in p["inputs"]:
            assert b["pinOne"]==byid[b["id"]]["pinOne"] and b["pinTwo"]==byid[b["id"]]["pinTwo"]
            if b["id"] in pos.values():
                assert b["types"][1:]==["11","11"]
                for s in ("","Long","Double"):
                    assert not b["isHold"+s] and not b["isTurbo"+s]
                assert not any(b[f]["steps"] for f in ("macro","longMacro","doubleMacro"))
                if b["types"][0]=="24":assert b["layeringProfileId"] in ids.values()
    represented={v for bank in emitted.values() for v in bank.values() if v!="UNASSIGNED" and not v.startswith("LAYER:")} | set("WASD")
    assert represented==set(design["target_keys"]) and len(represented)==78
    profdir=output/"profiles";profdir.mkdir()
    jsonbytes={}
    for i,(bank,p) in enumerate(candidates.items(),1):
        filename=f"{i:02d}_{NAMES[bank].replace(' - ','_').replace(' ','_')}.json"
        jsonbytes[bank]=dump(p);(profdir/filename).write_bytes(jsonbytes[bank])
    # Augment the original *full backup*, preserving every existing profile byte.
    patched=copy.deepcopy(backup);new_sw=copy.deepcopy(sw);newdd=new_sw["state"]["deviceData"][pid]
    ma=max((int(x["sortIndex"]) for x in newdd["profileOrderList"]),default=-1)
    newdd["profileOrderList"] += [{"profileId":ids[bank],"sortIndex":ma+i+1} for i,bank in enumerate(NAMES)]
    tagid=uuid.uuid4().hex[:8]
    while tagid in tags:tagid=uuid.uuid4().hex[:8]
    newdd["profileTagData"].append({"id":tagid,"label":"SHARED R5","color":"#459f9d"})
    patched["stores"][storekey]=json.dumps(new_sw,ensure_ascii=False,separators=(",",":"))
    # Keep original timestamp: this file augments that exact snapshot, not live state.
    target=output/"Azeron_Backup_PLUS_SHARED_R5.zip"
    with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for info in infos:z.writestr(info,dump(patched) if info.filename=="backup-data.json" else original[info.filename])
        for bank,p in candidates.items():
            q=copy.deepcopy(p);q["profileTags"]=[tagid]
            z.writestr(pref+"profile_"+q["id"]+".json",dump(q))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for n,b in original.items():
            if n!="backup-data.json":assert z.read(n)==b
        check=load(z.read("backup-data.json"))
        assert check["timestamp"]==backup["timestamp"] and check["version"]==backup["version"]
        for key,value in backup["stores"].items():
            if key!=storekey:assert check["stores"][key]==value
        checksw=load(check["stores"][storekey].encode());checkdd=checksw["state"]["deviceData"][pid]
        for key,val in dd.items():
            if key not in ("profileOrderList","profileTagData"):assert checkdd[key]==val
        assert checkdd["profileOrderList"][:len(dd["profileOrderList"]) ]==dd["profileOrderList"]
        assert checkdd["profileTagData"][:len(dd["profileTagData"]) ]==dd["profileTagData"]
        assert len([n for n in z.namelist() if n.startswith(pref+"profile_")])==len(ps)+4
    authored=[p for p in ps.values() if any(tags.get(t) in ("layered 1","FOR CHAT") for t in p["profileTags"])]
    record={"status":"NATIVE_CANDIDATE_FILES_CREATED_NOT_IMPORTED","generated_at":stamp,
      "source_backup_sha256":sha(src),"source_backup_timestamp":backup["timestamp"],"app_version":backup["version"],
      "device_model":"Azeron Cyborg II","device_model_code":base["metaData"]["device"],"product_id":int(pid),
      "source_software_profiles":len(ps),"user_authored_tagged_profiles":len(authored),
      "unattributed_other_profiles":len(ps)-len(authored),"new_profiles":4,
      "authorship_note":"User identifies only layered 1 and FOR CHAT as user-made. FOR CHAT is a feature demonstration, not a gaming-preference baseline.",
      "original_profiles_preserved_byte_for_byte":len(ps),"augmented_backup_profiles":len(ps)+4,
      "native_ids_from_exported_mapper":pos,"logical_output_count_including_WASD":78,
      "native_layer_links":links,"new_profile_ids":ids,"profile_names":NAMES,
      "implementation_deviations_from_R3":deviations,
      "primary_modifiers":"ControlLeft, ShiftLeft, AltLeft; explicitly chosen v2 codes, not a claim about historical generic codes.",
      "layer_gesture":"SINGLE -> Layering; Toggle on hold=true; Switch held binds on layer change=false; reciprocal same-button return. Matches current authored source, not old V/150ms setup.",
      "single_profile_json_import_tested":False,"single_profile_import_id_remapping_known":False,
      "augmented_backup_restore_tested":False,"live_button_behavior_tested":False,
      "official_app_code_inspection":"BLOCKED_BY_PLATFORM; not retried or bypassed.",
      "sha256":{"backup_plus":sha(target.read_bytes()),**{bank:sha(b) for bank,b in jsonbytes.items()}},
      "limits":["Native structure/link validation is not in-app acceptance or physical validation.",
       "The augmented archive is a full backup restore, NOT a merge into a newer live configuration.",
       "Normal individual profile import may regenerate IDs; check the three target names after importing all four.",
       "The existing R4 game-access exceptions remain open; this candidate is not optimal or complete for every game.",
       "The source backup contains software profiles and application state, not proof of a complete hardware/on-board backup."]}
    (output/"VALIDATION_AND_MANIFEST.json").write_bytes(dump(record))
    (output/"position_map.json").write_bytes(dump(pos))
    (output/"effective_logical_maps.json").write_bytes(dump(emitted))
    print(json.dumps({k:record[k] for k in ["status","app_version","source_software_profiles","new_profiles","original_profiles_preserved_byte_for_byte","logical_output_count_including_WASD"]}))
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--source-backup",type=pathlib.Path,required=True)
    a.add_argument("--design",type=pathlib.Path,required=True);a.add_argument("--output",type=pathlib.Path,required=True)
    x=a.parse_args();main(x.source_backup,x.design,x.output)
