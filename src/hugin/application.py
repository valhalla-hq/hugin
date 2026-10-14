"""One serial application owner, bounded callbacks and explicit native adapters.

Never log events/effects/futures: their payloads are private user content.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
import itertools
import json
import queue
import threading
import time
import uuid

from . import coordinator as c
from .errors import HuginError, MESSAGES
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
                 publish, capture_executor=None, audio_executor=None, maintenance_executor=None):
        self.settings = settings
        self.inputs,self.microphone,self.output = inputs,microphone,output
        self.clipboard,self.pool,self.publish = clipboard,pool,publish
        self.run_id = uuid.uuid4()
        self.core = c.Coordinator(instance_id=str(self.run_id),now=time.monotonic(),
            stt_idle_unload_seconds=settings.stt['idle_unload_seconds'],
            default_voice=self._voice(),limits=c.Limits(**{key:settings.limits[key] for key in
            ('capture_bytes','transcript_bytes','selection_bytes','frame_bytes','result_ttl_seconds')}))
        self.capture_executor = capture_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-capture')
        self.audio_executor = audio_executor or ThreadPoolExecutor(1,thread_name_prefix='hugin-audio')
        self.maintenance_executor = maintenance_executor or ThreadPoolExecutor(2,thread_name_prefix='hugin-cleanup')
        self._events = queue.PriorityQueue(maxsize=64)
        self._counter = itertools.count()
        self._lock = threading.RLock()
        self._tokens = {}
        self._bindings = {}
        self._incarnations = {}
        self._deadlines = {}
        self._closing = set()
        self._audio_job = None
        self._snapshot = self.core.snapshot()
        self._runtime_error = None
        self._overflow = threading.Event()
        self._stop = False
        self._closed = False
        self._last_input = None
        self._capture_failed = False
        self._devices = {}

    def _voice(self):
        path = self.settings.paths['state']/'preferences.json'
        if not path.exists(): return self.settings.default_voice
        try:
            if path.stat().st_size > 1024: raise ValueError
            data = json.loads(path.read_text(encoding='utf-8'))
            if set(data) != {'schema_version','voice'} or type(data['schema_version']) is not int or data['schema_version'] != 1 or data['voice'] not in ('freya','tyr'):
                raise ValueError
            return data['voice']
        except (OSError,ValueError,TypeError):
            raise HuginError('config_invalid','preferences') from None

    def _token(self, job):
        with self._lock:
            return self._tokens.setdefault(job,threading.Event())

    def _post(self, event, *, priority=1, audio_ack=None):
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
            invalidates = kind in ('cancel','quit') or (job is not None and job.kind == c.JobKind.READING
                and kind in ('dictation','read','voice'))
            if invalidates and job:
                self._token(job).set()
            if kind in ('dictation','read','cancel'):
                self._last_input = time.monotonic()
        if invalidates:
            try: self.output.stop()
            except HuginError as error: self._post(_Failure(error),priority=0)
        self._post(_Command(kind,value),priority=0)

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
        try: _,_,event,ack = self._events.get(timeout=timeout)
        except queue.Empty: return False
        self.handle(event,audio_ack=ack)
        return True

    def handle(self, event, *, audio_ack=None):
        if isinstance(event,_Command):
            mapping = {'dictation':c.DictationToggle,'read':c.ReadToggle,'cancel':c.Cancel,
                'copy':c.CopyResult,'clear':c.DeleteResult,'quit':c.Shutdown}
            if event.kind == 'voice': event = c.VoiceSelected(event.value)
            elif event.kind == 'diagnose':
                result = self.clipboard.copy(self.diagnostic())
                if result.status != 'copied': self._runtime_error = HuginError('clipboard_failed','diagnostic')
                self._publish(); return
            elif event.kind in mapping:
                if event.kind == 'quit': self._stop = True
                event = mapping[event.kind]()
            else: return
        if isinstance(event,_Started):
            if self.core.snapshot().gpu_slot != event.operation:
                return
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
                self._deadlines[(event.engine,event.incarnation)] = float('inf')
            else:
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
                        self._capture_failed = True
                        self._post(_Failure(HuginError('microphone_failed','capture_cleanup')))
                    else: self._post(c.RecordingStarted(effect.job,_safe_error(error,'capture')))
            self.capture_executor.submit(start)
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
                    self._capture_failed = True
                    self._post(_Failure(HuginError('microphone_failed','capture_cleanup')))
                else: self._post(c.RecordingStopped(effect.job,data,target,error))
            self.capture_executor.submit(stop)
        elif isinstance(effect,c.CaptureSelection):
            token = self._token(effect.job)
            result = self.clipboard.capture_selection(token.is_set)
            error = None if result.status == 'captured' else HuginError(
                'selection_empty' if result.status == 'selection_empty' else 'clipboard_failed','selection')
            self._post(c.SelectionReady(effect.job,result.text or '',error))
        elif isinstance(effect,(c.CancelSelection,c.CancelDelivery)):
            self._token(effect.job).set()
        elif isinstance(effect,c.ResetAudio):
            self._token(effect.job).set()
            try:
                self.output.stop(); self._audio_job = None
                self.handle(c.AudioReset(effect.job))
            except HuginError: self.handle(c.AudioReset(effect.job,False))
        elif isinstance(effect,c.BeginEngine):
            self._begin(effect)
        elif isinstance(effect,c.CancelEngine):
            operation = effect.operation
            if operation.job: self._token(operation.job).set()
            with self._lock: binding = self._bindings.get(operation.engine.value)
            if binding and binding.operation == operation and operation.action != c.Action.INITIALIZE:
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
                    if self._audio_job is None or self.output.drain(effect.job.request_id,token.is_set):
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

    def _close_engine(self, engine, incarnation):
        key = (engine,incarnation)
        if key in self._closing: return
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
        # Tokens contain no content. Retain only owners still capable of output.
        with self._lock:
            live = {snapshot.job,snapshot.cancelling_job}
            live.update(op.job for op in snapshot.retired_operations)
            self._tokens = {job:token for job,token in self._tokens.items() if job in live}

    def diagnostic(self):
        snap = self.core.snapshot()
        data = {'schema_version':1,'app':'Hugin','version':'0.1.0',
            'state':snap.state.value,'voice':snap.voice,'input_ready':bool(self.inputs.running),
            'input_age_seconds':None if self._last_input is None else round(max(0,time.monotonic()-self._last_input),2),
            'components':{item.engine.value:{'ready':item.ready,'blocked':item.blocked,
                'device':self._devices.get(item.engine.value)} for item in snap.components},
            'error_code':self._runtime_error.code if self._runtime_error else snap.error.code if snap.error else None,
            'pending_cleanup':bool(self._closing) or self._capture_failed}
        return json.dumps(data,ensure_ascii=False,indent=2)

    def view(self):
        snap = self.core.snapshot()
        labels = {c.State.IDLE:'Bereit',c.State.STARTING:'Mikrofon wird geöffnet',c.State.RECORDING:'Aufnahme läuft',
            c.State.TRANSCRIBING:'Diktat wird verarbeitet',c.State.DELIVERING:'Text wird übergeben',
            c.State.TTS_PREPARING:'Vorlesen wird vorbereitet',c.State.TTS_PLAYING:'Vorlesen läuft',
            c.State.CANCELLING:'Wird gestoppt',c.State.ERROR:'Aktion beendet',c.State.STOPPING:'Hugin wird beendet'}
        error = self._runtime_error.code if self._runtime_error else snap.error.code if snap.error else None
        components = ' · '.join(('Whisper' if item.engine == c.Engine.STT else 'Qwen')+': '+
            ('gestört' if item.blocked else 'bereit' if item.ready else 'bei Bedarf') for item in snap.components)
        return View(status=labels[snap.state],voice=snap.voice,text=snap.result.text if snap.result else '',
            detail='Erneut drücken, um das Diktat abzuschließen.' if snap.state == c.State.RECORDING else '',
            mode='Lokal · Pilot' if getattr(self.inputs,'pilot',False) else 'Lokal',components=components,
            error=MESSAGES.get(error,'') if error else '')

    def _publish(self): self.publish(self.view())

    def run(self, on_closed):
        while not self._closed:
            try:
                self.pump_once(.025)
                self.tick()
                snap = self.core.snapshot()
                if self._stop and not (snap.gpu_slot or self._closing or self.microphone.owned):
                    self.inputs.stop(); self.output.close(); self.clipboard.close()
                    for executor in (self.capture_executor,self.audio_executor,self.maintenance_executor):
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
        from .workers import EnginePool
        guard = InstanceGuard()
        if not guard.acquire(): return 0
        controller = None
        window = None
        thread = None
        try:
            def command(kind,value=None):
                if controller: controller.command(kind,value)
            def event(value):
                if controller: controller.worker_event(value)
            inputs = WindowsInputs(command,pilot=self.pilot)
            window = HuginWindow(command)
            controller = Controller(self.settings,inputs=inputs,
                microphone=Microphone(self.settings.limits['capture_bytes']),
                output=PCMOutput(buffer_ms=max(1,self.settings.limits['audio_buffer_ms']//2)),
                clipboard=ClipboardService(snapshot_budget=self.settings.limits['clipboard_bytes']),
                pool=EnginePool(self.settings.root,event),publish=window.post)
            inputs.start()
            thread = threading.Thread(target=controller.run,args=(window.request_stop,),name='hugin-owner',daemon=False)
            thread.start()
            if self.show: window.show()
            window.run()
            controller.command('quit')
            thread.join()
            return 0
        finally:
            if thread is None:
                if controller:
                    controller.inputs.stop()
                    controller.output.close()
                    controller.clipboard.close()
                    for executor in (controller.capture_executor,controller.audio_executor,controller.maintenance_executor):
                        executor.shutdown(wait=True,cancel_futures=True)
                if window: window.stop()
            guard.close()
