"""Explicit native fixture child: own hidden RichEdit only; never global selection."""
from pathlib import Path
import ctypes
from ctypes import wintypes as W
import gc
import os
import struct
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from hugin.windows.selection import REQUEST_LIMIT, encode_response, read_exact
from hugin.windows.selection_probe import _system_typelib, _identity, _selected, _text, _load_comtypes


class Fixture:
    def __init__(self):
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        for name, args, result in (
            ('CreateWindowExW', [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID], W.HWND),
            ('DestroyWindow', [W.HWND], W.BOOL),
            ('GetMessageW', [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT], ctypes.c_int),
            ('PostThreadMessageW', [W.DWORD, W.UINT, W.WPARAM, W.LPARAM], W.BOOL),
            ('TranslateMessage', [ctypes.POINTER(W.MSG)], W.BOOL),
            ('DispatchMessageW', [ctypes.POINTER(W.MSG)], ctypes.c_ssize_t),
            ('SendMessageTimeoutW', [W.HWND, W.UINT, W.WPARAM, W.LPARAM, W.UINT, W.UINT,
                                     ctypes.POINTER(ctypes.c_size_t)], ctypes.c_ssize_t),
            ('GetWindowThreadProcessId', [W.HWND, ctypes.POINTER(W.DWORD)], W.DWORD),
            ('GetForegroundWindow', [], W.HWND),
            ('GetClipboardSequenceNumber', [], W.DWORD),
        ):
            function = getattr(self.user, name)
            function.argtypes, function.restype = args, result
        self.kernel.GetCurrentThreadId.argtypes = []
        self.kernel.GetCurrentThreadId.restype = W.DWORD
        self.kernel.LoadLibraryExW.argtypes = [W.LPCWSTR, W.HANDLE, W.DWORD]
        self.kernel.LoadLibraryExW.restype = W.HMODULE
        self.kernel.FreeLibrary.argtypes = [W.HMODULE]
        self.kernel.FreeLibrary.restype = W.BOOL
        self.module = self.kernel.LoadLibraryExW(str(Path(_system_typelib()).with_name('msftedit.dll')), None, 0x800)
        if not self.module:
            raise RuntimeError('fixture_richedit_library')
        self.ready = threading.Event()
        self.failed = False
        self.hwnd = self.edit = None
        self.thread_id = 0
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        try:
            self.thread_id = self.kernel.GetCurrentThreadId()
            # No WS_VISIBLE, ShowWindow, SetFocus or SetForegroundWindow.
            self.hwnd = self.user.CreateWindowExW(0, 'STATIC', 'Hugin owned UIA fixture', 0,
                                                  0, 0, 400, 100, None, None, None, None)
            if not self.hwnd:
                raise RuntimeError('fixture_create')
            self.edit = self.user.CreateWindowExW(0, 'RICHEDIT50W', 'Hugin A😀Z selected sentence end',
                                                  0x50000000 | 4 | 0x100, 0, 0, 350, 80,
                                                  self.hwnd, None, None, None)
            if not self.edit:
                raise RuntimeError('fixture_edit')
            result = ctypes.c_size_t()
            if not self.user.SendMessageTimeoutW(self.edit, 0xB1, 6, 10, 0x23, 50, ctypes.byref(result)):
                raise RuntimeError('fixture_select')
            self.ready.set()
            message = W.MSG()
            while True:
                status = self.user.GetMessageW(ctypes.byref(message), None, 0, 0)
                if status <= 0:
                    if status < 0:
                        self.failed = True
                    break
                self.user.TranslateMessage(ctypes.byref(message))
                self.user.DispatchMessageW(ctypes.byref(message))
        except Exception:
            self.failed = True
        finally:
            for name in ('edit', 'hwnd'):
                handle = getattr(self, name)
                if handle and not self.user.DestroyWindow(handle):
                    self.failed = True
                setattr(self, name, None)
            self.ready.set()

    def start(self):
        self.thread.start()
        if not self.ready.wait(2) or self.failed or not self.edit:
            raise RuntimeError('fixture_start')
        owner = W.DWORD()
        self.user.GetWindowThreadProcessId(self.edit, ctypes.byref(owner))
        if owner.value != os.getpid():
            raise RuntimeError('fixture_owner')

    def close(self):
        if self.thread.is_alive():
            if not self.user.PostThreadMessageW(self.thread_id, 0x12, 0, 0):
                raise RuntimeError('fixture_stop')
            self.thread.join(2)
        if self.thread.is_alive() or self.failed:
            raise RuntimeError('fixture_cleanup')
        if self.module:
            if not self.kernel.FreeLibrary(self.module):
                raise RuntimeError('fixture_library_cleanup')
            self.module = None


def selected(client, uia, fixture):
    automation = client.CreateObject(uia.CUIAutomation, interface=uia.IUIAutomation, clsctx=1)
    # ElementFromHandle is restricted to the held, created HWND, not foreground.
    element = automation.ElementFromHandle(fixture.edit)
    if element.CurrentProcessId != os.getpid() or element.CurrentIsPassword:
        return 'target_changed', None
    _identity(element)
    available = element.GetCurrentPropertyValue(uia.UIA_IsTextPatternAvailablePropertyId)
    if type(available) is not bool or not available:
        return 'selection_unsupported', None
    pattern = element.GetCurrentPattern(uia.UIA_TextPatternId).QueryInterface(uia.IUIAutomationTextPattern)
    supported = pattern.SupportedTextSelection
    if type(supported) is not int or supported not in (1, 2):
        return 'selection_unsupported', None
    first = _selected(pattern)
    if first is None:
        return 'selection_empty', None
    original = first.Clone()
    text = _text(first, 32)
    second = _selected(pattern)
    if text != 'A😀Z' or second is None or _text(second, 32) != text or any(
            original.CompareEndpoints(endpoint, second, endpoint) != 0 for endpoint in (0, 1)):
        return 'target_changed', None
    return 'captured', text


def run():
    sys.coinit_flags = 0
    comtypes, client = _load_comtypes()
    comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
    fixture = None
    try:
        fixture = Fixture()
        foreground = fixture.user.GetForegroundWindow()
        clipboard = fixture.user.GetClipboardSequenceNumber()
        fixture.start()
        uia = client.GetModule(_system_typelib())
        result = selected(client, uia, fixture)
        if fixture.user.GetForegroundWindow() != foreground or fixture.user.GetClipboardSequenceNumber() != clipboard:
            return 'target_changed', None
        return result
    finally:
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
