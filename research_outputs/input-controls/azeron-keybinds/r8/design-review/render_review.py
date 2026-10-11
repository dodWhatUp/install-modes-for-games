#!/usr/bin/env python3
"""Render this authored Markdown memo to one self-contained RTL HTML document.
Supported subset: headings, paragraphs, tables, bold, inline code and HTTPS links.
No JavaScript, external assets, profile access or browser invocation.
"""
from pathlib import Path
import argparse, html, re

def inline(text):
    s=html.escape(text,quote=True)
    s=re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)',r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',s)
    s=re.sub(r'`([^`]+)`',r'<bdi><code>\1</code></bdi>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'\[(P[1-4]|D1|H[1-8])(?:, (P[1-4]|D1|H[1-8]))?\]',
       lambda m: ' <a class="ref" href="#ref-'+m[1]+'">'+m[1]+'</a>' + (' <a class="ref" href="#ref-'+m[2]+'">'+m[2]+'</a>' if m[2] else ''),s)
    return s

def render(source,target):
    text=source.read_text(encoding='utf-8');lines=text.splitlines();body=[];toc=[];paragraph=[];i=0;count=0
    def flush():
        if not paragraph:return
        t=' '.join(paragraph);anchor=''
        m=re.match(r'\*\*(P[1-4]|D1|H[1-8])\s+—',t)
        if m:anchor=' id="ref-'+m[1]+'"'
        body.append('<p'+anchor+'>'+inline(t)+'</p>');paragraph.clear()
    while i<len(lines):
        line=lines[i].strip()
        if not line:flush();i+=1;continue
        if line.startswith('#'):
            flush();n=len(line)-len(line.lstrip('#'));t=line[n:].strip()
            if n==1:body.append('<h1>'+inline(t)+'</h1>')
            else:
                count+=1;key='section-'+str(count)
                body.append(f'<h{n} id="{key}">'+inline(t)+f'</h{n}>');toc.append((key,t))
            i+=1;continue
        if line.startswith('|'):
            flush();rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',c) for c in row):rows.append(row)
                i+=1
            header=rows[0];body.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th scope="col">'+inline(x)+'</th>' for x in header)+'</tr></thead><tbody>')
            for row in rows[1:]:
                assert len(row)==len(header),'Table column mismatch'
                body.append('<tr>'+''.join('<td>'+inline(x)+'</td>' for x in row)+'</tr>')
            body.append('</tbody></table></div>');continue
        paragraph.append(line);i+=1
    flush()
    links=''.join('<a href="#'+k+'">'+html.escape(t)+'</a>' for k,t in toc)
    template='''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Azeron — ביקורת תכנון והכרעה לפני יישום</title><style>
:root{--ink:#203247;--muted:#53667c;--line:#d8e2ec;--panel:#fff;--bg:#eef2f6;--accent:#1b5c72}
*{box-sizing:border-box}html{scroll-behavior:auto;scroll-padding-top:22px}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.9 system-ui,Arial,sans-serif}header{background:#1b334a;color:#f3f7fb;padding:24px max(20px,calc((100vw - 1350px)/2));border-bottom:5px solid #568699}header b{font-size:14px;letter-spacing:.07em}header p{margin:7px 0 0;font-size:15px;max-width:980px}.layout{display:grid;grid-template-columns:260px minmax(0,1000px);gap:22px;max-width:1326px;padding:26px 18px 60px;margin:auto;align-items:start}.toc{position:sticky;top:18px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 14px;max-height:calc(100vh - 36px);overflow:auto;font-size:13px;line-height:1.5}.toc b{display:block;margin-bottom:10px;font-size:15px}.toc a{display:block;color:#27495f;text-decoration:none;padding:6px 4px;border-bottom:1px solid #edf0f4}.toc a:hover,.toc a:focus{background:#e7eef4;text-decoration:underline}article{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:30px 38px;min-width:0}h1{font-size:32px;line-height:1.3;margin:0 0 14px;color:#183d53}h2{font-size:24px;line-height:1.5;margin:38px 0 14px;padding-top:18px;border-top:1px solid var(--line)}p{margin:10px 0 17px}strong{font-weight:700}a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px;overflow-wrap:anywhere}.ref{display:inline-block;direction:ltr;font-size:11px;font-weight:650;text-decoration:none;background:#e9f0f4;border-radius:4px;padding:0 5px;margin:0 2px;vertical-align:middle}p[id^=ref]{font-size:14px;line-height:1.8;border-right:3px solid #d4e1eb;padding-right:12px}code{font:13px/1.6 ui-monospace,Consolas,monospace;background:#eef2f6;padding:2px 4px;overflow-wrap:anywhere}.table-wrap{overflow-x:auto;margin:18px 0 24px;border:1px solid var(--line);border-radius:8px}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.75}th,td{padding:11px 13px;text-align:right;vertical-align:top;border-bottom:1px solid var(--line)}th{background:#e9f0f6;color:#233f54;font-weight:700}tbody tr:nth-child(even){background:#f7f9fc}tbody tr:last-child td{border-bottom:0}.end{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px;margin-top:30px}.skip{position:absolute;left:-9999px}.skip:focus{position:static;display:block;padding:10px;color:var(--ink);background:#fff}
@media(max-width:1020px){.layout{display:block;max-width:1000px}.toc{position:static;max-height:none;margin-bottom:20px;columns:2}.toc b{column-span:all}.toc a{break-inside:avoid}article{padding:24px 27px}}
@media(max-width:650px){body{font-size:16px;line-height:1.85}.layout{padding:14px 9px 40px}.toc{columns:1}article{padding:22px 16px}h1{font-size:27px}h2{font-size:22px}table{min-width:600px;font-size:13px}header{padding:18px 15px}}
@media print{body{background:#fff;font-size:11pt}.toc,header{display:none}.layout{display:block;max-width:none;padding:0}article{border:0;padding:0;max-width:none}h2{break-after:avoid;font-size:16pt}h1{font-size:21pt}.table-wrap{overflow:visible}table{font-size:9pt;min-width:0}tr{break-inside:avoid}a{color:inherit}.ref{background:transparent}}
</style></head><body><a class="skip" href="#content">מעבר למסמך</a><header><b>AZERON · R8 DESIGN REVIEW · 11.10.2026</b><p>מסמך החלטה אחד, מבוסס על המועמדים הקיימים. אין פרופילים חדשים ואין שינוי בקלט המשחק.</p></header><div class="layout"><nav class="toc" aria-label="תוכן עניינים"><b>ניווט במסמך</b>__TOC__</nav><article id="content">__BODY__<div class="end">מקור עריך: DECISION_REVIEW_HE.md · קובצי הנתונים והבדיקות נלווים למסמך. תוצאות חומרה, משחק ודפדפן נשארות בלתי מאומתות.</div></article></div></body></html>'''
    target.write_text(template.replace('__TOC__',links).replace('__BODY__','\n'.join(body)),encoding='utf-8')
    return count
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('target',type=Path);a=p.parse_args()
    print('Rendered sections:',render(a.source,a.target))
