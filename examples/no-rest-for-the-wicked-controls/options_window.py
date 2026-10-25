"""One reusable, nonmodal options window per mod. Opening never saves."""
import tkinter as tk
from tkinter import ttk
from mod_options import SCHEMAS
from floating import show_near_pointer


class OptionsWindow:
    def __init__(self, panel, component):
        self.panel, self.component = panel, component
        self.ident = component['id']
        panel.mod_options.read(self.ident)
        self.window = tk.Toplevel(panel.root)
        self.window.withdraw()
        self.window.title(component['name'] + ' \u2014 Options')
        self.window.transient(panel.root)
        self.window.resizable(True, False)
        self.window.minsize(430, 230)
        self.window.protocol('WM_DELETE_WINDOW', self.window.withdraw)
        body = ttk.Frame(self.window, padding=16)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=component['name'], font=('Segoe UI', 13, 'bold')).pack(anchor='w')
        ttk.Label(body, text=component.get('note', ''), wraplength=440, justify='left').pack(anchor='w', pady=(6, 12))
        self.vars = {}
        self.inputs = []
        self.schema = SCHEMAS.get(self.ident, {'fields': ()})
        for field in self.schema['fields']:
            if field['type'] == 'bool':
                value = tk.BooleanVar(self.window)
                widget = ttk.Checkbutton(body, text=field['label'], variable=value)
                widget.pack(anchor='w', pady=3)
            else:
                line = ttk.Frame(body)
                line.pack(fill='x', pady=4)
                ttk.Label(line, text=field['label']).pack(side='left', padx=(0, 10))
                value = tk.StringVar(self.window)
                widget = ttk.Combobox(line, textvariable=value, values=field['choices'], state='readonly', width=18)
                widget.pack(side='right')
            self.vars[field['key']] = value
            self.inputs.append(widget)
        if not self.schema['fields']:
            ttk.Label(body, text='The loader is controlled by its checkbox in the main window.\nIts files, logs and configuration are available below.', wraplength=440).pack(anchor='w', pady=4)
        self.status = tk.StringVar(value='Reading options...')
        ttk.Label(body, textvariable=self.status, wraplength=440, justify='left').pack(anchor='w', pady=(12, 8))
        self.ontop = tk.BooleanVar(self.window, value=False)
        ttk.Checkbutton(body, text='Keep this window on top', variable=self.ontop,
            command=lambda: self.window.attributes('-topmost', self.ontop.get())).pack(anchor='w', pady=(0, 10))
        bar = ttk.Frame(body)
        bar.pack(fill='x')
        self.save_button = None
        if self.schema['fields']:
            self.save_button = ttk.Button(bar, text='Save options', command=self.save)
            self.save_button.pack(side='left')
            panel.buttons.append(self.save_button)
        self.reload_button = ttk.Button(bar, text='Reload', command=lambda: panel.safe(self.reload))
        self.reload_button.pack(side='left', padx=(6, 0))
        panel.buttons.append(self.reload_button)
        ttk.Button(bar, text='Files...', command=self.files).pack(side='left', padx=6)
        ttk.Button(bar, text='Close', command=self.window.withdraw).pack(side='right')
        self.reload()
        if panel.busy:
            self.reload_button.state(['disabled'])
            if self.save_button:
                self.save_button.state(['disabled'])

    def reload(self):
        self.snapshot = self.panel.mod_options.read(self.ident)
        for field, widget in zip(self.schema['fields'], self.inputs):
            value = self.snapshot['values'][field['key']]
            self.vars[field['key']].set(value)
            if field['type'] == 'enum':
                widget.configure(values=tuple(dict.fromkeys((*field['choices'], value))))
        self.status.set('Changes stay in this window until Save options. Save after exiting the game.'
            if self.vars else 'Opening this window does not change the loader.')

    def save(self):
        if self.panel.busy:
            return
        changes = {key: variable.get() for key, variable in self.vars.items()}
        revision = self.snapshot['revision']
        self.status.set('Checking and saving this mod\u2019s options...')
        for widget in self.inputs:
            widget.state(['disabled'])
        def unlock():
            for widget in self.inputs:
                widget.state(['!disabled'])
        def saved(result):
            unlock()
            self.snapshot = result['snapshot']
            self.status.set('Saved. These options apply on the next game start.' if result['changed'] else 'The options already match the saved values.')
            self.panel.status.set(self.component['name'] + ' options saved. Main checkbox choices are preserved.')
        def failed(error):
            unlock()
            self.status.set(error)
        self.panel.run_async(lambda: self.panel.mod_options.save(self.ident, changes, revision), saved, failed)

    def files(self):
        from mod_panel import open_path
        path = self.panel.service.game / ('MelonLoader' if self.ident == 'loader' else 'UserData')
        self.panel.safe(lambda: open_path(path))

    def show(self, pointer=None):
        show_near_pointer(self.window, pointer)
