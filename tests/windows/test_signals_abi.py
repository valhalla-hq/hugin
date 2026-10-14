"""Exact Win32 ABI and simulated producers only; no native window is created."""
import ctypes
from ctypes import wintypes as W
import sys
import unittest
from unittest.mock import patch

from hugin.errors import HuginError
from hugin.windows.signals import _NativeSignalWindow,_WindowClass,WM_POWERBROADCAST,WM_DEVICECHANGE


class Function:
    def __init__(self,result=1):
        self.argtypes=None;self.restype=None;self.result=result;self.calls=[]
    def __call__(self,*args):
        self.calls.append(args)
        return self.result(*args) if callable(self.result) else self.result


class Library:
    def __init__(self):self.functions={}
    def __getattr__(self,name):return self.functions.setdefault(name,Function())


@unittest.skipUnless(sys.platform=='win32','Windows ctypes ABI')
class WindowsSignalABI(unittest.TestCase):
    def setUp(self):
        libraries=[]
        def library(*args,**kwargs):
            result=Library();libraries.append(result);return result
        self.patch=patch.object(ctypes,'WinDLL',side_effect=library)
        self.patch.start()
        self.backend=_NativeSignalWindow()
        self.user,self.kernel=libraries
        self.user.CreateWindowExW.result=0x4321
        self.user.DefWindowProcW.result=777
        self.actions=[]
    def tearDown(self):
        self.patch.stop()

    def test_pointer_sized_callback_and_explicit_function_signatures(self):
        self.assertEqual(ctypes.sizeof(_WindowClass),72 if ctypes.sizeof(ctypes.c_void_p)==8 else 40)
        for library in (self.user,self.kernel):
            for name,function in library.functions.items():
                self.assertIsNotNone(function.argtypes,name)
                self.assertIsNotNone(function.restype,name)
        self.assertEqual(self.user.DefWindowProcW.restype,ctypes.c_ssize_t)
        self.assertEqual(self.user.CreateWindowExW.argtypes[8],W.HWND)
        self.assertEqual(self.user.RegisterClassW.argtypes,[ctypes.POINTER(_WindowClass)])

    def test_hidden_top_level_window_and_owned_class_leave_foreign_wndprocs_alone(self):
        self.backend.open(self.actions.append)
        args=self.user.CreateWindowExW.calls[-1]
        self.assertIsNone(args[8],'broadcast owner must not use HWND_MESSAGE')
        self.assertEqual(args[3]&0x50000000,0,'neither WS_CHILD nor WS_VISIBLE')
        self.assertTrue(args[1].startswith('Hugin.SystemSignals.'))
        self.assertNotIn('SetWindowLongPtrW',self.user.functions)
        callback=self.backend._wndproc
        self.assertEqual(callback(0x4321,WM_POWERBROADCAST,4,0x7FFFFFFF),1)
        self.assertEqual(callback(0x4321,WM_POWERBROADCAST,18,0),1)
        self.assertEqual(callback(0x4321,WM_DEVICECHANGE,7,0x7FFFFFFF),1)
        self.assertEqual(callback(0x4321,WM_DEVICECHANGE,0x8001,0),777)
        self.assertEqual(self.actions,['system_pause','system_resume','devices_changed'])
        self.backend.close()
        self.assertTrue(self.backend.closed)

    def test_callback_and_class_ownership_survive_each_cleanup_failure(self):
        self.backend.open(self.actions.append);callback=self.backend._wndproc
        self.user.DestroyWindow.result=0
        with self.assertRaises(HuginError):self.backend.close()
        self.assertEqual(self.backend.hwnd,0x4321)
        self.assertIs(self.backend._wndproc,callback)
        self.user.DestroyWindow.result=1;self.user.UnregisterClassW.result=0
        with self.assertRaises(HuginError):self.backend.close()
        self.assertIsNone(self.backend.hwnd)
        self.assertIs(self.backend._wndproc,callback)
        self.assertFalse(self.backend.closed)
        self.user.UnregisterClassW.result=1;self.backend.close()
        self.assertTrue(self.backend.closed)
        self.assertIsNone(self.backend._wndproc)

    def test_class_registration_failure_never_unregisters_foreign_class(self):
        self.user.RegisterClassW.result=0
        with self.assertRaises(HuginError):self.backend.open(self.actions.append)
        self.backend.close()
        self.assertEqual(self.user.UnregisterClassW.calls,[])
        self.assertEqual(self.user.DestroyWindow.calls,[])

    def test_create_failure_retains_only_registered_class_for_cleanup(self):
        self.user.CreateWindowExW.result=0
        with self.assertRaises(HuginError):self.backend.open(self.actions.append)
        self.assertIsNotNone(self.backend._wndproc)
        self.backend.close()
        self.assertEqual(self.user.DestroyWindow.calls,[])
        self.assertEqual(len(self.user.UnregisterClassW.calls),1)

    def test_cleanup_on_foreign_thread_id_is_refused_before_mutation(self):
        self.backend.open(self.actions.append)
        self.kernel.GetCurrentThreadId.result=2
        with self.assertRaises(HuginError):self.backend.close()
        self.assertFalse(self.backend.closed)
        self.assertEqual(self.user.DestroyWindow.calls,[])
        self.kernel.GetCurrentThreadId.result=1;self.backend.close()

    def test_default_callback_failure_never_escapes_native_boundary(self):
        self.backend.open(self.actions.append)
        def fail(*args):raise RuntimeError('PRIVATE NATIVE EXCEPTION')
        self.user.DefWindowProcW.result=fail
        self.assertEqual(self.backend._wndproc(0x4321,0xFFFF,0,0),0)
        self.assertEqual(self.backend._callback_error.code,'input_failed')
        self.assertNotIn('PRIVATE',str(self.backend._callback_error))
        self.user.DefWindowProcW.result=777;self.backend.close()


if __name__=='__main__':unittest.main()
