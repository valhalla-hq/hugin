"""Controller wiring through fake I/O; these are not native pilot claims."""
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import json
import threading
import time
import unittest
from unittest.mock import patch
from hugin.errors import HuginError

from hugin import coordinator as c
from hugin.config import load_settings
from hugin.application import Controller, _DeliveryCommit
from hugin.windows.clipboard import ClipboardFailure

ROOT = Path(__file__).resolve().parents[2]


def controller_settings(owner, root=ROOT):
    """Each fake controller owns disposable preferences, never the installation's."""
    settings=load_settings(root)
    state=TemporaryDirectory(prefix='hugin-controller-test-')
    owner.addCleanup(state.cleanup)
    return replace(settings,paths={**settings.paths,'state':Path(state.name)})


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
    def start(self, job): self.calls.append('player'); self.job=job; self.samples=0
    def write(self, pcm, job, cancelled, *, started=None, progress=None):
        self.calls.append('audio')
        if cancelled():return False
        if started is not None:started()
        if progress is not None:progress(self.samples)
        self.samples+=len(pcm)//2
        return True
    def pause(self,job,paused):
        self.calls.append(('pause',job,paused));return getattr(self,'job',None)==job
    def drain(self, job, cancelled, *, progress=None):
        if progress is not None:progress(self.samples)
        return getattr(self,'job',None)==job and not cancelled()
    def stop(self): self.calls.append('reset')
    def close(self): pass


class Clipboard:
    def __init__(self): self.submissions = []; self.copies = []; self.cancel_at_commit = None
    def capture_native_target(self): return NS(target='target', status='native_target_captured')
    def capture_target(self, **kwargs): return NS(target='target', status='target_captured')
    def capture_selection(self, cancelled): return NS(text='Synthetischer Test.', status='captured')
    def deliver(self, text, target, still_current, *, authorize, commit):
        if not still_current():return NS(status='cancelled',submitted=False,copied=False)
        self.copies.append(text)
        if target is None:return NS(status='target_unverifiable',submitted=False,copied=True)
        submitted=[False]
        def send():
            if self.cancel_at_commit:self.cancel_at_commit()
            if still_current() and authorize('transaction'):
                self.submissions.append(text);submitted[0]=True
        commit('transaction',send)
        return NS(status='submitted' if submitted[0] else 'cancelled',submitted=submitted[0],copied=True)
    def copy(self, text): self.submissions.append(text); return NS(status='copied')
    def close(self): pass


class Pool:
    def __init__(self):
        self.workers = {}; self.starts = []; self.inference = []; self.inference_futures=[]
        self.alignments=[];self.alignment_futures=[]
    def start(self, engine):
        self.starts.append(engine)
        self.workers[engine] = NS(engine_instance='actual-' + engine, process=None,close=lambda:None)
        self.future = Future()
        return self.future
    def transcribe(self, pcm, request_id, generation):
        self.inference.append((request_id, generation)); return Future()
    def synthesize(self, text, voice, request_id, generation, language=None):
        self.inference.append((request_id, generation)); future=Future();self.inference_futures.append(future);return future
    def align(self,pcm,text,request_id,generation,language=None):
        self.alignments.append((pcm,text,request_id,generation))
        future=Future();self.alignment_futures.append(future);return future
    def cancel(self, *args): return True


class Immediate:
    def submit(self, fn, *args):
        future = Future()
        try: future.set_result(fn(*args))
        except Exception as error: future.set_exception(error)
        return future
    def shutdown(self, **kwargs): pass


def prepare_section(controller,pool,pump,pcm=b'\0\0',result=None):
    from hugin.word_timing import AlignmentResult
    synthesis=controller.core.snapshot().gpu_slot
    controller.handle(c.EngineAudio(synthesis,pcm));pump()
    pool.inference_futures[-1].set_result({'code':None,'cancelled':False});pump()
    if controller.core.snapshot().gpu_slot.action==c.Action.INITIALIZE:
        pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});pump()
    _,_,request,generation=pool.alignments[-1]
    controller.worker_event(dict(type='alignment',engine='stt',engine_instance='actual-stt',
        request_id=request,generation=generation,result=result or AlignmentResult('rejected_path',())))
    pump()
    pool.alignment_futures[-1].set_result({'code':None,'cancelled':False});pump()


class ApplicationContracts(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.pool = Pool()
        self.clipboard = Clipboard()
        self.controller = Controller(controller_settings(self), inputs=Inputs(),
            microphone=Microphone(self.calls), output=Output(self.calls),
            clipboard=self.clipboard, pool=self.pool, publish=lambda view: None,
            capture_executor=Immediate(), audio_executor=Immediate(), maintenance_executor=Immediate(),
            selection_executor=Immediate(),delivery_executor=Immediate())

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

    def test_recording_focus_changes_resolve_recovered_field_at_final_text(self):
        focused=['first field'];ready=[False];captures=[];destinations=[]
        self.clipboard.capture_native_target=lambda:NS(target=focused[0],status='native_target_captured')
        def capture(*,expected,cancelled):
            captures.append(expected)
            if expected!=focused[0]:return NS(target=None,status='target_changed')
            return NS(target=expected if ready[0] else None,
                      status='target_captured' if ready[0] else 'target_unverifiable')
        self.clipboard.capture_target=capture
        original=self.clipboard.deliver
        def deliver(text,target,*args,**kwargs):
            destinations.append(target)
            return original(text,target,*args,**kwargs)
        self.clipboard.deliver=deliver
        self.controller.command('dictation');self.pump()
        focused[0]='outside field'
        focused[0]='last chosen field'
        self.controller.command('dictation');self.pump()
        stop_phase=json.loads(self.controller.diagnostic())['input_checks']['capture_field']
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});self.pump()
        ready[0]=True
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='late field test'));self.pump()
        self.assertEqual(captures,['last chosen field'])
        self.assertEqual(self.clipboard.submissions,['late field test'])
        self.assertEqual(destinations,['last chosen field'])
        self.assertEqual(stop_phase,'not_run')
        self.assertEqual(json.loads(self.controller.diagnostic())['input_checks']['delivery'],'submitted')

    def test_changed_target_after_stop_is_copied_without_insertion(self):
        focused=['stop field'];captures=[]
        self.clipboard.capture_native_target=lambda:NS(target=focused[0],status='native_target_captured')
        def capture(*,expected,cancelled):
            captures.append(expected)
            return NS(target=expected if expected==focused[0] else None,
                      status='target_captured' if expected==focused[0] else 'target_changed')
        self.clipboard.capture_target=capture
        self.dictation_ready()
        focused[0]='different window'
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='retain after change'));self.pump()
        self.assertEqual(captures,['stop field'])
        self.assertEqual(self.clipboard.submissions,[])
        self.assertEqual(self.clipboard.copies,['retain after change'])
        checks=json.loads(self.controller.diagnostic())['input_checks']
        self.assertEqual((checks['capture_field'],checks['clipboard'],checks['delivery']),
                         ('target_changed','copied','not_attempted'))

    def test_cancelled_recognition_never_starts_late_field_probe(self):
        captures=[]
        self.clipboard.capture_target=lambda **kwargs:captures.append(kwargs)
        self.dictation_ready()
        request,generation=self.pool.inference[-1]
        self.controller.command('cancel');self.pump()
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='stale result'));self.pump()
        self.assertEqual(captures,[])
        self.assertEqual(self.clipboard.submissions,[])
        self.assertEqual(self.clipboard.copies,[])

    def test_same_native_window_binds_current_uia_field_at_delivery(self):
        from dataclasses import replace
        from test_windows_clipboard import FakeClipboard
        from hugin.windows.clipboard import ClipboardService, NativeClipboard, UiaTargetIdentity
        backend=FakeClipboard()
        base=replace(backend.target,control_class='Chrome_WidgetWin_1',
                     caret=None,selection=None,native_editable=False)
        first=UiaTargetIdentity((1,),(2,),(1,),(1,),base.pid,(0,0),0,0)
        last=UiaTargetIdentity((3,),(2,),(3,),(3,),base.pid,(4,4),0,0)
        focused=[first];captures=[];destinations=[]
        def probe(*args):
            captures.append(focused[0])
            return NS(status='target_captured',identity=focused[0])
        # Exercise the production native-basis comparison without Windows I/O.
        native=NativeClipboard.__new__(NativeClipboard)
        native.capture_native_target=lambda:base
        native._selection_probe=NS(capture_target=probe)
        backend.capture_native_target=lambda:base
        backend.capture_target=native.capture_target
        backend.target=replace(base,uia=first)
        original_commit=backend.commit_paste
        def commit(expected,target,*args,**kwargs):
            destinations.append(target)
            return original_commit(expected,target,*args,**kwargs)
        backend.commit_paste=commit
        service=ClipboardService(backend=backend)
        service.approve_verified_edits(.02)
        self.controller.clipboard=service
        self.dictation_ready()
        self.assertEqual(captures,[])
        focused[0]=last
        backend.target=replace(base,uia=last)
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='current cursor'));self.pump()
        self.assertEqual(captures,[last])
        self.assertEqual(destinations,[replace(base,uia=last)])
        self.assertEqual(backend.pastes,1)
        self.assertEqual(backend.data[13].decode('utf-16-le'),'current cursor\0')
        self.assertIsNone(self.controller.core.snapshot().error)

    def test_cancel_at_final_clipboard_seam_prevents_injection(self):
        self.dictation_ready()
        self.clipboard.cancel_at_commit = lambda: self.controller.command('cancel')
        request, generation = self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='private marker'))
        self.pump()
        self.assertEqual(self.clipboard.submissions, [])
        self.assertEqual(self.controller.core.snapshot().result.text, 'private marker')

    def assert_delivery_rejection(self, status, expected_code):
        self.clipboard.deliver = lambda *args, **kwargs: NS(
            status=status, submitted=False, copied=False)
        self.dictation_ready()
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic rejected dictation'))
        self.pump()
        self.assertEqual(self.controller.core.snapshot().error.code,expected_code)
        self.assertEqual(self.controller.view().text,'synthetic rejected dictation')
        self.assertEqual(self.clipboard.submissions,[])
        self.assertNotIn('synthetic rejected dictation',self.controller.diagnostic())

    def test_unapproved_delivery_does_not_claim_target_changed(self):
        self.assert_delivery_rejection('target_unverified','target_unverified')

    def test_unverifiable_delivery_does_not_claim_target_changed(self):
        self.assert_delivery_rejection('target_unverifiable','target_unverifiable')

    def test_timed_out_target_proof_does_not_claim_clipboard_unavailable(self):
        self.assert_delivery_rejection('target_probe_timeout','input_check_timeout')

    def test_failed_field_capture_preserves_reason_and_ram_result_without_delivery(self):
        for status,code in (('target_probe_timeout','input_check_timeout'),
                ('dependency_unavailable','input_check_unavailable'),
                ('target_unverifiable','target_unverifiable'),
                ('private arbitrary provider detail','input_check_failed')):
            with self.subTest(status=status):
                self.setUp()
                self.clipboard.capture_target=lambda **kwargs:NS(target=None,status=status)
                self.dictation_ready()
                request,generation=self.pool.inference[-1]
                self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
                    request_id=request,generation=generation,text='synthetic retained dictation'))
                self.pump()
                self.assertEqual(self.controller.core.snapshot().error.code,code)
                self.assertEqual(self.controller.view().text,'synthetic retained dictation')
                checks=json.loads(self.controller.diagnostic())['input_checks']
                self.assertEqual(checks['capture_field'],status if status!='private arbitrary provider detail' else 'unknown')
                self.assertEqual(checks['delivery'],'not_attempted')
                self.assertEqual(checks['clipboard'],'copied')
                self.assertEqual(self.clipboard.copies,['synthetic retained dictation'])
                self.assertEqual(self.clipboard.submissions,[])
                self.assertIn('Strg+V',self.controller.view().error)
                self.assertNotIn('private arbitrary provider detail',self.controller.diagnostic())

    def test_native_capture_failure_does_not_invent_a_field_probe(self):
        self.clipboard.capture_native_target=lambda:NS(target=None,status='target_changed')
        self.clipboard.capture_target=lambda **kwargs:self.fail('missing native basis reached UIA')
        self.dictation_ready()
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic retained dictation'))
        self.pump()
        self.assertEqual(self.controller.core.snapshot().error.code,'target_changed')
        self.assertEqual(json.loads(self.controller.diagnostic())['input_checks'],
            {'capture_native':'target_changed','capture_field':'not_attempted','clipboard':'copied','delivery':'not_attempted'})

    def test_field_probe_exception_does_not_discard_successful_audio(self):
        def fail(**kwargs):raise RuntimeError('private provider payload')
        self.clipboard.capture_target=fail
        self.dictation_ready()
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic retained dictation'))
        self.pump()
        self.assertEqual(self.controller.view().text,'synthetic retained dictation')
        self.assertEqual(self.controller.core.snapshot().error.code,'input_check_failed')
        self.assertEqual(json.loads(self.controller.diagnostic())['input_checks']['capture_field'],'target_probe_failed')
        self.assertNotIn('private provider payload',self.controller.diagnostic())

    def test_clipboard_rejection_does_not_claim_target_changed(self):
        self.assert_delivery_rejection('format_unsupported','clipboard_failed')

    def test_known_later_copy_suppresses_ctrl_v_hint_but_retains_publication_fact(self):
        self.dictation_ready()
        self.clipboard.deliver=lambda *a,**k:NS(status='clipboard_changed',copied=True,submitted=False)
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic retained text'))
        self.pump()
        self.assertEqual(self.controller.view().text,'synthetic retained text')
        self.assertNotIn('Strg+V',self.controller.view().error)
        checks=json.loads(self.controller.diagnostic())['input_checks']
        self.assertEqual((checks['clipboard'],checks['delivery']),('copied','clipboard_changed'))

    def test_cold_model_load_is_distinguished_from_transcription(self):
        self.controller.command('dictation');self.pump()
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.controller.view().status,'Whisper wird geladen')
        self.assertIn('Whisper: wird geladen',self.controller.view().components)

    def test_delivery_field_probe_keeps_microphone_stopped_and_owner_pumping(self):
        entered,release,pumped=threading.Event(),threading.Event(),threading.Event()
        waiting=[False]
        def capture(**kwargs):
            entered.set();release.wait(2)
            return NS(target='target',status='target_captured')
        self.clipboard.capture_native_target=lambda:NS(target='target',status='native_target_captured')
        self.clipboard.capture_target=capture
        self.controller.delivery_executor=ThreadPoolExecutor(1)
        self.controller.publish=lambda view:pumped.set() if waiting[0] else None
        owner=threading.Thread(target=self.controller.run,args=(lambda:None,))
        owner.start()
        try:
            self.controller.command('dictation')
            deadline=time.monotonic()+1
            while not self.controller.microphone.owned and time.monotonic()<deadline:time.sleep(.005)
            self.controller.command('dictation')
            deadline=time.monotonic()+1
            while not self.pool.starts and time.monotonic()<deadline:time.sleep(.005)
            self.assertFalse(entered.is_set(),'field probe must wait for final text')
            self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'})
            deadline=time.monotonic()+1
            while not self.pool.inference and time.monotonic()<deadline:time.sleep(.005)
            request,generation=self.pool.inference[-1]
            self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
                request_id=request,generation=generation,text='delayed field probe'))
            self.assertTrue(entered.wait(1))
            self.assertFalse(self.controller.microphone.owned,'target probe must not extend the recording')
            waiting[0]=True;self.controller.command('clear')
            self.assertTrue(pumped.wait(.5),'provider waits must not block the serial owner')
        finally:
            release.set();self.controller.command('quit');owner.join(3)
            self.assertFalse(owner.is_alive())

    def test_slow_delivery_keeps_owner_pumping_and_quit_waits_for_its_cleanup(self):
        entered,release,pumped=threading.Event(),threading.Event(),threading.Event()
        waiting=[False]
        def deliver(*args,**kwargs):
            entered.set();release.wait(2)
            return NS(status='cancelled',submitted=False,copied=False)
        self.clipboard.deliver=deliver
        self.dictation_ready()
        self.controller.delivery_executor=ThreadPoolExecutor(1)
        self.controller.publish=lambda view:pumped.set() if waiting[0] else None
        owner=threading.Thread(target=self.controller.run,args=(lambda:None,))
        owner.start()
        try:
            request,generation=self.pool.inference[-1]
            self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
                request_id=request,generation=generation,text='synthetic delivery'))
            self.assertTrue(entered.wait(1))
            waiting[0]=True;self.controller.command('clear')
            self.assertTrue(pumped.wait(.5),'delivery waits must not block the serial owner')
            self.controller.command('quit');time.sleep(.05)
            self.assertTrue(owner.is_alive(),'live delivery owns its cleanup barrier')
        finally:
            release.set();self.controller.command('quit');owner.join(3)
            self.controller.delivery_executor.shutdown(wait=True)
            self.assertFalse(owner.is_alive())

    def test_background_delivery_commits_on_owner_and_finishes_on_worker(self):
        self.dictation_ready()
        self.controller.delivery_executor=ThreadPoolExecutor(1)
        threads=[]
        def deliver(text,target,current,*,authorize,commit):
            def send():
                threads.append(('commit',threading.get_ident()))
                if current() and authorize('transaction'):self.clipboard.submissions.append(text)
            commit('transaction',send)
            threads.append(('finish',threading.get_ident()))
            return NS(status='submitted',submitted=True,copied=True)
        self.clipboard.deliver=deliver
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic asynchronous delivery'))
        try:
            deadline=time.monotonic()+1
            while (not threads or self.controller._delivery_tasks or self.controller.core.snapshot().state==c.State.DELIVERING) and time.monotonic()<deadline:
                self.controller.pump_once(.01)
            self.assertEqual(self.clipboard.submissions,['synthetic asynchronous delivery'])
            self.assertEqual(threads[0],('commit',threading.get_ident()))
            self.assertEqual(threads[1][0],'finish')
            self.assertNotEqual(threads[1][1],threading.get_ident())
        finally:
            self.controller.command('quit');self.pump()
            self.controller.delivery_executor.shutdown(wait=True)

    def test_expired_commit_never_runs_and_every_claimed_failure_is_acknowledged(self):
        self.dictation_ready()
        job=self.controller.core.snapshot().job
        calls=[]
        expired=Future();expired.cancel()
        self.controller.handle(_DeliveryCommit(job,'expired',lambda:calls.append('late'),expired))
        self.assertEqual(calls,[])
        failures=(ClipboardFailure('input_partial',submitted=True,owned_sequence=123),KeyboardInterrupt())
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                acknowledgement=Future()
                def send():raise failure
                self.controller.handle(_DeliveryCommit(job,'failed',send,acknowledgement))
                self.assertTrue(acknowledgement.done())
                self.assertIs(acknowledgement.exception(),failure)

    def test_quit_with_full_queue_cancels_pending_native_commit_without_losing_finish(self):
        self.dictation_ready()
        self.controller.delivery_executor=ThreadPoolExecutor(1)
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic cancelled delivery'))
        self.controller.pump_once()
        try:
            deadline=time.monotonic()+1
            while time.monotonic()<deadline:
                with self.controller._lock:
                    pending=any(isinstance(item[2],_DeliveryCommit) for item in self.controller._completions.values())
                if pending:break
                time.sleep(.005)
            self.assertTrue(pending)
            for _ in range(64):self.controller.command('clear')
            self.controller.command('quit')
            deadline=time.monotonic()+1
            while not self.controller.shutdown_ready() and time.monotonic()<deadline:self.controller.pump_once(.01)
            self.assertEqual(self.clipboard.submissions,[])
            self.assertTrue(self.controller.shutdown_ready())
        finally:self.controller.delivery_executor.shutdown(wait=True)

    def test_failed_delivery_submit_revokes_even_an_already_queued_callable(self):
        class QueuedThenFailed:
            def submit(self,fn):
                self.queued=fn
                raise RuntimeError('synthetic thread start failure')
        self.dictation_ready()
        executor=QueuedThenFailed();self.controller.delivery_executor=executor
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic failed submit'))
        try:self.pump()
        except RuntimeError:pass  # The old path strands the closing delivery.
        executor.queued()
        self.controller.command('quit');self.pump()
        self.assertEqual(self.clipboard.submissions,[])
        self.assertTrue(self.controller.shutdown_ready())

    def test_submit_failure_after_execution_claim_retains_delivery_until_real_finish(self):
        entered,release=threading.Event(),threading.Event()
        class RunningThenFailed:
            def submit(self,fn):
                self.thread=threading.Thread(target=fn);self.thread.start()
                if not entered.wait(1):raise AssertionError('delivery did not start')
                raise RuntimeError('synthetic late submit failure')
        def deliver(*args,**kwargs):
            entered.set();release.wait(2)
            return NS(status='cancelled',submitted=False,copied=False)
        self.dictation_ready()
        self.clipboard.deliver=deliver
        executor=RunningThenFailed();self.controller.delivery_executor=executor
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='synthetic claimed delivery'))
        try:
            self.pump();self.controller.command('quit');self.pump()
            self.assertFalse(self.controller.shutdown_ready())
            self.assertEqual(len(self.controller._delivery_tasks),1)
        finally:
            release.set();executor.thread.join(2);self.pump()
        self.assertEqual(self.clipboard.submissions,[])
        self.assertTrue(self.controller.shutdown_ready())

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

    def test_cold_initialization_survives_old_deadline_but_remains_bounded(self):
        self.assertEqual(self.controller.settings.limits['ready_seconds'],120)
        self.assertEqual(self.controller.settings.limits['cancel_seconds'],2)
        self.assertEqual(self.controller.settings.limits['exit_seconds'],5)
        closed=[]
        started=time.monotonic()
        with patch('hugin.application.time.monotonic',return_value=started):
            self.controller.command('read');self.pump()
        worker=self.pool.workers['tts']
        worker.close=lambda:closed.append(True)
        with patch('hugin.application.time.monotonic',return_value=started+61):
            self.controller.tick();self.pump()
        self.assertFalse(closed)
        self.assertEqual(self.controller.core.snapshot().gpu_slot.action,c.Action.INITIALIZE)
        with patch('hugin.application.time.monotonic',return_value=started+120):
            self.controller.tick();self.pump()
        self.assertEqual(closed,[True])
        self.assertIsNone(self.controller.core.snapshot().gpu_slot)

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
        self.assertIsNone(json.loads(self.controller.diagnostic())['error_code'])

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

    def test_full_user_queue_cannot_drop_quit(self):
        for _ in range(64):self.controller.command('clear')
        self.controller.command('quit');self.pump()
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
        prepare_section(self.controller,self.pool,self.pump)
        self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)
        self.controller.command('read');self.pump()
        # A valid empty stream follows the spoken stream in the same worker.
        self.pool.inference_futures[-1].set_result({'code':None,'cancelled':False});self.pump()
        self.assertEqual(self.controller.core.snapshot().state,c.State.IDLE)

    def test_marking_uses_native_samples_with_gaps_and_no_duplicate_word_updates(self):
        from hugin.word_timing import AlignmentResult,WordTiming
        self.clipboard.capture_selection=lambda cancelled:NS(text='Hallo Welt.',status='captured')
        published=[]
        self.controller.publish=lambda view:published.append(view.reading_word)
        self.controller.command('read');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-tts','device':'cuda'});self.pump()
        progress=[]
        def write(pcm,job,cancelled,*,started=None,**kwargs):
            if started:started()
            progress.append(kwargs['progress']);return True
        self.controller.output.write=write
        self.controller.output.drain=lambda *args,**kwargs:False
        result=AlignmentResult('aligned',(WordTiming(0,5,100,5000),WordTiming(6,11,6000,12000)))
        prepare_section(self.controller,self.pool,self.pump,b'\0\0'*12000,result)
        observe=progress[0]
        observe(99);self.pump();self.assertIsNone(self.controller.view().reading_word)
        observe(100);self.pump();self.assertEqual(self.controller.view().reading_word,(0,5))
        count=len(published)
        observe(3000);self.pump();self.assertEqual(len(published),count)
        job=self.controller.core.snapshot().job
        self.controller.command('read_pause',job.request_id);self.pump()
        observe(6000);self.pump();self.assertEqual(self.controller.view().reading_word,(0,5))
        self.controller.command('read_pause',job.request_id);self.pump()
        observe(6000);self.pump();self.assertEqual(self.controller.view().reading_word,(6,11))
        observe(5000);self.pump();self.assertIsNone(self.controller.view().reading_word)
        observe(6000);self.pump();self.assertEqual(self.controller.view().reading_word,(6,11))
        observe(None);self.pump();self.assertEqual(self.controller.view().reading_marking,'unavailable_position')
        self.controller.command('cancel');self.pump()
        observe(7000);self.pump();self.assertEqual(self.controller.view().reading_text,'')

    def test_reading_view_follows_output_and_stale_controls_cannot_stop_new_reading(self):
        text='Synthetischer Mitlesetext. '*35
        self.clipboard.capture_selection=lambda cancelled:NS(text=text,status='captured')
        self.controller.command('read');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-tts','device':'cuda'});self.pump()
        job=self.controller.core.snapshot().job
        self.assertEqual(self.controller.view().reading_job,job.request_id)
        self.assertEqual(self.controller.view().reading_text,'')
        held=[]
        def delayed_write(pcm,identity,cancelled,*,started=None,progress=None):
            held.append(started);return not cancelled()
        self.controller.output.write=delayed_write
        self.controller.output.drain=lambda *args,**kwargs:False
        prepare_section(self.controller,self.pool,self.pump)
        self.assertEqual(self.controller.view().reading_index,0)
        held.pop()();self.pump()
        self.assertEqual(self.controller.view().reading_index,1)
        self.assertNotIn('Synthetischer Mitlesetext',self.controller.diagnostic())
        self.controller.command('read_pause',job.request_id);self.pump()
        self.assertTrue(self.controller.view().reading_paused)
        self.assertIn(('pause',job.request_id,True),self.calls)
        self.controller.handle(c.AudioFinished(job,1));self.pump()
        self.assertEqual(self.controller.core.snapshot().gpu_slot.action,c.Action.SYNTHESIZE)
        self.controller.command('read_pause',job.request_id);self.pump()
        second=self.controller.core.snapshot().gpu_slot
        self.assertIsNotNone(second)
        self.assertEqual(self.controller.view().reading_index,1)
        prepare_section(self.controller,self.pool,self.pump)
        self.assertEqual(self.controller.view().reading_index,1)
        held.pop()();self.pump()
        self.assertEqual(self.controller.view().reading_index,2)
        self.controller.command('read_stop',job.request_id);self.pump()
        self.assertEqual(self.controller.view().reading_text,'')
        self.pool.inference_futures[-1].set_result({'code':None,'cancelled':True});self.pump()
        self.controller.command('read');self.pump()
        new=self.controller.core.snapshot().job
        self.assertNotEqual(new,job)
        resets=self.calls.count('reset')
        self.controller.command('read_pause',job.request_id)
        self.controller.command('read_stop',job.request_id);self.pump()
        self.assertEqual(self.controller.core.snapshot().job,new)
        self.assertEqual(self.calls.count('reset'),resets)
        self.assertFalse(self.controller.view().reading_paused)

    def test_paused_reading_dictation_preempts(self):
        self.controller.command('read');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-tts','device':'cuda'});self.pump()
        op=self.controller.core.snapshot().gpu_slot;job=op.job
        self.controller.output.drain=lambda *args,**kwargs:False
        prepare_section(self.controller,self.pool,self.pump)
        self.controller.command('read_pause',job.request_id);self.pump()
        self.controller.command('dictation');self.pump()
        self.assertEqual(self.controller.core.snapshot().job.kind,c.JobKind.DICTATION)
        self.assertEqual(self.controller.view().reading_job,'')
        self.assertLess(self.calls.index('reset'),self.calls.index('microphone'))

    def test_pause_failure_cancels_and_is_not_presented_as_paused(self):
        self.controller.command('read');self.pump()
        self.pool.future.set_result({'engine_instance':'actual-tts','device':'cuda'});self.pump()
        op=self.controller.core.snapshot().gpu_slot
        self.controller.output.drain=lambda *args,**kwargs:False
        prepare_section(self.controller,self.pool,self.pump)
        self.controller.output.pause=lambda *args:False
        self.controller.command('read_pause',op.job.request_id);self.pump()
        self.assertIsNone(self.controller.core.snapshot().job)
        self.assertEqual(json.loads(self.controller.diagnostic())['error_code'],'audio_failed')
        self.assertFalse(self.controller.view().reading_paused)
        self.assertEqual(self.controller.view().reading_text,'')

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
