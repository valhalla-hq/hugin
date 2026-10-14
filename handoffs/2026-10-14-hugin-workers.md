# Hugin Engine Helper Handoff

## Objective

Bounded T005/T006 worker implementation for the accountable parent executor.
No helper integration, PR, activation, microphone use, playback or GPU model load.

## Git State

- Repository: private valhalla-hq/hugin.
- Branch: codex/hugin-workers-mjolnir, based on 9328f255980a5b896c3c7a356052a2b81bd25f20.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-workers-mjolnir.
- Parent: codex/hugin-v1-mjolnir. Parent owns overall integration/review.
- PR: none by bounded-helper instruction. Ownership remains active on Mjolnir.
- Preflight control: e3deecae6673a024aa9015a4387737fbec04c795, matching remote.

## Changed Files

- src/hugin/protocol.py: bounded JSON/binary framing, UUID/generation binding,
  ordered complete length/hash/UTF-8 transcript owner.
- src/hugin/workers/: private-pipe client/server, credit-controlled audio,
  separate cancel path, file-lock verification, native Whisper/Qwen parameters.
- docs/workers-api.md: public integration API and honest startup/cancel contract.
- tools/prepare_engines.py: write-free plan, additive copy/hash verification,
  new pinned venv preparation; divergent destinations fail without overwrite.
- locks/stt.txt, tts.txt, cuda.json, engines-provenance.json: transitive version
  pins and full copied CUDA DLL hashes; notice for Faster-Qwen3-TTS.
- tests/contracts/test_protocol.py and tests/integration/test_workers_simulated.py:
  malformed/framing/completion guards, cancel under backpressure, cleanup owner,
  stderr discard, and separate sentinel preservation.

## Verification

- Protocol guards initially failed for missing implementation, then passed.
- 11 contracts and 5 simulated worker tests passed; simulations do not establish
  provider behavior. Ruff F checks, doc check and diff whitespace check passed.
- Own STT/TTS package environments: 21/94 locked entries, pip check both passed.
- Own models: all six STT and eleven Qwen files verified before/after copying.
  Own CUDA: twelve DLLs, 1,796,257,072 bytes, fully SHA256-verified.
- Real CPU Whisper on two seconds generated silent PCM: load 7.243s, two warm
  completions 4.714/4.318s, offload/reload completion 4.428s, empty transcript.
  This verifies model loading/inference plumbing; speech accuracy is unverified.
- Real WorkerClient + private IPC + native held Windows Job Object: silent CPU
  inference/result/terminal/close passed in 7.995s with confirmed family exit.
  Windows process module was loaded read-only from the Windows helper worktree.
- Original command-reader placement before native initialization timed out at
  60s despite direct CPU engine success; synthetic transport over native job
  succeeded. A polling experiment did not establish a solution and was removed.
  Reading initialize synchronously, completing native warmup on the main thread,
  then starting the reader passed the same real public seam. Startup cancellation
  uses parent held-job watchdog. No helper worker remains running.
- GPU snapshot before preparation: 8188 MiB total, 4473 used, 3476 free. No GPU
  models loaded; Whispering/PipPal and their existing processes untouched.
- CPU time, process-family peak memory, token cost and GPU residency unmeasured.
  Timings are single probes, not a representative benchmark or performance claim.

## Runtime And Data Boundary

Own ignored runtime: this worktree's .runtime/{stt,tts,models/stt,models/tts,cuda}.
Environments are newly created, never moved. Models came from read-only old
local-tool directories; runtime code uses only Hugin-owned paths. No model
downloads, content logs, audio files, recordings or credentials added to Git.
TTS dependency closure includes Gradio because qwen-tts declares it; no HTTP
service is started. Package locks are exact version pins, not wheel hashes;
complete offline wheelhouse restore remains separate work.

## Open Verification

- Parent integration and independent review of unchanged helper commit.
- Native CUDA STT/Qwen, real streaming cancellation and startup watchdog cases.
- Combined VRAM, explicit residency/offload policy, both voices and listening.
- Synthetic speech recognition accuracy, final hardware and migration AC.
- Normal-user/offline restore with old paths inaccessible and complete wheelhouse.

## Starter Prompt

Continue the bounded Hugin worker helper from this exact handoff. Read AGENTS,
CONTEXT and docs/workers-api.md, verify branch/ownership/remote checkpoint, then
coordinate with the parent executor. Do not start a GPU model without the parent
scheduler's VRAM decision. Do not touch old processes, hooks, audio devices or
autostarts. Return helper changes to the parent; do not merge or release ownership.

## Restore Follow-Up Checkpoint

The parent explicitly requested a usable restore tool and preparation of its
runtime, then reviewed the diff before materialization. Changes are limited to
tools/restore.py, shared prepare_engines.py, file-lock owner assets.py, API docs,
restore guards and this helper's context/handoff. No tracked parent files written.

- Restore defaults to a write-free plan and requires initialized Hugin source
  and target checkouts. Source/target complete lock metadata and files must match;
  extra/different destination files fail before the first copy. Atomic new-file
  creation never replaces a concurrent destination. Expected failure codes are
  sanitized; raw exceptions are not printed.
- Engine environments are created in place with path/engine/pin ownership
  markers. Foreign/unmarked environments and changed installed versions fail
  closed. Repeated apply checks versions and pip consistency without reinstall.
  Model-lock parsing is owned by workers/assets.py and reused by both tools.
- Parent target: C:/Users/brian/brian-projects/worktrees/hugin/hugin-v1-mjolnir.
  Before apply effective free C: space: 543,585,005,568 bytes. Locked model/DLL
  copies total 5,934,025,392 bytes; environment reserve of 12 GiB was an explicit
  conservative estimate, not measured package cost.
- New parent .runtime/stt and .runtime/tts contain 21/94 exact pinned entries;
  both pip checks passed. Six STT, eleven Qwen and twelve CUDA files verified.
  Existing parent .runtime/controller and all old-stack files/processes untouched.
- 23 tests passed (11 contracts, 5 worker simulations, 7 restore guards), with
  doc check, Ruff F and whitespace checks. Restore guards were added before code
  and initially failed for missing implementation. Simulated environment tests
  cover single install, repeated verification, ownership refusal and model identity.
- Parent real CPU WorkerClient/private pipes/native Windows Job Object probe:
  approved Tyr reference, 6.48625s, mono PCM16, 22050 Hz converted to 16000 Hz only
  in test RAM. Ready 7.429s, inference 9.520s. Normalized reference/transcript:
  104 characters, 17 words, exact match, padded Hamming=0, character edit=0,
  word edit=0. No reference or transcript contents printed/stored. Worker family
  exit confirmed; independent sentinel remained alive and was then closed via
  its own held job. Single probe; CPU/family memory/token costs unmeasured.
- No GPU model load, microphone, playback, hotkey, autostart or old-stack change.
  Controller restore, cryptographic package hashes, complete offline wheelhouse
  and offline AC014 remain open. Online cache hits are not an offline proof.

After pushing this checkpoint, the parent requested a separate read-only
Standards review of its fixed head 8d604bb628898e96c2de5ecefee214356cdd040c.
Do not edit parent application/audio/UI/Windows files during that review.

## PCM Terminal Correction Checkpoint

Restore follow-up was pushed as de58d14893e5a743e74dbdad6e9cf0c50edc09e7.
The parent then requested a separate producer fix after discovering that the
client could complete a successful terminal before its final PCM callback.

- Root cause: `received` advanced before callback publication, and the control
  reader used that count to resolve terminal. It could retire the coordinator
  operation or start the next chunk before the last block was accepted.
- Structural fix: distinct per-request `received` and `accepted_audio` counts.
  Non-canceled terminal waits for declared PCM callbacks to return; receipt alone
  proves only framing. Cancellation bypasses the publication barrier, while
  declared framed bytes are drained before retiring identity. Returning stale
  callbacks never credit/increment a new request.
- Guard-first: last-callback and immediate next-chunk tests failed before the
  fix, then passed. Public simulated WorkerClient tests deliberately block the
  final callback, chain a new request from the terminal future, and cancel an
  old blocked callback before a new request. Existing cancellation remains
  independent of audio callback backpressure. These are simulation guarantees,
  not native Qwen/GPU coverage.
- 26 total source tests, docs, Ruff F and whitespace checks passed. No root
  edits, native actions, GPU model load, audio playback or microphone use.

Read-only Standards review at fixed parent 8d604bb628898e96c2de5ecefee214356cdd040c
found three root integration issues, all reproduced with Git-object code and
fake I/O only and delivered to the parent for correction:

1. P1 application.py:107-114/384: `_Closed` can be dropped when the event queue
   is full, permanently retaining `_closing` after the queue drains. Cleanup
   acknowledgements need bounded, non-lossy retention by resource owner.
2. P1 application.py:446-450: shutdown can cancel the queued microphone stop
   while a delayed start finishes, marking the controller closed while it still
   owns capture. Await the capture lifecycle cleanup barrier before closing.
3. P2 application.py:447-456 and windows/input.py:145-146: a sticky input error
   is re-raised after cleanup and prevents orderly shutdown indefinitely;
   startup finally also skips later owners after a first cleanup exception.
   Separate operational failure from remaining resource ownership.

Those root findings are not fixed in this helper. The accountable parent owns
their integration, re-review and native verification. Ownership remains active.

## Bounded T009 Signals Checkpoint

At the parent's request, merged fixed root 1a189d7b706afff3ba58705b0222f411290f1740
into the helper as 9c2cd05. Only CONTEXT conflicted; the helper's own checkpoint
context was retained. The subsequent source commit is the signal-only change
for the parent to cherry-pick, not the merge commit.

- New src/hugin/windows/signals.py: WindowsSignals(callback).start() creates
  an owned invisible top-level broadcast window on its own message thread.
  Parent HWND is None, not HWND_MESSAGE. Fresh UUID class name and retained
  module/window/class/callback ownership; no foreign WNDPROC replacement.
- A separate bounded dispatch thread emits only system_pause, system_resume
  and devices_changed. Native callback parses message kinds once, never reads
  lParam, and does no engine/mic/audio/clipboard/UI/input operation.
- ready/closed/error are distinct facts. close(timeout=2) bounds the combined
  cleanup/thread wait; cleanup runs on the original native owner thread. Failed
  DestroyWindow/UnregisterClass retains resources/callback for explicit retry.
  A healthy retained owner keeps pumping broadcasts; a failed native loop
  waits for recovery requests. No force-kill, owner search or hidden restart.
- Guards were added before source and first failed for missing module.
  Additional thread-start, dishonest-cleanup-return and native-callback exception
  guards failed before their fixes, then passed. Ten signal contracts and seven
  pure Win32 ABI/producer mocks passed. Full contracts+integration: 133 passed;
  docs, Ruff F and diff whitespace checks green. ABI mocks alone ran separately;
  the native/interactive Windows suite was not started.
- pystray 0.19.5 inspection found TaskbarCreated handling already built in:
  _win32.py mapping near46, _on_taskbarcreated near226 calls _show when visible,
  top-level window rationale near242; _util/win32.py registers near338. SHA256
  values are frozen in docs/system-signals.md. No extra Explorer code added.
- No actual native window, sleep/resume, device change, Explorer termination,
  microphone, playback or GPU model load. Old stack remains untouched.
- Application/UI wiring belongs to the parent. Actual broadcast delivery,
  controller invalidation/reopening, Modern Standby and Explorer restart need
  a controlled pilot. WM_DEVICECHANGE does not cover every default audio endpoint
  role change; the IMMNotificationClient contract is explicitly outside this
  bounded WM slice. Do not mark AC016 or all of T009 complete from these mocks.

Resume this helper using the same active ownership. Parent must cherry-pick the
last signal source commit, not merge the helper branch into the overall task.

## Bounded Default Audio Endpoint Follow-Up

Signals source checkpoint was pushed as 90cf52520ca20e5db137b6b149b8b9354a3a0cd0.
The next separate source commit adds default endpoint notifications; parent owns
Application/UI integration. This helper still owns its exclusive worktree.

- src/hugin/windows/audio_endpoints.py owns comtypes 1.4.17 MMDevice registration.
  SDK IIDs, method order and types come from primary Microsoft docs/mmdeviceapi.h;
  PROPERTYKEY is GUID/DWORD by value, LPCWSTR stays an opaque wchar pointer.
  Only OnDefaultDeviceChanged for render/capture and console/multimedia/
  communications emits devices_changed, including null default-device IDs.
  No enumeration, endpoint names/IDs, property lookup, settings, polling or streams.
- WindowsSignals now composes this owner on its original native thread; public
  start/ready/closed/error/close remain available. comtypes loads on start's caller
  thread, while the signal thread balances a separate explicit STA init. Native
  defaults require both window and endpoint registration; fake backend tests
  explicitly inject endpoints and never create native COM resources implicitly.
- MMDevice holds no callback reference: sink and exact QueryInterface pointer stay
  owned until unregister succeeds. Callback/enumerator release and CoUninitialize
  run on the original owner thread. Failed stages retain ownership for retry;
  cleanup success is separate from sticky operational error. Strong registries
  retain failed resources, but not an initialization failure with no resources.
- WindowsSignals close's combined deadline covers COM, window/class cleanup and
  both threads. A blocked COM unregister times out honestly, retaining its owner
  and wake window. Window cleanup follows COM cleanup. Closure facts are published
  before close acknowledgement, preventing a retry from racing successful cleanup.
- Guard-first: endpoint module contracts first failed missing-module; composition
  guards first failed absent endpoints API. Extra lifetime guard exposed stale
  notification closures retaining a successfully closed owner; disable now clears
  those application callback references. Twelve endpoint + sixteen signal
  contracts pass; full source suite 151 passed. Five fake COM ABI + seven fake
  Win32 ABI guards passed separately; Ruff F/docs/diff whitespace checked.
- Real read-only register/unregister with parent controller comtypes 1.4.17 passed.
  Reproducible test: tests/windows/test_audio_endpoints_native.py, opt-in
  HUGIN_ENDPOINT_READONLY_TESTS=1, PYTHONPATH=src. Its six default-change callbacks
  are synthetic invocations through the real COM vtable, not actual OS events.
  The test also invokes no-op ABI slots with a local synthetic string and observes
  its own thread exit. It performs no device query/change, mic/playback or GPU work.
- Separate Spec/Standards self-review used Code Review skill sequentially because
  parent forbids subagents. No unresolved source findings. Standard device switch
  delivery, parent invalidation/reopening, sleep/resume/Modern Standby and Explorer
  restart still require controlled pilot. Do not mark AC016/T009 complete.

Pick up using the same worktree and ownership. Parent should cherry-pick this
endpoint source commit after 90cf525; no root edits or process.py edits occurred.
Old Whispering/PipPal remain untouched and GPU load remains prohibited until the
parent coordinates the controlled pilot. Offline wheelhouse/controller restore
and genuine GPU/hearing/performance coverage remain open from earlier slices.
