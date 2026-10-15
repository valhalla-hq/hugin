"""Serialized, bounded clipboard transactions with explicit conflict outcomes.

Capture fallback and delivery policy are explicitly configured. Delivery may use
verified native/UIA field capabilities; SendInput does not prove app consumption.
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
import ctypes
from ctypes import wintypes as W
from dataclasses import dataclass, replace
import math
import sys
import threading
import time
import uuid

MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024
MAX_TEXT_BYTES = 256 * 1024
CF_UNICODETEXT = 13
NATIVE_EDIT_CLASSES = frozenset(('edit','richedit','richedit20a','richedit20w','richedit50w'))


class ClipboardFailure(Exception):
    def __init__(self, status: str, *, submitted=False, owned_sequence=None):
        self.status = status
        self.submitted = submitted
        self.owned_sequence = owned_sequence
        super().__init__(status)


@dataclass(frozen=True)
class UiaTargetIdentity:
    focus_id: tuple[int, ...]
    root_id: tuple[int, ...]
    start_id: tuple[int, ...]
    end_id: tuple[int, ...]
    focus_pid: int
    selection: tuple[int, int]  # Ordered UTF-16 prefixes in the focused field.
    start_relation: int  # Each endpoint relative to DocumentRange.End.
    end_relation: int

    def __post_init__(self):
        for parts in (self.focus_id,self.root_id,self.start_id,self.end_id):
            if type(parts) is not tuple or not 0<len(parts)<=64 or any(
                    type(part) is not int or not -(1<<31)<=part<1<<31 for part in parts):
                raise ValueError('invalid UIA runtime identity')
        if type(self.focus_pid) is not int or not 0<self.focus_pid<1<<32:
            raise ValueError('invalid UIA focus process')
        if (type(self.selection) is not tuple or len(self.selection)!=2
                or any(type(point) is not int for point in self.selection)
                or not 0<=self.selection[0]<=self.selection[1]<=MAX_TEXT_BYTES):
            raise ValueError('invalid UIA selection')
        for relation in (self.start_relation,self.end_relation):
            if type(relation) is not int or relation not in (-1,0,1):
                raise ValueError('invalid UIA endpoint relation')
        if self.start_relation>self.end_relation:
            raise ValueError('inverted UIA endpoint relation')
        if self.selection[0]==self.selection[1] and (self.start_id!=self.end_id or self.start_relation!=self.end_relation):
            raise ValueError('ambiguous UIA collapsed selection')


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
    native_editable: bool = False
    uia: UiaTargetIdentity | None = None
    package_family: str | None = None

    @property
    def without_uia(self):
        return replace(self,uia=None) if self.uia is not None else self

    @property
    def verifiable(self):
        return bool(self.hwnd and self.focus and self.process_created and
                    ((self.native_editable is True and self.caret is not None and self.selection is not None)
                     or isinstance(self.uia,UiaTargetIdentity)))


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
        self._approved: dict[tuple[str,str|None], float] = {}
        self._verified_edit_delay: float | None = None
        self._capture_approved: set[str] = set()
        self._pending_restore: tuple[ClipboardSnapshot, int] | None = None

    @property
    def recovery_pending(self):
        return self._pending_restore is not None

    def _check_recovery(self, backend):
        if self._pending_restore is not None:
            snapshot,sequence=self._pending_restore
            current=backend.restorable_sequence(sequence)
            if current is None:
                self._pending_restore = None  # A proven later user copy has priority.
            else:
                self._pending_restore=(snapshot,current)
                raise ClipboardFailure('clipboard_recovery_pending')

    def _native(self):
        if self.backend is None:
            self.backend = NativeClipboard()
        return self.backend

    def approve_target_class(self, control_class: str, restore_delay: float,*,package_family=None):
        """Caller must have explicit pilot proof for this class and delay."""
        if not isinstance(control_class, str) or not control_class or not 0.02 <= restore_delay <= 2:
            raise ValueError('invalid pilot approval')
        if package_family is not None and (not isinstance(package_family,str) or not 17<=len(package_family)<=64 or '\0' in package_family):
            raise ValueError('invalid package family approval')
        self._approved[control_class,package_family] = restore_delay

    def _restore_delay(self,target):
        scoped=self._approved.get((target.control_class,target.package_family))
        if scoped is not None:return scoped
        unscoped=self._approved.get((target.control_class,None))
        if unscoped is not None:return unscoped
        return self._verified_edit_delay if target.verifiable else None

    def approve_verified_edits(self, restore_delay: float):
        """Internal policy seam; adapters must prove the focused editable field."""
        if type(restore_delay) not in (int,float) or not .02<=restore_delay<=2 or not math.isfinite(restore_delay):
            raise ValueError('invalid verified edit approval')
        self._verified_edit_delay=float(restore_delay)

    def approve_capture_target_class(self, control_class: str):
        """Internal pilot seam; includes the copy-response attribution limit."""
        if not isinstance(control_class, str) or not control_class:
            raise ValueError('invalid capture pilot approval')
        self._capture_approved.add(control_class)

    def capture_native_target(self) -> ClipboardResult:
        """Fast Win32 facts only; this does not assert delivery verifiability."""
        if not self._lock.acquire(blocking=False):
            return ClipboardResult('clipboard_busy')
        try:
            backend=self._native()
            return ClipboardResult('native_target_captured',target=backend.capture_native_target())
        except ClipboardFailure as failure:
            return ClipboardResult(failure.status)
        finally:self._lock.release()

    @staticmethod
    def _selection_target(backend):
        return backend.capture_native_target()

    def capture_target(self,*,expected=None,cancelled=lambda:False) -> ClipboardResult:
        if not self._lock.acquire(blocking=False):
            return ClipboardResult('clipboard_busy')
        try:
            if cancelled():return ClipboardResult('cancelled')
            target = self._native().capture_target(expected=expected,cancelled=cancelled)
            if expected is not None and target.without_uia!=expected.without_uia:
                return ClipboardResult('target_changed')
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
        current=sequence
        try:
            current=backend.restorable_sequence(sequence)
            if current is None:
                self._pending_restore=None
                return False
            backend.replace(snapshot.formats,current)
            self._pending_restore = None
            return True
        except ClipboardFailure as failure:
            owned=failure.owned_sequence if failure.owned_sequence is not None else current
            if failure.status == 'clipboard_changed':
                try:
                    observed=backend.restorable_sequence(owned)
                    if observed is None:
                        self._pending_restore=None
                        return False
                    owned=observed
                except ClipboardFailure:
                    pass  # Unknown publication retains the original RAM snapshot.
            self._pending_restore = (snapshot,owned)
            raise ClipboardFailure('clipboard_restore_failed',owned_sequence=owned) from None

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
            target = self._selection_target(backend)
            if hasattr(backend, 'read_direct_selection'):
                text = backend.read_direct_selection(target, MAX_TEXT_BYTES, cancelled)
                if cancelled():
                    return ClipboardResult('cancelled')
                if self._selection_target(backend) != target:
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
            if self._selection_target(backend) != target:
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
            if self._selection_target(backend) != target:
                return ClipboardResult('target_changed')
            backend.copy_selection(target)
            deadline = time.monotonic() + self.selection_timeout
            while time.monotonic() < deadline:
                if cancelled():
                    return ClipboardResult('cancelled')
                if self._selection_target(backend) != target:
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
                authorize: Callable[[ClipboardTransaction], bool] | None = None,
                commit=None) -> ClipboardResult:
        try:
            return self._deliver(text, target, still_current, authorize,commit)
        except ClipboardFailure as failure:
            return ClipboardResult(failure.status, submitted=failure.submitted)

    def _deliver(self, text: str, target: WindowTarget | None,
                 still_current: Callable[[], bool], authorize,commit) -> ClipboardResult:
        if not self._lock.acquire(blocking=False):
            return ClipboardResult('clipboard_busy')
        snapshot = None
        owned_sequence = None
        submitted = False
        restore_delay=None
        try:
            formats = self._text_formats(text)
            if not still_current():
                return ClipboardResult('cancelled')
            if target is None or not target.verifiable:
                return ClipboardResult('target_unverifiable')
            backend = self._native()
            self._check_recovery(backend)
            # Field policy and cheap native identity precede clipboard mutation.
            # The one expensive UIA refresh happens only in commit_paste.
            if self._selection_target(backend).without_uia != target.without_uia:
                return ClipboardResult('target_changed')
            restore_delay=self._restore_delay(target)
            if restore_delay is None:
                return ClipboardResult('target_unverified')
            if backend.modifiers_down():
                return ClipboardResult('modifiers_active')
            snapshot = backend.snapshot(self.snapshot_budget)
            owned_sequence = backend.stage(formats, snapshot.sequence)
            transaction = ClipboardTransaction(uuid.uuid4().hex, owned_sequence, target)
            # The adapter rechecks sequence/transaction, target and generation
            # while holding the clipboard lock immediately before SendInput.
            if commit is None:
                backend.commit_paste(owned_sequence, target, still_current, authorize, transaction)
            else:
                backend.commit_paste(owned_sequence,target,still_current,authorize,transaction,commit=commit)
            submitted = True
            backend.sleep(restore_delay)
            restored = self._restore(backend, snapshot, owned_sequence)
            owned_sequence = None
            return ClipboardResult('submitted', submitted=True, restored=restored)
        except ClipboardFailure as failure:
            submitted = submitted or failure.submitted
            if failure.owned_sequence is not None:
                owned_sequence = failure.owned_sequence
            if submitted and owned_sequence is not None:
                backend.sleep(restore_delay)
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
            ('IsWindowEnabled', [W.HWND], W.BOOL),
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
        family=getattr(self.kernel,'GetPackageFamilyName',None)
        if family is not None:
            family.argtypes=[W.HANDLE,ctypes.POINTER(W.UINT),W.LPWSTR]
            family.restype=W.LONG
        self.allowed = {1, 7, 8, 13, 15, 16, 17}
        # Chromium publishes these two provenance formats as HGLOBAL bytes.
        # Preserve them opaquely; an arbitrary registered format may instead
        # contain an object/stream and still must fail before materialization.
        for name in ('HTML Format', 'Rich Text Format',
                     'Chromium internal source RFH token', 'Chromium internal source URL'):
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
        self._selection_probe = None

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

    def restorable_sequence(self,expected):
        # Our message-only HWND is held for this backend's lifetime, and the
        # service serializes its writers. Windows may add implicit formats on
        # CloseClipboard without changing this owner. Never claim a later
        # foreign sequence, or confuse an unstable observation with its loss.
        before=self.sequence()
        ctypes.set_last_error(0)
        owner=self.user.GetClipboardOwner()
        error=ctypes.get_last_error()
        after=self.sequence()
        if not before or before!=after or (not owner and error):
            raise ClipboardFailure('clipboard_busy')
        if after==expected:return after
        if not owner:raise ClipboardFailure('clipboard_busy')
        return after if self.hwnd and owner==self.hwnd else None

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
            published=self.restorable_sequence(last_owned_sequence)
            if published is None:raise ClipboardFailure('clipboard_changed')
            return published
        except ClipboardFailure as failure:
            if mutated:
                # Ownership is retained even when SetClipboardData partially
                # failed. The service still owns the original full snapshot.
                try:
                    published=self.restorable_sequence(last_owned_sequence)
                    if published is not None:last_owned_sequence=published
                except ClipboardFailure:
                    pass  # The service retains unknown own publication for retry.
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

    def _package_family(self,process):
        query=getattr(self.kernel,'GetPackageFamilyName',None)
        if query is None:return None
        length=W.UINT()
        # AppModel family names are at most 64 WCHARs plus their terminator.
        if query(process,ctypes.byref(length),None)!=122 or not 18<=length.value<=65:
            return None
        capacity=length.value;buffer=ctypes.create_unicode_buffer(capacity)
        if query(process,ctypes.byref(length),buffer)!=0 or not 18<=length.value<=capacity:
            return None
        value=buffer.value
        return value if len(value)+1==length.value else None

    def _native_edit_style(self,focus):
        ctypes.set_last_error(0)
        style=self.user.GetWindowLongPtrW(focus,-16)
        if (not style and ctypes.get_last_error()) or style & 0x20:
            raise ClipboardFailure('target_unverifiable')
        return style

    def capture_native_target(self):
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
            package_family=self._package_family(process)
        finally:
            if not self.kernel.CloseHandle(process):
                raise ClipboardFailure('clipboard_failed')
        name = ctypes.create_unicode_buffer(256)
        if not self.user.GetClassNameW(info.hwndFocus, name, len(name)):
            raise ClipboardFailure('target_unverifiable')
        caret = None
        selection = None
        native_editable = False
        if info.hwndCaret:
            rect = info.rcCaret
            caret = (int(info.hwndCaret), rect.left, rect.top, rect.right, rect.bottom)
        if name.value.lower() in NATIVE_EDIT_CLASSES:
            self._native_edit_style(info.hwndFocus)  # Never query password fields.
            start, end, result = W.DWORD(), W.DWORD(), ctypes.c_size_t()
            ok = self.user.SendMessageTimeoutW(info.hwndFocus, 0xB0, ctypes.addressof(start),
                                               ctypes.addressof(end), 0x23, 50, ctypes.byref(result))
            if ok and start.value <= end.value:
                selection = (start.value, end.value)
                style=self._native_edit_style(info.hwndFocus)
                native_editable = bool(self.user.IsWindowEnabled(info.hwndFocus)
                    and not style & 0x800 and info.hwndCaret==info.hwndFocus)
        return WindowTarget(int(hwnd), int(info.hwndFocus), pid.value, thread, creation,
                            name.value, caret, selection, native_editable,package_family=package_family)

    def capture_target(self,*,expected=None,cancelled=lambda:False):
        """Complete delivery proof; call off the controller/audio owner.

        The child probe calls capture_native_target only. UIA facts never
        recursively supplement themselves or reinterpret the native basis.
        """
        if cancelled():raise ClipboardFailure('cancelled')
        base=self.capture_native_target()
        if expected is not None and base!=expected.without_uia:
            raise ClipboardFailure('target_changed')
        if base.verifiable:return base
        result=self._probe().capture_target(base,cancelled)
        if cancelled():raise ClipboardFailure('cancelled')
        if self.capture_native_target()!=base:raise ClipboardFailure('target_changed')
        if result.status=='target_unverifiable':return base
        if result.status!='target_captured':raise ClipboardFailure(result.status)
        if result.identity is None:raise ClipboardFailure('target_unverifiable')
        return replace(base,uia=result.identity)

    def _probe(self):
        if self._selection_probe is None:
            from hugin.windows.selection import SelectionProbe
            self._selection_probe=SelectionProbe()
        return self._selection_probe

    def read_direct_selection(self, target, limit, cancelled):
        """Standard Edit uses system-marshaled WM messages, without clipboard.

        Custom/RichEdit/Browser providers need their own proven read boundary.
        Whole-control UTF-16 is bounded before allocation; only the selected
        range survives this call. EM_GETSEL offsets are UTF-16 code units.
        """
        if target.control_class.lower() != 'edit' or target.selection is None:
            result = self._probe().read(target, cancelled)
            if result.status == 'captured':
                return result.text
            if result.status == 'selection_empty':
                return ''
            if result.status == 'selection_unsupported':
                return None  # Clipboard fallback still requires class approval.
            raise ClipboardFailure(result.status)
        if cancelled():
            raise ClipboardFailure('cancelled')
        if self.capture_native_target() != target:
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
        if self.capture_native_target() != target:
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
        if self.capture_native_target() != target:
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

    def commit_paste(self, expected, target, still_current, authorize=None, transaction=None,commit=None):
        submitted = False
        active=False;attempted=False;gate=threading.Lock();lease=None
        try:
            with self._opened():
                try:
                    if self.sequence()!=expected or self.user.GetClipboardOwner()!=self.hwnd:
                        raise ClipboardFailure('clipboard_changed')
                    token_handle=self.user.GetClipboardData(self.tx_format)
                    size=self.kernel.GlobalSize(token_handle) if token_handle else 0
                    if size!=len(self._token or b'') or not size or self._read_handle(token_handle,size)!=self._token:
                        raise ClipboardFailure('clipboard_changed')
                    if target.uia is not None:
                        lease=self._probe().begin_delivery(target.without_uia,lambda:not still_current())
                        if lease.result.status!='target_captured':raise ClipboardFailure(lease.result.status)
                        if lease.result.identity!=target.uia:raise ClipboardFailure('target_changed')
                    active=True
                    def fast_commit():
                        nonlocal submitted,attempted
                        with gate:
                            if not active or attempted:raise ClipboardFailure('commit_rejected')
                            attempted=True
                            if lease is not None:
                                if not still_current():raise ClipboardFailure('cancelled')
                                confirmed=lease.confirm()  # Private IPC only; hard <=50ms.
                                if confirmed.status!='target_captured':raise ClipboardFailure(confirmed.status)
                                if confirmed.identity!=target.uia:raise ClipboardFailure('target_changed')
                            # The worker still holds OpenClipboard and this
                            # token HGLOBAL. Recheck it on the input owner
                            # without a cross-thread GetClipboardData/open.
                            if (self.sequence()!=expected or self.user.GetClipboardOwner()!=self.hwnd
                                    or self.kernel.GlobalSize(token_handle)!=size
                                    or self._read_handle(token_handle,size)!=self._token):
                                raise ClipboardFailure('clipboard_changed')
                            if self.capture_native_target()!=target.without_uia:raise ClipboardFailure('target_changed')
                            if self.modifiers_down():raise ClipboardFailure('modifiers_active')
                            if not still_current():raise ClipboardFailure('cancelled')
                            if authorize is not None and not authorize(transaction):raise ClipboardFailure('commit_rejected')
                            self._chord(0x56);submitted=True
                    if commit is None:fast_commit()
                    else:commit(transaction,fast_commit)
                    if not submitted:raise ClipboardFailure('commit_rejected')
                finally:
                    with gate:
                        active=False
                        # Saved rejected closures must not retain effect.text
                        # indirectly through application callbacks/transaction.
                        still_current=authorize=transaction=None
                    if lease is not None:
                        owned_lease=lease
                        with gate:lease=None
                        owned_lease.close()
        except ClipboardFailure as failure:
            failure.submitted = failure.submitted or submitted
            raise

    @staticmethod
    def sleep(seconds):
        time.sleep(seconds)

    def close(self):
        if self._selection_probe is not None:
            self._selection_probe.close()
            self._selection_probe = None
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
