"""Controller wiring through fake I/O; these are not native pilot claims."""
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace as NS
import json
import threading
import unittest
from hugin.errors import HuginError

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
    def start(self, job): self.calls.append('player'); self.job=job
    def write(self, pcm, job, cancelled): self.calls.append('audio'); return not cancelled()
    def drain(self, job, cancelled): return getattr(self,'job',None)==job and not cancelled()
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
    def __init__(self): self.workers = {}; self.starts = []; self.inference = []; self.inference_futures=[]
    def start(self, engine):
        self.starts.append(engine)
        self.workers[engine] = NS(engine_instance='actual-' + engine, process=None,close=lambda:None)
        self.future = Future()
        return self.future
    def transcribe(self, pcm, request_id, generation):
        self.inference.append((request_id, generation)); return Future()
    def synthesize(self, text, voice, request_id, generation, language=None):
        self.inference.append((request_id, generation)); future=Future();self.inference_futures.append(future);return future
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
            capture_executor=Immediate(), audio_executor=Immediate(), maintenance_executor=Immediate(),
            selection_executor=Immediate())

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

    def test_dictation_preemption_keeps_escape_bound_to_new_recording(self):
        self.controller.command('read'); self.pump()
        self.controller.command('dictation'); self.pump()
        snapshot=self.controller.core.snapshot()
        self.assertEqual(snapshot.job.kind,c.JobKind.DICTATION)
        self.assertTrue(snapshot.escape_reserved)
        self.assertTrue(self.controller.inputs.escape)

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

    def test_start_watchdog_finishes_before_inference_uses_same_worker(self):
        op = self.dictation_ready()
        self.assertNotIn((op.engine,op.engine_instance),self.controller._deadlines)

    def test_failed_worker_cleanup_remains_shutdown_barrier(self):
        self.dictation_ready()
        worker = self.pool.workers['stt']
        def fail(): raise HuginError('worker_timeout','cleanup')
        worker.close = fail
        self.controller.command('quit'); self.pump()
        self.assertFalse(self.controller.shutdown_ready())
        self.assertIs(self.pool.workers['stt'],worker)
        # A deliberate second quit retries that same held owner.
        worker.close = lambda:None
        self.controller.command('quit'); self.pump()
        self.assertTrue(self.controller.shutdown_ready())

    def test_selecting_same_voice_does_not_silence_current_reading(self):
        self.controller.command('read'); self.pump()
        job = self.controller.core.snapshot().job
        self.controller.command('voice','freya'); self.pump()
        self.assertFalse(self.controller._token(job).is_set())

    def test_quit_waits_for_pending_capture_start_and_stop_acknowledgements(self):
        class Deferred:
            def __init__(self): self.pending=[]
            def submit(self,fn,*args):
                future=Future();self.pending.append((fn,args,future));return future
            def flush(self):
                while self.pending:
                    fn,args,future=self.pending.pop(0)
                    try: future.set_result(fn(*args))
                    except Exception as error: future.set_exception(error)
        deferred=Deferred()
        self.controller.capture_executor=deferred
        self.controller.command('dictation');self.pump()
        self.controller.command('quit');self.pump()
        self.assertFalse(self.controller.shutdown_ready())
        deferred.flush();self.pump()
        self.assertFalse(self.controller.microphone.owned)
        self.assertTrue(self.controller.shutdown_ready())

    def test_full_user_queue_cannot_drop_confirmed_worker_cleanup(self):
        self.dictation_ready()
        # Quit dispatch is direct to isolate overflow at the completion producer.
        for _ in range(64): self.controller.command('clear')
        self.controller.handle(c.Shutdown())
        self.controller._stop=True
        self.pump()
        self.assertEqual(self.pool.workers,{})
        self.assertTrue(self.controller.shutdown_ready())

    def test_deliberate_quit_retries_identified_audio_reset_barrier(self):
        self.controller.command('read');self.pump()
        real_stop=self.controller.output.stop
        failures=[True,True]
        def stop():
            if failures:
                failures.pop()
                raise HuginError('audio_failed','transient_reset')
            real_stop()
        self.controller.output.stop=stop
        self.controller.command('cancel');self.pump()
        self.assertIsNotNone(self.controller.core.snapshot().cancelling_job)
        self.controller.command('quit');self.pump()
        self.assertTrue(self.controller.shutdown_ready())

    def test_quit_retry_preserves_success_after_queued_failed_reset(self):
        self.controller.command('read');self.pump()
        real_stop=self.controller.output.stop
        failures=[True,True]
        def stop():
            if failures:
                failures.pop()
                raise HuginError('audio_failed','transient_reset')
            real_stop()
        self.controller.output.stop=stop
        self.controller.command('cancel');self.controller.pump_once()
        self.controller.command('quit');self.pump()
        self.assertTrue(self.controller.shutdown_ready())

    def test_system_resume_invalidates_active_capture_and_never_replays_it(self):
        self.controller.command('dictation');self.pump()
        self.assertTrue(self.controller.microphone.owned)
        self.controller.command('system_resume');self.pump()
        self.assertFalse(self.controller.microphone.owned)
        self.assertIsNone(self.controller.core.snapshot().job)
        self.assertFalse(self.pool.starts)

    def test_io_cleanup_attempts_each_owner_and_retains_failed_one(self):
        calls=[]
        def fail(): calls.append('output');raise HuginError('audio_failed','close')
        self.controller.output.close=fail
        self.controller.inputs.stop=lambda:calls.append('inputs')
        self.controller.clipboard.close=lambda:calls.append('clipboard')
        self.assertFalse(self.controller.finish_io())
        self.assertEqual(calls,['inputs','output','clipboard'])
        self.controller.output.close=lambda:calls.append('output-retry')
        self.controller.command('quit');self.pump()
        self.assertTrue(self.controller.finish_io())
        self.assertEqual(calls,['inputs','output','clipboard','output-retry'])

    def test_spoken_reading_then_zero_pcm_reading_both_finish(self):
        self.controller.command('read');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-tts','device':'cuda'});self.pump()
        operation=self.controller.core.snapshot().gpu_slot
        self.controller.handle(c.EngineAudio(operation,b'\0\0'))
        self.pool.inference_futures[-1].set_result({'code':None,'cancelled':False});self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)
        self.controller.command('read');self.pump()
        # A valid empty stream follows the spoken stream in the same worker.
        self.pool.inference_futures[-1].set_result({'code':None,'cancelled':False});self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)

    def test_diagnostic_has_observed_engine_versions_profile_and_event_time(self):
        self.controller.command('cancel');self.pump()
        data=json.loads(self.controller.diagnostic())
        self.assertEqual(set(data['engine_versions']),{'stt','tts'})
        self.assertEqual(set(data['engine_versions']['stt']),{'faster-whisper','ctranslate2','numpy','av'})
        self.assertEqual(data['profile_id'],'deutsch-3')
        self.assertIsNotNone(data['last_input_utc'])

    def test_diagnostic_tracks_cancelled_native_operation_until_terminal(self):
        self.controller.command('read');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-tts','device':'cuda'});self.pump()
        self.controller.command('cancel');self.pump()
        self.assertTrue(json.loads(self.controller.diagnostic())['pending_cleanup'])
        self.assertFalse(json.loads(self.controller.diagnostic())['components']['tts']['ready'])
        self.pool.inference_futures[-1].set_result({'code':None,'cancelled':True});self.pump()
        self.assertFalse(json.loads(self.controller.diagnostic())['pending_cleanup'])

    def test_diagnostic_clears_capture_cleanup_after_confirmed_close(self):
        def partial_start():
            self.controller.microphone.owned=True
            raise HuginError('microphone_failed','synthetic_partial_start')
        self.controller.microphone.start=partial_start
        self.controller.command('dictation');self.pump()
        self.assertFalse(self.controller.microphone.owned)
        self.assertIsNone(self.controller.core.snapshot().cancelling_job)
        self.assertFalse(json.loads(self.controller.diagnostic())['pending_cleanup'])


if __name__ == '__main__': unittest.main()
