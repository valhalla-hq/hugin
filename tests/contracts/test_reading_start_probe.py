"""Probe ownership failures without devices, worker processes or native handles."""
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import probe_reading_start as probe


class ReadingProbeOwnershipTests(unittest.TestCase):
    def test_failed_controller_keeps_guard_and_executors_for_retry(self):
        guard = Mock()
        owner = probe._ProbeSession(guard)
        owner.controller = Mock()
        owner.controller.command.side_effect = RuntimeError('synthetic cleanup failure')
        executor = Mock()
        owner.executors.append(executor)
        self.assertFalse(owner.cleanup())
        guard.close.assert_not_called()
        executor.close_bounded.assert_not_called()  # Controller needs it for retry.
        owner.controller.command.side_effect = None
        owner.controller.shutdown_ready.return_value = True
        owner.controller.finish_io.return_value = True
        owner.controller.pump_once.return_value = False
        executor.close_bounded.return_value = True
        self.assertTrue(owner.cleanup())
        guard.close.assert_called_once()

    def test_real_controller_processes_quit_again_after_io_close_failure(self):
        from test_application import Inputs, Microphone, Output, Clipboard, Pool, Immediate, controller_settings
        from hugin.application import Controller
        from hugin.errors import HuginError
        root = Path(__file__).resolve().parents[2]
        calls = []
        output = Output(calls)
        output.close = Mock(side_effect=[HuginError('audio_failed', 'test_close'), None])
        controller = Controller(controller_settings(self,root), inputs=Inputs(), microphone=Microphone(calls),
            clipboard=Clipboard(), pool=Pool(), output=output, publish=lambda view: None,
            capture_executor=Immediate(), audio_executor=Immediate(), maintenance_executor=Immediate(),
            selection_executor=Immediate(), delivery_executor=Immediate())
        owner = probe._ProbeSession(Mock())
        owner.controller = controller
        self.assertFalse(owner.cleanup())
        owner.guard.close.assert_not_called()
        self.assertTrue(owner.cleanup())
        self.assertEqual(output.close.call_count, 2)
        owner.guard.close.assert_called_once()

    def test_executor_failure_does_not_skip_other_closes_or_release_guard(self):
        guard = Mock()
        owner = probe._ProbeSession(guard)
        first, second = Mock(), Mock()
        first.close_bounded.side_effect = RuntimeError('synthetic executor failure')
        second.close_bounded.return_value = True
        owner.executors.extend((first, second))
        owner.workers.append(NS(closed=True))
        self.assertFalse(owner.cleanup())
        second.close_bounded.assert_called_once()
        guard.close.assert_not_called()
        first.close_bounded.side_effect = None
        first.close_bounded.return_value = True
        self.assertTrue(owner.cleanup())
        guard.close.assert_called_once()

    def test_unclosed_worker_retains_guard_and_denied_acquire_closes_handle(self):
        guard = Mock()
        owner = probe._ProbeSession(guard)
        owner.workers.append(NS(closed=False))
        self.assertFalse(owner.cleanup())
        guard.close.assert_not_called()
        guard.acquire.return_value = False
        with patch.object(probe, 'InstanceGuard', return_value=guard):
            with self.assertRaisesRegex(RuntimeError, 'quit normally'):
                probe.run(Path('unused'))
        guard.close.assert_called_once()
