"""One serial application owner, bounded callbacks and explicit native adapters.

Never log events/effects/futures: their payloads are private user content.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime,timezone
import itertools
import json
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
class _Command:
    kind: str
    value: str | None = None


@dataclass(frozen=True)
class _Binding:
    operation: c.Operation
    actual: str
    request: str
    generation: int


def _safe_error(error, phase):
    return HuginError(error.code if isinstance(error,HuginError) else 'worker_failed',phase)


class Controller:
    """Construct and pump on one owner thread; callbacks call command/worker_event."""
    def __init__(self, settings, *, inputs, microphone, output, clipboard, pool,
                 publish, capture_executor=None, audio_executor=None, maintenance_executor=None,
                 selection_executor=None,signals=None):
        self.settings = settings
        self.inputs,self.microphone,self.output = inputs,microphone,output
        self.clipboard,self.pool,self.publish = clipboard,pool,publish
        self.signals = signals
        self.run_id = uuid.uuid4()
        self.core = c.Coordinator(instance_id=str(self.run_id),now=time.monotonic(),
            stt_idle_unload_seconds=settings.stt['idle_unload_seconds'],
            default_voice=self._voice(),limits=c.Limits(**{key:settings.limits[key] for key in
            ('capture_bytes','transcript_bytes','selection_bytes','frame_bytes','result_ttl_seconds')}))
        self.capture_executor = capture_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-capture')
        self.audio_executor = audio_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-audio')
        self.maintenance_executor = maintenance_executor or ThreadPoolExecutor(2,thread_name_prefix='hugin-cleanup')
        self.selection_executor = selection_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-selection')
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
        self._completions = {}
        self._queued_head = None
        self._audio_job = None
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
        elif isinstance(event,(c.RecordingStarted,c.RecordingStopped)):
            key = (type(event),event.job)
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
        with self._lock:
            job = self._snapshot.job
            invalidates = kind in ('cancel','quit','system_pause','system_resume','devices_changed') or (job is not None and job.kind == c.JobKind.READING
                and (kind in ('dictation','read') or kind == 'voice' and value != self._snapshot.voice))
            if invalidates and job:
                self._token(job).set()
            if kind in ('dictation','read','cancel'):
                self._last_input = time.monotonic()
                self._last_input_utc = datetime.now(timezone.utc).isoformat(timespec='seconds')
        if invalidates:
            try: self.output.stop()
            except HuginError as error: self._post(_Failure(error),priority=0)
        self._post(_Command(kind,value),priority=-1 if kind == 'quit' else 0)

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
        if isinstance(event,_Command):
            mapping = {'dictation':c.DictationToggle,'read':c.ReadToggle,'cancel':c.Cancel,
                'copy':c.CopyResult,'clear':c.DeleteResult,'quit':c.Shutdown,
                'system_pause':c.Cancel,'system_resume':c.Cancel,'devices_changed':c.Cancel}
            if event.kind == 'voice': event = c.VoiceSelected(event.value)
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
                event = mapping[event.kind]()
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
        effects = self.core.dispatch(event)
        with self._lock:
            self._snapshot = self.core.snapshot()
            if self._snapshot.job: self._token(self._snapshot.job)
        accepted_audio = False
        for effect in effects:
            if isinstance(effect,c.SetEscape):
                try: self.inputs.set_cancel_active(effect.enabled)
                except HuginError as error:
                    self._runtime_error = error
                    if effect.enabled:
                        # No start effect has run. Acknowledge unused capture ownership.
                        job = self._snapshot.job
                        self.handle(c.Cancel())
                        if job and job.kind == c.JobKind.DICTATION and not self.microphone.owned:
                            self.handle(c.RecordingStopped(job))
                        if audio_ack and not audio_ack.done(): audio_ack.set_result(False)
                        return
            else:
                accepted_audio |= self._effect(effect,audio_ack)
        if audio_ack and not accepted_audio and not audio_ack.done(): audio_ack.set_result(False)
        self._publish()

    def _effect(self, effect, audio_ack=None):
        if isinstance(effect,c.StartRecording):
            def start():
                try:
                    self.microphone.start()
                    self._post(c.RecordingStarted(effect.job))
                except Exception as error:
                    if self.microphone.owned:
                        self._post(_Failure(HuginError('microphone_failed','capture_cleanup')))
                    else: self._post(c.RecordingStarted(effect.job,_safe_error(error,'capture')))
            self._capture_submit(start)
        elif isinstance(effect,c.StopRecording):
            target = None if effect.discard else self.clipboard.capture_target().target
            def stop():
                data,error = None,None
                try:
                    if effect.discard: self.microphone.cancel()
                    else: data = self.microphone.stop()
                except Exception as cause:
                    error = _safe_error(cause,'capture')
                    try: self.microphone.cancel()
                    except HuginError: pass
                if self.microphone.owned:
                    self._post(_Failure(HuginError('microphone_failed','capture_cleanup')))
                else: self._post(c.RecordingStopped(effect.job,data,target,error))
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
                    return self.output.write(effect.pcm,effect.job.request_id,token.is_set)
                except Exception as error:
                    self._post(_Failure(_safe_error(error,'audio'))); return False
            future = self.audio_executor.submit(play)
            if audio_ack:
                def acknowledge(done):
                    if not audio_ack.done(): audio_ack.set_result(done.result())
                future.add_done_callback(acknowledge)
            return True
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
            token = self._token(effect.job)
            def current(): return not token.is_set() and self.core.snapshot().job == effect.job
            def authorize(transaction):
                committed = self.core.dispatch(c.DeliveryCommit(effect.job,transaction,current()))
                return any(isinstance(item,c.DeliverText) and item.transaction == transaction for item in committed)
            result = self.clipboard.deliver(effect.text,effect.target,current,authorize=authorize)
            error = None if result.submitted and result.restored else HuginError('target_changed','delivery')
            self.handle(c.DeliveryFinished(effect.job,error))
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
            abandoned_io=bool((self.microphone.owned or self._capture_tasks) and not capture_active
                or self._selection_tasks and not selection_active)
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
            'pending_cleanup':bool(self._closing or self._cleanup_failed or self._io_cleanup_failed
                or snap.retired_operations or snap.cancelling_job or abandoned_io)}
        return json.dumps(data,ensure_ascii=False,indent=2)

    def view(self):
        snap = self.core.snapshot()
        retiring={(op.engine,op.engine_instance) for op in snap.retired_operations}
        labels = {c.State.IDLE:'Bereit',c.State.STARTING:'Mikrofon wird geöffnet',c.State.RECORDING:'Aufnahme läuft',
            c.State.TRANSCRIBING:'Diktat wird verarbeitet',c.State.DELIVERING:'Text wird übergeben',
            c.State.TTS_PREPARING:'Vorlesen wird vorbereitet',c.State.TTS_PLAYING:'Vorlesen läuft',
            c.State.CANCELLING:'Wird gestoppt',c.State.ERROR:'Aktion beendet',c.State.STOPPING:'Hugin wird beendet'}
        error = self._runtime_error.code if self._runtime_error else snap.error.code if snap.error else None
        components = ' · '.join(('Whisper' if item.engine == c.Engine.STT else 'Qwen')+': '+
            ('wird beendet' if (item.engine,item.engine_instance) in self._closing else
             'Bereinigung offen' if (item.engine,item.engine_instance) in self._cleanup_failed else
             'wird gestoppt' if (item.engine,item.engine_instance) in retiring else
             'gestört' if item.blocked else 'bereit' if item.ready else 'bei Bedarf') for item in snap.components)
        pilot = getattr(self.inputs,'pilot',False)
        activity = 'error' if error else {c.State.IDLE:'idle',c.State.RECORDING:'recording',c.State.TTS_PLAYING:'playing'}.get(snap.state,'preparing')
        status=labels[snap.state]
        if snap.state == c.State.IDLE and retiring:
            status='Vorherige Verarbeitung wird beendet'
            if not error: activity='preparing'
        if not self.inputs.running or self.inputs.error: status='Eingaben nicht bereit'
        elif self.signals is not None and not self.signals.ready and not self._stop:
            status='Windows-Verbindung nicht bereit'
        view = View(status=status,voice=snap.voice,text=snap.result.text if snap.result else '',
            detail='Erneut drücken, um das Diktat abzuschließen.' if snap.state == c.State.RECORDING else '',
            mode='Lokal · Pilot' if pilot else 'Lokal',components=components,
            error=MESSAGES.get(error,'') if error else '',activity=activity)
        if pilot:
            from dataclasses import replace
            view=replace(view,dictation_shortcut='Ctrl+Alt+Shift+F9 · erneut: fertig',
                reading_shortcut='Text markieren · Ctrl+Alt+Shift+F10 · erneut: Stopp')
        return view

    def _publish(self): self.publish(self.view())

    def shutdown_ready(self):
        snap = self.core.snapshot()
        with self._lock: capture_pending = bool(self._capture_tasks or self._selection_tasks)
        return self._stop and not (snap.gpu_slot or snap.cancelling_job or self._closing or
            self._cleanup_failed or self.pool.workers or self.microphone.owned or capture_pending)

    def finish_io(self):
        """Retain each failed owner; completed owners never repeat cleanup."""
        owners=[('inputs',self.inputs,self.inputs.stop),('output',self.output,self.output.close),
            ('clipboard',self.clipboard,self.clipboard.close)]
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
        while not self._closed:
            try:
                self.pump_once(.025)
                self.tick()
                if self.shutdown_ready() and not self._io_cleanup_failed and self.finish_io():
                    for executor in (self.capture_executor,self.audio_executor,self.maintenance_executor,self.selection_executor):
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
            for name,delay in approvals.delivery: clipboard.approve_target_class(name,delay)
            for name in approvals.capture_fallback: clipboard.approve_capture_target_class(name)
            controller = Controller(self.settings,inputs=inputs,
                microphone=Microphone(self.settings.limits['capture_bytes']),
                output=PCMOutput(buffer_ms=max(1,self.settings.limits['audio_buffer_ms']//2)),
                clipboard=clipboard,
                pool=EnginePool(self.settings.root,event),publish=window.post,signals=signals)
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
                        for executor in (controller.capture_executor,controller.audio_executor,controller.maintenance_executor,controller.selection_executor):
                            executor.shutdown(wait=True,cancel_futures=True)
                if window:
                    window.stop()
                    window_closed=True
            finally:
                if owner_closed and window_closed: guard.close()
                else: self._startup_owners=(guard,controller,window,thread)
