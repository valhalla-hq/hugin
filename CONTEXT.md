# Hugin Context

Status: mouse controls and startup migration integrated and applied; clipboard insertion defect reproduced; persistent dictation correction under verification.
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
- Implementation base: 460534fff76741427f6c380405916be1c7947f10.
- Integrated implementation: PR28, source fbf64afc282edc0356038474ffb3f1379a01666f.
- Current follow-up: fix old clipboard format rejection and retain finished dictation for Ctrl+V.
- Control/preflight: 05181f9a99374ff8b298c626f903304f36ac8926.
- Ownership: active until final checkpoint/release; runtime uses stable deployment.
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
input-cleanup retry fixes are included with red/green guards. Exact-head hosted checks and both reviews passed. PR28 merged as
6239f4fcf28cb249e51681bd056aa16795d7efdf; deployment and startup migration are
complete. Physical mouse and next-login acceptance remain pending.

## Running source and deployment

Accepted source 379df037d1567f9ea3882f1f0e07902dd4d416e5 (PR26) is now stopped and retained
in hugin-button-target-mjolnir. Fresh receipt confirms session_exited, code 0,
own_family_exited true and no started old apps:
.runtime/pilot-session-e02be514-5fb9-412b-82ee-57f7f0bdb4bf.json.
Its source worktree ownership is released; recovery files remain.
No PID is termination authority. Normal tray Quit is the transition; the checked
pilot starter no longer launches Whispering/PipPal on exit. Never replay old
auto-return helpers. Prior PR25 owner exited cleanly; no repeated old-app Quit
request is needed absent fresh evidence.

C:/Users/brian/Hugin is the deployment junction to
C:/Users/brian/brian-projects/_repos/hugin. Models, worker/runtime inputs, voices
and original cues stay intact. The new persistent startup link must use this
stable installation, never a task worktree or --pilot. This is now applied: native
Startup inventory contains Hugin.lnk and neither old link. Backup hashes match
the originals under .runtime/desktop-setup-v1; activation profile is
mouse-back-dictation-v1. The separate old Whispering STT service was identified
through its live health and stopped with its existing validated stop.ps1; port
8178 no longer listens. Hugin runs normally from deployment with --show for the
user probe; its login shortcut has neither --show nor --pilot. Local exact backup and
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

## Active clipboard correction and Alt+Y

Brian's mouse test started/stopped dictation, but failed with both target
captures successful and delivery format_unsupported. Old OLE text metadata
caused rejection before payload access. He explicitly requests finished text
remain in the current clipboard for Ctrl+V, including when a field was missed.
He additionally requests Alt+Y instead of Ctrl+Alt+D for his existing automation.
This supersedes the earlier Ctrl+Alt+D retention; mouse mapping and reading
Ctrl+Alt+V remain. Binding owns native modifiers, UI and starter/preview hints.

Spec/plan/tasks: specs/2026-10-21-dictation-clipboard/. Dictation publishes once
without an old-content snapshot; target/generation/token/commit checks still
gate paste. Selection capture keeps restoration/recovery. Native publication
checks cancellation under its lock, excludes history/cloud before text, and
recognizes its own flat transaction format for subsequent selection snapshots.
Diagnostics separate publication from insertion; a known newer-copy conflict
suppresses Ctrl+V advice. RAM result remains and can be explicitly copied.

Verification: 500 contracts/integration in 20.707 s, 29 mocked native ABI/producer
checks and docs validation passed. Three actual registration/ownership tests
passed in 0.327 s. Synthetic native RichEdit paste, rendered owner-close
persistence, supported formatted-text snapshot and exact restoration passed in
0.045 s. An earlier plain Edit fixture failed consumption; the proven RichEdit
fixture corrected that test setup. Foreign file clipboard was refused before
mutation. No user's field received synthetic input.

Brian has now closed Hugin normally; fresh process inventory showed no Hugin
pythonw launch. The requested disposable text was restored; copying is released.
Stable deployment remains clean PR28 until checked integration. No application
is currently running. Task ownership remains active for checked merge, normal
restart and physical mouse/Alt+Y plus Ctrl+V acceptance. Only Hugin is restarted;
old apps stay disabled. No production installer or actual next-login claim.
