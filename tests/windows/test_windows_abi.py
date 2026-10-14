"""ABI checks and mocked native producers; no native input or clipboard calls."""
from contextlib import contextmanager
import ctypes
import sys
import unittest
from unittest.mock import patch

from hugin.windows.clipboard import (NativeClipboard, ClipboardFailure, _Input,
                                     _GuiThreadInfo, _KeyInput, _MouseInput)
from hugin.windows.process import (NativeProcess, _StartupInfo, _StartupInfoEx,
                                   _ProcessInformation, _ExtendedLimits)
from hugin.windows.input import NativeInputs
from hugin.windows.instance import NativeMutex


class Function:
    def __init__(self, result=1):
        self.argtypes = None
        self.restype = None
        self.result = result
    def __call__(self, *args):
        return self.result


class Library:
    def __init__(self):
        self.functions = {}
    def __getattr__(self, name):
        return self.functions.setdefault(name, Function())


@unittest.skipUnless(sys.platform == 'win32', 'Windows ctypes ABI')
class WindowsAbiContracts(unittest.TestCase):
    def test_x64_layouts_match_win32_headers(self):
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            self.skipTest('Hugin x64 target')
        for structure, size in ((_Input, 40), (_GuiThreadInfo, 72), (_KeyInput, 24),
                                (_MouseInput, 32), (_StartupInfo, 104), (_StartupInfoEx, 112),
                                (_ProcessInformation, 24), (_ExtendedLimits, 144)):
            self.assertEqual(ctypes.sizeof(structure), size, structure.__name__)

    def test_every_loaded_function_has_explicit_argument_and_result_types(self):
        libraries = []
        def library(*_, **__):
            value = Library()
            libraries.append(value)
            return value
        with patch.object(ctypes, 'WinDLL', side_effect=library):
            NativeInputs()
            NativeClipboard()
            NativeMutex()
            NativeProcess()
        for value in libraries:
            for name, function in value.functions.items():
                self.assertIsNotNone(function.argtypes, name)
                if name != 'DeleteProcThreadAttributeList':
                    self.assertIsNotNone(function.restype, name)

    def test_partial_input_releases_only_keys_this_call_pressed(self):
        backend = object.__new__(NativeClipboard)
        class InputOS:
            def __init__(self):
                self.calls = []
            def SendInput(self, count, inputs, size):
                self.calls.append([(item.ki.wVk, item.ki.dwFlags) for item in inputs])
                return 1 if len(self.calls) == 1 else count
        backend.user = InputOS()
        with self.assertRaises(ClipboardFailure) as failure:
            backend._chord(0x56)
        self.assertEqual(failure.exception.status, 'input_partial')
        self.assertEqual(backend.user.calls[1], [(0x11, 2)])
        self.assertFalse(failure.exception.submitted)

    def test_partial_paste_is_reported_as_possible_submission(self):
        backend = object.__new__(NativeClipboard)
        class InputOS:
            calls = 0
            def SendInput(self, count, inputs, size):
                self.calls += 1
                return 2 if self.calls == 1 else count
        backend.user = InputOS()
        with self.assertRaises(ClipboardFailure) as failure:
            backend._chord(0x56)
        self.assertTrue(failure.exception.submitted)

    def test_unknown_format_fails_before_any_data_materialization(self):
        backend = object.__new__(NativeClipboard)
        @contextmanager
        def opened():
            yield
        class ClipboardOS:
            def EnumClipboardFormats(self, previous):
                return 49199 if previous == 0 else 0
            def GetClipboardSequenceNumber(self):
                return 1
            def GetClipboardData(self, identity):
                raise AssertionError('must reject before materialization')
        backend.user, backend.allowed, backend._opened = ClipboardOS(), {13}, opened
        with self.assertRaises(ClipboardFailure) as failure:
            backend.snapshot(1024)
        self.assertEqual(failure.exception.status, 'format_unsupported')

    def test_native_snapshot_accounts_all_sizes_before_copying(self):
        backend = object.__new__(NativeClipboard)
        @contextmanager
        def opened():
            yield
        class ClipboardOS:
            def EnumClipboardFormats(self, previous):
                return {0: 13, 13: 49152, 49152: 0}[previous]
            def GetClipboardSequenceNumber(self):
                return 1
            def GetClipboardData(self, identity):
                return identity
        class MemoryOS:
            def GlobalSize(self, handle):
                return {13: 1000, 49152: 25}[handle]
        backend.user, backend.kernel = ClipboardOS(), MemoryOS()
        backend.allowed, backend._opened = {13, 49152}, opened
        backend._read_handle = lambda *_: self.fail('must check total before any byte copy')
        with self.assertRaises(ClipboardFailure) as failure:
            backend.snapshot(1024)
        self.assertEqual(failure.exception.status, 'snapshot_limit')

    def test_null_delayed_data_fails_before_mutation(self):
        backend = object.__new__(NativeClipboard)
        @contextmanager
        def opened():
            yield
        class ClipboardOS:
            def EnumClipboardFormats(self, previous):
                return 13 if previous == 0 else 0
            def GetClipboardSequenceNumber(self):
                return 1
            def GetClipboardData(self, identity):
                return 0
        backend.user, backend.allowed, backend._opened = ClipboardOS(), {13}, opened
        with self.assertRaises(ClipboardFailure) as failure:
            backend.snapshot(1024)
        self.assertEqual(failure.exception.status, 'format_delayed')

    def test_all_replacement_allocations_precede_empty_clipboard(self):
        backend = object.__new__(NativeClipboard)
        backend._unfreed = set()
        allocated = []
        freed = []
        def allocate(data):
            if allocated:
                raise ClipboardFailure('clipboard_failed')
            allocated.append(100)
            return 100
        backend._allocate = allocate
        class MemoryOS:
            def GlobalFree(self, handle):
                freed.append(handle)
                return 0
        backend.kernel = MemoryOS()
        backend._opened = lambda **_: self.fail('must not open for mutation before allocations succeed')
        with self.assertRaises(ClipboardFailure):
            backend.replace(((13, b'a'), (49152, b'b')), 1)
        self.assertEqual(freed, [100])

    def test_native_commit_authorization_is_after_checks_and_before_send(self):
        backend = object.__new__(NativeClipboard)
        events = []
        @contextmanager
        def opened():
            events.append('lock')
            yield
            events.append('unlock')
        class ClipboardOS:
            def GetClipboardSequenceNumber(self):
                events.append('sequence')
                return 10
            def GetClipboardOwner(self):
                return 100
            def GetClipboardData(self, identity):
                return 200
        class MemoryOS:
            def GlobalSize(self, handle):
                return 5
        backend.user, backend.kernel = ClipboardOS(), MemoryOS()
        backend._opened, backend.hwnd, backend.tx_format, backend._token = opened, 100, 49152, b'nonce'
        backend._read_handle = lambda *_: b'nonce'
        backend.capture_target = lambda: events.append('target') or 'target'
        backend.modifiers_down = lambda: events.append('modifiers') or False
        backend._chord = lambda _: events.append('send')
        sentinel = object()
        def authorize(transaction):
            self.assertIs(transaction, sentinel)
            events.append('authorize')
            return True
        backend.commit_paste(10, 'target', lambda: events.append('current') or True, authorize, sentinel)
        self.assertEqual(events, ['lock', 'sequence', 'target', 'modifiers', 'current', 'authorize', 'send', 'unlock'])

    def test_failed_close_after_send_keeps_possible_submission_fact(self):
        backend = object.__new__(NativeClipboard)
        @contextmanager
        def opened():
            yield
            raise ClipboardFailure('clipboard_failed')
        class ClipboardOS:
            def GetClipboardSequenceNumber(self):
                return 10
            def GetClipboardOwner(self):
                return 100
            def GetClipboardData(self, identity):
                return 200
        class MemoryOS:
            def GlobalSize(self, handle):
                return 5
        backend.user, backend.kernel = ClipboardOS(), MemoryOS()
        backend._opened, backend.hwnd, backend.tx_format, backend._token = opened, 100, 49152, b'nonce'
        backend._read_handle = lambda *_: b'nonce'
        backend.capture_target, backend.modifiers_down = lambda: 'target', lambda: False
        backend._chord = lambda _: None
        with self.assertRaises(ClipboardFailure) as failure:
            backend.commit_paste(10, 'target', lambda: True)
        self.assertTrue(failure.exception.submitted)

    def test_partial_write_does_not_claim_later_user_sequence(self):
        backend = object.__new__(NativeClipboard)
        backend._unfreed = set()
        class ClipboardOS:
            sequence = 1
            def GetClipboardSequenceNumber(self):
                return self.sequence
            def EmptyClipboard(self):
                self.sequence = 2
                return True
            def SetClipboardData(self, identity, handle):
                self.sequence = 3
                return True
        @contextmanager
        def opened(**_):
            yield
            backend.user.sequence = 77  # user copy after the clipboard lock
            raise ClipboardFailure('clipboard_failed')
        backend.user = ClipboardOS()
        backend._opened, backend._allocate = opened, lambda _: 100
        with self.assertRaises(ClipboardFailure) as failure:
            backend.replace(((13, b'text'),), 1)
        self.assertEqual(failure.exception.owned_sequence, 3)
