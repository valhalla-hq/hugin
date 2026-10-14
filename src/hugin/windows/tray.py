"""Bounded owner for the pinned pystray 0.19.5 Win32 producer.

The native runner and visibility setup are both held before they start. Public
Icon.stop is only intent, so retry uses the same icon's private _stop and joins
the actual runner before releasing its HICON. No method is monkeypatched.
"""
from __future__ import annotations

from importlib.metadata import version
import math
import threading
import time

from hugin.errors import HuginError

_LIVE_OWNERS=set()
_LIVE_LOCK=threading.Lock()


class _PystrayWin32:
    def __init__(self,icon):
        self.icon=icon
        self._class_released=False
        self._validated=False
    def validate(self):
        if self._validated:return
        if version('pystray')!='0.19.5' or type(self.icon).__module__!='pystray._win32':
            raise ValueError('unsupported tray producer')
        if self.icon._running or getattr(self.icon,'_thread',None) is not None:
            raise ValueError('tray already has a runner')
        self._validated=True
    def run(self):self.icon._run()
    def can_stop(self,thread):
        # _running can already be false after a failed public stop. Ownership
        # is the exact runner plus its own created windows, never an HWND search.
        return getattr(self.icon,'_thread',None) is thread and bool(
            self.icon._hwnd and self.icon._menu_hwnd)
    def ready(self,thread):return self.can_stop(thread) and self.icon._running
    def show(self):self.icon.visible=True
    def request_stop(self):self.icon._stop()
    def finish(self,*,unstarted,completed):
        if not unstarted and not completed:
            # A failed native loop may have only partly cleaned up its windows.
            # Do not reinterpret an exited thread as successful native cleanup.
            if self.icon._hwnd or self.icon._menu_hwnd:
                raise ValueError('native tray cleanup unconfirmed')
            unstarted=True
        if unstarted and not self._class_released:
            self.icon._unregister_class(self.icon._atom)
            self._class_released=True
        self.icon._release_icon()  # This resource otherwise waits for __del__.
        self.icon._running=False


class TrayOwner:
    """Single-use icon owner. Failed operations attach this same retryable owner."""
    def __init__(self,icon,*,timeout=2.0,backend=None):
        self._deadline(timeout)
        self._icon=icon
        self._backend=backend or _PystrayWin32(icon)
        self.timeout=timeout
        self._thread=self._setup=None
        self._started=False
        self._closed=False
        self._state_lock=threading.Lock()
        self._close_lock=threading.Lock()
        self._stop=threading.Event()
        self._run_done=threading.Event()
        self._setup_done=threading.Event()
        self._ready=threading.Event()
        self._completed=False
        self.error=None
        with _LIVE_LOCK:_LIVE_OWNERS.add(self)

    @staticmethod
    def _deadline(timeout):
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=5:
            raise ValueError('invalid tray deadline')
        return time.monotonic()+timeout

    def _failure(self,phase):
        error=HuginError('input_failed',phase)
        error.owner=self
        if self.error is None:self.error=error
        return error

    @property
    def closed(self):return self._closed

    @property
    def ready(self):
        return bool(self._ready.is_set() and not self._stop.is_set() and not self.error
            and self._thread is not None and self._thread.is_alive())

    @property
    def title(self):return self._icon.title
    @title.setter
    def title(self,value):
        if self._closed:raise self._failure('tray_closed')
        self._icon.title=value
    @property
    def icon(self):return self._icon.icon
    @icon.setter
    def icon(self,value):
        if self._closed:raise self._failure('tray_closed')
        self._icon.icon=value
    @property
    def menu(self):return self._icon.menu
    @menu.setter
    def menu(self,value):
        if self._closed:raise self._failure('tray_closed')
        self._icon.menu=value

    def _run(self):
        try:
            self._backend.run()
            self._completed=True
            if not self._stop.is_set():self._failure('tray_loop')
        except Exception:self._failure('tray_native')
        finally:self._run_done.set()

    def _show(self):
        try:
            while not self._stop.is_set():
                if self._run_done.is_set():return
                if self._backend.ready(self._thread):
                    if self._stop.is_set():return
                    self._backend.show()
                    if not self._stop.is_set():self._ready.set()
                    return
                self._stop.wait(.01)
        except Exception:self._failure('tray_show')
        finally:self._setup_done.set()

    def start(self):
        with self._state_lock:
            if self._started or self._stop.is_set() or self._closed:
                raise self._failure('tray_restart')
            self._started=True
            try:
                self._backend.validate()
                self._thread=threading.Thread(target=self._run,name='hugin-tray-native',daemon=True)
                self._setup=threading.Thread(target=self._show,name='hugin-tray-setup',daemon=True)
                self._thread.start()
                self._setup.start()
            except Exception:raise self._failure('tray_start') from None
        if not self._setup_done.wait(self.timeout):
            raise self._failure('tray_start_timeout')
        if not self.ready:raise self._failure('tray_start')
        return self

    def close(self,timeout=2.0):
        deadline=self._deadline(timeout)
        if not self._close_lock.acquire(timeout=max(0,deadline-time.monotonic())):
            raise self._failure('tray_cleanup_timeout')
        try:
            if self._closed:return
            self._stop.set()
            if threading.current_thread() in (self._thread,self._setup):
                raise self._failure('tray_close_thread')
            try:
                self._backend.validate()
                # Finish visibility before destroying its native notification
                # window. A blocked Shell call remains owned, never green.
                if self._setup is not None and self._setup.ident is not None:
                    self._setup.join(max(0,deadline-time.monotonic()))
                    if self._setup.is_alive():raise ValueError('setup still live')
                unstarted=self._thread is None or self._thread.ident is None
                if not unstarted:
                    while self._thread.is_alive() and not self._backend.can_stop(self._thread):
                        remaining=deadline-time.monotonic()
                        if remaining<=0:raise ValueError('native start still pending')
                        self._run_done.wait(min(.01,remaining))
                    if self._thread.is_alive():self._backend.request_stop()
                    self._thread.join(max(0,deadline-time.monotonic()))
                    if self._thread.is_alive():raise ValueError('native loop still live')
                self._backend.finish(unstarted=unstarted,completed=self._completed)
            except Exception:raise self._failure('tray_cleanup') from None
            self._closed=True
            with _LIVE_LOCK:_LIVE_OWNERS.discard(self)
        finally:self._close_lock.release()
