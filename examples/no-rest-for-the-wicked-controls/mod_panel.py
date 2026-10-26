"""Compact controls for an explicitly prepared private Wicked installation."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from switcher import Switcher
from mod_options import ModOptions
from options_window import OptionsWindow
from preview_window import PreviewWindow, read_catalog


def open_path(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError('This location does not exist yet: ' + str(path))
    if os.name == 'nt':
        os.startfile(str(path))
    else:
        subprocess.Popen(['xdg-open', str(path)])


class Panel(ttk.Frame):
    def __init__(self, root, service):
        super().__init__(root, padding=18)
        self.pack(fill='both', expand=True)
        self.root, self.service = root, service
        self.state = None
        self.busy = False
        self.events = queue.Queue()
        self.vars = {}
        self.status_vars = {}
        self.buttons = []
        self.row_actions = {}
        self.option_windows = {}
        self.preview_windows = {}
        self.catalog = read_catalog()
        self.mod_options = ModOptions(service)
        root.title('No Rest for the Wicked \u2014 Gameplay Mods 1.2')
        root.geometry('870x525')
        root.minsize(720, 490)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'))
        style.configure('Inline.TButton', font=('Segoe UI', 9), padding=(3, 0))
        header = ttk.Frame(self)
        header.pack(fill='x')
        title_label=ttk.Label(header, text='No Rest for the Wicked', style='Title.TLabel');title_label.pack(side='left')
        tools = ttk.Menubutton(header, text='Files & tools \u25be')
        tools.pack(side='right')
        menu = tk.Menu(tools, tearoff=False)
        tools['menu'] = menu
        for name, action in [
            ('Show APP LAUNCHER', lambda: open_path(service.workspace)),
            ('Open game folder', lambda: open_path(service.game)),
            ('Open mod settings folder', lambda: open_path(service.game / 'UserData')),
            ('Open loader files and logs', lambda: open_path(service.game / 'MelonLoader')),
            ('Read use and verification guide', lambda: open_path(service.workspace / 'START-HERE.txt')),
            ('Open recovery folder', lambda: open_path(service.workspace / 'recovery')),
            ('Install / Update files...', self.install_info),
        ]:
            menu.add_command(label=name, command=lambda fn=action: self.safe(fn))
        self.status = tk.StringVar(value='Reading installed files...')
        ttk.Label(self, textvariable=self.status, wraplength=800).pack(anchor='w', pady=(8, 10))
        box = ttk.LabelFrame(self, text='Managed gameplay mods', padding=12)
        self.mod_rows = box
        box.pack(fill='x')
        box.columnconfigure(0, weight=1)
        for index, component in enumerate(service.components):
            ident = component['id']
            variable = self.vars[ident] = tk.BooleanVar(value=False)
            state_var = self.status_vars[ident] = tk.StringVar(value='Reading...')
            label = component['name'] + ('  \u00b7 main setup' if component.get('recommended') else '')
            button = ttk.Checkbutton(box, text=label, variable=variable)
            button.grid(row=index, column=0, sticky='w', pady=3)
            self.buttons.append(button)
            ttk.Label(box, textvariable=state_var, width=11).grid(row=index, column=1, sticky='e')
            actions = {}
            for column, source, label, width in ((2, 'github', 'GitHub', 7), (3, 'nexus', 'Nexus', 6)):
                link = ttk.Button(box, text=label, width=width, style='Inline.TButton',
                    command=lambda c=component, s=source: self.author_page(c, s))
                link.grid(row=index, column=column, padx=(3, 0))
                if not self.catalog.get(ident, {}).get(source):
                    link.state(['disabled'])
                actions[source] = link
            preview = ttk.Button(box, text='Preview', width=7, style='Inline.TButton',
                command=lambda c=component: self.safe(lambda: self.open_preview(c)))
            preview.grid(row=index, column=4, padx=(3, 0))
            options = ttk.Button(box, text='Options', width=7, style='Inline.TButton',
                command=lambda c=component: self.safe(lambda: self.open_options(c)))
            options.grid(row=index, column=5, padx=(3, 0))
            self.row_actions[ident] = dict(actions, preview=preview, options=options)
        row = ttk.Frame(self)
        row.pack(fill='x', pady=(12, 8))
        for name, action in [('Main setup On', self.main_on), ('All Mods Off', self.all_off),
                             ('Apply selection', self.apply_selection), ('Refresh', self.refresh)]:
            button = ttk.Button(row, text=name, command=action)
            button.pack(side='left', padx=(0, 7))
            self.buttons.append(button)
        usage=ttk.Label(self, text='GitHub / Nexus: source pages. Preview: description and images. Options: mod settings.\nGrey source buttons have no verified page. Floating windows open beside the mouse.',wraplength=800)
        usage.pack(anchor='w', pady=(4, 6))
        ttk.Label(self, text='Apply after saving and exiting the game. Settings and saves stay in place.\nTurning a mod off does not undo items, inventory capacity or other changes already saved by that mod.',
            wraplength=800, foreground='#6b4d20').pack(anchor='w', pady=(10, 0))
        root.bind('<F5>', lambda event: self.refresh())
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.closed = False
        try:from GameToolAppMenus import AppMenus
        except ModuleNotFoundError as error:
            if error.name!='GameToolAppMenus':raise
            sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
            from GameToolAppMenus import AppMenus
        self.chrome=AppMenus(header,root=root,preference=service.workspace/'ui-chrome.json',title=title_label,
                             original_controls=(tools,),tools_menu=menu,status=self.status.set)
        self.chrome.visibility('Show usage tips',(usage,),'usage-tips')
        self.chrome.visibility('Show source links',(w for row in self.row_actions.values() for key,w in row.items() if key in ('github','nexus')),'source-links')
        self.job = root.after(100, self.drain)
        self.refresh()

    def safe(self, fn):
        try:
            return fn()
        except Exception as exc:
            messagebox.showerror('Gameplay mods', str(exc), parent=self.root)

    def author_page(self, component, source):
        url = self.catalog.get(component['id'], {}).get(source)
        if url:
            self.safe(lambda: webbrowser.open(url))

    def open_options(self, component):
        pointer = self.root.winfo_pointerxy()
        ident = component['id']
        if ident not in self.option_windows:
            self.option_windows[ident] = OptionsWindow(self, component)
        self.option_windows[ident].show(pointer)
        return self.option_windows[ident]

    def open_preview(self, component):
        pointer = self.root.winfo_pointerxy()
        ident = component['id']
        if ident not in self.preview_windows:
            self.preview_windows[ident] = PreviewWindow(self, component, self.catalog.get(ident, {}))
        self.preview_windows[ident].show(pointer)
        return self.preview_windows[ident]

    def install_info(self):
        messagebox.showinfo('Install / Update',
            'Opening these controls never installs or updates files.\n\n'
            'Downloaded author archives and the prepared installation receipt are in the setup folder. '
            'A loader or mod update needs its own source review, save backup and new hash manifest. '
            'The controls refuse changed or unknown files.\n\n'
            'Use Files & tools > Show APP LAUNCHER to open that folder.', parent=self.root)

    def refresh(self):
        if self.busy:
            return
        def read():
            self.state = self.service.inspect()
            on = 0
            for row in self.state['components']:
                self.vars[row['id']].set(row['state'] == 'on')
                self.status_vars[row['id']].set(row['state'].title() if row['available'] else 'Not ready')
                on += row['state'] == 'on'
            self.status.set(f'{on} managed components On. File state verified; in-game behavior has not been tested.'
                if self.state['game_build_matches'] else 'Game files changed. Compatibility review required before Apply.')
        self.safe(read)

    def main_on(self):
        for component in self.service.components:
            self.vars[component['id']].set(component['id'] == 'loader' or component.get('recommended', False))
        self.apply_selection()

    def all_off(self):
        for variable in self.vars.values():
            variable.set(False)
        self.apply_selection()

    def apply_selection(self):
        if self.busy or self.state is None:
            return
        desired = {key: value.get() for key, value in self.vars.items()}
        if any(value for key, value in desired.items() if key != 'loader'):
            desired['loader'] = True
            self.vars['loader'].set(True)
        revision = self.state['revision']
        self.status.set('Checking game state and applying the selected files...')
        def saved(result):
            self.refresh()
            self.status.set(f"Applied and verified {result['changed']} file changes. These controls can now be closed.")
        self.run_async(lambda: self.service.apply(desired, revision), saved, lambda error: self.refresh())

    def run_async(self, operation, on_success, on_error=None):
        if self.busy:
            return
        self.busy = True
        for button in self.buttons:
            button.state(['disabled'])
        def work():
            try:
                self.events.put(('ok', operation(), on_success))
            except Exception as exc:
                self.events.put(('error', str(exc), on_error))
        threading.Thread(target=work, daemon=True).start()

    def drain(self):
        try:
            kind, result, callback = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            for button in self.buttons:
                button.state(['!disabled'])
            if callback:
                self.safe(lambda: callback(result))
            if kind == 'error':
                self.status.set(result)
                messagebox.showerror('Nothing applied / changes recovered', result, parent=self.root)
        if not self.closed:
            self.job = self.root.after(100, self.drain)

    def close(self):
        if self.busy:
            messagebox.showinfo('Apply in progress', 'Wait for the current file transaction to finish.', parent=self.root)
            return
        self.closed = True
        self.root.after_cancel(self.job)
        self.root.destroy()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    root = tk.Tk()
    try:
        Panel(root, Switcher(args.workspace))
        root.mainloop()
    except Exception as exc:
        messagebox.showerror('Gameplay mod setup', str(exc), parent=root)
        root.destroy()
        sys.exit(1)
