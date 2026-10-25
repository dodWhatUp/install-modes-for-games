"""Focused Tk key-label capture. No global hooks, key emission or profile writes."""
from __future__ import annotations
import sys
import tkinter as tk
from tkinter import ttk

VERSION = "0.1.0"

SPECIAL_KEYS = (
    "Esc", "Tab", "Enter", "Space", "Backspace", "Delete", "Insert",
    "Home", "End", "Page Up", "Page Down", "Up Arrow", "Down Arrow",
    "Left Arrow", "Right Arrow", "Ctrl", "Right Ctrl", "Shift", "Right Shift",
    "Alt", "Right Alt", "Win", "Right Win", "Menu", "Caps Lock", "Num Lock",
    "Scroll Lock", "Print Screen", "Pause",
) + tuple(f"F{i}" for i in range(1, 25)) + tuple(f"Numpad {i}" for i in range(10)) + (
    "Numpad Enter", "Numpad Decimal", "Numpad Add", "Numpad Subtract",
    "Numpad Multiply", "Numpad Divide", "Volume Up", "Volume Down", "Volume Mute",
    "Media Play/Pause", "Media Stop", "Media Next", "Media Previous",
    "Minus", "Equals", "Left Bracket", "Right Bracket", "Backslash",
    "Semicolon", "Apostrophe", "Backtick", "Comma", "Period", "Slash",
)

ALIASES = {
    "Escape":"Esc", "Return":"Enter", "space":"Space", "BackSpace":"Backspace",
    "Prior":"Page Up", "Next":"Page Down", "Up":"Up Arrow", "Down":"Down Arrow",
    "Left":"Left Arrow", "Right":"Right Arrow", "Control_L":"Ctrl", "Control_R":"Right Ctrl",
    "Shift_L":"Shift", "Shift_R":"Right Shift", "Alt_L":"Alt", "Alt_R":"Right Alt",
    "Meta_L":"Win", "Meta_R":"Right Win", "Super_L":"Win", "Super_R":"Right Win",
    "Win_L":"Win", "Win_R":"Right Win", "App":"Menu", "Caps_Lock":"Caps Lock", "Num_Lock":"Num Lock",
    "Scroll_Lock":"Scroll Lock", "Print":"Print Screen", "Sys_Req":"Print Screen",
    "KP_Enter":"Numpad Enter", "KP_Decimal":"Numpad Decimal", "KP_Delete":"Numpad Decimal",
    "KP_Add":"Numpad Add", "KP_Subtract":"Numpad Subtract", "KP_Multiply":"Numpad Multiply",
    "KP_Divide":"Numpad Divide", "minus":"Minus", "equal":"Equals", "bracketleft":"Left Bracket",
    "bracketright":"Right Bracket", "backslash":"Backslash", "semicolon":"Semicolon",
    "apostrophe":"Apostrophe", "grave":"Backtick", "comma":"Comma", "period":"Period", "slash":"Slash",
    "XF86AudioRaiseVolume":"Volume Up", "XF86AudioLowerVolume":"Volume Down", "XF86AudioMute":"Volume Mute",
    "XF86AudioPlay":"Media Play/Pause", "XF86AudioStop":"Media Stop", "XF86AudioNext":"Media Next", "XF86AudioPrev":"Media Previous",
}
ALIASES.update({f"KP_{i}":f"Numpad {i}" for i in range(10)})
ALIASES.update(dict(zip(("KP_Insert","KP_End","KP_Down","KP_Next","KP_Left","KP_Begin","KP_Right","KP_Home","KP_Up","KP_Prior"),
                        (f"Numpad {i}" for i in range(10)))))
MODIFIERS = {"Ctrl", "Right Ctrl", "Shift", "Right Shift", "Alt", "Right Alt", "Win", "Right Win"}


def key_name(keysym, keycode=0, platform=None, state=0):
    """Windows VK letters remain stable across active text layouts; no raw key log."""
    if (platform or sys.platform) == "win32":
        if keycode==13 and state & 0x40000: return "Numpad Enter"
        if 65 <= keycode <= 90: return chr(keycode)
        if 48 <= keycode <= 57: return chr(keycode)
        if 96 <= keycode <= 105: return f"Numpad {keycode-96}"
        if 112 <= keycode <= 135: return f"F{keycode-111}"
        special = {186:"Semicolon",187:"Equals",188:"Comma",189:"Minus",190:"Period",191:"Slash",
                   192:"Backtick",219:"Left Bracket",220:"Backslash",221:"Right Bracket",222:"Apostrophe",
                   173:"Volume Mute",174:"Volume Down",175:"Volume Up",176:"Media Next",177:"Media Previous",
                   178:"Media Stop",179:"Media Play/Pause"}
        if keycode in special: return special[keycode]
    if keysym in ALIASES: return ALIASES[keysym]
    if len(keysym)==1 and keysym.isascii() and keysym.isalnum(): return keysym.upper()
    if keysym in SPECIAL_KEYS: return keysym
    return None


def chord(key, state=0, platform=None):
    if key in MODIFIERS: return key
    # Tk's Windows owner uses Mod1 for NumLock and Mod2 for Alt.
    windows=(platform or sys.platform)=="win32"
    modifiers = [name for bit,name in ((4,"Ctrl"),((16|0x20000) if windows else 8,"Alt"),(1,"Shift")) if state & bit]
    return "+".join(modifiers+[key])


class CaptureDialog:
    def __init__(self, parent, on_use):
        self.on_use=on_use; self.value=None; self.closed=False
        self.window=tk.Toplevel(parent); self.window.title("Capture key label")
        self.window.transient(parent); self.window.resizable(False,False)
        form=ttk.Frame(self.window,padding=14);form.pack(fill="both",expand=True)
        ttk.Label(form,text="Press a key or combination in the capture box.").pack(anchor="w")
        ttk.Label(form,text="Display label only · Azeron output stays unchanged.").pack(anchor="w",pady=(3,10))
        self.preview=tk.StringVar(self.window,value="Click here, then press a key")
        self.pad=tk.Label(form,textvariable=self.preview,width=42,height=4,takefocus=True,
                          relief="sunken",borderwidth=2,highlightthickness=2)
        self.pad.pack(fill="x");self.pad.bind("<Button-1>",lambda _:self.pad.focus_set())
        self.pad.bind("<KeyPress>",self.press)
        self.pad.bind("<KeyRelease>",lambda _:"break")
        self.pad.bind("<FocusIn>",lambda _:self.pad.configure(highlightbackground="#67A9FF"))
        self.pad.bind("<FocusOut>",lambda _:self.pad.configure(highlightbackground="#888888"))
        ttk.Label(form,text="Esc cancels. Choose Esc, system or media keys from the key list if capture is unavailable.",wraplength=420).pack(anchor="w",pady=8)
        buttons=ttk.Frame(form);buttons.pack(fill="x")
        ttk.Button(buttons,text="Cancel",command=self.cancel).pack(side="right")
        self.use_button=ttk.Button(buttons,text="Use key label",command=self.use,state="disabled")
        self.use_button.pack(side="right",padx=8)
        self.window.protocol("WM_DELETE_WINDOW",self.cancel)
        self.window.bind("<Escape>",lambda _:self.cancel())
        self.window.after_idle(self.pad.focus_set)

    def press(self,event):
        if self.closed or self.window.focus_get()!=self.pad: return
        if event.keysym=="Escape": self.cancel();return "break"
        key=key_name(event.keysym,event.keycode,state=event.state)
        self.value=chord(key,event.state) if key else None
        self.preview.set(self.value or "Key not recognized — use the special-key list")
        self.use_button.configure(state="normal" if self.value else "disabled")
        return "break"

    def use(self):
        if self.value and not self.closed:
            value=self.value;self.close();self.on_use(value)

    def cancel(self): self.close()

    def close(self):
        if not self.closed:
            self.closed=True;self.window.destroy()
