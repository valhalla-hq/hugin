"""Keyboard-native controls with bounded pre-rendered surface transitions."""
from __future__ import annotations
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
from .branding import FIELD, TEXT, MUTED, panel_surface


class SoftButton(tk.Button):
    def __init__(self,parent,*,text,command,scale,wake,accent=False):
        super().__init__(parent,text=text,command=command,compound='center',
            background=FIELD,activebackground=FIELD,foreground=TEXT,
            activeforeground=TEXT,disabledforeground=MUTED,relief='flat',
            borderwidth=0,highlightthickness=0,
            padx=0,pady=0,takefocus=True,cursor='hand2',
            font=('Segoe UI Semibold',10))
        self.scale=scale;self.wake=wake;self.accent=accent
        self._hover=False;self._pressed=False;self._selected=False
        self._frames=[];self._focus_frames=[];self._index=0;self._shape=None
        self._focused=False;self._backdrop=None;self._shown_image=None
        self.bind('<Enter>',lambda _:self._pointer(hover=True))
        self.bind('<Leave>',lambda _:self._pointer(hover=False,pressed=False))
        self.bind('<ButtonPress-1>',lambda _:self._pointer(pressed=True),add='+')
        self.bind('<ButtonRelease-1>',lambda _:self._pointer(pressed=False),add='+')
        self.bind('<Return>',lambda _:self.invoke())
        self.bind('<FocusIn>',lambda _:self._focus_changed(True),add='+')
        self.bind('<FocusOut>',lambda _:self._focus_changed(False),add='+')

    def _focus_changed(self,focused):
        self._focused=focused
        self._show_frame()
        self.wake()

    def _show_frame(self):
        if not self._frames:return
        frames=self._focus_frames if self._focused else self._frames
        self._shown_image=frames[self._index]
        self.configure(image=self._shown_image)

    def _pointer(self,*,hover=None,pressed=None):
        if hover is not None:self._hover=hover
        if pressed is not None:self._pressed=pressed
        self.wake()

    def resize(self,width,height,*,selected=False,backdrop=None):
        shape=(max(8,round(width)),max(8,round(height)),selected)
        if shape==self._shape and backdrop is None:return
        self._shape=shape;self._selected=selected
        w,h,_=shape
        if backdrop is not None:self._backdrop=backdrop.convert('RGBA')
        if self._backdrop is None or self._backdrop.size!=(w,h):
            self._backdrop=Image.new('RGBA',(w,h),FIELD)
        self._frames=[];self._focus_frames=[]
        for index in range(7):
            frame=self._backdrop.copy()
            frame.alpha_composite(panel_surface(w,h,radius=round(10*self.scale),
                accent=self.accent or selected,strength=index/12))
            self._frames.append(ImageTk.PhotoImage(frame,master=self))
            ImageDraw.Draw(frame).rounded_rectangle((2,2,w-3,h-3),
                radius=max(1,round(10*self.scale)-2),outline='#c5e6ff',
                width=max(1,round(2*self.scale)))
            self._focus_frames.append(ImageTk.PhotoImage(frame,master=self))
        self._index=0
        self.configure(width=w,height=h)
        self._show_frame()

    def step(self,*,immediate=False):
        if not self._frames:return False
        enabled=str(self.cget('state'))!='disabled'
        target=(2 if self._pressed else 6 if self._hover else 0) if enabled else 0
        before=self._index
        if immediate:self._index=target
        elif before!=target:self._index+=1 if target>before else -1
        if before!=self._index:self._show_frame()
        return self._index!=target
