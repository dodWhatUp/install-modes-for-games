"""Private, ordered manager handoffs made from already accepted original archives.

An export is NOT an installation. Do not deploy files, alter manager state or
redistribute these local third-party archives through Git/Drive automatically.
"""
from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path
from .safety import require, no_links, contained, json_new, copy_new, digest, local_lock, object_hash


def export_handoff(job,destination,*,reviewed_revision,confirmed=False):
    require(confirmed,'REVIEW_REQUIRED','Confirm a private manager handoff; it does not install anything.')
    revision=lambda:object_hash({'plan':job.plan,'events':job.events()})
    require(revision()==reviewed_revision,'CONCURRENT_CHANGE','Job changed since review.')
    dest=no_links(Path(destination))
    require(not dest.exists(),'EXISTS','Use a new export folder; existing files are never replaced.')
    require(dest!=job.path and job.path not in dest.parents and dest not in job.path.parents,
            'EXPORT_TARGET','Choose an export folder outside the job directory.')
    with local_lock(job.path):
        require(revision()==reviewed_revision,'CONCURRENT_CHANGE','Job changed before export.')
        entries=[]
        for n,(ident,item) in enumerate(job.items.items(),1):
            job.reconcile_gate(ident);source,receipt=job.acquired(ident)
            entries.append({'order':n,'item_id':ident,'name':item['name'],'kind':item['kind'],
                            'archive':f'{n:02d}_{ident}.zip','sha256':receipt['sha256'],
                            'bytes':source.stat().st_size,'source_private':source,
                            'requires':item.get('requires',[])})
        require(sum(e['bytes'] for e in entries)<=512*1024*1024,'EXPORT_LIMIT','Export exceeds the 512 MiB local-copy budget.')
        dest.mkdir(parents=True,exist_ok=False)
        for e in entries:copy_new(e['source_private'],contained(dest,e['archive']),e['sha256'])
        manifest={'schema_version':1,'kind':'private_manager_handoff','game_id':job.plan['game_id'],
                  'manager_id':job.plan['manager_id'],'job_id':job.path.name,'job_revision':reviewed_revision,
                  'plan_sha256':job.plan['plan_sha256'],'installed':False,'runtime_verified':False,
                  'items':[{k:v for k,v in e.items() if k!='source_private'} for e in entries]}
        json_new(dest/'MANAGER-HANDOFF.json',manifest)
        manager=job.plan['manager_id']
        route={'unity-mod-manager':'Use Unity Mod Manager’s Mods tab to import each original mod ZIP. Install the loader using its official installer first.',
               'smapi':'Use the official SMAPI installer for the loader. Unzip reviewed mod archives into individual Mods subfolders as documented by their authors.',
               'bepinex':'Use the correct BepInEx build for the game and runtime. Follow each plugin’s author instructions; this export does not decide where an arbitrary DLL belongs.',
               'mod-organizer-2':'Import original archives into the chosen Mod Organizer 2 instance/profile. Let MO2 manage virtual paths, FOMOD choices and priority.',
               'vortex':'Use Vortex’s archive import and deployment for the exact game. Let Vortex own its staging/deployment database.',
               'rhi':'Use the existing RHI profile for graphics hooks and libraries; do not independently copy proxy DLLs from this handoff.'}.get(manager,
                  'Follow the selected manager and mod author instructions. No arbitrary game-folder copy is authorized by this export.')
        from html import escape
        rows=''.join(f"<tr><td>{e['order']}</td><td>{escape(e['name'])}</td><td><a href='{e['archive']}'>{e['archive']}</a></td><td>{escape(e['kind'])}</td></tr>" for e in entries)
        page=("<!doctype html><html lang='en'><meta charset='utf-8'><title>Game Tools · Manager handoff</title>"
              "<style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px}td,th{padding:10px;text-align:left;border-bottom:1px solid #bbb}table{width:100%}</style>"
              f"<h1>{escape(job.plan['game_id'])}</h1><p><strong>Ready for manual manager import — not installed.</strong></p><p>{escape(route)}</p>"
              f"<table><tr><th>Order</th><th>Item</th><th>Original file</th><th>Role</th></tr>{rows}</table>"
              "<details><summary>Checks and limits</summary><p>Original archives were hash-checked. This does not establish safety, compatible game builds, or runtime success. "
              "Back up valued saves/settings and close the game before changes. Do not publish this private handoff as a redistributed mod bundle.</p></details></html>")
        (dest/'OPEN Manager Handoff.html').write_text(page,encoding='utf-8')
        require(revision()==reviewed_revision,'CONCURRENT_CHANGE','Job changed during export; inspect existing output before using it.')
        for e in entries:require(digest(dest/e['archive'])==e['sha256'],'SOURCE_CHANGED','Export readback failed.')
        json_new(dest/'VERIFIED.json',{'manifest_sha256':digest(dest/'MANAGER-HANDOFF.json'),
                                     'status':'HANDOFF_EXPORTED_NOT_INSTALLED'})
        return {'status':'HANDOFF_EXPORTED_NOT_INSTALLED','game_id':job.plan['game_id'],
                'files':len(entries),'bytes':sum(e['bytes'] for e in entries),'runtime':'NOT_VERIFIED'}
