"""Saved display-only show/hide preference for Studio maps."""
from __future__ import annotations
import configparser
import io
import os
from pathlib import Path
import tempfile

VERSION = "0.1.0"


def read(directory):
    path = Path(directory) / "overlay-transition.ini"
    raw = path.read_bytes() if path.exists() else None
    if raw is None:
        return {"enabled": False, "duration_ms": 120}, raw
    if len(raw) > 16384 or path.is_symlink():
        raise ValueError("Invalid overlay transition settings")
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(raw.decode("utf-8-sig"))
    section = config["Transition"]
    if section.get("Schema") != "1" or section.get("Enabled") not in {"0", "1"}:
        raise ValueError("Unsupported overlay transition settings")
    duration = section.get("DurationMs", "")
    if not duration.isascii() or not duration.isdecimal() or not 20 <= int(duration) <= 400:
        raise ValueError("Transition duration must be 20–400 ms")
    return {"enabled": section["Enabled"] == "1", "duration_ms": int(duration)}, raw


def save(directory, enabled, duration_ms, expected):
    if type(enabled) is not bool or type(duration_ms) is not int or not 20 <= duration_ms <= 400:
        raise ValueError("Transition duration must be 20–400 ms")
    directory = Path(directory)
    _, current = read(directory)
    if current != expected:
        raise ValueError("Transition settings changed; reopen the controls")
    config = configparser.ConfigParser(interpolation=None)
    if current:
        config.read_string(current.decode("utf-8-sig"))
    if not config.has_section("Transition"):
        config.add_section("Transition")
    config["Transition"].update(Schema="1", Enabled=str(int(enabled)), DurationMs=str(duration_ms))
    stream = io.StringIO(); config.write(stream)
    directory.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="transition-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(stream.getvalue()); out.flush(); os.fsync(out.fileno())
        path = directory / "overlay-transition.ini"
        if (path.read_bytes() if path.exists() else None) != expected:
            raise ValueError("Transition settings changed while saving")
        os.replace(name, path)
    finally:
        if Path(name).exists():
            Path(name).unlink()
    return read(directory)


class TransitionEditor:
    def __init__(self, parent, directory, on_save=lambda: None):
        import tkinter as tk
        from tkinter import ttk
        self.directory, self.on_save = directory, on_save
        value, self.expected = read(directory)
        self.window = tk.Toplevel(parent)
        self.window.title("Overlay show/hide transition")
        self.window.minsize(360, 220)
        body = ttk.Frame(self.window, padding=16); body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        self.enabled = tk.BooleanVar(self.window, value=value["enabled"])
        self.duration = tk.StringVar(self.window, value=str(value["duration_ms"]))
        ttk.Checkbutton(body, text="Smooth show/hide", variable=self.enabled,
                        command=self.refresh).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(body, text="Fade duration (ms)").grid(row=1, column=0, sticky="w", pady=12, padx=(0, 12))
        self.spin = ttk.Spinbox(body, from_=20, to=400, increment=20, width=7, textvariable=self.duration)
        self.spin.grid(row=1, column=1, sticky="w")
        ttk.Label(body, text="20–400 ms · lower is faster.\nLayer changes stay continuous. Applies to the Studio overlay.",
                  wraplength=330).grid(row=2, column=0, columnspan=2, sticky="w")
        self.message = tk.StringVar(self.window)
        ttk.Label(body, textvariable=self.message, wraplength=330).grid(row=3, column=0, columnspan=2, sticky="w", pady=6)
        actions = ttk.Frame(body); actions.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(actions, text="Cancel", command=self.window.destroy).pack(side="left", padx=6)
        ttk.Button(actions, text="Save", command=self.commit).pack(side="left")
        self.window.bind("<Escape>", lambda _: self.window.destroy())
        self.refresh()

    def refresh(self):
        self.spin.configure(state="normal" if self.enabled.get() else "disabled")

    def commit(self):
        try:
            text = self.duration.get()
            if not text.isascii() or not text.isdecimal():
                raise ValueError("Enter a whole duration from 20 to 400 ms")
            save(self.directory, self.enabled.get(), int(text), self.expected)
        except (ValueError, OSError, configparser.Error) as error:
            self.message.set(str(error)); return
        self.on_save()
        self.window.destroy()
