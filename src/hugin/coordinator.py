"""Serial, deterministic job reducer. Adapters execute effects; this module does no I/O."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from collections import deque
import math
import re

from .errors import HuginError


class State(StrEnum):
    STARTING = 'STARTING'
    IDLE = 'IDLE'
    RECORDING = 'RECORDING'
    TRANSCRIBING = 'TRANSCRIBING'
    DELIVERING = 'DELIVERING'
    TTS_PREPARING = 'TTS_PREPARING'
    TTS_PLAYING = 'TTS_PLAYING'
    CANCELLING = 'CANCELLING'
    ERROR = 'ERROR'
    STOPPING = 'STOPPING'


class JobKind(StrEnum):
    DICTATION = 'dictation'
    READING = 'reading'


class Engine(StrEnum):
    STT = 'stt'
    TTS = 'tts'


class Action(StrEnum):
    INITIALIZE = 'initialize'
    TRANSCRIBE = 'transcribe'
    SYNTHESIZE = 'synthesize'


@dataclass(frozen=True)
class Job:
    request_id: str
    generation: int
    kind: JobKind


@dataclass(frozen=True)
class Operation:
    job: Job
    engine: Engine
    engine_instance: str
    request_id: str
    action: Action


@dataclass(frozen=True)
class Limits:
    capture_bytes: int = 16 * 1024 * 1024
    transcript_bytes: int = 256 * 1024
    selection_bytes: int = 256 * 1024
    frame_bytes: int = 64 * 1024
    result_ttl_seconds: int = 300


@dataclass(frozen=True)
class Failure:
    code: str
    phase: str


@dataclass(frozen=True)
class ResultSlot:
    job: Job
    text: str
    expires_at: float


@dataclass(frozen=True)
class Component:
    engine: Engine
    engine_instance: str | None
    ready: bool
    blocked: bool


@dataclass(frozen=True)
class Snapshot:
    state: State
    job: Job | None
    cancelling_job: Job | None
    generation: int
    voice: str
    result: ResultSlot | None
    gpu_slot: Operation | None
    retired_operations: tuple[Operation, ...]
    components: tuple[Component, ...]
    error: Failure | None
    escape_reserved: bool


class Event:
    """Events already parsed by the owning adapter, never raw IPC dictionaries."""


@dataclass(frozen=True)
class DictationToggle(Event):
    pass


@dataclass(frozen=True)
class ReadToggle(Event):
    pass


@dataclass(frozen=True)
class Cancel(Event):
    pass


@dataclass(frozen=True)
class VoiceSelected(Event):
    voice: str


@dataclass(frozen=True)
class RecordingStarted(Event):
    job: Job
    error: HuginError | None = None


@dataclass(frozen=True)
class RecordingStopped(Event):
    job: Job
    capture: bytes | None = None
    target: object = None
    error: HuginError | None = None


@dataclass(frozen=True)
class SelectionReady(Event):
    job: Job
    text: str
    error: HuginError | None = None


@dataclass(frozen=True)
class EngineReady(Event):
    operation: Operation


@dataclass(frozen=True)
class EngineResult(Event):
    operation: Operation
    text: str


@dataclass(frozen=True)
class EngineAudio(Event):
    operation: Operation
    pcm: bytes


@dataclass(frozen=True)
class EngineTerminal(Event):
    operation: Operation
    success: bool = True


@dataclass(frozen=True)
class EngineFault(Event):
    operation: Operation
    error: HuginError


@dataclass(frozen=True)
class EngineExited(Event):
    engine: Engine
    engine_instance: str


@dataclass(frozen=True)
class AudioReset(Event):
    job: Job
    success: bool = True


@dataclass(frozen=True)
class AudioFinished(Event):
    job: Job
    through_sequence: int


@dataclass(frozen=True)
class DeliveryCommit(Event):
    job: Job
    transaction: object
    valid: bool


@dataclass(frozen=True)
class DeliveryFinished(Event):
    job: Job
    error: HuginError | None = None


@dataclass(frozen=True)
class Tick(Event):
    now: float


@dataclass(frozen=True)
class CopyResult(Event):
    pass


@dataclass(frozen=True)
class DeleteResult(Event):
    pass


@dataclass(frozen=True)
class Shutdown(Event):
    pass


class Effect:
    """An instruction for an adapter; effects are never executed by the reducer."""


@dataclass(frozen=True)
class StartRecording(Effect):
    job: Job


@dataclass(frozen=True)
class StopRecording(Effect):
    job: Job
    discard: bool = False


@dataclass(frozen=True)
class CaptureSelection(Effect):
    job: Job


@dataclass(frozen=True)
class CancelSelection(Effect):
    job: Job


@dataclass(frozen=True)
class ResetAudio(Effect):
    job: Job


@dataclass(frozen=True)
class BeginEngine(Effect):
    operation: Operation
    payload: bytes | str | None = None
    voice: str | None = None


@dataclass(frozen=True)
class CancelEngine(Effect):
    operation: Operation


@dataclass(frozen=True)
class ShutdownEngine(Effect):
    engine: Engine
    engine_instance: str


@dataclass(frozen=True)
class PlayAudio(Effect):
    job: Job
    pcm: bytes
    sequence: int


@dataclass(frozen=True)
class DrainAudio(Effect):
    job: Job
    through_sequence: int


@dataclass(frozen=True)
class StageDelivery(Effect):
    job: Job
    text: str
    target: object


@dataclass(frozen=True)
class DeliverText(Effect):
    job: Job
    transaction: object


@dataclass(frozen=True)
class CancelDelivery(Effect):
    job: Job


@dataclass(frozen=True)
class CopyText(Effect):
    text: str


@dataclass(frozen=True)
class PersistVoice(Effect):
    voice: str


@dataclass(frozen=True)
class SetEscape(Effect):
    enabled: bool


@dataclass(frozen=True)
class Busy(Effect):
    kind: JobKind | None


class Coordinator:
    """Call dispatch/snapshot only from the application's one serial owner.

    instance_id must be a fresh, caller-generated identity for this run. Tick
    supplies monotonic time; no clock, devices, threads, workers or file writes
    live here. Do not queue DeliverText for execution outside the serial owner.
    """

    def __init__(self, *, instance_id: str, limits: Limits | None = None,
                 default_voice: str = 'freya', now: float = 0):
        self.limits = limits if limits is not None else Limits()
        if not isinstance(self.limits, Limits):
            raise HuginError('config_invalid', 'coordinator')
        if not isinstance(instance_id, str) or not instance_id or len(instance_id) > 128:
            raise HuginError('config_invalid', 'coordinator')
        if default_voice not in ('freya', 'tyr'):
            raise HuginError('config_invalid', 'coordinator')
        for name, ceiling in (('capture_bytes', 16777216), ('transcript_bytes', 262144),
                              ('selection_bytes', 262144), ('frame_bytes', 65536),
                              ('result_ttl_seconds', 67108864)):
            value = getattr(self.limits, name)
            if type(value) is not int or not 0 < value <= ceiling:
                raise HuginError('config_invalid', 'coordinator')
        if self.limits.capture_bytes % 2 or self.limits.frame_bytes % 2:
            raise HuginError('config_invalid', 'coordinator')
        self._validate_time(now)
        self._now = float(now)
        self._instance_id = instance_id
        self._generation = 0
        self._operation_number = 0
        self._worker_number = 0
        self._state = State.IDLE
        self._job: Job | None = None
        self._cancelling: Job | None = None
        self._voice = default_voice
        self._job_voice: str | None = None
        self._selection_pending: Job | None = None
        self._result: ResultSlot | None = None
        self._error: Failure | None = None
        self._slot: Operation | None = None
        self._slot_result = False
        self._components = {engine: Component(engine, None, False, False) for engine in Engine}
        self._payload: bytes | str | None = None
        self._target: object = None
        self._recording_open: Job | None = None
        self._stopping_capture = False
        self._closing_capture: Job | None = None
        self._closing_delivery: Job | None = None
        self._audio_reset: Job | None = None
        self._audio_failed = False
        self._pending_dictation = False
        self._tts_chunks: deque[str] = deque()
        self._audio_sequence = 0
        self._tts_terminal = False
        self._delivery_attempted = False
        self._shutdown = False
        self._dispatching = False

    @staticmethod
    def _validate_time(now: float) -> None:
        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise HuginError('protocol_invalid', 'clock')

    def snapshot(self) -> Snapshot:
        retired = (self._slot,) if self._slot and self._slot.job != self._job else ()
        return Snapshot(self._state, self._job, self._cancelling, self._generation,
                        self._voice, self._result, self._slot, retired,
                        tuple(self._components.values()), self._error, self._job is not None)

    def dispatch(self, event: Event) -> tuple[Effect, ...]:
        if self._dispatching:
            raise HuginError('protocol_invalid', 'coordinator')
        self._dispatching = True
        escape_before = self._job is not None
        effects: list[Effect] = []
        try:
            self._reduce(event, effects)
            if self._shutdown:
                self._state = State.STOPPING
            escape_after = self._job is not None
            if escape_after != escape_before:
                if escape_after:
                    effects.insert(0, SetEscape(True))
                else:
                    effects.append(SetEscape(False))
            return tuple(effects)
        finally:
            self._dispatching = False

    def _new_job(self, kind: JobKind) -> Job:
        self._generation += 1
        job = Job(f'{self._instance_id}:job:{self._generation}', self._generation, kind)
        self._job = job
        self._error = None
        self._payload = None
        self._target = None
        self._stopping_capture = False
        self._delivery_attempted = False
        self._tts_chunks.clear()
        self._audio_sequence = 0
        self._tts_terminal = False
        self._job_voice = self._voice if kind == JobKind.READING else None
        return job

    def _start_recording(self, effects: list[Effect]) -> None:
        job = self._new_job(JobKind.DICTATION)
        self._recording_open = job
        self._state = State.STARTING
        effects.append(StartRecording(job))

    def _finish_job(self) -> None:
        self._job = None
        self._payload = None
        self._target = None
        self._job_voice = None
        self._selection_pending = None
        self._tts_chunks.clear()
        self._state = State.ERROR if self._error else State.IDLE

    def _cancel(self, effects: list[Effect]) -> None:
        job = self._job
        if job is None:
            self._pending_dictation = False
            return
        self._generation += 1
        self._cancelling = job
        self._job = None
        self._payload = None
        self._target = None
        self._job_voice = None
        self._selection_pending = None
        self._tts_chunks.clear()
        self._state = State.CANCELLING
        if job.kind == JobKind.READING:
            effects.extend((CancelSelection(job), ResetAudio(job)))
            self._audio_reset = job
        else:
            if self._recording_open == job:
                self._closing_capture = job
                effects.append(StopRecording(job, discard=True))
            if self._closing_delivery == job:
                effects.append(CancelDelivery(job))
        if self._slot and self._slot.job == job:
            effects.append(CancelEngine(self._slot))
        self._settle_cancel(effects)

    def _settle_cancel(self, effects: list[Effect]) -> None:
        job = self._cancelling
        if job is None:
            return
        if job.kind == JobKind.READING:
            if self._audio_reset == job:
                return
        elif (self._closing_capture == job or self._closing_delivery == job or
              (self._slot is not None and self._slot.job == job)):
            return
        self._cancelling = None
        self._state = State.ERROR if self._error else State.IDLE
        if self._pending_dictation and not self._audio_failed and not self._shutdown:
            self._pending_dictation = False
            self._start_recording(effects)

    def _fail(self, error: HuginError, phase: str, effects: list[Effect]) -> None:
        self._error = Failure(error.code, phase)
        self._pending_dictation = False
        self._cancel(effects)
        if self._cancelling is None:
            self._state = State.ERROR

    @staticmethod
    def _text_error(value: str, limit: int) -> HuginError | None:
        if not isinstance(value, str):
            return HuginError('protocol_invalid')
        if len(value) > limit:
            return HuginError('resource_limit')
        try:
            if len(value.encode('utf-8')) > limit:
                return HuginError('resource_limit')
        except UnicodeEncodeError:
            return HuginError('protocol_invalid')
        return None

    def _schedule(self, effects: list[Effect]) -> None:
        if self._shutdown or self._job is None or self._slot is not None or self._payload is None:
            return
        engine = Engine.STT if self._job.kind == JobKind.DICTATION else Engine.TTS
        component = self._components[engine]
        if component.blocked:
            self._fail(HuginError('worker_failed'), 'engine', effects)
            return
        if component.engine_instance is None:
            self._worker_number += 1
            component = Component(engine, f'{self._instance_id}:worker:{self._worker_number}', False, False)
            self._components[engine] = component
        action = (Action.TRANSCRIBE if engine == Engine.STT else Action.SYNTHESIZE) if component.ready else Action.INITIALIZE
        self._operation_number += 1
        operation = Operation(self._job, engine, component.engine_instance,
                              f'{self._instance_id}:operation:{self._operation_number}', action)
        self._slot = operation
        self._slot_result = False
        payload = None if action == Action.INITIALIZE else self._payload
        if action != Action.INITIALIZE:
            self._payload = None
        effects.append(BeginEngine(operation, payload, self._job_voice))

    @staticmethod
    def _split_selection(text: str) -> deque[str]:
        """Preserve content, preferring sentence then whitespace boundaries.

        Whitespace-only spans have no spoken content and need no engine call.
        Each scan examines at most 400 characters; a long token is split rather
        than silently truncated or sent beyond the worker's character bound.
        """
        chunks: deque[str] = deque()
        offset = 0
        while offset < len(text):
            end = min(offset + 400, len(text))
            window = text[offset:end]
            if end < len(text):
                sentence = list(re.finditer(r'[.!?]["\'”’\)\]]*\s+|\n+', window))
                whitespace = list(re.finditer(r'\s+', window)) if not sentence else []
                boundaries = sentence or whitespace
                if boundaries:
                    end = offset + boundaries[-1].end()
            chunk = text[offset:end]
            if chunk.strip():
                chunks.append(chunk)
            offset = end
        return chunks

    def _reduce(self, event: Event, effects: list[Effect]) -> None:
        if isinstance(event, Tick):
            self._validate_time(event.now)
            if event.now < self._now:
                raise HuginError('protocol_invalid', 'clock')
            self._now = float(event.now)
            if self._result and self._now >= self._result.expires_at:
                self._result = None
            return
        if isinstance(event, Shutdown):
            if not self._shutdown:
                self._shutdown = True
                self._pending_dictation = False
                self._cancel(effects)
                self._result = None
                for component in self._components.values():
                    if component.engine_instance:
                        effects.append(ShutdownEngine(component.engine, component.engine_instance))
            return
        if self._shutdown and not isinstance(event, (EngineTerminal, EngineExited, AudioReset,
                                                     RecordingStopped, DeliveryFinished)):
            return
        if isinstance(event, DictationToggle):
            if self._job and self._job.kind == JobKind.DICTATION:
                if self._state in (State.STARTING, State.RECORDING) and not self._stopping_capture:
                    self._stopping_capture = True
                    self._state = State.TRANSCRIBING
                    effects.append(StopRecording(self._job))
                else:
                    effects.append(Busy(JobKind.DICTATION))
            elif self._cancelling and self._cancelling.kind == JobKind.DICTATION:
                effects.append(Busy(JobKind.DICTATION))
            elif self._audio_failed:
                effects.append(Busy(JobKind.READING))
            elif self._job:
                self._cancel(effects)
                self._pending_dictation = True
            elif self._audio_reset:
                self._pending_dictation = True
            else:
                self._start_recording(effects)
            return
        if isinstance(event, ReadToggle):
            if self._job and self._job.kind == JobKind.READING:
                self._cancel(effects)
            elif self._job or self._cancelling or self._pending_dictation or self._audio_failed:
                effects.append(Busy(self._job.kind if self._job else self._cancelling.kind if self._cancelling else None))
            else:
                job = self._new_job(JobKind.READING)
                self._state = State.TTS_PREPARING
                self._selection_pending = job
                effects.append(CaptureSelection(job))
            return
        if isinstance(event, Cancel):
            self._cancel(effects)
            return
        if isinstance(event, VoiceSelected):
            if event.voice not in ('freya', 'tyr'):
                self._error = Failure('config_invalid', 'preferences')
                if self._job is None:
                    self._state = State.ERROR
            elif event.voice != self._voice:
                self._voice = event.voice
                if self._job and self._job.kind == JobKind.READING:
                    self._cancel(effects)
                effects.append(PersistVoice(self._voice))
            return
        if isinstance(event, RecordingStarted):
            if event.job == self._job and self._recording_open == event.job:
                if event.error:
                    self._recording_open = None
                    self._fail(event.error, 'capture', effects)
                elif not self._stopping_capture:
                    self._state = State.RECORDING
            return
        if isinstance(event, RecordingStopped):
            if event.job == self._closing_capture:
                self._closing_capture = None
                self._recording_open = None
                if event.error:
                    self._error = Failure(event.error.code, 'capture')
                self._settle_cancel(effects)
            elif event.job == self._job and self._stopping_capture and self._recording_open == event.job:
                self._recording_open = None
                if event.error:
                    self._fail(event.error, 'capture', effects)
                elif not isinstance(event.capture, bytes) or not event.capture or len(event.capture) % 2:
                    self._fail(HuginError('microphone_failed'), 'capture', effects)
                elif len(event.capture) > self.limits.capture_bytes:
                    self._fail(HuginError('capture_limit'), 'capture', effects)
                else:
                    self._payload = event.capture
                    self._target = event.target
                    self._schedule(effects)
            return
        if isinstance(event, SelectionReady):
            if event.job != self._job or event.job != self._selection_pending:
                return
            self._selection_pending = None
            error = event.error or self._text_error(event.text, self.limits.selection_bytes)
            if error:
                self._fail(error, 'selection', effects)
            elif not event.text.strip():
                self._fail(HuginError('selection_empty'), 'selection', effects)
            else:
                self._tts_chunks = self._split_selection(event.text)
                self._payload = self._tts_chunks.popleft()
                self._schedule(effects)
            return
        if isinstance(event, AudioReset):
            if event.job != self._audio_reset:
                return
            if not event.success:
                self._audio_failed = True
                self._pending_dictation = False
                self._error = Failure('audio_failed', 'audio')
                self._state = State.ERROR
            else:
                self._audio_reset = None
                self._audio_failed = False
                self._settle_cancel(effects)
            return
        if isinstance(event, AudioFinished):
            if (event.job == self._job and event.job.kind == JobKind.READING and
                    self._tts_terminal and type(event.through_sequence) is int and
                    event.through_sequence == self._audio_sequence):
                self._finish_job()
            return
        if isinstance(event, DeliveryCommit):
            if event.job == self._job and self._state == State.DELIVERING and not self._delivery_attempted:
                self._delivery_attempted = True
                if event.valid is True:
                    effects.append(DeliverText(event.job, event.transaction))
                else:
                    self._error = Failure('target_changed', 'delivery')
            return
        if isinstance(event, DeliveryFinished):
            if event.job != self._closing_delivery:
                return
            self._closing_delivery = None
            if event.error:
                self._error = Failure(event.error.code, 'delivery')
            if event.job == self._job:
                self._finish_job()
            else:
                self._settle_cancel(effects)
            return
        if isinstance(event, CopyResult):
            if self._result:
                effects.append(CopyText(self._result.text))
            return
        if isinstance(event, DeleteResult):
            self._result = None
            return
        if isinstance(event, EngineExited):
            component = self._components.get(event.engine)
            if component is None or component.engine_instance != event.engine_instance:
                return
            self._components[event.engine] = Component(event.engine, None, False, False)
            if self._slot and self._slot.engine == event.engine and self._slot.engine_instance == event.engine_instance:
                operation = self._slot
                self._slot = None
                if operation.job == self._job:
                    self._fail(HuginError('worker_failed'), 'engine', effects)
            self._settle_cancel(effects)
            self._schedule(effects)
            return
        if isinstance(event, (EngineReady, EngineResult, EngineAudio, EngineTerminal, EngineFault)):
            self._engine_event(event, effects)
            return
        raise HuginError('protocol_invalid', 'coordinator')

    def _engine_event(self, event: EngineReady | EngineResult | EngineAudio | EngineTerminal | EngineFault,
                      effects: list[Effect]) -> None:
        operation = event.operation
        if operation != self._slot:
            return
        current = operation.job == self._job
        component = self._components[operation.engine]
        if isinstance(event, EngineReady):
            if operation.action == Action.INITIALIZE and not component.blocked:
                self._components[operation.engine] = Component(operation.engine, operation.engine_instance, True, False)
            elif current:
                self._fail(HuginError('protocol_invalid'), 'engine', effects)
        elif isinstance(event, EngineFault):
            self._components[operation.engine] = Component(operation.engine, operation.engine_instance, False, True)
            if current:
                self._fail(event.error, 'engine', effects)
        elif isinstance(event, EngineTerminal):
            self._slot = None
            valid_terminal = (operation.action != Action.INITIALIZE or component.ready)
            if not valid_terminal:
                self._components[operation.engine] = Component(operation.engine, operation.engine_instance, False, True)
            if current and (event.success is not True or not valid_terminal or
                            operation.action == Action.TRANSCRIBE and not self._slot_result):
                self._components[operation.engine] = Component(operation.engine, operation.engine_instance, False, True)
                self._fail(HuginError('worker_failed' if not event.success else 'protocol_invalid'), 'engine', effects)
            elif current and operation.action == Action.SYNTHESIZE:
                if self._tts_chunks:
                    self._payload = self._tts_chunks.popleft()
                else:
                    self._tts_terminal = True
                    effects.append(DrainAudio(operation.job, self._audio_sequence))
            self._settle_cancel(effects)
            self._schedule(effects)
        elif not current:
            return
        elif isinstance(event, EngineResult):
            if operation.action != Action.TRANSCRIBE or self._state != State.TRANSCRIBING or self._slot_result:
                self._fail(HuginError('protocol_invalid'), 'engine', effects)
                return
            error = self._text_error(event.text, self.limits.transcript_bytes)
            if error:
                self._fail(error, 'result', effects)
                return
            self._slot_result = True
            self._result = ResultSlot(operation.job, event.text, self._now + self.limits.result_ttl_seconds)
            self._state = State.DELIVERING
            self._closing_delivery = operation.job
            effects.append(StageDelivery(operation.job, event.text, self._target))
            self._target = None
        elif isinstance(event, EngineAudio):
            if operation.action != Action.SYNTHESIZE or self._state not in (State.TTS_PREPARING, State.TTS_PLAYING):
                self._fail(HuginError('protocol_invalid'), 'engine', effects)
            elif not isinstance(event.pcm, bytes) or not event.pcm or len(event.pcm) % 2:
                self._fail(HuginError('protocol_invalid'), 'audio', effects)
            elif len(event.pcm) > self.limits.frame_bytes:
                self._fail(HuginError('resource_limit'), 'audio', effects)
            else:
                self._audio_sequence += 1
                self._state = State.TTS_PLAYING
                effects.append(PlayAudio(operation.job, event.pcm, self._audio_sequence))
