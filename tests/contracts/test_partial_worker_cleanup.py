"""Real process ownership across failed creation; synthetic OS handles only."""
from dataclasses import replace
from pathlib import Path
import unittest

from hugin.errors import HuginError
from hugin.windows.process import OwnedProcess
from hugin.workers.client import WorkerClient
from test_windows_process import FakeProcess


class PartialWorkerCleanup(unittest.TestCase):
    def test_no_created_process_retries_handles_without_waiting_for_exit(self):
        backend=FakeProcess();attempts=[]
        def create(*args):raise HuginError('worker_failed','synthetic_create')
        def close(handle):
            attempts.append(handle)
            if len(attempts)<=2:raise HuginError('worker_failed','synthetic_handle_cleanup')
        backend.create_suspended=create;backend.close_handle=close
        with self.assertRaises(HuginError) as failure:
            OwnedProcess(['fake','worker'],backend=backend)
        owner=failure.exception.owner
        client=WorkerClient(Path(__file__).resolve().parents[2],'stt',lambda event:None)
        client.process=owner
        client.settings=replace(client.settings,limits={**client.settings.limits,
            'cancel_seconds':0,'exit_seconds':0})
        try:
            with self.assertRaises(HuginError):client.close()
            self.assertFalse(client.closed)
            self.assertIs(client.process,owner)
            self.assertEqual(len(attempts),2)
            client.close()
            self.assertTrue(client.closed)
            self.assertEqual(len(attempts),3)
            self.assertFalse(any(isinstance(e,tuple) and e[0].startswith('terminate') for e in backend.events))
        finally:
            backend.close_handle=lambda handle:None
            owner.close()
