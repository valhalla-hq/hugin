# Physical button target handoff

## Objective and state

Fix button dictation that stops but cannot capture the Codex field. This is the
authorized continuation of Brian's panel-button request, with checked private
integration. No target history, external focus restoration or clipboard bypass.

- Private repository valhalla-hq/hugin, runtime Mjolnir.
- Base 392977f2fc824dff30522f645156bc855bc0bf26 (merged PR25).
- Branch codex/hugin-button-target-mjolnir.
- Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-button-target-mjolnir.
- Control/preflight e3deecae6673a024aa9015a4387737fbec04c795; ownership active.
- Spec/plan/tasks: specs/2026-10-21-button-target/.
- PR https://github.com/valhalla-hq/hugin/pull/26; resolve head/checks freshly.
- Independent spec and standards reviews found no material issues. Hosted runs
  39599004831, 39598999791 and 39599004686 passed for source
  379df037d1567f9ea3882f1f0e07902dd4d416e5. PR26 merged at 12:23:11 UTC on
  21 October 2026 as e15205f303bc1e47ae37c1e46253b5e56519c5bb.
- Acceptance documentation uses the separate branch
  codex/hugin-button-acceptance-mjolnir in
  C:/Users/brian/brian-projects/worktrees/hugin/hugin-button-acceptance-mjolnir.

## Evidence and structural fix

Latest diagnosis: capture_native target_unverifiable, field/delivery not attempted.
The screenshot clipboard fix is unrelated. A technical-only physical Codex-to-
Hugin click probe reproduced GetForegroundWindow NULL already inside the button's
WM_MOUSEACTIVATE, continuing through release and 500 ms later. Child suppression
alone did not preserve the other application's foreground. The same physical
probe with top-level WS_EX_NOACTIVATE|WS_EX_APPWINDOW preserved the Codex field
and native capture succeeded immediately, after 100 ms and after 500 ms.

ActionFocus now owns wrapper protection before showing the UI. Child actions
retain MA_NOACTIVATE; ordinary clicks forwarded to the wrapper explicitly activate
only Hugin. Taskbar entry remains. Cleanup removes only its added style bits,
preserves other bits and retains the native owner on failed restoration/removal.
The existing stop-without-target behavior, command generations, clipboard and
selection/delivery proofs remain unchanged. No delays or cached targets added.

## Verification and limits

- 483 contracts/integration pass in 26.496 s.
- 32 native UI/focus/geometry/motion checks pass in 12.818 s.
- Docs validator: 19 requirements/17 AC, no problems; whitespace clean.
- Independent spec review: 23 focused pure checks; standards review: 61 focused
  pure checks; no material findings. Neither review repeated physical UI input.
- Physical probe red/green as above; no audio, transcription or clipboard payload.
- Background native tests could not activate their own source fixture because
  Windows rejected SetForegroundWindow. A click-activated own harness passed.
- An unrelated composition-style bit made an early test hang; the owned exec
  session was cancelled. The restoration test now uses the inert accept-files
  bit. All fixtures and the successful harness are closed.
- Brian's repeated live tests on 21 October confirm dictation/insertion, reading,
  stopping, and dictation interrupting reading before recording starts. The
  reported panel flow is accepted; no additional Word/device matrix is claimed.
- Original reported physical shortcut failure remains unexplained; prior PR25
  synthetic Windows-input tests passed. No claim of a new shortcut fix.

## Running source and recovery

Previous PR25 source is 0e283ac3ded9e34e34514ce8af884500fc5e47e7 in
C:/Users/brian/brian-projects/worktrees/hugin/hugin-panel-stop-mjolnir.
Its .runtime/pilot-session-e9462fe7-0c69-4eb2-ba0f-d6b1cb1cf343.json now proves
session_exited, exit_code 0, own_family_exited true and started_shortcuts empty.
The accepted pilot is now running from source
379df037d1567f9ea3882f1f0e07902dd4d416e5 in hugin-button-target-mjolnir, with
receipt .runtime/pilot-session-e02be514-5fb9-412b-82ee-57f7f0bdb4bf.json.
Fresh receipts govern later live state, never historical PIDs. The documentation
update does not restart or change this source. C:/Users/brian/Hugin remains the
deployment junction; this session started against e15205f303bc1e47ae37c1e46253b5e56519c5bb.
Keep worker/runtime/model/asset inputs identical. tools/pilot_session.py exits
without starting Whispering or PipPal. Never replay old auto-return helpers.

## Pickup

Read AGENTS.md, CONTEXT.md and this exact handoff. The requested button correction
is accepted; no further test or restart is required for it. Keep the running
source frozen and use a new exclusive worktree for any future enhancement.
Revalidate exact source/runtime heads before a later checked pilot start.
Do not persist raw dictation, diagnostics or trace logs.
