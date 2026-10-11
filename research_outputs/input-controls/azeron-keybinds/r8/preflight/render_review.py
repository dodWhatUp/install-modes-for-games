#!/usr/bin/env python3
"""Render a private read-only snapshot result. No scripts or external assets."""
import argparse,html,json
from pathlib import Path
from safe_io import read_regular,strict_json,ReviewError

def render(source,out):
 raw,_=read_regular(source);d=strict_json(raw)
 if d.get('schema')!='azeron-native-review/v1':raise ReviewError('Expected the native review receipt schema.')
 e=lambda x:html.escape(str(x),quote=True)
 rows=''.join('<tr><td>'+e(r['name'])+'</td><td><code>'+e(r['status'])+'</code></td><td>'+e(', '.join(r['different_fields']))+'</td></tr>' for r in d['family_review']['rows'])
 preservation=d.get('preservation');extra=''
 if preservation:
  prows=''.join('<tr><td>'+e(r['name'])+'</td><td>'+e(r['status'])+'</td><td>'+e(', '.join(r['different_fields']))+'</td></tr>' for r in preservation['prior_profiles'])
  extra='<h2>Preservation of prior profiles</h2><table><tr><th>Profile</th><th>Result</th><th>Changed fields</th></tr>'+prows+'</table>'
 unresolved=''.join('<li>'+e(x['profile_name'])+' / button '+e(x['button_id'])+' / slot '+e(x['gesture_slot'])+'</li>' for x in d['current_unresolved_links'])
 text='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Azeron snapshot review</title><style>body{font:16px/1.6 system-ui,sans-serif;background:#edf2f7;color:#17314b;margin:0}main{max-width:1080px;margin:24px auto;background:white;padding:30px;border-radius:12px}h1{font-size:28px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:12px;border-bottom:1px solid #ced8e3;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#e3ecf6}.warn{padding:16px;background:#fff2d8;border-left:4px solid #987030}code{font-size:12px;overflow-wrap:anywhere}.facts{background:#f0f5fa;padding:16px}</style></head><body><main>'''
 text+='<h1>R8 snapshot review — '+e(d['family_review']['family'])+'</h1><p class="warn"><strong>No import or runtime validation.</strong> This compares the supplied files, not the live device. Scope: '+e(d['snapshot_scope'])+'. A historical snapshot is not a current installation inventory.</p>'
 text+='<div class="facts"><b>'+e(d['family_review']['decision'])+'</b><p>Profiles read: '+e(d['current_profile_count'])+'<br>Snapshot SHA-256: <code>'+e(d['current_source']['sha256'])+'</code></p></div>'
 text+='<h2>Candidate-family presence</h2><table><tr><th>Profile</th><th>File comparison</th><th>Differences needing review</th></tr>'+rows+'</table>'+extra
 text+='<h2>Unresolved active layer references in supplied snapshot</h2>'+('<ul>'+unresolved+'</ul>' if unresolved else '<p>No unresolved active Layering reference was found in the supplied profiles.</p>')
 text+='<h2>Interpretation</h2><p>ALREADY_MATCHES / MATCHES_WITH_REMAPPED_ID means that the compared operational fields and linked target names agree. It does not prove the importer, hardware, physical comfort or game behavior. Any STOP result needs reconciliation before further native changes. Metadata-only differences still require review.</p><p>This report contains private profile names. Keep it in the existing private recovery route rather than public Git.</p></main></body></html>'
 with Path(out).open('x',encoding='utf-8') as f:f.write(text)
 return len(text.encode())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(render(a.receipt,a.out))
