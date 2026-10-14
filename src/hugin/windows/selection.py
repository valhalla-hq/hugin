"""Deadline-bound one-shot UIA probe; no COM/provider calls on the controller.

Private anonymous stdio carries a small target request and one bounded UTF-8
response. Provider text/exception payloads never enter diagnostics or stderr.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time

from hugin.windows.clipboard import MAX_TEXT_BYTES, ClipboardFailure, WindowTarget,UiaTargetIdentity

REQUEST_LIMIT = 4092
PROBE_MEMORY = 256 * 1024 * 1024
HEADER = struct.Struct('!BBI')
STATUS_CODES = {
    'captured': 0, 'selection_empty': 1, 'selection_unsupported': 2,
    'target_changed': 3, 'selection_limit': 4, 'selection_failed': 5,
    'dependency_unavailable': 6, 'cancelled': 7,
}
CODE_STATUSES = {code: status for status, code in STATUS_CODES.items()}


@dataclass(frozen=True)
class SelectionResult:
    status: str
    text: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TargetResult:
    status: str
    identity: UiaTargetIdentity | None = None


TARGET_CODES={'target_captured':0,'target_unverifiable':1,'target_changed':3,
              'target_probe_failed':5,'dependency_unavailable':6,'cancelled':7}


def read_exact(stream, length):
    data = bytearray()
    while len(data) < length:
        chunk = stream.read(length - len(data))
        if not isinstance(chunk, bytes) or not chunk or len(chunk) > length - len(data):
            raise ValueError('invalid selection frame')
        data.extend(chunk)
    return bytes(data)


def decode_operation(data: bytes):
    if len(data) > REQUEST_LIMIT:
        raise ValueError('selection request limit')
    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError('duplicate selection key')
            result[key] = item
        return result
    value = json.loads(data, object_pairs_hook=unique)
    if not isinstance(value,dict) or type(value.get('version')) is not int:
        raise ValueError('selection request version')
    if value['version']==1 and set(value)=={'version','target'}:operation='selection'
    elif value['version']==2 and set(value)=={'version','operation','target'} and value['operation']=='target':operation='target'
    else:raise ValueError('selection request version')
    target = value['target']
    keys = {'hwnd', 'focus', 'pid', 'thread', 'process_created', 'control_class', 'caret', 'selection', 'editable','package_family'}
    if not isinstance(target, dict) or set(target) != keys:
        raise ValueError('selection target fields')
    for name in ('hwnd', 'focus', 'process_created', 'pid', 'thread'):
        if type(target[name]) is not int or not 0 < target[name] < 1 << (32 if name in ('pid', 'thread') else 64):
            raise ValueError('selection target identity')
    if not isinstance(target['control_class'], str) or not 0 < len(target['control_class']) <= 256 or '\0' in target['control_class']:
        raise ValueError('selection control class')
    if type(target['editable']) is not bool:
        raise ValueError('selection editability')
    family=target['package_family']
    if family is not None and (not isinstance(family,str) or not 17<=len(family)<=64 or '\0' in family):
        raise ValueError('selection package family')
    for name, count in (('caret', 5), ('selection', 2)):
        item = target[name]
        if item is not None:
            if not isinstance(item, list) or len(item) != count or any(type(part) is not int for part in item):
                raise ValueError('selection target range')
            if name == 'selection' and not 0 <= item[0] <= item[1] < 1 << 32:
                raise ValueError('selection target range')
            if name == 'caret' and (not 0 < item[0] < 1 << 64 or any(not -(1 << 31) <= part < 1 << 31 for part in item[1:])):
                raise ValueError('selection target caret')
            target[name] = tuple(item)
    return operation,WindowTarget(**target)


def decode_request(data:bytes)->WindowTarget:
    return decode_operation(data)[1]


def encode_request(target: WindowTarget,*,operation='selection') -> bytes:
    if not isinstance(target,WindowTarget):raise ValueError('invalid native target')
    fields=asdict(target.without_uia);fields.pop('uia')
    envelope={'version':1,'target':fields} if operation=='selection' else {'version':2,'operation':operation,'target':fields}
    data = json.dumps(envelope, ensure_ascii=True,
                      separators=(',', ':')).encode('utf-8')
    decode_request(data)
    return struct.pack('!I', len(data)) + data


def _decode_identity(value):
    if not isinstance(value,dict) or set(value)!={'focus_id','root_id','element_id','focus_pid','position'}:
        raise ValueError('target metadata fields')
    for name in ('focus_id','root_id','element_id'):
        parts=value[name]
        if not isinstance(parts,list):
            raise ValueError('target runtime identity')
        value[name]=tuple(parts)
    return UiaTargetIdentity(**value)


def encode_target_response(result:TargetResult)->bytes:
    if result.status not in TARGET_CODES:raise ValueError('target status')
    if result.status=='target_captured':
        if not isinstance(result.identity,UiaTargetIdentity):raise ValueError('missing target metadata')
        data=json.dumps(asdict(result.identity),separators=(',',':')).encode('ascii')
        _decode_identity(json.loads(data))
        if len(data)>REQUEST_LIMIT:raise ValueError('target metadata limit')
    else:
        if result.identity is not None:raise ValueError('unexpected target metadata')
        data=b''
    return HEADER.pack(2,TARGET_CODES[result.status],len(data))+data


def decode_target_response(stream)->TargetResult:
    version,code,length=HEADER.unpack(read_exact(stream,HEADER.size))
    codes={code:status for status,code in TARGET_CODES.items()}
    if version!=2 or code not in codes or length>REQUEST_LIMIT or (code==0)!=(length>0):
        raise ValueError('invalid target frame')
    def unique(pairs):
        value={}
        for name,item in pairs:
            if name in value:raise ValueError('duplicate target metadata')
            value[name]=item
        return value
    identity=_decode_identity(json.loads(read_exact(stream,length),object_pairs_hook=unique)) if length else None
    if stream.read(1)!=b'':raise ValueError('trailing target metadata')
    return TargetResult(codes[code],identity)


def encode_response(status: str, text: str | None = None) -> bytes:
    if status not in STATUS_CODES:
        raise ValueError('selection status')
    if status == 'captured':
        if not isinstance(text, str) or not text or '\0' in text or len(text) > MAX_TEXT_BYTES:
            raise ValueError('selection text')
        data = text.encode('utf-8')
        if len(data) > MAX_TEXT_BYTES:
            raise ValueError('selection text limit')
    else:
        if text is not None:
            raise ValueError('unexpected selection text')
        data = b''
    return HEADER.pack(1, STATUS_CODES[status], len(data)) + data


def decode_response(stream) -> SelectionResult:
    version, code, length = HEADER.unpack(read_exact(stream, HEADER.size))
    if version != 1 or code not in CODE_STATUSES or length > MAX_TEXT_BYTES:
        raise ValueError('invalid selection header')
    status = CODE_STATUSES[code]
    if (status == 'captured') != (length > 0):
        raise ValueError('invalid selection body')
    text = read_exact(stream, length).decode('utf-8') if length else None
    if text is not None and '\0' in text:
        raise ValueError('invalid selection text')
    if stream.read(1) != b'':
        raise ValueError('trailing selection data')
    return SelectionResult(status, text)


class SelectionProbe:
    def __init__(self, *, spawn=None, timeout=2.0, cleanup_timeout=3.0):
        if not 0 < timeout <= 5 or not 0 < cleanup_timeout <= 5:
            raise ValueError('invalid selection deadline')
        self.spawn, self.timeout, self.cleanup_timeout = spawn, timeout, cleanup_timeout
        self._lock = threading.Lock()
        self._process = None
        self._threads: list[threading.Thread] = []

    def read(self, target: WindowTarget, cancelled) -> SelectionResult:
        return self._read(target,cancelled,operation='selection')

    def capture_target(self,target:WindowTarget,cancelled)->TargetResult:
        return self._read(target,cancelled,operation='target')

    def _read(self,target,cancelled,*,operation):
        target_mode=operation=='target'
        result_type=TargetResult if target_mode else SelectionResult
        failed='target_probe_failed' if target_mode else 'selection_failed'
        busy='target_probe_busy' if target_mode else 'selection_busy'
        pending='target_cleanup_pending' if target_mode else 'selection_cleanup_pending'
        cleanup_failed='target_cleanup_failed' if target_mode else 'selection_cleanup_failed'
        timeout='target_probe_timeout' if target_mode else 'selection_timeout'
        if not self._lock.acquire(blocking=False):
            return result_type(busy)
        try:
            if self._process is not None:
                return result_type(pending)
            if cancelled():
                return result_type('cancelled')
            try:
                request = encode_request(target,operation=operation)
            except (ValueError, TypeError, UnicodeError):
                return result_type('target_changed')
            if self.spawn is None:
                from hugin.windows.process import OwnedProcess
                self.spawn = OwnedProcess
            deadline = time.monotonic() + self.timeout
            try:
                self._process = self.spawn(
                    [sys.executable, '-I', '-B', '-u', str(Path(__file__).with_name('selection_probe.py').resolve())],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    close_fds=True, creationflags=0x08000000, memory_limit=PROBE_MEMORY)
            except Exception as failure:
                self._process = getattr(failure, 'owner', None)
                return result_type(cleanup_failed if self._process is not None else failed)
            process = self._process
            done = threading.Event()
            outcome = {'result': result_type(failed), 'fault': False}
            stdin, stdout, stderr = process.stdin, process.stdout, process.stderr

            def write():
                try:
                    view = memoryview(request)
                    while view:
                        written = stdin.write(view)
                        if not written or written > len(view):
                            raise ValueError('invalid selection write')
                        view = view[written:]
                    stdin.close()
                except Exception:
                    outcome['fault'] = True
                    outcome['result'] = result_type(failed)
                    done.set()

            def read():
                try:
                    outcome['result'] = decode_target_response(stdout) if target_mode else decode_response(stdout)
                except Exception:
                    outcome['fault'] = True
                    outcome['result'] = result_type(failed)
                finally:
                    done.set()

            def drain():
                try:
                    if stderr.read(4096):
                        outcome['fault'] = True
                        done.set()
                except Exception:
                    outcome['fault'] = True
                    done.set()

            self._threads = []
            result = result_type(failed)
            try:
                for name, function in (('write', write), ('read', read), ('stderr', drain)):
                    thread = threading.Thread(target=function, daemon=True, name='hugin-selection-' + name)
                    self._threads.append(thread)
                    thread.start()
                while not done.wait(0.01):
                    if cancelled():
                        result = result_type('cancelled')
                        break
                    if time.monotonic() >= deadline:
                        result = result_type(timeout)
                        break
                else:
                    result = outcome['result']
                    if not outcome['fault']:
                        try:
                            if process.wait(max(0, deadline - time.monotonic())) != 0:
                                result = result_type(failed)
                        except subprocess.TimeoutExpired:
                            result = result_type(timeout)
                if cancelled():
                    result = result_type('cancelled')
            except Exception:
                result = result_type(failed)
            finally:
                try:
                    self._cleanup()
                except Exception:
                    result = result_type(cleanup_failed)
            if outcome['fault'] and result.status not in (cleanup_failed,timeout,'cancelled'):
                return result_type(failed)
            return result
        finally:
            self._lock.release()

    def _cleanup(self):
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.kill()
        self._process.wait(self.cleanup_timeout)
        deadline = time.monotonic() + 1
        for thread in self._threads:
            if thread.ident is not None:
                thread.join(max(0, deadline - time.monotonic()))
        if any(thread.is_alive() for thread in self._threads):
            raise ClipboardFailure('selection_cleanup_failed')
        self._process.close()
        self._process = None
        self._threads = []

    def close(self):
        with self._lock:
            try:
                self._cleanup()
            except Exception:
                raise ClipboardFailure('selection_cleanup_failed') from None
