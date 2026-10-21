"""Owned zero-PCM waveOut stream only; no microphone or audible speech."""
import os
import time
import unittest

from hugin.audio import PCMOutput


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_AUDIO_TESTS')=='1',
                     'explicit owned silent playback fixture required')
class PlaybackPositionNative(unittest.TestCase):
    def test_silent_position_pause_resume_drain_and_new_job(self):
        output=PCMOutput(buffer_ms=250);seen=[]
        self.addCleanup(output.close)
        output.start('silent-first')
        self.assertTrue(output.write(b'\0\0'*6000,'silent-first',progress=seen.append))
        self.assertTrue(output.pause('silent-first',True))
        held=output.position('silent-first')
        time.sleep(.06)
        self.assertEqual(output.position('silent-first'),held)
        self.assertTrue(output.pause('silent-first',False))
        deadline=time.monotonic()+2
        self.assertTrue(output.drain('silent-first',lambda:time.monotonic()>deadline,
                                     progress=seen.append))
        positions=[position for position in seen if position is not None]
        if not positions:self.skipTest('native driver has no trustworthy playback counter')
        self.assertEqual(positions,sorted(positions))
        self.assertGreater(positions[-1],0)
        self.assertLessEqual(positions[-1],6000)
        output.stop();self.assertIsNone(output.position('silent-first'))
        output.start('silent-next')
        self.assertEqual(output.position('silent-next'),0)
        self.assertIsNone(output.position('silent-first'))

