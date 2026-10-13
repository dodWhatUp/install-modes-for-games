"""Small source/build/DOM fixture, with no network or package dependencies."""
from pathlib import Path
import json

page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Guest build test</title>
<label>Project <input aria-label="Project" value="Baseline"></label>
<label><input type="checkbox">Enable report</label><button>Run test</button>
<p role="status">Waiting</p><script>
document.querySelector('button').onclick = () => {
  document.querySelector('[role="status"]').textContent =
    document.querySelector('input').value + ': ' +
    (document.querySelector('[type="checkbox"]').checked ? 'PASS' : 'DISABLED');
};</script></html>'''
out = Path("dist")
out.mkdir(exist_ok=False)
(out / "index.html").write_text(page, encoding="utf-8")
(out / "build-result.json").write_text(json.dumps({"built": True, "encoding": "UTF-8"}) + "\n")
print("BUILD_PASS")
