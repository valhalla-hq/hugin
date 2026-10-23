"""Deadline-bound one-shot UIA probe; no COM/provider calls on the controller.

Private anonymous stdio carries a small target request and one bounded UTF-8
response. Provider text/exception payloads never enter diagnostics or stderr.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time

from hugin.windows.clipboard import MAX_TEXT_BYTES, ClipboardFailure, WindowTarget

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


def read_exact(stream, length):
    data = bytearray()
    while len(data) < length:
        chunk = stream.read(length - len(data))
        if not isinstance(chunk, bytes) or not chunk or len(chunk) > length - len(data):
            raise ValueError('invalid selection frame')
        data.extend(chunk)
    return bytes(data)


def write_all(stream,data):
    view=memoryview(data)
    while view:
        written=stream.write(view)
        if not written or written>len(view):raise ValueError('invalid probe write')
        view=view[written:]


def decode_request(data: bytes)->WindowTarget:
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
    if (value['version']!=5 or set(value)!={'version','operation','target'}
            or value['operation'] != 'selection'):
        raise ValueError('selection request version')
    target = value['target']
    keys = {'hwnd', 'focus', 'pid', 'thread', 'process_created', 'control_class', 'caret', 'selection', 'native_editable','package_family'}
    if not isinstance(target, dict) or set(target) != keys:
        raise ValueError('selection target fields')
    for name in ('hwnd', 'focus', 'process_created', 'pid', 'thread'):
        if type(target[name]) is not int or not 0 < target[name] < 1 << (32 if name in ('pid', 'thread') else 64):
            raise ValueError('selection target identity')
    if not isinstance(target['control_class'], str) or not 0 < len(target['control_class']) <= 256 or '\0' in target['control_class']:
        raise ValueError('selection control class')
    if type(target['native_editable']) is not bool:
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
    return WindowTarget(**target)


def encode_request(target: WindowTarget) -> bytes:
    if not isinstance(target,WindowTarget):raise ValueError('invalid native target')
    fields=asdict(target)
    envelope={'version':5,'operation':'selection','target':fields}
    data = json.dumps(envelope, ensure_ascii=True,
                      separators=(',', ':')).encode('utf-8')
    decode_request(data)
    return struct.pack('!I', len(data)) + data


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

    def _spawn_process(self):
        if self.spawn is None:
            from hugin.windows.process import OwnedProcess
            self.spawn=OwnedProcess
        executable=Path(sys.executable).resolve();environment=None
        if sys.platform=='win32' and sys.prefix!=sys.base_prefix:
            # The Windows venv redirector retains inherited pipe handles until
            # its child exits. Start the same base interpreter directly, using
            # CPython's own launcher context to retain this exact venv.
            base=Path(sys._base_executable).resolve()
            if not base.is_file() or not base.is_relative_to(Path(sys.base_prefix).resolve()):
                raise ClipboardFailure('dependency_unavailable')
            environment=dict(os.environ)
            environment['__PYVENV_LAUNCHER__']=str(executable)
            executable=base
        return self.spawn([str(executable),'-I','-B','-u',str(Path(__file__).with_name('selection_probe.py').resolve())],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            close_fds=True,creationflags=0x08000000,memory_limit=PROBE_MEMORY,env=environment)

    def _spawn_failure(self,error,failed,cleanup_failed):
        """Retain partial ownership before normalizing known launch failures."""
        self._process=getattr(error,'owner',None)
        if self._process is not None:return cleanup_failed
        if (isinstance(error,ClipboardFailure) and type(error.status) is str
                and error.status=='dependency_unavailable'):
            return 'dependency_unavailable'
        return failed

    def read(self,target:WindowTarget,cancelled)->SelectionResult:
        result_type=SelectionResult
        failed='selection_failed'
        busy='selection_busy'
        pending='selection_cleanup_pending'
        cleanup_failed='selection_cleanup_failed'
        timeout='selection_timeout'
        if not self._lock.acquire(blocking=False):
            return result_type(busy)
        try:
            if self._process is not None:
                return result_type(pending)
            if cancelled():
                return result_type('cancelled')
            try:
                request = encode_request(target)
            except (ValueError, TypeError, UnicodeError):
                return result_type('target_changed')
            deadline = time.monotonic() + self.timeout
            try:
                self._process=self._spawn_process()
            except Exception as failure:
                return result_type(self._spawn_failure(failure,failed,cleanup_failed))
            process = self._process
            done = threading.Event()
            outcome = {'result': result_type(failed), 'fault': False}
            stdin, stdout, stderr = process.stdin, process.stdout, process.stderr

            def write():
                try:
                    write_all(stdin,request)
                    stdin.close()
                except Exception:
                    outcome['fault'] = True
                    outcome['result'] = result_type(failed)
                    done.set()

            def read():
                try:
                    outcome['result'] = decode_response(stdout)
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
        try:code=self._process.wait(self.cleanup_timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(self.cleanup_timeout)
            # The actual completed channel is valid, but normal unwind failed.
            code=1
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
