"""Optional section view. Holds no playback clock and no persistent text."""
import sys
import tkinter as tk
from tkinter import ttk

from .branding import CARD,FIELD,TEXT,MUTED,BLUE,BORDER,MAX_SURFACE_SIDE
from .ui_controls import SoftButton


def panel_geometry(work,scale):
    left,top,right,bottom=work
    width=max(1,min(round(720*scale),MAX_SURFACE_SIDE,right-left-24))
    height=max(1,min(round(232*scale),MAX_SURFACE_SIDE,bottom-top-24))
    return left+(right-left-width)//2,bottom-height-12,width,height


class ReadingPanel:
    def __init__(self,root,scale,on_action,on_hide):
        self.window=tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(background=BORDER)
        self.window.title('Hugin · Mitlesen')
        self.window.protocol('WM_DELETE_WINDOW',on_hide)
        self._view=None;self._job='';self._shown=False;self._placement=None
        self.on_action=on_action;self.on_hide=on_hide;self.scale=scale
        body=self.body=tk.Frame(self.window,background=CARD,padx=round(18*scale),pady=round(12*scale))
        body.pack(fill='both',expand=True,padx=1,pady=1)
        self.heading=tk.Label(body,text='',background=CARD,foreground=BLUE,
            font=('Segoe UI Semibold',11),anchor='w')
        self.heading.pack(fill='x')
        controls=self.controls=tk.Frame(body,background=CARD)
        controls.pack(side='bottom',fill='x',pady=(round(10*scale),0))
        self.pause=SoftButton(controls,text='Pause',scale=scale,wake=self._wake,
            command=lambda:self._action('read_pause'))
        self.stop=SoftButton(controls,text='Stopp',scale=scale,wake=self._wake,
            command=lambda:self._action('read_stop'))
        self.hide=SoftButton(controls,text='Ausblenden',scale=scale,wake=self._wake,command=on_hide)
        self.buttons=(self.pause,self.stop,self.hide)
        for button in self.buttons:
            button.resize(round(112*scale),round(32*scale))
            button.pack(side='left',padx=(0,round(8*scale)))
        text_area=self.text_area=tk.Frame(body,background=FIELD)
        text_area.pack(fill='both',expand=True,pady=(round(9*scale),0))
        self.text=tk.Text(text_area,wrap='word',background=FIELD,foreground=TEXT,
            font=('Segoe UI',12),borderwidth=0,highlightthickness=0,
            padx=round(10*scale),pady=round(7*scale),height=4,state='disabled',takefocus=False)
        scroll=ttk.Scrollbar(text_area,command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.text.pack(fill='both',expand=True)

    def _wake(self):
        for button in self.buttons:button.step(immediate=True)

    def _action(self,kind):
        if self._job:self.on_action(kind,self._job)

    def _set_text(self,text):
        self.text.configure(state='normal')
        self.text.delete('1.0','end');self.text.insert('1.0',text)
        self.text.configure(state='disabled');self.text.yview_moveto(0)

    def _fit(self,work):
        # A panel can appear on a smaller monitor than the main window. Scale
        # both layout and pixel fonts together, including the native controls.
        s=min(self.scale,(work[2]-work[0]-24)/720,(work[3]-work[1]-24)/232)
        s=max(.5,s)
        self.body.configure(padx=round(18*s),pady=round(12*s))
        self.heading.configure(font=('Segoe UI Semibold',-max(10,round(15*s))))
        self.text.configure(font=('Segoe UI',-max(10,round(16*s))),padx=round(10*s),pady=round(7*s))
        self.controls.pack_configure(pady=(round(10*s),0))
        self.text_area.pack_configure(pady=(round(9*s),0))
        for button in self.buttons:
            button.scale=s
            button.configure(font=('Segoe UI Semibold',-max(10,round(13*s))))
            button.resize(round(112*s),round(32*s))
            button.pack_configure(padx=(0,round(8*s)))
        return panel_geometry(work,s)

    def render(self,view,enabled):
        if not enabled or not view.reading_job or view.error:
            self.clear();return
        old=self._view
        self._view=view;self._job=view.reading_job
        title='Vorlesen pausiert' if view.reading_paused else 'Mitlesen'
        section=f'Abschnitt {view.reading_index} von {view.reading_total}' if view.reading_index else 'Wird vorbereitet'
        self.heading.configure(text=f'{title}  ·  {section}')
        if old is None or old.reading_text!=view.reading_text:
            self._set_text(view.reading_text or 'Der erste Abschnitt wird vorbereitet …')
        self.pause.configure(text='Fortsetzen' if view.reading_paused else 'Pause',
                             state='normal' if view.reading_index else 'disabled')
        if not self._shown:
            if sys.platform!='win32':return
            if self._placement is None:
                from .windows.reading_panel import PanelPlacement
                self._placement=PanelPlacement(self.window)
            self._placement.show(*self._fit(self._placement.work_area()))
            self._shown=True

    def clear(self):
        self.window.withdraw();self._shown=False;self._job='';self._view=None
        self._set_text('');self.heading.configure(text='')

