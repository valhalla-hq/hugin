import io
from pathlib import Path
import struct
import subprocess
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from hugin.windows.clipboard import WindowTarget
from hugin.windows.selection import SelectionProbe, encode_response
from hugin.windows.selection_probe import read_uia_selection
from hugin.windows.selection import SelectionResult, decode_response, encode_request, decode_request

TARGET = WindowTarget(100, 200, 3, 4, 500, 'Chrome_WidgetWin_1', None, None)


class Range:
    def __init__(self, text, start=0, end=None):
        self.text, self.start, self.end = text, start, len(text) if end is None else end
        self.requests = []
        self.after_read = lambda: None
        self.CurrentIsPassword = False
    def Clone(self):
        return Range(self.text, self.start, self.end)
    def CompareEndpoints(self, endpoint, other, other_endpoint):
        return (self.start if endpoint == 0 else self.end) - (other.start if other_endpoint == 0 else other.end)
    def GetText(self, limit):
        self.requests.append(limit)
        text = self.text[:limit]
        self.after_read()
        return text
    def GetEnclosingElement(self):
        return self


class Ranges:
    def __init__(self, values):
        self.values = values
        self.Length = len(values)
    def GetElement(self, index):
        return self.values[index]


class Pattern:
    SupportedTextSelection = 1
    def __init__(self, text):
        self.range = Range(text)
        self.values = [self.range]
        self.after_selection = lambda: None
    def QueryInterface(self, interface):
        return self
    def GetSelection(self):
        self.after_selection()
        return Ranges(self.values)
    @property
    def DocumentRange(self):
        raise AssertionError('document-full-text fallback is forbidden')


class Element:
    CurrentProcessId = 3
    CurrentHasKeyboardFocus = True
    CurrentIsPassword = False
    def __init__(self, identity, parent=None, pattern=None):
        self.identity, self.parent, self.pattern = identity, parent, pattern
    def GetRuntimeId(self):
        return (42, self.identity)
    def GetCurrentPropertyValue(self, identity):
        return self.pattern is not None
    def GetCurrentPattern(self, identity):
        return self.pattern


class Automation:
    class Walker:
        def GetParentElement(self, element):
            return element.parent
    RawViewWalker = Walker()
    def __init__(self, text='selected'):
        self.pattern = Pattern(text)
        self.root = Element(1)
        self.document = Element(2, self.root, self.pattern)
        self.focus = Element(3, self.document)
    def GetFocusedElement(self):
        return self.focus
    def ElementFromHandle(self, hwnd):
        return self.root
    def CompareElements(self, one, two):
        return one is two


class UiaTypes:
    UIA_IsTextPatternAvailablePropertyId = 30040
    UIA_TextPatternId = 10014
    IUIAutomationTextPattern = object()


class UiaSelectionContracts(unittest.TestCase):
    def read(self, automation, limit=1024, native=lambda: TARGET):
        return read_uia_selection(automation, UiaTypes, TARGET, native, lambda: False, limit)

    def test_reads_one_selected_range_on_bound_ancestor_with_positive_limit(self):
        automation = Automation('a selected sentence')
        result = self.read(automation)
        self.assertEqual((result.status, result.text), ('captured', 'a selected sentence'))
        self.assertEqual(automation.pattern.range.requests, [1025, 1025])
        self.assertNotIn('a selected sentence', repr(result))

    def test_empty_or_missing_pattern_never_reads_document(self):
        automation = Automation('')
        self.assertEqual(self.read(automation).status, 'selection_empty')
        automation.document.pattern = None
        self.assertEqual(self.read(automation).status, 'selection_unsupported')

    def test_multiple_ranges_are_rejected_without_silent_partial_text(self):
        automation = Automation('first')
        automation.pattern.values.append(Range('second'))
        self.assertEqual(self.read(automation).status, 'selection_unsupported')
        self.assertEqual(automation.pattern.range.requests, [])

    def test_password_or_unbound_focus_is_rejected(self):
        automation = Automation('password contents')
        automation.focus.CurrentIsPassword = True
        self.assertEqual(self.read(automation).status, 'selection_unsupported')
        automation = Automation('other app')
        automation.focus.parent = None
        self.assertEqual(self.read(automation).status, 'target_changed')

    def test_changed_range_or_text_is_rejected(self):
        for kind in ('range', 'text'):
            automation = Automation('initial')
            def change():
                if kind == 'range':
                    automation.pattern.range.end += 1
                else:
                    automation.pattern.range.text = 'changed'
            automation.pattern.range.after_read = change
            self.assertEqual(self.read(automation).status, 'target_changed')

    def test_text_is_bounded_and_never_requested_as_full_document(self):
        automation = Automation('x' * 1025)
        self.assertEqual(self.read(automation, 1024).status, 'selection_limit')
        self.assertEqual(automation.pattern.range.requests, [1025])

    def test_provider_failure_contains_no_raw_payload(self):
        automation = Automation('synthetic text')
        def fail(_):
            raise RuntimeError('PRIVATE SELECTED CONTENT')
        automation.pattern.range.GetText = fail
        result = self.read(automation)
        self.assertEqual(result.status, 'selection_failed')
        self.assertIsNone(result.text)
        self.assertNotIn('PRIVATE', repr(result))

    def test_renderer_process_can_be_bound_through_the_actual_window_ancestor(self):
        automation = Automation('renderer text')
        automation.focus.CurrentProcessId = 500
        self.assertEqual(self.read(automation).status, 'captured')

    def test_invalid_limit_cannot_request_unbounded_gettext(self):
        automation = Automation('selection')
        self.assertEqual(self.read(automation, -2).status, 'selection_limit')
        self.assertEqual(automation.pattern.range.requests, [])

    def test_protected_enclosing_element_is_rejected_before_gettext(self):
        automation = Automation('protected selection')
        automation.pattern.range.CurrentIsPassword = True
        self.assertEqual(self.read(automation).status, 'selection_unsupported')
        self.assertEqual(automation.pattern.range.requests, [])

    def test_focus_or_password_change_before_gettext_is_checked_fresh(self):
        for kind in ('focus', 'password'):
            automation = Automation('must not read')
            if kind == 'password':
                automation.pattern.after_selection = lambda: setattr(automation.focus, 'CurrentIsPassword', True)
            else:
                automation.pattern.after_selection = lambda: setattr(automation, 'focus', Element(99, automation.document))
            self.assertEqual(self.read(automation).status,
                             'selection_unsupported' if kind == 'password' else 'target_changed')
            self.assertEqual(automation.pattern.range.requests, [])


class NonClosingBytesIO(io.BytesIO):
    def close(self):
        pass


class FakeProcess:
    def __init__(self, data, *, blocked=False, kill_fails=False):
        self.stdin = NonClosingBytesIO()
        self.stderr = io.BytesIO()
        self.output = io.BytesIO(data)
        self.blocked, self.kill_fails = blocked, kill_fails
        self.release = threading.Event()
        self.closed = False
        self.killed = False
        owner = self
        class Output:
            def read(self, count):
                if owner.blocked:
                    owner.release.wait(2)
                return owner.output.read(count)
        self.stdout = Output()
    def poll(self):
        return None if self.blocked and not self.killed else 0
    def wait(self, timeout=None):
        if self.poll() is None:
            raise subprocess.TimeoutExpired(['synthetic-probe'], timeout)
        return 0
    def kill(self):
        if self.kill_fails:
            raise OSError('PRIVATE PROVIDER PAYLOAD')
        self.killed = True
        self.release.set()
    def close(self):
        self.closed = True


class ProbeProcessContracts(unittest.TestCase):
    def test_private_framed_text_is_read_and_owned_process_closed(self):
        process = FakeProcess(encode_response('captured', 'selected 😀'))
        calls = []
        def spawn(command, **options):
            calls.append(options)
            return process
        result = SelectionProbe(spawn=spawn).read(TARGET, lambda: False)
        self.assertEqual((result.status, result.text), ('captured', 'selected 😀'))
        self.assertTrue(process.closed)
        self.assertEqual(calls[0]['memory_limit'], 256 * 1024 * 1024)
        self.assertNotIn(b'selected', process.stdin.getvalue()[4:])

    def test_declared_oversize_is_rejected_before_payload_read(self):
        process = FakeProcess(struct.pack('!BBI', 1, 0, 256 * 1024 + 1))
        result = SelectionProbe(spawn=lambda *_, **__: process).read(TARGET, lambda: False)
        self.assertEqual(result.status, 'selection_failed')
        self.assertTrue(process.closed)

    def test_hung_provider_is_killed_as_owned_family_before_timeout_result(self):
        process = FakeProcess(b'', blocked=True)
        probe = SelectionProbe(spawn=lambda *_, **__: process, timeout=0.02)
        self.assertEqual(probe.read(TARGET, lambda: False).status, 'selection_timeout')
        self.assertTrue(process.killed)
        self.assertTrue(process.closed)

    def test_failed_cleanup_retains_owner_and_prevents_second_probe(self):
        process = FakeProcess(b'', blocked=True, kill_fails=True)
        probe = SelectionProbe(spawn=lambda *_, **__: process, timeout=0.02)
        self.assertEqual(probe.read(TARGET, lambda: False).status, 'selection_cleanup_failed')
        self.assertFalse(process.closed)
        self.assertEqual(probe.read(TARGET, lambda: False).status, 'selection_cleanup_pending')
        process.kill_fails = False
        probe.close()
        self.assertTrue(process.closed)

    def test_cancellation_prevents_late_selection_publication(self):
        process = FakeProcess(encode_response('captured', 'late text'), blocked=True)
        calls = {'count': 0}
        def cancelled():
            calls['count'] += 1
            return calls['count'] >= 2
        result = SelectionProbe(spawn=lambda *_, **__: process).read(TARGET, cancelled)
        self.assertEqual(result.status, 'cancelled')
        self.assertIsNone(result.text)
        self.assertTrue(process.killed)
        self.assertTrue(process.closed)

    def test_provider_stderr_is_discarded_and_never_a_green_result(self):
        process = FakeProcess(encode_response('captured', 'selected'))
        process.stderr = io.BytesIO(b'PRIVATE PROVIDER EXCEPTION')
        result = SelectionProbe(spawn=lambda *_, **__: process).read(TARGET, lambda: False)
        self.assertEqual(result.status, 'selection_failed')
        self.assertNotIn('PRIVATE', repr(result))

    def test_communication_thread_failure_cleans_owned_process(self):
        process = FakeProcess(encode_response('captured', 'selected'))
        with patch.object(threading.Thread, 'start', side_effect=RuntimeError('thread capacity')):
            result = SelectionProbe(spawn=lambda *_, **__: process).read(TARGET, lambda: False)
        self.assertEqual(result.status, 'selection_failed')
        self.assertTrue(process.closed)

    def test_duplicate_or_boolean_version_request_is_rejected(self):
        data = encode_request(TARGET)[4:]
        self.assertEqual(decode_request(data), TARGET)
        for invalid in (data.replace(b'"version":1', b'"version":true'),
                        data.replace(b'"version":1', b'"version":1,"version":1')):
            with self.assertRaises(ValueError):
                decode_request(invalid)

    def test_trailing_truncated_and_invalid_utf8_responses_fail_closed(self):
        frame = encode_response('captured', 'text')
        for invalid in (frame + b'x', frame[:-1], struct.pack('!BBI', 1, 0, 1) + b'\xff'):
            with self.assertRaises((ValueError, UnicodeError)):
                decode_response(io.BytesIO(invalid))

    def test_com_apartment_is_mta_and_explicit_reference_is_balanced(self):
        from hugin.windows import selection_probe
        events = []
        comtypes = types.ModuleType('comtypes')
        comtypes.__path__ = []
        comtypes.COINIT_MULTITHREADED = 0
        comtypes.CoInitializeEx = lambda flags: events.append(('initialize', flags))
        comtypes.CoUninitialize = lambda: events.append('uninitialize')
        client = types.ModuleType('comtypes.client')
        client.gen_dir = 'original'
        client.GetModule = lambda path: events.append('typelib') or UiaTypes
        comtypes.client = client
        import sys
        with patch.dict(sys.modules, {'comtypes': comtypes, 'comtypes.client': client}), \
             patch.object(sys, 'platform', 'win32'), patch.object(sys, 'coinit_flags', 2, create=True), \
             patch.object(selection_probe, '_system_typelib', return_value='C:/Windows/System32/UIAutomationCore.dll'), \
             patch.object(selection_probe, '_load_comtypes', return_value=(comtypes, client)), \
             patch.object(selection_probe, '_com_read', side_effect=lambda *_: events.append('read') or SelectionResult('selection_empty')), \
             patch('gc.collect', side_effect=lambda: events.append('collect')):
            result = selection_probe.run_native(TARGET)
            self.assertEqual(sys.coinit_flags, 0)
        self.assertEqual(result.status, 'selection_empty')
        self.assertEqual(events, [('initialize', 0), 'typelib', 'read', 'collect', 'uninitialize'])

    def test_non_hugin_comtypes_runtime_is_rejected_before_client_cache_initialization(self):
        from hugin.windows import selection_probe
        import sys
        comtypes = types.ModuleType('comtypes')
        comtypes.__file__ = str(Path('foreign/site-packages/comtypes/__init__.py').resolve())
        with patch.dict(sys.modules, {'comtypes': comtypes}), patch.object(sys, 'prefix', str(Path('Hugin/.runtime/controller').resolve())):
            with self.assertRaises(selection_probe._SelectionFailure) as failure:
                selection_probe._load_comtypes()
        self.assertEqual(failure.exception.status, 'dependency_unavailable')

    def test_runtime_cache_namespace_is_preserved_and_generation_is_memory_only(self):
        from hugin.windows import selection_probe
        import sys
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / '.runtime/controller'
            package = prefix / 'Lib/site-packages/comtypes'
            generated = package / 'gen'
            generated.mkdir(parents=True)
            namespace = generated / '__init__.py'
            namespace.write_text('# existing namespace\n', encoding='utf-8')
            comtypes = types.ModuleType('comtypes')
            comtypes.__file__, comtypes.__path__ = str(package / '__init__.py'), [str(package)]
            gen = types.ModuleType('comtypes.gen')
            gen.__path__ = [str(generated)]
            client = types.ModuleType('comtypes.client')
            client.gen_dir = 'unexpected-global-cache'
            comtypes.gen, comtypes.client = gen, client
            with patch.dict(sys.modules, {'comtypes': comtypes, 'comtypes.gen': gen, 'comtypes.client': client}), \
                 patch.object(sys, 'prefix', str(prefix)):
                loaded = selection_probe._load_comtypes()
            self.assertEqual(loaded, (comtypes, client))
            self.assertIsNone(client.gen_dir)
            self.assertEqual(namespace.read_text(encoding='utf-8'), '# existing namespace\n')

    def test_readonly_runtime_does_not_initialize_client_or_global_cache(self):
        from hugin.windows import selection_probe
        import sys
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / '.runtime/controller'
            package = prefix / 'Lib/site-packages/comtypes'
            (package / 'gen').mkdir(parents=True)
            (package / 'gen/__init__.py').write_text('# existing\n', encoding='utf-8')
            comtypes = types.ModuleType('comtypes')
            comtypes.__file__ = str(package / '__init__.py')
            client = types.ModuleType('comtypes.client')
            client.gen_dir = 'unchanged'
            with patch.dict(sys.modules, {'comtypes': comtypes, 'comtypes.client': client}), \
                 patch.object(sys, 'prefix', str(prefix)), patch.object(selection_probe.os, 'access', return_value=False):
                with self.assertRaises(selection_probe._SelectionFailure):
                    selection_probe._load_comtypes()
            self.assertEqual(client.gen_dir, 'unchanged')
