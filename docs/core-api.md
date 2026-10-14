# Coordinator adapter contract

`hugin.coordinator` is deterministic and performs no I/O. The application owns
one serial event loop, constructs a fresh run identity (for example UUID4), and
executes the returned typed effects. UI and native callbacks enqueue events;
they do not call the reducer concurrently. No event or effect should be logged
with `repr`: recording, selection, transcript and audio payloads are private.

```python
core = Coordinator(instance_id=fresh_run_id, limits=Limits(),
                   default_voice="freya", now=time.monotonic())
core.dispatch(Tick(time.monotonic()))
effects = core.dispatch(DictationToggle())
view = core.snapshot()
```

`Limits` fields are `capture_bytes`, `transcript_bytes`, `selection_bytes`,
`frame_bytes`, `result_ttl_seconds`; use those names from `Settings.limits`.
`Snapshot` has `state`, `job`, `cancelling_job`, `generation`, `voice`, `result`,
`gpu_slot`, `retired_operations`, `components`, `error`, `escape_reserved`.
`ResultSlot(job, text, expires_at)` is the only retained finished transcript.
Send `Tick(now)` before handling queued events and at least periodically to
expire it. Snapshots/effects are immutable but consumers must drop their old
references on replacement, deletion, expiry and shutdown.

`Job(request_id, generation, kind)` identifies the complete user action;
`kind` is `JobKind.DICTATION` or `JobKind.READING`. Use `job.request_id` for
controller audio ownership. `Operation(job, engine, engine_instance,
request_id, action)` identifies one GPU operation; `engine` is `Engine.STT`
or `Engine.TTS`, `action` is `Action.INITIALIZE`, `TRANSCRIBE` or `SYNTHESIZE`.
Keep the exact operation with worker requests and normalized replies. Identity
comparison includes the full operation, not a PID, engine name or generation
alone.

| Input event | Adapter effects / acknowledgement |
| --- | --- |
| `DictationToggle()` | `StartRecording(job)` or `StopRecording(job, discard=False)`; the same event serves front mouse and Alt+Y. Busy processing emits `Busy(kind)`. |
| `ReadToggle()` | `CaptureSelection(job)` or cancellation; no selection work starts during dictation. |
| `Cancel()` | Invalidate the user job, request applicable cleanup and release Escape. |
| `VoiceSelected(voice)` | Exact IDs `freya`/`tyr`; emits `PersistVoice(voice)` and cancels active reading. |
| `RecordingStarted(job, error=None)` | Acknowledge start, changing `STARTING` to `RECORDING`; an error means no owned capture stream remains. A second toggle while starting still requests a stop. |
| `RecordingStopped(job, capture=None, target=None, error=None)` | Verified stream closure. Normal stop supplies bounded even-length PCM16/mono/16 kHz bytes and an opaque target identity captured at stop. Cancel closure discards any data. An error may report capture failure after closure; never send this event while the stream remains owned. |
| `SelectionReady(job, text, error=None)` | Only a current, newly captured selection. Empty selection fails; stale replies cannot schedule engines. |
| `EngineReady(operation)` | Valid only for initialization; readiness alone retains the GPU slot. |
| `EngineResult(operation, text)` | Only fully validated atomic STT text; emits `StageDelivery(job, text, target)` and replaces the RAM slot. Framing/UTF-8/hash validation belongs to IPC before this event. |
| `EngineAudio(operation, pcm)` | Validated 24 kHz mono PCM16 bytes; emits `PlayAudio(job, pcm, sequence)` with a monotonically increasing per-job audio sequence. The player owns bounded buffering/backpressure. |
| `EngineTerminal(operation, success=True)` | Verified end of this operation's native/GPU work and stream. Releases only its matching slot, including retired jobs. May emit the next `BeginEngine`. |
| `EngineFault(operation, error)` | `error` is `HuginError`; public failure keeps only its code and the reducer-owned phase. Resource ownership persists until terminal or verified exit. |
| `EngineExited(engine, engine_instance)` | Adapter has observed exit of its owned process/handle. Releases only that incarnation's resource; a foreign/stale identity does nothing. |
| `AudioReset(job, success=True)` | Reply to `ResetAudio(job)` only after confirmed stop/reset and queue discard. Failure retains the barrier and forbids microphone start. |
| `AudioFinished(job, through_sequence)` | Reply to `DrainAudio(job, through_sequence)` after all packets through that sequence have played. Early/old drains cannot complete a later chunk. |
| `DeliveryCommit(job, transaction, valid)` | Immediately before irreversible input, adapter revalidates target/caret plus its clipboard sequence/transaction. If still current and `valid is True`, emits one `DeliverText(job, transaction)`. |
| `DeliveryFinished(job, error=None)` | Delivery/clipboard cleanup is complete, whether inserted or suppressed. A cancelled delivery still needs this acknowledgement. |
| `CopyResult()` / `DeleteResult()` | `CopyText(text)` for an explicit copy; deletion only clears the RAM slot. |
| `Shutdown()` | Clears result/current job and emits necessary cleanup plus `ShutdownEngine(engine, engine_instance)`; retains outstanding ownership until acknowledged. |

`BeginEngine(operation, payload=None, voice=None)` is the only GPU-start effect.
Initialization has no payload; transcription has capture bytes; synthesis has
one selected-text chunk and its exact voice ID. The coordinator splits once
at selection receipt: prefer sentence, then whitespace boundaries, otherwise
split long tokens at 400 Python characters. Whitespace-only spans produce no
worker request; all spoken content remains. A single user job owns the whole
selection up to its byte limit. Each chunk has its own operation request ID,
and the next starts only after the preceding terminal. Do not split again in
the application. Keep the same output stream across chunks; do not reset the
player between them. The final terminal emits `DrainAudio(job, through_sequence)`;
run player drain, then acknowledge that exact sequence with `AudioFinished`.
Initialize and inference use the same
slot. After `EngineReady`, send the initialization terminal only when its native
work is finished. No model work may be started independently of this arbiter.
Worker chunking, cancellation/exit watchdogs, offload and recovery need their
adapter implementations; they are not simulated by the reducer.

`CancelEngine(operation)` requests independent worker cancellation;
`CancelSelection(job)` and `CancelDelivery(job)` cancel the clipboard owner's
transactions. `ResetAudio(job)` must be honored even before the first block.
The application must stop/remove queued payloads for a retired job: checking the
reducer before queuing a block does not authorize playing it after cancellation.
TTS cancellation allows a new microphone capture after `AudioReset`; old GPU
work retains its slot, so later STT waits for its own matching terminal/exit.
Dictation cancellation remains busy until capture/delivery and its engine
operation have closed. Cancel is never a GPU-release acknowledgement.

Consume `DeliverText` immediately on the same serial owner as `DeliveryCommit`;
do not queue it for a later thread. This is the serialized irreversible handoff.
Escape processed before that dispatch suppresses insertion; Escape afterwards
cannot promise undo. The clipboard owner still owns the final Windows checks
and platform limitations. Failed/uncertain delivery never retries itself and
keeps the successful transcript for manual copy.

`SetEscape(enabled)` changes the temporary Escape reservation. Surface native
registration failure through the application's input fault path. Reservation
is the first effect for a newly active job; if registration fails, cancel that
job and suppress its remaining start effects. Render status
from the complete snapshot after each event; component readiness is separate
from foreground state, so failed TTS does not globally disable capture. Error
states do not prove cleanup complete: inspect the retained job/slot/barrier.

Contract tests exercise reducer-visible races, not physical input, clipboard
preservation, actual audio silence, GPU memory, IPC framing or real providers.
Those remain T003–T010 integration/hardware gates.
