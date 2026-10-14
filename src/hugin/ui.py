"""One small native view; all callbacks enqueue work on the application owner."""
from __future__ import annotations

from dataclasses import dataclass
import queue
import tkinter as tk
from tkinter import ttk


@dataclass(frozen=True)
class View:
    status: str = 'Wird vorbereitet'
    detail: str = ''
    mode: str = 'Lokal'
    voice: str = 'freya'
    text: str = ''
    components: str = 'Sprachkomponenten werden geprüft.'
    error: str = ''


def tray_image(color='#b58b39'):
    from PIL import Image,ImageDraw,ImageFont
    image = Image.new('RGBA',(64,64),(0,0,0,0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4,4,60,60),radius=16,fill='#172b3a')
    draw.line((22,18,22,46),fill=color,width=5)
    draw.line((42,18,42,46),fill=color,width=5)
    draw.line((22,32,42,32),fill=color,width=5)
    return image


class HuginWindow:
    def __init__(self, on_action, *, with_tray=True):
        self.on_action = on_action
        self.root = tk.Tk(className='Hugin')
        self.root.withdraw()
        self.root.title('Hugin')
        self.root.geometry('500x550')
        self.root.minsize(430,480)
        self.root.configure(background='#f3f5f7')
        self.root.protocol('WM_DELETE_WINDOW',self.hide)
        self._updates = queue.Queue(maxsize=2)
        self._commands = queue.Queue(maxsize=32)
        self._view = None
        self._tray = None
        self._alive = True
        style = ttk.Style(self.root)
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        style.configure('TFrame',background='#f3f5f7')
        style.configure('TLabel',background='#f3f5f7',font=('Segoe UI',10))
        style.configure('Title.TLabel',font=('Segoe UI Semibold',26),foreground='#172b3a')
        style.configure('Status.TLabel',font=('Segoe UI Semibold',13),foreground='#21516a')
        style.configure('Small.TLabel',font=('Segoe UI',9),foreground='#586675')
        style.configure('Error.TLabel',foreground='#a53328')
        body = ttk.Frame(self.root,padding=20)
        body.pack(fill='both',expand=True)
        body.columnconfigure(0,weight=1)
        body.rowconfigure(8,weight=1)
        title = ttk.Frame(body)
        title.grid(row=0,column=0,sticky='ew',pady=(0,10))
        ttk.Label(title,text='Hugin',style='Title.TLabel').pack(side='left')
        self.mode = ttk.Label(title,style='Small.TLabel')
        self.mode.pack(side='right',anchor='center')
        self.status = ttk.Label(body,style='Status.TLabel')
        self.status.grid(row=1,column=0,sticky='w')
        self.detail = ttk.Label(body,style='Small.TLabel',wraplength=440)
        self.detail.grid(row=2,column=0,sticky='ew',pady=(2,16))
        shortcuts = ttk.Frame(body)
        shortcuts.grid(row=3,column=0,sticky='ew',pady=(0,14))
        shortcuts.columnconfigure(1,weight=1)
        for index,(name,text) in enumerate((('Diktieren','Vordere Taste oder Alt+Y · erneut: fertig'),
                ('Vorlesen','Text markieren · hintere Taste · erneut: Stopp'),
                ('Abbrechen','Escape während einer Aktion'))):
            ttk.Label(shortcuts,text=name).grid(row=index,column=0,sticky='nw',padx=(0,12),pady=3)
            ttk.Label(shortcuts,text=text,style='Small.TLabel',wraplength=330).grid(row=index,column=1,sticky='w',pady=3)
        voices = ttk.Frame(body)
        voices.grid(row=4,column=0,sticky='ew',pady=(0,16))
        ttk.Label(voices,text='Stimme').pack(side='left',padx=(0,12))
        self.voice = ttk.Combobox(voices,state='readonly',values=('Freya – ruhig, weiblich','Tyr – männlich'))
        self.voice.pack(side='left',fill='x',expand=True)
        self.voice.bind('<<ComboboxSelected>>',lambda _:self.on_action('voice','freya' if self.voice.current()==0 else 'tyr'))
        ttk.Label(body,text='Letztes Diktat').grid(row=5,column=0,sticky='w',pady=(0,5))
        text_frame = ttk.Frame(body)
        text_frame.grid(row=8,column=0,sticky='nsew')
        self.text = tk.Text(text_frame,height=5,wrap='word',font=('Segoe UI',10),
            background='white',foreground='#172b3a',relief='solid',borderwidth=1,state='disabled')
        scrollbar = ttk.Scrollbar(text_frame,command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.pack(side='left',fill='both',expand=True)
        scrollbar.pack(side='right',fill='y')
        buttons = ttk.Frame(body)
        buttons.grid(row=9,column=0,sticky='ew',pady=(8,14))
        self.copy = ttk.Button(buttons,text='Kopieren',command=lambda:self.on_action('copy',None))
        self.copy.pack(side='left')
        self.clear = ttk.Button(buttons,text='Löschen',command=lambda:self.on_action('clear',None))
        self.clear.pack(side='left',padx=(8,0))
        self.components = ttk.Label(body,style='Small.TLabel',wraplength=440)
        self.components.grid(row=10,column=0,sticky='ew')
        self.error = ttk.Label(body,style='Error.TLabel',wraplength=440)
        self.error.grid(row=11,column=0,sticky='ew',pady=(5,8))
        ttk.Button(body,text='Diagnose kopieren',command=lambda:self.on_action('diagnose',None)).grid(row=12,column=0,sticky='w')
        if with_tray:
            import pystray
            self._tray = pystray.Icon('hugin',tray_image(),'Hugin · wird vorbereitet',menu=pystray.Menu(
                pystray.MenuItem('Öffnen',lambda:self._command('show'),default=True),
                pystray.MenuItem('Diagnose kopieren',lambda:self.on_action('diagnose',None)),
                pystray.MenuItem('Beenden',lambda:self.on_action('quit',None))))
            self._tray.run_detached()
        self.render(View())
        self.root.after(25,self._pump)

    def _command(self, command):
        try:
            self._commands.put_nowait(command)
        except queue.Full:
            pass

    def post(self, view: View):
        try:
            self._updates.put_nowait(view)
        except queue.Full:
            try:
                self._updates.get_nowait()
            except queue.Empty:
                pass
            try:
                self._updates.put_nowait(view)
            except queue.Full:
                pass

    def _pump(self):
        if not self._alive:
            return
        try:
            while True:
                command = self._commands.get_nowait()
                if command == 'show':self.show()
                elif command == 'stop':self.stop()
        except queue.Empty:
            pass
        try:
            while True:
                view = self._updates.get_nowait()
                self.render(view)
        except queue.Empty:
            pass
        if self._alive:
            self.root.after(25,self._pump)

    def render(self, view):
        old = self._view
        self._view = view
        self.status.configure(text=view.status)
        self.detail.configure(text=view.detail)
        self.mode.configure(text=view.mode)
        self.components.configure(text=view.components)
        self.error.configure(text=view.error)
        self.voice.current(0 if view.voice=='freya' else 1)
        if old is None or old.text != view.text:
            self.text.configure(state='normal')
            self.text.delete('1.0','end')
            self.text.insert('1.0',view.text)
            self.text.configure(state='disabled')
        self.copy.configure(state='normal' if view.text else 'disabled')
        self.clear.configure(state='normal' if view.text else 'disabled')
        if self._tray and (old is None or old.status!=view.status):
            self._tray.title='Hugin · '+view.status

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def hide(self):
        self.root.withdraw()

    def request_stop(self):
        self._command('stop')

    def stop(self):
        self._alive = False
        if self._tray:
            self._tray.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
