"""Lossless, existing-scalar-only edits. Never synthesize a whole game config.

Selectors and key vocabularies are local reviewed recipe data, not guessed action
IDs. Duplicate/ambiguous entries fail closed. Unknown binary/encoded formats do
not pass through this module. JSON whitespace, INI comments, XML order, BOM and
newlines outside changed scalar spans are retained exactly.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import re
from typing import Any
import xml.parsers.expat as expat
from .deps import require, Error, strict_json

MAX_BYTES = 8 * 1024 * 1024
MAX_LEAVES = 50000

@dataclass(frozen=True)
class Cell:
    selector: dict
    value: Any
    start: int
    end: int
    writer: str
    group: str = ''
    quote: str = '"'
    parts: tuple = ()

class Document:
    def __init__(self, raw: bytes, adapter: str, encoding: str | None = None):
        require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'SIZE_LIMIT', 'Config must be nonempty and at most 8 MiB.')
        self.raw, self.adapter = raw, adapter
        if raw.startswith(b'\xff\xfe'):
            self.bom, self.encoding = b'\xff\xfe', 'utf-16-le'
        elif raw.startswith(b'\xfe\xff'):
            self.bom, self.encoding = b'\xfe\xff', 'utf-16-be'
        elif raw.startswith(b'\xef\xbb\xbf'):
            self.bom, self.encoding = b'\xef\xbb\xbf', 'utf-8'
        else:
            self.bom, self.encoding = b'', encoding or 'utf-8'
        require(self.encoding in {'utf-8','utf-16-le','utf-16-be','cp1252'}, 'ENCODING_UNSUPPORTED', 'Encoding must be explicitly supported; no guessing.')
        try: self.text = raw[len(self.bom):].decode(self.encoding)
        except UnicodeError as e: raise Error('ENCODING_UNSUPPORTED', 'Config is not valid in the selected encoding.') from e
        require('\x00' not in self.text, 'BINARY_UNSUPPORTED', 'NUL-containing data needs a dedicated reviewed adapter.')
        self.cells: list[Cell] = []
        try:
            if adapter == 'json': self._json()
            elif adapter == 'jsonc':
                from .format_extensions import jsonc_text
                self._json(jsonc_text(self.text))
            elif adapter in {'ini','ue-ini','ini-sparse'}: self._ini()
            elif adapter in {'keyvalues','colon-lines','ue-chord'}:
                from .format_extensions import parse_extra
                parse_extra(self)
            elif adapter == 'xml': self._xml()
            elif adapter == 'cfg-bind': self._cfg()
            else:
                from .adapter_registry import adapter_info
                a=adapter_info(adapter)
                require(callable(a.parser),'ADAPTER_UNSUPPORTED','Adapter implementation unavailable.')
                a.parser(self)
        except (ValueError, RecursionError, expat.ExpatError) as e:
            raise Error('FORMAT_INVALID', 'Config could not be parsed within the supported subset.') from e
        require(len(self.cells) <= MAX_LEAVES, 'SIZE_LIMIT', 'Too many scalar entries.')
        require(self.bom + self.text.encode(self.encoding) == raw, 'ROUNDTRIP_FAILED', 'Input encoding did not round-trip.')

    def add(self, cell: Cell):
        require(len(self.cells) < MAX_LEAVES, 'SIZE_LIMIT', 'Too many scalar entries.')
        self.cells.append(cell)

    def _json(self, parsed_text=None):
        source = self.text if parsed_text is None else parsed_text
        strict_json(source)  # rejects duplicate names and nonfinite values
        t, dec = source, json.JSONDecoder()
        def ws(i):
            while i < len(t) and t[i] in ' \r\n\t': i += 1
            return i
        def value(i, path, depth=0):
            require(depth <= 64, 'SIZE_LIMIT', 'JSON nesting exceeds 64.')
            i = ws(i)
            if t[i] == '{':
                i = ws(i+1)
                if t[i] == '}': return i+1
                while True:
                    key, end = dec.raw_decode(t, i)
                    require(isinstance(key,str), 'FORMAT_INVALID', 'Invalid object key.')
                    i = ws(end)
                    require(t[i] == ':', 'FORMAT_INVALID', 'Missing JSON colon.')
                    pointer = path + '/' + key.replace('~','~0').replace('/','~1')
                    i = ws(value(i+1, pointer, depth+1))
                    if t[i] == '}': return i+1
                    require(t[i] == ',', 'FORMAT_INVALID', 'Missing JSON comma.')
                    i = ws(i+1)
            elif t[i] == '[':
                i, n = ws(i+1), 0
                if t[i] == ']': return i+1
                while True:
                    i = ws(value(i, path+'/'+str(n), depth+1)); n += 1
                    if t[i] == ']': return i+1
                    require(t[i] == ',', 'FORMAT_INVALID', 'Missing JSON comma.')
                    i = ws(i+1)
            else:
                v, end = dec.raw_decode(t, i)
                self.add(Cell({'pointer':path},v,i,end,'json'))
                return end
        require(ws(value(0,'')) == len(t), 'FORMAT_INVALID', 'Trailing JSON data.')

    def _ini(self):
        section, offset, counts, commands = '', 0, {}, {}
        for line in self.text.splitlines(keepends=True):
            body = line.rstrip('\r\n')
            sm = re.fullmatch(r'\s*\[([^\]\r\n]+)\]\s*(?:[;#].*)?',body)
            if sm: section = sm.group(1)
            elif body.strip() and not body.lstrip().startswith((';','#')):
                m = re.fullmatch(r'(\s*)([^=\r\n]+?)(\s*)=(\s*)(.*)',body)
                require(m is not None, 'FORMAT_UNSUPPORTED', 'Multiline/bare INI entries need a dedicated adapter.')
                key = m.group(2); val = m.group(5)
                if self.adapter=='ue-ini' and key.startswith(('-', '!')) and key[1:] in {'ActionMappings','AxisMappings'}:
                    raise Error('EFFECTIVE_OWNER_REQUIRED','Unreal removal/clear directives require an explicit native array resolver.')
                trimmed = val.rstrip(); trailing = len(val)-len(trimmed)
                # Retain clearly delimited inline comments for plain scalar values.
                cm = re.search(r'\s+[;#]', trimmed)
                if cm and not trimmed.startswith(('"',"'",'(')): trimmed = trimmed[:cm.start()].rstrip()
                count_key = (section,key); occurrence = counts.get(count_key,0); counts[count_key] = occurrence+1
                if self.adapter in {'ini','ini-sparse'}:
                    base = {'section':section,'key':key,'occurrence':occurrence}
                    self.add(Cell({**base,'part':'value'},trimmed,offset+m.start(5),offset+m.start(5)+len(trimmed),'plain',section))
                    command_key=(section,trimmed); cn=commands.get(command_key,0); commands[command_key]=cn+1
                    self.add(Cell({'section':section,'command':trimmed,'occurrence':cn,'part':'key'},key,offset+m.start(2),offset+m.end(2),'ini-key',section))
                else:
                    if key.lstrip('+-!.') in {'ActionMappings','AxisMappings'}:
                        action = re.search(r'\b(?:ActionName|AxisName)\s*=\s*"([^"\r\n]+)"',trimmed)
                        km = re.findall(r'\bKey\s*=\s*([^,()\s]+)',trimmed)
                        if action and len(km)==1:
                            mt = re.search(r'\bKey\s*=\s*([^,()\s]+)',trimmed)
                            name = action.group(1)
                            matches = sum(c.selector.get('action')==name and c.selector.get('section')==section for c in self.cells)
                            # Modifiers remain literal native qualifiers; they are never silently removed.
                            mods = tuple(re.findall(r'\bb(?:Shift|Ctrl|Alt|Cmd)\s*=\s*[^,)]+',trimmed))
                            self.add(Cell({'section':section,'action':name,'occurrence':matches},mt.group(1),
                                          offset+m.start(5)+mt.start(1),offset+m.start(5)+mt.end(1),'token',section+'|'+','.join(mods)))
            offset += len(line)

    def _xml(self):
        require(not re.search(r'<!\s*(?:DOCTYPE|ENTITY)',self.text,re.I), 'XML_ENTITY_BLOCKED', 'DTD/entity declarations are not accepted.')
        # Parse the decoded Unicode string; expat then uses UTF-8 byte offsets
        # even when the retained original declaration says UTF-16.
        raw = self.text.encode('utf-8'); p = expat.ParserCreate()
        stack, counts = [], [{}]
        def start(name, attrs):
            index = counts[-1].get(name,0); counts[-1][name] = index+1
            path = '/'.join(stack+[f'{name}[{index}]'])
            i = len(raw[:p.CurrentByteIndex].decode('utf-8'))
            j, quote = i, None
            while j < len(self.text):
                c = self.text[j]
                if quote:
                    if c == quote: quote = None
                elif c in "\"'": quote = c
                elif c == '>': break
                j += 1
            tag = self.text[i:j+1]
            for m in re.finditer(r'([A-Za-z_:][\w:.-]*)\s*=\s*([\"\'])(.*?)\2',tag,re.S):
                attr = m.group(1)
                require(attr in attrs, 'FORMAT_INVALID', 'XML attribute mismatch.')
                self.add(Cell({'element':path,'attribute':attr},attrs[attr],i+m.start(3),i+m.end(3),'xml',path,m.group(2)))
            stack.append(f'{name}[{index}]');counts.append({})
        def end(name): stack.pop(); counts.pop()
        p.StartElementHandler, p.EndElementHandler = start, end
        p.ExternalEntityRefHandler = lambda *_: 0
        p.Parse(self.text, True)

    def _cfg(self):
        counts, offset = {}, 0
        for line in self.text.splitlines(keepends=True):
            m = re.fullmatch(r'\s*bind\s+"([^"\r\n]+)"\s+"([^"\r\n]+)"\s*(?://[^\r\n]*)?[\r\n]*',line)
            if m:
                command = m.group(2); n = counts.get(command,0);counts[command] = n+1
                self.add(Cell({'command':command,'occurrence':n},m.group(1),offset+m.start(1),offset+m.end(1),'token','bind'))
            elif line.lstrip().startswith('bind '):
                raise Error('FORMAT_UNSUPPORTED','Unrecognized bind syntax; no generic command rewriting.')
            offset += len(line)

    def select(self, selector: dict) -> Cell:
        require(type(selector) is dict, 'INVALID_SELECTOR','Selector must be an object.')
        from .format_extensions import resolve_selector
        selector, special = resolve_selector(self, selector)
        if special is not None:return special
        found = [c for c in self.cells if c.selector == selector]
        require(len(found)==1,'SELECTOR_AMBIGUOUS','Selector must identify exactly one existing scalar, including occurrence where required.')
        return found[0]

    def render(self, changes: list[tuple[dict,Any]]) -> bytes:
        spans = []
        for selector, new in changes:
            c = self.select(selector)
            if c.writer in {'sparse','ue-chord','kv','colon','extension'}:
                from .format_extensions import render_extra
                spans.extend(render_extra(self,c,new))
                continue
            if c.writer == 'json':
                require(type(new) in (str,int,float,bool) or new is None,'INVALID_VALUE','Only JSON scalar replacements are supported.')
                v = json.dumps(new,ensure_ascii=False,allow_nan=False)
            else:
                require(type(new) is str and len(new)<=256 and not any(ord(x)<32 for x in new),'INVALID_VALUE','Expected a short single-line native key token.')
                if c.writer == 'xml':
                    v = new.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                    v = v.replace(c.quote,'&quot;' if c.quote=='"' else '&apos;')
                else:
                    require(not any(x in new for x in '"\'\\;#=,()[]'),'INVALID_VALUE','Unsafe native token; use a native key name/code.')
                    require(new and new.strip()==new and not any(x.isspace() for x in new),'INVALID_VALUE','Expected one native key token.')
                    v = new
            spans.append((c.start,c.end,v))
        # Multiple sparse entries can share one insertion point; merge deterministically.
        merged=[]
        for start,end,text in sorted(spans,key=lambda x:(x[0],x[1])):
            require(type(start) is int and type(end) is int and 0<=start<=end<=len(self.text) and type(text) is str,
                    'INVALID_SPAN','Adapter returned an invalid edit span.')
            if merged and start==end==merged[-1][0]==merged[-1][1]:
                merged[-1]=(start,end,merged[-1][2]+text)
            else:merged.append((start,end,text))
        spans=merged
        spans.sort()
        require(all(spans[n][1] <= spans[n+1][0] for n in range(len(spans)-1)),'OVERLAPPING_PATCH','A scalar was selected more than once.')
        t = self.text
        for start,end,v in reversed(spans): t = t[:start]+v+t[end:]
        try: result = self.bom+t.encode(self.encoding)
        except UnicodeError as e: raise Error('ENCODING_UNSUPPORTED','Requested key is not representable in this file encoding.') from e
        Document(result,self.adapter,self.encoding)
        return result
