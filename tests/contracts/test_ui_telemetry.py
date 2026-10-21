"""UI facts come from accepted capture/delivery; no native devices or UI."""
from pathlib import Path
import struct
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from hugin import coordinator as c
from hugin.application import Controller, _CueFailure
from hugin.audio import Microphone
from hugin.config import load_settings
from hugin.errors import HuginError
from test_application import Inputs, Output, Clipboard, Pool, Immediate
from test_capture_cues import Mic, Cues, Stream
from test_completion_cue import Deferred


ROOT=Path(__file__).resolve().parents[2]


class MicrophoneMeterContracts(unittest.TestCase):
    def setUp(self):
        class Abort(Exception):pass
        self.now=100.0
        self.sd=NS(CallbackAbort=Abort)
        self.patcher=patch.dict('sys.modules',sounddevice=self.sd)
        self.patcher.start();self.addCleanup(self.patcher.stop)
        self.mic=Microphone(4096,stream_factory=Stream,clock=lambda:self.now)
        self.addCleanup(self.mic.cancel)

    def send(self,pcm,adc=101.0,status=False,stream=None):
        (stream or self.mic._stream).callback(pcm,len(pcm)//2,NS(inputBufferAdcTime=adc),status)

    def test_meter_uses_only_accepted_pcm_after_gate_and_preserves_capture_bytes(self):
        pcm=struct.pack('<hhhh',16384,-16384,16384,-16384)
        self.mic.start(armed=False)
        self.send(pcm);self.assertEqual(self.mic.audio_level,0.0)
        self.mic.arm_after(101.025)
        self.send(pcm,101.02);self.assertEqual(self.mic.audio_level,0.0)
        self.send(pcm,101.025);self.assertAlmostEqual(self.mic.audio_level,.5)
        self.assertEqual(self.mic.stop(),pcm)
        self.assertEqual(self.mic.audio_level,0.0)

    def test_meter_is_bounded_current_window_fresh_and_silent_without_fabricated_activity(self):
        self.mic.start()
        self.send(struct.pack('<h',-32768)*512)
        self.assertEqual(self.mic.audio_level,1.0)
        self.now+=.251;self.assertEqual(self.mic.audio_level,0.0)
        # The current bounded tail, rather than retained speech, owns the meter.
        pcm=struct.pack('<h',-32768)*512+b'\0\0'*512
        self.send(pcm);self.assertEqual(self.mic.audio_level,0.0)
        self.send(struct.pack('<h',8192)*4)
        self.assertAlmostEqual(self.mic.audio_level,.25)
        self.now-=1;self.assertEqual(self.mic.audio_level,0.0)

    def test_fault_cancel_and_retired_inflight_callback_do_not_contaminate_new_session(self):
        self.mic.start(armed=False);self.mic.arm_after(100)
        self.send(struct.pack('<h',16384)*4)
        with self.assertRaises(self.sd.CallbackAbort):self.send(b'\0\0',status=True)
        self.assertEqual(self.mic.audio_level,0.0)
        self.mic.cancel();self.mic.start(armed=False);self.mic.arm_after(100)
        old=self.mic._stream
        outer=self
        class Delayed:
            @property
            def inputBufferAdcTime(self):
                outer.mic.cancel();outer.mic.start(armed=False);outer.mic.arm_after(100)
                outer.send(struct.pack('<h',8192)*4)
                return 101.0
        with self.assertRaises(self.sd.CallbackAbort):
            old.callback(struct.pack('<h',32767)*4,4,Delayed(),False)
        self.assertAlmostEqual(self.mic.audio_level,.25)
        self.mic.cancel();self.assertEqual(self.mic.audio_level,0.0)

    def test_stop_resets_meter_before_native_cleanup_and_blocks_late_meter_updates(self):
        self.mic.start();self.send(struct.pack('<h',16384)*4)
        original=self.mic._stream.stop
        def stop(**kwargs):
            self.assertEqual(self.mic.audio_level,0.0)
            self.send(struct.pack('<h',32767)*4)
            self.assertEqual(self.mic.audio_level,0.0)
            original(**kwargs)
        self.mic._stream.stop=stop
        self.mic.stop();self.assertEqual(self.mic.audio_level,0.0)

    def test_rejected_capture_capacity_clears_previous_meter(self):
        self.mic.start();self.send(struct.pack('<h',16384)*4)
        with self.assertRaises(self.sd.CallbackAbort):self.send(b'\0'*(4096+2))
        self.assertEqual(self.mic.audio_level,0.0)


class PresentationFactsContracts(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.pool=Pool();self.clipboard=Clipboard();self.mic=Mic(self.calls)
        self.controller=Controller(load_settings(ROOT),inputs=Inputs(),microphone=self.mic,
            output=Output(self.calls),clipboard=self.clipboard,pool=self.pool,publish=lambda _:None,
            capture_executor=Immediate(),audio_executor=Immediate(),maintenance_executor=Immediate(),
            selection_executor=Immediate(),delivery_executor=Immediate(),cues=Cues(self.calls))

    def pump(self):
        while self.controller.pump_once():pass

    def recognize(self):
        self.controller.command('dictation');self.pump()
        self.controller.command('dictation');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});self.pump()
        self.operation=self.controller.core.snapshot().gpu_slot
        request,generation=self.pool.inference[-1]
        return dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic UI receipt')

    def finish(self,event):
        self.controller.worker_event(event);self.pump()

    def test_view_exposes_only_bounded_live_recording_meter_and_actual_processing_states(self):
        self.mic.audio_level=.4
        self.assertEqual(self.controller.view().audio_level,0.0)
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.controller.view().audio_level,.4)
        for invalid in (None,True,-.1,1.1,float('nan'),float('inf'),'0.5'):
            self.mic.audio_level=invalid
            self.assertEqual(self.controller.view().audio_level,0.0)
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.controller.view().activity,'processing')
        self.assertEqual(self.controller.view().audio_level,0.0)
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});self.pump()
        request,generation=self.pool.inference[-1]
        self.controller.delivery_executor=Deferred()
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic processing'))
        self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.DELIVERING)
        self.assertEqual(self.controller.view().activity,'processing')

    def test_active_action_follows_workflow_and_clears_on_cancel_error_and_idle(self):
        from dataclasses import replace
        snapshot=self.controller.core.snapshot()
        # Public coordinator snapshot -> Controller -> presentation boundary.
        for states,expected in (((c.State.STARTING,c.State.RECORDING,c.State.TRANSCRIBING,
                                   c.State.DELIVERING),'dictation'),
                                ((c.State.TTS_PREPARING,c.State.TTS_PLAYING),'reading'),
                                ((c.State.IDLE,c.State.CANCELLING,c.State.ERROR,c.State.STOPPING),'')):
            for state in states:
                with self.subTest(state=state),patch.object(self.controller.core,'snapshot',
                        return_value=replace(snapshot,state=state)):
                    self.assertEqual(self.controller.view().active_action,expected)
                    self.controller._runtime_error=HuginError('audio_failed','fixture')
                    self.assertEqual(self.controller.view().active_action,'')
                    self.controller._runtime_error=None

    def test_accepted_delivery_owns_fixed_receipt_even_without_cues_and_duplicates_do_not_replay(self):
        self.controller.cues=None
        event=self.recognize()
        self.assertEqual(self.controller.view().completion_id,0)
        self.finish(event);first=self.controller.view()
        self.assertEqual(first.completion_id,1)
        self.assertGreater(first.completion_until,0.0)
        for _ in range(3):
            self.controller.tick()
            self.controller.handle(c.DeliveryFinished(self.operation.job))
            self.finish(event)
            view=self.controller.view()
            self.assertEqual((view.completion_id,view.completion_until),
                (first.completion_id,first.completion_until))
        self.assertEqual(self.clipboard.submissions,['synthetic UI receipt'])

    def test_failed_or_cancelled_delivery_and_manual_copy_never_issue_success(self):
        for failure in ('capture','partial','cancel'):
            with self.subTest(failure=failure):
                self.setUp()
                if failure=='capture':
                    self.clipboard.capture_target=lambda **_:NS(status='target_unverifiable',target=None)
                elif failure=='partial':
                    self.clipboard.deliver=lambda *a,**k:NS(status='clipboard_failed',submitted=True,copied=failure=='partial')
                else:self.clipboard.cancel_at_commit=lambda:self.controller.command('cancel')
                self.finish(self.recognize())
                if failure!='cancel':self.assertEqual(self.controller.core.snapshot().error.code,
                    'target_unverifiable' if failure=='capture' else 'clipboard_failed')
                self.assertEqual(self.controller.view().completion_id,0)
                self.assertEqual(self.controller.view().completion_until,0.0)
                self.controller.command('copy');self.pump()
                self.assertEqual(self.controller.view().completion_id,0)

    def test_new_action_cancel_and_error_clear_visual_without_losing_delivered_text(self):
        for action in ('dictation','read','cancel','copy','clear','quit','error'):
            with self.subTest(action=action):
                self.setUp();self.finish(self.recognize())
                first=self.controller.view()
                self.assertGreater(first.completion_until,0.0)
                if action=='error':self.controller.handle(_CueFailure(HuginError('audio_failed','fixture')))
                else:self.controller.command(action)
                self.assertEqual(self.controller.view().completion_until,0.0)
                self.assertEqual(self.controller.view().completion_id,first.completion_id)
                if action!='clear':self.assertEqual(self.controller.view().text,'synthetic UI receipt')

    def test_input_during_delivery_dispatch_prevents_late_visual_registration(self):
        event=self.recognize();original=self.controller.core.dispatch
        def dispatch(value):
            result=original(value)
            if isinstance(value,c.DeliveryFinished):self.controller.command('read')
            return result
        self.controller.core.dispatch=dispatch
        self.finish(event)
        self.assertEqual(self.controller.view().completion_until,0.0)
        self.assertEqual(self.controller.view().completion_id,0)

    def test_input_after_delivery_before_finish_handler_cannot_create_a_late_receipt(self):
        event=self.recognize();original=self.controller._token;interrupted=False
        def token(job):
            nonlocal interrupted
            value=original(job)
            if self.clipboard.submissions and not interrupted:
                interrupted=True;self.controller.command('read')
            return value
        self.controller._token=token
        self.finish(event)
        self.assertTrue(interrupted)
        self.assertEqual(self.controller.view().completion_id,0)
        self.assertEqual(self.controller.view().completion_until,0.0)

    def test_cue_failure_preserves_delivery_receipt_but_error_supersedes_its_visual(self):
        original=self.controller.cues.play
        def play(kind,*args):
            if kind=='complete':raise HuginError('audio_failed','fixture')
            return original(kind,*args)
        self.controller.cues.play=play
        self.finish(self.recognize());view=self.controller.view()
        self.assertEqual(view.completion_id,1)
        self.assertEqual(view.completion_until,0.0)
        self.assertEqual(view.activity,'error')
        self.assertEqual(self.clipboard.submissions,['synthetic UI receipt'])

    def test_receipt_ids_advance_after_cleared_success_without_reusing_previous_deadline(self):
        self.finish(self.recognize());first=self.controller.view()
        self.controller.handle(c.EngineTerminal(self.operation))
        self.controller.command('dictation');self.pump()
        self.controller.command('dictation');self.pump()
        request,generation=self.pool.inference[-1]
        self.finish(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='second synthetic receipt'))
        self.assertEqual(self.controller.view().completion_id,first.completion_id+1)
        self.assertGreaterEqual(self.controller.view().completion_until,first.completion_until)


if __name__=='__main__':unittest.main()
