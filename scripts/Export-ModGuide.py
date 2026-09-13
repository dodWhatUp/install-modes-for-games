"""Export the curated knowledge base, never game files or private snapshots."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit, unquote

ALLOWED = {'.md', '.txt', '.json', '.ini', '.toml', '.ps1', '.py', '.lua', '.cpp', '.h', '.hpp', '.patch'}
ROOT_FILES = {'README.md', 'AGENTS.md', 'LICENSE', '.gitignore', '.gitattributes'}
ROOT_DIRS = {'docs', 'games', 'preferences', 'templates', 'examples', 'scripts', 'evidence'}
REMOTE = 'https://github.com/dodWhatUp/install-modes-for-games/blob/main/'
PRIVATE = re.compile(r'[A-Za-z]:[\\/]+Users[\\/]+(?:danie|[^<>\\/\s]+)(?=[\\/])|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{25,}')


def collect(repo: Path) -> dict[str, bytes]:
    files = {}
    candidates = [repo / name for name in ROOT_FILES if (repo / name).is_file()]
    for folder in sorted(ROOT_DIRS):
        candidates.extend((repo / folder).rglob('*'))
    for path in sorted(candidates):
        rel = path.relative_to(repo)
        if not path.is_file() or path.is_symlink():
            continue
        if rel.as_posix() not in ROOT_FILES:
            if rel.parts[0] not in ROOT_DIRS or path.suffix.lower() not in ALLOWED:
                continue
        if any(p.startswith('.') and p not in {'.gitignore', '.gitattributes'} for p in rel.parts):
            continue
        data = path.read_bytes()
        if len(data) > 2_000_000 or b'\0' in data:
            raise ValueError(f'Non-text or oversized export candidate: {rel}')
        content = data.decode('utf-8-sig')
        # The scanner source contains patterns, not credentials or private paths.
        if PRIVATE.search(content):
            raise ValueError(f'Private path/credential pattern requires review: {rel}')
        files[rel.as_posix()] = data
    return files


def render(repo: Path, files: dict[str, bytes]) -> str:
    import markdown
    primary = 'docs/INSTALLED-GAMES-MOD-GUIDE.md'
    chapters = [primary, 'games/skyrim-special-edition/HISTORY.md', 'games/skyrim-special-edition/BASIC-SETUP.md', 'games/skyrim-special-edition/COMPARISONS.md']
    chapters += sorted(p for p in files if p.endswith('/COMPARISONS.md') and p not in chapters)
    anchors = {p: 'chapter-' + str(i) for i, p in enumerate(chapters)}
    nav, body = [], []
    for p in chapters:
        text = files[p].decode('utf-8-sig')
        title = text.splitlines()[0].lstrip('# ')
        content = markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists'])

        def link(match):
            href = html.unescape(match.group(1))
            if urlsplit(href).scheme or href.startswith('#'):
                return match.group(0)
            dest = (repo / Path(p).parent / unquote(href.split('#')[0])).resolve()
            if not dest.is_relative_to(repo):
                raise ValueError(f'Link leaves repository: {p} -> {href}')
            relative = dest.relative_to(repo).as_posix()
            if not dest.exists():
                raise ValueError(f'Missing link: {p} -> {href}')
            target = '#' + anchors[relative] if relative in anchors else REMOTE + quote(relative, safe='/')
            return 'href="' + html.escape(target, quote=True) + '"'

        content = re.sub(r'href="([^"]+)"', link, content)
        content = content.replace('<table>', '<div class="table-scroll"><table>').replace('</table>', '</table></div>')
        nav.append(f'<a href="#{anchors[p]}">{html.escape(title)}</a>')
        body.append(f'<article id="{anchors[p]}" data-game><p class="source">Reviewed 14 September 2026 · <a href="{REMOTE}{quote(p, safe="/")}">Repository source</a></p>{content}</article>')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Installed Games — Mod Guide</title>
<style>
:root{color-scheme:dark;--bg:#10141c;--panel:#19212e;--ink:#e8edf4;--muted:#aab9cc;--accent:#81d7c8}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,sans-serif}a{color:var(--accent);text-underline-offset:3px}header{padding:40px 5vw;border-bottom:1px solid #334155;background:linear-gradient(120deg,#152e35,#1e2438)}header h1{font-size:clamp(28px,4vw,48px);line-height:1.15;margin:8px 0 20px}header p{max-width:900px;color:var(--muted)}.eyebrow{letter-spacing:.13em;text-transform:uppercase;font-size:12px}main{display:grid;grid-template-columns:260px minmax(0,1fr);gap:30px;max-width:1600px;margin:auto;padding:30px}nav{position:sticky;top:15px;max-height:94vh;overflow:auto;align-self:start}nav a{display:block;font-size:13px;line-height:1.4;padding:8px 0}label{font-weight:650;display:block}input{width:100%;padding:12px;margin:8px 0 14px;border-radius:8px;border:1px solid #52627c;background:#0d1522;color:var(--ink)}article{background:var(--panel);padding:30px;border-radius:12px;margin-bottom:30px;scroll-margin-top:18px}article h1{font-size:28px;line-height:1.3}h2{font-size:22px;margin-top:34px}h3{font-size:18px}.source{color:var(--muted);font-size:12px}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.55;min-width:650px}th,td{vertical-align:top;text-align:left;padding:12px;border-bottom:1px solid #3c485c}th{background:#253347;color:#d7f6f0}tr:nth-child(even){background:#1c2736}.table-scroll{overflow:auto;margin:18px 0}code{font-size:.9em;overflow-wrap:anywhere}pre{overflow:auto;padding:14px;background:#10141c}li{margin-bottom:8px}article[hidden]{display:none}#empty{display:none;padding:30px}footer{padding:25px 5vw;color:var(--muted);font-size:13px}@media(max-width:850px){main{grid-template-columns:1fr;padding:15px}nav{position:static;max-height:250px}article{padding:18px}}@media print{body{background:white;color:black}header,article{background:white}nav,input{display:none}main{display:block}article{break-before:page}a{color:#12665d}.table-scroll{overflow:visible}table{min-width:0;font-size:9px}th,td{padding:5px}.source{color:#555}}
</style></head><body><header><div class="eyebrow">Game modding library · September 2026</div><h1>Better games, organized choices.</h1><p>Fourteen installed games. Compare foundations, performance, graphics, menus, gameplay systems and new content. Installation status stays separate from recommendations.</p><a href="https://github.com/dodWhatUp/install-modes-for-games">Open maintained repository</a></header><main><nav><label for="search">Find a game or mod</label><input id="search" type="search" placeholder="Skyrim, magic, DLSS…">''' + ''.join(nav) + '''</nav><section><p id="empty">No guide matches that search.</p>''' + ''.join(body) + '''</section></main><footer>Dated information export. Use original author links for downloads; no mod binaries or saves are included.</footer><script>
const q=document.getElementById('search');const articles=[...document.querySelectorAll('[data-game]')];q.addEventListener('input',()=>{const term=q.value.toLowerCase().trim();let count=0;articles.forEach(a=>{a.hidden=!a.textContent.toLowerCase().includes(term);if(!a.hidden)count++});document.getElementById('empty').style.display=count?'none':'block'});document.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>{q.value='';articles.forEach(x=>x.hidden=false);document.getElementById('empty').style.display='none'}));
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    if not (repo / 'docs/INSTALLED-GAMES-MOD-GUIDE.md').is_file():
        raise ValueError('Not the expected modding repository')
    if out.is_relative_to(repo):
        raise ValueError('Choose an output directory outside the repository')
    files = collect(repo)
    files['Mod-Guide.html'] = render(repo, files).encode('utf-8')
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(), 'source': REMOTE.removesuffix('blob/main/'), 'files': [{'path': p, 'bytes': len(d), 'sha256': hashlib.sha256(d).hexdigest()} for p, d in sorted(files.items())]}
    files['EXPORT-MANIFEST.json'] = json.dumps(manifest, indent=2).encode('utf-8')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'Mod-Guide.html').write_bytes(files['Mod-Guide.html'])
    (out / 'EXPORT-MANIFEST.json').write_bytes(files['EXPORT-MANIFEST.json'])
    archive = out / 'Game-Modding-Guides-2026-09-14.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p, data in sorted(files.items()):
            z.writestr(p, data)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for row in manifest['files']:
            assert hashlib.sha256(z.read(row['path'])).hexdigest() == row['sha256']
    print(json.dumps({'files': len(files), 'archive_bytes': archive.stat().st_size, 'output': str(out)}))


if __name__ == '__main__':
    main()
