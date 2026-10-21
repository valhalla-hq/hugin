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
- Independent spec and standards reviews found no material issues; final hosted
  checks and integration follow this checkpoint.

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
- Full live button dictation/reading in Codex and Word remains a separate check.
- Original reported physical shortcut failure remains unexplained; prior PR25
  synthetic Windows-input tests passed. No claim of a new shortcut fix.

## Running source and recovery

Previous PR25 source is 0e283ac3ded9e34e34514ce8af884500fc5e47e7 in
C:/Users/brian/brian-projects/worktrees/hugin/hugin-panel-stop-mjolnir.
Its .runtime/pilot-session-e9462fe7-0c69-4eb2-ba0f-d6b1cb1cf343.json now proves
session_exited, exit_code 0, own_family_exited true and started_shortcuts empty.
No further Quit request is needed before the next checked start. Fresh receipts
govern later live state, never historical PIDs.
C:/Users/brian/Hugin is the clean deployment junction at base 392977f2fc824dff30522f645156bc855bc0bf26.
Keep worker/runtime/model/asset inputs identical. tools/pilot_session.py exits
without starting Whispering or PipPal. Never replay old auto-return helpers.

## Pickup

Read AGENTS.md, CONTEXT.md and this exact handoff. Finish independent reviews,
exact-head checks and authorized integration. The previous pilot already exited;
advance deployment and run the checked starter with exact source/runtime heads.
Then request the real button dictation/reading check. Keep live source frozen
until orderly exit. Do not persist raw dictation, diagnostics or trace logs.
