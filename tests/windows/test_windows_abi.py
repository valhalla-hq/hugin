"""ABI checks and mocked native producers; no native input or clipboard calls."""
from contextlib import contextmanager
import ctypes
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS

from hugin.windows.clipboard import (NativeClipboard, ClipboardFailure,ClipboardService,ClipboardSnapshot, _Input,
                                     _GuiThreadInfo, _KeyInput, _MouseInput, WindowTarget)
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
    def native_target_fixture(self):
        from ctypes import wintypes as W
        backend=object.__new__(NativeClipboard)
        class User:
            name='Edit';style=0;enabled=True;caret=200;selection=(7,10);reply=True
            after_selection=lambda self:None
            def GetForegroundWindow(self):return 100
            def GetWindowThreadProcessId(self,hwnd,pointer):
                ctypes.cast(pointer,ctypes.POINTER(W.DWORD))[0]=3;return 4
            def GetGUIThreadInfo(self,thread,pointer):
                info=ctypes.cast(pointer,ctypes.POINTER(_GuiThreadInfo)).contents
                info.hwndFocus=200;info.hwndCaret=self.caret
                return 1
            def GetClassNameW(self,hwnd,buffer,limit):buffer.value=self.name;return len(self.name)
            def GetWindowLongPtrW(self,*args):return self.style
            def IsWindowEnabled(self,hwnd):return self.enabled
            def SendMessageTimeoutW(self,hwnd,message,start,end,flags,timeout,result):
                self.assertion=(hwnd,message,flags,timeout)
                ctypes.cast(start,ctypes.POINTER(W.DWORD))[0]=self.selection[0]
                ctypes.cast(end,ctypes.POINTER(W.DWORD))[0]=self.selection[1]
                self.after_selection();return int(self.reply)
        def times(handle,created,*args):
            ctypes.cast(created,ctypes.POINTER(W.FILETIME)).contents.dwLowDateTime=500;return 1
        backend.user=User();backend.kernel=NS(OpenProcess=lambda *args:77,GetProcessTimes=times,CloseHandle=lambda handle:1)
        backend._package_family=lambda handle:None
        return backend,backend.user

    def test_native_capability_requires_enabled_edit_selection_and_owned_caret(self):
        for kind in ('edit','rich','unknown_rich','combo','readonly','disabled','foreign_caret','missing_caret','inverted','timeout'):
            backend,user=self.native_target_fixture()
            if kind=='rich':user.name='RICHEDIT50W'
            elif kind=='unknown_rich':user.name='RichEditUnknown'
            elif kind=='combo':user.name='ComboBox'
            elif kind=='readonly':user.style=0x800
            elif kind=='disabled':user.enabled=False
            elif kind=='foreign_caret':user.caret=201
            elif kind=='missing_caret':user.caret=0
            elif kind=='inverted':user.selection=(10,7)
            elif kind=='timeout':user.reply=False
            target=backend.capture_native_target()
            self.assertEqual((target.native_editable,target.verifiable),(kind in ('edit','rich'),)*2,kind)
        backend,user=self.native_target_fixture();user.style=0x20
        with self.assertRaises(ClipboardFailure) as failure:backend.capture_native_target()
        self.assertEqual(failure.exception.status,'target_unverifiable')

    def test_native_readonly_change_during_selection_query_is_not_proven_editable(self):
        backend,user=self.native_target_fixture()
        user.after_selection=lambda:setattr(user,'style',0x800)
        self.assertFalse(backend.capture_native_target().verifiable)

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

    def test_browser_text_preserves_opaque_source_metadata_and_rejects_unknown_formats(self):
        names={'HTML Format':49152,'Rich Text Format':49153,
            'Chromium internal source RFH token':49154,
            'Chromium internal source URL':49155,
            'Hugin.Private.ClipboardTransaction.v1':49156}
        library=Library()
        library.functions['RegisterClipboardFormatW']=lambda name:names[name]
        with patch.object(ctypes,'WinDLL',return_value=library):
            backend=NativeClipboard()
        original={13:b'T\0\0\0',49152:b'<b>T</b>',
            49154:b'\x00\xff\x01\x80',49155:b'\x00https://example.invalid/\xff'}
        class ClipboardOS:
            current=4
            data=dict(original)
            def EnumClipboardFormats(self,previous):
                order=list(self.data)
                index=order.index(previous)+1 if previous else 0
                return order[index] if index<len(order) else 0
            def GetClipboardSequenceNumber(self):return self.current
            def GetClipboardOwner(self):return 100
            def GetClipboardData(self,identity):return identity
            def EmptyClipboard(self):self.data={};self.current+=1;return 1
            def SetClipboardData(self,identity,handle):
                self.data[identity]=allocations[handle];self.current+=1;return handle
        class MemoryOS:
            def GlobalSize(self,handle):return len(backend.user.data[handle])
        @contextmanager
        def opened(**_):yield
        backend.user,backend.kernel=ClipboardOS(),MemoryOS()
        backend._opened,backend.hwnd=opened,100
        backend._read_handle=lambda handle,size:backend.user.data[handle][:size]
        allocations={}
        def allocate(data):
            handle=len(allocations)+1000;allocations[handle]=data;return handle
        backend._allocate=allocate
        saved=backend.snapshot(1024)
        self.assertEqual(dict(saved.formats),original)
        backend.replace(saved.formats,saved.sequence)
        self.assertEqual(backend.user.data,original)
        backend.user.data[49199]=b'unknown format'
        backend._read_handle=lambda *_:self.fail('unknown format must reject before byte copy')
        with self.assertRaises(ClipboardFailure) as failure:backend.snapshot(1024)
        self.assertEqual(failure.exception.status,'format_unsupported')
        self.assertEqual(backend.user.data,{**original,49199:b'unknown format'})

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
        target=WindowTarget(100,200,3,4,500,'Edit',(200,1,2,3,4),(2,2))
        backend.capture_target = lambda **kwargs: events.append('target') or target
        backend.capture_native_target=lambda:events.append('native') or target
        backend.modifiers_down = lambda: events.append('modifiers') or False
        backend._chord = lambda _: events.append('send')
        sentinel = object()
        def authorize(transaction):
            self.assertIs(transaction, sentinel)
            events.append('authorize')
            return True
        backend.commit_paste(10,target,lambda:events.append('current') or True,authorize,sentinel)
        self.assertEqual(events,['lock','sequence','sequence','native','modifiers','current','authorize','send','unlock'])

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
        target=WindowTarget(100,200,3,4,500,'Edit',(200,1,2,3,4),(2,2))
        backend.capture_target,backend.modifiers_down=lambda **kwargs:target,lambda:False
        backend.capture_native_target=lambda:target
        backend._chord = lambda _: None
        with self.assertRaises(ClipboardFailure) as failure:
            backend.commit_paste(10,target,lambda:True)
        self.assertTrue(failure.exception.submitted)

    def test_partial_write_does_not_claim_later_user_sequence(self):
        backend = object.__new__(NativeClipboard)
        backend._unfreed = set()
        class ClipboardOS:
            sequence = 1;owner=99
            def GetClipboardSequenceNumber(self):
                return self.sequence
            def GetClipboardOwner(self):return self.owner
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
            backend.user.owner=200
            raise ClipboardFailure('clipboard_failed')
        backend.user = ClipboardOS()
        backend.hwnd=99
        backend._opened, backend._allocate = opened, lambda _: 100
        with self.assertRaises(ClipboardFailure) as failure:
            backend.replace(((13, b'text'),), 1)
        self.assertEqual(failure.exception.owned_sequence, 3)

    def publication_fixture(self,*,foreign=False,partial=False):
        backend=object.__new__(NativeClipboard)
        backend.hwnd=99;backend._unfreed=set()
        class ClipboardOS:
            current=1;owner=99
            def GetClipboardSequenceNumber(self):return self.current
            def GetClipboardOwner(self):return self.owner
            def EmptyClipboard(self):self.current=2;return True
            def SetClipboardData(self,identity,handle):
                if partial and identity==49152:return 0
                self.current=3;return handle
        class MemoryOS:
            def GlobalFree(self,handle):return 0
        @contextmanager
        def opened(write=False):
            try:yield
            finally:
                if write:
                    # Windows adds its implicit text formats on CloseClipboard.
                    backend.user.current=77 if foreign else 6
                    backend.user.owner=200 if foreign else 99
        backend.user,backend.kernel=ClipboardOS(),MemoryOS()
        backend._opened=opened;backend._allocate=lambda _:100
        return backend

    def test_complete_write_reports_own_sequence_after_implicit_format_publication(self):
        backend=self.publication_fixture()
        self.assertEqual(backend.replace(((13,b'text'),),1),6)

    def test_user_copy_at_publication_is_not_claimed_as_an_owned_sequence(self):
        backend=self.publication_fixture(foreign=True)
        with self.assertRaises(ClipboardFailure) as failure:
            backend.replace(((13,b'text'),),1)
        self.assertEqual(failure.exception.status,'clipboard_changed')
        self.assertEqual(failure.exception.owned_sequence,3)
        self.assertEqual(backend.user.current,77)

    def test_partial_write_retains_the_published_own_sequence_for_restore(self):
        backend=self.publication_fixture(partial=True)
        with self.assertRaises(ClipboardFailure) as failure:
            backend.replace(((13,b'text'),(49152,b'nonce')),1)
        self.assertEqual(failure.exception.status,'clipboard_write_failed')
        self.assertEqual(failure.exception.owned_sequence,6)

    def test_unstable_zero_or_failed_owner_observation_is_unknown_not_foreign(self):
        for kind in ('unstable','zero','owner_error'):
            backend=self.publication_fixture()
            sequence=iter((5,6) if kind=='unstable' else (0,0) if kind=='zero' else (6,6))
            backend.user.GetClipboardSequenceNumber=lambda:next(sequence)
            if kind=='owner_error':
                def owner_error():ctypes.set_last_error(5);return 0
                backend.user.GetClipboardOwner=owner_error
            with self.assertRaises(ClipboardFailure) as failure:
                backend.restorable_sequence(3)
            self.assertEqual(failure.exception.status,'clipboard_busy',kind)

    def test_changed_sequence_with_null_owner_retains_the_original_recovery_snapshot(self):
        backend=self.publication_fixture();backend.user.current=6;backend.user.owner=0
        saved=ClipboardSnapshot(1,((13,b'original'),))
        service=ClipboardService(backend=backend);service._pending_restore=(saved,3)
        self.assertEqual(service.recover().status,'clipboard_restore_failed')
        self.assertTrue(service.recovery_pending)
        self.assertIs(service._pending_restore[0],saved)
        self.assertEqual(backend.restorable_sequence(6),6)

    def test_direct_edit_selection_uses_utf16_offsets_without_clipboard(self):
        backend = object.__new__(NativeClipboard)
        target = WindowTarget(100, 200, 3, 4, 500, 'Edit', None, (1, 3), native_editable=False)
        data = 'A😀Z'.encode('utf-16-le')
        class ReadOS:
            def SendMessageTimeoutW(self, hwnd, message, capacity, pointer, flags, timeout, result):
                if message == 0xE:
                    ctypes.cast(result, ctypes.POINTER(ctypes.c_size_t))[0] = len(data) // 2
                elif message == 0xD:
                    ctypes.memmove(pointer, data + b'\0\0', len(data) + 2)
                    ctypes.cast(result, ctypes.POINTER(ctypes.c_size_t))[0] = len(data) // 2
                else:
                    raise AssertionError('unexpected message')
                return 1
            def OpenClipboard(self, *_):
                raise AssertionError('direct reads must not access clipboard')
        backend.user = ReadOS()
        backend.capture_native_target = lambda: target
        self.assertEqual(backend.read_direct_selection(target, 1024, lambda: False), '😀')

    def test_direct_read_bounds_whole_control_before_buffer_allocation(self):
        backend = object.__new__(NativeClipboard)
        target = WindowTarget(100, 200, 3, 4, 500, 'Edit', None, (1, 2))
        class ReadOS:
            def SendMessageTimeoutW(self, hwnd, message, capacity, pointer, flags, timeout, result):
                ctypes.cast(result, ctypes.POINTER(ctypes.c_size_t))[0] = 1025
                return 1
        backend.user, backend.capture_native_target = ReadOS(), lambda: target
        with patch.object(ctypes, 'create_unicode_buffer', side_effect=AssertionError('allocation before limit')):
            with self.assertRaises(ClipboardFailure) as failure:
                backend.read_direct_selection(target, 1024, lambda: False)
        self.assertEqual(failure.exception.status, 'text_limit')

    def test_selection_probe_job_memory_limit_uses_native_job_contract(self):
        library = Library()
        captured = []
        def limits(job, information_class, pointer, size):
            value = ctypes.cast(pointer, ctypes.POINTER(_ExtendedLimits)).contents
            captured.append((value.BasicLimitInformation.LimitFlags, value.JobMemoryLimit))
            return 1
        library.SetInformationJobObject = limits
        with patch.object(ctypes, 'WinDLL', return_value=library):
            backend = NativeProcess()
        backend.create_job(256 * 1024 * 1024)
        self.assertEqual(captured, [(0x2000 | 0x200, 256 * 1024 * 1024)])

    def test_non_edit_direct_read_uses_isolated_selection_probe(self):
        from hugin.windows.selection import SelectionResult
        backend = object.__new__(NativeClipboard)
        target = WindowTarget(100, 200, 3, 4, 500, 'Chrome_WidgetWin_1', None, None)
        calls = []
        class Probe:
            def read(self, expected, cancelled):
                calls.append(expected)
                return SelectionResult('captured', 'UIA selected text')
        backend._selection_probe = Probe()
        self.assertEqual(backend.read_direct_selection(target, 1024, lambda: False), 'UIA selected text')
        self.assertEqual(calls, [target])

    def test_selection_probe_failure_never_falls_back_to_clipboard(self):
        from hugin.windows.selection import SelectionResult
        backend = object.__new__(NativeClipboard)
        target = WindowTarget(100, 200, 3, 4, 500, 'Chrome_WidgetWin_1', None, None)
        class Probe:
            def read(self, expected, cancelled):
                return SelectionResult('selection_timeout')
        backend._selection_probe = Probe()
        with self.assertRaises(ClipboardFailure) as failure:
            backend.read_direct_selection(target, 1024, lambda: False)
        self.assertEqual(failure.exception.status, 'selection_timeout')
