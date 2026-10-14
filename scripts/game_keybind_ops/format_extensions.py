"""Bounded text dialects, stable selectors and explicit sparse scalar overrides.
No shell, file includes, eval, binary guessing, or whole-config serialization.
"""
from __future__ import annotations
from dataclasses import replace
import json,re
from .deps import Error,require,strict_json

INHERIT='__GT_INHERIT__'

def jsonc_text(text: str) -> str:
    out=list(text);i=0;quoted=False;esc=False
    while i<len(text):
        c=text[i]
        if quoted:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c=='"':quoted=False
            i+=1;continue
        if c=='"':quoted=True;i+=1;continue
        if text.startswith('//',i):
            j=text.find('\n',i);j=len(text) if j<0 else j
            for k in range(i,j):out[k]=' '
            i=j;continue
        if text.startswith('/*',i):
            j=text.find('*/',i+2);require(j>=0,'FORMAT_INVALID','Unclosed JSON comment.')
            for k in range(i,j+2):
                if out[k] not in '\r\n':out[k]=' '
            i=j+2;continue
        i+=1
    require(not quoted,'FORMAT_INVALID','Unclosed JSON string.')
    clean=''.join(out)
    # Remove trailing comma only outside a string; keep offsets exactly aligned.
    i=0;quoted=False;esc=False
    while i<len(clean):
        c=clean[i]
        if quoted:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c==',':
            j=i+1
            while j<len(clean) and clean[j].isspace():j+=1
            if j<len(clean) and clean[j] in ']}':out[i]=' '
        i+=1
    return ''.join(out)

def keyvalues_tokens(text):
    i=0;tokens=[]
    while i<len(text):
        if text[i].isspace():i+=1;continue
        if text.startswith('//',i):
            n=text.find('\n',i);i=len(text) if n<0 else n;continue
        if text[i] in '{}':tokens.append((text[i],i,i+1));i+=1;continue
        require(text[i]=='"','FORMAT_UNSUPPORTED','Only quoted KeyValues1; includes, conditions, macros and KV3 require their own owner.')
        start=i;i+=1;v=[]
        while i<len(text) and text[i]!='"':
            require(text[i] not in '\r\n','FORMAT_UNSUPPORTED','Multiline KeyValues token unsupported.')
            if text[i]=='\\':
                i+=1;require(i<len(text),'FORMAT_INVALID','Unclosed KeyValues escape.')
                require(text[i] in '\\"ntr','FORMAT_UNSUPPORTED','Unsupported KeyValues escape.')
                v.append({'n':'\n','t':'\t','r':'\r'}.get(text[i],text[i]))
            else:v.append(text[i])
            i+=1
        require(i<len(text),'FORMAT_INVALID','Unclosed KeyValues token.')
        tokens.append((''.join(v),start+1,i));i+=1
        require(len(tokens)<=100000,'SIZE_LIMIT','KeyValues token budget exceeded.')
    return tokens

def parse_extra(d):
    from .documents import Cell
    if d.adapter=='keyvalues':
        ts=keyvalues_tokens(d.text);i=0
        def obj(path,depth,closing=False):
            nonlocal i
            require(depth<=48,'SIZE_LIMIT','KeyValues nesting exceeds limit.')
            counts={}
            while i<len(ts):
                if ts[i][0]=='}' and d.text[ts[i][1]:ts[i][2]]=='}':
                    require(closing,'FORMAT_INVALID','Unexpected closing brace.');i+=1;return
                name=ts[i][0];require(d.text[ts[i][1]-1]=='"','FORMAT_INVALID','Expected quoted key.');i+=1
                n=counts.get(name,0);counts[name]=n+1;here=path+[[name,n]]
                require(i<len(ts),'FORMAT_INVALID','Missing KeyValues value.')
                v,a,b=ts[i];i+=1
                if v=='{' and d.text[a:b]=='{':obj(here,depth+1,True)
                else:
                    require(d.text[a-1]=='"','FORMAT_INVALID','Expected quoted scalar value.')
                    d.add(Cell({'kv_path':here},v,a,b,'kv',json.dumps(path)))
            require(not closing,'FORMAT_INVALID','Missing closing brace.')
        obj([],0);return
    if d.adapter=='colon-lines':
        off=0;counts={}
        for line in d.text.splitlines(keepends=True):
            body=line.rstrip('\r\n')
            if body.strip() and not body.lstrip().startswith('#'):
                m=re.fullmatch(r'(\s*)([^:\r\n]+?)(\s*):(\s*)(.*)',body)
                require(m is not None,'FORMAT_UNSUPPORTED','Only one key:value per line.')
                key=m.group(2);n=counts.get(key,0);counts[key]=n+1;val=m.group(5).rstrip()
                d.add(Cell({'key':key,'occurrence':n},val,off+m.start(5),off+m.start(5)+len(val),'colon'))
            off+=len(line)
        return
    # Unreal chord: edit only existing ActionMappings with all four flag tokens.
    sec='';off=0;counts={}
    for line in d.text.splitlines(keepends=True):
        body=line.rstrip('\r\n');sm=re.fullmatch(r'\s*\[([^\]]+)\]\s*(?:;.*)?',body)
        if sm:sec=sm.group(1)
        elif re.match(r'\s*[+.]?ActionMappings\s*=',body):
            am=re.search(r'\bActionName\s*=\s*"([^"\r\n]+)"',body)
            require(am is not None,'FORMAT_UNSUPPORTED','ActionName must be explicit.')
            parts=[];value={}
            for key,native in [('key','Key'),('shift','bShift'),('ctrl','bCtrl'),('alt','bAlt'),('cmd','bCmd')]:
                ms=list(re.finditer(r'\b'+native+r'\s*=\s*([^,()\s]+)',body))
                require(len(ms)==1,'FORMAT_UNSUPPORTED','Key and all four modifier flags must occur once.')
                m=ms[0];v=m.group(1)
                if key!='key':
                    require(v.lower() in {'true','false'},'FORMAT_UNSUPPORTED','Modifier flags must be boolean.');v=v.lower()=='true'
                value[key]=v;parts.append((key,off+m.start(1),off+m.end(1)))
            key=(sec,am.group(1));n=counts.get(key,0);counts[key]=n+1
            d.add(Cell({'section':sec,'action':am.group(1),'occurrence':n},value,off,off+len(body),'ue-chord',sec,parts=tuple(parts)))
        elif re.match(r'\s*[-!]ActionMappings',body):
            raise Error('EFFECTIVE_OWNER_REQUIRED','Unreal removal/clear directives require a native array resolver; no scalar override guessing.')
        off+=len(line)

def _pointer(obj,pointer):
    require(type(pointer) is str and (not pointer or pointer.startswith('/')),'INVALID_SELECTOR','Expected JSON pointer.')
    for raw in pointer.split('/')[1:]:
        require(not re.search(r'~(?![01])',raw),'INVALID_SELECTOR','Invalid pointer escape.')
        k=raw.replace('~1','/').replace('~0','~')
        if type(obj) is list:
            require(k.isdigit() and (k=='0' or not k.startswith('0')) and int(k)<len(obj),'SELECTOR_AMBIGUOUS','No array element.')
            obj=obj[int(k)]
        else:
            require(type(obj) is dict and k in obj,'SELECTOR_AMBIGUOUS','No object member.');obj=obj[k]
    return obj

def resolve_selector(d,s):
    from .documents import Cell
    require(len(json.dumps(s))<=4096,'INVALID_SELECTOR','Selector budget exceeded.')
    if 'json_match' in s:
        require(set(s)=={'json_match'} and d.adapter in {'json','jsonc'},'INVALID_SELECTOR','json_match only for JSON.')
        m=s['json_match'];require(type(m) is dict and set(m)=={'array','where','value'},'INVALID_SELECTOR','Expected array, where and value pointers.')
        require(type(m['where']) is dict and 0<len(m['where'])<=8,'INVALID_SELECTOR','Use bounded identity equalities.')
        data=strict_json(jsonc_text(d.text) if d.adapter=='jsonc' else d.text);rows=_pointer(data,m['array'])
        require(type(rows) is list and len(rows)<=10000,'INVALID_SELECTOR','Identity lookup requires a bounded array.')
        found=[]
        for i,row in enumerate(rows):
            try:ok=all(type(_pointer(row,k)) is type(v) and _pointer(row,k)==v for k,v in m['where'].items())
            except Error:ok=False
            if ok:found.append(i)
        require(len(found)==1,'SELECTOR_AMBIGUOUS','Identity must select exactly one row; never guess from position.')
        return {'pointer':m['array']+'/'+str(found[0])+m['value']},None
    if 'xml_match' in s:
        require(set(s)=={'xml_match'} and d.adapter=='xml','INVALID_SELECTOR','xml_match only for XML.')
        m=s['xml_match'];require(type(m) is dict and set(m)=={'tag','where','attribute'},'INVALID_SELECTOR','Expected tag, where and attribute.')
        require(type(m['where']) is dict and 0<len(m['where'])<=8,'INVALID_SELECTOR','Use explicit XML identity attributes.')
        grouped={}
        for c in d.cells:grouped.setdefault(c.selector['element'],{})[c.selector['attribute']]=c.value
        found=[p for p,a in grouped.items() if p.rsplit('/',1)[-1].split('[',1)[0]==m['tag'] and all(a.get(k)==v for k,v in m['where'].items())]
        require(len(found)==1,'SELECTOR_AMBIGUOUS','XML identity must be unique across the document.')
        return {'element':found[0],'attribute':m['attribute']},None
    if d.adapter=='ini-sparse' and s.get('optional') is True:
        base={k:v for k,v in s.items() if k!='optional'}
        require(set(base)=={'section','key','occurrence','part'} and base['occurrence']==0 and base['part']=='value',
                'INVALID_SELECTOR','Sparse fields require a single section/key value.')
        require(type(base['key']) is str and re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',base['key']),
                'INVALID_SELECTOR','Sparse keys use safe literal names.')
        found=[c for c in d.cells if c.selector==base]
        all_same=[c for c in d.cells if c.selector.get('section')==base['section'] and c.selector.get('key')==base['key']]
        require(len(all_same)<=1,'SELECTOR_AMBIGUOUS','Sparse duplicate overrides require native review.')
        if found:return s,replace(found[0],selector=s,writer='sparse')
        # Insert before next section; require one existing section (or root section).
        sec='';off=0;ends=[];active=base['section']==''
        for line in d.text.splitlines(keepends=True):
            match=re.fullmatch(r'\s*\[([^\]]+)\]\s*(?:[;#].*)?',line.rstrip('\r\n'))
            if match:
                if active:ends.append(off)
                sec=match.group(1);active=sec==base['section']
            off+=len(line)
        if active:ends.append(off)
        require(len(ends)==1,'SELECTOR_AMBIGUOUS','Sparse insertion needs exactly one existing section, not a new section.')
        return s,Cell(s,INHERIT,ends[0],ends[0],'sparse')
    return s,None

def render_extra(d,c,new):
    from .adapter_registry import adapter_info
    if c.writer=='extension':return adapter_info(d.adapter).renderer(d,c,new)
    if c.writer=='ue-chord':
        require(type(new) is dict and set(new)=={'key','shift','ctrl','alt','cmd'},'INVALID_VALUE','Use a complete native chord object.')
        require(type(new['key']) is str and re.fullmatch(r'[A-Za-z0-9_]+',new['key']),'INVALID_VALUE','Unsafe native key.')
        require(all(type(new[k]) is bool for k in ('shift','ctrl','alt','cmd')),'INVALID_VALUE','Modifier flags must be booleans.')
        return [(a,b,new[k] if k=='key' else ('True' if new[k] else 'False')) for k,a,b in c.parts if new[k]!=c.value[k]]
    require(type(new) is str and len(new)<=256 and not any(ord(x)<32 for x in new),'INVALID_VALUE','Expected a short single-line token.')
    if c.writer=='kv':return [(c.start,c.end,new.replace('\\','\\\\').replace('"','\\"'))]
    if c.writer=='colon':
        require(new and not any(x.isspace() for x in new) and not any(x in new for x in '#\\'),'INVALID_VALUE','Unsafe key code.')
        return [(c.start,c.end,new)]
    require(c.writer=='sparse','ADAPTER_UNSUPPORTED','Unknown writer.')
    if new==INHERIT:
        if c.value==INHERIT:return []
        a=d.text.rfind('\n',0,c.start)+1;b=d.text.find('\n',c.end);b=len(d.text) if b<0 else b+1
        body=d.text[a:b]
        require(not re.search(r'\s+[;#]',body),'SPARSE_REMOVE_COMMENT','Inline comments need manual/native removal review.')
        return [(a,b,'')]
    require(re.fullmatch(r'[A-Za-z0-9_.+/-]{1,128}',new),'INVALID_VALUE','Unsafe sparse native token.')
    if c.value!=INHERIT:return [(c.start,c.end,new)]
    nl='\r\n' if '\r\n' in d.text else '\n'
    prefix='' if c.start==0 or d.text[:c.start].endswith('\n') else nl
    return [(c.start,c.start,prefix+c.selector['key']+' = '+new+nl)]
