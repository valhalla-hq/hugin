"""One serial application owner, bounded callbacks and explicit native adapters.

Never log events/effects/futures: their payloads are private user content.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime,timezone
import itertools
import json
import math
import queue
import threading
import time
import uuid

from . import coordinator as c
from . import __version__
from .errors import HuginError, MESSAGES
from .config import read_json_object
from .diagnostics import observed_versions
from .ui import View
from .windows.clipboard import ClipboardFailure


@dataclass(frozen=True)
class _Started:
    operation: c.Operation
    ready: dict | None
    error: HuginError | None = None


@dataclass(frozen=True)
class _Closed:
    engine: c.Engine
    incarnation: str
    error: HuginError | None = None


@dataclass(frozen=True)
class _Failure:
    error: HuginError


@dataclass(frozen=True)
class _CueFailure:
    error: HuginError


@dataclass(frozen=True)
class _CompletionCue:
    job: c.Job
    token: threading.Event


@dataclass(frozen=True)
class _CompletionCueFinished:
    owner: _CompletionCue


@dataclass(frozen=True)
class _Command:
    kind: str
    value: str | None = None


@dataclass(frozen=True)
class _Binding:
    operation: c.Operation
    actual: str
    request: str
    generation: int


@dataclass(frozen=True)
class _DeliveryCommit:
    job: c.Job
    transaction: object
    send: Callable[[],None]
    acknowledgement: Future


@dataclass(frozen=True)
class _CapturedTarget:
    """One parsed capture outcome, passed opaquely through the reducer."""
    status: str
    target: object = None


@dataclass(frozen=True)
class _PanelInterruption:
    """An already accepted cancellation must finish for this exact job."""
    job: c.Job
    start_dictation: bool = False


_INPUT_STATUSES=frozenset(('not_run','not_attempted','native_target_captured',
    'target_captured','target_changed','target_unverifiable','target_unverified',
    'target_probe_timeout','target_probe_failed','target_probe_busy','target_cleanup_pending',
    'target_cleanup_failed','dependency_unavailable','unsupported','cancelled','submitted',
    'clipboard_busy','clipboard_changed','clipboard_failed','clipboard_cleanup_failed',
    'clipboard_recovery_pending','clipboard_restore_failed','clipboard_write_failed',
    'format_delayed','format_unsupported','snapshot_limit','modifiers_active',
    'modifier_release_failed','input_partial','commit_rejected','commit_timeout',
    'text_invalid','text_limit','unknown'))


def _input_error(status,phase):
    if status in ('target_changed','target_unverifiable','target_unverified'):code=status
    elif status in ('target_probe_timeout','commit_timeout'):code='input_check_timeout'
    elif status in ('dependency_unavailable','unsupported'):code='input_check_unavailable'
    elif status in ('target_probe_failed','target_probe_busy','target_cleanup_pending',
            'target_cleanup_failed','unknown'):code='input_check_failed'
    else:code='clipboard_failed'
    return HuginError(code,phase)


def _safe_error(error, phase):
    return HuginError(error.code if isinstance(error,HuginError) else 'worker_failed',phase)


class Controller:
    """Construct and pump on one owner thread; callbacks call command/worker_event."""
    def __init__(self, settings, *, inputs, microphone, output, clipboard, pool,
                 publish, capture_executor=None, audio_executor=None, maintenance_executor=None,
                 selection_executor=None,delivery_executor=None,signals=None,cues=None):
        self.settings = settings
        self.inputs,self.microphone,self.output = inputs,microphone,output
        self.clipboard,self.pool,self.publish = clipboard,pool,publish
        self.signals = signals
        self.cues = cues
        self.run_id = uuid.uuid4()
        self.core = c.Coordinator(instance_id=str(self.run_id),now=time.monotonic(),
            stt_idle_unload_seconds=settings.stt['idle_unload_seconds'],
            default_voice=self._voice(),limits=c.Limits(**{key:settings.limits[key] for key in
            ('capture_bytes','transcript_bytes','selection_bytes','frame_bytes','result_ttl_seconds')}))
        self.capture_executor = capture_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-capture')
        self.audio_executor = audio_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-audio')
        self.maintenance_executor = maintenance_executor or ThreadPoolExecutor(2,thread_name_prefix='hugin-cleanup')
        self.selection_executor = selection_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-selection')
        self.delivery_executor = delivery_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-delivery')
        self._owner_ident = None
        self._events = queue.PriorityQueue(maxsize=64)
        self._counter = itertools.count()
        self._lock = threading.RLock()
        self._tokens = {}
        self._bindings = {}
        self._incarnations = {}
        self._deadlines = {}
        self._closing = set()
        self._cleanup_failed = set()
        self._capture_tasks = set()
        self._selection_tasks = set()
        self._delivery_tasks = set()
        self._completions = {}
        self._queued_head = None
        self._audio_job = None
        self._audio_section = 0
        self._snapshot = self.core.snapshot()
        self._runtime_error = None
        self._overflow = threading.Event()
        self._stop = False
        self._closed = False
        self._last_input = None
        self._last_input_utc = None
        self._engine_versions = observed_versions(settings.root)
        self._devices = {}
        self._closed_io = set()
        self._io_cleanup_failed = set()
        self._input_checks = dict(capture_native='not_run',capture_field='not_run',delivery='not_run')
        self._completion_cue: _CompletionCue | None = None
        self._completion_id=0
        self._completion_until=0.0
        self._visual_epoch=0
        self._delivery_visual: tuple[c.Job,int] | None = None

    def _input_status(self,job,phase,value):
        """Normalize once at the adapter boundary; keep no raw provider data."""
        status=value if type(value) is str and len(value)<=64 and value in _INPUT_STATUSES else 'unknown'
        with self._lock:
            if self._snapshot.job==job:self._input_checks[phase]=status
        return status

    def _capture_target_outcome(self,job,phase,action):
        """Field failures never reinterpret an already valid microphone capture."""
        try:
            result=action();value=getattr(result,'status',None);target=getattr(result,'target',None)
            if type(value) is str and value in ('native_target_captured','target_captured') and target is None:
                value='target_probe_failed'
        except Exception:
            value,target='target_probe_failed',None
        status=self._input_status(job,phase,value)
        return _CapturedTarget(status,target if status in ('native_target_captured','target_captured') else None)

    def _voice(self):
        path = self.settings.paths['state']/'preferences.json'
        if not path.exists(): return self.settings.default_voice
        try:
            data = read_json_object(path,1024)
            if set(data) != {'schema_version','voice'} or type(data['schema_version']) is not int or data['schema_version'] != 1 or data['voice'] not in ('freya','tyr'):
                raise ValueError
            return data['voice']
        except (OSError,ValueError,TypeError):
            raise HuginError('config_invalid','preferences') from None

    def _token(self, job):
        with self._lock:
            return self._tokens.setdefault(job,threading.Event())

    def _post(self, event, *, priority=1, audio_ack=None):
        # Owner-keyed completion lane: one GPU operation (at most three
        # completion kinds), two process owners and one capture lifecycle.
        # User-toggle saturation cannot discard their ownership evidence.
        key = None
        if isinstance(event,(_Started,c.EngineFault,c.EngineTerminal)):
            key = (type(event),event.operation)
        elif isinstance(event,_Closed): key = (type(event),event.engine,event.incarnation)
        elif isinstance(event,c.AudioReset):
            # Failed attempts and later confirmed retries are distinct facts.
            key = (type(event),event.job,event.success)
        elif isinstance(event,_DeliveryCommit):
            key=(type(event),event.job,event.acknowledgement)
        elif isinstance(event,(c.RecordingStarted,c.RecordingStopped,c.DeliveryFinished)):
            key = (type(event),event.job)
        elif isinstance(event,_CueFailure):key=(type(event),'capture_cue')
        elif isinstance(event,_CompletionCueFinished):key=(type(event),event.owner.job)
        elif isinstance(event,_Command) and event.kind == 'quit':
            key = (type(event),'quit')
        if key is not None:
            with self._lock:
                if key not in self._completions:
                    if len(self._completions)>=16:
                        self._overflow.set()
                        raise HuginError('resource_limit','completion_ownership')
                    self._completions[key] = (priority,next(self._counter),event,audio_ack)
            return True
        try:
            self._events.put_nowait((priority,next(self._counter),event,audio_ack))
            return True
        except queue.Full:
            if audio_ack and not audio_ack.done(): audio_ack.set_result(False)
            self._overflow.set()
            return False

    def command(self, kind, value=None):
        """Prompt invalidation before clipboard waits; no model work on input threads."""
        queued_event=_Command(kind,value)
        with self._lock:
            if kind in ('panel_dictation','panel_read'):
                if not self._panel_current(kind,value,self._snapshot):return
                action=self._panel_controls(self._snapshot)[0 if kind=='panel_dictation' else 1]
                preempt=(kind=='panel_dictation' and self._snapshot.job is not None
                    and self._snapshot.job.kind==c.JobKind.READING)
                if self._snapshot.job is not None and (action in ('cancel','stop') or preempt):
                    queued_event=_PanelInterruption(self._snapshot.job,preempt)
                kind='dictation' if kind=='panel_dictation' else 'read'
            if kind in ('dictation','read','cancel','copy','clear','voice','quit',
                    'system_pause','system_resume','devices_changed'):
                self._clear_completion_visual()
            job = self._snapshot.job
            cue=self._invalidate_completion_cue(kind)
            starting_stop = kind == 'dictation' and job is not None and self._snapshot.state == c.State.STARTING
            invalidates = starting_stop or kind in ('cancel','quit','system_pause','system_resume','devices_changed') or (kind == 'read_stop' and job is not None and value == job.request_id and job.kind == c.JobKind.READING) or (job is not None and job.kind == c.JobKind.READING
                and (kind in ('dictation','read') or kind == 'voice' and value != self._snapshot.voice))
            if invalidates and job:
                self._token(job).set()
            if kind in ('dictation','read','cancel'):
                self._last_input = time.monotonic()
                self._last_input_utc = datetime.now(timezone.utc).isoformat(timespec='seconds')
        if invalidates:
            try: self.output.stop()
            except HuginError as error: self._post(_Failure(error),priority=0)
            if self.cues is not None:
                try:self.cues.stop()
                except HuginError as error:self._post(_CueFailure(error),priority=0)
        elif cue is not None:
            try:self.cues.stop(cue.job)
            except HuginError as error:self._post(_CueFailure(error),priority=0)
        self._post(queued_event,priority=-1 if kind == 'quit' else 0)

    @staticmethod
    def _panel_controls(snap):
        dictation={c.State.IDLE:'start',c.State.ERROR:'start',
            c.State.STARTING:'cancel',c.State.RECORDING:'finish',
            c.State.TTS_PREPARING:'start',c.State.TTS_PLAYING:'start'}.get(snap.state,'')
        reading={c.State.IDLE:'start',c.State.ERROR:'start',
            c.State.TTS_PREPARING:'stop',c.State.TTS_PLAYING:'stop'}.get(snap.state,'')
        return dictation,reading

    def _panel_current(self,kind,token,snap):
        control=self._panel_controls(snap)[0 if kind=='panel_dictation' else 1]
        return bool(control and token==(snap.generation,snap.state.value))

    def _clear_completion_visual(self):
        with self._lock:
            self._visual_epoch+=1
            self._completion_until=0.0

    def _accept_completion_visual(self,job,token):
        with self._lock:
            # Bind presentation eligibility when delivery starts. Input can
            # invalidate it even before its queued finish handler begins.
            if token.is_set() or self._delivery_visual!=(job,self._visual_epoch):return
            self._completion_id+=1
            self._completion_until=time.monotonic()+1.2

    def _invalidate_completion_cue(self,kind):
        if kind not in ('dictation','read','cancel','quit','system_pause','system_resume','devices_changed'):
            return None
        with self._lock:
            cue=self._completion_cue
            if cue is None or cue.token.is_set():return None
            cue.token.set()
            return cue

    def worker_event(self, event):
        """WorkerClient owns protocol parsing; map exact incarnations and requests."""
        with self._lock:
            binding = self._bindings.get(event.get('engine'))
        if binding is None or binding.operation.action == c.Action.INITIALIZE:
            return
        if (event.get('engine_instance'),event.get('request_id'),event.get('generation')) != (
                binding.actual,binding.request,binding.generation):
            return
        operation = binding.operation
        kind = event.get('type')
        if kind == 'result':
            self._post(c.EngineResult(operation,event['text']))
        elif kind == 'fault':
            self._post(c.EngineFault(operation,HuginError(event['code'],'engine')))
        elif kind == 'audio':
            token = self._token(operation.job)
            if token.is_set(): return
            acknowledgement = Future()
            if self._post(c.EngineAudio(operation,event['pcm']),audio_ack=acknowledgement):
                while not acknowledgement.done() and not token.wait(.025): pass
        # ready/terminal publication is normalized by each operation's future.

    def pump_once(self, timeout=0):
        if self._overflow.is_set():
            self._overflow.clear()
            self._runtime_error = HuginError('input_failed','event_capacity')
            self.handle(c.Cancel())
        if self._queued_head is None:
            try: self._queued_head = self._events.get_nowait()
            except queue.Empty:
                with self._lock: has_completion = bool(self._completions)
                if not has_completion:
                    try: self._queued_head = self._events.get(timeout=timeout)
                    except queue.Empty: pass
        with self._lock:
            key = min(self._completions,key=lambda key:self._completions[key][:2],default=None)
            completed = self._completions.get(key)
            if completed and (self._queued_head is None or completed[:2] < self._queued_head[:2]):
                _,_,event,ack = self._completions.pop(key)
            elif self._queued_head is not None:
                _,_,event,ack = self._queued_head
                self._queued_head = None
            else: return False
        self.handle(c.Tick(time.monotonic()))
        self.handle(event,audio_ack=ack)
        return True

    def handle(self, event, *, audio_ack=None):
        if self._owner_ident is None:self._owner_ident=threading.get_ident()
        if isinstance(event,_DeliveryCommit):
            acknowledgement=event.acknowledgement
            if not acknowledgement.set_running_or_notify_cancel():return
            try:
                if self._snapshot.job != event.job or self._token(event.job).is_set():
                    raise ClipboardFailure('cancelled')
                event.send()
            except BaseException as failure:acknowledgement.set_exception(failure)
            else:acknowledgement.set_result(None)
            return
        if isinstance(event,_CompletionCueFinished):
            with self._lock:
                if self._completion_cue is not event.owner:return
                self._completion_cue=None
            try:self.inputs.set_cancel_active(self._snapshot.escape_reserved)
            except HuginError as error:self.handle(_Failure(error))
            self._publish();return
        if isinstance(event,_PanelInterruption):
            if self.core.snapshot().job!=event.job:return
            event=c.DictationToggle() if event.start_dictation else c.Cancel()
        if isinstance(event,_Command):
            if event.kind in ('panel_dictation','panel_read'):
                if not self._panel_current(event.kind,event.value,self.core.snapshot()):return
                event=_Command('dictation' if event.kind=='panel_dictation' else 'read')
            mapping = {'dictation':c.DictationToggle,'read':c.ReadToggle,'cancel':c.Cancel,
                'copy':c.CopyResult,'clear':c.DeleteResult,'quit':c.Shutdown,
                'system_pause':c.Cancel,'system_resume':c.Cancel,'devices_changed':c.Cancel}
            if event.kind == 'voice': event = c.VoiceSelected(event.value)
            elif event.kind == 'read_pause':event = c.PauseReading(event.value)
            elif event.kind == 'read_stop':
                job=self.core.snapshot().job
                if job is None or job.kind != c.JobKind.READING or event.value != job.request_id:return
                event=c.Cancel()
            elif event.kind in ('system_pause','system_resume','devices_changed'):
                self.handle(c.Cancel())
                # Cancel while the registry still owns each worker; only then
                # close their CUDA contexts and wait for observed family exit.
                for engine,(incarnation,_) in tuple(self._incarnations.items()):
                    self._close_engine(c.Engine(engine),incarnation)
                return
            elif event.kind == 'diagnose':
                result = self.clipboard.copy(self.diagnostic())
                if result.status != 'copied': self._runtime_error = HuginError('clipboard_failed','diagnostic')
                self._publish(); return
            elif event.kind in mapping:
                if event.kind == 'quit':
                    self._stop = True
                    self._io_cleanup_failed.clear()
                    for key in tuple(self._cleanup_failed): self._close_engine(*key,retry=True)
                    self.handle(c.RetryCleanup())
                if event.kind=='dictation' and self.core.snapshot().state==c.State.STARTING:
                    event=c.Cancel()  # No armed recording exists to transcribe yet.
                else:event = mapping[event.kind]()
            else: return
        if isinstance(event,_Started):
            if self.core.snapshot().gpu_slot != event.operation:
                return
            self._deadlines.pop((event.operation.engine,event.operation.engine_instance),None)
            if event.error:
                self.handle(c.EngineFault(event.operation,event.error))
                self._close_engine(event.operation.engine,event.operation.engine_instance)
            else:
                self._devices[event.operation.engine.value] = event.ready['device']
                self.handle(c.EngineReady(event.operation))
                self.handle(c.EngineTerminal(event.operation))
            return
        if isinstance(event,_Closed):
            self._closing.discard((event.engine,event.incarnation))
            if event.error:
                self._runtime_error = event.error
                self._cleanup_failed.add((event.engine,event.incarnation))
            else:
                self._cleanup_failed.discard((event.engine,event.incarnation))
                self._deadlines.pop((event.engine,event.incarnation),None)
                current = self._incarnations.get(event.engine.value)
                if current is None or current[0] == event.incarnation:
                    self._incarnations.pop(event.engine.value,None)
                    with self._lock: self._bindings.pop(event.engine.value,None)
                self.handle(c.EngineExited(event.engine,event.incarnation))
            self._publish(); return
        if isinstance(event,_Failure):
            self._runtime_error = event.error
            self.handle(c.Cancel()); return
        if isinstance(event,_CueFailure):
            self._runtime_error=event.error
            self._clear_completion_visual()
            self._publish();return  # Cue failure preserves captured speech and delivered text.
        if isinstance(event,(c.DictationToggle,c.ReadToggle,c.Cancel,c.Shutdown,
                c.CopyResult,c.DeleteResult,c.VoiceSelected)):
            self._clear_completion_visual()
        if isinstance(event,(c.DictationToggle,c.ReadToggle,c.Cancel,c.Shutdown)):
            # Recheck after queued input races registration; domain-level
            # failures also cancel the cue after the dictation job has ended.
            cue=self._invalidate_completion_cue('cancel')
            if cue is not None:
                try:self.cues.stop(cue.job)
                except HuginError as error:self._post(_CueFailure(error),priority=0)
        completed_job=(event.job if isinstance(event,c.DeliveryFinished) and event.error is None
            and self._snapshot.job==event.job and self._snapshot.state==c.State.DELIVERING else None)
        completion_token=self._token(completed_job) if completed_job is not None else None
        effects = self.core.dispatch(event)
        with self._lock:
            self._snapshot = self.core.snapshot()
            if self._snapshot.job: self._token(self._snapshot.job)
        completed=completed_job is not None and self._snapshot.job!=completed_job
        if completed:self._accept_completion_visual(completed_job,completion_token)
        if isinstance(event,c.DeliveryFinished):
            with self._lock:
                if self._delivery_visual is not None and self._delivery_visual[0]==event.job:
                    self._delivery_visual=None
        cue=self._reserve_completion_cue(completed_job,completion_token) if completed else None
        accepted_audio = False
        for effect in effects:
            if isinstance(effect,c.SetEscape):
                try:self.inputs.set_cancel_active(effect.enabled or self._completion_cue is not None)
                except HuginError as error:
                    self._runtime_error = error
                    job = self._snapshot.job
                    self.handle(c.Cancel())
                    if effect.enabled:
                        # No start effect has run. Acknowledge unused capture ownership.
                        if job and job.kind == c.JobKind.DICTATION and not self.microphone.owned:
                            self.handle(c.RecordingStopped(job))
                        if audio_ack and not audio_ack.done(): audio_ack.set_result(False)
                        return
            else:
                accepted_audio |= self._effect(effect,audio_ack)
        if cue is not None:self._submit_completion_cue(cue)
        if audio_ack and not accepted_audio and not audio_ack.done(): audio_ack.set_result(False)
        self._publish()

    def _reserve_completion_cue(self,job,token):
        if self.cues is None or token.is_set():return
        owner=_CompletionCue(job,token)
        with self._lock:
            if self._completion_cue is not None:
                self._post(_CueFailure(HuginError('audio_failed','completion_cue_owner')))
                return
            self._completion_cue=owner
        return owner

    def _submit_completion_cue(self,owner):
        # Reserve before finish effects retain Escape, submit only after those
        # effects succeed or invalidate the reservation. Even an eager executor
        # then observes registration failure before it can emit any audio.
        job,token=owner.job,owner.token
        ticket=Future()
        with self._lock:self._capture_tasks.add(ticket)
        def finished(done):
            with self._lock:self._capture_tasks.discard(done)
        ticket.add_done_callback(finished)
        def release():
            # Input registration belongs to the controllerowner, never this
            # audio worker. Keep the cue reservation until that owner ACKs it.
            self._post(_CompletionCueFinished(owner),priority=0)
        def play():
            # Retain our own ticket before submit: an executor may enqueue or
            # start work and then throw. A cancelled queued claim stays inert.
            if not ticket.set_running_or_notify_cancel():return
            try:
                if not token.is_set():
                    if not self.cues.play('complete',job,token.is_set) and not token.is_set():
                        raise HuginError('audio_failed','completion_cue')
            except Exception:
                self._post(_CueFailure(HuginError('audio_failed','completion_cue')))
            finally:
                try:release()
                finally:ticket.set_result(None)
        try:self.capture_executor.submit(play)
        except BaseException:
            token.set()
            if ticket.cancel():release()
            else:
                try:self.cues.stop(job)
                except HuginError as error:self._post(_CueFailure(error))
            self._post(_CueFailure(HuginError('audio_failed','completion_cue_start')))

    def _effect(self, effect, audio_ack=None):
        if isinstance(effect,c.StartRecording):
            with self._lock:
                self._input_checks=dict(capture_native='not_run',capture_field='not_run',delivery='not_run')
            token=self._token(effect.job)
            def start():
                try:
                    if token.is_set():return
                    if self.cues is None:self.microphone.start()
                    else:
                        if self.cues.cleanup_pending:
                            raise HuginError('audio_failed','capture_cue_cleanup')
                        self.microphone.start(armed=False)
                        played=self.cues.play('start',effect.job,token.is_set)
                        if token.is_set():
                            self.microphone.cancel();return
                        if not played:raise HuginError('audio_failed','capture_start_cue')
                        self.microphone.arm_after(self.microphone.device_time+self.cues.tail_seconds)
                    if token.is_set():
                        self.microphone.cancel();return
                    self._post(c.RecordingStarted(effect.job))
                except Exception as error:
                    try:self.microphone.cancel()
                    except HuginError:pass
                    if self.microphone.owned:
                        self._post(_Failure(HuginError('microphone_failed','capture_cleanup')))
                    else: self._post(c.RecordingStarted(effect.job,_safe_error(error,'capture')))
            self._capture_submit(start)
        elif isinstance(effect,c.StopRecording):
            target=None;native_status='not_attempted'
            if not effect.discard:
                native=self._capture_target_outcome(effect.job,'capture_native',self.clipboard.capture_native_target)
                native_status,target=native.status,native.target
            token = self._token(effect.job)
            if effect.discard:
                token.set()
                if self.cues is not None:
                    try:self.cues.stop(effect.job)
                    except HuginError as error:self._post(_CueFailure(error))
            def stop():
                data,error = None,None
                bound_target=_CapturedTarget(native_status,target)
                try:
                    if effect.discard: self.microphone.cancel()
                    else:
                        data = self.microphone.stop()
                        if self.cues is not None and not token.is_set():
                            try:
                                if not self.cues.play('end',effect.job,token.is_set) and not token.is_set():
                                    raise HuginError('audio_failed','capture_end_cue')
                            except Exception:self._post(_CueFailure(HuginError('audio_failed','capture_end_cue')))
                        if target is not None and not token.is_set():
                            bound_target=self._capture_target_outcome(effect.job,'capture_field',
                                lambda:self.clipboard.capture_target(expected=target,cancelled=token.is_set))
                        else:
                            self._input_status(effect.job,'capture_field','not_attempted')
                except Exception as cause:
                    error = _safe_error(cause,'capture')
                    try: self.microphone.cancel()
                    except HuginError: pass
                if self.microphone.owned:
                    self._post(_Failure(HuginError('microphone_failed','capture_cleanup')))
                else: self._post(c.RecordingStopped(effect.job,data,bound_target,error))
            self._capture_submit(stop)
        elif isinstance(effect,c.CaptureSelection):
            token = self._token(effect.job)
            with self._lock: pending = bool(self._selection_tasks)
            if pending:
                self._post(c.SelectionReady(effect.job,'',HuginError('clipboard_failed','selection_busy')))
                return False
            def capture():
                try:
                    result = self.clipboard.capture_selection(token.is_set)
                    error = None if result.status == 'captured' else HuginError(
                        'selection_empty' if result.status == 'selection_empty' else 'clipboard_failed','selection')
                    self._post(c.SelectionReady(effect.job,result.text or '',error))
                except Exception as cause:
                    self._post(c.SelectionReady(effect.job,'',_safe_error(cause,'selection')))
            future = self.selection_executor.submit(capture)
            with self._lock: self._selection_tasks.add(future)
            def finished(done):
                with self._lock: self._selection_tasks.discard(done)
            future.add_done_callback(finished)
        elif isinstance(effect,(c.CancelSelection,c.CancelDelivery)):
            self._token(effect.job).set()
        elif isinstance(effect,c.ResetAudio):
            self._token(effect.job).set()
            try:
                self.output.stop(); self._audio_job = None
                reset=True
            except HuginError: reset=False
            # Complete the old effect batch before this ACK starts a new job.
            # Reentrant dispatch could disable the new job's Escape binding.
            self._post(c.AudioReset(effect.job,reset))
        elif isinstance(effect,c.BeginEngine):
            self._begin(effect)
        elif isinstance(effect,c.CancelEngine):
            operation = effect.operation
            if operation.job: self._token(operation.job).set()
            with self._lock: binding = self._bindings.get(operation.engine.value)
            if binding and binding.operation == operation and operation.action != c.Action.INITIALIZE and operation.engine.value in self.pool.workers:
                try: self.pool.cancel(operation.engine.value,binding.request,binding.generation)
                except HuginError: pass
            self._deadlines[(operation.engine,operation.engine_instance)] = time.monotonic()+self.settings.limits['cancel_seconds']
        elif isinstance(effect,c.ShutdownEngine):
            self._close_engine(effect.engine,effect.engine_instance)
        elif isinstance(effect,c.PlayAudio):
            token = self._token(effect.job)
            def play():
                try:
                    if token.is_set(): return False
                    if self._audio_job != effect.job:
                        self.output.start(effect.job.request_id); self._audio_job = effect.job
                        self._audio_section = 0
                    started=None
                    if self._audio_section != effect.section.index:
                        if self._audio_section and not self.output.drain(effect.job.request_id,token.is_set):return False
                        def started():
                            self._audio_section=effect.section.index
                            self._post(c.SectionStarted(effect.job,effect.section))
                    return self.output.write(effect.pcm,effect.job.request_id,token.is_set,started=started)
                except Exception as error:
                    self._post(_Failure(_safe_error(error,'audio'))); return False
            future = self.audio_executor.submit(play)
            if audio_ack:
                def acknowledge(done):
                    if not audio_ack.done(): audio_ack.set_result(done.result())
                future.add_done_callback(acknowledge)
            return True
        elif isinstance(effect,c.PauseAudio):
            try:
                token=self._token(effect.job)
                if not token.is_set() and not self.output.pause(effect.job.request_id,effect.paused) and not token.is_set():
                    raise HuginError('audio_failed','audio_pause')
            except Exception as error:self._post(_Failure(_safe_error(error,'audio_pause')),priority=0)
        elif isinstance(effect,c.DrainAudio):
            token = self._token(effect.job)
            def drain():
                try:
                    # A silent completed stream has no native player to drain.
                    if self._audio_job != effect.job or self.output.drain(effect.job.request_id,token.is_set):
                        if self._audio_job == effect.job: self._audio_job=None
                        self._post(c.AudioFinished(effect.job,effect.through_sequence))
                except Exception as error: self._post(_Failure(_safe_error(error,'audio')))
            self.audio_executor.submit(drain)
        elif isinstance(effect,c.StageDelivery):
            with self._lock:self._delivery_visual=(effect.job,self._visual_epoch)
            token = self._token(effect.job)
            def current():
                with self._lock:return not token.is_set() and self._snapshot.job == effect.job
            def authorize(transaction):
                if threading.get_ident() != self._owner_ident:
                    raise ClipboardFailure('commit_rejected')
                committed = self.core.dispatch(c.DeliveryCommit(effect.job,transaction,current()))
                return any(isinstance(item,c.DeliverText) and item.transaction == transaction for item in committed)
            def commit(transaction,send):
                if threading.get_ident() == self._owner_ident:
                    send();return
                acknowledgement=Future()
                self._post(_DeliveryCommit(effect.job,transaction,send,acknowledgement))
                deadline=time.monotonic()+2
                while not acknowledgement.done():
                    if token.is_set() or time.monotonic() >= deadline:
                        if acknowledgement.cancel():raise ClipboardFailure(
                            'cancelled' if token.is_set() else 'commit_timeout')
                    try:acknowledgement.result(timeout=.025)
                    except TimeoutError:pass
                acknowledgement.result()
            def deliver():
                try:
                    captured=effect.target
                    if not isinstance(captured,_CapturedTarget) or captured.status!='target_captured' or captured.target is None:
                        self._input_status(effect.job,'delivery','not_attempted')
                        error=_input_error(captured.status if isinstance(captured,_CapturedTarget) else 'unknown','target_capture')
                    else:
                        result=self.clipboard.deliver(effect.text,captured.target,current,
                            authorize=authorize,commit=commit)
                        status=self._input_status(effect.job,'delivery',result.status)
                        error=None if result.submitted and result.restored else _input_error(status,'delivery')
                except BaseException as cause:error=_safe_error(cause,'delivery')
                self._post(c.DeliveryFinished(effect.job,error))
            ticket=Future()
            with self._lock:self._delivery_tasks.add(ticket)
            def finished(done):
                with self._lock:self._delivery_tasks.discard(done)
            ticket.add_done_callback(finished)
            def claimed_delivery():
                # submit can fail after enqueueing or starting a WorkItem.
                # This independently owned gate precedes all native work.
                if not ticket.set_running_or_notify_cancel():return
                try:deliver()
                finally:ticket.set_result(None)
            try:self.delivery_executor.submit(claimed_delivery)
            except BaseException:
                if ticket.cancel():
                    self._post(c.DeliveryFinished(effect.job,HuginError('worker_failed','delivery_start')))
                elif not ticket.done():
                    self._post(_Failure(HuginError('worker_failed','delivery_start')))
        elif isinstance(effect,c.CopyText):
            if self.clipboard.copy(effect.text).status != 'copied':
                self._runtime_error = HuginError('clipboard_failed','copy')
        elif isinstance(effect,c.PersistVoice):
            try:
                path = self.settings.paths['state']/'preferences.json'
                path.parent.mkdir(parents=True,exist_ok=True)
                temporary = path.with_suffix('.tmp')
                temporary.write_text(json.dumps({'schema_version':1,'voice':effect.voice}),encoding='utf-8')
                temporary.replace(path)
            except OSError: self._runtime_error = HuginError('config_invalid','preferences')
        return False

    def _begin(self, effect):
        operation = effect.operation
        engine = operation.engine.value
        try:
            if operation.action == c.Action.INITIALIZE:
                future = self.pool.start(engine)
                worker = self.pool.workers[engine]
                self._incarnations[engine] = (operation.engine_instance,worker.engine_instance)
                self._deadlines[(operation.engine,operation.engine_instance)] = time.monotonic()+self.settings.limits['ready_seconds']
                def initialized(done):
                    try: ready = done.result(); error = None
                    except Exception as cause: ready,error = None,_safe_error(cause,'initialize')
                    self._post(_Started(operation,ready,error))
                future.add_done_callback(initialized)
                return
            worker = self.pool.workers[engine]
            if operation.action == c.Action.OFFLOAD:
                future = self.pool.offload(engine)
                # Offload creates its own protocol UUID. Only this future can
                # acknowledge this exact centrally scheduled operation.
                with self._lock: self._bindings.pop(engine,None)
            else:
                request = str(uuid.uuid5(self.run_id,operation.request_id))
                binding = _Binding(operation,worker.engine_instance,request,operation.job.generation)
                with self._lock: self._bindings[engine] = binding
                if operation.action == c.Action.TRANSCRIBE:
                    future = self.pool.transcribe(effect.payload,request,binding.generation)
                elif operation.action == c.Action.SYNTHESIZE:
                    future = self.pool.synthesize(effect.payload,effect.voice,request,binding.generation,self.settings.language)
                else: raise HuginError('unsupported','engine')
            def finished(done):
                try:
                    terminal = done.result()
                    success = terminal.get('code') is None and not terminal.get('cancelled',False)
                    self._post(c.EngineTerminal(operation,success))
                except Exception as cause: self._post(c.EngineFault(operation,_safe_error(cause,'engine')))
            future.add_done_callback(finished)
        except Exception as error:
            self.handle(c.EngineFault(operation,_safe_error(error,'engine')))
            self._close_engine(operation.engine,operation.engine_instance)

    def _capture_submit(self, operation):
        future = self.capture_executor.submit(operation)
        with self._lock: self._capture_tasks.add(future)
        def finished(done):
            with self._lock: self._capture_tasks.discard(done)
        future.add_done_callback(finished)

    def _close_engine(self, engine, incarnation, *, retry=False):
        key = (engine,incarnation)
        if key in self._closing or key in self._cleanup_failed and not retry: return
        if retry: self._cleanup_failed.discard(key)
        current = self._incarnations.get(engine.value)
        if current is not None and current[0] != incarnation:
            return
        self._closing.add(key)
        worker = self.pool.workers.get(engine.value)
        def close():
            error = None
            try:
                if worker is not None:
                    worker.close()
                    self.pool.workers.pop(engine.value,None)
            except Exception as cause: error = _safe_error(cause,'worker_cleanup')
            self._post(_Closed(engine,incarnation,error))
        self.maintenance_executor.submit(close)

    def tick(self):
        now = time.monotonic()
        self.handle(c.Tick(now))
        snapshot = self.core.snapshot()
        slot = snapshot.gpu_slot
        for key,deadline in tuple(self._deadlines.items()):
            if slot is None or key != (slot.engine,slot.engine_instance):
                self._deadlines.pop(key,None)
            elif now >= deadline: self._close_engine(*key)
        if slot:
            worker = self.pool.workers.get(slot.engine.value)
            if worker and (getattr(worker,'failed',False) or
                    worker.process is not None and worker.process.poll() is not None):
                self._close_engine(slot.engine,slot.engine_instance)
        if self.microphone.fault and snapshot.state == c.State.RECORDING:
            self._runtime_error = self.microphone.fault
            self.handle(c.Cancel())
        if self.inputs.error:
            self._runtime_error = self.inputs.error
            self.handle(c.Cancel())
        if self.signals is not None and self.signals.error:
            self._runtime_error = self.signals.error
            self.handle(c.Cancel())
        # Tokens contain no content. Retain only owners still capable of output.
        with self._lock:
            live = {snapshot.job,snapshot.cancelling_job}
            live.update(op.job for op in snapshot.retired_operations)
            self._tokens = {job:token for job,token in self._tokens.items() if job in live}

    def diagnostic(self):
        snap = self.core.snapshot()
        retiring={(op.engine,op.engine_instance) for op in snap.retired_operations}
        capture_active=snap.job is not None and snap.job.kind == c.JobKind.DICTATION
        selection_active=snap.job is not None and snap.job.kind == c.JobKind.READING
        with self._lock:
            abandoned_io=bool((self.microphone.owned or self._capture_tasks or self._delivery_tasks
                or self._completion_cue is not None) and not capture_active
                or self._selection_tasks and not selection_active
                or self.cues is not None and self.cues.cleanup_pending)
            input_checks=dict(self._input_checks)
        data = {'schema_version':1,'app':'Hugin','version':__version__,
            'state':snap.state.value,'voice':snap.voice,'input_ready':bool(self.inputs.running and not self.inputs.error),
            'profile_id':self.settings.voices[snap.voice].source_id,
            'engine_versions':self._engine_versions,
            'engine_versions_source':'installed metadata at application startup',
            'last_input_utc':self._last_input_utc,
            'input_age_seconds':None if self._last_input is None else round(max(0,time.monotonic()-self._last_input),2),
            'components':{item.engine.value:{'ready':item.ready and (item.engine,item.engine_instance) not in self._closing | self._cleanup_failed | retiring,
                'blocked':item.blocked or (item.engine,item.engine_instance) in self._cleanup_failed,
                'device':self._devices.get(item.engine.value)} for item in snap.components},
            'error_code':self._runtime_error.code if self._runtime_error else snap.error.code if snap.error else None,
            'input_checks':input_checks,
            'pending_cleanup':bool(self._closing or self._cleanup_failed or self._io_cleanup_failed
                or snap.retired_operations or snap.cancelling_job or abandoned_io)}
        return json.dumps(data,ensure_ascii=False,indent=2)

    def view(self):
        snap = self.core.snapshot()
        retiring={(op.engine,op.engine_instance) for op in snap.retired_operations}
        loading = snap.gpu_slot if snap.gpu_slot and snap.gpu_slot.action == c.Action.INITIALIZE else None
        labels = {c.State.IDLE:'Bereit für dein Diktat',c.State.STARTING:'Mikrofon wird geöffnet',c.State.RECORDING:'Aufnahme läuft',
            c.State.TRANSCRIBING:'Diktat wird verarbeitet',c.State.DELIVERING:'Text wird übergeben',
            c.State.TTS_PREPARING:'Vorlesen wird vorbereitet',c.State.TTS_PLAYING:'Vorlesen läuft',
            c.State.CANCELLING:'Wird gestoppt',c.State.ERROR:'Aktion beendet',c.State.STOPPING:'Hugin wird beendet'}
        error = self._runtime_error.code if self._runtime_error else snap.error.code if snap.error else None
        components = ' · '.join(('Whisper' if item.engine == c.Engine.STT else 'Qwen')+': '+
            ('wird beendet' if (item.engine,item.engine_instance) in self._closing else
             'Bereinigung offen' if (item.engine,item.engine_instance) in self._cleanup_failed else
             'wird gestoppt' if (item.engine,item.engine_instance) in retiring else
             'gestört' if item.blocked else 'wird geladen' if loading and item.engine == loading.engine
             else 'bereit' if item.ready else 'bei Bedarf') for item in snap.components)
        pilot = getattr(self.inputs,'pilot',False)
        activity = 'error' if error else {c.State.IDLE:'idle',c.State.RECORDING:'recording',
            c.State.TRANSCRIBING:'processing',c.State.DELIVERING:'processing',
            c.State.TTS_PLAYING:'playing'}.get(snap.state,'preparing')
        active_action='' if error else {
            c.State.STARTING:'dictation',c.State.RECORDING:'dictation',
            c.State.TRANSCRIBING:'dictation',c.State.DELIVERING:'dictation',
            c.State.TTS_PREPARING:'reading',c.State.TTS_PLAYING:'reading',
        }.get(snap.state,'')
        status=labels[snap.state]
        if snap.reading_paused:
            status='Vorlesen pausiert'
            activity='idle'
        if loading and loading.job == snap.job and snap.job:
            status=('Whisper' if loading.engine == c.Engine.STT else 'Qwen')+' wird geladen'
        if snap.state == c.State.IDLE and retiring:
            status='Vorherige Verarbeitung wird beendet'
            if not error: activity='preparing'
        if not self.inputs.running or self.inputs.error: status='Eingaben nicht bereit'
        elif self.signals is not None and not self.signals.ready and not self._stop:
            status='Windows-Verbindung nicht bereit'
        audio_level=0.0
        if not error and snap.state==c.State.RECORDING:
            try:observed=getattr(self.microphone,'audio_level',0.0)
            except Exception:observed=0.0
            if type(observed) in (int,float) and math.isfinite(observed) and 0<=observed<=1:
                audio_level=float(observed)
        with self._lock:
            completion_id=self._completion_id
            completion_until=0.0 if error else self._completion_until
        view = View(status=status,voice=snap.voice,text=snap.result.text if snap.result else '',
            panel_token=(snap.generation,snap.state.value),
            dictation_control=self._panel_controls(snap)[0],reading_control=self._panel_controls(snap)[1],
            detail='Erneut drücken, um das Diktat abzuschließen.' if snap.state == c.State.RECORDING else '',
            mode='Lokal · Pilot' if pilot else 'Lokal',components=components,
            error=MESSAGES.get(error,'') if error else '',activity=activity,audio_level=audio_level,
            completion_id=completion_id,completion_until=completion_until,active_action=active_action,
            reading_job=snap.job.request_id if snap.job and snap.job.kind==c.JobKind.READING and snap.reading_total else '',
            reading_text=snap.reading_section.text if snap.reading_section else '',
            reading_index=snap.reading_section.index if snap.reading_section else 0,
            reading_total=snap.reading_total,reading_paused=snap.reading_paused)
        if pilot:
            from dataclasses import replace
            view=replace(view,dictation_shortcut='Strg+Alt+D · erneut: fertig',
                reading_shortcut='Text markieren · Strg+Alt+V · erneut: Stopp')
        return view

    def _publish(self): self.publish(self.view())

    def shutdown_ready(self):
        snap = self.core.snapshot()
        with self._lock: capture_pending = bool(self._capture_tasks or self._selection_tasks
            or self._delivery_tasks or self._completion_cue is not None)
        return self._stop and not (snap.gpu_slot or snap.cancelling_job or self._closing or
            self._cleanup_failed or self.pool.workers or self.microphone.owned or capture_pending)

    def finish_io(self):
        """Retain each failed owner; completed owners never repeat cleanup."""
        owners=[('inputs',self.inputs,self.inputs.stop),('output',self.output,self.output.close),
            ('clipboard',self.clipboard,self.clipboard.close)]
        if self.cues is not None:owners.insert(2,('cues',self.cues,self.cues.close))
        if self.signals is not None: owners.insert(1,('signals',self.signals,self.signals.close))
        for name,owner,close in owners:
            if name in self._closed_io: continue
            try:
                if not getattr(owner,'closed',False): close()
                self._closed_io.add(name)
            except Exception as cause:
                self._runtime_error=_safe_error(cause,'shutdown_'+name)
                if getattr(owner,'closed',False): self._closed_io.add(name)
                else: self._io_cleanup_failed.add(name)
        return not self._io_cleanup_failed

    def run(self, on_closed):
        self._owner_ident=threading.get_ident()
        while not self._closed:
            try:
                self.pump_once(.025)
                self.tick()
                if self.shutdown_ready() and not self._io_cleanup_failed and self.finish_io():
                    for executor in (self.capture_executor,self.audio_executor,self.maintenance_executor,self.selection_executor,self.delivery_executor):
                        executor.shutdown(wait=True,cancel_futures=True)
                    self._closed = True
            except Exception as cause:
                self._runtime_error = _safe_error(cause,'controller')
                self._publish()
                # Retain ownership and surface failure; no blind process cleanup/retry.
                self._stop = True
                self.handle(c.Shutdown())
        on_closed()


class Application:
    def __init__(self, settings, *, pilot=False, show=False):
        self.settings,self.pilot,self.show = settings,pilot,show

    def run(self):
        from .audio import Microphone,PCMOutput
        from .cues import DictationCues,load_cue_signals
        from .ui import HuginWindow
        from .windows.input import WindowsInputs
        from .windows.instance import InstanceGuard
        from .windows.clipboard import ClipboardService
        from .windows.signals import WindowsSignals
        from .workers import EnginePool
        from .targets import load_target_approvals
        approvals=load_target_approvals(self.settings.root)
        guard = InstanceGuard()
        if not guard.acquire():
            guard.close()
            return 0
        controller = None
        window = None
        thread = None
        thread_started=False
        try:
            cue_signals=load_cue_signals(self.settings.root)
            def command(kind,value=None):
                if controller: controller.command(kind,value)
            def event(value):
                if controller: controller.worker_event(value)
            inputs = WindowsInputs(command,pilot=self.pilot)
            signals = WindowsSignals(command)
            try: window = HuginWindow(command)
            except BaseException as error:
                if isinstance(getattr(error,'owner',None),HuginWindow): window=error.owner
                raise
            clipboard=ClipboardService(snapshot_budget=self.settings.limits['clipboard_bytes'])
            for approval in approvals.delivery:
                clipboard.approve_target_class(approval.control_class,approval.restore_delay_seconds,
                    package_family=approval.package_family)
            for name in approvals.capture_fallback: clipboard.approve_capture_target_class(name)
            if approvals.verified_edit is not None:
                clipboard.approve_verified_edits(approvals.verified_edit.restore_delay_seconds)
            controller = Controller(self.settings,inputs=inputs,
                microphone=Microphone(self.settings.limits['capture_bytes']),
                output=PCMOutput(buffer_ms=max(1,self.settings.limits['audio_buffer_ms']//2)),
                clipboard=clipboard,
                pool=EnginePool(self.settings.root,event),publish=window.post,signals=signals,
                cues=DictationCues(cue_signals))
            signals.start()
            inputs.start()
            thread = threading.Thread(target=controller.run,args=(window.request_stop,),name='hugin-owner',daemon=False)
            thread.start()
            thread_started=True
            if self.show: window.show()
            window.run()
            if getattr(window,'failure',None): raise window.failure
            return 0
        finally:
            owner_closed=controller is None
            window_closed=window is None
            try:
                if thread_started:
                    # A UI/show failure must follow the same owned shutdown as
                    # a normal close. Keep the mutex until native cleanup ends.
                    controller.command('quit')
                    thread.join()
                    owner_closed=controller._closed
                    if not owner_closed: raise HuginError('worker_failed','controller_exit')
                else:
                    if controller:
                        owner_closed=controller.finish_io()
                        for executor in (controller.capture_executor,controller.audio_executor,controller.maintenance_executor,controller.selection_executor,controller.delivery_executor):
                            executor.shutdown(wait=True,cancel_futures=True)
                if window:
                    window.stop()
                    window_closed=True
            finally:
                if owner_closed and window_closed: guard.close()
                else: self._startup_owners=(guard,controller,window,thread)
