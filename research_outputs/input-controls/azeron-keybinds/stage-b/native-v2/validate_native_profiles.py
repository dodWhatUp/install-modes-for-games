#!/usr/bin/env python3
"""Independent readback of generated native files; no device or application use."""
import argparse, collections, hashlib, json, pathlib, zipfile

KEYS={"Escape":"Esc","CapsLock":"Caps Lock","PageUp":"Page Up","PageDown":"Page Down",
"ArrowUp":"Up Arrow","ArrowDown":"Down Arrow","ArrowLeft":"Left Arrow","ArrowRight":"Right Arrow",
"Equal":"Equals","Minus":"Minus","Backquote":"Backtick","BracketLeft":"Left Bracket",
"BracketRight":"Right Bracket","Comma":"Comma","Period":"Period","Slash":"Slash",
"Backslash":"Backslash","Semicolon":"Semicolon","Quote":"Apostrophe"}
MODS={"ControlLeft":"Ctrl","ShiftLeft":"Shift","AltLeft":"Alt"}
def loads(b):return json.loads(b.decode("utf-8-sig"))
def digest(b):return hashlib.sha256(b).hexdigest()
def main(src, dest):
    manifest=loads((dest/"VALIDATION_AND_MANIFEST.json").read_bytes())
    pos=loads((dest/"position_map.json").read_bytes())
    maps=loads((dest/"effective_logical_maps.json").read_bytes())
    with zipfile.ZipFile(src) as z:
        assert z.testzip() is None
        original={i.filename:z.read(i) for i in z.infolist()}
    assert digest(src.read_bytes())==manifest["source_backup_sha256"]
    backup=loads(original["backup-data.json"])
    swkey="sw-profile-store:sw-profile-store"
    sw=json.loads(backup["stores"][swkey])
    pid=str(sw["state"]["activeDevicePid"]);dd=sw["state"]["deviceData"][pid]
    pre="storage/DevicesStorage/"+pid+"/ProfileStorage/"
    old={loads(b)["id"]:loads(b) for n,b in original.items() if n.startswith(pre+"profile_") and n.endswith(".json")}
    base=next(p for p in old.values() if p["name"]=="LAYER - 1 BASIC")
    binputs={b["id"]:b for b in base["inputs"]}
    new={}
    for file in sorted((dest/"profiles").glob("*.json")):
        p=loads(file.read_bytes());bank=next(k for k,v in manifest["new_profile_ids"].items() if v==p["id"])
        assert digest(file.read_bytes())==manifest["sha256"][bank]
        assert p["id"] not in old
        assert p["name"]==manifest["profile_names"][bank] and p["profileTags"]==[]
        assert p["metaData"]["schemeName"]==base["metaData"]["schemeName"]=="azeron-profile-v1"
        assert p["metaData"]["device"]==8 and p["isSoftware"] is True
        assert p["profileSettings"]==base["profileSettings"]
        assert len(p["inputs"])==43 and {b["id"] for b in p["inputs"]}==set(binputs)
        new[bank]=p
    decoded={};links=[]
    for bank,p in new.items():
        inp={b["id"]:b for b in p["inputs"]};decoded[bank]={}
        for k,b in inp.items():
            assert (b["pinOne"],b["pinTwo"])==(binputs[k]["pinOne"],binputs[k]["pinTwo"])
            if k not in pos.values():assert b==binputs[k]
        for visual,num in pos.items():
            b=inp[num]
            assert b["types"][1:]==["11","11"]
            assert len(b["keyValues"])==4 and len(b["metaValues"])==3
            assert all(v=="0" for k in ["keyValuesLong","keyValuesDouble","metaValuesLong","metaValuesDouble"] for v in b[k])
            assert not b["sequenceTriggerSettings"]["sequenceSteps"]
            assert all(not b[k]["steps"] and not b[k]["repeat"] for k in ["macro","longMacro","doubleMacro"])
            assert all(b["isHold"+s] is False and b["isTurbo"+s] is False for s in ["","Long","Double"])
            typ=b["types"][0]
            if typ=="24":
                target=next(k for k,v in manifest["new_profile_ids"].items() if v==b["layeringProfileId"])
                assert b["isToggleOnHold"] is True and b["isBelkin"] is False
                assert b["keyValues"]==["0"]*4 and b["metaValues"]==["0"]*3
                actual="LAYER:"+target
                links.append({"bank":bank,"button_id":num,"target":target})
            elif typ=="11":
                assert b["keyValues"]==["0"]*4 and b["metaValues"]==["0"]*3
                actual="UNASSIGNED"
            else:
                assert typ=="1" and not b["isToggleOnHold"] and not b["isBelkin"]
                nonzero=[x for x in b["keyValues"]+b["metaValues"] if x!="0"]
                assert len(nonzero)==1
                c=nonzero[0]
                actual=MODS.get(c) or KEYS.get(c) or (c[3:] if c.startswith("Key") else c[5:] if c.startswith("Digit") else c)
            expected=maps[bank][visual]
            if expected.startswith("LAYER:") and bank!="BASIC":expected="LAYER:BASIC"
            assert actual==expected,(bank,visual,actual,expected)
            decoded[bank][visual]=actual
    assert len(links)==6
    for link in links:
        if link["bank"]=="BASIC":
            assert {"bank":link["target"],"button_id":link["button_id"],"target":"BASIC"} in links
    with zipfile.ZipFile(dest/"Azeron_Backup_PLUS_SHARED_R5.zip") as z:
        assert z.testzip() is None
        assert digest((dest/"Azeron_Backup_PLUS_SHARED_R5.zip").read_bytes())==manifest["sha256"]["backup_plus"]
        for name,data in original.items():
            if name!="backup-data.json":assert z.read(name)==data,name
        updated=loads(z.read("backup-data.json"))
        assert {k:v for k,v in updated.items() if k!="stores"}=={k:v for k,v in backup.items() if k!="stores"}
        assert {k:v for k,v in updated["stores"].items() if k!=swkey}=={k:v for k,v in backup["stores"].items() if k!=swkey}
        us=json.loads(updated["stores"][swkey]); ud=us["state"]["deviceData"][pid]
        assert {k:v for k,v in ud.items() if k not in ["profileTagData","profileOrderList"]}=={k:v for k,v in dd.items() if k not in ["profileTagData","profileOrderList"]}
        assert ud["profileOrderList"][:-4]==dd["profileOrderList"]
        assert ud["profileTagData"][:-1]==dd["profileTagData"]
        assert ud["profileTagData"][-1]["label"]=="SHARED R5"
        for bank,p in new.items():
            q=loads(z.read(pre+"profile_"+p["id"]+".json"))
            assert q["profileTags"]==[ud["profileTagData"][-1]["id"]]
            assert {k:v for k,v in p.items() if k!="profileTags"}=={k:v for k,v in q.items() if k!="profileTags"}
        numprof=len([n for n in z.namelist() if n.startswith(pre+"profile_") and n.endswith(".json")])
        assert numprof==22
    result={"status":"INDEPENDENT_STATIC_READBACK_PASS","mapped_cells_decoded":120,
       "native_input_records_checked":172,"independent_layer_links_checked":6,
       "original_profile_bytes_preserved":18,"profile_settings_and_joystick_preserved":True,
       "source_zip_unchanged":digest(src.read_bytes())==manifest["source_backup_sha256"],
       "new_ids_disjoint_from_original":True,"new_uuid_targets_resolve_in_files":True,
       "augmented_backup_crc_valid":True,"augmented_backup_profile_count":numprof,
       "global_stores_except_append_only_software_index_preserved":True,
       "template_additional_nonvisual_inputs_preserved":True,
       "gameplay_verified":False,"importer_acceptance_verified":False,
       "importer_id_remapping_verified":False,"physical_hold_release_verified":False}
    (dest/"INDEPENDENT_QA.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("source_backup",type=pathlib.Path);p.add_argument("delivery",type=pathlib.Path)
    a=p.parse_args();main(a.source_backup,a.delivery)
