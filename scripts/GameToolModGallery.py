"""Offline author description/gallery; no game or browser state is changed."""
import json
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import webbrowser
from GameToolFloatingWindows import show_near_pointer


class PreviewWindow:
    def __init__(self, panel, component, detail, media_root=None):
        self.panel, self.component, self.detail = panel, component, detail
        self.media_root = Path(media_root) if media_root is not None else Path(__file__).parent
        self.window = tk.Toplevel(panel.root)
        self.window.withdraw()
        self.window.title(component['name'] + ' - Preview')
        self.window.transient(panel.root)
        self.window.minsize(430, 350)
        self.window.protocol('WM_DELETE_WINDOW', self.window.withdraw)
        body = ttk.Frame(self.window, padding=12)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(3, weight=1)
        ttk.Label(body, text=component['name'], font=('Segoe UI', 13, 'bold')).grid(row=0, column=0, sticky='w')
        self.description = ttk.Label(body, text=detail.get('description', component.get('note', '')),
            wraplength=560, justify='left')
        self.description.grid(row=1, column=0, sticky='ew', pady=(5, 8))
        self.images = detail.get('images', [])
        self.index = 0
        self.fit = True
        self.original = self.photo = None
        self.counter = tk.StringVar()
        self.caption = tk.StringVar()
        self.credit = tk.StringVar()
        controls = ttk.Frame(body)
        controls.grid(row=2, column=0, sticky='ew')
        self.previous = ttk.Button(controls, text='<', width=3, command=lambda: self.change(-1))
        self.previous.pack(side='left')
        ttk.Label(controls, textvariable=self.counter).pack(side='left', padx=7)
        self.next = ttk.Button(controls, text='>', width=3, command=lambda: self.change(1))
        self.next.pack(side='left')
        ttk.Button(controls, text='Fit', width=5, command=lambda: self.zoom(True)).pack(side='right')
        ttk.Button(controls, text='100%', width=5, command=lambda: self.zoom(False)).pack(side='right', padx=4)
        viewport = ttk.Frame(body)
        viewport.grid(row=3, column=0, sticky='nsew', pady=6)
        viewport.rowconfigure(0, weight=1)
        viewport.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(viewport, width=560, height=245, background='#202428', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(viewport, orient='vertical', command=self.canvas.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(viewport, orient='horizontal', command=self.canvas.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        self.canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.canvas.bind('<Configure>', lambda event: self.draw())
        self.canvas.bind('<ButtonPress-1>', lambda event: self.canvas.scan_mark(event.x, event.y))
        self.canvas.bind('<B1-Motion>', lambda event: self.canvas.scan_dragto(event.x, event.y, gain=1))
        self.caption_label = ttk.Label(body, textvariable=self.caption, wraplength=560, justify='left')
        self.caption_label.grid(row=4, column=0, sticky='ew')
        self.credit_label = ttk.Label(body, textvariable=self.credit, wraplength=560, justify='left')
        self.credit_label.grid(row=5, column=0, sticky='ew', pady=(3, 6))
        self.source_label = ttk.Label(body, text=detail.get('source_note', ''), wraplength=560, justify='left')
        self.source_label.grid(row=6, column=0, sticky='ew', pady=(0, 8))
        footer = ttk.Frame(body)
        footer.grid(row=7, column=0, sticky='ew')
        self.original_button = ttk.Button(footer, text='Original image', command=self.open_original)
        self.original_button.pack(side='left')
        ttk.Button(footer, text='Options', command=lambda: panel.safe(lambda: panel.open_options(component))).pack(side='left', padx=6)
        ttk.Button(footer, text='Close', command=self.window.withdraw).pack(side='right')
        self.window.bind('<Configure>', self.reflow)
        self.load_image()

    def reflow(self, event):
        if event.widget is self.window:
            width = max(250, event.width - 30)
            for label in (self.description, self.caption_label, self.credit_label, self.source_label):
                label.configure(wraplength=width)

    def load_image(self):
        self.original = None
        self.photo = None
        self.error = ''
        if self.images:
            item = self.images[self.index]
            self.counter.set(f'{self.index + 1} / {len(self.images)}')
            self.caption.set(item['caption'])
            self.credit.set('Image: ' + item['credit'] + '. Drag to pan at 100%.')
            try:
                path = (self.media_root / item['file']).resolve()
                if not path.is_relative_to(self.media_root.resolve()):
                    raise ValueError('Preview image path is outside the media folder.')
                self.original = tk.PhotoImage(master=self.window, file=str(path))
            except (OSError, ValueError, tk.TclError):
                self.error = 'Local image unavailable. Use Original image to view the author source.'
            self.original_button.state(['!disabled'])
        else:
            self.counter.set('No gameplay image')
            self.caption.set(self.detail.get('image_note', 'No verified author image is available.'))
            self.credit.set('')
            self.original_button.state(['disabled'])
        for button in (self.previous, self.next):
            button.state(['!disabled'] if len(self.images) > 1 else ['disabled'])
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.draw()

    def draw(self):
        self.canvas.delete('all')
        if self.original is None:
            self.canvas.create_text(16, 16, anchor='nw', text=self.error or 'Description above; documentation at the source links.',
                width=max(200, self.canvas.winfo_width() - 32), fill='white')
            self.canvas.configure(scrollregion=(0, 0, 1, 1))
            return
        width, height = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        factor = max(1, math.ceil(max(self.original.width() / width, self.original.height() / height))) if self.fit else 1
        self.photo = self.original.subsample(factor, factor) if factor > 1 else self.original
        x = max(0, (width - self.photo.width()) // 2) if self.fit else 0
        y = max(0, (height - self.photo.height()) // 2) if self.fit else 0
        self.canvas.create_image(x, y, anchor='nw', image=self.photo)
        self.canvas.configure(scrollregion=(0, 0, max(width, self.photo.width()), max(height, self.photo.height())))

    def change(self, delta):
        if self.images:
            self.index = (self.index + delta) % len(self.images)
            self.load_image()

    def zoom(self, fit):
        self.fit = fit
        self.draw()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def open_original(self):
        if self.images:
            self.panel.safe(lambda: webbrowser.open(self.images[self.index]['url']))

    def show(self, pointer=None):
        size = (self.window.winfo_width(), self.window.winfo_height())
        if min(size) <= 1:
            size = (610, 570)
        show_near_pointer(self.window, pointer, size)
