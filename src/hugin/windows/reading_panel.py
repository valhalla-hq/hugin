"""Placement/show contract for Hugin's own reading window; never external UI."""
import ctypes as ct
from ctypes import wintypes as wt


class _MonitorInfo(ct.Structure):
    _fields_=[('size',wt.DWORD),('monitor',wt.RECT),('work',wt.RECT),('flags',wt.DWORD)]


class PanelPlacement:
    def __init__(self,window):
        self.window=window
        self.api=ct.WinDLL('user32',use_last_error=True)
        signatures={
            'GetAncestor':([wt.HWND,wt.UINT],wt.HWND),
            'GetForegroundWindow':([],wt.HWND),
            'MonitorFromWindow':([wt.HWND,wt.DWORD],wt.HANDLE),
            'GetMonitorInfoW':([wt.HANDLE,ct.POINTER(_MonitorInfo)],wt.BOOL),
            'GetWindowLongPtrW':([wt.HWND,ct.c_int],ct.c_ssize_t),
            'SetWindowLongPtrW':([wt.HWND,ct.c_int,ct.c_ssize_t],ct.c_ssize_t),
            'SetWindowPos':([wt.HWND,wt.HWND,ct.c_int,ct.c_int,ct.c_int,ct.c_int,wt.UINT],wt.BOOL),
        }
        for name,(args,result) in signatures.items():
            fn=getattr(self.api,name);fn.argtypes=args;fn.restype=result
        window.update_idletasks()
        self.hwnd=self.api.GetAncestor(window.winfo_id(),2)
        if not self.hwnd:raise OSError('reading_panel_handle')
        style=self.api.GetWindowLongPtrW(self.hwnd,-20)
        ct.set_last_error(0)
        result=self.api.SetWindowLongPtrW(self.hwnd,-20,style|0x08000000|0x80)
        if result==0 and ct.get_last_error():raise OSError('reading_panel_style')

    def work_area(self):
        monitor=self.api.MonitorFromWindow(self.api.GetForegroundWindow(),2)
        info=_MonitorInfo(size=ct.sizeof(_MonitorInfo))
        if not self.api.GetMonitorInfoW(monitor,ct.byref(info)):
            raise OSError('reading_panel_monitor')
        rect=info.work
        return rect.left,rect.top,rect.right,rect.bottom

    def show(self,x,y,width,height):
        # WS_EX_NOACTIVATE is installed before Tk maps this owned window.
        # SWP_NOACTIVATE also covers placement/topmost; no lift/focus/restore.
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        self.window.deiconify()
        self.window.update_idletasks()
        if not self.api.SetWindowPos(self.hwnd,wt.HWND(-1),x,y,width,height,0x10|0x40):
            self.window.withdraw()
            raise OSError('reading_panel_show')
