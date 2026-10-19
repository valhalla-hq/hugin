"""Keyboard-native controls with bounded pre-rendered surface transitions."""
from __future__ import annotations
import tkinter as tk
from PIL import ImageTk
from .branding import BACKGROUND, FIELD, TEXT, MUTED, panel_surface


class SoftButton(tk.Button):
    def __init__(self,parent,*,text,command,scale,wake,accent=False):
        super().__init__(parent,text=text,command=command,compound='center',
            background=FIELD,activebackground=FIELD,foreground=TEXT,
            activeforeground=TEXT,disabledforeground=MUTED,relief='flat',
            borderwidth=0,highlightthickness=1,highlightbackground=FIELD,
            highlightcolor='#b9c8ff',padx=0,pady=0,takefocus=True,cursor='hand2',
            font=('Segoe UI Semibold',10))
        self.scale=scale;self.wake=wake;self.accent=accent
        self._hover=False;self._pressed=False;self._selected=False
        self._frames=[];self._index=0;self._shape=None
        self.bind('<Enter>',lambda _:self._pointer(hover=True))
        self.bind('<Leave>',lambda _:self._pointer(hover=False,pressed=False))
        self.bind('<ButtonPress-1>',lambda _:self._pointer(pressed=True),add='+')
        self.bind('<ButtonRelease-1>',lambda _:self._pointer(pressed=False),add='+')
        self.bind('<Return>',lambda _:self.invoke())
        self.bind('<FocusIn>',lambda _:self.wake(),add='+')
        self.bind('<FocusOut>',lambda _:self.wake(),add='+')

    def _pointer(self,*,hover=None,pressed=None):
        if hover is not None:self._hover=hover
        if pressed is not None:self._pressed=pressed
        self.wake()

    def resize(self,width,height,*,selected=False):
        shape=(max(8,round(width)),max(8,round(height)),selected)
        if shape==self._shape:return
        self._shape=shape;self._selected=selected
        w,h,_=shape
        self._frames=[ImageTk.PhotoImage(panel_surface(w-2,h-2,
            radius=round(10*self.scale),accent=self.accent or selected,
            strength=index/12),master=self) for index in range(7)]
        self._index=0
        self.configure(image=self._frames[0],width=w-2,height=h-2)

    def step(self,*,immediate=False):
        if not self._frames:return False
        enabled=str(self.cget('state'))!='disabled'
        target=(2 if self._pressed else 6 if self._hover else 0) if enabled else 0
        before=self._index
        if immediate:self._index=target
        elif before!=target:self._index+=1 if target>before else -1
        if before!=self._index:self.configure(image=self._frames[self._index])
        return self._index!=target
