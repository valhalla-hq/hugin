"""Controller wiring through fake I/O; these are not native pilot claims."""
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace as NS
import threading
import unittest

from hugin import coordinator as c
from hugin.config import load_settings
from hugin.application import Controller

ROOT = Path(__file__).resolve().parents[2]


class Inputs:
    running = True
    error = None
    def set_cancel_active(self, enabled): self.escape = enabled
    def stop(self): pass


class Microphone:
    owned = False
    fault = None
    def __init__(self, calls): self.calls = calls
    def start(self): self.calls.append('microphone'); self.owned = True
    def stop(self): self.owned = False; return b'\0\0' * 160
    def cancel(self): self.owned = False


class Output:
    def __init__(self, calls): self.calls = calls
    def start(self, job): self.calls.append('player')
    def write(self, pcm, job, cancelled): self.calls.append('audio'); return not cancelled()
    def drain(self, job, cancelled): return not cancelled()
    def stop(self): self.calls.append('reset')
    def close(self): pass


class Clipboard:
    def __init__(self): self.submissions = []; self.cancel_at_commit = None
    def capture_target(self): return NS(target='target', status='target_captured')
    def capture_selection(self, cancelled): return NS(text='Synthetischer Test.', status='captured')
    def deliver(self, text, target, still_current, *, authorize):
        if self.cancel_at_commit: self.cancel_at_commit()
        if still_current() and authorize('transaction'):
            self.submissions.append(text)
            return NS(status='submitted', submitted=True, restored=True)
        return NS(status='cancelled', submitted=False, restored=True)
    def copy(self, text): self.submissions.append(text); return NS(status='copied')
    def close(self): pass


class Pool:
    def __init__(self): self.workers = {}; self.starts = []; self.inference = []
    def start(self, engine):
        self.starts.append(engine)
        self.workers[engine] = NS(engine_instance='actual-' + engine, process=None)
        self.future = Future()
        return self.future
    def transcribe(self, pcm, request_id, generation):
        self.inference.append((request_id, generation)); return Future()
    def synthesize(self, text, voice, request_id, generation, language=None):
        self.inference.append((request_id, generation)); return Future()
    def cancel(self, *args): return True


class Immediate:
    def submit(self, fn, *args):
        future = Future()
        try: future.set_result(fn(*args))
        except Exception as error: future.set_exception(error)
        return future
    def shutdown(self, **kwargs): pass


class ApplicationContracts(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.pool = Pool()
        self.clipboard = Clipboard()
        self.controller = Controller(load_settings(ROOT), inputs=Inputs(),
            microphone=Microphone(self.calls), output=Output(self.calls),
            clipboard=self.clipboard, pool=self.pool, publish=lambda view: None,
            capture_executor=Immediate(), audio_executor=Immediate(), maintenance_executor=Immediate())

    def pump(self):
        while self.controller.pump_once(): pass

    def dictation_ready(self):
        self.controller.command('dictation'); self.pump()
        self.controller.command('dictation'); self.pump()
        init = self.controller.core.snapshot().gpu_slot
        self.assertEqual(self.pool.starts, ['stt'])
        self.assertFalse(self.pool.inference, 'ready callback alone must not schedule native inference')
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'})
        self.pump()
        op = self.controller.core.snapshot().gpu_slot
        self.assertNotEqual(op, init)
        return op

    def test_init_terminal_then_bound_transcript_delivers_once(self):
        op = self.dictation_ready()
        request, generation = self.pool.inference[-1]
        event = dict(type='result', engine='stt', engine_instance='actual-stt',
            request_id=request, generation=generation, text='synthetic marker')
        self.controller.worker_event(event); self.pump()
        self.controller.worker_event(event); self.pump()
        self.assertEqual(self.clipboard.submissions, ['synthetic marker'])
        self.assertEqual(self.controller.core.snapshot().result.text, 'synthetic marker')
        # Delivery is complete, but GPU native ownership remains until terminal.
        self.assertEqual(self.controller.core.snapshot().gpu_slot, op)

    def test_cancel_at_final_clipboard_seam_prevents_injection(self):
        self.dictation_ready()
        self.clipboard.cancel_at_commit = lambda: self.controller.command('cancel')
        request, generation = self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='private marker'))
        self.pump()
        self.assertEqual(self.clipboard.submissions, [])
        self.assertEqual(self.controller.core.snapshot().result.text, 'private marker')

    def test_foreign_worker_identity_cannot_publish_text(self):
        self.dictation_ready()
        request, generation = self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='foreign',
            request_id=request,generation=generation,text='foreign text'))
        self.pump()
        self.assertIsNone(self.controller.core.snapshot().result)
        self.assertEqual(self.clipboard.submissions, [])

    def test_dictation_reset_precedes_microphone_and_old_init_still_holds_slot(self):
        self.controller.command('read'); self.pump()
        old = self.controller.core.snapshot().gpu_slot
        self.calls.clear()
        self.controller.command('dictation'); self.pump()
        self.assertIn('reset',self.calls)
        self.assertIn('microphone',self.calls)
        self.assertLess(self.calls.index('reset'),self.calls.index('microphone'))
        self.assertEqual(self.controller.core.snapshot().gpu_slot,old)

    def test_diagnostic_is_whitelist_and_ram_expiry_clears_ui(self):
        self.dictation_ready()
        request, generation = self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='unique private marker'))
        self.pump()
        self.assertNotIn('unique private marker',self.controller.diagnostic())
        now = self.controller.core.snapshot().result.expires_at
        self.controller.handle(c.Tick(now))
        self.assertEqual(self.controller.view().text,'')


if __name__ == '__main__': unittest.main()
