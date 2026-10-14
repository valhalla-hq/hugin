"""COM ABI producer guards with fake comtypes; no native library/device calls."""
import ctypes
from ctypes import wintypes as W
import sys
import types
import unittest
import uuid
from unittest.mock import patch

from hugin.windows.audio_endpoints import DefaultDeviceChanges, _ComRuntime


class GUID(ctypes.Structure):
    _fields_=[('data',ctypes.c_ubyte*16)]
    def __init__(self,value):
        super().__init__()
        ctypes.memmove(ctypes.addressof(self),uuid.UUID(value).bytes_le,16)
    def __str__(self):return str(uuid.UUID(bytes_le=bytes(self.data))).upper()


class IUnknown(ctypes.Structure):
    _fields_=[]


class FakeObject:
    def QueryInterface(self,interface):
        self.queried=interface
        return self


class FakeEnumerator:
    def __init__(self):self.calls=[]
    def RegisterEndpointNotificationCallback(self,pointer):self.calls.append(('register',pointer))
    def UnregisterEndpointNotificationCallback(self,pointer):self.calls.append(('unregister',pointer))
    # No queries are implemented: any enumeration/lookup would fail the test.


def fake_comtypes():
    com=types.ModuleType('comtypes')
    com.GUID=GUID;com.IUnknown=IUnknown;com.COMObject=FakeObject
    com.HRESULT=ctypes.c_int32;com.COINIT_APARTMENTTHREADED=2;com.CLSCTX_INPROC_SERVER=1
    com.COMMETHOD=lambda flags,result,name,*arguments:(name,result,arguments)
    com.calls=[];com.enumerator=FakeEnumerator()
    com.CoInitializeEx=lambda flags:com.calls.append(('initialize',flags))
    com.CoUninitialize=lambda:com.calls.append(('uninitialize',))
    def create(clsid,interface,context):
        com.calls.append(('create',str(clsid),interface,context))
        return com.enumerator
    com.CoCreateInstance=create
    return com


class AudioEndpointABI(unittest.TestCase):
    def setUp(self):
        self.com=fake_comtypes()
        self.patch=patch.dict(sys.modules,{'comtypes':self.com});self.patch.start()
        self.platform=patch.object(sys,'platform','win32');self.platform.start()
        self.addCleanup(self.patch.stop);self.addCleanup(self.platform.stop)
        self.runtime=_ComRuntime()

    def test_sdk_iids_vtable_order_and_by_value_property_key(self):
        runtime=self.runtime
        self.assertEqual(str(runtime.enumerator_type._iid_),'A95664D2-9614-4F35-A746-DE8DB63617E6')
        self.assertEqual(str(runtime.notification_type._iid_),'7991EEC9-7E89-4D85-8390-6C703CEC60C0')
        enum=runtime.enumerator_type._methods_;notify=runtime.notification_type._methods_
        self.assertEqual([entry[0] for entry in enum],['EnumAudioEndpoints','GetDefaultAudioEndpoint','GetDevice',
            'RegisterEndpointNotificationCallback','UnregisterEndpointNotificationCallback'])
        self.assertEqual([entry[0] for entry in notify],['OnDeviceStateChanged','OnDeviceAdded','OnDeviceRemoved',
            'OnDefaultDeviceChanged','OnPropertyValueChanged'])
        self.assertEqual(ctypes.sizeof(runtime.property_key),20)
        self.assertIs(notify[4][2][1][1],runtime.property_key)
        self.assertIs(notify[0][2][1][1],W.DWORD)
        self.assertIs(notify[3][2][0][1],ctypes.c_int)
        self.assertIs(notify[3][2][1][1],ctypes.c_int)
        for entry in notify:
            wide=entry[2][-1][1] if entry[0]=='OnDefaultDeviceChanged' else entry[2][0][1]
            self.assertIs(wide,ctypes.POINTER(ctypes.c_wchar))
            self.assertIsNot(wide,ctypes.c_wchar_p)

    def test_only_create_register_unregister_without_device_query(self):
        runtime=self.runtime
        runtime.initialize();enumerator=runtime.create_enumerator()
        sink,pointer=runtime.create_callback(DefaultDeviceChanges(lambda action:None))
        runtime.register(enumerator,pointer);runtime.unregister(enumerator,pointer);runtime.uninitialize()
        self.assertIs(sink.queried,runtime.notification_type)
        self.assertEqual(self.com.calls,[('initialize',2),('create','BCDE0395-E52F-467C-8E3D-C4579291692E',
            runtime.enumerator_type,1),('uninitialize',)])
        self.assertEqual(enumerator.calls,[('register',pointer),('unregister',pointer)])

    def test_callbacks_never_read_endpoint_identifiers_or_properties(self):
        class Unreadable:
            def __getattribute__(self,name):raise AssertionError('endpoint payload accessed')
        actions=[];payload=Unreadable()
        sink,_=self.runtime.create_callback(DefaultDeviceChanges(actions.append))
        for flow in (0,1):
            for role in (0,1,2):
                self.assertEqual(sink.OnDefaultDeviceChanged(None,flow,role,payload),0)
        self.assertEqual(sink.OnDefaultDeviceChanged(None,0,0,None),0)
        self.assertEqual(sink.OnDeviceAdded(None,payload),0)
        self.assertEqual(sink.OnDeviceRemoved(None,payload),0)
        self.assertEqual(sink.OnDeviceStateChanged(None,payload,1),0)
        self.assertEqual(sink.OnPropertyValueChanged(None,payload,payload),0)
        self.assertEqual(actions,['devices_changed']*7)

    def test_callback_error_does_not_escape_to_comtypes_logger(self):
        def failure(*args):raise RuntimeError('PRIVATE device name')
        messages=DefaultDeviceChanges(failure,failure)
        sink,_=self.runtime.create_callback(messages)
        self.assertLess(sink.OnDefaultDeviceChanged(None,0,0,None),0)
        self.assertNotIn('PRIVATE',str(messages.error))

    def test_explicit_release_clears_ctypes_pointer_to_prevent_second_release(self):
        releases=[]
        class Pointer(ctypes.c_void_p):
            def Release(self):releases.append(self.value);return 0
            def __del__(self):
                if self:self.Release()
        pointer=Pointer(123)
        self.runtime.release(pointer)
        self.assertFalse(pointer)
        del pointer
        self.assertEqual(releases,[123])


if __name__=='__main__':unittest.main()
