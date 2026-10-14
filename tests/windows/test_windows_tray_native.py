"""Explicit own-icon smoke only; no global input, microphone, or model work."""
import ctypes
from ctypes import wintypes
import os
import unittest


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_NATIVE_TRAY')=='1',
    'explicit owned tray smoke')
class NativeTray(unittest.TestCase):
    def test_own_icon_start_stop_releases_native_runner_and_hicon(self):
        from PIL import Image
        import pystray
        from hugin.windows.tray import TrayOwner
        user=ctypes.WinDLL('user32')
        user.GetForegroundWindow.argtypes=[];user.GetForegroundWindow.restype=wintypes.HWND
        user.GetClipboardSequenceNumber.argtypes=[];user.GetClipboardSequenceNumber.restype=wintypes.DWORD
        foreground=user.GetForegroundWindow();sequence=user.GetClipboardSequenceNumber()
        icon=pystray.Icon('hugin-owned-tray-smoke',Image.new('RGBA',(32,32),'#21516a'),
            'Hugin owned tray smoke',menu=pystray.Menu(pystray.MenuItem('Synthetic smoke',lambda:None)))
        owner=TrayOwner(icon)
        try:
            owner.start()
            self.assertTrue(owner.ready)
            self.assertIs(icon._thread,owner._thread)
            hwnd=icon._hwnd
            self.assertIn(hwnd,icon._HWND_TO_ICON)
        finally:owner.close()
        self.assertTrue(owner.closed)
        self.assertFalse(owner._thread.is_alive());self.assertFalse(owner._setup.is_alive())
        self.assertNotIn(hwnd,icon._HWND_TO_ICON)
        self.assertIsNone(icon._icon_handle)
        self.assertEqual(user.GetForegroundWindow(),foreground)
        self.assertEqual(user.GetClipboardSequenceNumber(),sequence)


if __name__=='__main__':unittest.main()
