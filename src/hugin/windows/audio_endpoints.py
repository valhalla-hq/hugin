"""Owned default-endpoint notifications; no device lookup, polling or settings.

Registration, unregistration and all owned COM releases run on the signal
window's thread. MMDevice does not AddRef the sink: our exact interface pointer
and COMObject stay held until unregister succeeds. Callback IDs remain pointers
and are never converted into Python strings.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
from functools import lru_cache
import sys
import threading

from hugin.errors import HuginError

_LIVE_OWNERS=set()  # Retain partial/failing COM cleanup even outside WindowsSignals.
_LIVE_LOCK=threading.Lock()


class DefaultDeviceChanges:
    def __init__(self,notify,on_error=None):
        self.notify=notify
        self.on_error=on_error
        self.active=True
        self.error=None

    def disable(self):
        self.active=False
        self.notify=None
        self.on_error=None  # A stale native callback must not retain the controller.

    def handle(self,flow,role):
        notify,on_error=self.notify,self.on_error
        try:
            if self.active and type(flow) is int and type(role) is int and flow in (0,1) and role in (0,1,2):
                notify('devices_changed')
            return 0  # S_OK, including ignored flow/role values and late events.
        except Exception:
            self.active=False
            self.error=HuginError('input_failed','audio_endpoints_callback')
            try:
                if on_error is not None:
                    on_error('input_failed','audio_endpoints_callback')
            except Exception:
                pass
            return -2147467259  # E_FAIL; never let comtypes log a raw exception.


class AudioEndpointNotifications:
    """Single-use COM owner, composed inside WindowsSignals' bounded close.

The native backend imports comtypes on the constructing (application) thread.
comtypes initializes its import thread automatically. open/close separately
balance one explicit STA reference on the dedicated signal owner thread.
"""
    def __init__(self,*,backend=None):
        self._backend=backend if backend is not None else _ComRuntime()
        self._thread=None
        self._used=False
        self._initialized=False
        self._registered=False
        self._enumerator=None
        self._sink=None
        self._callback=None
        self._messages=None
        self.error=None

    @property
    def closed(self):
        return not self._initialized and not self._registered and all(
            item is None for item in (self._enumerator,self._sink,self._callback))

    @property
    def ready(self):
        return bool(self._registered and self.error is None and self._messages is not None
            and self._messages.active and self._messages.error is None)

    def _owner_thread(self):
        if self._thread is not None and threading.get_ident()!=self._thread:
            raise HuginError('input_failed','audio_endpoints_owner_thread')

    def open(self,notify,on_error=None):
        self._owner_thread()
        if self._used or not callable(notify):
            raise HuginError('input_failed','audio_endpoints_restart')
        self._used=True
        self._thread=threading.get_ident()
        def failed(code,phase):
            self.error=self.error or HuginError(code,phase)
            if on_error is not None:
                on_error(code,phase)
        self._messages=DefaultDeviceChanges(notify,failed)
        try:
            self._backend.initialize()
            self._initialized=True
            with _LIVE_LOCK:
                _LIVE_OWNERS.add(self)
            self._enumerator=self._backend.create_enumerator()
            self._sink,self._callback=self._backend.create_callback(self._messages)
            self._backend.register(self._enumerator,self._callback)
            self._registered=True
        except Exception:
            self._messages.disable()
            self.error=HuginError('input_failed','audio_endpoints_start')
            raise self.error from None  # Caller retains this owner for same-thread cleanup.

    def close(self):
        self._owner_thread()
        self._used=True
        if self._messages is not None:
            self._messages.disable()
        try:
            if self._registered:
                self._backend.unregister(self._enumerator,self._callback)
                self._registered=False
            if self._callback is not None:
                self._backend.release(self._callback)
                self._callback=None
                self._sink=None
            if self._enumerator is not None:
                self._backend.release(self._enumerator)
                self._enumerator=None
            if self._initialized:
                self._backend.uninitialize()
                self._initialized=False
        except Exception:
            self.error=self.error or HuginError('input_failed','audio_endpoints_cleanup')
            raise HuginError('input_failed','audio_endpoints_cleanup') from None
        with _LIVE_LOCK:
            _LIVE_OWNERS.discard(self)


@lru_cache(maxsize=1)
def _interfaces(com):
    """SDK mmdeviceapi.h vtable order and types; device outputs are forward-only.

LPCWSTR is represented by POINTER(c_wchar), ABI-equivalent but without ctypes'
automatic c_wchar_p string copy. PROPERTYKEY is a GUID plus DWORD, by value.
No typelib generation, registry modification or endpoint query is needed.
"""
    pointer=ctypes.POINTER
    wide=pointer(ctypes.c_wchar)
    class PropertyKey(ctypes.Structure):
        _fields_=[('fmtid',com.GUID),('pid',W.DWORD)]
    class IMMDevice(com.IUnknown):
        _iid_=com.GUID('{D666063F-1587-4E43-81F1-B948E807363F}')
        _methods_=[]  # Forward output type; no IMMDevice method is invoked.
    class IMMDeviceCollection(com.IUnknown):
        _iid_=com.GUID('{0BD7A1BE-7A1A-44DB-8397-CC5392387B5E}')
        _methods_=[]
    class IMMNotificationClient(com.IUnknown):
        _iid_=com.GUID('{7991EEC9-7E89-4D85-8390-6C703CEC60C0}')
        _methods_=[
            com.COMMETHOD([],com.HRESULT,'OnDeviceStateChanged',(['in'],wide,'device'),(['in'],W.DWORD,'state')),
            com.COMMETHOD([],com.HRESULT,'OnDeviceAdded',(['in'],wide,'device')),
            com.COMMETHOD([],com.HRESULT,'OnDeviceRemoved',(['in'],wide,'device')),
            com.COMMETHOD([],com.HRESULT,'OnDefaultDeviceChanged',(['in'],ctypes.c_int,'flow'),
                (['in'],ctypes.c_int,'role'),(['in'],wide,'device')),
            com.COMMETHOD([],com.HRESULT,'OnPropertyValueChanged',(['in'],wide,'device'),(['in'],PropertyKey,'key')),
        ]
    class IMMDeviceEnumerator(com.IUnknown):
        _iid_=com.GUID('{A95664D2-9614-4F35-A746-DE8DB63617E6}')
        _methods_=[
            com.COMMETHOD([],com.HRESULT,'EnumAudioEndpoints',(['in'],ctypes.c_int,'flow'),
                (['in'],W.DWORD,'state'),(['out'],pointer(pointer(IMMDeviceCollection)),'devices')),
            com.COMMETHOD([],com.HRESULT,'GetDefaultAudioEndpoint',(['in'],ctypes.c_int,'flow'),
                (['in'],ctypes.c_int,'role'),(['out'],pointer(pointer(IMMDevice)),'device')),
            com.COMMETHOD([],com.HRESULT,'GetDevice',(['in'],wide,'id'),(['out'],pointer(pointer(IMMDevice)),'device')),
            com.COMMETHOD([],com.HRESULT,'RegisterEndpointNotificationCallback',(['in'],pointer(IMMNotificationClient),'client')),
            com.COMMETHOD([],com.HRESULT,'UnregisterEndpointNotificationCallback',(['in'],pointer(IMMNotificationClient),'client')),
        ]
    return IMMDeviceEnumerator,IMMNotificationClient,PropertyKey


class _ComRuntime:
    def __init__(self):
        if sys.platform!='win32':
            raise HuginError('unsupported','audio_endpoints')
        try:
            import comtypes
            self.com=comtypes
            self.enumerator_type,self.notification_type,self.property_key=_interfaces(comtypes)
        except Exception:
            raise HuginError('input_failed','audio_endpoints_interfaces') from None

    def initialize(self):
        self.com.CoInitializeEx(self.com.COINIT_APARTMENTTHREADED)

    def uninitialize(self):
        self.com.CoUninitialize()

    def create_enumerator(self):
        return self.com.CoCreateInstance(self.com.GUID('{BCDE0395-E52F-467C-8E3D-C4579291692E}'),
            self.enumerator_type,self.com.CLSCTX_INPROC_SERVER)

    def create_callback(self,messages):
        class Sink(self.com.COMObject):
            _com_interfaces_=[self.notification_type]
            def OnDeviceStateChanged(self,this,device,state):return 0
            def OnDeviceAdded(self,this,device):return 0
            def OnDeviceRemoved(self,this,device):return 0
            def OnDefaultDeviceChanged(self,this,flow,role,device):return messages.handle(flow,role)
            def OnPropertyValueChanged(self,this,device,key):return 0
        sink=Sink()
        return sink,sink.QueryInterface(self.notification_type)  # Own AddRef, MMDevice holds none.

    def register(self,enumerator,callback):
        enumerator.RegisterEndpointNotificationCallback(callback)

    def unregister(self,enumerator,callback):
        enumerator.UnregisterEndpointNotificationCallback(callback)

    def release(self,pointer):
        pointer.Release()
        # comtypes interface pointers auto-Release at __del__. Null the same
        # ctypes storage after explicit release, preventing a second Release.
        ctypes.c_void_p.value.__set__(pointer,None)
