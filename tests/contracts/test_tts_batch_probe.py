"""Probe failure ownership without loading models, native input or audio devices."""
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import probe_tts_batch as probe


class BatchProbeOwnershipTests(unittest.TestCase):
    def test_late_cancelled_audio_cannot_enter_next_request_or_closed_snapshot(self):
        old, current = probe.Observation('old', 'old-align'), probe.Observation('new', 'new-align')
        entered, release = threading.Event(), threading.Event()
        event = dict(type='audio', engine='tts', request_id='old', generation=1, pcm=b'\0\0')

        def delayed_callback():
            entered.set()
            release.wait(2)
            old.receive(event)  # Callback captured the previous owner before cancel.
            current.receive(event)  # Or it observed the rotated owner after cancel.

        thread = threading.Thread(target=delayed_callback)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            snapshot = old.snapshot(close=True)
            current.receive(dict(event, request_id='new', pcm=b'\1\0'))
        finally:
            release.set()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(snapshot['pcm'], b'')
        self.assertEqual(old.snapshot()['pcm'], b'')
        self.assertEqual(current.snapshot()['pcm'], b'\1\0')

    def test_failed_worker_close_keeps_guard_and_still_closes_other_workers(self):
        guard, first, second = Mock(), Mock(), Mock()
        first.close.side_effect = RuntimeError('synthetic close failure')
        first.closed, second.closed = False, True
        owner = probe.Session(guard)
        owner.workers.extend((first, second))
        self.assertFalse(owner.cleanup())
        second.close.assert_called_once()
        guard.close.assert_not_called()
        first.close.side_effect, first.closed = None, True
        self.assertTrue(owner.cleanup())
        guard.close.assert_called_once()

    def test_incomplete_worker_and_mutex_cleanup_remain_retryable(self):
        guard, worker = Mock(), Mock()
        owner = probe.Session(guard)
        owner.workers.append(worker)
        worker.closed = False
        self.assertFalse(owner.cleanup())
        guard.close.assert_not_called()
        worker.closed = True
        guard.close.side_effect = RuntimeError('synthetic handle failure')
        self.assertFalse(owner.cleanup())
        guard.close.side_effect = None
        self.assertTrue(owner.cleanup())

    def test_busy_guard_starts_no_workers(self):
        guard = Mock()
        guard.acquire.return_value = False
        with patch.object(probe, 'InstanceGuard', return_value=guard), \
                patch.object(probe, 'WorkerClient') as worker:
            with self.assertRaisesRegex(RuntimeError, 'quit normally'):
                probe.run(Path('unused'))
            worker.assert_not_called()
        guard.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
