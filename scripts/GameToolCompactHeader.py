"""Compact shared chrome; existing views, commands and settings keep their owners."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

VERSION = '0.2.0'


class CompactHeader:
    def __init__(self, root, header, workspace, appearance):
        self.root, self.header, self.w, self.a = root, header, workspace, appearance
        self.closed = False
        self.interface = None
        self._job = self._poll = None
        self._attempts = 0
        self._interface_trace = None
        self.expanded = tk.BooleanVar(root, False)
        self.menu = workspace.view_menu
        for index in range(self.menu.index('end'),-1,-1):
            if self.menu.type(index)=='cascade' and str(self.menu.entrycget(index,'menu'))==str(workspace.browse_menu):
                self.menu.delete(index)
        self.menu.insert_checkbutton(3,label='Show expanded app controls', variable=self.expanded,
                                  command=self.refresh)
        from GameToolChoiceIcons import install as choice_icons
        self.icon_manager=choice_icons(root)
        self.menu.insert_checkbutton(3,label='Show field icons',variable=self.icon_manager.show_icons,
                                  command=self.icon_manager.save_visibility)
        self.layout_menu = tk.Menu(root, tearoff=False)
        for mode in appearance.selector.cget('values'):
            self.layout_menu.add_radiobutton(label=mode, variable=appearance.mode, value=mode,
                                             command=lambda m=mode: appearance.change(m))
        self.tools_menu = tk.Menu(root, tearoff=False)
        self.tools_menu.add_cascade(label='Browse by', menu=workspace.browse_menu)
        self.tools_menu.add_separator()
        self.tools_menu.add_cascade(label='Identify UI', menu=appearance.marker_menu)
        self.layout_button=ttk.Menubutton(workspace.toolbar,text='Layout \u25be',menu=self.layout_menu)
        self.tools_button=ttk.Menubutton(workspace.toolbar,text='Tools \u25be',menu=self.tools_menu)
        workspace.add_toolbar_action(self.layout_button)
        workspace.add_toolbar_action(self.tools_button)
        # The New interface hides the original workspace. Keep the same View
        # menu reachable there without duplicating any editor or operation.
        self.new_bar = ttk.Frame(root, padding=(8, 2))
        ttk.Label(self.new_bar, text='Interface: New').pack(side='left')
        self.new_menu_button = ttk.Menubutton(self.new_bar, text='View \u25be', menu=self.menu)
        self.new_menu_button.pack(side='left',padx=(16,0))
        self.new_layout_button=ttk.Menubutton(self.new_bar,text='Layout \u25be',menu=self.layout_menu)
        self.new_layout_button.pack(side='left',padx=(6,0))
        self.new_tools_button=ttk.Menubutton(self.new_bar,text='Tools \u25be',menu=self.tools_menu)
        self.new_tools_button.pack(side='left',padx=(6,0))
        self._mode_trace = appearance.mode.trace_add('write', self._queue)
        self.refresh()
        self._connect_interface()

    def _queue(self, *_):
        if not self.closed and self._job is None:
            self._job = self.root.after_idle(self._refresh_idle)

    def _refresh_idle(self):
        self._job = None
        self.refresh()

    def _connect_interface(self):
        self._poll = None
        if self.closed:
            return
        integration = getattr(self.root, 'game_tools_mod_integration', None)
        views = getattr(integration, 'interface_views', None)
        if views is None:
            self._attempts += 1
            if self._attempts < 200:
                self._poll = self.root.after(50, self._connect_interface)
            return
        self.interface = views
        self.interface_menu = tk.Menu(self.menu, tearoff=False)
        for mode in views.selector.cget('values'):
            self.interface_menu.add_radiobutton(label=mode, variable=views.selected, value=mode,
                                                command=lambda m=mode: views.show(m))
        self.layout_menu.add_separator()
        self.layout_menu.add_cascade(label='Interface', menu=self.interface_menu)
        self.tools_menu.insert_cascade(1,label='Open tool', menu=views.menu)
        self.tools_menu.insert_command(2,label='Show APP LAUNCHER', command=views.show_launcher)
        self._interface_trace = views.selected.trace_add('write', self._queue)
        self.refresh()

    def refresh(self):
        if self.closed:
            return
        views = self.interface
        new = bool(views and views.mode == 'New')
        expanded = self.expanded.get()
        self.new_bar.pack_forget()
        self.header.pack_forget()
        if views:
            views.bar.pack_forget()
        banner = self.a.banner
        if expanded:
            if not new:
                before = banner if banner and banner.winfo_manager() == 'pack' else self.w.frame
                options = {'before': before} if before.winfo_manager() == 'pack' else {}
                self.header.pack(fill='x', **options)
            if views:
                packed = self.root.pack_slaves()
                views.bar.pack(side='top', fill='x', **({'before': packed[0]} if packed else {}))
        if new:
            packed = self.root.pack_slaves()
            self.new_bar.pack(side='top', fill='x', **({'before': packed[0]} if packed else {}))
        style = ttk.Style(self.root)
        style.configure('Header.TButton', padding=(8, 3), font=('Segoe UI', 10))
        style.configure('Header.TMenubutton', padding=(8, 3), font=('Segoe UI', 10))
        style.configure('Header.TCombobox', padding=(4, 2), font=('Segoe UI', 10))
        self.w.toolbar.configure(padding=(8, 3))
        self.w.search_label.configure(text='Find  \u00b7  Ctrl+K')
        self.w.selector.configure(style='Header.TCombobox',width=28)
        self.w.navigation_button.configure(style='Header.TButton')
        self.w.view_menu.master.configure(style='Header.TMenubutton')
        for button in (self.new_menu_button,self.new_layout_button,self.new_tools_button,self.layout_button,self.tools_button):
            button.configure(style='Header.TMenubutton')
        self.w.breadcrumb.configure(padding=(10, 4))
        modern = self.w.modern
        if modern and modern.active:
            for button in (modern.back, modern.detail_button):
                button.configure(style='Header.TButton')
        if banner:
            banner.configure(pady=1)
            if banner.winfo_manager() == 'pack':
                banner.pack_configure(padx=8, pady=0)

    def close(self):
        if self.closed:
            return
        self.closed = True
        for job in (self._job, self._poll):
            if job is not None:
                self.root.after_cancel(job)
        self.a.mode.trace_remove('write', self._mode_trace)
        if self.interface and self._interface_trace:
            self.interface.selected.trace_remove('write', self._interface_trace)
        for button in (self.layout_button,self.tools_button):
            if button in self.w.toolbar_actions:self.w.toolbar_actions.remove(button)
            button.destroy()
        self.layout_menu.destroy()
        self.tools_menu.destroy()
        self.new_bar.destroy()
