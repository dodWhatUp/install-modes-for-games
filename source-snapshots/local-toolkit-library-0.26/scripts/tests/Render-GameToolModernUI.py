"""Render actual Python presentation and Comparison with private fixture data.

Use only in a selected isolated X display. No game, AHK, capture provider or
installed user data is accessed. These are UI snapshots, not video recording.
"""
import argparse
from pathlib import Path
import sys
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from GameToolWorkspace import Workspace
from GameToolAppearance import Appearance
from GameToolComparisonPanel import ComparisonPanel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as private:
        root = tk.Tk(); root.title("Unified Game Tools · offline UI fixture")
        root.geometry("1360x880+0+0")
        errors = []
        root.report_callback_exception = lambda *e: errors.append(str(e))
        status = tk.StringVar(root, "UI fixture only · no live providers")
        footer = ttk.Frame(root, padding=(16, 8)); footer.pack(side="bottom", fill="x")
        ttk.Label(footer, textvariable=status, wraplength=600).pack(anchor="w")
        header = ttk.Frame(root, padding=(18, 12)); header.pack(fill="x")
        ttk.Label(header, text="GameTools", font=("Segoe UI", 16, "bold")).pack(side="left")
        root.game_tools_scope_banner = tk.Label(root, text="Offline fixture scope", bg="#fff0bf", fg="#604800")
        root.game_tools_scope_banner.pack(fill="x", padx=12)
        w = Workspace(root, status); w.frame.pack(fill="both", expand=True, padx=12)
        tabs = ttk.Notebook(w.content); tabs.pack(fill="both", expand=True)
        pages = {}
        for record in w.registry.features:
            page = ttk.Frame(tabs, padding=16); tabs.add(page, text=record["route"])
            pages[record["route"]] = page
            if record["route"] != "comparison":
                ttk.Label(page, text="Inert fixture: " + record["title"]).pack(anchor="w")
        panel = ComparisonPanel(pages["comparison"], status)
        w.attach(tabs, pages)
        a = Appearance(root, header, w, status, Path(private)/"views.json", "0.18.0 fixture")
        root.update(); a.preview("Modern"); root.update()
        def snapshot(name, size):
            root.geometry(size+"+0+0"); root.update()
            root.after(80, lambda: None); root.update_idletasks()
            if w.home_visible and w.modern.cards and w.modern.columns == 1:
                assert w.modern.cards[0].winfo_width() >= w.modern.grid.winfo_width()-70, "Narrow card did not fill its available column"
            # Selected test-owned X window, not the host desktop. Use the
            # guest's already installed ImageMagick; no Pillow installation.
            subprocess.run(["import", "-window", hex(root.winfo_id()), str(args.output/name)],
                           check=True, timeout=15)
        snapshot("modern-home-wide.png", "1360x880")
        snapshot("modern-home-narrow.png", "620x600")
        snapshot("modern-home-minimum.png", "620x430")
        root.geometry("880x600+0+0"); root.update()
        root.tk.call("tk", "scaling", 1.8); w.modern.refresh(); root.update()
        snapshot("modern-home-scaled.png", "880x600")
        root.tk.call("tk", "scaling", 1.33); w.modern.refresh(); root.update()
        root.geometry("1360x880+0+0"); root.update()
        w.modern.domain_buttons[1].invoke(); root.update()
        snapshot("modern-controls.png", "1360x880")
        w.modern.show_home(); w.query.set("saved-result"); root.update()
        snapshot("modern-search.png", "880x650")
        w.query.set(""); w.route("page.comparison"); root.update()
        panel.load_from_path(Path(__file__).resolve().parents[2]/"examples/game-tool-hub/comparison-fixture.example.json")
        snapshot("modern-comparison.png", "1360x880")
        a.preview_only = True; a.close(); w.close(); root.update_idletasks(); root.destroy()
        if errors:
            raise RuntimeError("Fixture UI callback failures: " + str(errors))
    print("Rendered 7 actual UI snapshots; no live measurements or installed data.")


if __name__ == "__main__":
    main()
