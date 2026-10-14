# Engine client contract

`hugin.workers.EnginePool(root: Path, callback, *, spawn=None)` starts no
process implicitly. `start(engine='stt'|'tts', *, device=None)` starts one
worker and returns `Future[ready_event]`. The future completes only after the
initialization terminal proves native work synchronized. Use `device='cpu'`
only for an explicit Whisper CPU probe. Qwen requires CUDA.

The parent serializes **all** initialization, inference, and STT offload through
its GPU owner. Worker readiness is separate from user-action state. No worker
spontaneously reloads/offloads outside a scheduled operation. The parent can
schedule `offload('stt')` after 90 idle seconds; the next `transcribe` reloads
inside that scheduled operation. Qwen offload uses a fully observed worker
exit/restart, not a partial model-unload claim.

```python
pool = EnginePool(root, on_event)
ready = pool.start('stt').result(timeout=60)  # outside input/UI thread
job = pool.transcribe(pcm_bytes, request_id=str(uuid.uuid4()), generation=1)
pool.cancel('stt', request_id, 1)
terminal = job.result(timeout=2)
pool.close()
```

`transcribe(pcm: bytes, request_id: canonical UUID str, generation: int)`
accepts PCM16 little endian / mono / 16 kHz, nonempty, frame aligned, at most
the configured capture budget. Submission returns a terminal future; hashing
and input pipe writes run on a transfer thread. `synthesize(text, voice,
request_id, generation, language=None)` accepts nonblank text up to 600
characters, voice `freya` or `tyr`, language `German` or `English` (default
configuration). The parent splits selections at sentence boundaries to at
most 400 characters. Neither worker records audio/text or plays audio.

Callbacks receive dictionaries. They run on reader threads and must safely
enqueue to the controller/UI. Every event has `type`, `engine`,
`engine_instance`, `request_id`, and `generation`:

- `ready`: `device`, `sample_rate`.
- `audio`: `pcm: bytes`, `sample_rate=24000`, `offset` (byte offset).
- `result`: complete verified `text`; partial transcript data is never exposed.
- `terminal`: `cancelled`, `code` (nullable), `audio_bytes`, `elapsed_seconds`.
- `fault`: sanitized `code`, `phase`, `retry`; no raw native messages.

An audio callback may wait until the parent's bounded player accepts the
fragment. It must return after cancellation stops the player. At most one
credit-controlled fragment (at most 6000 bytes, half the configured audio time
budget) is outstanding; no unbounded client audio queue exists. The parent
allocates the other half to its native player, making their combined budget
at most 12000 bytes / 250 ms initially. Cancellation has its own
control pipe and wakes the worker's credit wait independently of audio. The
parent must still reject stale generations at its audio/text boundaries.
Normal terminal futures wait until every declared PCM byte has completed its
audio callback. Framing receipt and completed callback publication are separate
per-request counts, so a terminal cannot retire the final block before the
controller accepts it. A canceled terminal bypasses that publication wait;
returning stale callbacks cannot credit or acknowledge a newer request.
`cancel(engine, request_id, generation)` is identity matched and returns bool.
It invalidates client transcript drafts immediately. It does not assert native
work has stopped. Only a matching terminal or observed family exit releases
the scheduler slot. Stream close plus native GPU synchronization precede
terminal. A failed synchronization sends a fault and exits without terminal.
Initialization reads its first command synchronously and completes native
DLL/model warmup before starting the command-reader thread, following the
reproduced Windows initialization boundary. Cancellation during initialization
therefore uses the parent's held-job startup watchdog and confirmed family
exit; an in-process initialization-cancel acknowledgement is not promised.

`WorkerClient(root, engine, callback, *, spawn=None, command=None)` exposes the
same per-worker methods and `.process`, `.engine_instance`, `.ready`, `.device`.
`spawn` is a Popen-compatible own-family factory. On Windows the default is
`hugin.windows.process.OwnedProcess`, creating the process suspended and
assigning it to a held Job Object before resume. The parent can inject its
factory. `command` is an explicit alternate launcher for protocol simulations;
the production default is the corresponding Hugin `.runtime/stt` or
`.runtime/tts` interpreter and `-m hugin.workers.server`.

`close()` requests cancel/shutdown, waits the configured two seconds, then
terminates only the held own-family job and waits up to five seconds. Cleanup
failure retains `.process` ownership and raises `worker_timeout`. No PID/path
enumeration or foreign-process cleanup is performed. The controller owns the
60-second ready and two-second active-job watchdogs; no hidden restart loop is
provided. Each worker has a fresh engine-instance UUID.

Control JSON is length-prefixed UTF-8 capped at 64 KiB before parse. Anonymous
binary pipes use fixed validated headers with kind, identity, offset, and body
length capped at 64 KiB. Each framing stream has one writer lock. STT input
declares full PCM length/hash. Transcript begin/contiguous fragments/end verify
UTF-8, length, and SHA256 atomically up to 256 KiB. Stderr drains in fixed 4 KiB
chunks and is discarded entirely; raw output is never retained as diagnostics.

Worker operation locals end before GPU synchronization and terminal publication:
provider text, encoded transcript bytes, PCM chunks and closed generators do not
survive into the next idle Queue.get. Consumed command dictionaries are cleared
at their owning operation boundary, including failure paths. The command reader
transfers ownership into the bounded queue and drops its own reference before
reading another command. Input frames end their scope after copying into the
active capture draft, before the next frame read.

Client control-event and data-frame processing each have a short scope ending
before their next blocking read. A completed frame or callback publication does
not remain in reader-loop locals while idle. The active transcript draft is
cleared on cancellation/terminal. Results deliberately retained by the caller,
including the controller's one RAM slot, remain that caller's responsibility.
An executing callback may still own its in-flight argument until it returns;
cancel remains independent of a blocked audio callback. These are Python object
lifetime guarantees, not a claim of secure allocator erasure or verified native
provider-cache clearing.

Tests using injected synthetic engines establish IPC behavior only. Real CPU
Whisper, GPU Whisper, Qwen, cancellation under native CUDA work, both-voice
listening and combined GPU residency require separate explicit evidence.

## Runtime restore

Run `tools/restore.py --target C:/path/to/Hugin-checkout --source-root
C:/path/to/verified-Hugin-checkout` to inspect a read-only plan. Both roots
must already contain Hugin configuration, voices and matching file locks from
Git. Sources are the selected checkout's owned model/CUDA files; no old-stack
paths or model downloads are built into restore. Add `--apply` to copy only
missing locked files and create new STT/TTS environments at the destination.
`--install none` copies model/DLL files only. Existing differing bytes,
unlocked files, unowned environments or changed package pins fail closed.
The target's tracked files and controller environment remain untouched.

New engine environments carry `hugin-environment.json` binding their path,
engine and pins. Repeated apply verifies installed distribution versions and
runs pip check without reinstalling correct packages. Older unmarked
environments require separately reviewed adoption; restore does not assume
ownership from matching package versions. A complete controller restore and
offline wheelhouse with cryptographic package hashes remain open. Cache hits
in an online installation do not establish an offline restore.
