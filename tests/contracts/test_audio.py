import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import wave

from hugin.audio import PCMOutput, RecordingBuffer
from hugin.config import load_settings
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


class FIFO(Device):
    """Deterministic whole-header reclamation, not a native audio driver."""
    def __init__(self, rate, clock):
        super().__init__(rate)
        self.clock = clock
        self.headers = []; self.tail = 0; self.gaps = []; self.peak = 0

    def collect(self):
        # Reclaimable 10ms after its last sample. Two queued headers leave
        # time to refill the first while the second still has ready samples.
        while self.headers and self.headers[0][0]+240 <= self.clock[0]:
            _, size = self.headers.pop(0)
            self.queued_bytes -= size

    def submit(self, data):
        if self.writes and self.clock[0] > self.tail:
            self.gaps.append(self.clock[0]-self.tail)
        self.tail = max(self.clock[0], self.tail)+len(data)//2
        self.headers.append((self.tail, len(data)))
        super().submit(data)
        self.peak = max(self.peak, self.queued_bytes)

    def reset(self):
        super().reset()
        self.headers.clear()
        self.tail = self.clock[0]


class AudioContract(unittest.TestCase):
    def test_both_voice_pcm_streams_refill_before_the_last_native_header_finishes(self):
        """Deterministic FIFO driver, not a physical playback/provider claim."""
        settings = load_settings(Path(__file__).resolve().parents[2])
        for voice in settings.voices.values():
            with self.subTest(voice=voice.id):
                with wave.open(str(voice.reference.parent/'bestaetigte-hoerprobe.wav'), 'rb') as source:
                    self.assertEqual((source.getnchannels(), source.getsampwidth(), source.getframerate()), (1, 2, 24000))
                    pcm = source.readframes(24000)  # Existing small synthetic voice asset.
                clock = [0]
                device = FIFO(24000, clock)
                output = PCMOutput(buffer_ms=125, factory=lambda rate:device)
                def advance(seconds): clock[0] += round(seconds*24000)
                try:
                    output.start(voice.id)
                    with patch('hugin.audio.time.sleep', advance):
                        for offset in range(0, len(pcm), 6000):
                            # Bounded dispatch/credit latency, not slow synthesis.
                            clock[0] += 24
                            self.assertTrue(output.write(pcm[offset:offset+6000], voice.id))
                        self.assertTrue(output.drain(voice.id))
                    self.assertEqual(b''.join(device.writes), pcm)
                    self.assertLessEqual(device.peak, 6000)
                    self.assertEqual(device.gaps, [], 'ready PCM must refill while another header remains queued')
                finally: output.close()

    def test_small_remainder_frames_drain_and_cancel_preserve_capacity_and_identity(self):
        for milliseconds in (1, 63, 125, 250):
            with self.subTest(buffer_ms=milliseconds):
                clock = [0]
                device = FIFO(24000, clock)
                output = PCMOutput(buffer_ms=milliseconds, factory=lambda rate:device)
                chunks = [b'\1\0', b'\2\0'*617, b'\3\0'*3001]
                def advance(seconds): clock[0] += round(seconds*24000)
                try:
                    output.start('current')
                    with patch('hugin.audio.time.sleep', advance):
                        for chunk in chunks: self.assertTrue(output.write(chunk, 'current'))
                        self.assertTrue(output.drain('current'))
                    self.assertEqual(b''.join(device.writes), b''.join(chunks))
                    self.assertEqual(device.queued_bytes, 0)
                    self.assertEqual(device.headers, [])
                    self.assertLessEqual(device.peak, output.capacity)
                    self.assertTrue(output.write(b'\4\0', 'current'))
                    output.stop()
                    self.assertEqual(device.headers, [])
                    self.assertFalse(output.write(b'\5\0', 'current'))
                finally: output.close()

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
