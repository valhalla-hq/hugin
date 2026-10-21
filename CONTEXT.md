# Hugin Context

Status: accepted panel baseline; persistent mouse/startup migration in progress.
Owner: Brian. Private repository valhalla-hq/hugin; runtime Mjolnir.
Data boundary: curated source/configuration/locks and approved synthetic voice
references only. No raw dictation, clipboard/image content, recordings,
credentials, model weights, virtual environments or local startup backups in Git.

## Current objective and authorization

Brian confirmed repeated successful dictation/insertion, reading, stopping and
switching from reading to dictation with the PR26 panel buttons. PR26 and its
PR27 acceptance record are merged. Main is
460534fff76741427f6c380405916be1c7947f10.

He now explicitly requests permanent mouse Back/XBUTTON1 = dictation and
Forward/XBUTTON2 = reading, removing PipPal/Whispering login startup, and
confirms Hugin should start silently after login. This supersedes the old
opposite mouse mapping, Alt+Y and previous no-migration restrictions.
Ctrl+Alt+D/V remain additional controls; existing panel buttons remain.
Complete routine private integration and the requested Windows setup after
checks/review. Production packaging follows this prerequisite; do not equate
this increment with the entire V1 acceptance matrix.

## Active work and handoff

- Branch: codex/hugin-mouse-startup-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-mouse-startup-mjolnir.
- Base: 460534fff76741427f6c380405916be1c7947f10.
- Control/preflight: e3deecae6673a024aa9015a4387737fbec04c795.
- Ownership: active; no live runtime is started from this worktree yet.
- Active handoff: `handoffs/2026-10-21-mouse-startup.md`.
- Spec/plan/tasks: specs/2026-10-21-mouse-startup/.

One binding definition owns dispatch and hints; strict read-only activation
permits normal desktop launches. Explicit keyboard pilots cannot reset it.
Setup has a read-only hash-pinned plan, exact backups, idempotent apply/restore,
and only the two named old links plus the new Hugin link/activation as targets.
No registry/Logitech writes, package/model installs, global target history or
external focus restoration. Preserve the accepted clipboard/focus corrections.
Final checks: 494 contracts/integration, 20.721 s; native shortcut roundtrip,
3 ownership checks and 2 real hidden normal CLI launches passed. Independent
spec/standards reviews have no remaining findings. Prepare-retry and same-thread
input-cleanup retry fixes are included with red/green guards. Hosted checks,
deployment and physical mouse acceptance are still in progress.

## Running source and deployment

Accepted source 379df037d1567f9ea3882f1f0e07902dd4d416e5 (PR26) is now stopped and retained
in hugin-button-target-mjolnir. Fresh receipt confirms session_exited, code 0,
own_family_exited true and no started old apps:
.runtime/pilot-session-e02be514-5fb9-412b-82ee-57f7f0bdb4bf.json.
No PID is termination authority. Normal tray Quit is the transition; the checked
pilot starter no longer launches Whispering/PipPal on exit. Never replay old
auto-return helpers. Prior PR25 owner exited cleanly; no repeated old-app Quit
request is needed absent fresh evidence.

C:/Users/brian/Hugin is the deployment junction to
C:/Users/brian/brian-projects/_repos/hugin. Models, worker/runtime inputs, voices
and original cues stay intact. The new persistent startup link must use this
stable installation, never a task worktree or --pilot. Local exact backup and
activation metadata remain under its ignored .runtime; use the guarded restore
in docs/desktop-startup.md after normal Quit if a rollback is needed.

## Accepted behavior and remaining evidence

Accepted: Word/Codex dictation probes, Codex screenshot plus text, original
Whispering cues, Obsidian UI/motion, active mode, movable rounded reading panel,
explicit show/hide, pause/resume implementation, and repeated panel-button flows.
Reading orientation is by section; exact word highlighting is deferred pending
measured Freya/Tyr synchronization, never invented fixed-rate timing.

Historical evidence: docs/baseline-closeout-2026-10-21.md,
docs/panel-actions-2026-10-21.md, docs/screenshot-formats-2026-10-21.md,
docs/reading-panel-2026-10-21.md and handoffs/2026-10-21-button-target.md.
New native registration is not a physical mouse test; shortcut readback is not
an observed Windows login. Full target/device matrix, mixed-DPI/monitor loss,
long-pause Freya/Tyr hearing and broad performance/restore acceptance remain
separate open evidence. Earlier target_changed/audio_failed observations and
reported physical shortcut failure must not be declared fixed by this change.
