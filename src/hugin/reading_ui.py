"""Optional movable section view; presentation coordinates and text stay in RAM."""
import sys
import tkinter as tk
from tkinter import ttk

from .branding import CARD,FIELD,TEXT,MUTED,BLUE,BORDER,MAX_SURFACE_SIDE,panel_surface
from .ui_controls import SoftButton


def panel_geometry(work,scale,position=None):
    left,top,right,bottom=work
    width=max(1,min(round(720*scale),MAX_SURFACE_SIDE,right-left-24))
    height=max(1,min(round(232*scale),MAX_SURFACE_SIDE,bottom-top-24))
    x,y=position if position is not None else (left+(right-left-width)//2,bottom-height-12)
    return max(left,min(x,right-width)),max(top,min(y,bottom-height)),width,height


class ReadingPanel:
    def __init__(self,root,scale,on_action,on_hide,on_unavailable):
        self.window=tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(background=CARD)
        self.window.title('Hugin · Mitlesen')
        self.window.protocol('WM_DELETE_WINDOW',on_hide)
        self._view=None;self._job='';self._shown=False;self._placement=None;self._word=None
        self._position=None;self._geometry=None;self._drag=None;self._layout_size=None
        self.on_action=on_action;self.on_unavailable=on_unavailable;self.scale=scale
        self.scene=tk.Canvas(self.window,background=CARD,highlightthickness=0,borderwidth=0)
        self.scene.pack(fill='both',expand=True)
        self._surface=self.scene.create_image(0,0,anchor='nw')
        self._heading=self.scene.create_text(0,0,anchor='w',fill=BLUE)
        self._hint=self.scene.create_text(0,0,anchor='e',text='Ziehen zum Verschieben',fill=MUTED)
        self.scene.bind('<ButtonPress-1>',self._drag_begin)
        self.scene.bind('<B1-Motion>',self._drag_move)
        self.scene.bind('<ButtonRelease-1>',self._drag_end)
        self.scene.bind('<Motion>',self._pointer)
        self.pause=SoftButton(self.scene,text='Pause',scale=scale,wake=self._wake,
            command=lambda:self._action('read_pause'))
        self.stop=SoftButton(self.scene,text='Stopp',scale=scale,wake=self._wake,
            command=lambda:self._action('read_stop'))
        self.hide=SoftButton(self.scene,text='Ausblenden',scale=scale,wake=self._wake,command=on_hide)
        self.buttons=(self.pause,self.stop,self.hide)
        self.text=tk.Text(self.scene,wrap='word',background=FIELD,foreground=TEXT,
            font=('Segoe UI',12),borderwidth=0,highlightthickness=0,
            padx=0,pady=0,state='disabled',takefocus=False)
        self.scroll=ttk.Scrollbar(self.scene,command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)
        self.text.tag_configure('reading_word',background=BLUE,foreground=FIELD)
        self._controls={widget:self.scene.create_window(0,0,window=widget,anchor='nw')
                        for widget in (*self.buttons,self.text,self.scroll)}

    def _wake(self):
        for button in self.buttons:button.step(immediate=True)

    def _action(self,kind):
        if self._job:self.on_action(kind,self._job)

    def _set_text(self,text):
        self._clear_word()
        self.text.configure(state='normal')
        self.text.delete('1.0','end');self.text.insert('1.0',text)
        self.text.configure(state='disabled');self.text.yview_moveto(0)

    def _clear_word(self):
        self.text.tag_remove('reading_word','1.0','end');self._word=None

    def _mark_word(self,view):
        span=view.reading_word
        if (view.reading_marking!='aligned' or not isinstance(span,tuple) or len(span)!=2
                or any(type(value) is not int for value in span)
                or not 0<=span[0]<span[1]<=len(view.reading_text)):
            self._clear_word();return span is None
        key=(view.reading_job,view.reading_index,view.reading_text,span)
        if self._word!=key:
            self._clear_word()
            def index(offset):
                prefix=view.reading_text[:offset]
                # Windows Tk 8.6 columns count UTF-16 units, unlike Python's
                # code-point offsets. Ask this Tcl runtime at each new mark.
                column=self.text.tk.call('string','length',prefix.rsplit('\n',1)[-1])
                return f'{prefix.count(chr(10))+1}.{column}'
            start,end=map(index,span)
            self.text.tag_add('reading_word',start,end)
            self.text.see(start)
            self._word=key
        return True

    def _fit(self,work):
        # Scale the owned surface, controls and pixel fonts together on smaller
        # monitors. Moving without resizing never allocates new images/regions.
        s=max(.5,min(self.scale,(work[2]-work[0]-24)/720,(work[3]-work[1]-24)/232))
        geometry=panel_geometry(work,s,self._position)
        _,_,width,height=geometry
        if self._layout_size!=(width,height,s):
            self._layout_size=(width,height,s)
            self._display_scale=s
            from PIL import Image,ImageDraw,ImageTk
            surface=Image.new('RGBA',(width,height),CARD)
            surface.alpha_composite(panel_surface(width,height,radius=round(18*s)))
            draw=ImageDraw.Draw(surface)
            draw.rounded_rectangle((round(18*s),round(50*s),width-round(18*s),height-round(58*s)),
                radius=round(12*s),fill=FIELD,outline=BORDER,width=max(1,round(s)))
            for dx in (21,26):
                for dy in (20,25,30):
                    draw.ellipse((round(dx*s),round(dy*s),round((dx+2)*s),round((dy+2)*s)),fill=MUTED)
            self._image=ImageTk.PhotoImage(surface,master=self.window)
            self.scene.itemconfigure(self._surface,image=self._image)
            self.scene.coords(self._heading,round(40*s),round(26*s))
            self.scene.itemconfigure(self._heading,font=('Segoe UI Semibold',-max(10,round(15*s))))
            self.scene.coords(self._hint,width-round(20*s),round(26*s))
            self.scene.itemconfigure(self._hint,font=('Segoe UI',-max(9,round(11*s))))
            def place(widget,x,y,w,h):
                self.scene.coords(self._controls[widget],round(x),round(y))
                self.scene.itemconfigure(self._controls[widget],width=max(1,round(w)),height=max(1,round(h)))
            self.text.configure(font=('Segoe UI',-max(10,round(16*s))))
            place(self.text,30*s,60*s,width-76*s,height-130*s)
            place(self.scroll,width-40*s,60*s,10*s,height-130*s)
            button_w,button_h,gap=round(112*s),round(32*s),round(8*s)
            start=(width-3*button_w-2*gap)//2
            for index,button in enumerate(self.buttons):
                x,y=start+index*(button_w+gap),height-round(44*s)
                button.scale=s
                button.configure(font=('Segoe UI Semibold',-max(10,round(13*s))))
                button.resize(button_w,button_h,backdrop=surface.crop((x,y,x+button_w,y+button_h)))
                place(button,x,y,button_w,button_h)
        self._geometry=geometry
        return geometry

    def _place(self):
        rect=None
        if self._position is not None and self._geometry is not None:
            x,y=self._position;_,_,w,h=self._geometry
            rect=(x,y,x+w,y+h)
        geometry=self._fit(self._placement.work_area(rect))
        self._placement.show(*geometry,radius=round(18*self._display_scale))
        self._position=geometry[:2]

    def _pointer(self,event):
        self.scene.configure(cursor='fleur' if event.y<50*getattr(self,'_display_scale',self.scale) else '')

    def _drag_begin(self,event):
        if self._shown and event.y<50*self._display_scale:
            self._drag=(event.x_root,event.y_root,*self._position)

    def _drag_move(self,event):
        if self._drag is None:return
        px,py,x,y=self._drag
        position=(x+event.x_root-px,y+event.y_root-py)
        try:self._placement.move(*position)
        except OSError:
            self.on_unavailable();return
        self._position=position

    def _drag_end(self,event):
        if self._drag is None:return
        self._drag_move(event)
        if self._drag is None:return
        self._drag=None
        try:self._place()
        except OSError:self.on_unavailable()

    def render(self,view,enabled):
        if not enabled or not view.reading_job or view.error:
            self.clear();return
        old=self._view
        self._view=view;self._job=view.reading_job
        if old is None or (old.reading_job,old.reading_index)!=(view.reading_job,view.reading_index):
            self._clear_word()
        title='Vorlesen pausiert' if view.reading_paused else 'Mitlesen'
        section=f'Abschnitt {view.reading_index} von {view.reading_total}' if view.reading_index else 'Wird vorbereitet'
        if old is None or old.reading_text!=view.reading_text:
            self._set_text(view.reading_text or 'Der erste Abschnitt wird vorbereitet …')
        valid=self._mark_word(view)
        if view.reading_marking=='preparing':title='Wörter werden zugeordnet'
        elif view.activity=='playing' and (view.reading_marking!='aligned' or not valid):
            title='Wortmarkierung nicht verfügbar'
        self.scene.itemconfigure(self._heading,text=f'{title}  ·  {section}')
        self.pause.configure(text='Fortsetzen' if view.reading_paused else 'Pause',
                             state='normal' if view.reading_index else 'disabled')
        if not self._shown:
            if sys.platform!='win32':return
            if self._placement is None:
                from .windows.reading_panel import PanelPlacement
                self._placement=PanelPlacement(self.window)
            self._place()
            self._shown=True

    def clear(self):
        if self._view is None and not self._shown:return
        self.window.withdraw();self._shown=False;self._job='';self._view=None;self._drag=None
        self._set_text('');self.scene.itemconfigure(self._heading,text='')

    def close(self):
        if self._placement is not None:self._placement.close()
