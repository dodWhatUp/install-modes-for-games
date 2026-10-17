"""One explicit installation from a trusted, verified local source ZIP.

No runtime download/start, settings migration, native profile import or game work.
"""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from GameToolUnified import (STUDIO, apply_release, digest, inspect_archive, local_path, read_bytes, studio_hashes)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("install-root","archive","studio-dir","studio-settings","data-dir","pythonw","ahk","expected-studio-json"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--expected-sha256",required=True)
    a=p.parse_args(argv)
    release=inspect_archive(a.archive,a.expected_sha256)
    expected=json.loads(read_bytes(a.expected_studio_json).decode("utf-8-sig"))
    if set(expected)!=set(STUDIO): raise ValueError("Expected exact six-file pre-mutation map")
    initial={"schema_version":1,**{key:str(local_path(getattr(a,key))) for key in
        ("studio_dir","studio_settings","data_dir","pythonw","ahk")}}
    for key in ("pythonw","ahk"):
        if not Path(initial[key]).is_file(): raise ValueError("Missing configured runtime: "+key)
    value=apply_release(a.install_root,release,expected_state_sha256=None,expected_studio=expected,initial=initial)
    launcher=a.install_root/"Start-UnifiedTools.pyw"
    raw=release["payloads"]["scripts/Start-UnifiedTools.pyw"]
    if read_bytes(launcher)!=raw: raise ValueError("Stable launcher readback differs")
    print(json.dumps({"installed":str(a.install_root),"versions":value["component_versions"],
        "studio_source_verified":studio_hashes(a.studio_dir)==value["studio_hashes"],
        "launcher_sha256":digest(raw),"activation":"none; launch separately", "recovery":value["recovery"]},indent=2))
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError) as e:
        print(json.dumps({"valid":False,"error":str(e)})); raise SystemExit(2)
