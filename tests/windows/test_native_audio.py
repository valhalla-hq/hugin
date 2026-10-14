"""Opt-in native device probes. Captured bytes stay in RAM and are discarded."""
import os
import threading
import time
import unittest

from hugin.audio import Microphone,PCMOutput


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_AUDIO_TESTS')=='1',
    'requires explicit native audio-device probe')
class NativeAudio(unittest.TestCase):
    def test_microphone_closes_without_persisting_audio(self):
        mic = Microphone(16000*2*2)
        try:
            mic.start()
            time.sleep(.35)
            data = mic.stop()
            self.assertFalse(mic.owned)
            self.assertGreater(len(data),0)
            self.assertEqual(len(data)%2,0)
            del data
        finally: mic.cancel()

    def test_native_zero_pcm_reset_releases_backpressure_and_owned_headers(self):
        output = PCMOutput(buffer_ms=125)
        cancelled = threading.Event()
        writer = None
        try:
            output.start('native-synthetic')
            writer = threading.Thread(target=lambda:output.write(b'\0\0'*24000,'native-synthetic',cancelled.is_set))
            writer.start()
            time.sleep(.04)
            cancelled.set()
            started = time.perf_counter()
            output.stop()
            elapsed = time.perf_counter()-started
            writer.join(1)
            self.assertFalse(writer.is_alive())
            self.assertLess(elapsed,.3)
        finally:
            cancelled.set()
            output.close()
            if writer: writer.join(1)


if __name__=='__main__': unittest.main()
