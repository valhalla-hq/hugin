# Hugin Context

Status: late field-capture correction is merged and deployed; Hugin is ready. Physical return-to-field acceptance is pending.
Owner: Brian. Private repository valhalla-hq/hugin; runtime Mjolnir.
Data boundary: curated source/configuration/locks and approved synthetic voice
references only. No raw dictation, clipboard/image content, recordings,
credentials, model weights, virtual environments or local startup backups in Git.

## Current objective and authorization

Brian confirmed repeated successful dictation/insertion, reading, stopping and
switching from reading to dictation with the PR26 panel buttons. PR26 and its
PR27 acceptance record are merged. Current deployed main is
4e18f7460e3004f7b25ecb09a08b0fca8fc986da (PR31 late field capture).

He now explicitly requests permanent mouse Back/XBUTTON1 = dictation and
Forward/XBUTTON2 = reading, removing PipPal/Whispering login startup, and
confirms Hugin should start silently after login. The latest keyboard steering
sets Alt+Y for dictation and retains Ctrl+Alt+V for reading. Existing panel
buttons remain; the old opposite mouse mapping and no-migration restriction
are superseded.
Complete routine private integration and the requested Windows setup after
checks/review. Production packaging follows this prerequisite; do not equate
this increment with the entire V1 acceptance matrix.

## Active work and handoff

- Branch: codex/hugin-mouse-startup-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-mouse-startup-mjolnir.
- Implementation base: 460534fff76741427f6c380405916be1c7947f10.
- Integrated implementation: PR28, source fbf64afc282edc0356038474ffb3f1379a01666f.
- Current follow-up: move full field capture to delivery, after Brian's reported click-away/return failure.
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
complete. Latest physical dictation acceptance is recorded below; next-login
and permanent resolution of the earlier intermittent rejection remain open.

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

PR29 merged at 2026-10-21T13:44:15Z as
7f288d4bf2021712f4e4d3283058a22311c31376, checked source
d5aa060f3fb6f408963703e1536a6c7442691335. Both independent reviews clear;
hosted checks 39609867294, 39609951874 and 39609951730 attempt 2 succeeded.
The latter rerun resolved an inconsistent GitHub completed-run/pending-job state;
no check was bypassed. Stable main fast-forwarded cleanly; runtime/model inputs
and activation stayed identical. Normal Hugin launched at 15:44:38 Europe/Berlin.
Native window readback confirmed ready, Lokal, Back/Alt+Y and Forward/Ctrl+Alt+V.
Hugin is running from the stable installation; do not edit its files live.

Brian confirms Ctrl+V inserts the last dictation, but automatic insertion fails
with both Alt+Y and mouse Back. Fresh diagnosis: native_target_captured,
capture_field=target_unverifiable, clipboard=copied, delivery=not_attempted;
error_code=target_unverifiable. The new clipboard behavior is accepted. The
remaining failure is before insertion, in focused-field proof. Exact failed
provider condition is not yet known; do not weaken the proof speculatively.
An ignored, bounded read-only diagnostic reused the product's isolated target
probe. A focused empty Codex field passed. During a 45-second observation with
55 samples, field proof passed during Brian's dictation tests. A later sample
rejected a Document range at selection_probe.py:264 because its read-only
attribute did not explicitly prove false. This is an observed rejection site,
not proof of the cause of Brian's earlier failed dictation. A final separate
probe passed with focused Edit control type 50004. No document/clipboard payload
was recorded, no windows activated and no input/audio generated by the probes.
The observation finished; no diagnostic helper remains running.

Brian confirms the current Alt+Y/mouse dictation attempts and explicitly the
Fertig & einfügen button work. Ctrl+V fallback was separately confirmed. No
production code changed between the failed and successful attempts, so do not
claim the intermittent error permanently fixed. Next recurrence needs exact
failed-field facts before a correction. Keep task ownership active. Production
packaging, full target matrix and actual next login remain open; old apps stay
disabled. Only these curated context/handoff updates are being checkpointed;
the ignored diagnostic script and raw probe output stay out of Git.

## Current correction: late field capture

Brian reports clicking elsewhere during dictation then returning to the field
before stop can fail, and requests the last chosen cursor plus comparison with
Whispering. The repeated physical flow passed. Another 45-second/55-sample
read-only observation saw Group -> Edit and later Document -> Edit. A rejected
Document's read-only attribute was unknown/mixed while its selection was false.
This remains separate from proof of the historical failing capture.

Pinned Whispering7.11.0 write_text sends clipboard Ctrl+V at delivery; it does
not retain an earlier UIA field. The new change adopts late field resolution,
retaining the exact native stop basis and every final UIA/native commit guard.
Full field capture moves once from the audio-stop worker to the delivery worker
after final text. The old early capture path is removed. No retries, focus
restoration, whitelist expansion, clipboard behavior or input-shortcut changes.
The native basis is exact, but the old pre-recognition UIA identity is no longer
pinned. A Chromium surface with one native HWND/focus and no native caret or
selection may therefore use a different UIA field/caret selected even after stop.
This consequence follows the requested latest-cursor behavior and is explicitly
tested; do not claim every same-window field change after stop is rejected.

Spec/plan/tasks: specs/2026-10-21-late-field-capture/. A controller regression
reproduced early unavailability permanently blocking later valid insertion;
it now passes. After-stop native-target change, persistent failure, no native
basis, cancellation and owner responsiveness are covered. The same-native/UIA
field-switch guard passes through Controller, ClipboardService and the native
capture boundary with synthetic I/O. 504 contracts and integration tests pass
in 22.627s; two real owned hidden RichEdit UIA fixtures pass in 0.590s without
user focus/clipboard changes. Docs check passes. Independent spec and standards
reviews have no open findings. No real Codex acceptance of the new code yet.
PR31 https://github.com/valhalla-hq/hugin/pull/31 merged source
22d513c5e471d8a7c5669beed49a1ca737a0d19a as
4e18f7460e3004f7b25ecb09a08b0fca8fc986da at 14:34:53 UTC. Both independent
reviews confirmed that exact source head. Hosted runs 39617479727,
39617490293 and 39617490238 succeeded. Remote main and source context/handoff
blobs were verified. Task and stable clone were clean at the merge commit
before this documentation follow-up.
After Brian confirmed normal Quit, the stable clone fast-forwarded and Hugin
restarted at 16:36:02 local time. Activation, preferences, all three environment
manifests and desktop-setup manifest hashes are unchanged. UI readback shows
Bereit fuer dein Diktat, Alt+Y and the existing mouse/panel controls.
Physical click-away/return acceptance requested; no result yet. Keep ownership
active. Rollback is previous main 7ac3cc6 after normal Quit. Packaging and actual
next-login acceptance remain separate; Whispering and PipPal stay disabled.
