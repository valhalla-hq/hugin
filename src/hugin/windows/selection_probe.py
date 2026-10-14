"""One-shot comtypes UIA reader. Executed only inside SelectionProbe's job."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hugin.windows.selection import (REQUEST_LIMIT, SelectionResult, decode_request,
                                     encode_response, read_exact)
from hugin.windows.clipboard import MAX_TEXT_BYTES


class _SelectionFailure(Exception):
    def __init__(self, status):
        self.status = status


@dataclass
class _Binding:
    focus_id: tuple
    root_id: tuple
    element_id: tuple
    focus_pid: int
    pattern: object


def _identity(element):
    identity = element.GetRuntimeId()
    if not isinstance(identity, (tuple, list)) or not 0 < len(identity) <= 64 or any(
            type(part) is not int or not -(1 << 31) <= part < 1 << 31 for part in identity):
        raise _SelectionFailure('target_changed')
    return tuple(identity)


def _flag(value):
    if type(value) not in (bool, int) or value not in (0, 1):
        raise _SelectionFailure('selection_unsupported')
    return bool(value)


def _bind(automation, uia, target):
    focus = automation.GetFocusedElement()
    root = automation.ElementFromHandle(target.hwnd)
    if not focus or not root or not _flag(focus.CurrentHasKeyboardFocus):
        raise _SelectionFailure('target_changed')
    if _flag(focus.CurrentIsPassword):
        raise _SelectionFailure('selection_unsupported')
    focus_id, root_id = _identity(focus), _identity(root)
    pid = focus.CurrentProcessId
    if type(pid) is not int or not 0 < pid < 1 << 32:
        raise _SelectionFailure('target_changed')
    walker = automation.RawViewWalker
    current = focus
    pattern = None
    element_id = None
    for _ in range(64):
        if not current:
            break
        if pattern is None:
            available = current.GetCurrentPropertyValue(uia.UIA_IsTextPatternAvailablePropertyId)
            if type(available) is not bool:
                raise _SelectionFailure('selection_unsupported')
            if available:
                if _flag(current.CurrentIsPassword):
                    raise _SelectionFailure('selection_unsupported')
                unknown = current.GetCurrentPattern(uia.UIA_TextPatternId)
                if not unknown:
                    raise _SelectionFailure('selection_unsupported')
                pattern = unknown.QueryInterface(uia.IUIAutomationTextPattern)
                element_id = _identity(current)
        if automation.CompareElements(current, root):
            if pattern is None:
                raise _SelectionFailure('selection_unsupported')
            supported = pattern.SupportedTextSelection
            if type(supported) is not int or supported not in (1, 2):
                raise _SelectionFailure('selection_unsupported')
            return _Binding(focus_id, root_id, element_id, pid, pattern)
        current = walker.GetParentElement(current)
    raise _SelectionFailure('target_changed')


def _selected(pattern):
    ranges = pattern.GetSelection()
    if not ranges:
        raise _SelectionFailure('selection_unsupported')
    count = ranges.Length
    if type(count) is not int or count < 0 or count > 1:
        raise _SelectionFailure('selection_unsupported')
    return ranges.GetElement(0) if count else None


def _text(selected, limit):
    # Never -1, DocumentRange, ValuePattern, or unbounded document text.
    enclosing = selected.GetEnclosingElement()
    if not enclosing or _flag(enclosing.CurrentIsPassword):
        raise _SelectionFailure('selection_unsupported')
    text = selected.GetText(limit + 1)
    if not isinstance(text, str) or '\0' in text:
        raise _SelectionFailure('selection_failed')
    if len(text) > limit or len(text.encode('utf-8')) > limit:
        raise _SelectionFailure('selection_limit')
    return text


def _confirm_focus(automation, binding, target, native_target):
    if native_target() != target:
        raise _SelectionFailure('target_changed')
    focus = automation.GetFocusedElement()
    if not focus or not _flag(focus.CurrentHasKeyboardFocus):
        raise _SelectionFailure('target_changed')
    if _flag(focus.CurrentIsPassword):
        raise _SelectionFailure('selection_unsupported')
    if _identity(focus) != binding.focus_id or focus.CurrentProcessId != binding.focus_pid:
        raise _SelectionFailure('target_changed')


def read_uia_selection(automation, uia, target, native_target, cancelled, limit):
    try:
        if type(limit) is not int or not 0 < limit <= MAX_TEXT_BYTES:
            return SelectionResult('selection_limit')
        if cancelled():
            return SelectionResult('cancelled')
        if native_target() != target:
            return SelectionResult('target_changed')
        binding = _bind(automation, uia, target)
        selected = _selected(binding.pattern)
        if selected is None:
            return SelectionResult('selection_empty')
        original = selected.Clone()
        _confirm_focus(automation, binding, target, native_target)
        first = _text(selected, limit)
        after = _bind(automation, uia, target)
        if (binding.focus_id, binding.root_id, binding.element_id, binding.focus_pid) != (
                after.focus_id, after.root_id, after.element_id, after.focus_pid):
            return SelectionResult('target_changed')
        current = _selected(after.pattern)
        if current is None or any(original.CompareEndpoints(endpoint, current, endpoint) != 0 for endpoint in (0, 1)):
            return SelectionResult('target_changed')
        _confirm_focus(automation, after, target, native_target)
        second = _text(current, limit)
        final = _selected(after.pattern)
        if final is None or any(original.CompareEndpoints(endpoint, final, endpoint) != 0 for endpoint in (0, 1)):
            return SelectionResult('target_changed')
        focus = automation.GetFocusedElement()
        if not focus or _identity(focus) != binding.focus_id or focus.CurrentProcessId != binding.focus_pid or not _flag(focus.CurrentHasKeyboardFocus) or _flag(focus.CurrentIsPassword):
            return SelectionResult('target_changed')
        if cancelled():
            return SelectionResult('cancelled')
        if first != second or native_target() != target:
            return SelectionResult('target_changed')
        return SelectionResult('captured', first) if first else SelectionResult('selection_empty')
    except _SelectionFailure as failure:
        return SelectionResult(failure.status)
    except Exception:
        # COM provider exception text may contain document content.
        return SelectionResult('selection_failed')


def _system_typelib():
    import ctypes
    from ctypes import wintypes as W
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetSystemDirectoryW.argtypes = [W.LPWSTR, W.UINT]
    kernel.GetSystemDirectoryW.restype = W.UINT
    path = ctypes.create_unicode_buffer(32768)
    length = kernel.GetSystemDirectoryW(path, len(path))
    if not 0 < length < len(path):
        raise _SelectionFailure('dependency_unavailable')
    return str(Path(path.value) / 'UIAutomationCore.dll')


def _com_read(client, uia, target):
    from hugin.windows.clipboard import NativeClipboard, MAX_TEXT_BYTES
    native = NativeClipboard()
    try:
        automation = client.CreateObject(uia.CUIAutomation, interface=uia.IUIAutomation, clsctx=1)
        return read_uia_selection(automation, uia, target, native.capture_target, lambda: False, MAX_TEXT_BYTES)
    finally:
        native.close()


def _load_comtypes():
    """Prevent comtypes' import-time code-cache fallback to a user profile.

    The pinned controller owns its runtime. Provision only the static namespace
    there before client import; generated type interfaces remain memory-only.
    A different/read-only runtime is an explicit unavailable dependency.
    """
    import comtypes
    prefix = Path(sys.prefix).resolve()
    package = Path(comtypes.__file__).resolve().parent
    if prefix.name != 'controller' or prefix.parent.name != '.runtime' or not package.is_relative_to(prefix):
        raise _SelectionFailure('dependency_unavailable')
    generated = (package / 'gen').resolve()
    if not generated.is_relative_to(prefix):
        raise _SelectionFailure('dependency_unavailable')
    generated.mkdir(exist_ok=True)
    namespace = generated / '__init__.py'
    try:
        with namespace.open('x', encoding='utf-8') as output:
            output.write('# comtypes generated-interface namespace; Hugin uses memory-only generation.\n')
    except FileExistsError:
        pass
    if not namespace.is_file() or not namespace.resolve().is_relative_to(prefix) or not os.access(generated, os.W_OK):
        raise _SelectionFailure('dependency_unavailable')
    import comtypes.gen as gen
    if not gen.__path__ or any(Path(item).resolve() != generated for item in gen.__path__):
        raise _SelectionFailure('dependency_unavailable')
    import comtypes.client as client
    client.gen_dir = None
    return comtypes, client


def run_native(target):
    if sys.platform != 'win32':
        return SelectionResult('dependency_unavailable')
    # comtypes initializes its importing thread. Select MTA before import;
    # its process-shutdown hook balances that initial apartment reference.
    sys.coinit_flags = 0
    try:
        comtypes, client = _load_comtypes()
    except (ImportError, OSError, _SelectionFailure):
        return SelectionResult('dependency_unavailable')
    import gc
    initialized = False
    try:
        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        initialized = True
        uia = client.GetModule(_system_typelib())
        return _com_read(client, uia, target)
    except _SelectionFailure as failure:
        return SelectionResult(failure.status)
    except Exception:
        return SelectionResult('selection_failed')
    finally:
        # Provider interfaces leave _com_read before apartment teardown.
        gc.collect()
        if initialized:
            comtypes.CoUninitialize()


def main():
    import struct
    try:
        length = struct.unpack('!I', read_exact(sys.stdin.buffer, 4))[0]
        if length > REQUEST_LIMIT:
            raise ValueError('selection request limit')
        target = decode_request(read_exact(sys.stdin.buffer, length))
        if sys.stdin.buffer.read(1) != b'':
            raise ValueError('trailing selection request')
        result = run_native(target)
        data = encode_response(result.status, result.text)
    except Exception:
        data = encode_response('selection_failed')
    try:
        view = memoryview(data)
        while view:
            written = sys.stdout.buffer.write(view)
            if not written or written > len(view):
                return 2
            view = view[written:]
        sys.stdout.buffer.flush()
    except (OSError, ValueError):
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
