# Panel stop and quiet test exit handoff

## Objective and authorization

Fix Brian's button-started recording that would not stop. Explicit latest request:
remove automatic Whispering/PipPal restart after Hugin during tests. Routine
private implementation/integration under the central lifecycle is authorized.
No login startup changes, stored external target or forced foreground restore.

## Git state

- Repository: private valhalla-hq/hugin; runtime Mjolnir.
- Branch: codex/hugin-panel-stop-mjolnir; base ad9b0a083c0472eda06fc42546f88fccca9eea9f.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-panel-stop-mjolnir.
- Control/preflight: e3deecae6673a024aa9015a4387737fbec04c795.
- Ownership active; exact checkpoint and PR resolved from fresh remote state.
- Spec/plan/tasks: specs/2026-10-21-panel-stop/.

## Findings and change

Live UI showed the finish guard's own-foreground hint; no command was sent.
The stopped pilot's last-input timestamp did not reflect later shortcut attempts.
Normal tray Quit succeeded. Native regression reproduced the finish guard failure
before removal and passed afterward. Only read start now uses the UI foreground
guard. The existing controller stops the microphone, transcribes, and retains
text without delivery when target proof fails. A new controller test verifies it.

The separate reported physical-key failure remains unexplained. Two new native
message-loop/controller tests pass, and Windows key injection into an own Hugin
synthetic-I/O window successfully finished via Ctrl+Alt+D and cancelled via
Escape. Button finish also worked while Hugin was foreground. No speculative
keyboard, focus-history or external-window mutations were introduced.

tools/pilot_session.py replaces the local auto-return helpers. It validates the
exact clean source/runtime and identical worker inputs, keeps the existing
OwnedProcess family owner, records bounded session facts and starts no old app.
Cleanup failures retain the owner and retry. Manual old-app startup is the return.
Old local auto-return helpers must not be replayed.

## Verification

- Full contracts/integration: 481 tests, 22.888 s, passed.
- Focused launcher contracts after cleanup refinement: 3 passed.
- Native UI/focus/geometry/motion: 26 tests, 11.006 s, passed.
- Native input dispatch: 2 tests, 0.133 s, passed; posted messages are not physical keys.
- Real owned-child launcher exit: 1 test, 0.063 s, passed; no old-app dispatch.
- Separate synthetic UI via Windows input: button finish, Ctrl+Alt+D, Escape passed;
  temporary fixture is closed. No microphone, models or private clipboard used.
- Docs validator: 19 requirements/17 AC, no problems; whitespace check clean.
- Independent review and exact-head hosted checks pending at this checkpoint.

## Running and data boundary

Previous PR24 source 751f088241f0d8e1403ba7737225c397df430b10 is stopped. Its
.runtime/pilot-session-c29822b6-6ef2-4f0f-bc18-2159534d4b00.json proves own-family
exit, code 0 and historical old-app return. Brian closed both returned apps.
C:/Users/brian/Hugin is the deployment junction; retain byte-identical worker,
model, environment and asset inputs. No personal text, recording, screenshot,
credentials or raw logs in Git. Ignored fixture/log files remain local recovery
evidence. No test process remains active. A later fresh receipt supersedes this.

## Pickup and starter

Read AGENTS.md, CONTEXT.md and this handoff. Complete separate reviews, exact-head
CI and checked private integration. Advance deployment, plan tools/pilot_session.py
with exact source and runtime commits, then start with --run. Do not ask Brian to
close returned apps again: the new launcher never returns them. Verify actual
mouse finish and keyboard behavior with Brian before claiming acceptance. Keep
live source frozen and ownership active until orderly exit and remote release.
