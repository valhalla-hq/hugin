"""Opt-in read-only COM registration plus synthetic callbacks; no device changes."""
import ctypes
import os
import sys
import threading
import unittest

from hugin.windows.audio_endpoints import AudioEndpointNotifications


@unittest.skipUnless(sys.platform=='win32' and os.environ.get('HUGIN_ENDPOINT_READONLY_TESTS')=='1',
    'requires explicit read-only endpoint registration opt-in and controller comtypes')
class NativeEndpointRegistration(unittest.TestCase):
    def test_register_synthetic_callback_and_unregister_without_device_queries(self):
        # Import comtypes on the calling test/application thread, not its first
        # time on a short-lived signal thread (comtypes owns its import init).
        owner=AudioEndpointNotifications()
        actions=[];facts={}
        def probe():
            try:
                owner.open(actions.append)
                facts['ready']=owner.ready
                pointer=owner._callback
                for flow in (0,1):
                    for role in (0,1,2):
                        pointer.OnDefaultDeviceChanged(flow,role,None)
                # A native LPCWSTR pointer stays opaque even in comtypes' real
                # vtable. Only a local synthetic string is used, never a device ID.
                synthetic=ctypes.create_unicode_buffer('synthetic')
                pointer.OnDeviceAdded(synthetic)
                pointer.OnDeviceRemoved(synthetic)
                pointer.OnDeviceStateChanged(synthetic,1)
                pointer.OnPropertyValueChanged(synthetic,owner._backend.property_key())
                # Drop this temporary Python alias before owner clears/releases
                # its sole COM reference on this same thread.
                del pointer
            except Exception:
                facts['error']='audio_endpoints_native_probe'
            finally:
                try:owner.close()
                except Exception:facts['cleanup_error']='audio_endpoints_native_cleanup'
                facts['closed']=owner.closed
        thread=threading.Thread(target=probe,name='hugin-readonly-endpoint-probe',daemon=True)
        thread.start();thread.join(5)
        self.assertFalse(thread.is_alive(),'owned read-only probe did not finish within five seconds')
        self.assertEqual(facts,{'ready':True,'closed':True})
        self.assertEqual(actions,['devices_changed']*6,
            'callbacks here are synthetic, not evidence of real default-device event delivery')


if __name__=='__main__':unittest.main()
