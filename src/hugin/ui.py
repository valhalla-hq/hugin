"""One small native view; all callbacks enqueue work on the application owner."""
from __future__ import annotations

from dataclasses import dataclass
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk
from .errors import HuginError
from .branding import (BACKGROUND,CARD,FIELD,BORDER,TEXT,MUTED,ACCENT,BLUE,
                       ACTIVITY_COLORS,hugin_icon,header_backdrop)


@dataclass(frozen=True)
class View:
    status: str = 'Wird vorbereitet'
    detail: str = ''
    mode: str = 'Lokal'
    voice: str = 'freya'
    text: str = ''
    components: str = 'Sprachkomponenten werden geprüft.'
    error: str = ''
    activity: str = 'preparing'
    audio_level: float = 0.0
    completion_id: int = 0
    completion_until: float = 0.0
    dictation_shortcut: str = 'Vordere Taste oder Alt+Y · erneut: fertig'
    reading_shortcut: str = 'Text markieren · hintere Taste · erneut: Stopp'


def tray_image(color=ACCENT):
    return hugin_icon(64,color)


class _Card(tk.Canvas):
    """Small rounded background; the ordinary frame still owns its widgets."""
    def __init__(self,parent,scale,*,expand=False,compact=False):
        super().__init__(parent,background=BACKGROUND,highlightthickness=0,
                         borderwidth=0,height=round(120*scale),takefocus=False)
        self._pad=round((8 if compact else 14)*scale);self._radius=round(16*scale);self._expand=expand
        self.content=ttk.Frame(self,style='Card.TFrame')
        self._item=self.create_window(self._pad,self._pad,window=self.content,anchor='nw')
        self.bind('<Configure>',self._layout)
        self.content.bind('<Configure>',self._fit)
    def _fit(self,event=None):
        if not self._expand:
            height=self.content.winfo_reqheight()+2*self._pad
            if self.winfo_reqheight()!=height:self.configure(height=height)
    def _layout(self,event):
        w,h=event.width,event.height;r=min(self._radius,w/2,h/2)
        self.delete('surface')
        self.create_polygon((r,0,w-r,0,w,0,w,r,w,h-r,w,h,w-r,h,r,h,0,h,0,h-r,0,r,0,0),
            smooth=True,splinesteps=24,fill=CARD,outline=BORDER,tags='surface')
        self.tag_lower('surface')
        self.itemconfigure(self._item,width=max(1,w-2*self._pad))
        if self._expand:self.itemconfigure(self._item,height=max(1,h-2*self._pad))


class HuginWindow:
    def __init__(self, on_action, *, with_tray=True):
        self.root=None
        self._tray=None
        self._alive=False
        self._closed=False
        self.failure=None
        self._stop_requested=threading.Event()
        try: self._build(on_action,with_tray=with_tray)
        except BaseException as cause:
            # A failed constructor still owns its created root/tray parts.
            try: self.stop()
            except BaseException: pass
            error=HuginError('interface_failed','window_start') if isinstance(cause,Exception) else cause
            error.owner=self
            raise error from None

    def _build(self,on_action,*,with_tray):
        self.on_action = on_action
        if sys.platform == 'win32':
            import ctypes
            dpi = ctypes.WinDLL('user32').SetProcessDpiAwarenessContext
            dpi.argtypes = [ctypes.c_void_p]
            dpi.restype = ctypes.c_int
            dpi(ctypes.c_void_p(-4))
        self.root = tk.Tk(className='Hugin')
        self.root.withdraw()
        self.root.title('Hugin')
        scale = max(1,self.root.winfo_fpixels('1i')/96)
        compact=self.root.winfo_screenheight()/scale<650
        self.root.geometry(f'{round(520*scale)}x{min(round(640*scale),round(self.root.winfo_screenheight()*.9))}')
        self.root.minsize(round(460*scale),min(round(600*scale),round(self.root.winfo_screenheight()*.9)))
        from PIL import ImageTk
        self._window_icon = ImageTk.PhotoImage(tray_image(),master=self.root)
        self.root.iconphoto(True,self._window_icon)
        self.root.configure(background=BACKGROUND)
        self.root.protocol('WM_DELETE_WINDOW',self.hide)
        self._updates = queue.Queue(maxsize=2)
        self._commands = queue.Queue(maxsize=32)
        self._view = None
        self._tray = None
        self._alive = True
        self._closed = False
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TFrame',background=BACKGROUND)
        style.configure('Card.TFrame',background=CARD)
        style.configure('TLabel',background=CARD,foreground=TEXT,font=('Segoe UI',10))
        style.configure('Title.TLabel',background=BACKGROUND,font=('Segoe UI Semibold',24 if compact else 27),foreground=TEXT)
        style.configure('Status.TLabel',background=BACKGROUND,font=('Segoe UI Semibold',12),foreground=TEXT)
        style.configure('Header.TLabel',background=BACKGROUND,foreground=MUTED,font=('Segoe UI',9))
        style.configure('Small.TLabel',font=('Segoe UI',9),foreground=MUTED)
        style.configure('Section.TLabel',font=('Segoe UI Semibold',10),foreground=TEXT)
        style.configure('Error.TLabel',background=BACKGROUND,foreground='#ffabb7',font=('Segoe UI',9))
        style.configure('Footer.TLabel',background=BACKGROUND,foreground=MUTED,font=('Segoe UI',9))
        style.configure('TSeparator',background=BORDER)
        for name,bg in (('TButton','#202642'),('Accent.TButton',ACCENT),('Ghost.TButton',BACKGROUND)):
            style.configure(name,background=bg,foreground=TEXT,bordercolor=BORDER,
                lightcolor=bg,darkcolor=bg,padding=(round(13*scale),round((4 if compact else 7)*scale)),
                font=('Segoe UI Semibold',9),focusthickness=1,focuscolor='#b8afff')
            style.map(name,background=[('disabled','#1a2039'),('pressed','#5145b3'),('active','#34315c')],
                foreground=[('disabled','#8d97b9')],bordercolor=[('focus',ACCENT)])
        style.configure('TCombobox',fieldbackground=FIELD,background=CARD,foreground=TEXT,
            arrowcolor='#b9b1ff',bordercolor=BORDER,lightcolor=BORDER,darkcolor=BORDER,
            selectbackground=FIELD,selectforeground=TEXT,padding=round(7*scale),font=('Segoe UI',10))
        style.map('TCombobox',fieldbackground=[('disabled',CARD),('readonly',FIELD)],
            foreground=[('disabled',MUTED),('readonly',TEXT)],selectbackground=[('readonly',FIELD)],
            selectforeground=[('readonly',TEXT)],bordercolor=[('focus',ACCENT)],
            background=[('disabled',CARD),('pressed','#22294a'),('active','#22294a'),('readonly',CARD)],
            lightcolor=[('pressed',BORDER),('active',BORDER)],darkcolor=[('pressed',BORDER),('active',BORDER)])
        self.root.option_add('*TCombobox*Listbox.background',FIELD)
        self.root.option_add('*TCombobox*Listbox.foreground',TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground',ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground',TEXT)
        self.root.option_add('*TCombobox*Listbox.font',('Segoe UI',10))
        style.configure('Vertical.TScrollbar',background='#303758',troughcolor=FIELD,
            bordercolor=FIELD,arrowcolor=MUTED,lightcolor=FIELD,darkcolor=FIELD,width=round(9*scale))
        style.map('Vertical.TScrollbar',background=[('active',ACCENT),('pressed',BLUE)])
        body = ttk.Frame(self.root,padding=round((8 if compact else 16)*scale))
        body.pack(fill='both',expand=True)
        body.columnconfigure(0,weight=1)
        body.rowconfigure(2,weight=1)
        header_height=round((106 if compact else 112)*scale)
        status_y=round((74 if compact else 80)*scale)
        detail_y=round((88 if compact else 94)*scale)
        header=tk.Canvas(body,background=BACKGROUND,height=header_height,highlightthickness=0,takefocus=False)
        header.grid(row=0,column=0,sticky='ew',pady=(0,round((6 if compact else 10)*scale)))
        self._brand_icon=ImageTk.PhotoImage(hugin_icon(round(58*scale)),master=self.root)
        header.create_image(0,round(6*scale),image=self._brand_icon,anchor='nw')
        title=ttk.Frame(header)
        ttk.Label(title,text='Hugin',style='Title.TLabel').pack(anchor='w')
        ttk.Label(title,text='Diktieren · Vorlesen',style='Header.TLabel').pack(anchor='w')
        header.create_window(round(72*scale),0,window=title,anchor='nw')
        self.mode=tk.Label(header,background='#1a1c3d',foreground='#ccc6ff',font=('Segoe UI',9),
            padx=round(10*scale),pady=round(4*scale),borderwidth=0)
        mode_item=header.create_window(0,round(16*scale),window=self.mode,anchor='ne')
        self._activity_dot=tk.Canvas(header,width=round(9*scale),height=round(9*scale),
            background=BACKGROUND,highlightthickness=0,takefocus=False)
        self._activity_dot.create_oval(0,0,round(8*scale),round(8*scale),fill=ACCENT,outline='',tags='dot')
        header.create_window(0,status_y,window=self._activity_dot,anchor='w')
        self.status=ttk.Label(header,style='Status.TLabel')
        header.create_window(round(18*scale),status_y,window=self.status,anchor='w')
        self.detail=ttk.Label(header,style='Header.TLabel',wraplength=440)
        header.create_window(round(18*scale),detail_y,window=self.detail,anchor='nw')
        self.detail.bind('<Configure>',lambda _:header.configure(
            height=max(header_height,detail_y+self.detail.winfo_reqheight())))
        backdrop_item=header.create_image(0,0,anchor='nw')
        header.tag_lower(backdrop_item)
        def paint_header(event):
            self._header_image=ImageTk.PhotoImage(header_backdrop(event.width,event.height),master=self.root)
            header.itemconfigure(backdrop_item,image=self._header_image)
            header.coords(mode_item,event.width,round(16*scale))
            self.detail.configure(wraplength=max(100,event.width-round(20*scale)))
        header.bind('<Configure>',paint_header)
        controls=_Card(body,scale,compact=compact)
        controls.grid(row=1,column=0,sticky='ew',pady=(0,round((8 if compact else 12)*scale)))
        shortcuts = controls.content
        shortcuts.columnconfigure(1,weight=1)
        self._shortcut_labels = []
        for index,(name,text) in enumerate((('Diktieren','Vordere Taste oder Alt+Y · erneut: fertig'),
                ('Vorlesen','Text markieren · hintere Taste · erneut: Stopp'),
                ('Abbrechen','Escape während einer Aktion'))):
            ttk.Label(shortcuts,text=name).grid(row=index,column=0,sticky='nw',padx=(0,round(14*scale)),pady=round((2 if compact else 3)*scale))
            label = ttk.Label(shortcuts,text=text,style='Small.TLabel',wraplength=round(330*scale))
            label.grid(row=index,column=1,sticky='w',pady=round((2 if compact else 3)*scale))
            self._shortcut_labels.append(label)
        ttk.Separator(shortcuts).grid(row=3,column=0,columnspan=2,sticky='ew',pady=round((4 if compact else 10)*scale))
        voices = ttk.Frame(shortcuts,style='Card.TFrame')
        voices.grid(row=4,column=0,columnspan=2,sticky='ew')
        ttk.Label(voices,text='Stimme').pack(side='left',padx=(0,12))
        self.voice = ttk.Combobox(voices,state='readonly',values=('Freya – ruhig, weiblich','Tyr – männlich'))
        self.voice.pack(side='left',fill='x',expand=True)
        self.voice.bind('<<ComboboxSelected>>',lambda _:self.on_action('voice','freya' if self.voice.current()==0 else 'tyr'))
        result=_Card(body,scale,expand=True,compact=compact)
        result.grid(row=2,column=0,sticky='nsew',pady=(0,round((6 if compact else 10)*scale)))
        result.content.columnconfigure(0,weight=1);result.content.rowconfigure(1,weight=1)
        ttk.Label(result.content,text='Letztes Diktat',style='Section.TLabel').grid(row=0,column=0,sticky='w',pady=(0,round((5 if compact else 9)*scale)))
        text_frame = ttk.Frame(result.content,style='Card.TFrame')
        text_frame.grid(row=1,column=0,sticky='nsew')
        self.text = tk.Text(text_frame,height=5,wrap='word',font=('Segoe UI',10),
            background=FIELD,foreground=TEXT,insertbackground=TEXT,selectbackground='#5146a6',
            selectforeground=TEXT,inactiveselectbackground='#37335f',relief='flat',borderwidth=0,
            highlightthickness=1,highlightbackground=BORDER,highlightcolor=ACCENT,
            padx=round(10*scale),pady=round((6 if compact else 9)*scale),state='disabled')
        scrollbar = ttk.Scrollbar(text_frame,command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.pack(side='left',fill='both',expand=True)
        scrollbar.pack(side='right',fill='y')
        buttons = ttk.Frame(result.content,style='Card.TFrame')
        buttons.grid(row=2,column=0,sticky='ew',pady=(round((6 if compact else 10)*scale),0))
        self.copy = ttk.Button(buttons,text='Kopieren',style='Accent.TButton',command=lambda:self.on_action('copy',None))
        self.copy.pack(side='left')
        self.clear = ttk.Button(buttons,text='Löschen',command=lambda:self.on_action('clear',None))
        self.clear.pack(side='left',padx=(8,0))
        self.components = ttk.Label(body,style='Footer.TLabel',wraplength=440)
        self.components.grid(row=3,column=0,sticky='ew')
        self.error = ttk.Label(body,style='Error.TLabel',wraplength=440)
        self.error.grid(row=4,column=0,sticky='ew',pady=(round(3*scale),0))
        ttk.Button(body,text='Diagnose kopieren',style='Ghost.TButton',command=lambda:self.on_action('diagnose',None)).grid(row=5,column=0,sticky='w',pady=(round(3*scale),0))
        def reflow(event):
            width = max(100,event.width-round(40*scale))
            for label in (self.components,self.error): label.configure(wraplength=width)
            for label in self._shortcut_labels: label.configure(wraplength=max(100,width-round(120*scale)))
        body.bind('<Configure>',reflow)
        if with_tray:
            import pystray
            from .windows.tray import TrayOwner
            self._tray = TrayOwner(pystray.Icon('hugin',tray_image(),'Hugin · wird vorbereitet',menu=pystray.Menu(
                pystray.MenuItem('Öffnen',lambda:self._command('show'),default=True),
                pystray.MenuItem('Diagnose kopieren',lambda:self.on_action('diagnose',None)),
                pystray.MenuItem('Beenden',lambda:self.on_action('quit',None)))))
            self._tray.start()
        self.render(View())
        self.root.after(25,self._pump)

    def _command(self, command):
        if command == 'stop':
            self._stop_requested.set()
            return
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

    def _fail(self,cause=None,*,notify=True):
        if self.failure is None:
            self._forget_views()
            if cause is not None and not isinstance(cause,Exception):
                # Preserve the abort type/owner without retaining render(view)
                # frames or chained exceptions containing completed UI text.
                cause.__traceback__=cause.__context__=cause.__cause__=None
            self.failure=cause if cause is not None and not isinstance(cause,Exception) else HuginError('interface_failed','window_pump')
            self.failure.owner=self
            if notify:
                try: self.on_action('quit',None)
                except BaseException: self._stop_requested.set()

    def _pump(self):
        if not self._alive: return
        try:
            if self._stop_requested.is_set():
                try: self.stop()
                except BaseException as cause:
                    self._fail(cause,notify=False)
                    self.root.quit()  # Application finally retains/retries this owner.
                return
            if self._tray and self._tray.error: self._fail()
            if self.failure is None:
                try:
                    while True:
                        command=self._commands.get_nowait()
                        if command == 'show': self.show()
                except queue.Empty: pass
                try:
                    while True: self.render(self._updates.get_nowait())
                except queue.Empty: pass
        except BaseException as cause: self._fail(cause)
        finally:
            if self._alive:
                try: self.root.after(25,self._pump)
                except BaseException as cause:
                    self._fail(cause)
                    try: self.root.quit()
                    except BaseException: pass

    def render(self, view):
        old = self._view
        self._view = view
        self.status.configure(text=view.status)
        self.detail.configure(text=view.detail)
        self.mode.configure(text=view.mode)
        self.components.configure(text=view.components)
        self.error.configure(text=view.error)
        if view.error:self.error.grid()
        else:self.error.grid_remove()
        self.voice.current(0 if view.voice=='freya' else 1)
        self._shortcut_labels[0].configure(text=view.dictation_shortcut)
        self._shortcut_labels[1].configure(text=view.reading_shortcut)
        if old is None or old.text != view.text:
            self.text.configure(state='normal')
            self.text.delete('1.0','end')
            self.text.insert('1.0',view.text)
            self.text.configure(state='disabled')
        self.copy.configure(state='normal' if view.text else 'disabled')
        self.clear.configure(state='normal' if view.text else 'disabled')
        dot=getattr(self,'_activity_dot',None)
        if dot is not None:dot.itemconfigure('dot',fill=ACTIVITY_COLORS.get(view.activity,ACCENT))
        if self._tray and (old is None or old.status!=view.status or old.activity!=view.activity):
            self._tray.title='Hugin · '+view.status
            color = ACTIVITY_COLORS.get(view.activity,ACCENT)
            self._tray.icon=tray_image(color)

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def hide(self):
        self.root.withdraw()

    def request_stop(self):
        self._command('stop')

    def _forget_views(self):
        self._view=None
        updates=getattr(self,'_updates',None)
        if updates is not None:
            try:
                while True: updates.get_nowait()
            except queue.Empty: pass
        text=getattr(self,'text',None)
        if text is not None:
            try:
                text.configure(state='normal');text.delete('1.0','end');text.configure(state='disabled')
            except Exception:
                # Confirmed root destruction remains the native cleanup barrier.
                pass

    def stop(self):
        if self._closed: return
        self._forget_views()
        if self._tray:
            self._tray.close()
            if not self._tray.closed: raise HuginError('interface_failed','tray_cleanup')
            self._tray = None
        if self.root is not None: self.root.destroy()
        self._alive = False
        self._closed = True

    def run(self):
        self.root.mainloop()
