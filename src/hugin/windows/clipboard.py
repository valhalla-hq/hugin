"""Serialized, bounded clipboard transactions with explicit conflict outcomes.

Native capture/delivery are opt-in per proven target class. No application is approved
by default: SendInput success does not prove that a foreign app read the text.
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
import ctypes
from ctypes import wintypes as W
from dataclasses import dataclass
import sys
import threading
import time
import uuid

MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024
MAX_TEXT_BYTES = 256 * 1024
CF_UNICODETEXT = 13


class ClipboardFailure(Exception):
    def __init__(self, status: str, *, submitted=False, owned_sequence=None):
        self.status = status
        self.submitted = submitted
        self.owned_sequence = owned_sequence
        super().__init__(status)


@dataclass(frozen=True)
class WindowTarget:
    hwnd: int
    focus: int
    pid: int
    thread: int
    process_created: int
    control_class: str
    caret: tuple[int, int, int, int, int] | None
    selection: tuple[int, int] | None
    editable: bool = True

    @property
    def verifiable(self):
        return bool(self.editable and self.hwnd and self.focus and self.process_created and
                    self.caret is not None and self.selection is not None)


@dataclass(frozen=True)
class ClipboardSnapshot:
    sequence: int
    formats: tuple[tuple[int, bytes], ...]


@dataclass(frozen=True)
class ClipboardTransaction:
    transaction_id: str
    sequence: int
    target: WindowTarget


@dataclass(frozen=True)
class ClipboardResult:
    status: str
    text: str | None = None
    target: WindowTarget | None = None
    submitted: bool = False
    restored: bool = False


class ClipboardService:
    def __init__(self, *, backend=None, snapshot_budget=MAX_SNAPSHOT_BYTES,
                 selection_timeout=0.9):
        if type(snapshot_budget) is not int or not 0 < snapshot_budget <= MAX_SNAPSHOT_BYTES:
            raise ValueError('snapshot budget exceeds contract')
        if not 0 < selection_timeout <= 2:
            raise ValueError('selection timeout exceeds contract')
        self.backend = backend
        self.snapshot_budget = snapshot_budget
        self.selection_timeout = selection_timeout
        self._lock = threading.Lock()
        self._approved: dict[str, float] = {}
        self._capture_approved: set[str] = set()
        self._pending_restore: tuple[ClipboardSnapshot, int] | None = None

    @property
    def recovery_pending(self):
        return self._pending_restore is not None

    def _check_recovery(self, backend):
        if self._pending_restore is not None:
            if backend.sequence() != self._pending_restore[1]:
                self._pending_restore = None  # A later user copy has priority.
            else:
                raise ClipboardFailure('clipboard_recovery_pending')

    def _native(self):
        if self.backend is None:
            self.backend = NativeClipboard()
        return self.backend

    def approve_target_class(self, control_class: str, restore_delay: float):
        """Caller must have explicit pilot proof for this class and delay."""
        if not isinstance(control_class, str) or not control_class or not 0.02 <= restore_delay <= 2:
            raise ValueError('invalid pilot approval')
        self._approved[control_class] = restore_delay

    def approve_capture_target_class(self, control_class: str):
        """Internal pilot seam; includes the copy-response attribution limit."""
        if not isinstance(control_class, str) or not control_class:
            raise ValueError('invalid capture pilot approval')
        self._capture_approved.add(control_class)

    def capture_target(self) -> ClipboardResult:
        if not self._lock.acquire(blocking=False):
            return ClipboardResult('clipboard_busy')
        try:
            target = self._native().capture_target()
            return ClipboardResult('target_captured' if target.verifiable else 'target_unverifiable', target=target)
        except ClipboardFailure as failure:
            return ClipboardResult(failure.status)
        finally:
            self._lock.release()

    @staticmethod
    def _text_formats(text: str):
        if not isinstance(text, str) or '\0' in text:
            raise ClipboardFailure('text_invalid')
        try:
            if len(text) > MAX_TEXT_BYTES or len(text.encode('utf-8')) > MAX_TEXT_BYTES:
                raise ClipboardFailure('text_limit')
            return ((CF_UNICODETEXT, (text + '\0').encode('utf-16-le')),)
        except UnicodeError:
            raise ClipboardFailure('text_invalid') from None

    def _restore(self, backend, snapshot, sequence):
        # Compare-and-replace is performed while the OS clipboard is locked.
        try:
            backend.replace(snapshot.formats, sequence)
            self._pending_restore = None
            return True
        except ClipboardFailure as failure:
            if failure.status == 'clipboard_changed':
                # Retained recovery may refer to a newer partial mutation.
                if self._pending_restore is not None and backend.sequence() != self._pending_restore[1]:
                    self._pending_restore = None
                return False
            self._pending_restore = (snapshot, failure.owned_sequence if failure.owned_sequence is not None else sequence)
            raise ClipboardFailure('clipboard_restore_failed') from None

    def capture_selection(self, cancelled: Callable[[], bool]) -> ClipboardResult:
        try:
            return self._capture_selection(cancelled)
        except ClipboardFailure as failure:
            return ClipboardResult(failure.status)

    def _capture_selection(self, cancelled: Callable[[], bool]) -> ClipboardResult:
        if not self._lock.acquire(blocking=False):
            return ClipboardResult('clipboard_busy')
        snapshot = None
        owned_sequence = None
        try:
            if cancelled():
                return ClipboardResult('cancelled')
            backend = self._native()
            self._check_recovery(backend)
            target = backend.capture_target()
            if hasattr(backend, 'read_direct_selection'):
                text = backend.read_direct_selection(target, MAX_TEXT_BYTES, cancelled)
                if cancelled():
                    return ClipboardResult('cancelled')
                if backend.capture_target() != target:
                    return ClipboardResult('target_changed')
                if text is not None:
                    if not isinstance(text, str) or '\0' in text:
                        return ClipboardResult('text_invalid')
                    try:
                        if len(text) > MAX_TEXT_BYTES or len(text.encode('utf-8')) > MAX_TEXT_BYTES:
                            return ClipboardResult('text_limit')
                    except UnicodeError:
                        return ClipboardResult('text_invalid')
                    return ClipboardResult('captured' if text else 'selection_empty',
                                           text=text or None, target=target)
            if target.control_class not in self._capture_approved:
                return ClipboardResult('target_unverified')
            if backend.modifiers_down():
                return ClipboardResult('modifiers_active')
            snapshot = backend.snapshot(self.snapshot_budget)
            if cancelled():
                return ClipboardResult('cancelled')
            if backend.capture_target() != target:
                return ClipboardResult('target_changed')
            marker = '__hugin_selection_' + uuid.uuid4().hex
            owned_sequence = backend.stage(self._text_formats(marker), snapshot.sequence)
            if cancelled():
                restored = self._restore(backend, snapshot, owned_sequence)
                owned_sequence = None
                return ClipboardResult('cancelled', restored=restored)
            # A user's copy between staging and Ctrl+C wins as well.
            if backend.sequence() != owned_sequence:
                owned_sequence = None
                return ClipboardResult('clipboard_changed')
            if backend.capture_target() != target:
                return ClipboardResult('target_changed')
            backend.copy_selection(target)
            deadline = time.monotonic() + self.selection_timeout
            while time.monotonic() < deadline:
                if cancelled():
                    return ClipboardResult('cancelled')
                if backend.capture_target() != target:
                    return ClipboardResult('target_changed')
                current = backend.sequence()
                if current != owned_sequence:
                    # Only a response attributed to the bound target can be
                    # acknowledged as part of this capture transaction.
                    try:
                        text = backend.read_selection(current, target, MAX_TEXT_BYTES)
                    except ClipboardFailure:
                        owned_sequence = None
                        raise
                    owned_sequence = current
                    if not text or text == marker:
                        return ClipboardResult('selection_empty')
                    restored = self._restore(backend, snapshot, owned_sequence)
                    owned_sequence = None
                    return ClipboardResult('captured', text=text, target=target, restored=restored)
                backend.sleep(0.01)
            return ClipboardResult('selection_empty')
        except ClipboardFailure as failure:
            if failure.owned_sequence is not None:
                owned_sequence = failure.owned_sequence
            return ClipboardResult(failure.status)
        finally:
            try:
                if snapshot is not None and owned_sequence is not None:
                    self._restore(self.backend, snapshot, owned_sequence)
            finally:
                self._lock.release()

    def deliver(self, text: str, target: WindowTarget | None,
                still_current: Callable[[], bool], *,
                authorize: Callable[[ClipboardTransaction], bool] | None = None) -> ClipboardResult:
        try:
            return self._deliver(text, target, still_current, authorize)
        except ClipboardFailure as failure:
            return ClipboardResult(failure.status, submitted=failure.submitted)

    def _deliver(self, text: str, target: WindowTarget | None,
                 still_current: Callable[[], bool], authorize) -> ClipboardResult:
        if not self._lock.acquire(blocking=False):
            return ClipboardResult('clipboard_busy')
        snapshot = None
        owned_sequence = None
        submitted = False
        try:
            formats = self._text_formats(text)
            if not still_current():
                return ClipboardResult('cancelled')
            if target is None or not target.verifiable:
                return ClipboardResult('target_unverifiable')
            backend = self._native()
            self._check_recovery(backend)
            if backend.capture_target() != target:
                return ClipboardResult('target_changed')
            if target.control_class not in self._approved:
                return ClipboardResult('target_unverified')
            if backend.modifiers_down():
                return ClipboardResult('modifiers_active')
            snapshot = backend.snapshot(self.snapshot_budget)
            owned_sequence = backend.stage(formats, snapshot.sequence)
            transaction = ClipboardTransaction(uuid.uuid4().hex, owned_sequence, target)
            # The adapter rechecks sequence/transaction, target and generation
            # while holding the clipboard lock immediately before SendInput.
            backend.commit_paste(owned_sequence, target, still_current, authorize, transaction)
            submitted = True
            backend.sleep(self._approved[target.control_class])
            restored = self._restore(backend, snapshot, owned_sequence)
            owned_sequence = None
            return ClipboardResult('submitted', submitted=True, restored=restored)
        except ClipboardFailure as failure:
            submitted = submitted or failure.submitted
            if failure.owned_sequence is not None:
                owned_sequence = failure.owned_sequence
            if submitted and owned_sequence is not None:
                backend.sleep(self._approved[target.control_class])
            return ClipboardResult(failure.status, submitted=submitted)
        finally:
            try:
                if snapshot is not None and owned_sequence is not None:
                    try:
                        self._restore(self.backend, snapshot, owned_sequence)
                    except ClipboardFailure as failure:
                        raise ClipboardFailure(failure.status, submitted=submitted) from None
            finally:
                self._lock.release()

    def copy(self, text: str) -> ClipboardResult:
        if not self._lock.acquire(blocking=False):
            return ClipboardResult('clipboard_busy')
        try:
            self._native().replace(self._text_formats(text))
            self._pending_restore = None  # Explicit copy intentionally replaces it.
            return ClipboardResult('copied')
        except ClipboardFailure as failure:
            return ClipboardResult(failure.status)
        finally:
            self._lock.release()

    def close(self):
        with self._lock:
            if self._pending_restore is not None:
                snapshot, sequence = self._pending_restore
                self._restore(self.backend, snapshot, sequence)
                self._pending_restore = None
            if self.backend is not None and hasattr(self.backend, 'close'):
                self.backend.close()

    def recover(self) -> ClipboardResult:
        with self._lock:
            if self._pending_restore is None:
                return ClipboardResult('no_recovery')
            snapshot, sequence = self._pending_restore
            try:
                restored = self._restore(self.backend, snapshot, sequence)
                self._pending_restore = None
                return ClipboardResult('restored' if restored else 'clipboard_changed', restored=restored)
            except ClipboardFailure as failure:
                return ClipboardResult(failure.status)


class _GuiThreadInfo(ctypes.Structure):
    _fields_ = [('cbSize', W.DWORD), ('flags', W.DWORD), ('hwndActive', W.HWND),
                ('hwndFocus', W.HWND), ('hwndCapture', W.HWND), ('hwndMenuOwner', W.HWND),
                ('hwndMoveSize', W.HWND), ('hwndCaret', W.HWND), ('rcCaret', W.RECT)]


class _KeyInput(ctypes.Structure):
    _fields_ = [('wVk', W.WORD), ('wScan', W.WORD), ('dwFlags', W.DWORD),
                ('time', W.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class _MouseInput(ctypes.Structure):
    _fields_ = [('dx', W.LONG), ('dy', W.LONG), ('mouseData', W.DWORD),
                ('dwFlags', W.DWORD), ('time', W.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class _InputUnion(ctypes.Union):
    _fields_ = [('ki', _KeyInput), ('mi', _MouseInput)]


class _Input(ctypes.Structure):
    _anonymous_ = ('data',)
    _fields_ = [('type', W.DWORD), ('data', _InputUnion)]


class NativeClipboard:
    def __init__(self):
        if sys.platform != 'win32':
            raise ClipboardFailure('unsupported')
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        for name, arguments, result in (
            ('OpenClipboard', [W.HWND], W.BOOL), ('CloseClipboard', [], W.BOOL),
            ('EmptyClipboard', [], W.BOOL), ('EnumClipboardFormats', [W.UINT], W.UINT),
            ('GetClipboardData', [W.UINT], W.HANDLE), ('SetClipboardData', [W.UINT, W.HANDLE], W.HANDLE),
            ('GetClipboardSequenceNumber', [], W.DWORD), ('GetClipboardOwner', [], W.HWND),
            ('RegisterClipboardFormatW', [W.LPCWSTR], W.UINT),
            ('GetForegroundWindow', [], W.HWND), ('GetGUIThreadInfo', [W.DWORD, ctypes.POINTER(_GuiThreadInfo)], W.BOOL),
            ('GetWindowThreadProcessId', [W.HWND, ctypes.POINTER(W.DWORD)], W.DWORD),
            ('GetClassNameW', [W.HWND, W.LPWSTR, ctypes.c_int], ctypes.c_int),
            ('GetWindowLongPtrW', [W.HWND, ctypes.c_int], ctypes.c_ssize_t),
            ('SendMessageTimeoutW', [W.HWND, W.UINT, W.WPARAM, W.LPARAM, W.UINT, W.UINT,
                                     ctypes.POINTER(ctypes.c_size_t)], ctypes.c_ssize_t),
            ('GetAsyncKeyState', [ctypes.c_int], W.SHORT),
            ('SendInput', [W.UINT, ctypes.POINTER(_Input), ctypes.c_int], W.UINT),
            ('CreateWindowExW', [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID], W.HWND),
            ('DestroyWindow', [W.HWND], W.BOOL),
            ('GetMessageW', [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT], ctypes.c_int),
            ('PostThreadMessageW', [W.DWORD, W.UINT, W.WPARAM, W.LPARAM], W.BOOL),
            ('TranslateMessage', [ctypes.POINTER(W.MSG)], W.BOOL),
            ('DispatchMessageW', [ctypes.POINTER(W.MSG)], ctypes.c_ssize_t),
        ):
            function = getattr(self.user, name)
            function.argtypes, function.restype = arguments, result
        for name, arguments, result in (
            ('GlobalSize', [W.HGLOBAL], ctypes.c_size_t),
            ('GlobalLock', [W.HGLOBAL], W.LPVOID), ('GlobalUnlock', [W.HGLOBAL], W.BOOL),
            ('GlobalAlloc', [W.UINT, ctypes.c_size_t], W.HGLOBAL), ('GlobalFree', [W.HGLOBAL], W.HGLOBAL),
            ('OpenProcess', [W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
            ('GetProcessTimes', [W.HANDLE, ctypes.POINTER(W.FILETIME), ctypes.POINTER(W.FILETIME),
                                 ctypes.POINTER(W.FILETIME), ctypes.POINTER(W.FILETIME)], W.BOOL),
            ('CloseHandle', [W.HANDLE], W.BOOL), ('GetCurrentThreadId', [], W.DWORD),
        ):
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result
        self.allowed = {1, 7, 8, 13, 15, 16, 17}
        for name in ('HTML Format', 'Rich Text Format'):
            identity = self.user.RegisterClipboardFormatW(name)
            if not identity:
                raise ClipboardFailure('clipboard_failed')
            self.allowed.add(identity)
        self.tx_format = self.user.RegisterClipboardFormatW('Hugin.Private.ClipboardTransaction.v1')
        if not self.tx_format:
            raise ClipboardFailure('clipboard_failed')
        self.hwnd = None
        self._owner_thread = None
        self._owner_thread_id = 0
        self._owner_ready = threading.Event()
        self._owner_failed = False
        self._token: bytes | None = None
        self._unfreed: set[int] = set()

    def _window_loop(self):
        try:
            self._owner_thread_id = self.kernel.GetCurrentThreadId()
            self.hwnd = self.user.CreateWindowExW(0, 'STATIC', '', 0, 0, 0, 0, 0, -3, None, None, None)
            if not self.hwnd:
                raise ClipboardFailure('clipboard_failed')
            self._owner_ready.set()
            message = W.MSG()
            while True:
                result = self.user.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result <= 0:
                    if result < 0:
                        self._owner_failed = True
                    break
                self.user.TranslateMessage(ctypes.byref(message))
                self.user.DispatchMessageW(ctypes.byref(message))
        except Exception:
            self._owner_failed = True
        finally:
            if self.hwnd:
                if self.user.DestroyWindow(self.hwnd):
                    self.hwnd = None
                else:
                    self._owner_failed = True
            self._owner_ready.set()

    def _ensure_window(self):
        if self._owner_thread is None:
            self._owner_thread = threading.Thread(target=self._window_loop, name='hugin-clipboard-owner', daemon=True)
            self._owner_thread.start()
        if not self._owner_ready.wait(2) or self._owner_failed or not self.hwnd:
            raise ClipboardFailure('clipboard_failed')

    @contextmanager
    def _opened(self, write=False):
        if write:
            self._ensure_window()
        deadline = time.monotonic() + 0.25
        while not self.user.OpenClipboard(self.hwnd if write else None):
            if time.monotonic() >= deadline:
                raise ClipboardFailure('clipboard_busy')
            time.sleep(0.005)
        try:
            yield
        finally:
            if not self.user.CloseClipboard():
                raise ClipboardFailure('clipboard_failed')

    def sequence(self):
        return self.user.GetClipboardSequenceNumber()

    def _read_handle(self, handle, size):
        pointer = self.kernel.GlobalLock(handle)
        if not pointer:
            raise ClipboardFailure('format_delayed')
        try:
            return ctypes.string_at(pointer, size)
        finally:
            ctypes.set_last_error(0)
            if not self.kernel.GlobalUnlock(handle) and ctypes.get_last_error():
                raise ClipboardFailure('clipboard_failed')

    def snapshot(self, budget):
        with self._opened():
            sequence = self.sequence()
            identities = []
            previous = 0
            while True:
                ctypes.set_last_error(0)
                identity = self.user.EnumClipboardFormats(previous)
                if not identity:
                    if ctypes.get_last_error():
                        raise ClipboardFailure('clipboard_failed')
                    break
                if len(identities) >= 256 or identity in identities:
                    raise ClipboardFailure('format_unsupported')
                identities.append(identity)
                previous = identity
            # Windows synthesizes CF_BITMAP for a DIB. Preserve the source
            # DIB bytes rather than misinterpreting a GDI handle as HGLOBAL.
            if 8 in identities or 17 in identities:
                identities = [identity for identity in identities if identity != 2]
            if any(identity not in self.allowed for identity in identities):
                raise ClipboardFailure('format_unsupported')
            handles = []
            total = 0
            for identity in identities:
                handle = self.user.GetClipboardData(identity)
                size = self.kernel.GlobalSize(handle) if handle else 0
                if not size or self.sequence() != sequence:
                    raise ClipboardFailure('format_delayed')
                total += size
                if total > budget:
                    raise ClipboardFailure('snapshot_limit')
                handles.append((identity, handle, size))
            formats = tuple((identity, self._read_handle(handle, size)) for identity, handle, size in handles)
            if self.sequence() != sequence:
                raise ClipboardFailure('clipboard_changed')
            return ClipboardSnapshot(sequence, formats)

    def _allocate(self, data):
        handle = self.kernel.GlobalAlloc(2, len(data))  # GMEM_MOVEABLE
        if not handle:
            raise ClipboardFailure('clipboard_failed')
        pointer = self.kernel.GlobalLock(handle)
        if not pointer:
            if self.kernel.GlobalFree(handle):
                self._unfreed.add(handle)
            raise ClipboardFailure('clipboard_failed')
        ctypes.memmove(pointer, data, len(data))
        ctypes.set_last_error(0)
        if not self.kernel.GlobalUnlock(handle) and ctypes.get_last_error():
            if self.kernel.GlobalFree(handle):
                self._unfreed.add(handle)
            raise ClipboardFailure('clipboard_failed')
        return handle

    def replace(self, formats, expected=None):
        # All fallible allocations precede destructive EmptyClipboard.
        handles = []
        mutated = False
        last_owned_sequence = None
        try:
            for identity, data in formats:
                handles.append([identity, self._allocate(data)])
            with self._opened(write=True):
                if expected is not None and self.sequence() != expected:
                    raise ClipboardFailure('clipboard_changed')
                if not self.user.EmptyClipboard():
                    raise ClipboardFailure('clipboard_failed')
                mutated = True
                last_owned_sequence = self.sequence()
                for item in handles:
                    if not self.user.SetClipboardData(item[0], item[1]):
                        raise ClipboardFailure('clipboard_write_failed')
                    item[1] = None  # Ownership transferred only after success.
                    last_owned_sequence = self.sequence()
                return last_owned_sequence
        except ClipboardFailure as failure:
            if mutated:
                # Ownership is retained even when SetClipboardData partially
                # failed. The service still owns the original full snapshot.
                failure.owned_sequence = last_owned_sequence
            raise
        finally:
            failed = False
            for _, handle in handles:
                if handle:
                    if self.kernel.GlobalFree(handle):
                        self._unfreed.add(handle)
                        failed = True
            if failed:
                raise ClipboardFailure('clipboard_cleanup_failed',
                                       owned_sequence=last_owned_sequence)

    def stage(self, formats, expected):
        self._token = uuid.uuid4().hex.encode('ascii')
        return self.replace((*formats, (self.tx_format, self._token)), expected)

    def capture_target(self):
        hwnd = self.user.GetForegroundWindow()
        pid = W.DWORD()
        thread = self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)) if hwnd else 0
        info = _GuiThreadInfo(cbSize=ctypes.sizeof(_GuiThreadInfo))
        if not thread or not self.user.GetGUIThreadInfo(thread, ctypes.byref(info)) or not info.hwndFocus:
            raise ClipboardFailure('target_unverifiable')
        focus_pid = W.DWORD()
        self.user.GetWindowThreadProcessId(info.hwndFocus, ctypes.byref(focus_pid))
        if focus_pid.value != pid.value:
            raise ClipboardFailure('target_unverifiable')
        process = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not process:
            raise ClipboardFailure('target_unverifiable')
        try:
            created, exited, kernel, user = W.FILETIME(), W.FILETIME(), W.FILETIME(), W.FILETIME()
            if not self.kernel.GetProcessTimes(process, ctypes.byref(created), ctypes.byref(exited),
                                               ctypes.byref(kernel), ctypes.byref(user)):
                raise ClipboardFailure('target_unverifiable')
            creation = created.dwLowDateTime | (created.dwHighDateTime << 32)
        finally:
            if not self.kernel.CloseHandle(process):
                raise ClipboardFailure('clipboard_failed')
        name = ctypes.create_unicode_buffer(256)
        if not self.user.GetClassNameW(info.hwndFocus, name, len(name)):
            raise ClipboardFailure('target_unverifiable')
        caret = None
        selection = None
        editable = True
        if info.hwndCaret:
            rect = info.rcCaret
            caret = (int(info.hwndCaret), rect.left, rect.top, rect.right, rect.bottom)
        if name.value.lower() == 'edit' or name.value.lower().startswith('richedit'):
            ctypes.set_last_error(0)
            style = self.user.GetWindowLongPtrW(info.hwndFocus, -16)
            if not style and ctypes.get_last_error():
                raise ClipboardFailure('target_unverifiable')
            if style & 0x20:  # never read password controls
                raise ClipboardFailure('target_unverifiable')
            editable = not bool(style & 0x800)
            start, end, result = W.DWORD(), W.DWORD(), ctypes.c_size_t()
            ok = self.user.SendMessageTimeoutW(info.hwndFocus, 0xB0, ctypes.addressof(start),
                                               ctypes.addressof(end), 0x23, 50, ctypes.byref(result))
            if ok:
                selection = (start.value, end.value)
        return WindowTarget(int(hwnd), int(info.hwndFocus), pid.value, thread, creation,
                            name.value, caret, selection, editable)

    def read_direct_selection(self, target, limit, cancelled):
        """Standard Edit uses system-marshaled WM messages, without clipboard.

        Custom/RichEdit/Browser providers need their own proven read boundary.
        Whole-control UTF-16 is bounded before allocation; only the selected
        range survives this call. EM_GETSEL offsets are UTF-16 code units.
        """
        if target.control_class.lower() != 'edit' or target.selection is None:
            return None
        if cancelled():
            raise ClipboardFailure('cancelled')
        if self.capture_target() != target:
            raise ClipboardFailure('target_changed')
        start, end = target.selection
        if start == end:
            return ''
        result = ctypes.c_size_t()
        if not self.user.SendMessageTimeoutW(target.focus, 0xE, 0, 0, 0x23, 50, ctypes.byref(result)):
            raise ClipboardFailure('target_unverifiable')
        length = result.value
        if length > limit or start < 0 or end < start or end > length:
            raise ClipboardFailure('text_limit')
        buffer = ctypes.create_unicode_buffer(length + 1)
        if cancelled():
            raise ClipboardFailure('cancelled')
        if not self.user.SendMessageTimeoutW(target.focus, 0xD, length + 1, ctypes.addressof(buffer),
                                             0x23, 50, ctypes.byref(result)):
            raise ClipboardFailure('target_unverifiable')
        if result.value > length or end > result.value:
            raise ClipboardFailure('target_changed')
        if cancelled():
            raise ClipboardFailure('cancelled')
        if self.capture_target() != target:
            raise ClipboardFailure('target_changed')
        data = ctypes.string_at(ctypes.addressof(buffer) + start * 2, (end - start) * 2)
        try:
            text = data.decode('utf-16-le')
            if len(text.encode('utf-8')) > limit:
                raise ClipboardFailure('text_limit')
            return text
        except UnicodeError:
            raise ClipboardFailure('text_invalid') from None

    def modifiers_down(self):
        return any(self.user.GetAsyncKeyState(key) & 0x8000 for key in (0x10, 0x11, 0x12, 0x5B, 0x5C))

    def _chord(self, key):
        events = [(0x11, 0), (key, 0), (key, 2), (0x11, 2)]
        inputs = (_Input * len(events))(*(_Input(type=1, ki=_KeyInput(wVk=vk, dwFlags=flags))
                                           for vk, flags in events))
        sent = self.user.SendInput(len(inputs), inputs, ctypes.sizeof(_Input))
        if sent != len(inputs):
            held = set()
            for vk, flags in events[:sent]:
                if flags & 2:
                    held.discard(vk)
                else:
                    held.add(vk)
            if held:
                releases = (_Input * len(held))(*(_Input(type=1, ki=_KeyInput(wVk=vk, dwFlags=2)) for vk in held))
                if self.user.SendInput(len(releases), releases, ctypes.sizeof(_Input)) != len(releases):
                    raise ClipboardFailure('modifier_release_failed', submitted=key == 0x56 and sent >= 2)
            raise ClipboardFailure('input_partial', submitted=key == 0x56 and sent >= 2)

    def copy_selection(self, target):
        if self.capture_target() != target:
            raise ClipboardFailure('target_changed')
        if self.modifiers_down():
            raise ClipboardFailure('modifiers_active')
        self._chord(0x43)

    def read_selection(self, expected, target, limit):
        with self._opened():
            if self.sequence() != expected:
                raise ClipboardFailure('clipboard_changed')
            owner = self.user.GetClipboardOwner()
            owner_pid = W.DWORD()
            if not owner:
                raise ClipboardFailure('clipboard_changed')
            self.user.GetWindowThreadProcessId(owner, ctypes.byref(owner_pid))
            if owner_pid.value != target.pid:
                raise ClipboardFailure('clipboard_changed')
            handle = self.user.GetClipboardData(CF_UNICODETEXT)
            size = self.kernel.GlobalSize(handle) if handle else 0
            if not size:
                raise ClipboardFailure('selection_empty')
            if size > 2 * limit + 2 or size % 2:
                raise ClipboardFailure('text_limit')
            data = self._read_handle(handle, size)
            if self.sequence() != expected:
                raise ClipboardFailure('clipboard_changed')
            try:
                text = data.decode('utf-16-le').split('\0', 1)[0]
                if len(text.encode('utf-8')) > limit:
                    raise ClipboardFailure('text_limit')
                return text
            except UnicodeError:
                raise ClipboardFailure('text_invalid') from None

    def commit_paste(self, expected, target, still_current, authorize=None, transaction=None):
        submitted = False
        try:
            with self._opened():
                if self.sequence() != expected or self.user.GetClipboardOwner() != self.hwnd:
                    raise ClipboardFailure('clipboard_changed')
                token_handle = self.user.GetClipboardData(self.tx_format)
                size = self.kernel.GlobalSize(token_handle) if token_handle else 0
                if size != len(self._token or b'') or not size or self._read_handle(token_handle, size) != self._token:
                    raise ClipboardFailure('clipboard_changed')
                if self.capture_target() != target:
                    raise ClipboardFailure('target_changed')
                if self.modifiers_down():
                    raise ClipboardFailure('modifiers_active')
                if not still_current():
                    raise ClipboardFailure('cancelled')
                if authorize is not None and not authorize(transaction):
                    raise ClipboardFailure('commit_rejected')
                self._chord(0x56)
                submitted = True
        except ClipboardFailure as failure:
            failure.submitted = failure.submitted or submitted
            raise

    @staticmethod
    def sleep(seconds):
        time.sleep(seconds)

    def close(self):
        for handle in tuple(self._unfreed):
            if not self.kernel.GlobalFree(handle):
                self._unfreed.remove(handle)
        if self._unfreed:
            raise ClipboardFailure('clipboard_cleanup_failed')
        if self._owner_thread is not None and self._owner_thread.is_alive():
            if not self.user.PostThreadMessageW(self._owner_thread_id, 0x12, 0, 0):
                raise ClipboardFailure('clipboard_failed')
            self._owner_thread.join(2)
            if self._owner_thread.is_alive() or self._owner_failed:
                raise ClipboardFailure('clipboard_cleanup_failed')
