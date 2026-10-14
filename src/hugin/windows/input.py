"""One message-loop owner; callbacks only enqueue bounded direct commands.

The button semantics were independently implemented from Hugin DEC-003.
PipPal's MIT mouse_button.py was a read-only behavior reference.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
from dataclasses import dataclass, field
import queue
import sys
import threading
from collections.abc import Callable

from hugin.errors import HuginError

WM_XBUTTONDOWN, WM_XBUTTONUP = 0x020B, 0x020C
WM_HOTKEY, WM_QUIT, WM_CONTROL = 0x0312, 0x0012, 0x8001
MOD_NOREPEAT = 0x4000


class MousePresses:
    def __init__(self, emit: Callable[[str], None]):
        self.emit = emit
        self.down: set[int] = set()

    def handle(self, message: int, button: int, flags: int = 0) -> bool:
        if flags & 2 or button not in (1, 2):
            return False
        if message == WM_XBUTTONDOWN:
            if button not in self.down:
                self.down.add(button)
                self.emit('read' if button == 1 else 'dictation')
            return True
        if message == WM_XBUTTONUP:
            self.down.discard(button)
            return True
        return False


@dataclass
class _CancelCommand:
    active: bool
    done: threading.Event = field(default_factory=threading.Event)
    error: HuginError | None = None


class WindowsInputs:
    def __init__(self, on_action: Callable[[str], None], pilot: bool = False,
                 *, backend=None, queue_size: int = 32):
        if type(queue_size) is not int or not 1 <= queue_size <= 256:
            raise ValueError('queue_size must be between 1 and 256')
        self.on_action, self.pilot = on_action, pilot
        self._cleanup_succeeded = False
        self._backend = backend
        self._events: queue.Queue[str] = queue.Queue(queue_size)
        self._commands: queue.Queue[_CancelCommand] = queue.Queue(16)
        self._ready, self._halt = threading.Event(), threading.Event()
        self._thread: threading.Thread | None = None
        self._dispatcher: threading.Thread | None = None
        self._cancel_active = False
        self.running = False
        self.error: HuginError | None = None

    def _fail(self, failure: HuginError):
        if self.error is None:
            self.error = failure
        self._halt.set()
        if self._backend is not None:
            try:
                self._backend.post(WM_QUIT)
            except Exception:
                # The owner thread is still retained; stop() observes its exit.
                pass

    def _enqueue(self, action: str):
        if self.error is not None:
            return
        try:
            self._events.put_nowait(action)
        except queue.Full:
            self._fail(HuginError('resource_limit', 'input_queue'))

    def start(self):
        if self.running:
            return
        if self._thread is not None:
            raise HuginError('input_failed', 'input_restart')
        if self._backend is None:
            try:
                self._backend = NativeInputs()
            except HuginError as failure:
                self.error = failure
                raise
        self._dispatcher = threading.Thread(target=self._dispatch, name='hugin-input-dispatch', daemon=True)
        self._thread = threading.Thread(target=self._run, name='hugin-input-loop', daemon=True)
        self._dispatcher.start()
        self._thread.start()
        if not self._ready.wait(3):
            self._fail(HuginError('input_failed', 'input_start_timeout'))
        if self.error is not None or not self.running:
            self.stop()
            raise self.error or HuginError('input_failed', 'input_start')

    def set_cancel_active(self, active: bool):
        if type(active) is not bool:
            raise ValueError('active must be bool')
        if not self.running or self.error is not None:
            raise self.error or HuginError('input_failed', 'escape_registration')
        command = _CancelCommand(active)
        try:
            self._commands.put_nowait(command)
        except queue.Full:
            self._fail(HuginError('resource_limit', 'input_commands'))
            raise self.error
        try:
            self._backend.post(WM_CONTROL)
        except HuginError as failure:
            self._fail(failure)
            raise
        if not command.done.wait(2):
            self._fail(HuginError('input_failed', 'escape_timeout'))
            raise self.error
        if command.error is not None:
            raise command.error

    @property
    def closed(self):
        """Cleanup fact is independent of the retained operational error."""
        return self._cleanup_succeeded and not any(
            thread is not None and thread.is_alive() for thread in (self._thread,self._dispatcher))

    def stop(self):
        self._halt.set()
        if self._thread is not None and self._thread.is_alive():
            try:
                self._backend.post(WM_QUIT)
            except HuginError as failure:
                self.error = failure
                raise
            if threading.current_thread() is not self._thread:
                self._thread.join(3)
            if self._thread.is_alive():
                self.error = HuginError('input_failed', 'input_cleanup_timeout')
                raise self.error
        if self._dispatcher is not None and threading.current_thread() is not self._dispatcher:
            self._dispatcher.join(2)
            if self._dispatcher.is_alive():
                self.error = HuginError('input_failed', 'input_callback_timeout')
                raise self.error
        if self.error is not None:
            raise self.error

    def _dispatch(self):
        while not self._halt.is_set():
            try:
                action = self._events.get(timeout=0.05)
            except queue.Empty:
                continue
            if self._halt.is_set():
                return
            try:
                self.on_action(action)
            except Exception:
                self._fail(HuginError('input_failed', 'input_callback'))

    def _run(self):
        try:
            presses = MousePresses(self._enqueue)
            self._backend.open(None if self.pilot else presses.handle)
            mods = (1 | 2) if self.pilot else 1
            self._backend.register(1, mods | MOD_NOREPEAT, 0x44 if self.pilot else 0x59)
            if self.pilot:
                self._backend.register(2, mods | MOD_NOREPEAT, 0x56)
            self.running = True
            self._ready.set()
            while not self._halt.is_set():
                message, identity = self._backend.next_message()
                if message == WM_QUIT:
                    break
                if message == WM_HOTKEY:
                    if identity == 1:
                        self._enqueue('dictation')
                    elif identity == 2 and self.pilot:
                        self._enqueue('read')
                    elif identity == 3 and self._cancel_active:
                        self._enqueue('cancel')
                elif message == WM_CONTROL:
                    while True:
                        try:
                            command = self._commands.get_nowait()
                        except queue.Empty:
                            break
                        try:
                            if command.active != self._cancel_active:
                                if command.active:
                                    self._backend.register(3, MOD_NOREPEAT, 0x1B)
                                else:
                                    self._backend.unregister(3)
                                self._cancel_active = command.active
                        except HuginError as failure:
                            command.error = failure
                            self._fail(failure)
                        finally:
                            command.done.set()
        except HuginError as failure:
            self._fail(failure)
        except Exception:
            self._fail(HuginError('input_failed', 'input_loop'))
        finally:
            self.running = False
            self._halt.set()
            try:
                self._backend.close()
                self._cleanup_succeeded = True
            except Exception:
                self.error = HuginError('input_failed', 'input_cleanup')
            self._ready.set()
            while True:
                try:
                    command = self._commands.get_nowait()
                except queue.Empty:
                    break
                command.error = self.error or HuginError('input_failed', 'input_stopped')
                command.done.set()


class NativeInputs:
    """ctypes adapter. Constructing it does not register or consume input."""
    def __init__(self):
        if sys.platform != 'win32':
            raise HuginError('unsupported', 'windows_input')
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.callback_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, W.WPARAM, W.LPARAM)
        self.hook = None
        self.callback = None
        self.callback_error = None
        self.thread_id = 0
        self.keys: set[int] = set()
        for name, arguments, result in (
            ('RegisterHotKey', [W.HWND, ctypes.c_int, W.UINT, W.UINT], W.BOOL),
            ('UnregisterHotKey', [W.HWND, ctypes.c_int], W.BOOL),
            ('SetWindowsHookExW', [ctypes.c_int, self.callback_type, W.HINSTANCE, W.DWORD], W.HANDLE),
            ('CallNextHookEx', [W.HANDLE, ctypes.c_int, W.WPARAM, W.LPARAM], ctypes.c_ssize_t),
            ('UnhookWindowsHookEx', [W.HANDLE], W.BOOL),
            ('GetMessageW', [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT], ctypes.c_int),
            ('PeekMessageW', [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT], W.BOOL),
            ('PostThreadMessageW', [W.DWORD, W.UINT, W.WPARAM, W.LPARAM], W.BOOL),
            ('TranslateMessage', [ctypes.POINTER(W.MSG)], W.BOOL),
            ('DispatchMessageW', [ctypes.POINTER(W.MSG)], ctypes.c_ssize_t),
        ):
            function = getattr(self.user, name)
            function.argtypes, function.restype = arguments, result
        self.kernel.GetCurrentThreadId.argtypes = []
        self.kernel.GetCurrentThreadId.restype = W.DWORD
        self.kernel.GetModuleHandleW.argtypes = [W.LPCWSTR]
        self.kernel.GetModuleHandleW.restype = W.HMODULE

    def open(self, mouse):
        self.thread_id = self.kernel.GetCurrentThreadId()
        message = W.MSG()
        self.user.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
        if mouse is None:
            return

        class MouseEvent(ctypes.Structure):
            _fields_ = [('pt', W.POINT), ('mouseData', W.DWORD), ('flags', W.DWORD),
                        ('time', W.DWORD), ('dwExtraInfo', ctypes.c_size_t)]

        def callback(code, message, pointer):
            try:
                if code >= 0 and message in (WM_XBUTTONDOWN, WM_XBUTTONUP):
                    event = ctypes.cast(pointer, ctypes.POINTER(MouseEvent)).contents
                    if mouse(message, event.mouseData >> 16, event.flags):
                        return 1
            except Exception:
                self.callback_error = HuginError('input_failed', 'mouse_callback')
                self.user.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
            return self.user.CallNextHookEx(self.hook, code, message, pointer)

        self.callback = self.callback_type(callback)
        self.hook = self.user.SetWindowsHookExW(14, self.callback, self.kernel.GetModuleHandleW(None), 0)
        if not self.hook:
            raise HuginError('input_failed', 'mouse_registration')

    def register(self, identity, modifiers, key):
        if not self.user.RegisterHotKey(None, identity, modifiers, key):
            raise HuginError('input_conflict', 'hotkey_registration')
        self.keys.add(identity)

    def unregister(self, identity):
        if not self.user.UnregisterHotKey(None, identity):
            raise HuginError('input_failed', 'hotkey_cleanup')
        self.keys.remove(identity)

    def next_message(self):
        message = W.MSG()
        result = self.user.GetMessageW(ctypes.byref(message), None, 0, 0)
        if self.callback_error is not None:
            raise self.callback_error
        if result == -1:
            raise HuginError('input_failed', 'get_message')
        if result == 0:
            return WM_QUIT, 0
        self.user.TranslateMessage(ctypes.byref(message))
        self.user.DispatchMessageW(ctypes.byref(message))
        return message.message, message.wParam

    def post(self, message, value=0):
        if self.thread_id and not self.user.PostThreadMessageW(self.thread_id, message, value, 0):
            raise HuginError('input_failed', 'post_message')

    def close(self):
        failed = False
        for identity in tuple(self.keys):
            try:
                self.unregister(identity)
            except HuginError:
                failed = True
        if self.hook:
            if self.user.UnhookWindowsHookEx(self.hook):
                self.hook = None
                self.callback = None
            else:
                failed = True
        if failed:
            raise HuginError('input_failed', 'native_input_cleanup')
        self.thread_id = 0
