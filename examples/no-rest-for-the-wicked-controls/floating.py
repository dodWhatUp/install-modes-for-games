"""Compatibility entry for the shared floating-window owner."""
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
_api=shared('GameToolFloatingWindows')
popup_rectangle=_api.popup_rectangle
work_area=_api.work_area
show_near_pointer=_api.show_near_pointer
