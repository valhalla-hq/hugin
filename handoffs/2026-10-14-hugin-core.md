# Hugin Core Helper Handoff

## Objective

Return the bounded T002 coordinator implementation, explicit STT idle-offload
and the separately assigned cleanup-retry producer fix plus offline package
preparation/restore tools to the accountable parent for application integration
and independent review. Do not restart the overall
Hugin project or change productive Whispering/PipPal ownership.

## Git State

- Repository: `valhalla-hq/hugin`, private.
- Branch: `codex/hugin-core-mjolnir`.
- HEAD: the checkpoint containing this handoff; obtain the exact hash with `git rev-parse HEAD` and verify against `origin/codex/hugin-core-mjolnir`.
- Base/foundation: `9328f255980a5b896c3c7a356052a2b81bd25f20` from the accountable implementation branch.
- First core checkpoint: `72fbd99715eb52463b86e3d7063d499e434fb048`, already returned to parent. The next commit is the bounded offload delta only.
- Offload checkpoint: `915b37b1c7f0c2a3ca0bbdaee083bdee08975872`, integrated by parent. Parent checkpoint `1a189d7b706afff3ba58705b0222f411290f1740` was fast-forwarded into this worktree before the separate RetryCleanup delta.
- Cleanup producer checkpoint: `fa6141dd62fa372ebc87d17a50085389eedc199c`, returned separately. This checkpoint adds only the bounded offline preparation/restore scope after it; later parent commits are not in this helper base.
- Worktree: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-core-mjolnir`.
- PR: none for this helper, by bounded parent instruction.
- Ownership: active on Mjolnir; do not release until the parent coordinates cleanup.
- Authorization: bounded implementation and private checkpoint/push; no merge, publication, migration or deployment authority.
- Preflight/control: `e3deecae6673a024aa9015a4387737fbec04c795`, successful after establishing the newly opened remote helper branch at the unchanged foundation.

## Changed Files

- `src/hugin/coordinator.py`: deterministic `Coordinator(instance_id=..., limits=Limits(), default_voice='freya', now=..., stt_idle_unload_seconds=90)`, `dispatch(event) -> tuple[Effect, ...]`, `snapshot()`. `Action.OFFLOAD` uses `Operation.job=None` and the same GPU slot.
- `tests/contracts/test_coordinator.py`: 57 public-event guards, including 12 idle-offload/config/terminal/exit and six explicit cleanup-retry guards.
- `docs/core-api.md`: exact dataclass fields, adapter acknowledgements and trust/ownership boundaries.
- `CONTEXT.md` and this helper handoff: checkpoint metadata only.
- `tools/runtime_packages.py`: single owner of pins, wheel facts, source provenance, combined lock parsing, local hash requirements and validation.
- `tools/prepare_engines.py`: explicit online wheelhouse preparation, fixed-source builds with receipts, offline installation of controller/STT/TTS at their final paths.
- `tools/restore.py`: read-only plan default, full preflight before copy, additive local wheel/model/CUDA materialization and offline installation; separate `--wheelhouse-source`.
- `locks/runtime-wheels.json`: 122 exact artifacts (controller 7, STT 21, TTS 94), 3,205,420,299 bytes. `locks/controller-wheels.json` removed only after all seven original records matched; no secondary artifact truth. `locks/engines-provenance.json` points to the combined lock; no version pins changed.
- `tests/contracts/test_runtime_packages.py`, `tests/integration/test_workers_restore.py`: package identity/hash/platform/source facts and public plan/apply/owned-venv boundaries, including real fixture wheel installation.
- `docs/offline-restore.md`: preparation, offline Apply, prerequisites and evidence limits.

## Verification

Using `C:/Users/brian/AppData/Local/Python/pythoncore-3.12-64/python.exe` and `PYTHONPATH=src`:

- `-m unittest discover -s tests/contracts -p test_coordinator.py`: 57 pass; six retry guards started red for missing RetryCleanup before implementation.
- `tools/dev.py check --group all`: 146 pass (contracts, synthetic IPC/model fixtures and real tiny-wheel pip/venv installation, no GPU/model loads). New preflight, manifest and source-receipt guards started red, then passed after fixes; ambient pip-redirection and wheelhouse symlink-destination guards also began red.
- Synthetic adapter-seam probe: two failed reset attempts, later successful fast Quit stop leaves barrier without retry binding; dispatching RetryCleanup before Shutdown yields an identity-bound successful reset acknowledgement and `shutdown_ready=True`. Parent's actual adapter binding remains its own integration work.
- `tools/dev.py check --docs`: 19 requirements, 17 AC, no problems.
- `-m compileall -q src/hugin/coordinator.py tests/contracts/test_coordinator.py`: pass.
- `git diff --check`: pass.
- Self-inspection of public contracts, data references, producing selection boundary and affected scheduler consumers complete; parent independent review still required.

Offline artifact/probe evidence:

- All 122 actual wheel sizes/hashes and name/version/platform metadata validated against the combined lock; complete preparation repeat reports writes=false/downloads=false.
- Faster Qwen Git archive SHA256: `f205afd2dc972ab19939da67d5a25620f7c908afbc4068f4801d2a70ed86fe79`; wheel `faster_qwen3_tts-0.3.2-py3-none-any.whl`, 42,986 bytes, SHA256 `53c6ce5115c0bf6256e90bf1f906e236b352eae2bc7b0459c4a40cd5bbb15d0e`.
- Sox 1.5.0 sdist SHA256: `12c7be5bb1f548d891fe11e82c08cf5f1a1d74e225298f60082e5aeb2469ada0`; wheel `sox-1.5.0-py3-none-any.whl`, 40,166 bytes, SHA256 `5818e173112fff80202b437da1ab114d1deb838b25a935aeb66fcf10cd8a2ad4`. Source-only upstream release required this second bounded build.
- Both source wheels independently rebuilt to identical SHA256 using setuptools 78.1.0, wheel 0.45.1 and SOURCE_DATE_EPOCH=315532800. These are same-machine rebuild observations, not cross-platform reproducibility claims.
- Fresh `.runtime/offline-full-probe/target` installed all three real-wheel profiles, exact metadata and pip check passed. First plan/apply: 266.20s; repeat Apply: 22.16s with unchanged proof mtimes. 39 child Python processes loaded a socket block; zero network attempts. Python 3.12.10 x64/Tk 8.6 verified. Model/CUDA bytes were synthetic 25-byte fixtures. No Torch/Qwen/Whisper model imports or inference.
- Final isolated/no-cache pip call separately reinstalled the seven controller wheels under a root/child socket block and intentionally divergent ambient PIP_TARGET/config: 7.08s, correct in-place target, no foreign install, zero network attempts. Complete fixture suite also exercises the final call.
- Ignored scripts/results: `.runtime/offline_full_probe.py`, `.runtime/offline-full-probe/result.json`, `.runtime/offline_recheck.py`, `.runtime/offline-full-probe/recheck-result.json`, `.runtime/rebuild_sources_probe.py`, `.runtime/source-rebuild-probe/result.json`. Logs and binaries are not committed. Wall time observed; CPU, process-family peak memory and cross-machine restore unmeasured here. No equivalent old offline workflow existed for a before/after comparison.

## Source And Data Boundary

Only private source, synthetic fixtures and curated API/context documentation.
No speech content, real recordings, model weights, credentials, raw logs or
runtime binaries added to Git. No files outside the delegated core and
offline preparation/restore scope changed.

## Running State

No helper service, microphone, hook, model or audio output started. Existing
Whispering/PipPal left untouched. GPU and playback in tests are typed event
sequences, not real-provider evidence.

## Open Blockers / Required Parent Work

- No blocker for reviewing/integrating this helper result.
- Wheelhouse exists only in this helper's ignored `.runtime/wheelhouse`; Git stores hashes/provenance, not 3.2GB binaries. Parent can supply this directory via `--wheelhouse-source` after integrating the source, while `--source-root` names its separately verified Hugin model/CUDA checkout. No old installation paths are read by restore.
- Restore fails closed for an existing unowned environment; it does not silently adopt or move it. Base Python/Tk remains a checked prerequisite. Offline packages are verified; real-model offline copy/inference and native provider dependencies (including external Sox when used) remain separate gates.
- Parent must bind `RetryCleanup()` before explicit Quit/Shutdown. It remains allowed during STOPPING, suppresses pending dictation, and reissues only held ResetAudio/StopRecording(discard=True). No actual cleanup proof is implied by retry; GPU lifetime and delivery are unchanged. Serial capture tasks and verified acknowledgements stay with the adapter.
- Run identity must be freshly generated by the application; all dispatch and irreversible `DeliverText` execution share one serial owner.
- `SetEscape(True)` is the first start effect; registration failure must cancel the job and suppress remaining start effects.
- Only `BeginEngine` authorizes initialization/inference/offload. `EngineReady` does not release its slot; verified `EngineTerminal` or owned `EngineExited` does. Watchdogs, bounded process cleanup, offload execution and recovery remain adapter work.
- Offload contract was agreed with the parent after read-only inspection of `hugin-workers-mjolnir/src/hugin/workers/client.py`, `engines.py`, `server.py` and `docs/workers-api.md`. Constructor interval comes from `Settings.stt['idle_unload_seconds']` (initially 90), separate from Limits. Tick requires no active/cancelling user job, cleanup barrier or GPU slot. Maintenance has no user generation and is shown only in gpu_slot. Bind the exact authorized operation to the pool's offload Future and verify the actual incarnation; never reinterpret foreign terminals. Successful offload preserves STT readiness because next scheduled transcription reloads inside its own operation. Failure retains ownership until terminal/exit, blocks retry, and cannot overlap newer inference. No worker code or GPU invocation changed here.
- Core splits TTS selection once into <=400-character chunks with distinct operation IDs under one user job. Keep player open between chunks. Final terminal emits `DrainAudio(job, through_sequence)`; acknowledge exact sequence after player drain via `AudioFinished`.
- `ResetAudio` must produce confirmed `AudioReset` before microphone start. Failed reset retains the barrier. Stale payloads cannot be played from application queues after retirement.
- Clipboard owner proves current target/caret and transaction/sequence at `DeliveryCommit`. Consume its returned `DeliverText` immediately; finish/ack cleanup even after cancellation. Failed/uncertain delivery has no retry.
- Snapshot/effect consumers must drop old content references on replacement, TTL, delete and shutdown. Feed monotonic `Tick` before events and periodically.
- Physical input, actual silence, clipboard formats/targets, IPC framing/hash, real engines, CPU/RAM/VRAM, latency and full AC remain unverified here.

## Pick Up Here

1. Parent reviews the exact additional helper diff after `fa6141dd62fa372ebc87d17a50085389eedc199c` and integrates only this delegated offline delta plus appropriate curated context. Core/offload/cleanup checkpoints were already returned separately.
2. Bind application adapters to `docs/core-api.md`, then run public integration guards and the later real/hardware gates.
3. Preserve the parent's overall `handoffs/2026-10-14-hugin-v1.md` as the accountable project handoff; coordinate helper ownership cleanup later.
4. Use docs/offline-restore.md for the read-only plan and explicit Apply. Actual model/CUDA bytes must come from a verified Hugin-owned runtime; this helper's full package probe deliberately used synthetic model bytes. Preserve normal launch gating and remaining T009/native acceptance work.

## Starter Prompt

Continue the bounded core helper in `valhalla-hq/hugin` from
`handoffs/2026-10-14-hugin-core.md`. Read `AGENTS.md`, `CONTEXT.md`, this exact
handoff, `docs/core-api.md` and `docs/offline-restore.md`; verify branch, remote head and active ownership
before mutation. The parent owns overall integration, review, PR and completion.
Do not activate production inputs or touch the old Whispering/PipPal stack.
