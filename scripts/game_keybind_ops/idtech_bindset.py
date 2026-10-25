"""Reviewed DOOM configVersion 19 binding subset; lossless key spans only.

No cvar/command evaluation, insertion, includes, or file access. Contexts and
intentional multi-command keys retain their identities across simultaneous swaps.
"""
import re
from .deps import require
from .documents import Cell


def parse(document):
    header=False; current=None; sections=set(); resets=set(); counts={}; offset=0
    for line in document.text.splitlines(keepends=True):
        body=line.rstrip('\r\n'); text=body.strip()
        if not text or text.startswith('//'):pass
        elif re.fullmatch(r'configVersion\s+\d+',text):
            require(not header and current is None,'FORMAT_UNSUPPORTED','One configVersion header must precede binding sets.')
            match=re.fullmatch(r'\s*configVersion\s+(\d+)\s*',body)
            require(match[1]=='19','FORMAT_UNSUPPORTED','Only reviewed DOOM configVersion 19 is supported.')
            document.add(Cell({'header':'configVersion'},19,offset+match.start(1),offset+match.end(1),'json'))
            header=True
        elif re.fullmatch(r'bindset\s+\d+',text):
            require(header,'FORMAT_UNSUPPORTED','Missing configVersion before bindset.')
            current=int(text.split()[1])
            require(0<=current<=31 and current not in sections,'FORMAT_UNSUPPORTED','Duplicate or unsupported binding set.')
            sections.add(current)
        elif text=='unbindall':
            require(current is not None and current not in resets,'FORMAT_UNSUPPORTED','Each binding set needs one initial unbindall.')
            resets.add(current)
        else:
            match=re.fullmatch(r'\s*(bindMulti|bindSecondary)\s+"([^"\r\n]+)"\s+"([^"\r\n]+)"\s*(?://[^\r\n]*)?',body)
            if match:
                require(current in resets,'FORMAT_UNSUPPORTED','Bindings require a preceding unbindall in their set.')
                kind,key,command=match.groups();identity=(current,kind,command)
                occurrence=counts.get(identity,0);counts[identity]=occurrence+1
                document.add(Cell({'bindset':current,'kind':kind,'command':command,'occurrence':occurrence},
                                  key,offset+match.start(2),offset+match.end(2),'token',f'bindset:{current}'))
            else:
                # Keep literal cvars byte-for-byte. Execution/alias/binding
                # directives outside the reviewed grammar are not passthrough.
                cvar=re.fullmatch(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s+"[^"\r\n]*"\s*(?://[^\r\n]*)?',body)
                require(cvar is not None and not re.match(r'(?i)^(?:bind|unbind|exec|alias|set)',cvar[1]),
                        'FORMAT_UNSUPPORTED','Unrecognized idTech statement; review the schema before editing.')
        offset+=len(line)
    require(header and sections and sections==resets,'FORMAT_UNSUPPORTED','Incomplete binding-set reset/header inventory.')


def duplicate_pairs(document):
    """Sharing-pair identity permits moving an intentional command bundle.

    A key-count comparison would wrongly reject moving Shield+Spear together
    to a formerly unused key. Newly merged command pairs remain refused,
    including fields omitted from the caller's reviewed patch.
    """
    from .deps import object_hash
    groups={}
    for cell in document.cells:
        if cell.writer=='token':groups.setdefault((cell.group,cell.value.casefold()),[]).append(object_hash(cell.selector))
    return {tuple(sorted((a,b))) for ids in groups.values() for i,a in enumerate(ids) for b in ids[i+1:]}
