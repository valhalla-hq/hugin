# Hugin: aktueller Cursor statt früherer Feldbindung

- Repository: valhalla-hq/hugin, private; runtime Mjolnir.
- Task: current-cursor-delivery; ownership active.
- Branch: codex/current-cursor-delivery-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/current-cursor-delivery-mjolnir.
- Base: e82e9a625f897a0eda33479637a3a802bd2d2636.
- Control/preflight:46e362d1d3284d712757fc2f0e67a165dbf3a41c, current.
- PR: create Draft after this meaningful checkpoint; exact branch only.
- Spec/plan/tasks: specs/2026-10-23-current-cursor/.
- Evidence/limits: docs/current-cursor-2026-10-23.md.

Brian requests reliable insertion at the current cursor despite target switches
and comparison with Whispering. Diagnose supplied23October: native capture,
UIA target_unverifiable, clipboard copied, no paste. Parallel technical samples
show transient non-text Codex focus and later valid Edit; do not claim the
specific failed internal sample was captured. No raw text/images/audio retained.
Whispering pinned source confirmed clipboard + current-focus Ctrl+V.

Implemented source candidate1.0.1: no stop-target transport, current native
focus selected on the serial commit owner after the queue, no UIA delivery gate.
Removed obsolete field proof/protocol; reading's selection reader remains.
Clipboard generation/transaction/token, cancel, modifiers, one-shot/partial
input and native focus guards preserved. config v3=current_focus; no preference
or activation migration. Tests now express the newly requested semantics.

Regression was red before production changes (no chord after window switch)
and green afterwards. Focused128 tests and33 selection/policy tests passed;
29 mocked Win32 ABI tests passed. Current-cursor/native focused12 pass.
First full run524 cases found stale fake signatures, a remaining removed
target-mode decoder and HEAD-export/config mismatch; corrections are being
verified, not a green full claim yet. Full/native checks and independent review
still pending. No1.0.1 runtime/build has been installed or started.

Earlier installed1.0.0 remains unchanged at
C:/Users/brian/AppData/Local/Programs/Hugin/releases/1.0.0-3b6bc4304a87.
Immutable installer/build/rollback evidence remains under
C:/Users/brian/Hugin-Releases/1.0.0-3b6bc4304a87.
Whispering/PipPal stay disabled. Do not quit a live user app by remembered PID.
Normal Hugin Quit is required before a later update switches the installed app.
No logout, reboot, unrelated installation or new scheduler.

Separate open Save: PR49 / codex/input-login-acceptance-mjolnir at
e9e59a66f52e7bc2c49b60967d1d1451e8c7e72c contains Brian's manual restart and
four successful physical mouse/hotkey flows on22October. Keep its worktree and
ownership untouched. That did not prove a new Windows login; login stays open.

Next: finish full/native current-cursor guards, independently review, build
additive1.0.1 from clean pinned source, preserve1.0.0/preferences/startup/profile,
then switch only after normal Quit and request physical Codex switching check.
Routine checked private integration is within this fix request; no check bypass.
Paste still relies on target consumption of Ctrl+V and does not claim all apps.

Starter: continue this exact current-cursor-delivery handoff, inspect Git/PR
and ownership, finish the bounded cursor fix. Do not resume old production work
or confuse PR49's successful manual restart with Windows-login evidence.
