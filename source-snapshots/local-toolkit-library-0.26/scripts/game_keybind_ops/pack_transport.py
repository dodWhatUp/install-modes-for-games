"""Portable data-pack ZIP roundtrip. No archive auto-extraction or executable payloads."""
from __future__ import annotations
import json,os,stat,zipfile,tempfile
from pathlib import Path
from .deps import require,no_links,contained,object_hash
from .core import sha,snapshot
from .packs import payloads,inspect_pack,portable_path,MAX_PACK_FILES,MAX_PACK_BYTES


def export_pack_local(folder:Path,destination:Path)->dict:
    report=inspect_pack(folder);blobs=payloads(folder);destination=no_links(destination)
    require(object_hash([{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in sorted(blobs.items())])==report['pack_sha256'],'PACK_CHANGED','Pack changed during export.')
    require('PACK-MANIFEST.json' not in blobs,'PACK_MANIFEST','The transport manifest name is reserved.')
    require(not destination.exists(),'DEST_EXISTS','Do not overwrite an existing exported pack.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    manifest={'schema_version':1,'kind':'keybind-data-pack','pack_sha256':report['pack_sha256'],'files':report['files']}
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(blobs.items()):z.writestr(name,data)
        z.writestr('PACK-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    return {'status':'DATA_PACK_EXPORTED','pack_sha256':report['pack_sha256'],'archive_sha256':sha(destination.read_bytes()),'game_targets_read':False,'fixture_payloads_included':True}


def inspect_archive(archive:Path)->tuple[dict,dict[str,bytes]]:
    raw=snapshot(archive);require(len(raw)<=MAX_PACK_BYTES+128*1024,'PACK_BUDGET','Archive exceeds budget.')
    import io
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            members=z.infolist();require(0<len(members)<=MAX_PACK_FILES+1,'PACK_BUDGET','Too many archive entries.')
            seen=set();total=0;blobs={}
            for info in members:
                name=portable_path(info.filename)
                require(name.casefold() not in seen,'PACK_DUPLICATE','Duplicate or case-aliased archive entry.');seen.add(name.casefold())
                mode=info.external_attr>>16
                require(not info.is_dir() and stat.S_IFMT(mode) in (0,stat.S_IFREG) and not info.flag_bits&1,'PACK_UNSAFE','Directories, links and encryption are not accepted.')
                require(info.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),'PACK_UNSAFE','Unsupported compression.')
                total+=info.file_size;require(info.file_size<=MAX_PACK_BYTES and total<=MAX_PACK_BYTES+65536,'PACK_BUDGET','Expanded archive exceeds budget.')
                require(info.file_size/max(1,info.compress_size)<=250,'PACK_BUDGET','Excessive compression ratio.')
                with z.open(info) as stream:data=stream.read(info.file_size+1)
                require(len(data)==info.file_size,'PACK_CORRUPT','ZIP entry size differs.');blobs[name]=data
    except zipfile.BadZipFile as e:
        from .deps import Error
        raise Error('PACK_CORRUPT','ZIP CRC/format failed; no repair or retry.') from e
    require('PACK-MANIFEST.json' in blobs and 'pack.json' in blobs,'PACK_MANIFEST','A complete manifest and pack.json are required.')
    from .deps import strict_json
    m=strict_json(blobs.pop('PACK-MANIFEST.json'))
    require(type(m) is dict and set(m)=={'schema_version','kind','pack_sha256','files'} and m['schema_version']==1 and m['kind']=='keybind-data-pack','PACK_MANIFEST','Invalid data-pack manifest.')
    actual=[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in sorted(blobs.items())]
    require(m['files']==actual and m['pack_sha256']==object_hash(actual),'PACK_CORRUPT','Manifest does not cover exact archive contents.')
    return m,blobs


def unpack_pack_local(archive:Path,destination:Path,expected_sha256:str)->dict:
    """Copy verified pack data to a NEW local folder; no import or game activation."""
    m,blobs=inspect_archive(archive);require(m['pack_sha256']==expected_sha256,'PACK_CHANGED','Review this exact pack hash.')
    destination=no_links(destination);require(not destination.exists(),'DEST_EXISTS','Do not overwrite an authoring folder.')
    destination.mkdir(parents=True,exist_ok=False)
    for path,data in blobs.items():
        out=contained(destination,path);out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('xb') as s:s.write(data);s.flush();os.fsync(s.fileno())
    report=inspect_pack(destination)
    return {**report,'status':'UNPACKED_DATA_NOT_IMPORTED','activated':False}
