"""User/session-scoped named mutex; only an acquired handle can release it."""
import ctypes
from ctypes import wintypes as W
import hashlib
import sys
import threading

from hugin.errors import HuginError


class InstanceGuard:
    def __init__(self, *, user_sid=None, backend=None):
        self.backend = backend
        self.user_sid = user_sid
        self.handle = None
        self.acquired = False
        self.owner_thread = None

    def acquire(self):
        if self.handle is not None:
            return self.acquired
        if self.backend is None:
            self.backend = NativeMutex()
        sid = self.user_sid or self.backend.user_sid()
        if not isinstance(sid, str) or not sid.startswith('S-1-'):
            raise HuginError('input_failed', 'instance_identity')
        name = 'Local\\Hugin.v1.' + hashlib.sha256(sid.encode('ascii')).hexdigest()[:32]
        self.handle, self.acquired = self.backend.acquire(name)
        self.owner_thread = threading.get_ident()
        return self.acquired

    def close(self):
        if self.handle is None:
            return
        if self.owner_thread != threading.get_ident():
            raise HuginError('input_failed', 'instance_owner_thread')
        try:
            self.backend.release(self.handle, self.acquired)
        except HuginError as failure:
            if getattr(failure, 'mutex_released', False):
                self.acquired = False
            raise
        self.handle = None
        self.acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_):
        self.close()


class NativeMutex:
    def __init__(self):
        if sys.platform != 'win32':
            raise HuginError('unsupported', 'instance')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.advapi = ctypes.WinDLL('advapi32', use_last_error=True)
        for library, name, arguments, result in (
            (self.kernel, 'CreateMutexW', [W.LPVOID, W.BOOL, W.LPCWSTR], W.HANDLE),
            (self.kernel, 'WaitForSingleObject', [W.HANDLE, W.DWORD], W.DWORD),
            (self.kernel, 'ReleaseMutex', [W.HANDLE], W.BOOL),
            (self.kernel, 'CloseHandle', [W.HANDLE], W.BOOL),
            (self.kernel, 'GetCurrentProcess', [], W.HANDLE),
            (self.kernel, 'LocalFree', [W.HLOCAL], W.HLOCAL),
            (self.advapi, 'OpenProcessToken', [W.HANDLE, W.DWORD, ctypes.POINTER(W.HANDLE)], W.BOOL),
            (self.advapi, 'GetTokenInformation', [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, ctypes.POINTER(W.DWORD)], W.BOOL),
            (self.advapi, 'ConvertSidToStringSidW', [W.LPVOID, ctypes.POINTER(W.LPWSTR)], W.BOOL),
        ):
            function = getattr(library, name)
            function.argtypes, function.restype = arguments, result

    def user_sid(self):
        token = W.HANDLE()
        if not self.advapi.OpenProcessToken(self.kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
            raise HuginError('input_failed', 'instance_identity')
        try:
            size = W.DWORD()
            self.advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
            if not 0 < size.value <= 64 * 1024:
                raise HuginError('input_failed', 'instance_identity')
            buffer = ctypes.create_string_buffer(size.value)
            if not self.advapi.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)):
                raise HuginError('input_failed', 'instance_identity')
            sid_pointer = ctypes.cast(buffer, ctypes.POINTER(W.LPVOID))[0]
            text = W.LPWSTR()
            if not self.advapi.ConvertSidToStringSidW(sid_pointer, ctypes.byref(text)):
                raise HuginError('input_failed', 'instance_identity')
            try:
                return text.value
            finally:
                if self.kernel.LocalFree(ctypes.cast(text, W.HLOCAL)):
                    raise HuginError('input_failed', 'instance_identity_cleanup')
        finally:
            if not self.kernel.CloseHandle(token):
                raise HuginError('input_failed', 'instance_identity_cleanup')

    def acquire(self, name):
        handle = self.kernel.CreateMutexW(None, False, name)
        if not handle:
            raise HuginError('input_failed', 'instance_mutex')
        result = self.kernel.WaitForSingleObject(handle, 0)
        if result in (0, 0x80):  # acquired / abandoned
            return handle, True
        if result == 0x102:
            return handle, False
        if not self.kernel.CloseHandle(handle):
            raise HuginError('input_failed', 'instance_cleanup')
        raise HuginError('input_failed', 'instance_mutex')

    def release(self, handle, acquired):
        if acquired and not self.kernel.ReleaseMutex(handle):
            raise HuginError('input_failed', 'instance_cleanup')
        if not self.kernel.CloseHandle(handle):
            failure = HuginError('input_failed', 'instance_cleanup')
            failure.mutex_released = acquired
            raise failure
