"""Compatibility entry for the shared offline gallery owner."""
import json
from pathlib import Path
import importlib.util
import sys

def shared(name):
    if name not in sys.modules:
        try:
            __import__(name)
        except ModuleNotFoundError:
            path=Path(__file__).resolve().parents[2]/'scripts'/(name+'.py')
            spec=importlib.util.spec_from_file_location(name,path)
            module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name]
shared('GameToolFloatingWindows')
_api=shared('GameToolModGallery')
PreviewWindow=_api.PreviewWindow
webbrowser=_api.webbrowser

def read_catalog():
    return json.loads(Path(__file__).with_name('mod_details.json').read_text(encoding='utf-8'))['mods']
