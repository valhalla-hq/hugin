"""Placement/show contract for Hugin's own reading window; never external UI."""
import ctypes as ct
from ctypes import wintypes as wt


class _MonitorInfo(ct.Structure):
    _fields_=[('size',wt.DWORD),('monitor',wt.RECT),('work',wt.RECT),('flags',wt.DWORD)]


class PanelPlacement:
    def __init__(self,window):
        self.window=window
        self.api=ct.WinDLL('user32',use_last_error=True)
        self.gdi=ct.WinDLL('gdi32',use_last_error=True)
        self._shape=None;self._region=None
        signatures={
            'GetAncestor':([wt.HWND,wt.UINT],wt.HWND),
            'GetForegroundWindow':([],wt.HWND),
            'MonitorFromWindow':([wt.HWND,wt.DWORD],wt.HANDLE),
            'MonitorFromRect':([ct.POINTER(wt.RECT),wt.DWORD],wt.HANDLE),
            'GetMonitorInfoW':([wt.HANDLE,ct.POINTER(_MonitorInfo)],wt.BOOL),
            'GetWindowLongPtrW':([wt.HWND,ct.c_int],ct.c_ssize_t),
            'SetWindowLongPtrW':([wt.HWND,ct.c_int,ct.c_ssize_t],ct.c_ssize_t),
            'SetWindowPos':([wt.HWND,wt.HWND,ct.c_int,ct.c_int,ct.c_int,ct.c_int,wt.UINT],wt.BOOL),
            'SetWindowRgn':([wt.HWND,wt.HANDLE,wt.BOOL],ct.c_int),
        }
        for name,(args,result) in signatures.items():
            fn=getattr(self.api,name);fn.argtypes=args;fn.restype=result
        self.gdi.CreateRoundRectRgn.argtypes=[ct.c_int]*6
        self.gdi.CreateRoundRectRgn.restype=wt.HANDLE
        self.gdi.DeleteObject.argtypes=[wt.HANDLE];self.gdi.DeleteObject.restype=wt.BOOL
        window.update_idletasks()
        self.hwnd=self.api.GetAncestor(window.winfo_id(),2)
        if not self.hwnd:raise OSError('reading_panel_handle')
        style=self.api.GetWindowLongPtrW(self.hwnd,-20)
        ct.set_last_error(0)
        result=self.api.SetWindowLongPtrW(self.hwnd,-20,style|0x08000000|0x80)
        if result==0 and ct.get_last_error():raise OSError('reading_panel_style')

    def work_area(self,rect=None):
        if rect is None:monitor=self.api.MonitorFromWindow(self.api.GetForegroundWindow(),2)
        else:monitor=self.api.MonitorFromRect(ct.byref(wt.RECT(*rect)),2)
        info=_MonitorInfo(size=ct.sizeof(_MonitorInfo))
        if not self.api.GetMonitorInfoW(monitor,ct.byref(info)):
            raise OSError('reading_panel_monitor')
        rect=info.work
        return rect.left,rect.top,rect.right,rect.bottom

    def show(self,x,y,width,height,*,radius=18):
        # WS_EX_NOACTIVATE is installed before Tk maps this owned window.
        # SWP_NOACTIVATE also covers placement/topmost; no lift/focus/restore.
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        shape=(width,height,radius)
        if shape!=self._shape:
            self.close()  # Never overwrite an untransferred region after failed cleanup.
            self._region=self.gdi.CreateRoundRectRgn(0,0,width+1,height+1,2*radius,2*radius)
            if not self._region:raise OSError('reading_panel_region')
            if not self.api.SetWindowRgn(self.hwnd,self._region,True):
                self.close()
                raise OSError('reading_panel_region')
            # On success Windows owns and eventually deletes this region.
            self._region=None
            self._shape=shape
        self.window.deiconify()
        self.window.update_idletasks()
        if not self.api.SetWindowPos(self.hwnd,wt.HWND(-1),x,y,width,height,0x10|0x40):
            self.window.withdraw()
            raise OSError('reading_panel_show')

    def move(self,x,y):
        if not self.api.SetWindowPos(self.hwnd,None,x,y,0,0,0x1|0x4|0x10):
            raise OSError('reading_panel_move')

    def close(self):
        if self._region:
            if not self.gdi.DeleteObject(self._region):raise OSError('reading_panel_region_cleanup')
            self._region=None
