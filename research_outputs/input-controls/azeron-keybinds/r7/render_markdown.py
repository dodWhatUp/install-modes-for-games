#!/usr/bin/env python3
"""Small local Markdown→HTML renderer for authored reports; no external assets."""
import argparse,html,re
from pathlib import Path

def inline(t):
 t=html.escape(t,quote=True)
 t=re.sub(r'\[([^\]]+)\]\((https://[^ )]+)\)',r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',t)
 t=re.sub(r'`([^`]+)`',r'<bdi><code>\1</code></bdi>',t)
 t=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',t)
 return t

def render(src,dst):
 lines=src.read_text(encoding='utf-8').splitlines();out=[];para=[];i=0
 def flush():
  if para:out.append('<p>'+inline(' '.join(para))+'</p>');para.clear()
 while i<len(lines):
  s=lines[i].strip()
  if not s:flush();i+=1;continue
  if s.startswith('#'):
   flush();n=len(s)-len(s.lstrip('#'));out.append(f'<h{n}>'+inline(s[n:].strip())+f'</h{n}>');i+=1;continue
  if s.startswith('|'):
   flush();table=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch('[: -]+',x) for x in row):table.append(row)
    i+=1
   out.append('<div class="scroll"><table>')
   for j,row in enumerate(table):
    tag='th' if j==0 else 'td';out.append('<tr>'+''.join('<'+tag+'>'+inline(c)+'</'+tag+'>' for c in row)+'</tr>')
   out.append('</table></div>');continue
  para.append(s);i+=1
 flush()
 template='''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Azeron R7 — מחקר והחלטות</title><style>
*{box-sizing:border-box}body{margin:0;background:#eef2f7;color:#193047;font:17px/1.9 system-ui,Arial,sans-serif}main{max-width:1040px;margin:30px auto;background:white;border:1px solid #d1dbea;border-radius:12px;padding:30px 42px}h1{font-size:31px;line-height:1.35;color:#153956}h2{margin-top:38px;border-top:1px solid #dbe4ee;padding-top:20px;font-size:24px;line-height:1.5}h3{font-size:20px;margin-top:24px}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.6}th,td{padding:11px 13px;text-align:right;border-bottom:1px solid #d4deea;vertical-align:top}th{background:#e7eef7}tr:nth-child(odd){background:#f6f8fb}a{color:#185d87}code{font:14px monospace;background:#ecf1f7;padding:2px 4px}footer{font-size:13px;color:#54687e}@media(max-width:650px){main{margin:0;padding:22px 16px;border:0}h1{font-size:26px}table{min-width:660px}}@media print{body{background:white}main{border:0;margin:0;padding:0}h2{break-after:avoid}.scroll{overflow:visible}tr{break-inside:avoid}}
</style></head><body><main>__CONTENT__<footer>R7 · 2026-10-11 · תכנון, מקור ונתונים אינם הוכחת התקנה או בדיקת משחק.</footer></main></body></html>'''
 dst.write_text(template.replace('__CONTENT__','\n'.join(out)),encoding='utf-8');print(dst)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();render(a.source,a.output)
