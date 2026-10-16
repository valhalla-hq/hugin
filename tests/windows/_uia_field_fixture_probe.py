"""Own hidden RichEdit matrix with real UIA ranges; no global focus lookup.

Never selects the user's foreground window, sends keys, or opens the clipboard.
Replacement uses EM_REPLACESEL on the created HWND, not a SendInput claim.
"""
from pathlib import Path
import ctypes
import gc
import json
import os
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _uia_fixture_probe import Fixture
from hugin.windows.selection import REQUEST_LIMIT, encode_response, read_exact
from hugin.windows.selection_probe import (
    _system_typelib, _load_comtypes, _identity, _Binding, _measure_range, _range_snapshot,
)

def send(fixture, message, wparam, lparam):
    result = ctypes.c_size_t()
    if not fixture.user.SendMessageTimeoutW(
            fixture.edit, message, wparam, lparam, 0x23, 100, ctypes.byref(result)):
        raise RuntimeError('owned_fixture_message')
    return result.value


def set_text(fixture, text):
    buffer = ctypes.create_unicode_buffer(text)
    if not send(fixture, 0xC, 0, ctypes.addressof(buffer)):
        raise RuntimeError('owned_fixture_set_text')


def get_text(fixture):
    buffer = ctypes.create_unicode_buffer(128)
    send(fixture, 0xD, len(buffer), ctypes.addressof(buffer))
    return buffer.value


def run():
    sys.coinit_flags = 0
    comtypes, client = _load_comtypes()
    comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
    fixture = native = element = root = pattern = binding = selected = current = final = None
    try:
        fixture = Fixture()
        foreground = fixture.user.GetForegroundWindow()
        clipboard = fixture.user.GetClipboardSequenceNumber()
        fixture.start()
        uia = client.GetModule(_system_typelib())
        native = client.CreateObject(uia.CUIAutomation, interface=uia.IUIAutomation, clsctx=1)
        element = native.ElementFromHandle(fixture.edit)
        root = native.ElementFromHandle(fixture.hwnd)
        if element.CurrentProcessId != os.getpid() or root.CurrentProcessId != os.getpid():
            raise RuntimeError('owned_fixture_provider_identity')
        pattern = element.GetCurrentPattern(uia.UIA_TextPatternId).QueryInterface(uia.IUIAutomationTextPattern)
        binding = _Binding(_identity(element), _identity(root), _identity(element), os.getpid(), pattern)
        text = 'Anfang alte Wörter Ende'
        cases = (
            ('cursor', text, 7, 7), ('end_cursor', text, 23, 23),
            ('partial', text, 7, 18), ('full', text, 0, 23),
            ('unicode', 'A😀e\u0301Z', 1, 6),
        )
        report = []
        for name, source, start, end in cases:
            set_text(fixture, source)
            send(fixture, 0xB1, start, end)
            identity, selected = _measure_range(native, binding)
            if identity.selection != (start, end):
                raise RuntimeError('owned_fixture_wrong_offsets')
            confirmed, current = _measure_range(native, binding)
            final, ids, relations, _, _ = _range_snapshot(native, binding)
            if (identity != confirmed or ids != (identity.start_id, identity.end_id)
                    or relations != (identity.start_relation, identity.end_relation)
                    or any(selected.CompareEndpoints(i, current, i) != 0
                           or current.CompareEndpoints(i, final, i) != 0 for i in (0, 1))):
                raise RuntimeError('owned_fixture_confirmation')
            replacement = ctypes.create_unicode_buffer('neu')
            send(fixture, 0xC2, 0, ctypes.addressof(replacement))
            encoded = source.encode('utf-16-le')
            expected = (encoded[:2*start] + 'neu'.encode('utf-16-le') + encoded[2*end:]).decode('utf-16-le')
            if get_text(fixture) != expected:
                raise RuntimeError('owned_fixture_replacement')
            report.append({'case': name, 'selection': list(identity.selection),
                           'replacement_verified': True})
        set_text(fixture, text)
        send(fixture, 0xB1, 7, 18)
        identity, selected = _measure_range(native, binding)
        send(fixture, 0xB1, 8, 18)
        changed_identity, _ = _measure_range(native, binding)
        if identity == changed_identity:
            raise RuntimeError('owned_fixture_change_not_rejected')
        if (fixture.user.GetForegroundWindow() != foreground
                or fixture.user.GetClipboardSequenceNumber() != clipboard):
            return 'target_changed', None
        return 'captured', json.dumps({'cases': report, 'changed_selection_detected': True,
                                       'scope': 'owned_textpattern_ranges', 'clipboard_untouched': True})
    finally:
        selected = current = final = binding = pattern = root = element = native = None
        _ = None
        gc.collect()
        comtypes.CoUninitialize()
        if fixture is not None:
            fixture.close()


def main():
    try:
        length = struct.unpack('!I', read_exact(sys.stdin.buffer, 4))[0]
        if length > REQUEST_LIMIT:
            raise ValueError('fixture_request_limit')
        read_exact(sys.stdin.buffer, length)
        if sys.stdin.buffer.read(1) != b'':
            raise ValueError('fixture_trailing_request')
        status, text = run()
        data = encode_response(status, text)
    except Exception:
        data = encode_response('selection_failed')
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
