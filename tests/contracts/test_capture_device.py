"""The native capture boundary owns WASAPI selection and usable gate clocks."""
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from hugin.audio import Microphone
from hugin.errors import HuginError


class Stream:
    def __init__(self,callback):self.callback=callback;self.time=50.0;self.closed=False
    def start(self):pass
    def stop(self,*,ignore_errors):assert ignore_errors is False
    def abort(self,*,ignore_errors):assert ignore_errors is False
    def close(self,*,ignore_errors):assert ignore_errors is False;self.closed=True


class Device:
    class CallbackAbort(Exception):pass
    def __init__(self):
        self.hosts=[{'name':'MME','default_input_device':1},
            {'name':'Windows WASAPI','default_input_device':35}]
        self.device={'hostapi':1,'max_input_channels':1}
        self.checked=[];self.opened=[];self.extras=[];self.check_error=None
    def query_hostapis(self):return self.hosts
    def query_devices(self,index):assert index==35;return self.device
    def WasapiSettings(self,**kwargs):
        self.extras.append(kwargs);return NS(**kwargs)
    def check_input_settings(self,**kwargs):
        self.checked.append(kwargs)
        if self.check_error:raise self.check_error
    def RawInputStream(self,**kwargs):
        self.opened.append(kwargs);return Stream(kwargs['callback'])


class CaptureDevice(unittest.TestCase):
    def test_native_check_and_stream_use_same_wasapi_default_and_shared_conversion(self):
        sd=Device();mic=Microphone(1000)
        with patch.dict('sys.modules',{'sounddevice':sd}):
            mic.start(armed=False)
            try:
                self.assertEqual(sd.extras,[{'auto_convert':True}])
                self.assertEqual(len(sd.checked),1);self.assertEqual(len(sd.opened),1)
                stream=dict(sd.opened[0]);stream.pop('callback')
                self.assertEqual(stream,sd.checked[0])
                self.assertEqual((stream['device'],stream['samplerate'],stream['channels'],stream['dtype']),
                    (35,16000,1,'int16'))
            finally:mic.cancel()
        self.assertFalse(mic.owned)

    def test_missing_ambiguous_or_invalid_default_fails_before_device_open(self):
        candidates=([],[{'name':'MME','default_input_device':1}],
            [{'name':'Windows WASAPI','default_input_device':35}]*2,
            *[[{'name':'Windows WASAPI','default_input_device':value}]
                for value in (None,True,-1,'35',2**32)])
        for hosts in candidates:
            with self.subTest(hosts=hosts):
                sd=Device();sd.hosts=hosts;mic=Microphone(1000)
                with patch.dict('sys.modules',{'sounddevice':sd}):
                    with self.assertRaises(HuginError):mic.start(armed=False)
                self.assertEqual((sd.checked,sd.opened),([],[]));self.assertFalse(mic.owned)

    def test_default_must_belong_to_wasapi_and_have_input_channels(self):
        for device in ({'hostapi':0,'max_input_channels':1},
                {'hostapi':True,'max_input_channels':1},
                {'hostapi':1,'max_input_channels':0},
                {'hostapi':1,'max_input_channels':True}):
            sd=Device();sd.device=device;mic=Microphone(1000)
            with patch.dict('sys.modules',{'sounddevice':sd}):
                with self.assertRaises(HuginError):mic.start(armed=False)
            self.assertEqual((sd.checked,sd.opened),([],[]))

    def test_failed_preflight_never_opens_stream_or_falls_back(self):
        sd=Device();sd.check_error=RuntimeError('synthetic device failure');mic=Microphone(1000)
        with patch.dict('sys.modules',{'sounddevice':sd}):
            with self.assertRaises(HuginError):mic.start(armed=False)
        self.assertEqual(len(sd.checked),1);self.assertEqual(sd.opened,[])

    def test_zero_adc_is_a_clock_fault_before_and_after_arming(self):
        for armed in (False,True):
            sd=Device();mic=Microphone(1000)
            with patch.dict('sys.modules',{'sounddevice':sd}):
                mic.start(armed=False)
                try:
                    if armed:mic.arm_after(50.1)
                    with self.assertRaises(sd.CallbackAbort):
                        mic._stream.callback(b'\0\0',1,NS(inputBufferAdcTime=0.0),False)
                    self.assertEqual((mic.fault.code,mic.fault.phase),('microphone_failed','capture_clock'))
                finally:mic.cancel()

    def test_injected_stream_factory_performs_no_native_device_discovery(self):
        sd=NS(CallbackAbort=Device.CallbackAbort)
        mic=Microphone(1000,stream_factory=lambda **kwargs:Stream(kwargs['callback']))
        with patch.dict('sys.modules',{'sounddevice':sd}):
            mic.start(armed=False);mic.cancel()
        self.assertFalse(mic.owned)

    def test_zero_adc_during_native_start_aborts_and_closes_the_opened_owner(self):
        sd=Device();construct=sd.RawInputStream;created=[]
        def opening(**kwargs):
            stream=construct(**kwargs);created.append(stream)
            stream.start=lambda:stream.callback(b'\0\0',1,NS(inputBufferAdcTime=0.0),False)
            return stream
        sd.RawInputStream=opening;mic=Microphone(1000)
        with patch.dict('sys.modules',{'sounddevice':sd}):
            with self.assertRaises(HuginError):mic.start(armed=False)
        self.assertTrue(created[0].closed);self.assertFalse(mic.owned)


if __name__=='__main__':unittest.main()
