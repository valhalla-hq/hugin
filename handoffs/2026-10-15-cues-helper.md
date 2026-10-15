# Hugin IA-003/005 Cue Helper Handoff

## Objective and Git State

- Bounded helper for recording feedback/capture gate. Root owns integration,
  wider input/audio change, native acceptance and the running pilot.
- Repository: valhalla-hq/hugin. Branch: codex/hugin-cues-20261015-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-cues-20261015-mjolnir.
- Source commit: ac942eb6280792435e6e19c3d68528c86ea7a917.
- Base/spec:5a238677ce0ff915b141f313e7960434cf92ad28,
  specs/2026-10-15-hugin-input-audio/{spec,plan,tasks}.md.
- Preflight control e3deecae6673a024aa9015a4387737fbec04c795; deployment main
  bb700f0469dd3f75007041c430058c5bae368b47 was current at preflight.
- Workspace tool accepts only a remote branch as base: opened regularly from
  origin/codex/hugin-pilot-fixes-mjolnir, then approved ff-only to the exact spec.
- Source integrated by root as087afa16966a0ba160bb3a217ef6ac1edb46f49e.
  The bounded implementation and follow-up review are complete. Root's later
  endpoint/WASAPI source6f4897c16cec03ce37ae014f708271b5f7332f71 was independently
  reviewed; this historical helper source has not adopted that later code.
- Initial local-only instruction is superseded solely for the explicitly
  authorized private checkpoint, regular release and verified removal of this
  worktree/local branch. No helper PR/merge or runtime action is authorized.
  The remote branch must preserve the checkpoint before removal. These helper
  metadata files remain separate and should not be cherry-picked into root.

## Changed Files and Contract

- src/hugin/audio.py: per-stream buffer/gate/fault; start(armed=False),
  device_time, arm_after(absolute_device_time). Reject old/overlapping ADC
  blocks and unknown times. Explicit PortAudio cleanup error reporting;
  failed close retains the same microphone owner.
- src/hugin/cues.py: original54ms dark double pulse /52ms brighter end tone,
  PCM16 mono24kHz, soft edges, no external assets/dependencies. Own PCMOutput
  with100ms capacity, play(kind,job,cancelled), stop(job=None), close(),
  closed/cleanup_pending. Playback deadline0.5s; reset remains outside FIFO.
- src/hugin/application.py: optional cues DI, production composition,
  successful mic open unarmed -> cue/drain -> device cutoff -> started ACK.
  Normal mic stop/close -> end cue -> UIA -> stopped ACK/STT. Cancel/shutdown
  do not emit end cue; fast second toggle during STARTING cancels the start.
  End-cue failure reports a sanitized audio fault while preserving valid PCM.
  Cue cleanup is a real retained finish_io owner and diagnosis fact.
- tests/contracts/test_capture_cues.py:22 synthetic public-seam guards.
- tests/contracts/test_startup.py: composition/unwind includes the cue owner.
- No Coordinator, worker, configuration, UI or native Windows adapter changes.
  Application.run only imports/composes the cue owner; root's generic approval
  block is a separate integration concern.

## Verification

- Guard-first: initial12 missing-feature guards red before source. Additional
  timeout/False-start, concurrent reset-fact order, retired callback-fault,
  callback-abort during native start and suppressed PortAudio cleanup failures
  were independently red before their producing-boundary fixes.
- Base Python3.12, PYTHONPATH=src;tests/contracts, -B; no model/device loads.
- Full contracts+integration351 tests passed in19.499s. Final scoped capture,
  cues, PCM, controller and startup75 tests passed in0.390s; startup fixture
  now includes cue ownership and was rerun with the scoped group.
- tools/dev.py check --docs:19 requirements/17 AC, no problems.
- git diff --check passed. Self-review against IA-003/005 and ownership rules.
- Ruff unavailable in base Python; no package installed. Root can run its lint
  gate and independent integration review on the exact source commit.
- Final independent follow-up on fixed root6f4897c:66 simulated target/device/
  gate guards passed in0.238s, including the original endpoint repro and an
  independent clock-abort/failed-cleanup/retry guard. Own cues were excluded
  from the independent review. No hardware action was performed by this helper.

## Data, Running State and Remaining Limits

- Only original synthetic PCM and technical fixtures in source. Input audio
  stays in the existing bounded RAM buffer. No private samples/logs in Git.
- No actual playback, microphone, GPU, clipboard/input, UI or restart action.
  Simulated workers/isolated temporary offline restore fixtures were used by
  the existing source suite; no application/old-stack runtime was changed.
- Fixed25ms acoustic tail is provisional. Hearing distinction, real ADC clocks,
  echo/reverberation, initial-speech latency and native cleanup must be checked
  serially by root; no acoustic or physical success is claimed.
- Existing TTS immediate reset and retired GPU lifetime remain covered by the
  cue-enabled preemption guard; no change to TTS buffering/model scheduling.

## Pick Up Here / Starter Prompt

This helper task is complete. Continue the overall project only through the
accountable root task and its current handoff; do not restart this historical
implementation. Preserve this private remote checkpoint. Verify the central
released ownership record and final cleanup report before reusing any old path;
open a regular new exclusive worktree only for a new bounded request. No helper
PR/merge, native audio/GPU/input or pilot restart is authorized by this handoff.
