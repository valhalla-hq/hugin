"""Popen-shaped worker owner: suspended creation, job assignment, then resume.

The held job includes interpreter redirectors and descendants. No PID/name
lookup grants cleanup authority. Handles remain held until family exit.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import sys
import time

from hugin.errors import HuginError


class OwnedProcess:
    def __init__(self, command, *, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE, startupinfo=None, close_fds=True,
                 creationflags=0x08000000, cwd=None, env=None, backend=None,
                 memory_limit=None):
        if not isinstance(command, (list, tuple)) or not command or any(
                not isinstance(part, str) or '\0' in part for part in command):
            raise ValueError('command must be an argument list')
        if not close_fds or creationflags & ~0x08000000:
            raise ValueError('only hidden creation with explicit handles is supported')
        if any(value not in (subprocess.PIPE, subprocess.DEVNULL) for value in (stdin, stdout, stderr)):
            raise ValueError('stdio must use PIPE or DEVNULL')
        if memory_limit is not None and (type(memory_limit) is not int or
                not 0 < memory_limit < 1 << (ctypes.sizeof(ctypes.c_size_t) * 8)):
            raise ValueError('invalid job memory limit')
        attributes = getattr(startupinfo, 'lpAttributeList', None) or {}
        if set(attributes) - {'handle_list'}:
            raise ValueError('unsupported process attribute')
        extra_handles = list(attributes.get('handle_list', []))
        if any(type(handle) is not int or handle <= 0 for handle in extra_handles):
            raise ValueError('invalid inherited handles')
        self.args = list(command)
        self.backend = backend or NativeProcess()
        self.stdin = self.stdout = self.stderr = None
        self.pid = None
        self.returncode = None
        self._process = self._thread = self._job = None
        self._assigned = False
        self._final_metrics = None
        child_descriptors = []
        try:
            self._job = self.backend.create_job() if memory_limit is None else self.backend.create_job(memory_limit)
            stdio = []
            for name, mode, incoming in (('stdin', stdin, True), ('stdout', stdout, False), ('stderr', stderr, False)):
                if mode == subprocess.PIPE:
                    read, write = os.pipe()
                    child, parent = (read, write) if incoming else (write, read)
                    child_descriptors.append(child)
                    os.set_inheritable(child, True)
                    try:
                        setattr(self, name, os.fdopen(parent, 'wb' if incoming else 'rb', buffering=0))
                    except Exception:
                        os.close(parent)
                        raise
                else:
                    child = os.open(os.devnull, os.O_RDONLY if incoming else os.O_WRONLY)
                    child_descriptors.append(child)
                    os.set_inheritable(child, True)
                stdio.append(self.backend.stdio_handle(child))
            self._process, self._thread, self.pid = self.backend.create_suspended(
                list(command), stdio, extra_handles, cwd, env, creationflags)
            self.backend.assign(self._job, self._process)
            self._assigned = True
            self.backend.resume(self._thread)
            self.backend.close_handle(self._thread)
            self._thread = None
        except Exception as failure:
            # Failed creation is still owned. Return an owner on cleanup error
            # so the caller can retain it and keep the engine slot blocked.
            try:
                if self._process is not None:
                    if self.poll() is None:
                        if self._assigned:
                            self.backend.terminate_job(self._job)
                        else:
                            self.backend.terminate_process(self._process)
                    self.wait(5)
                self.close()
            except Exception:
                error = HuginError('worker_failed', 'process_cleanup')
                error.owner = self
                raise error from None
            if isinstance(failure, HuginError):
                raise failure from None
            raise HuginError('worker_failed', 'process_create') from None
        finally:
            for descriptor in child_descriptors:
                os.close(descriptor)

    def poll(self):
        if self.returncode is not None:
            return self.returncode
        if self._process is None:
            return None
        code = self.backend.exit_status(self._process)
        if code is None:
            return None
        if self._assigned and self.backend.active_processes(self._job) != 0:
            return None
        self.returncode = code
        return code

    def wait(self, timeout=None):
        if timeout is not None and timeout < 0:
            timeout = 0
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            result = self.poll()
            if result is not None:
                return result
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(self.args, timeout)
            time.sleep(0.01)

    def terminate(self):
        if self._job is not None and self.poll() is None:
            if self._assigned:
                self.backend.terminate_job(self._job)
            elif self._process is not None:
                self.backend.terminate_process(self._process)

    kill = terminate

    def metrics(self):
        """Held-job accounting; peak commit is not physical working-set RAM."""
        if self._job is None: return self._final_metrics
        if not hasattr(self.backend,'metrics'): return None
        try: return self.backend.metrics(self._job)
        except HuginError: return None

    def close(self):
        if self._process is not None and self.poll() is None:
            raise HuginError('worker_failed', 'process_not_terminal')
        if self._job is not None: self._final_metrics = self.metrics()
        for name in ('stdin', 'stdout', 'stderr'):
            stream = getattr(self, name)
            if stream is not None:
                stream.close()
                setattr(self, name, None)
        for name in ('_thread', '_process', '_job'):
            handle = getattr(self, name)
            if handle is not None:
                self.backend.close_handle(handle)
                setattr(self, name, None)
        if hasattr(self.backend, 'close_pending'):
            self.backend.close_pending()


class _StartupInfo(ctypes.Structure):
    _fields_ = [('cb', W.DWORD), ('lpReserved', W.LPWSTR), ('lpDesktop', W.LPWSTR),
                ('lpTitle', W.LPWSTR), ('dwX', W.DWORD), ('dwY', W.DWORD), ('dwXSize', W.DWORD),
                ('dwYSize', W.DWORD), ('dwXCountChars', W.DWORD), ('dwYCountChars', W.DWORD),
                ('dwFillAttribute', W.DWORD), ('dwFlags', W.DWORD), ('wShowWindow', W.WORD),
                ('cbReserved2', W.WORD), ('lpReserved2', ctypes.POINTER(ctypes.c_byte)),
                ('hStdInput', W.HANDLE), ('hStdOutput', W.HANDLE), ('hStdError', W.HANDLE)]


class _StartupInfoEx(ctypes.Structure):
    _fields_ = [('StartupInfo', _StartupInfo), ('lpAttributeList', W.LPVOID)]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [('hProcess', W.HANDLE), ('hThread', W.HANDLE), ('dwProcessId', W.DWORD), ('dwThreadId', W.DWORD)]


class _BasicLimits(ctypes.Structure):
    _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong), ('PerJobUserTimeLimit', ctypes.c_longlong),
                ('LimitFlags', W.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', W.DWORD),
                ('Affinity', ctypes.c_size_t), ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in ('ReadOperationCount', 'WriteOperationCount',
                'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [('BasicLimitInformation', _BasicLimits), ('IoInfo', _IoCounters),
                ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]


class _BasicAccounting(ctypes.Structure):
    _fields_ = [('TotalUserTime', ctypes.c_longlong), ('TotalKernelTime', ctypes.c_longlong),
                ('ThisPeriodTotalUserTime', ctypes.c_longlong), ('ThisPeriodTotalKernelTime', ctypes.c_longlong),
                ('TotalPageFaultCount', W.DWORD), ('TotalProcesses', W.DWORD),
                ('ActiveProcesses', W.DWORD), ('TotalTerminatedProcesses', W.DWORD)]


class NativeProcess:
    def __init__(self):
        if sys.platform != 'win32':
            raise HuginError('unsupported', 'process_owner')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self._pending_handles: set[int] = set()
        for name, arguments, result in (
            ('CreateJobObjectW', [W.LPVOID, W.LPCWSTR], W.HANDLE),
            ('SetInformationJobObject', [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD], W.BOOL),
            ('QueryInformationJobObject', [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, ctypes.POINTER(W.DWORD)], W.BOOL),
            ('AssignProcessToJobObject', [W.HANDLE, W.HANDLE], W.BOOL),
            ('TerminateJobObject', [W.HANDLE, W.UINT], W.BOOL),
            ('TerminateProcess', [W.HANDLE, W.UINT], W.BOOL),
            ('ResumeThread', [W.HANDLE], W.DWORD), ('CloseHandle', [W.HANDLE], W.BOOL),
            ('GetExitCodeProcess', [W.HANDLE, ctypes.POINTER(W.DWORD)], W.BOOL),
            ('WaitForSingleObject', [W.HANDLE, W.DWORD], W.DWORD),
            ('InitializeProcThreadAttributeList', [W.LPVOID, W.DWORD, W.DWORD, ctypes.POINTER(ctypes.c_size_t)], W.BOOL),
            ('UpdateProcThreadAttribute', [W.LPVOID, W.DWORD, ctypes.c_size_t, W.LPVOID,
                                           ctypes.c_size_t, W.LPVOID, ctypes.POINTER(ctypes.c_size_t)], W.BOOL),
            ('DeleteProcThreadAttributeList', [W.LPVOID], None),
            ('CreateProcessW', [W.LPCWSTR, W.LPWSTR, W.LPVOID, W.LPVOID, W.BOOL, W.DWORD,
                                W.LPVOID, W.LPCWSTR, ctypes.POINTER(_StartupInfoEx),
                                ctypes.POINTER(_ProcessInformation)], W.BOOL),
        ):
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result

    @staticmethod
    def stdio_handle(descriptor):
        import msvcrt
        return msvcrt.get_osfhandle(descriptor)

    def create_job(self, memory_limit=None):
        job = self.kernel.CreateJobObjectW(None, None)
        if not job:
            raise HuginError('worker_failed', 'job_create')
        limits = _ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE; no breakaway.
        if memory_limit is not None:
            limits.BasicLimitInformation.LimitFlags |= 0x200  # JOB_OBJECT_LIMIT_JOB_MEMORY
            limits.JobMemoryLimit = memory_limit
        if not self.kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            if not self.kernel.CloseHandle(job):
                self._pending_handles.add(job)
            raise HuginError('worker_failed', 'job_limits')
        return job

    def create_suspended(self, command, stdio, extra_handles, cwd, env, flags):
        application = str(Path(command[0]).resolve())
        if not Path(application).is_file():
            raise HuginError('worker_failed', 'process_executable')
        command = [application, *command[1:]]
        size = ctypes.c_size_t()
        self.kernel.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
        if not 0 < size.value <= 64 * 1024:
            raise HuginError('worker_failed', 'process_attributes')
        storage = ctypes.create_string_buffer(size.value)
        if not self.kernel.InitializeProcThreadAttributeList(storage, 1, 0, ctypes.byref(size)):
            raise HuginError('worker_failed', 'process_attributes')
        try:
            inherited = list(dict.fromkeys([*stdio, *extra_handles]))
            handles = (W.HANDLE * len(inherited))(*inherited)
            if not self.kernel.UpdateProcThreadAttribute(storage, 0, 0x20002, handles,
                                                         ctypes.sizeof(handles), None, None):
                raise HuginError('worker_failed', 'process_handles')
            startup = _StartupInfoEx()
            startup.StartupInfo.cb = ctypes.sizeof(startup)
            startup.StartupInfo.dwFlags = 0x100  # STARTF_USESTDHANDLES
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = stdio
            startup.lpAttributeList = ctypes.cast(storage, W.LPVOID)
            environment = None
            if env is not None:
                if not isinstance(env, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                                   or '\0' in key + value or '=' in key for key, value in env.items()):
                    raise HuginError('worker_failed', 'process_environment')
                environment = ctypes.create_unicode_buffer('\0'.join(f'{key}={value}' for key, value
                                                                    in sorted(env.items(), key=lambda item: item[0].upper())) + '\0\0')
            information = _ProcessInformation()
            commandline = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
            if not self.kernel.CreateProcessW(application, commandline, None, None, True,
                                              flags | 4 | 0x80000 | 0x400, environment,
                                              str(cwd) if cwd is not None else None,
                                              ctypes.byref(startup), ctypes.byref(information)):
                raise HuginError('worker_failed', 'process_create')
            return information.hProcess, information.hThread, information.dwProcessId
        finally:
            self.kernel.DeleteProcThreadAttributeList(storage)

    def assign(self, job, process):
        if not self.kernel.AssignProcessToJobObject(job, process):
            raise HuginError('worker_failed', 'job_assignment')

    def resume(self, thread):
        if self.kernel.ResumeThread(thread) == 0xFFFFFFFF:
            raise HuginError('worker_failed', 'process_resume')

    def exit_status(self, process):
        status = self.kernel.WaitForSingleObject(process, 0)
        if status == 0x102:
            return None
        code = W.DWORD()
        if status != 0 or not self.kernel.GetExitCodeProcess(process, ctypes.byref(code)):
            raise HuginError('worker_failed', 'process_observe')
        return code.value

    def active_processes(self, job):
        accounting = _BasicAccounting()
        if not self.kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
            raise HuginError('worker_failed', 'job_observe')
        return accounting.ActiveProcesses

    def metrics(self, job):
        accounting,limits = _BasicAccounting(),_ExtendedLimits()
        for kind,value in ((1,accounting),(9,limits)):
            if not self.kernel.QueryInformationJobObject(job,kind,ctypes.byref(value),ctypes.sizeof(value),None):
                raise HuginError('worker_failed','job_metrics')
        return {'cpu_seconds':(accounting.TotalUserTime+accounting.TotalKernelTime)/10000000,
            'peak_job_commit_bytes':limits.PeakJobMemoryUsed}

    def terminate_job(self, job):
        if not self.kernel.TerminateJobObject(job, 1):
            raise HuginError('worker_failed', 'job_terminate')

    def terminate_process(self, process):
        if not self.kernel.TerminateProcess(process, 1):
            raise HuginError('worker_failed', 'process_terminate')

    def close_handle(self, handle):
        if not self.kernel.CloseHandle(handle):
            raise HuginError('worker_failed', 'process_handle_cleanup')

    def close_pending(self):
        for handle in tuple(self._pending_handles):
            if self.kernel.CloseHandle(handle):
                self._pending_handles.remove(handle)
        if self._pending_handles:
            raise HuginError('worker_failed', 'process_handle_cleanup')
