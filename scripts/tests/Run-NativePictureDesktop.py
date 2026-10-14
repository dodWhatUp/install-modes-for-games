"""Prepare an inert AHK desktop fixture; never use installed settings or hooks.

Default runs assertions then exits. --preview opens only the isolated native UI
for supported desktop inspection; it cannot start Game Input/MIC/key capture.
"""
from pathlib import Path
import argparse
import os
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--editor", choices=("picture", "mic"), default="picture")
    options = parser.parse_args()
    fixture = Path(tempfile.gettempdir()) / ("StudioPictureUiFixture-" + uuid.uuid4().hex)
    fixture.mkdir()
    # Authored BMP and INI, not copied user content; preserve failed fixtures.
    image = fixture / "preview.bmp"
    image.write_bytes(bytes.fromhex("424D3A0000000000000036000000280000000100000001000000010018000000000004000000130B0000130B00000000000000000000" + "0000FF00"))
    config = "[General]\nSlotCount=3\nMicToggle=^!h\n[KeyDisplay]\nEnabled=0\n"
    for n in range(1, 4):
        config += f"[Slot{n}]\nEnabled=0\nName=Desktop fixture picture {n}\nKey=F{13+n}\nSource=Local\nMode=Hold\nFile={image}\nWidth=320\nOpacity=75\nPosition=TopRight\nOffsetX=0\nOffsetY=0\nDuration=2\nPass=0\n"
    (fixture / "settings.ini").write_text(config, encoding="utf-8")
    script = ROOT / "examples/game-input" / ("AzeronOverlayStudio.integrated.ahk" if options.preview else
             ("tests/Test-MicEditor.ahk" if options.editor == "mic" else "tests/Test-PictureEditor.ahk"))
    command = [r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe", "/ErrorStdOut=UTF-8", str(script), "--picture-ui-fixture", str(fixture)]
    print(f"ISOLATED FIXTURE: {fixture}", flush=True)
    if options.preview:
        process = subprocess.Popen(command, cwd=script.parent)
        print(f"PREVIEW PID: {process.pid}; exit normally through the fixture's EXIT button.")
        return 0
    result = subprocess.run(command, cwd=script.parent, capture_output=True, timeout=45)
    print(result.stdout.decode("utf-8", errors="replace"))
    print(result.stderr.decode("utf-8", errors="replace"))
    return result.returncode

if __name__ == "__main__":
    raise SystemExit(main())
