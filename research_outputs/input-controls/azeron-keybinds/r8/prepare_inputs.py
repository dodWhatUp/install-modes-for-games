#!/usr/bin/env python3
"""Extract exact bounded roles from the existing verified private R7 recovery.
No native app, source execution, network or profile mutation. New directory only.
"""
import argparse,hashlib,io,stat,zipfile
from pathlib import Path,PurePosixPath
R7='91d9c4d0fee4c2ebed54e38f4dbe8d0a8889d49b73824756150159d06ae65a6f'
R6='8d1977ee2aa0e4dccf8e9ed0636bfb91e36dd52dc1fcb4f8a813801b3bdc9205'
def digest(b):return hashlib.sha256(b).hexdigest()
def get(z,name):
 p=PurePosixPath(name);i=z.getinfo(name)
 if p.is_absolute() or '..' in p.parts or stat.S_ISLNK(i.external_attr>>16) or i.file_size>25_000_000:raise ValueError('Unsafe or oversize archive member')
 return z.read(i)
def prepare(archive,out):
 if out.exists():raise FileExistsError('Use a new private input directory')
 raw=archive.read_bytes()
 if digest(raw)!=R7:raise ValueError('R7 input hash mismatch')
 files={}
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate source archive entries')
  for f in ['REVIEWED_ACTIONS_R7.json','SEMANTIC_AND_DEMAND_REVIEW_R7.json','SOURCES_R7.json']:
   files['r7/'+f]=get(z,'R7/'+f)
  r6=get(z,'prior/Azeron_R6_Complete_Package.zip')
 if digest(r6)!=R6:raise ValueError('R6 nested source hash mismatch')
 with zipfile.ZipFile(io.BytesIO(r6)) as z:
  for name in ['research/DESIGN_R6.json','research/audit_r6_access.py','inputs/r4/CORPUS_AUDIT_R4.json','inputs/r5/SOURCE_original_backup.zip']:
   files['r6/'+name]=get(z,name)
  for name in z.namelist():
   if (name.startswith('inputs/r5/profiles/') or name.startswith('native/')) and name.endswith('.json'):files['r6/'+name]=get(z,name)
 out.mkdir(parents=True,exist_ok=False)
 for name,b in files.items():
  p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 print('Verified input roles extracted:',len(files));return files
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--r7-archive',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();prepare(x.r7_archive,x.out)
