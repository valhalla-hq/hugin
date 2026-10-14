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
