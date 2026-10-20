"""Explicit real-volume synthetic acceptance; creates only new owned folders."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

SCRIPTS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(SCRIPTS))
from GameToolAIContracts import stable_revision
from game_system_control.contracts import require
from game_system_control.vault import VaultRegistry,volume_identity
from game_system_control.policy import PolicyStore
from game_system_control.access import AccessStore
from game_system_control.workspace_state import private_root


def run(data_parent,local_parent):
    data_parent=private_root(data_parent);local_parent=private_root(local_parent)
    require(data_parent.is_dir() and local_parent.is_dir(),"Select existing private parent directories.")
    observed=volume_identity(data_parent)
    require(not observed["system_volume"],"Synthetic data acceptance requires a real non-system volume.")
    tag="managed-workspace-"+uuid.uuid4().hex
    data=data_parent/tag;local=local_parent/tag
    data.mkdir();local.mkdir()
    registry=VaultRegistry.create(local/"bindings");registry.enroll(data/"vault","fixture-workspace",registry.state.snapshot()["revision"])
    vault_id=registry.state.snapshot()["body"]["vaults"][0]["marker"]["vault_id"]
    policy=PolicyStore.create(local/"policy")
    rule={"id":"fixture-placement","scope":{"account_id":"fixture-account","workspace_id":"fixture-workspace","project_id":"fixture-project",
          "source_device":"fixture-device","destination_device":"fixture-device","capability":"managed.write","content_class":"*"},"origin":"destination","enabled":True,
          "controls":{"transfer":False,"adoption":True,"index":False,"context":False},"context_depth":"none","trigger":{"kind":"manual"}}
    proposal=policy.propose_rule(rule);policy.accept(proposal,proposal["preview_sha256"])
    access=AccessStore.create(local/"access","fixture-account","fixture-device","fixture-project",workspace_id="fixture-workspace",now=time.time())
    actor={"account_id":"fixture-account","workspace_id":"fixture-workspace","project_id":"fixture-project","device_id":"fixture-device","generation":1,"capability":"enrollment.manage"}
    def change(action,values):
        proposal=access.propose_change(actor,action,values,now=time.time())
        return access.accept(actor,proposal,proposal["preview_sha256"],now=time.time())
    change("membership",{"account_id":"fixture-account","project_id":"fixture-project","roles":["policy_administrator","contributor"]})
    classes=["project_source","selected_assets","selected_results","continuation_packet"]
    change("storage",{"account_id":"fixture-account","project_id":"fixture-project","storage_id":vault_id,"read":classes,"write":classes})
    revision=stable_revision(policy.snapshot()["body"])
    change("pin_policy",{"policy_revision":revision});change("acknowledge",{"device_id":"fixture-device","policy_revision":revision})
    results=[]
    def place(cls,name,payload,expected_exit=0):
        source=local/("source-"+name);source.write_bytes(payload)
        request={"authorization":{**actor,"capability":"managed.write","storage_id":vault_id,"content_class":cls,"policy_revision":revision},
                 "policy":{**rule["scope"],"content_class":cls}}
        request_path=local/("request-"+name+".json");request_path.write_text(json.dumps(request),encoding="utf-8")
        command=[sys.executable,"-B","-X","utf8",str(SCRIPTS/"GameToolManagedWorkspace.py"),"place","--state",str(local/"bindings"),"--vault-id",vault_id,
                 "--project","fixture-project","--class",cls,"--relative",name,"--source",str(source),"--source-sha256",hashlib.sha256(payload).hexdigest(),
                 "--policy-state",str(local/"policy"),"--access-state",str(local/"access"),"--input",str(request_path)]
        result=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",timeout=30)
        require(result.returncode==expected_exit,"Synthetic CLI placement outcome differed: "+result.stderr[:500])
        require(source.read_bytes()==payload,"Synthetic source was changed.")
        target=VaultRegistry(local/"bindings").route(vault_id,"fixture-project",cls,name)
        require((target.read_bytes()==payload) if expected_exit==0 else not target.exists(),"Synthetic managed output placement mismatch.")
        return {"class":cls,"relative":name,"sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload),"exit_code":result.returncode}
    for cls,name,payload in [("project_source","README.md",b"# Synthetic source\n"),("selected_assets","sample.bin",b"\x00\xffselected bytes"),
                             ("selected_results","result.txt","Synthetic result שלום\n".encode()),("continuation_packet","handoff.json",b'{"kind":"synthetic_continuation","native_chat":false}')]:
        results.append(place(cls,name,payload))
    stopped=access.stop_local();place("selected_results","stopped.txt",b"must not appear",2)
    access.resume_local(actor,stopped["stop_sha256"],now=time.time())
    old=data/"vault";moved=data/"vault-relocated";old.rename(moved)
    registry.rebind(vault_id,moved,registry.state.snapshot()["revision"])
    require(VaultRegistry(local/"bindings").inspect(vault_id)["available"],"Relocated vault did not reopen.")
    marker_before=(moved/"vault.json").read_bytes()
    attached=VaultRegistry.create(local/"fresh-destination-bindings")
    attached.attach(moved,attached.state.snapshot()["revision"])
    require(attached.inspect(vault_id)["available"] and (moved/"vault.json").read_bytes()==marker_before,"Fresh local attachment changed the portable vault marker.")
    clone=data/"clone";shutil.copytree(moved,clone)
    require(registry.selected_collisions([moved,clone])["state"]=="blocked","Selected clone collision was missed.")
    change("revoke",{"device_id":"fixture-device"});place("selected_results","revoked.txt",b"must not appear",2)
    access.stop_local()
    receipt={"state":"SYNTHETIC_NATIVE_VOLUME_ACCEPTANCE_PASS","data_root":str(data),"local_root":str(local),"observed_volume":observed,
             "outputs":results,"exact_placement_and_reopen":True,"relocated_same_volume_rebind":True,"clone_collision_blocked":True,
             "fresh_local_binding_attach_without_rewriting_vault":True,"second_physical_computer_tested":False,
             "local_stop_and_revocation_blocked_placement":True,"access_left_stopped":True,"native_settings_changed":False,
             "codex_changed":False,"provider_account_authentication":"not_connected","network_or_model_calls":0}
    (local/"ACCEPTANCE.private.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    return receipt


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--data-parent",type=Path,required=True);parser.add_argument("--local-parent",type=Path,required=True)
    args=parser.parse_args();print(json.dumps(run(args.data_parent,args.local_parent),indent=2))
