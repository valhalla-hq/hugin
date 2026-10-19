"""IA-003/005: synthetic device clocks and fake owned outputs; no native audio."""
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from hugin import coordinator as c
from hugin.audio import Microphone
from hugin.application import Controller
from hugin.config import load_settings
from hugin.errors import HuginError
from test_application import Inputs, Output, Clipboard, Pool, Immediate

ROOT=Path(__file__).resolve().parents[2]


class Stream:
    time=100.0
    def __init__(self,**kwargs):self.callback=kwargs['callback'];self.closed=False
    def start(self):pass
    def stop(self,**kwargs):pass
    def abort(self,**kwargs):pass
    def close(self,**kwargs):self.closed=True


class GateContracts(unittest.TestCase):
    def microphone(self):
        class Abort(Exception):pass
        fake=NS(CallbackAbort=Abort)
        microphone=Microphone(4096,stream_factory=Stream)
        self.addCleanup(microphone.cancel)
        return microphone,fake

    def test_unarmed_and_old_or_overlapping_adc_blocks_never_enter_the_capture(self):
        microphone,sd=self.microphone()
        with patch.dict('sys.modules',sounddevice=sd):
            microphone.start(armed=False);stream=microphone._stream
            stream.callback(b'\1\0'*160,160,NS(inputBufferAdcTime=100),False)
            self.assertEqual(microphone.device_time,100)
            microphone.arm_after(100.025)
            for adc in (99.9,100.02):
                stream.callback(b'\1\0'*160,160,NS(inputBufferAdcTime=adc),False)
            stream.callback(b'\2\0'*160,160,NS(inputBufferAdcTime=100.025),False)
            self.assertEqual(microphone.stop(),b'\2\0'*160)
        self.assertFalse(microphone.owned)

    def test_unknown_adc_time_fails_closed_and_cancel_discards_late_callback(self):
        for adc in (None,True,float('nan'),float('inf')):
            microphone,sd=self.microphone()
            with patch.dict('sys.modules',sounddevice=sd):
                microphone.start(armed=False);microphone.arm_after(100)
                with self.assertRaises(sd.CallbackAbort):
                    microphone._stream.callback(b'\1\0',1,NS(inputBufferAdcTime=adc),False)
                self.assertEqual(microphone.fault.code,'microphone_failed')
                microphone.cancel()
        microphone,sd=self.microphone()
        with patch.dict('sys.modules',sounddevice=sd):
            microphone.start(armed=False);old=microphone._stream
            microphone.cancel();microphone.start(armed=False);microphone.arm_after(100)
            old.callback(b'\7\0',1,NS(inputBufferAdcTime=101),False)
            microphone._stream.callback(b'\2\0',1,NS(inputBufferAdcTime=101),False)
            self.assertEqual(microphone.stop(),b'\2\0')

    def test_gate_rejects_unknown_clock_and_invalid_cutoff(self):
        microphone,sd=self.microphone()
        with patch.dict('sys.modules',sounddevice=sd):
            microphone.start(armed=False)
            for value in (True,float('nan'),float('inf')):
                with self.assertRaises(HuginError):microphone.arm_after(value)
                microphone._stream.time=value
                with self.assertRaises(HuginError):_ = microphone.device_time

    def test_retired_callback_fault_cannot_poison_the_next_microphone_session(self):
        microphone,sd=self.microphone()
        with patch.dict('sys.modules',sounddevice=sd):
            microphone.start(armed=False);old=microphone._stream
            class Delayed:
                @property
                def inputBufferAdcTime(self):
                    microphone.cancel();microphone.start(armed=False);microphone.arm_after(100)
                    return None
            with self.assertRaises(sd.CallbackAbort):old.callback(b'\1\0',1,Delayed(),False)
            self.assertIsNone(microphone.fault,'callback failure belongs to its original stream')
            microphone._stream.callback(b'\2\0',1,NS(inputBufferAdcTime=101),False)
            self.assertEqual(microphone.stop(),b'\2\0')

    def test_callback_failure_during_native_start_is_not_a_successful_open(self):
        class Abort(Exception):pass
        class FailedStream(Stream):
            def start(self):
                try:self.callback(b'\1\0',1,NS(inputBufferAdcTime=100),True)
                except Abort:pass  # PortAudio does not propagate callback exceptions.
        microphone=Microphone(4096,stream_factory=FailedStream)
        with patch.dict('sys.modules',sounddevice=NS(CallbackAbort=Abort)):
            with self.assertRaises(HuginError):microphone.start(armed=False)
        self.assertFalse(microphone.owned)

    def test_portaudio_cleanup_errors_are_requested_and_never_acknowledged_as_closed(self):
        class StrictStream(Stream):
            failure=None
            def stop(self,ignore_errors=True):
                if self.failure=='stop' and not ignore_errors:raise RuntimeError('synthetic native stop error')
            def abort(self,ignore_errors=True):
                if self.failure=='abort' and not ignore_errors:raise RuntimeError('synthetic native abort error')
            def close(self,ignore_errors=True):
                if self.failure=='close' and not ignore_errors:raise RuntimeError('synthetic native close error')
                self.closed=True
        for operation in ('stop','close','abort'):
            microphone=Microphone(4096,stream_factory=StrictStream)
            with patch.dict('sys.modules',sounddevice=NS(CallbackAbort=RuntimeError)):
                microphone.start();microphone._stream.failure=operation
                with self.assertRaises(HuginError):
                    (microphone.cancel if operation=='abort' else microphone.stop)()
                self.assertTrue(microphone.owned)
                microphone._stream.failure=None;microphone.cancel()
                self.assertFalse(microphone.owned)


class Mic:
    owned=False;fault=None;device_time=100.0
    def __init__(self,calls):self.calls=calls
    def start(self,*,armed=True):self.calls.append('mic' if armed else 'mic_unarmed');self.owned=True
    def arm_after(self,cutoff):self.calls.append(('arm',cutoff))
    def stop(self):self.calls.append('mic_close');self.owned=False;return b'\2\0'*160
    def cancel(self):self.calls.append('mic_cancel');self.owned=False


class Cues:
    tail_seconds=.025;cleanup_pending=False;closed=False
    def __init__(self,calls):self.calls=calls;self.stopped=threading.Event()
    def play(self,kind,job,cancelled):
        if cancelled():return False
        self.calls.append(kind+'_cue');return True
    def stop(self,job=None):self.stopped.set()
    def close(self):self.closed=True


class CaptureCueContracts(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.mic=Mic(self.calls);self.cues=Cues(self.calls);self.pool=Pool()
        self.clipboard=Clipboard()
        self.clipboard.capture_target=lambda **_:self.calls.append('uia') or NS(target='target',status='target_captured')
        self.controller=Controller(load_settings(ROOT),inputs=Inputs(),microphone=self.mic,
            output=Output(self.calls),clipboard=self.clipboard,pool=self.pool,publish=lambda _:None,
            capture_executor=Immediate(),audio_executor=Immediate(),maintenance_executor=Immediate(),
            selection_executor=Immediate(),delivery_executor=Immediate(),cues=self.cues)

    def pump(self):
        while self.controller.pump_once():pass

    def test_hardware_cue_gate_and_stop_cue_precede_slow_target_and_engine(self):
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.calls,['mic_unarmed','start_cue',('arm',100.025)])
        self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.calls[-3:],['mic_close','end_cue','uia'])
        self.assertEqual(self.pool.starts,['stt'])

    def test_start_failure_and_start_cue_failure_never_arm_or_emit_end_cue(self):
        for failure in ('mic','cue'):
            self.setUp()
            def fail(*_,**__):raise HuginError('audio_failed' if failure=='cue' else 'microphone_failed')
            if failure=='mic':self.mic.start=fail
            else:self.cues.play=fail
            self.controller.command('dictation');self.pump()
            self.assertFalse(self.mic.owned)
            self.assertFalse(any(isinstance(item,tuple) for item in self.calls))
            self.assertNotIn('end_cue',self.calls)
            self.assertEqual(self.controller.core.snapshot().state,c.State.ERROR)

    def test_unexplained_false_start_cue_is_a_failure_not_a_permanent_starting_job(self):
        self.cues.play=lambda *args:False
        self.controller.command('dictation');self.pump()
        self.assertFalse(self.mic.owned)
        self.assertEqual(self.controller.core.snapshot().state,c.State.ERROR)

    def test_end_cue_failure_preserves_valid_pcm_and_retains_cleanup_fact(self):
        real=self.cues.play
        def play(kind,*args):
            if kind=='end':
                self.cues.cleanup_pending=True
                raise HuginError('audio_failed','cue_cleanup')
            return real(kind,*args)
        self.cues.play=play
        self.controller.command('dictation');self.pump()
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.pool.starts,['stt'])
        seen=[]
        self.pool.transcribe=lambda pcm,*args:seen.append(pcm) or Future()
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});self.pump()
        self.assertEqual(seen,[b'\2\0'*160])
        import json
        self.assertTrue(json.loads(self.controller.diagnostic())['pending_cleanup'])

    def test_stop_failure_does_not_emit_normal_end_signal(self):
        self.controller.command('dictation');self.pump()
        def fail():raise HuginError('microphone_failed')
        self.mic.stop=fail
        self.controller.command('dictation');self.pump()
        self.assertNotIn('end_cue',self.calls)
        self.assertFalse(self.pool.starts)

    def test_failed_microphone_close_remains_owned_until_quit_retry(self):
        self.controller.command('dictation');self.pump()
        real_cancel=self.mic.cancel
        def fail():raise HuginError('microphone_failed','capture_close')
        self.mic.stop=fail;self.mic.cancel=fail
        self.controller.command('dictation');self.pump()
        self.assertTrue(self.mic.owned)
        self.assertIsNotNone(self.controller.core.snapshot().cancelling_job)
        self.assertNotIn('end_cue',self.calls)
        self.mic.cancel=real_cancel
        self.controller.command('quit');self.pump()
        self.assertTrue(self.controller.shutdown_ready())

    def test_tts_reset_still_precedes_cue_capture_without_waiting_for_engine_terminal(self):
        self.controller.command('read');self.pump()
        old=self.controller.core.snapshot().gpu_slot
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
        self.assertEqual(self.controller.core.snapshot().gpu_slot,old)
        self.assertLess(self.calls.index('reset'),self.calls.index('mic_unarmed'))
        self.assertLess(self.calls.index('mic_unarmed'),self.calls.index('start_cue'))

    def test_unknown_cue_cleanup_blocks_a_new_microphone_open(self):
        self.cues.cleanup_pending=True
        self.controller.command('dictation');self.pump()
        self.assertNotIn('mic_unarmed',self.calls)
        self.assertEqual(self.controller.core.snapshot().state,c.State.ERROR)

    def test_cancel_reaches_blocked_cue_without_waiting_behind_capture_fifo(self):
        entered=threading.Event()
        def blocked(kind,job,cancelled):
            entered.set();self.cues.stopped.wait(1);return not cancelled()
        self.cues.play=blocked
        executor=ThreadPoolExecutor(1);self.controller.capture_executor=executor
        try:
            self.controller.command('dictation');self.pump();self.assertTrue(entered.wait(1))
            self.controller.command('cancel')
            self.assertTrue(self.cues.stopped.is_set(),'input cancellation must reach cue outside FIFO')
            self.pump();executor.shutdown(wait=True);self.pump()
            self.assertFalse(self.mic.owned)
            self.assertFalse(any(isinstance(item,tuple) for item in self.calls))
            self.assertNotIn('end_cue',self.calls)
        finally:self.cues.stopped.set();executor.shutdown(wait=True)

    def test_fast_double_toggle_never_opens_or_arms_a_cancelled_start(self):
        class Deferred:
            def __init__(self):self.pending=[]
            def submit(self,fn):
                self.pending.append(fn);return Future()
        deferred=Deferred();self.controller.capture_executor=deferred
        self.controller.command('dictation');self.pump()
        self.controller.command('dictation');self.pump()
        for fn in deferred.pending:fn()
        self.pump()
        self.assertFalse(self.mic.owned)
        self.assertNotIn('mic_unarmed',self.calls)
        self.assertNotIn('start_cue',self.calls)
        self.assertFalse(self.pool.starts)
        self.assertIsNone(self.controller.core.snapshot().job)

    def test_quit_retains_failed_cue_owner_until_explicit_cleanup_retry(self):
        failures=[True]
        def close():
            if failures:failures.pop();raise HuginError('audio_failed','cue_cleanup')
            self.cues.closed=True
        self.cues.close=close
        self.controller.command('quit');self.pump()
        self.assertFalse(self.controller.finish_io());self.assertFalse(self.cues.closed)
        self.controller.command('quit');self.pump()
        self.assertTrue(self.controller.finish_io());self.assertTrue(self.cues.closed)

    def test_quit_while_start_cue_is_blocked_waits_for_capture_cleanup(self):
        entered=threading.Event();release=threading.Event()
        def play(*args):entered.set();release.wait(1);return False
        self.cues.play=play
        executor=ThreadPoolExecutor(1);self.controller.capture_executor=executor
        try:
            self.controller.command('dictation');self.pump();self.assertTrue(entered.wait(1))
            self.controller.command('quit');self.pump()
            self.assertFalse(self.controller.shutdown_ready())
            release.set();executor.shutdown(wait=True);self.pump()
            self.assertFalse(self.mic.owned)
            self.assertTrue(self.controller.shutdown_ready())
            self.assertNotIn('end_cue',self.calls)
        finally:release.set();executor.shutdown(wait=True)


TEST_SIGNALS={'start':b'\x01\0'*100,'end':b'\x02\0'*200,'complete':b'\x03\0'*32309}


class CueOutputContracts(unittest.TestCase):
    def test_concurrent_reset_facts_do_not_overwrite_a_later_cleanup_failure(self):
        from hugin.cues import DictationCues
        entered=threading.Event();release=threading.Event();second=threading.Event();errors=[]
        class PCM:
            calls=0
            def stop(self):
                self.calls+=1
                if self.calls==1:entered.set();release.wait(1)
                else:raise HuginError('audio_failed')
        owner=DictationCues(TEST_SIGNALS,output=PCM())
        def reset(later=False):
            if later:second.set()
            try:owner.stop()
            except HuginError:errors.append(True)
        first=threading.Thread(target=reset);last=threading.Thread(target=reset,args=(True,))
        first.start();self.assertTrue(entered.wait(1));last.start();self.assertTrue(second.wait(1))
        threading.Event().wait(.02);release.set();first.join(1);last.join(1)
        self.assertEqual(errors,[True])
        self.assertTrue(owner.cleanup_pending,'a confirmed older reset must not erase a newer failure')

    def test_deadline_is_failure_even_when_driver_reports_completed_after_expiry(self):
        from hugin.cues import DictationCues
        now=[0.0]
        class PCM:
            def start(self,job):pass
            def write(self,*args):return True
            def drain(self,*args):now[0]=1;return True
            def stop(self):pass
            def close(self):pass
        owner=DictationCues(TEST_SIGNALS,output=PCM(),clock=lambda:now[0])
        with self.assertRaises(HuginError):owner.play('start','job',lambda:False)
        self.assertFalse(owner.cleanup_pending)
        owner.close()

    def test_supplied_cues_reach_output_unchanged_and_long_completion_can_finish(self):
        from hugin.cues import DictationCues
        calls=[];blocks=[];now=[0.0]
        class PCM:
            def start(self,job):calls.append('open')
            def write(self,pcm,job,cancelled):blocks.append(pcm);return not cancelled()
            def drain(self,job,cancelled):
                calls.append('drain')
                now[0]+=len(TEST_SIGNALS[job[1]])/48000+.1
                return not cancelled()
            def stop(self):calls.append('reset')
            def close(self):calls.append('close')
        owner=DictationCues(TEST_SIGNALS,output=PCM(),clock=lambda:now[0])
        self.assertTrue(owner.play('start','job',lambda:False))
        self.assertTrue(owner.play('end','job',lambda:False))
        self.assertTrue(owner.play('complete','job',lambda:False))
        self.assertEqual(blocks,list(TEST_SIGNALS.values()))
        self.assertEqual(calls.count('drain'),3)
        owner.close();self.assertTrue(owner.closed)

    def test_cancel_timeout_and_failed_reset_cannot_claim_success_or_drop_owner(self):
        from hugin.cues import DictationCues
        class PCM:
            failed=True
            def start(self,job):pass
            def write(self,pcm,job,cancelled):return not cancelled()
            def drain(self,job,cancelled):return not cancelled()
            def stop(self):
                if self.failed:raise HuginError('audio_failed')
            def close(self):self.stop()
        output=PCM();owner=DictationCues(TEST_SIGNALS,output=output)
        with self.assertRaises(HuginError):owner.play('start','job',lambda:False)
        self.assertTrue(owner.cleanup_pending);self.assertFalse(owner.closed)
        with self.assertRaises(HuginError):owner.close()
        output.failed=False;owner.stop();self.assertFalse(owner.cleanup_pending)
        self.assertFalse(owner.play('start','old',lambda:True))
        owner.close();self.assertTrue(owner.closed)


if __name__=='__main__':unittest.main()
