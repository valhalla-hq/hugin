"""Mouse clicks on our action buttons without activating the Hugin window.

Top-level protection prevents Windows from deactivating the external app before
the child receives WM_MOUSEACTIVATE. Ordinary clicks activate only our window.
No foreground history, focus restoration, hooks or external-window mutation.
All registrations and teardown belong to the creating Tk UI thread.
"""
import ctypes as ct
from ctypes import wintypes as wt


class ActionFocus:
    def __init__(self):
        self.handles=set()
        self._top=None;self._added_style=0
        self.user=ct.WinDLL('user32',use_last_error=True)
        self.kernel=ct.WinDLL('kernel32',use_last_error=True)
        self.api=ct.WinDLL('comctl32',use_last_error=True)
        self._signature=ct.WINFUNCTYPE(ct.c_ssize_t,wt.HWND,wt.UINT,
            ct.c_size_t,ct.c_ssize_t,ct.c_size_t,ct.c_size_t)
        for api,name,args,result in (
            (self.user,'GetForegroundWindow',[],wt.HWND),
            (self.user,'GetAncestor',[wt.HWND,wt.UINT],wt.HWND),
            (self.user,'GetWindowLongPtrW',[wt.HWND,ct.c_int],ct.c_ssize_t),
            (self.user,'SetWindowLongPtrW',[wt.HWND,ct.c_int,ct.c_ssize_t],ct.c_ssize_t),
            (self.user,'SetForegroundWindow',[wt.HWND],wt.BOOL),
            (self.user,'GetWindowThreadProcessId',[wt.HWND,ct.POINTER(wt.DWORD)],wt.DWORD),
            (self.kernel,'GetCurrentProcessId',[],wt.DWORD),
            (self.kernel,'GetCurrentThreadId',[],wt.DWORD),
            (self.api,'SetWindowSubclass',[wt.HWND,self._signature,ct.c_size_t,ct.c_size_t],wt.BOOL),
            (self.api,'RemoveWindowSubclass',[wt.HWND,self._signature,ct.c_size_t],wt.BOOL),
            (self.api,'GetWindowSubclass',[wt.HWND,self._signature,ct.c_size_t,ct.POINTER(ct.c_size_t)],wt.BOOL),
            (self.api,'DefSubclassProc',[wt.HWND,wt.UINT,ct.c_size_t,ct.c_ssize_t],ct.c_ssize_t)):
            fn=getattr(api,name);fn.argtypes=args;fn.restype=result
        self._thread=self.kernel.GetCurrentThreadId()
        self._pid=self.kernel.GetCurrentProcessId()
        self._callback=self._signature(self._message)
        self._id=id(self)

    def _check_thread(self):
        if self.kernel.GetCurrentThreadId()!=self._thread:
            raise OSError('Action focus belongs to its UI thread')

    def attach(self,widget):
        self._check_thread()
        hwnd=widget.winfo_id()
        self._register(hwnd)
        widget.bind('<Destroy>',lambda event:self._destroyed(hwnd),add='+')

    def protect_window(self,window):
        self._check_thread()
        window.update_idletasks()
        hwnd=self.user.GetAncestor(window.winfo_id(),2)
        if self._top is not None:
            if hwnd!=self._top:raise OSError('Action window changed')
            return
        self._register(hwnd)
        self._top=hwnd
        style=self._style(hwnd)
        # Keep the taskbar/Alt+Tab entry while suppressing system activation.
        # Child actions also veto queue activation. Other clicks reach the
        # wrapper callback, which explicitly activates only this owned window.
        self._added_style=(0x08000000|0x00040000)&~style
        self._set_style(hwnd,style|self._added_style)

    def _register(self,hwnd):
        pid=wt.DWORD()
        thread=self.user.GetWindowThreadProcessId(hwnd,ct.byref(pid))
        if thread!=self._thread or pid.value!=self._pid:
            raise OSError('Action button is not owned by this UI thread')
        if hwnd in self.handles:return
        if not self.api.SetWindowSubclass(hwnd,self._callback,self._id,0):
            raise OSError('Cannot preserve action focus')
        self.handles.add(hwnd)

    def _style(self,hwnd):
        ct.set_last_error(0)
        style=self.user.GetWindowLongPtrW(hwnd,-20)
        if not style and ct.get_last_error():raise OSError('Cannot read action window style')
        return style

    def _set_style(self,hwnd,style):
        ct.set_last_error(0)
        previous=self.user.SetWindowLongPtrW(hwnd,-20,style)
        if not previous and ct.get_last_error():raise OSError('Cannot set action window style')

    def _message(self,hwnd,message,wparam,lparam,subclass_id,reference):
        if message==0x21:  # WM_MOUSEACTIVATE
            if hwnd!=self._top:return 3  # Action: deliver click, retain foreground.
            # Action children never forward here. Activate Hugin only for a
            # deliberate ordinary mouse click, not mouse-hover activation.
            if (lparam>>16)&0xffff in (0x201,0x204,0x207,0x20b):
                self.user.SetForegroundWindow(hwnd)
            else:return 3
        if message==0x82:  # WM_NCDESTROY: no reusable HWND remains owned.
            self.api.RemoveWindowSubclass(hwnd,self._callback,self._id)
            result=self.api.DefSubclassProc(hwnd,message,wparam,lparam)
            self.handles.discard(hwnd)
            if hwnd==self._top:self._top=None;self._added_style=0
            return result
        return self.api.DefSubclassProc(hwnd,message,wparam,lparam)

    def external_target(self):
        """Early UX guard only; clipboard adapter still proves the actual field."""
        self._check_thread()
        hwnd=self.user.GetForegroundWindow();pid=wt.DWORD()
        thread=self.user.GetWindowThreadProcessId(hwnd,ct.byref(pid)) if hwnd else 0
        return bool(thread and pid.value and pid.value!=self._pid)

    def _detach(self,hwnd):
        # Tk can replace its native procedure before DestroyWindow. Verify the
        # exact callback registration rather than treating a reused HWND as ours.
        reference=ct.c_size_t()
        if self.api.GetWindowSubclass(hwnd,self._callback,self._id,ct.byref(reference)):
            if hwnd==self._top and self._added_style:
                self._set_style(hwnd,self._style(hwnd)&~self._added_style)
                self._added_style=0
            if not self.api.RemoveWindowSubclass(hwnd,self._callback,self._id):
                raise OSError('Cannot release action focus')
        self.handles.discard(hwnd)
        if hwnd==self._top:self._top=None;self._added_style=0

    def _destroyed(self,hwnd):
        try:self._detach(hwnd)
        except OSError:pass  # Explicit close retries while retaining the callback.

    def close(self):
        self._check_thread()
        for hwnd in tuple(self.handles):
            self._detach(hwnd)
