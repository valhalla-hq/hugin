"""Panel intent races through the real controller; synthetic I/O only."""
import unittest
from types import SimpleNamespace as NS

from hugin import coordinator as c
import test_application as app


class PanelActions(unittest.TestCase):
    setUp = app.ApplicationContracts.setUp
    pump = app.ApplicationContracts.pump

    def test_duplicate_start_and_stale_finish_cannot_toggle_another_recording(self):
        start=self.controller.view().panel_token
        self.controller.command('panel_dictation',start)
        self.controller.command('panel_dictation',start)
        self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
        view=self.controller.view()
        self.assertEqual(view.dictation_control,'finish')
        old=view.panel_token
        self.controller.command('cancel');self.pump()
        self.controller.command('panel_dictation',self.controller.view().panel_token);self.pump()
        self.controller.command('panel_dictation',old);self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)

    def test_target_is_bound_at_finish_and_shortcut_can_finish_button_recording(self):
        captured=[]
        self.clipboard.capture_native_target=lambda:captured.append('field-at-finish') or NS(
            status='native_target_captured',target='field-at-finish')
        self.clipboard.capture_target=lambda **kw:NS(status='target_captured',target=kw['expected'])
        self.controller.command('panel_dictation',self.controller.view().panel_token);self.pump()
        self.assertEqual(captured,[])
        self.controller.command('dictation');self.pump()
        self.assertEqual(captured,['field-at-finish'])
        self.assertEqual(self.controller.view().dictation_control,'')

    def test_read_button_can_stop_during_selection_before_any_section(self):
        from test_completion_cue import Deferred
        self.controller.selection_executor=Deferred()
        start=self.controller.view().panel_token
        self.controller.command('panel_read',start)
        self.controller.command('panel_read',start)
        self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.TTS_PREPARING)
        self.assertEqual(self.controller.view().reading_control,'stop')
        self.assertFalse(self.controller.view().reading_job)
        self.controller.command('panel_read',self.controller.view().panel_token);self.pump()
        self.assertIsNone(self.controller.core.snapshot().job)
        self.assertFalse(self.pool.starts)

    def test_button_finish_without_target_stops_and_keeps_transcript_without_delivery(self):
        self.clipboard.capture_native_target=lambda:NS(target=None,status='target_unverifiable')
        self.clipboard.capture_target=lambda **kw:self.fail('no target must not reach probe')
        self.clipboard.deliver=lambda *a,**kw:self.fail('no target must not reach delivery')
        self.controller.command('panel_dictation',self.controller.view().panel_token);self.pump()
        self.assertTrue(self.controller.microphone.owned)
        self.controller.command('panel_dictation',self.controller.view().panel_token);self.pump()
        self.assertFalse(self.controller.microphone.owned)
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});self.pump()
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='Synthetic retained text'))
        self.pump()
        self.assertEqual(self.controller.view().text,'Synthetic retained text')
        self.assertEqual(self.controller.core.snapshot().error.code,'target_unverifiable')

    def test_read_is_disabled_during_dictation_and_button_start_interrupts_reading(self):
        self.controller.command('panel_read',self.controller.view().panel_token);self.pump()
        self.assertEqual(self.controller.view().dictation_control,'start')
        self.controller.command('panel_dictation',self.controller.view().panel_token);self.pump()
        self.assertEqual(self.controller.core.snapshot().job.kind,c.JobKind.DICTATION)
        self.assertEqual(self.controller.view().reading_control,'')

    def test_accepted_starting_cancel_survives_recording_ack_during_prompt_stop(self):
        self.controller.command('dictation');self.controller.pump_once()
        self.assertEqual(self.controller.core.snapshot().state,c.State.STARTING)
        token=self.controller.view().panel_token
        original=self.controller.output.stop
        def stop():
            self.controller.output.stop=original
            self.controller.pump_once()  # RecordingStarted ACK wins the thread race.
            self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
            original()
        self.controller.output.stop=stop
        self.controller.command('panel_dictation',token);self.pump()
        self.assertIsNone(self.controller.core.snapshot().job)
        self.assertFalse(self.controller.microphone.owned)

    def test_accepted_read_stop_and_preemption_survive_first_audio_race(self):
        for command in ('panel_read','panel_dictation'):
            with self.subTest(command=command):
                self.setUp()
                self.controller.command('read');self.pump()
                self.pool.future.set_result({'engine_instance':'actual-tts','device':'cpu'});self.pump()
                operation=self.controller.core.snapshot().gpu_slot
                self.assertEqual(self.controller.core.snapshot().state,c.State.TTS_PREPARING)
                token=self.controller.view().panel_token
                original=self.controller.output.stop
                def stop():
                    self.controller.output.stop=original
                    self.controller.handle(c.EngineAudio(operation,b'\0\0'))
                    self.assertEqual(self.controller.core.snapshot().state,c.State.TTS_PLAYING)
                    original()
                self.controller.output.stop=stop
                self.controller.command(command,token);self.pump()
                if command=='panel_dictation':
                    self.assertEqual(self.controller.core.snapshot().job.kind,c.JobKind.DICTATION)
                else:self.assertIsNone(self.controller.core.snapshot().job)
