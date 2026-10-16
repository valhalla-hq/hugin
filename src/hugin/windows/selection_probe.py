"""One-shot comtypes UIA reader. Executed only inside SelectionProbe's job."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hugin.windows.selection import (REQUEST_LIMIT, SelectionResult,
                                     encode_response, read_exact,TargetResult,
                                     decode_operation,encode_target_response)
from hugin.windows.clipboard import MAX_TEXT_BYTES,UiaTargetIdentity


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


def _edit_pattern(focus,uia):
    if not focus or not _flag(focus.CurrentHasKeyboardFocus):
        raise _SelectionFailure('target_changed')
    if (focus.CurrentControlType not in (uia.UIA_EditControlTypeId,uia.UIA_ComboBoxControlTypeId) or not _flag(focus.CurrentIsEnabled)
            or _flag(focus.CurrentIsPassword)):
        raise _SelectionFailure('target_unverifiable')
    for identity in (uia.UIA_IsTextPatternAvailablePropertyId,uia.UIA_IsValuePatternAvailablePropertyId):
        if focus.GetCurrentPropertyValue(identity) is not True:
            raise _SelectionFailure('target_unverifiable')
    value=focus.GetCurrentPattern(uia.UIA_ValuePatternId).QueryInterface(uia.IUIAutomationValuePattern)
    if _flag(value.CurrentIsReadOnly):raise _SelectionFailure('target_unverifiable')
    pattern=focus.GetCurrentPattern(uia.UIA_TextPatternId).QueryInterface(uia.IUIAutomationTextPattern)
    if type(pattern.SupportedTextSelection) is not int or pattern.SupportedTextSelection not in (1,2):
        raise _SelectionFailure('target_unverifiable')
    return pattern


def _bind_edit(automation,uia,target):
    """A focused Edit/ComboBox provider, never an ancestor or class whitelist."""
    focus=automation.GetFocusedElement();root=automation.ElementFromHandle(target.hwnd)
    if not root:raise _SelectionFailure('target_changed')
    pattern=_edit_pattern(focus,uia)
    pid=focus.CurrentProcessId
    if type(pid) is not int or not 0<pid<1<<32 or root.CurrentProcessId!=target.pid:
        raise _SelectionFailure('target_changed')
    current=focus
    for _ in range(64):
        if not current:break
        if automation.CompareElements(current,root):
            return _Binding(_identity(focus),_identity(root),_identity(focus),pid,pattern)
        current=automation.RawViewWalker.GetParentElement(current)
    raise _SelectionFailure('target_changed')


def _edit_enclosure(automation,binding,text_range):
    enclosing=text_range.GetEnclosingElement();origin=None
    for _ in range(64):
        if not enclosing or _flag(enclosing.CurrentIsPassword):
            raise _SelectionFailure('target_unverifiable')
        identity=_identity(enclosing)
        if origin is None:origin=identity
        if identity==binding.element_id:return origin
        enclosing=automation.RawViewWalker.GetParentElement(enclosing)
    raise _SelectionFailure('target_unverifiable')


def _prefix_units(prefix):
    text=None
    try:
        text=prefix.GetText(MAX_TEXT_BYTES+1)
        if not isinstance(text,str) or len(text)>MAX_TEXT_BYTES or '\0' in text:
            raise _SelectionFailure('target_unverifiable')
        try:units=len(text.encode('utf-16-le'))//2
        except UnicodeError:raise _SelectionFailure('target_unverifiable') from None
        if units>MAX_TEXT_BYTES:raise _SelectionFailure('target_unverifiable')
        return units
    finally:
        text=None  # Only the integer leaves this isolated provider call.


def _plain_range(text_range):
    # Plain text can omit embedded object boundaries. Unknown is not empty.
    children=text_range.GetChildren()
    if not children or type(children.Length) is not int or children.Length!=0:
        raise _SelectionFailure('target_unverifiable')


def _endpoint(selected,endpoint):
    point=selected.Clone()
    point.MoveEndpointByRange(1-endpoint,selected,endpoint)
    if (point.CompareEndpoints(0,point,1)!=0
            or point.CompareEndpoints(0,selected,endpoint)!=0):
        raise _SelectionFailure('target_unverifiable')
    return point


def _range_snapshot(automation,binding):
    selected=_selected(binding.pattern)
    if selected is None:
        raise _SelectionFailure('target_unverifiable')
    ordering=selected.CompareEndpoints(0,selected,1)
    if ordering>0:
        raise _SelectionFailure('target_unverifiable')
    document=binding.pattern.DocumentRange
    if not document:raise _SelectionFailure('target_unverifiable')
    _edit_enclosure(automation,binding,document)
    _plain_range(document)
    start=selected.Clone() if ordering==0 else _endpoint(selected,0)
    end=start if ordering==0 else _endpoint(selected,1)
    ids=[];relations=[]
    for index,point in enumerate((start,end)):
        if index and point is start:
            ids.append(ids[0]);relations.append(relations[0]);continue
        if point.CompareEndpoints(0,document,0)<0:
            raise _SelectionFailure('target_unverifiable')
        identity=_edit_enclosure(automation,binding,point)
        # A proven descendant may expose its trailing boundary beyond the
        # focused provider's structural End. Preserve that affinity per end.
        relation=point.CompareEndpoints(0,document,1)
        relation=(relation>0)-(relation<0)
        if relation>0 and identity==binding.element_id:
            raise _SelectionFailure('target_unverifiable')
        ids.append(identity);relations.append(relation)
    return (start if ordering==0 else selected.Clone()),tuple(ids),tuple(relations),document,(start,end)


def _measure_range(automation,binding):
    selected,ids,relations,document,points=_range_snapshot(automation,binding)
    positions=[]
    for index,point in enumerate(points):
        if index and point is points[0]:positions.append(positions[0]);continue
        if point.CompareEndpoints(0,document,0)==0:positions.append(0);continue
        prefix=document.Clone();prefix.MoveEndpointByRange(1,point,0)
        if (prefix.CompareEndpoints(0,document,0)!=0
                or prefix.CompareEndpoints(1,point,0)!=0):
            raise _SelectionFailure('target_unverifiable')
        _edit_enclosure(automation,binding,prefix)
        _plain_range(prefix)
        positions.append(_prefix_units(prefix))
    if (positions[0]>positions[1]
            or (positions[0]==positions[1] and selected.CompareEndpoints(0,selected,1)!=0)):
        # Plain text cannot prove an invisible/non-injective selected span.
        raise _SelectionFailure('target_unverifiable')
    identity=UiaTargetIdentity(binding.focus_id,binding.root_id,*ids,binding.focus_pid,
        tuple(positions),*relations)
    return identity,selected


def _confirm_range(automation,uia,binding,identity,measured):
    """Fresh selection/editability after the final GetText; no further text."""
    focus=automation.GetFocusedElement()
    if not focus or _identity(focus)!=identity.focus_id:
        raise _SelectionFailure('target_changed')
    binding.pattern=_edit_pattern(focus,uia)
    final,ids,relations,_,_=_range_snapshot(automation,binding)
    if (ids!=(identity.start_id,identity.end_id)
            or relations!=(identity.start_relation,identity.end_relation)
            or any(measured.CompareEndpoints(endpoint,final,endpoint)!=0 for endpoint in (0,1))):
        raise _SelectionFailure('target_changed')


@dataclass
class _TargetProof:
    identity: UiaTargetIdentity
    binding: _Binding
    verified_at: float


def _target_proof(automation,uia,target,native_target,cancelled):
    if cancelled():raise _SelectionFailure('cancelled')
    if native_target()!=target:raise _SelectionFailure('target_changed')
    first=_bind_edit(automation,uia,target)
    identity,original=_measure_range(automation,first)
    if cancelled():raise _SelectionFailure('cancelled')
    _confirm_focus(automation,first,target,native_target)
    second=_bind_edit(automation,uia,target)
    current_identity,current=_measure_range(automation,second)
    if (identity!=current_identity
            or any(original.CompareEndpoints(endpoint,current,endpoint)!=0 for endpoint in (0,1))):
        raise _SelectionFailure('target_changed')
    _confirm_range(automation,uia,second,identity,current)
    _confirm_focus(automation,second,target,native_target)
    if cancelled():raise _SelectionFailure('cancelled')
    return _TargetProof(identity,second,time.monotonic())


def _target_failure(failure):
    return TargetResult('target_unverifiable' if failure.status=='selection_unsupported' else failure.status)


def read_uia_target(automation,uia,target,native_target,cancelled):
    try:
        proof=_target_proof(automation,uia,target,native_target,cancelled)
        return TargetResult('target_captured',proof.identity,proof.verified_at)
    except _SelectionFailure as failure:
        return _target_failure(failure)
    except Exception:
        return TargetResult('target_probe_failed')


def confirm_uia_target(automation,uia,target,native_target,proof):
    """Warm single confirmation; no repeated walk from the Edit to its root."""
    try:
        _confirm_focus(automation,proof.binding,target,native_target)
        root=automation.ElementFromHandle(target.hwnd)
        if not root or _identity(root)!=proof.identity.root_id or root.CurrentProcessId!=target.pid:
            return TargetResult('target_changed')
        focus=automation.GetFocusedElement()
        if not focus or _identity(focus)!=proof.identity.focus_id:return TargetResult('target_changed')
        pattern=_edit_pattern(focus,uia)
        binding=_Binding(proof.identity.focus_id,proof.identity.root_id,
            proof.identity.focus_id,proof.identity.focus_pid,pattern)
        identity,current=_measure_range(automation,binding)
        if identity!=proof.identity:
            return TargetResult('target_changed')
        # Provider calls above can span a user selection/editability change.
        # Reacquire the current Edit and compare a second fresh local integer,
        # not only endpoints of COM ranges that may move with document edits.
        focus=automation.GetFocusedElement()
        if not focus or _identity(focus)!=proof.identity.focus_id:return TargetResult('target_changed')
        binding.pattern=_edit_pattern(focus,uia)
        final_identity,measured=_measure_range(automation,binding)
        if (final_identity!=proof.identity
                or any(current.CompareEndpoints(endpoint,measured,endpoint)!=0 for endpoint in (0,1))):
            return TargetResult('target_changed')
        # GetText can block while selection or editability changes. Reacquire
        # these facts after the last text read, without reading further text.
        _confirm_range(automation,uia,binding,proof.identity,measured)
        _confirm_focus(automation,proof.binding,target,native_target)
        return TargetResult('target_captured',proof.identity,time.monotonic())
    except _SelectionFailure as failure:return _target_failure(failure)
    except Exception:return TargetResult('target_probe_failed')


def _write_frame(data):
    view=memoryview(data)
    while view:
        written=sys.stdout.buffer.write(view)
        if not written or written>len(view):raise OSError('invalid probe write')
        view=view[written:]
    sys.stdout.buffer.flush()


def _com_delivery(client,uia,target,native):
    automation=client.CreateObject(uia.CUIAutomation,interface=uia.IUIAutomation,clsctx=1)
    try:proof=_target_proof(automation,uia,target,native.capture_native_target,lambda:False)
    except _SelectionFailure as failure:
        _write_frame(encode_target_response(_target_failure(failure)));return
    _write_frame(encode_target_response(TargetResult('target_captured',proof.identity,proof.verified_at)))
    # Exactly one private confirmation command. EOF and any other byte reject.
    if read_exact(sys.stdin.buffer,1)!=b'\x01' or sys.stdin.buffer.read(1)!=b'':
        raise ValueError('invalid delivery confirmation')
    _write_frame(encode_target_response(confirm_uia_target(automation,uia,target,
        native.capture_native_target,proof)))
    # The immutable attestation channel ends before native/COM/interpreter
    # unwind. The parent still owns this process family until off-owner close.
    stdout_fd,stderr_fd=sys.stdout.fileno(),sys.stderr.fileno()
    sys.stdout.close();sys.stderr.close()
    # CPython's standard FileIO owns the wrapper with closefd=False. Closing
    # that wrapper alone does not publish pipe EOF before interpreter exit.
    os.close(stdout_fd);os.close(stderr_fd)


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


def _com_read(client, uia, target,operation='selection'):
    from hugin.windows.clipboard import NativeClipboard, MAX_TEXT_BYTES
    native = NativeClipboard()
    try:
        if operation=='delivery':
            return _com_delivery(client,uia,target,native)
        automation = client.CreateObject(uia.CUIAutomation, interface=uia.IUIAutomation, clsctx=1)
        if operation=='target':
            return read_uia_target(automation,uia,target,native.capture_native_target,lambda:False)
        return read_uia_selection(automation, uia, target, native.capture_native_target, lambda: False, MAX_TEXT_BYTES)
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


def run_native(target,operation='selection'):
    result_type=TargetResult if operation in ('target','delivery') else SelectionResult
    if sys.platform != 'win32':
        return result_type('dependency_unavailable')
    # comtypes initializes its importing thread. Select MTA before import;
    # its process-shutdown hook balances that initial apartment reference.
    sys.coinit_flags = 0
    try:
        comtypes, client = _load_comtypes()
    except (ImportError, OSError, _SelectionFailure):
        return result_type('dependency_unavailable')
    import gc
    initialized = False
    try:
        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
        initialized = True
        uia = client.GetModule(_system_typelib())
        return _com_read(client, uia, target,operation)
    except _SelectionFailure as failure:
        return result_type(failure.status)
    except Exception:
        return result_type('target_probe_failed' if operation in ('target','delivery') else 'selection_failed')
    finally:
        # Provider interfaces leave _com_read before apartment teardown.
        gc.collect()
        if initialized:
            comtypes.CoUninitialize()


def main():
    import struct
    operation='selection'
    try:
        length = struct.unpack('!I', read_exact(sys.stdin.buffer, 4))[0]
        if length > REQUEST_LIMIT:
            raise ValueError('selection request limit')
        operation,target = decode_operation(read_exact(sys.stdin.buffer, length))
        if operation!='delivery' and sys.stdin.buffer.read(1) != b'':
            raise ValueError('trailing selection request')
        result = run_native(target,operation)
        if operation=='delivery' and result is None:return 0
        data = encode_target_response(result) if operation in ('target','delivery') else encode_response(result.status, result.text)
    except Exception:
        data = encode_target_response(TargetResult('target_probe_failed')) if operation in ('target','delivery') else encode_response('selection_failed')
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
