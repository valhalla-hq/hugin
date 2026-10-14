"""Owned invisible top-level broadcast window; no audio, input or model work.

The native callback only classifies a message and enqueues a bounded action.
Only the dedicated dispatch thread invokes the caller. Failed cleanup retains
the native owner and callback and may be retried on its original message thread.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import queue
import sys
import threading
import time
import uuid

from hugin.errors import HuginError

WM_POWERBROADCAST = 0x0218
WM_DEVICECHANGE = 0x0219
WM_CLOSE = 0x0010
WM_WAKE = 0x8002
_ACTIONS = frozenset(('system_pause','system_resume','devices_changed'))
_LIVE_OWNERS = set()  # Native window classes do not reference-count ctypes callbacks.
_LIVE_LOCK = threading.Lock()


class SignalMessages:
    """Parse event kinds once; never dereference or retain native lParam data."""
    def __init__(self,emit):
        self.emit=emit
        self._automatic_resume=False

    def handle(self,message,event):
        if message == WM_POWERBROADCAST:
            if event == 4:  # PBT_APMSUSPEND
                self._automatic_resume=False
                self.emit('system_pause')
            elif event == 18:  # PBT_APMRESUMEAUTOMATIC: every resume cycle.
                self._automatic_resume=True
                self.emit('system_resume')
            elif event == 7:  # Follow-up user resume need not invalidate twice.
                if not self._automatic_resume:
                    self._automatic_resume=True
                    self.emit('system_resume')
            else:
                return False
            return True
        if message == WM_DEVICECHANGE and event in (7,0x18,0x8000,0x8003,0x8004):
            self.emit('devices_changed')
            return True
        return False  # Queries/custom data are forwarded, never treated as changes.


class _CloseRequest:
    def __init__(self):
        self.done=threading.Event()
        self.error=None


class WindowsSignals:
    def __init__(self,on_action,*,backend=None,endpoints=None,queue_size=32):
        if not callable(on_action) or type(queue_size) is not int or not 1 <= queue_size <= 256:
            raise ValueError('invalid signal callback or queue bound')
        self.on_action=on_action
        self._native_defaults=backend is None
        self._backend=backend
        self._endpoints=endpoints
        self._events=queue.Queue(queue_size)
        self._requests=queue.Queue(1)
        self._request=None
        self._close_lock=threading.Lock()
        self._error_lock=threading.Lock()
        self._started=threading.Event()
        self._halt=threading.Event()
        self._native_closed=threading.Event()
        self._native_closed.set()
        self._opened=False
        self._thread=None
        self._dispatcher=None
        self.error=None

    @property
    def ready(self):
        return bool(self._opened and not self._halt.is_set() and self.error is None
            and (self._endpoints is None or self._endpoints.ready)
            and self._thread is not None and self._thread.is_alive()
            and self._dispatcher is not None and self._dispatcher.is_alive())

    @property
    def closed(self):
        return self._native_closed.is_set() and (self._endpoints is None or self._endpoints.closed) and not any(
            thread is not None and thread.is_alive() for thread in (self._thread,self._dispatcher))

    def _fail(self,code,phase):
        with self._error_lock:
            if self.error is None:
                self.error=HuginError(code,phase)
        self._halt.set()

    def _enqueue(self,action):
        if self._halt.is_set():
            return
        if not isinstance(action,str) or action not in _ACTIONS:
            self._fail('input_failed','signals_event')
            return
        try:
            self._events.put_nowait(action)
        except queue.Full:
            self._fail('resource_limit','signals_queue')

    def _dispatch(self):
        while not self._halt.is_set():
            try:
                action=self._events.get(timeout=.025)
            except queue.Empty:
                continue
            if self._halt.is_set():
                return
            try:
                self.on_action(action)
            except Exception:
                self._fail('input_failed','signals_callback')
                return

    def start(self):
        if self._thread is not None or self._halt.is_set():
            raise HuginError('input_failed','signals_restart')
        try:
            if self._backend is None:
                self._backend=_NativeSignalWindow()
            if self._native_defaults and self._endpoints is None:
                from hugin.windows.audio_endpoints import AudioEndpointNotifications
                self._endpoints=AudioEndpointNotifications()
        except Exception:
            self._fail('input_failed','signals_start')
            raise self.error from None
        self._native_closed.clear()
        self._dispatcher=threading.Thread(target=self._dispatch,name='hugin-signals-dispatch',daemon=True)
        self._thread=threading.Thread(target=self._run,name='hugin-signals-window',daemon=True)
        with _LIVE_LOCK:
            _LIVE_OWNERS.add(self)
        try:
            self._dispatcher.start()
            self._thread.start()
        except Exception:
            self._fail('input_failed','signals_start')
            if not self._thread.is_alive() and self._backend.closed and (
                self._endpoints is None or self._endpoints.closed):
                self._native_closed.set()
            raise HuginError('input_failed','signals_start') from None
        if not self._started.wait(3):
            self._fail('input_failed','signals_start_timeout')
            raise self.error
        if not self.ready:
            raise self.error or HuginError('input_failed','signals_start')

    def _cleanup(self,request=None):
        try:
            if self._endpoints is not None and not self._endpoints.closed:
                self._endpoints.close()
                if not self._endpoints.closed:
                    raise HuginError('input_failed','signals_endpoint_cleanup')
            # Keep the message queue/window available for COM cleanup recovery
            # until unregister and all same-thread COM releases have succeeded.
            self._backend.close()
            if not self._backend.closed:
                raise HuginError('input_failed','signals_cleanup')
        except Exception:
            self._fail('input_failed','signals_cleanup')
            if request is not None:
                request.error=HuginError('input_failed','signals_cleanup')
                request.done.set()
            return False
        self._opened=False
        self._native_closed.set()
        self._halt.set()
        if request is not None:
            request.done.set()  # Publish closure facts before the acknowledgement.
        return True

    def _run(self):
        recovering=False
        try:
            self._backend.open(self._enqueue)
            if self._endpoints is not None:
                self._endpoints.open(self._enqueue,self._fail)
            self._opened=True
        except Exception:
            self._fail('input_failed','signals_start')
            if self._cleanup():
                self._started.set()
                return
            # A partial open retains its established owner queue. Keep pumping
            # the owned window/class while awaiting explicit cleanup recovery.
        self._started.set()
        while True:
            try:
                request=self._requests.get(timeout=.025) if recovering else self._requests.get_nowait()
            except queue.Empty:
                request=None
            if request is not None:
                if self._cleanup(request):
                    return
                # Keep a healthy message pump alive even after cleanup fails;
                # the retained top-level window must still answer broadcasts.
                continue
            if recovering:
                continue  # Retain resources; retry only on an explicit close request.
            try:
                if self._backend.dispatch_one():
                    continue
            except Exception:
                pass
            self._fail('input_failed','signals_loop')
            if self._cleanup():
                return
            recovering=True

    def close(self,timeout=2):
        if type(timeout) not in (int,float) or not 0 < timeout <= 5:
            raise ValueError('invalid signal cleanup timeout')
        with self._close_lock:
            deadline=time.monotonic()+timeout
            self._halt.set()
            if self._thread is not None and threading.current_thread() in (self._thread,self._dispatcher):
                raise HuginError('input_failed','signals_close_thread')
            if self._thread is not None and self._thread.is_alive() and not self._native_closed.is_set():
                if self._request is None or self._request.done.is_set():
                    self._request=_CloseRequest()
                    self._requests.put_nowait(self._request)
                try:
                    self._backend.wake()
                except Exception:
                    self._fail('input_failed','signals_wake')
                    raise HuginError('input_failed','signals_wake') from None
                if not self._request.done.wait(max(0,deadline-time.monotonic())):
                    self._fail('input_failed','signals_cleanup_timeout')
                    raise HuginError('input_failed','signals_cleanup_timeout')
                if self._request.error:
                    raise self._request.error
            for thread in (self._thread,self._dispatcher):
                if thread is not None and thread.ident is not None:
                    thread.join(max(0,deadline-time.monotonic()))
            if not self.closed:
                self._fail('input_failed','signals_cleanup_timeout')
                raise HuginError('input_failed','signals_cleanup_timeout')
            with _LIVE_LOCK:
                _LIVE_OWNERS.discard(self)


class _WindowClass(ctypes.Structure):
    _fields_=[('style',W.UINT),('procedure',ctypes.c_void_p),
        ('class_extra',ctypes.c_int),('window_extra',ctypes.c_int),('instance',W.HINSTANCE),
        ('icon',W.HICON),('cursor',W.HANDLE),('background',W.HBRUSH),
        ('menu',W.LPCWSTR),('name',W.LPCWSTR)]


class _NativeSignalWindow:
    def __init__(self):
        if sys.platform != 'win32':
            raise HuginError('unsupported','signals')
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.callback_type=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM)
        for library,name,args,result in (
            (self.user,'RegisterClassW',[ctypes.POINTER(_WindowClass)],W.ATOM),
            (self.user,'UnregisterClassW',[W.LPCWSTR,W.HINSTANCE],W.BOOL),
            (self.user,'CreateWindowExW',[W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,
                ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.HWND,W.HMENU,W.HINSTANCE,W.LPVOID],W.HWND),
            (self.user,'DestroyWindow',[W.HWND],W.BOOL),
            (self.user,'DefWindowProcW',[W.HWND,W.UINT,W.WPARAM,W.LPARAM],ctypes.c_ssize_t),
            (self.user,'GetMessageW',[ctypes.POINTER(W.MSG),W.HWND,W.UINT,W.UINT],ctypes.c_int),
            (self.user,'PeekMessageW',[ctypes.POINTER(W.MSG),W.HWND,W.UINT,W.UINT,W.UINT],W.BOOL),
            (self.user,'TranslateMessage',[ctypes.POINTER(W.MSG)],W.BOOL),
            (self.user,'DispatchMessageW',[ctypes.POINTER(W.MSG)],ctypes.c_ssize_t),
            (self.user,'PostThreadMessageW',[W.DWORD,W.UINT,W.WPARAM,W.LPARAM],W.BOOL),
            (self.kernel,'GetCurrentThreadId',[],W.DWORD),
            (self.kernel,'GetModuleHandleW',[W.LPCWSTR],W.HMODULE),
        ):
            function=getattr(library,name)
            function.argtypes,function.restype=args,result
        self.name='Hugin.SystemSignals.'+uuid.uuid4().hex
        self.hwnd=None
        self._registered=False
        self._wndproc=None
        self._thread_id=0
        self._instance=None
        self._callback_error=None

    @property
    def closed(self):
        return self.hwnd is None and not self._registered and self._wndproc is None

    def _owner_thread(self):
        if self._thread_id and self.kernel.GetCurrentThreadId() != self._thread_id:
            raise HuginError('input_failed','signals_owner_thread')

    def open(self,notify):
        if not self.closed:
            raise HuginError('input_failed','signals_native_restart')
        self._thread_id=self.kernel.GetCurrentThreadId()
        self._instance=self.kernel.GetModuleHandleW(None)
        if not self._thread_id or not self._instance:
            raise HuginError('input_failed','signals_identity')
        message=W.MSG()
        self.user.PeekMessageW(ctypes.byref(message),None,0,0,0)  # Establish the owned thread queue.
        messages=SignalMessages(notify)
        def callback(hwnd,message,event,data):
            try:
                if message == WM_CLOSE:
                    return 0  # Only the owned close request can destroy this window.
                if messages.handle(message,event):
                    return 1
                return self.user.DefWindowProcW(hwnd,message,event,data)
            except Exception:
                self._callback_error=HuginError('input_failed','signals_callback')
                return 0
        self._wndproc=self.callback_type(callback)
        window_class=_WindowClass(procedure=ctypes.cast(self._wndproc,ctypes.c_void_p),
            instance=self._instance,name=self.name)
        if not self.user.RegisterClassW(ctypes.byref(window_class)):
            self._wndproc=None
            raise HuginError('input_failed','signals_class')
        self._registered=True
        # Parent None and no WS_CHILD/WS_VISIBLE: a hidden broadcast top-level,
        # never HWND_MESSAGE. No existing WNDPROC is read or overwritten.
        self.hwnd=self.user.CreateWindowExW(0,self.name,'',0,0,0,0,0,None,None,self._instance,None)
        if not self.hwnd:
            self.hwnd=None
            raise HuginError('input_failed','signals_window')

    def dispatch_one(self):
        self._owner_thread()
        message=W.MSG()
        result=self.user.GetMessageW(ctypes.byref(message),None,0,0)
        if result == -1:
            raise HuginError('input_failed','signals_message')
        if result == 0:
            return False
        self.user.TranslateMessage(ctypes.byref(message))
        self.user.DispatchMessageW(ctypes.byref(message))
        if self._callback_error:
            raise self._callback_error
        return True

    def wake(self):
        if self._thread_id and not self.user.PostThreadMessageW(self._thread_id,WM_WAKE,0,0):
            raise HuginError('input_failed','signals_wake')

    def close(self):
        self._owner_thread()
        if self.hwnd is not None:
            if not self.user.DestroyWindow(self.hwnd):
                raise HuginError('input_failed','signals_window_cleanup')
            self.hwnd=None
        if self._registered:
            if not self.user.UnregisterClassW(self.name,self._instance):
                raise HuginError('input_failed','signals_class_cleanup')
            self._registered=False
        self._wndproc=None  # Both window and class no longer retain the callback.
        self._thread_id=0
