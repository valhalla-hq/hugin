"""Public IPC guards; content never becomes a partial successful transcript."""
import hashlib
import io
import struct
import unittest
import uuid

from hugin.errors import HuginError
from hugin.protocol import (Identity, Frame, read_control, write_control,
    read_frame, write_frame, TranscriptReceiver)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.identity = Identity(str(uuid.uuid4()), str(uuid.uuid4()), 4)

    def test_control_size_is_checked_before_body_read(self):
        source = io.BytesIO(struct.pack('!I', 65537))
        with self.assertRaises(HuginError):
            read_control(source)
        with self.assertRaises(HuginError):
            write_control(io.BytesIO(), {'payload': 'x' * 65536})

    def test_control_rejects_duplicate_keys_and_nonfinite_values(self):
        for raw in (b'{"type":"ready","type":"fault"}', b'{"generation":NaN}'):
            with self.assertRaises(HuginError):
                read_control(io.BytesIO(struct.pack('!I', len(raw)) + raw))

    def test_fragment_roundtrip_and_alignment(self):
        stream = io.BytesIO()
        write_frame(stream, Frame('pcm', self.identity, 0, b'\x00\x00'))
        stream.seek(0)
        self.assertEqual(read_frame(stream), Frame('pcm', self.identity, 0, b'\x00\x00'))
        for body in (b'x', b'x' * 65538):
            with self.assertRaises(HuginError):
                write_frame(io.BytesIO(), Frame('pcm', self.identity, 0, body))

    def test_large_utf8_transcript_completes_atomically(self):
        raw = ('Grüße. ' * 20000).encode()
        digest = hashlib.sha256(raw).hexdigest()
        receiver = TranscriptReceiver(self.identity, len(raw), digest)
        self.assertIsNone(receiver.text)
        for offset in range(0, len(raw), 65536):
            receiver.add(Frame('text', self.identity, offset, raw[offset:offset+65536]))
            self.assertIsNone(receiver.text)
        self.assertEqual(receiver.finish(len(raw), digest), raw.decode())

    def test_incomplete_duplicate_out_of_order_and_hash_are_rejected(self):
        raw = b'hello'
        digest = hashlib.sha256(raw).hexdigest()
        for offset, data in ((1, raw), (0, raw + b'x')):
            receiver = TranscriptReceiver(self.identity, len(raw), digest)
            with self.assertRaises(HuginError):
                receiver.add(Frame('text', self.identity, offset, data))
        receiver = TranscriptReceiver(self.identity, len(raw), digest)
        receiver.add(Frame('text', self.identity, 0, raw))
        with self.assertRaises(HuginError):
            receiver.add(Frame('text', self.identity, 0, raw))
        for data in (b'hell', b'wrong'):
            receiver = TranscriptReceiver(self.identity, len(raw), digest)
            receiver.add(Frame('text', self.identity, 0, data))
            with self.assertRaises(HuginError):
                receiver.finish(len(raw), digest)
            self.assertIsNone(receiver.text)

    def test_invalid_utf8_and_cancel_discard_entire_draft(self):
        raw = b'\xff'
        digest = hashlib.sha256(raw).hexdigest()
        receiver = TranscriptReceiver(self.identity, 1, digest)
        receiver.add(Frame('text', self.identity, 0, raw))
        with self.assertRaises(HuginError):
            receiver.finish(1, digest)
        receiver = TranscriptReceiver(self.identity, 1, digest)
        receiver.cancel()
        with self.assertRaises(HuginError):
            receiver.add(Frame('text', self.identity, 0, raw))

    def test_malformed_identity_and_truncation_fail_closed(self):
        for generation in (-1, True, '1'):
            with self.assertRaises(HuginError):
                Identity(str(uuid.uuid4()), str(uuid.uuid4()), generation)
        with self.assertRaises(HuginError):
            read_frame(io.BytesIO(b'HUG1'))


if __name__ == '__main__':
    unittest.main()
