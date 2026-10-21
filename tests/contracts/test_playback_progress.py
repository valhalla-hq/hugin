"""Actual device positions, never a clock-derived speech estimate."""
import ctypes as ct
import threading
import unittest
from types import SimpleNamespace as NS

from hugin import audio
from hugin.audio import PCMOutput


class PositionedDevice:
    def __init__(self, rate):
        self.queued_bytes=0;self.submitted=0;self.played=0;self.paused=False
        self.advance=0;self.fail_position=False

    def collect(self):
        if not self.paused:self.played=min(self.submitted,self.played+self.advance)
        self.queued_bytes=max(0,(self.submitted-self.played)*2)

    def submit(self, pcm):
        self.submitted+=len(pcm)//2;self.queued_bytes+=len(pcm)

    def position(self):
        if self.fail_position:raise OSError('unavailable device counter')
        return self.played

    def pause(self, paused):self.paused=paused
    def reset(self):self.submitted=self.played=self.queued_bytes=0
    def close(self):self.reset()


class PlaybackProgress(unittest.TestCase):
    def output(self):
        device=PositionedDevice(24000)
        output=PCMOutput(factory=lambda _:device)
        self.addCleanup(output.close)
        output.start('job')
        return output,device

    def test_progress_uses_cumulative_device_samples_in_write_and_drain(self):
        output,device=self.output();seen=[]
        self.assertTrue(output.write(b'\0\0'*1000,'job',progress=seen.append))
        self.assertEqual(seen,[0])
        device.advance=240
        self.assertTrue(output.drain('job',progress=seen.append))
        self.assertEqual(seen,[0,240,480,720,960,1000])
        self.assertTrue(output.write(b'\0\0'*200,'job',progress=seen.append))
        self.assertEqual(seen[-1],1000)
        self.assertTrue(output.drain('job',progress=seen.append))
        self.assertEqual(seen[-1],1200)

    def test_position_is_bounded_monotonic_and_resets_for_new_job(self):
        output,device=self.output()
        output.write(b'\0\0'*10,'job')
        device.played=4;self.assertEqual(output.position('job'),4)
        device.played=2;self.assertIsNone(output.position('job'))
        device.played=100;self.assertEqual(output.position('job'),10)
        self.assertIsNone(output.position('stale'))
        output.stop();self.assertIsNone(output.position('job'))
        output.start('next');self.assertEqual(output.position('next'),0)
        self.assertFalse(output.write(b'\0\0','job'))

    def test_pause_freezes_real_observation_resume_and_optional_failure(self):
        output,device=self.output();output.write(b'\0\0'*10,'job')
        device.played=4
        self.assertTrue(output.pause('job',True))
        device.played=8;self.assertEqual(output.position('job'),4)
        self.assertTrue(output.pause('job',False));self.assertEqual(output.position('job'),8)
        device.fail_position=True;self.assertIsNone(output.position('job'))
        seen=[];self.assertTrue(output.write(b'\0\0','job',progress=seen.append))
        self.assertEqual(seen,[None])

    def test_started_and_progress_callbacks_do_not_hold_output_lock(self):
        output,_=self.output();checks=[]
        def callback(*args):
            observed=[]
            worker=threading.Thread(target=lambda:observed.append(output.position('job')))
            worker.start();worker.join(.5)
            checks.append(not worker.is_alive())
        self.assertTrue(output.write(b'\0\0','job',started=callback,progress=callback))
        self.assertEqual(checks,[True,True])

    def test_stale_callbacks_cannot_report_after_started_stops_job(self):
        output,_=self.output();seen=[]
        self.assertFalse(output.write(b'\0\0','job',started=output.stop,progress=seen.append))
        self.assertEqual(seen,[])

    def test_no_device_position_preserves_speech_and_reports_unknown(self):
        output,device=self.output();device.position=None
        seen=[]
        self.assertTrue(output.write(b'\0\0','job',progress=seen.append))
        self.assertEqual(seen,[None])


class WavePositionABI(unittest.TestCase):
    def test_mmtime_abi_and_driver_sample_byte_ms_alternatives(self):
        self.assertEqual(ct.sizeof(audio._MMTime),12)
        self.assertEqual(audio._MMTime.u.offset,4)
        for kind,value,expected in ((2,480,480),(4,960,480),(1,20,480),(4,961,None),(32,480,None)):
            device=audio._WaveOut.__new__(audio._WaveOut)
            device.handle=ct.c_void_p(123);device.rate=24000
            def position(handle,pointer,size):
                self.assertEqual(size,12)
                result=ct.cast(pointer,ct.POINTER(audio._MMTime)).contents
                self.assertEqual(result.wType,2)
                result.wType=kind;result.u.sample=value
                return 0
            device.api=NS(waveOutGetPosition=position)
            self.assertEqual(device.position(),expected)
        device.api=NS(waveOutGetPosition=lambda *_:5)
        self.assertIsNone(device.position())

