"""Completion follows accepted delivery, never recognition alone or a new job."""
from concurrent.futures import Future, ThreadPoolExecutor
from types import SimpleNamespace as NS
import json
import threading
import time
import unittest

from hugin import coordinator as c
from hugin.application import Controller
from hugin.errors import HuginError
from test_application import Inputs, Output, Clipboard, Pool, Immediate, controller_settings
from test_capture_cues import Mic, Cues

class Deferred:
    def __init__(self):self.pending=[]
    def submit(self,fn):
        future=Future();self.pending.append((fn,future));return future
    def run(self):
        while self.pending:
            fn,future=self.pending.pop(0)
            if future.set_running_or_notify_cancel():
                try:future.set_result(fn())
                except BaseException as error:future.set_exception(error)


class CompletionCueContracts(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.cues=Cues(self.calls);self.pool=Pool();self.clipboard=Clipboard()
        self.controller=Controller(controller_settings(self),inputs=Inputs(),microphone=Mic(self.calls),
            output=Output(self.calls),clipboard=self.clipboard,pool=self.pool,publish=lambda _:None,
            capture_executor=Immediate(),audio_executor=Immediate(),maintenance_executor=Immediate(),
            selection_executor=Immediate(),delivery_executor=Immediate(),cues=self.cues)

    def pump(self):
        while self.controller.pump_once():pass

    def recognize(self):
        self.controller.command('dictation');self.pump()
        self.controller.command('dictation');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});self.pump()
        self.operation=self.controller.core.snapshot().gpu_slot
        request,generation=self.pool.inference[-1]
        return dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic completed dictation')

    def finish(self,event):
        self.controller.worker_event(event);self.pump()

    def test_success_emits_one_cue_after_delivery_returns_and_duplicates_do_nothing(self):
        original=self.clipboard.deliver
        def deliver(*args,**kwargs):
            self.assertNotIn('complete_cue',self.calls)
            result=original(*args,**kwargs)
            self.calls.append('delivery_returned');return result
        self.clipboard.deliver=deliver
        event=self.recognize()
        self.assertNotIn('complete_cue',self.calls)
        self.finish(event)
        self.assertEqual(self.calls.count('complete_cue'),1)
        self.assertLess(self.calls.index('delivery_returned'),self.calls.index('complete_cue'))
        self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)
        self.controller.handle(c.DeliveryFinished(self.operation.job));self.finish(event)
        self.assertEqual(self.calls.count('complete_cue'),1)
        self.assertEqual(self.clipboard.submissions,['synthetic completed dictation'])

    def test_failed_capture_delivery_and_partial_submission_keep_ram_result_without_success_cue(self):
        for failure in ('capture','delivery','partial'):
            with self.subTest(failure=failure):
                self.setUp()
                if failure=='capture':
                    self.clipboard.capture_target=lambda **_:NS(status='target_unverifiable',target=None)
                else:
                    self.clipboard.deliver=lambda *a,**k:NS(status='clipboard_failed',
                        submitted=failure=='partial',copied=failure=='partial')
                self.finish(self.recognize())
                self.assertNotIn('complete_cue',self.calls)
                self.assertEqual(self.controller.core.snapshot().error.code,
                    'target_unverifiable' if failure=='capture' else 'clipboard_failed')
                self.assertEqual(self.controller.view().text,'synthetic completed dictation')
                self.assertEqual(self.clipboard.submissions,[])

    def test_copy_does_not_repeat_completion_and_a_cancelled_delivery_emits_none(self):
        event=self.recognize()
        self.clipboard.cancel_at_commit=lambda:self.controller.command('cancel')
        self.finish(event)
        self.assertEqual(self.clipboard.submissions,[])
        self.assertNotIn('complete_cue',self.calls)
        self.controller.command('copy');self.pump()
        self.assertNotIn('complete_cue',self.calls)
        self.assertEqual(self.clipboard.submissions,['synthetic completed dictation'])

    def test_queued_completion_is_cancelled_before_a_new_recording_opens(self):
        event=self.recognize();deferred=Deferred();self.controller.capture_executor=deferred
        self.finish(event)
        self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)
        self.assertTrue(deferred.pending,'completion must be owned on the capture FIFO')
        self.controller.tick()  # Old coordinator job no longer owns its token.
        self.calls.clear();self.controller.command('dictation');self.pump()
        deferred.run();self.pump()
        self.assertNotIn('complete_cue',self.calls)
        self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
        self.assertEqual(self.calls,['mic_unarmed','start_cue',('arm',100.025)])

    def test_completion_failure_preserves_delivery_and_result_without_a_second_paste(self):
        original=self.cues.play
        def play(kind,*args):
            if kind=='complete':
                self.cues.cleanup_pending=True
                raise HuginError('audio_failed','synthetic_cue_cleanup')
            return original(kind,*args)
        self.cues.play=play;self.finish(self.recognize())
        self.assertEqual(self.clipboard.submissions,['synthetic completed dictation'])
        self.assertEqual(self.controller.view().text,'synthetic completed dictation')
        report=json.loads(self.controller.diagnostic())
        self.assertEqual(report['error_code'],'audio_failed')
        self.assertTrue(report['pending_cleanup'])
        self.calls.clear();self.controller.command('dictation');self.pump()
        self.assertNotIn('mic_unarmed',self.calls)

    def test_new_recording_interrupts_playing_completion_and_waits_for_cleanup(self):
        event=self.recognize();entered=threading.Event();release=threading.Event()
        original=self.cues.play
        def play(kind,job,cancelled):
            if kind!='complete':return original(kind,job,cancelled)
            self.calls.append('complete_entered');entered.set();release.wait(2)
            self.calls.append('complete_closed');return not cancelled()
        self.cues.play=play
        executor=ThreadPoolExecutor(1);self.controller.capture_executor=executor
        try:
            self.finish(event);self.assertTrue(entered.wait(1))
            self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)
            self.cues.stopped.clear();self.calls.clear()
            self.controller.command('dictation')
            self.assertTrue(self.cues.stopped.is_set(),'new action must reset the old cue immediately')
            self.pump();self.assertNotIn('mic_unarmed',self.calls)
            release.set()
            deadline=time.monotonic()+1
            while self.controller.core.snapshot().state!=c.State.RECORDING and time.monotonic()<deadline:
                self.pump();threading.Event().wait(.001)
            self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
            self.assertLess(self.calls.index('complete_closed'),self.calls.index('mic_unarmed'))
        finally:release.set();executor.shutdown(wait=True);self.pump()

    def test_quit_cancels_queued_completion_and_retains_shutdown_ownership(self):
        event=self.recognize();deferred=Deferred();self.controller.capture_executor=deferred
        self.finish(event)
        self.controller.handle(c.EngineTerminal(self.operation))
        self.controller.command('quit');self.pump()
        self.assertFalse(self.controller.shutdown_ready())
        deferred.run();self.pump()
        self.assertNotIn('complete_cue',self.calls)
        self.assertTrue(self.controller.shutdown_ready())

    def test_input_between_delivery_dispatch_and_cue_registration_cancels_queued_tone(self):
        event=self.recognize();deferred=Deferred();self.controller.capture_executor=deferred
        original=self.controller.core.dispatch
        def dispatch(event):
            result=original(event)
            if isinstance(event,c.DeliveryFinished):self.controller.command('dictation')
            return result
        self.controller.core.dispatch=dispatch
        self.finish(event);deferred.run();self.pump()
        self.assertNotIn('complete_cue',self.calls)
        self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)

    def test_enqueue_then_throw_cancels_claim_without_sound_or_result_loss(self):
        class Broken(Deferred):
            def submit(self,fn):
                super().submit(fn);raise RuntimeError('synthetic enqueue failure')
        event=self.recognize();broken=Broken();self.controller.capture_executor=broken
        self.finish(event);broken.run();self.pump()
        self.assertNotIn('complete_cue',self.calls)
        self.assertEqual(self.clipboard.submissions,['synthetic completed dictation'])
        self.assertEqual(self.controller.view().text,'synthetic completed dictation')
        self.assertEqual(json.loads(self.controller.diagnostic())['error_code'],'audio_failed')
        self.controller.handle(c.EngineTerminal(self.operation))
        self.controller.command('quit');self.pump()
        self.assertTrue(self.controller.shutdown_ready())

    def test_real_input_dispatch_keeps_escape_until_the_completion_owner_finishes(self):
        from hugin.windows.input import WindowsInputs,WM_HOTKEY
        from test_windows_input import FakeInputs
        backend=FakeInputs();cancelled=threading.Event()
        def action(kind):
            self.controller.command(kind);cancelled.set()
        inputs=WindowsInputs(action,pilot=True,backend=backend)
        self.controller.inputs=inputs;inputs.start()
        try:
            event=self.recognize();deferred=Deferred();self.controller.capture_executor=deferred
            self.finish(event)
            self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)
            self.assertIn(3,backend.keys,'completion audio must still be cancellable by Escape')
            backend.post(WM_HOTKEY,3)
            self.assertTrue(cancelled.wait(1),'the input boundary must emit the cancel command')
            self.pump();deferred.run();self.pump()
            self.assertNotIn('complete_cue',self.calls)
            self.assertNotIn(3,backend.keys)
        finally:inputs.stop()

    def test_old_completion_does_not_unregister_escape_for_the_next_recording(self):
        event=self.recognize();deferred=Deferred();self.controller.capture_executor=deferred
        self.finish(event)
        self.controller.command('dictation');self.pump()
        deferred.run();self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
        self.assertTrue(self.controller.inputs.escape)

    def test_domain_cancel_also_invalidates_completion_when_no_domain_job_remains(self):
        event=self.recognize();deferred=Deferred();self.controller.capture_executor=deferred
        self.finish(event);self.controller.handle(c.Cancel())
        deferred.run();self.pump()
        self.assertNotIn('complete_cue',self.calls)

    def test_escape_registration_failure_suppresses_cue_but_preserves_successful_text(self):
        event=self.recognize()
        original=self.controller.inputs.set_cancel_active
        def register(enabled):
            if self.controller.core.snapshot().state==c.State.IDLE:
                raise HuginError('input_conflict','synthetic_escape')
            return original(enabled)
        self.controller.inputs.set_cancel_active=register
        self.finish(event)
        self.assertNotIn('complete_cue',self.calls)
        self.assertEqual(self.clipboard.submissions,['synthetic completed dictation'])


if __name__=='__main__':unittest.main()
