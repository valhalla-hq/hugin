"""Compact native Obsidian view; presentation never owns input or audio work."""
from __future__ import annotations

from dataclasses import dataclass,replace
import math
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

from .errors import HuginError
from .branding import (BACKGROUND,CARD,FIELD,BORDER,TEXT,MUTED,ACCENT,BLUE,
                       ACTIVITY_COLORS,MAX_SURFACE_SIDE,hugin_icon,raven_mark,backdrop,panel_surface,mix,ambient_light)
from .motion import Motion
from .bindings import DICTATION, READING


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
    active_action: str = ''
    audio_level: float = 0.0
    completion_id: int = 0
    completion_until: float = 0.0
    dictation_shortcut: str = DICTATION.hint()
    reading_shortcut: str = READING.hint()
    reading_job: str = ''
    reading_text: str = ''
    reading_index: int = 0
    reading_total: int = 0
    reading_paused: bool = False
    reading_word: tuple[int,int] | None = None
    reading_marking: str = ''
    panel_token: tuple[int,str] | None = None
    dictation_control: str = ''
    reading_control: str = ''


def tray_image(color=ACCENT):
    return hugin_icon(64,color)


def window_geometry(dpi_scale, screen_height):
    """Fit layout and font scaling into the same bounded raster workspace."""
    scale=max(1,min(dpi_scale,MAX_SURFACE_SIDE/780,screen_height*.90/520))
    available=screen_height/scale
    min_height=round(min(620,available*.90)*scale)
    height=max(min_height,round(min(780,available*.86)*scale))
    return scale,round(620*scale),height,round(460*scale),min_height


class HuginWindow:
    def __init__(self,on_action,*,with_tray=True):
        self.root=None;self._tray=None;self._alive=False;self._closed=False
        self.failure=None
        self._action_focus=None;self._panel_notice='';self._panel_intents={};self._panel_releasing=None
        self._stop_requested=threading.Event()
        self._animation_after=None;self._pump_after=None;self._layout_after=None
        self._frame_count=0;self._visible=False;self._last_size=None
        try:self._build(on_action,with_tray=with_tray)
        except BaseException as cause:
            try:self.stop()
            except BaseException:pass
            error=HuginError('interface_failed','window_start') if isinstance(cause,Exception) else cause
            error.owner=self
            raise error from None

    def _build(self,on_action,*,with_tray):
        self.on_action=on_action
        if sys.platform=='win32':
            import ctypes
            dpi=ctypes.WinDLL('user32').SetProcessDpiAwarenessContext
            dpi.argtypes=[ctypes.c_void_p];dpi.restype=ctypes.c_int
            dpi(ctypes.c_void_p(-4))
        self.root=tk.Tk(className='Hugin')
        self.root.withdraw()
        self.root.title('Hugin')
        dpi_scale=max(1,self.root.winfo_fpixels('1i')/96)
        self.scale,width,height,min_width,min_height=window_geometry(dpi_scale,self.root.winfo_screenheight())
        if self.scale < dpi_scale:
            self.root.tk.call('tk','scaling',96*self.scale/72)
        self.root.maxsize(MAX_SURFACE_SIDE,MAX_SURFACE_SIDE)
        self.root.geometry(f'{width}x{height}')
        self.root.minsize(min_width,min_height)
        self.root.configure(background=BACKGROUND)
        self.root.protocol('WM_DELETE_WINDOW',self.hide)
        from PIL import ImageTk
        from .ui_controls import SoftButton
        self._window_icon=ImageTk.PhotoImage(tray_image(),master=self.root)
        self.root.iconphoto(True,self._window_icon)
        self._updates=queue.Queue(maxsize=2);self._commands=queue.Queue(maxsize=32)
        self._view=None;self._alive=True
        self.motion=Motion()
        self.reduced_motion=tk.BooleanVar(master=self.root,value=False)
        self.reading_panel_enabled=True
        self.scene=tk.Canvas(self.root,background=BACKGROUND,highlightthickness=0,
                             borderwidth=0,takefocus=False)
        self.scene.pack(fill='both',expand=True)
        self._images={};self._items={};self._tile_images={}
        for name in ('background','dictation','reading','voices','result','header_logo','ambient','hero'):
            self._items[name]=self.scene.create_image(0,0,anchor='nw')
        self._labels={}
        for name in ('brand','mode','status','detail','dictation_title','dictation_key',
                     'reading_title','reading_key','voice','result_title','empty','escape','error'):
            self._labels[name]=self.scene.create_text(0,0,fill=TEXT,anchor='nw',
                                                     font=('Segoe UI',10))
        # Every animated item is allocated once and subsequently moved/recolored.
        self._bars=[self.scene.create_line(0,0,0,0,fill=BLUE,capstyle='round') for _ in range(29)]
        self._particles=[self.scene.create_oval(0,0,0,0,fill=BLUE,outline='') for _ in range(42)]
        self._rings=[self.scene.create_oval(0,0,0,0,outline=BLUE) for _ in range(3)]
        self._check=self.scene.create_line(0,0,0,0,fill=TEXT,capstyle='round',joinstyle='round')
        self._glyphs=[]
        # Simple native canvas line icons, independent of font glyph coverage.
        for _ in range(9):
            self._glyphs.append(self.scene.create_line(0,0,0,0,fill=TEXT,capstyle='round',joinstyle='round'))
        self._mic_head=self.scene.create_oval(0,0,0,0,outline=TEXT)
        self._speaker=self.scene.create_polygon(0,0,0,0,fill=TEXT,outline='')

        self.voice_buttons={}
        for voice,title in (('freya','Freya'),('tyr','Tyr')):
            self.voice_buttons[voice]=SoftButton(self.scene,text=title,
                command=lambda voice=voice:self.on_action('voice',voice),
                scale=self.scale,wake=self._wake_animation)
        self.copy=SoftButton(self.scene,text='Kopieren',command=lambda:self.on_action('copy',None),
                            scale=self.scale,wake=self._wake_animation)
        self.clear=SoftButton(self.scene,text='Löschen',command=lambda:self.on_action('clear',None),
                             scale=self.scale,wake=self._wake_animation)
        self.diagnose=SoftButton(self.scene,text='Diagnose kopieren',
                command=lambda:self.on_action('diagnose',None),
                scale=self.scale,wake=self._wake_animation)
        self._buttons=[*self.voice_buttons.values(),self.copy,self.clear,self.diagnose]
        self.read_pause=SoftButton(self.scene,text='Pause',scale=self.scale,wake=self._wake_animation,
            command=lambda:self._reading_action('read_pause'))
        self.dictation_button=SoftButton(self.scene,text='Diktat starten',scale=self.scale,
            wake=self._wake_animation,accent=True,command=lambda:self._panel_action('dictation'))
        self.read_action=SoftButton(self.scene,text='Vorlesen starten',scale=self.scale,
            wake=self._wake_animation,accent=True,command=lambda:self._panel_action('read'))
        # Latch before Tk's ButtonDown; clear after ButtonUp has invoked. A
        # hotkey/view update between press and release cannot change the intent.
        release_tag='HuginPanelRelease'
        self.root.bind_class(release_tag,'<ButtonRelease-1>',lambda _:self._panel_release_done())
        for kind,button in (('dictation',self.dictation_button),('read',self.read_action)):
            button.bind('<ButtonPress-1>',lambda _,kind=kind:self._panel_pressed(kind),add='+')
            button.bind('<ButtonRelease-1>',lambda _,kind=kind:self._panel_released(kind),add='+')
            tags=button.bindtags()
            button.bindtags((*tags[:2],release_tag,*tags[2:]))
        self.reading_toggle=SoftButton(self.scene,text='Mitleseleiste ausblenden',
            command=lambda:self._reading_visibility(not self.reading_panel_enabled),
            scale=self.scale,wake=self._wake_animation)
        self._buttons.extend((self.dictation_button,self.read_pause,self.read_action,self.reading_toggle))
        if sys.platform=='win32':
            from .windows.action_focus import ActionFocus
            self._action_focus=ActionFocus()
            for button in (self.dictation_button,self.read_action):self._action_focus.attach(button)
        self.motion_toggle=tk.Checkbutton(self.scene,text='Bewegung reduzieren',
            variable=self.reduced_motion,command=self._motion_changed,
            background=BACKGROUND,foreground=MUTED,activebackground=BACKGROUND,
            activeforeground=TEXT,selectcolor=FIELD,relief='flat',borderwidth=0,
            highlightthickness=1,highlightbackground=BACKGROUND,highlightcolor=BLUE,
            font=('Segoe UI',9),takefocus=True,padx=0,pady=0)
        self.text=tk.Text(self.scene,wrap='word',font=('Segoe UI',11),background=FIELD,
            foreground=TEXT,insertbackground=TEXT,selectbackground='#354579',
            selectforeground=TEXT,inactiveselectbackground='#29344e',relief='flat',
            borderwidth=0,highlightthickness=1,highlightbackground=BORDER,
            highlightcolor=BLUE,padx=round(13*self.scale),pady=round(10*self.scale),
            state='disabled',takefocus=True)
        style=ttk.Style(self.root);style.theme_use('clam')
        style.configure('Vertical.TScrollbar',background='#35425f',troughcolor=FIELD,
            bordercolor=FIELD,arrowcolor=MUTED,lightcolor=FIELD,darkcolor=FIELD,
            width=round(10*self.scale))
        style.map('Vertical.TScrollbar',background=[('active',ACCENT),('pressed',BLUE)])
        self.scrollbar=ttk.Scrollbar(self.scene,command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.empty=tk.Label(self.scene,text='Hier erscheint dein letztes Diktat.',
            background=FIELD,foreground=MUTED,font=('Segoe UI',10),anchor='w',
            borderwidth=0,padx=0,pady=0)
        self._windows={}
        for name,widget in [('text',self.text),('scroll',self.scrollbar),
                ('freya',self.voice_buttons['freya']),('tyr',self.voice_buttons['tyr']),
                ('copy',self.copy),('clear',self.clear),('diagnose',self.diagnose),
                ('dictation_button',self.dictation_button),('read_pause',self.read_pause),
                ('read_action',self.read_action),('reading_toggle',self.reading_toggle),
                ('motion',self.motion_toggle),('empty_hint',self.empty)]:
            self._windows[name]=self.scene.create_window(0,0,window=widget,anchor='nw')
        self.scene.bind('<Configure>',self._queue_layout)
        self.root.bind('<Map>',self._mapped,add='+')
        self.root.bind('<Unmap>',self._unmapped,add='+')
        if with_tray:
            import pystray
            from .windows.tray import TrayOwner
            self._tray=TrayOwner(pystray.Icon('hugin',tray_image(),'Hugin · wird vorbereitet',
                menu=pystray.Menu(
                    pystray.MenuItem('Öffnen',lambda:self._command('show'),default=True),
                    pystray.MenuItem('Diagnose kopieren',lambda:self.on_action('diagnose',None)),
                    pystray.MenuItem('Beenden',lambda:self.on_action('quit',None)))))
            self._tray.start()
        from .reading_ui import ReadingPanel
        self.reading_panel=ReadingPanel(self.root,self.scale,self.on_action,self._hide_reading,
                                        self._reading_unavailable)
        self.render(View())
        if self._action_focus is not None:self._action_focus.protect_window(self.root)
        self._pump_after=self.root.after(25,self._pump)

    def _native_caption(self):
        if sys.platform!='win32':return
        # Cosmetic attributes of our own window only. Unsupported versions keep
        # their native caption and controls, including resizing and accessibility.
        import ctypes
        try:
            self.root.update_idletasks()
            user=ctypes.WinDLL('user32')
            user.GetParent.argtypes=[ctypes.c_void_p];user.GetParent.restype=ctypes.c_void_p
            hwnd=user.GetParent(self.root.winfo_id())
            set_attr=ctypes.WinDLL('dwmapi').DwmSetWindowAttribute
            set_attr.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
            set_attr.restype=ctypes.c_long
            for attribute,value in ((20,1),(35,0x120b08),(36,0xf7eee9)):
                item=ctypes.c_uint(value)
                set_attr(hwnd,attribute,ctypes.byref(item),ctypes.sizeof(item))
        except (OSError,AttributeError):pass

    def _queue_layout(self,event=None):
        if self._alive and self._layout_after is None:
            self._layout_after=self.root.after_idle(self._layout)

    def _image(self,name,image,x,y):
        from PIL import ImageTk
        self._images[name]=ImageTk.PhotoImage(image,master=self.root)
        self.scene.itemconfigure(self._items[name],image=self._images[name])
        self.scene.coords(self._items[name],round(x),round(y))

    def _label(self,name,text,x,y,*,size=10,color=TEXT,anchor='nw',width=0,bold=False):
        item=self._labels[name]
        self.scene.coords(item,x*self.scale,y*self.scale)
        self.scene.itemconfigure(item,text=text,fill=color,anchor=anchor,
            width=round(width*self.scale),font=('Segoe UI Semibold' if bold else 'Segoe UI',size))

    def _place(self,name,x,y,w,h):
        self.scene.coords(self._windows[name],round(x*self.scale),round(y*self.scale))
        self.scene.itemconfigure(self._windows[name],width=max(1,round(w*self.scale)),
                                 height=max(1,round(h*self.scale)))

    def _layout(self):
        from PIL import ImageTk
        self._layout_after=None
        if not self._alive or not self.scene.winfo_exists():return
        pixel_w,pixel_h=self.scene.winfo_width(),self.scene.winfo_height()
        if pixel_w<10 or pixel_h<10:return
        size=(pixel_w,pixel_h,bool(self._view and self._view.error),self._view.active_action,
              self._view.reading_control)
        if size==self._last_size:return
        self._last_size=size
        s=self.scale;w=pixel_w/s;h=pixel_h/s
        pad=24 if w>=550 else 18
        inner=w-pad*2;gap=12
        compact=h<640
        header=36 if compact else 52
        error_h=52 if self._view and self._view.error else 0
        hero_h=max(48,min(170,h-420-error_h)) if compact else min(230,h*.29,h-465-error_h)
        title_y=header+hero_h-36
        self._center=(w/2,(title_y-32))
        self._logo_center=(w/2,header+(hero_h-72)/2)
        logo_size=max(40,min(146,hero_h-76))
        tiles_y=header+hero_h+8
        tile_h=140 if compact else 146
        section_gap=8 if compact else 12
        voice_y=tiles_y+tile_h+section_gap;voice_h=42 if compact else 47
        result_y=voice_y+voice_h+section_gap
        footer_h=72
        result_h=max(134,h-result_y-footer_h-error_h)
        background=backdrop(pixel_w,pixel_h)
        self._image('background',background,0,0)
        self._image('header_logo',raven_mark(round(29*s)),pad*s,14*s)
        light_w,light_h=round(logo_size*1.8*s),round(logo_size*1.1*s)
        self._ambient_frames=[ImageTk.PhotoImage(ambient_light(light_w,light_h,index/9),
                              master=self.root) for index in range(10)]
        self.scene.coords(self._items['ambient'],(w*s-light_w)/2,
                          self._logo_center[1]*s-light_h/2)
        self.scene.itemconfigure(self._items['ambient'],image=self._ambient_frames[3],
                                 state='hidden' if hero_h<126 else 'normal')
        self._image('hero',raven_mark(round(logo_size*s)),
                    (w-logo_size)*s/2,(self._logo_center[1]-logo_size/2)*s)
        self.scene.itemconfigure(self._items['hero'],state='hidden' if hero_h<126 else 'normal')
        surfaces={}
        self._tile_images={}
        for name,x,y,ww,hh in (
                ('dictation',pad,tiles_y,(inner-gap)/2,tile_h),
                ('reading',pad+(inner+gap)/2,tiles_y,(inner-gap)/2,tile_h),
                ('voices',pad,voice_y,inner,voice_h),
                ('result',pad,result_y,inner,result_h)):
            px,py,pw,ph=round(x*s),round(y*s),round(ww*s),round(hh*s)
            surface=background.crop((px,py,px+pw,py+ph))
            surface.alpha_composite(panel_surface(pw,ph,radius=round(16*s)))
            surfaces[name]=(surface,px,py)
            self._image(name,surface,px,py)
            if name in ('dictation','reading'):
                active=background.crop((px,py,px+pw,py+ph))
                active.alpha_composite(panel_surface(pw,ph,radius=round(16*s),highlighted=True))
                self._tile_images[name]=(self._images[name],ImageTk.PhotoImage(active,master=self.root))
                if self._view.active_action==name and not self._view.error:
                    surfaces[name]=(active,px,py)
        self._render_action_tiles()

        def place_button(name,button,x,y,ww,hh,parent=None,selected=False):
            self._place(name,x,y,ww,hh)
            surface,bx,by=surfaces[parent] if parent else (background,0,0)
            px,py,pw,ph=round(x*s)-bx,round(y*s)-by,round(ww*s),round(hh*s)
            button.resize(pw,ph,selected=selected,
                          backdrop=surface.crop((px,py,px+pw,py+ph)))
        self._label('brand','Hugin',pad+40,15,size=17,bold=True)
        self._label('mode',self._view.mode if self._view else 'Lokal',w-pad,23,
                    color=MUTED,anchor='e',size=9)
        self._status_y=title_y;self._detail_y=title_y+27
        self._label('status','',w/2,title_y,size=18 if compact else 22,bold=True,
                    anchor='center',width=inner)
        self._label('detail','',w/2,title_y+27,size=9,color=MUTED,anchor='center',width=inner)
        tile_w=(inner-gap)/2
        for prefix,x,title,key in (
                ('dictation',pad,'Diktieren',self._view.dictation_shortcut),
                ('reading',pad+tile_w+gap,'Vorlesen',self._view.reading_shortcut)):
            self._label(prefix+'_title',title,x+51,tiles_y+9,size=12,bold=True)
            self._label(prefix+'_key',key,x+51,tiles_y+31,size=8,
                        color=MUTED,width=tile_w-62)
        # Microphone and speaker icons: drawn once per layout, not animated.
        mx=(pad+26)*s;my=(tiles_y+21)*s
        self.scene.coords(self._mic_head,mx-4*s,my-9*s,mx+4*s,my+4*s)
        self.scene.itemconfigure(self._mic_head,width=2*s)
        glyph_coords=[
            (mx-8*s,my,mx-8*s,my+8*s,mx,my+13*s,mx+8*s,my+8*s,mx+8*s,my),
            (mx,my+13*s,mx,my+19*s),(mx-5*s,my+19*s,mx+5*s,my+19*s)]
        sx=(pad+tile_w+gap+24)*s;sy=(tiles_y+27)*s
        self.scene.coords(self._speaker,sx-9*s,sy-5*s,sx-3*s,sy-5*s,sx+4*s,sy-11*s,
                          sx+4*s,sy+11*s,sx-3*s,sy+5*s,sx-9*s,sy+5*s)
        glyph_coords.extend(((sx+8*s,sy-6*s,sx+11*s,sy,sx+8*s,sy+6*s),
                            (sx+12*s,sy-11*s,sx+17*s,sy,sx+12*s,sy+11*s)))
        for item,coords in zip(self._glyphs,glyph_coords):
            self.scene.coords(item,*coords);self.scene.itemconfigure(item,width=2*s)
        self._label('voice','Stimme',pad+17,voice_y+15,color=MUTED,size=10)
        voice_w=(inner-115)/2
        for index,(voice,button) in enumerate(self.voice_buttons.items()):
            place_button(voice,button,pad+92+index*voice_w,voice_y+7,voice_w-7,33,
                         parent='voices',selected=self._view.voice==voice)
        self._label('result_title','Letztes Diktat',pad+17,result_y+13,size=11,bold=True)
        text_h=max(42,result_h-92)
        self._place('text',pad+16,result_y+39,inner-42,text_h)
        self._place('scroll',w-pad-25,result_y+39,10,text_h)
        self._place('empty_hint',pad+30,result_y+51,inner-72,23)
        self._label('empty','',pad+29,result_y+52,color=MUTED,size=10,width=inner-70)
        button_y=result_y+result_h-43
        for name,x,button in (('copy',w-pad-213,self.copy),('clear',w-pad-108,self.clear)):
            place_button(name,button,x,button_y,92,31,parent='result')
        footer_y=result_y+result_h+10
        self._label('error',self._view.error,pad,footer_y,size=9,
                    color='#edba92',width=inner)
        footer_y+=error_h
        self._label('escape','Esc · Abbrechen',pad,footer_y+3,size=8,color=MUTED)
        self._place('motion',pad,footer_y+34,180,23)
        toggle_w=min(230,tile_w-20)
        place_button('reading_toggle',self.reading_toggle,pad+tile_w+gap+(tile_w-toggle_w)/2,
                     tiles_y+tile_h-38,toggle_w,28,parent='reading')
        control_w=(tile_w-26)/2
        place_button('dictation_button',self.dictation_button,pad+10,tiles_y+65,tile_w-20,30,parent='dictation')
        rx=pad+tile_w+gap
        place_button('read_pause',self.read_pause,rx+10,tiles_y+65,control_w,30,parent='reading')
        active=self._view.reading_control=='stop'
        place_button('read_action',self.read_action,rx+16+control_w if active else rx+10,
                     tiles_y+65,control_w if active else tile_w-20,30,parent='reading')
        self._reading_controls()
        place_button('diagnose',self.diagnose,w-pad-138,footer_y-1,138,30)
        self._paint(time.monotonic(),animate=not self.reduced_motion.get())
        self._wake_animation()

    def _mapped(self,event):
        if event.widget is self.root:
            self._visible=True
            self._paint(time.monotonic(),animate=not self.reduced_motion.get())
            self._wake_animation()

    def _unmapped(self,event):
        if event.widget is self.root:
            self._visible=False
            self._cancel_timer('_animation_after')

    def _cancel_timer(self,name):
        token=getattr(self,name,None)
        if token is not None and self.root is not None:
            try:self.root.after_cancel(token)
            except tk.TclError:pass
        setattr(self,name,None)

    def _motion_changed(self):
        self._cancel_timer('_animation_after')
        self._paint(time.monotonic(),animate=False)
        for button in self._buttons:button.step(immediate=True)
        self._wake_animation()

    def _wake_animation(self):
        if not self._alive or not getattr(self,'_visible',False) or self.failure:return
        if self.reduced_motion.get():
            for button in self._buttons:button.step(immediate=True)
            return
        if self._animation_after is None:
            self._animation_after=self.root.after(33,self._animate)

    def _animate(self):
        self._animation_after=None
        if not self._alive or not self._visible or self.failure or self.reduced_motion.get():return
        try:
            self._paint(time.monotonic(),animate=True)
            for button in self._buttons:button.step()
            self._frame_count+=1
            interval=66 if self.motion.phase(time.monotonic())=='idle' else 33
            self._animation_after=self.root.after(interval,self._animate)
        except BaseException as cause:self._fail(cause)

    def _paint(self,now,*,animate):
        if self._last_size is None or self._view is None:return
        reduced=self.reduced_motion.get()
        phase=self.motion.phase(now)
        self._painted_phase=phase
        # Fixed point for reduced motion, irrespective of render frequency.
        t=now if animate and not reduced else 0
        light=round(4.5+4.5*math.sin(t*(.8 if phase=='idle' else 1.8))) if t else 3
        self.scene.itemconfigure(self._items['ambient'],image=self._ambient_frames[light])
        s=self.scale;cx,cy=(value*s for value in self._center)
        for item in (*self._bars,*self._particles,*self._rings,self._check):
            self.scene.itemconfigure(item,state='hidden')
        if phase in ('recording','playing','idle'):
            level=(0 if reduced and phase=='recording' else
                   min(1.0,self.motion.level**.5*2.6) if phase=='recording'
                   else .25 if phase=='playing' else .025)
            for index,item in enumerate(self._bars):
                distance=abs(index-14)/14
                envelope=(1-distance**1.5)
                wave=(.6+.4*math.sin(index*.8+t*5)**2) if phase!='idle' else 1
                half=(1+level*16*envelope*wave)*s
                x=cx+(index-14)*5*s
                self.scene.coords(item,x,cy-half,x,cy+half)
                glow=.32 if phase=='idle' else .65
                if phase=='idle' and t:glow+=.08*math.sin(t*.8)
                self.scene.itemconfigure(item,state='normal',width=2.4*s,
                    fill=mix('#26334e',BLUE,glow*(.5+.5*envelope)))
        elif phase in ('processing','preparing'):
            for index,item in enumerate(self._particles):
                u=index/41
                x=cx+(u-.5)*170*s
                wave=math.sin(u*math.pi*3-t*2.4)*math.sin(u*math.pi)
                y=cy+wave*12*s
                radius=(1.1+.6*(.5+.5*math.sin(u*12-t*2)))*s
                self.scene.coords(item,x-radius,y-radius,x+radius,y+radius)
                self.scene.itemconfigure(item,state='normal',fill=mix('#283856',BLUE,
                    .35+.6*(.5+.5*math.sin(u*9-t*2))))
        elif phase=='complete':
            progress=self.motion.progress(now) if not reduced else .4
            for index,item in enumerate(self._rings):
                r=(18+index*10+progress*15)*s
                self.scene.coords(item,cx-r,cy+8*s-r*.22,cx+r,cy+8*s+r*.22)
                self.scene.itemconfigure(item,state='normal',width=1.2*s,
                    outline=mix('#192238',BLUE,max(.08,.7-index*.16-progress*.4)))
            self.scene.coords(self._check,cx-6*s,cy-3*s,cx-1*s,cy+2*s,cx+8*s,cy-8*s)
            self.scene.itemconfigure(self._check,state='normal',width=2.4*s)
        elif phase=='error':
            for item,x in zip(self._bars[:2],(-4,4)):
                self.scene.coords(item,cx+x*s,cy-6*s,cx-x*s,cy+6*s)
                self.scene.itemconfigure(item,state='normal',width=2*s,fill='#edba92')
        self._render_state_text(now)

    def _render_state_text(self,now):
        phase=self.motion.phase(now)
        status='Text eingefügt' if phase=='complete' else self._view.status
        detail=('Fertig. Du kannst direkt weiterarbeiten.' if phase=='complete' else self._view.detail)
        self.scene.itemconfigure(self._labels['status'],text=status)
        self.scene.itemconfigure(self._labels['detail'],text=self._panel_notice or detail)

    def _render_action_tiles(self):
        for name,frames in self._tile_images.items():
            selected=self._view.active_action==name and not self._view.error
            self.scene.itemconfigure(self._items[name],image=frames[int(selected)])

    def _command(self,command):
        if command=='stop':self._stop_requested.set();return
        try:self._commands.put_nowait(command)
        except queue.Full:pass

    def post(self,view):
        try:self._updates.put_nowait(view)
        except queue.Full:
            try:self._updates.get_nowait()
            except queue.Empty:pass
            try:self._updates.put_nowait(view)
            except queue.Full:pass

    def _fail(self,cause=None,*,notify=True):
        if self.failure is None:
            self._forget_views()
            self._cancel_timer('_animation_after')
            if cause is not None and not isinstance(cause,Exception):
                cause.__traceback__=cause.__context__=cause.__cause__=None
            self.failure=cause if cause is not None and not isinstance(cause,Exception) else HuginError('interface_failed','window_pump')
            self.failure.owner=self
            if notify:
                try:self.on_action('quit',None)
                except BaseException:self._stop_requested.set()

    def _pump(self):
        self._pump_after=None
        if not self._alive:return
        try:
            if self._stop_requested.is_set():
                try:self.stop()
                except BaseException as cause:
                    self._fail(cause,notify=False)
                    self.root.quit()
                return
            if self._tray and self._tray.error:self._fail()
            if self.failure is None:
                try:
                    while True:
                        command=self._commands.get_nowait()
                        if command=='show':self.show()
                except queue.Empty:pass
                try:
                    while True:self.render(self._updates.get_nowait())
                except queue.Empty:pass
        except BaseException as cause:self._fail(cause)
        finally:
            if self._alive:
                try:self._pump_after=self.root.after(25,self._pump)
                except BaseException as cause:
                    self._fail(cause)
                    try:self.root.quit()
                    except BaseException:pass

    def render(self,view):
        old=self._view;self._view=view
        if old is None or old.panel_token!=view.panel_token:self._panel_notice=''
        now=time.monotonic()
        self.motion.update(view,now)
        if old is not None and replace(view,audio_level=old.audio_level,
                reading_word=old.reading_word,reading_marking=old.reading_marking)==old:
            if (view.reading_word,view.reading_marking)!=(old.reading_word,old.reading_marking):
                self._render_reading_panel(view)
            # The UI has its own bounded paint clock. A 40Hz controller update
            # with only a meter/word update must not repaint all native controls.
            if self._visible and self.motion.phase(now)!=getattr(self,'_painted_phase',None):
                self._paint(now,animate=not self.reduced_motion.get())
            return
        if old is None or old.text!=view.text:
            self.text.configure(state='normal')
            self.text.delete('1.0','end')
            self.text.insert('1.0',view.text)
            self.text.configure(state='disabled')
        self.copy.configure(state='normal' if view.text else 'disabled')
        self.clear.configure(state='normal' if view.text else 'disabled')
        self.read_pause.configure(text='Fortsetzen' if view.reading_paused else 'Pause',
            state='normal' if view.reading_job and view.reading_index and not view.error else 'disabled')
        self.dictation_button.configure(text={'start':'Diktat starten','cancel':'Abbrechen',
            'finish':'Fertig & einfügen'}.get(view.dictation_control,'Bitte warten …'),
            state='normal' if view.dictation_control and view.panel_token is not None else 'disabled')
        self.read_action.configure(text='Stopp' if view.reading_control=='stop' else 'Vorlesen starten',
            state='normal' if view.reading_control and view.panel_token is not None else 'disabled')
        self._reading_controls()
        self._render_reading_panel(view)
        if old is None or old.voice!=view.voice:
            for name,button in self.voice_buttons.items():
                button._selected=view.voice==name
                if button._shape:
                    width,height,_=button._shape
                    button.resize(width,height,selected=view.voice==name)
        if (old is None or bool(old.error)!=bool(view.error) or old.active_action!=view.active_action
                or old.reading_control!=view.reading_control):
            self._last_size=None;self._queue_layout()
        self.scene.itemconfigure(self._labels['mode'],text=view.mode)
        self.scene.itemconfigure(self._labels['dictation_key'],text=view.dictation_shortcut)
        self.scene.itemconfigure(self._labels['reading_key'],text=view.reading_shortcut)
        self.scene.itemconfigure(self._labels['error'],text=view.error)
        self._render_action_tiles()
        self._render_state_text(time.monotonic())
        self.scene.itemconfigure(self._windows['empty_hint'],state='hidden' if view.text else 'normal')
        # The empty hint is never inserted into the RAM text widget.
        if old is None or old.text!=view.text:
            self.text.configure(inactiveselectbackground='#29344e')
        if self._tray and (old is None or old.status!=view.status or old.activity!=view.activity):
            self._tray.title='Hugin · '+view.status
            self._tray.icon=tray_image(ACTIVITY_COLORS.get(view.activity,ACCENT))
        now=time.monotonic()
        changed=(old is None or old.activity!=view.activity or old.status!=view.status
                 or old.detail!=view.detail or old.error!=view.error
                 or old.completion_id!=view.completion_id
                 or old.completion_until!=view.completion_until)
        if self._visible and (changed or self.reduced_motion.get()
                and (old.audio_level!=view.audio_level or self.motion.phase(now)!=getattr(self,'_painted_phase',None))):
            self._paint(now,animate=not self.reduced_motion.get())

    def show(self):
        if getattr(self,'motion',None) is not None:
            # A hidden/minimized canvas may still contain the old success glyph.
            # Refresh before mapping, including when motion is fully disabled.
            self._paint(time.monotonic(),animate=not self.reduced_motion.get())
        self.root.deiconify()
        self._native_caption()
        self.root.lift()
        self._visible=True
        self._wake_animation()

    def _reading_action(self,kind):
        if self._view and self._view.reading_job:self.on_action(kind,self._view.reading_job)

    def _panel_action(self,kind):
        view=self._view
        if view is None or view.panel_token is None:return
        # Keyboard/accessibility invokes use the current view independently;
        # they must not erase a mouse press that has not been released yet.
        if self._panel_releasing==kind and self._panel_intents.get(kind)!=view.panel_token:return
        control=view.dictation_control if kind=='dictation' else view.reading_control
        if not control:return
        # Stopping the microphone must never depend on a usable paste target.
        # The controller retains the transcript if the normal target proof fails.
        if kind=='read' and control=='start' and (
                self._action_focus is None or not self._action_focus.external_target()):
            self._panel_notice='Text im anderen Fenster markieren, dann hier starten.'
            self._render_state_text(time.monotonic())
            return
        self._panel_notice=''
        self._render_state_text(time.monotonic())
        self.on_action('panel_'+kind,view.panel_token)

    def _panel_pressed(self,kind):
        self._panel_intents[kind]=self._view.panel_token if self._view else None

    def _panel_released(self,kind):
        self._panel_releasing=kind

    def _panel_release_done(self):
        self._panel_intents.clear();self._panel_releasing=None

    def _reading_controls(self):
        active=bool(self._view and self._view.reading_control=='stop')
        self.scene.itemconfigure(self._windows['read_pause'],state='normal' if active else 'hidden')

    def _reading_visibility(self,enabled):
        self.reading_panel_enabled=enabled
        self.reading_toggle.configure(text='Mitleseleiste ausblenden' if enabled else 'Mitleseleiste einblenden')
        if self._view:self._render_reading_panel(self._view)

    def _render_reading_panel(self,view):
        try:self.reading_panel.render(view,self.reading_panel_enabled)
        except OSError:self._reading_unavailable()

    def _reading_unavailable(self):
        # Optional placement/drag failure leaves speech and main controls usable.
        self.reading_panel.clear()
        self.reading_panel_enabled=False
        self.reading_toggle.configure(text='Mitleseleiste nicht verfügbar',state='disabled')

    def _hide_reading(self):
        self._reading_visibility(False)

    def hide(self):
        self._visible=False
        self._cancel_timer('_animation_after')
        self.root.withdraw()

    def request_stop(self):
        self._command('stop')

    def _forget_views(self):
        panel=getattr(self,'reading_panel',None)
        if panel is not None:
            try:panel.clear()
            except Exception:pass
        self._view=None
        updates=getattr(self,'_updates',None)
        if updates is not None:
            try:
                while True:updates.get_nowait()
            except queue.Empty:pass
        text=getattr(self,'text',None)
        if text is not None:
            try:
                text.configure(state='normal');text.delete('1.0','end');text.configure(state='disabled')
            except Exception:pass

    def stop(self):
        if self._closed:return
        self._forget_views()
        for name in ('_animation_after','_layout_after','_pump_after'):
            self._cancel_timer(name)
        panel=getattr(self,'reading_panel',None)
        if panel is not None:panel.close()
        if self._action_focus is not None:self._action_focus.close()
        if self._tray:
            self._tray.close()
            if not self._tray.closed:raise HuginError('interface_failed','tray_cleanup')
        if self.root is not None:self.root.destroy()
        self._alive=False;self._closed=True

    def run(self):
        self.root.mainloop()
