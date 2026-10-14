import threading
import time
import unittest

from hugin.audio import PCMOutput, RecordingBuffer
from hugin.errors import HuginError


class Device:
    def __init__(self, rate):
        self.queued_bytes = 0
        self.writes = []
        self.resets = 0
        self.fail_reset = False

    def collect(self):
        pass

    def submit(self, pcm):
        self.writes.append(pcm)
        self.queued_bytes += len(pcm)

    def reset(self):
        if self.fail_reset:
            raise HuginError('audio_failed','reset')
        self.resets += 1
        self.queued_bytes = 0

    def close(self):
        self.reset()


class AudioContract(unittest.TestCase):
    def test_reset_unblocks_old_writer_and_prevents_late_audio(self):
        device = Device(24000)
        output = PCMOutput(factory=lambda rate: device)
        output.start('old')
        result = []
        writer = threading.Thread(target=lambda: result.append(output.write(b'\0'*24000,'old')))
        writer.start()
        deadline = time.monotonic()+1
        while not device.writes and time.monotonic()<deadline:
            time.sleep(.001)
        output.stop()
        writer.join(1)
        self.assertFalse(writer.is_alive())
        self.assertEqual(result,[False])
        self.assertLessEqual(max(map(len,device.writes)),12000)
        self.assertFalse(output.write(b'\0\0','old'))

    def test_failed_reset_is_not_reported_as_silence(self):
        device = Device(24000)
        output = PCMOutput(factory=lambda rate: device)
        output.start('job')
        device.fail_reset = True
        with self.assertRaises(HuginError):
            output.stop()

    def test_capture_overflow_does_not_return_truncated_success(self):
        buffer = RecordingBuffer(8)
        buffer.append(b'\0'*6)
        buffer.append(b'\0'*4)
        with self.assertRaises(HuginError) as error:
            buffer.finish()
        self.assertEqual(error.exception.code,'capture_limit')

    def test_capture_is_pcm_aligned_and_cancel_discards_current_data(self):
        buffer = RecordingBuffer(8)
        with self.assertRaises(HuginError):
            buffer.append(b'odd')
        buffer = RecordingBuffer(8)
        buffer.append(b'\0'*4)
        buffer.cancel()
        self.assertEqual(buffer.finish(),b'')
