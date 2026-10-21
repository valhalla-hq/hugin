# Mouse controls and startup handoff

## Objective and authorization

Brian accepted the PR26 panel flows and explicitly requests saving/merging,
then Back=XBUTTON1=dictation, Forward=XBUTTON2=reading and removing PipPal plus
Whispering from login startup. He explicitly confirmed Hugin should replace
them and start silently on login. Ctrl+Alt+D/V remain additional controls.
This supersedes earlier restrictions/mapping; production packaging follows
this prerequisite and is not claimed complete here.

## Git state

- Private repository valhalla-hq/hugin, runtime Mjolnir.
- Branch codex/hugin-mouse-startup-mjolnir; base/main
  460534fff76741427f6c380405916be1c7947f10 (accepted baseline through PR27).
- Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-mouse-startup-mjolnir.
- Initial control e3deecae6673a024aa9015a4387737fbec04c795; deployment preflight
  advanced control to 05181f9a99374ff8b298c626f903304f36ac8926, with no lifecycle
  contract changes. Task ownership active until final pushed checkpoint.
- PR28 https://github.com/valhalla-hq/hugin/pull/28 merged at 13:09:02 UTC on
  21 October 2026. Source fbf64afc282edc0356038474ffb3f1379a01666f, merge
  6239f4fcf28cb249e51681bd056aa16795d7efdf. Both exact-head reviews clear;
  hosted runs 39605133065, 39605132749 and 39605076262 succeeded.
- This follow-up records deployment and fixes the observed clipboard rejection.
- Spec/plan/tasks: specs/2026-10-21-mouse-startup/.

## Implementation and verification

One versioned binding definition owns mouse/keyboard routing and UI hints.
Normal CLI reads activation.json; explicit pilot never writes it. Diagnosis
names the input profile. Existing focus/clipboard/worker ownership stays intact.
tools/desktop_setup.py plans by default, hash-checks apply, stages complete
backups before publication, replaces only two named Startup links and supports
guarded exact-byte restore. Stable pythonw/launch/root, no --pilot/--show.

- Initial red guards reproduced reversed mouse mapping, old Alt+Y registration
  and unconditional normal-launch refusal; new guards pass.
- Final contract/integration run: 494 passed in 20.721 s. Migration 7/7;
  native Shell-Link creation,
  repeat and restore in a private temporary folder pass.
- Independent review found incomplete backup preparation blocked retry; fixed
  at the producing boundary using unique staging plus validated publication.
  Spec re-review confirms closure. Standards review found an older unretryable
  native-input cleanup failure; input owner now survives and retries its
  remaining resources on the same thread, with backoff. Red/green guard plus
  standards re-review (33 focused pure checks) confirm closure; no open findings.
- Native ownership: 3 tests in 0.314 s, including normal/pilot/normal hook and
  hotkey acquisition/release. Two actual normal CLI starts with isolated state
  reached ready/withdrawn/Lokal and preserved activation bytes in 1.954 s.
  No speech/input injection/clipboard data used. Three native UI lifecycle
  checks also passed in 0.449 s. Actual startup readback is recorded below;
  physical mouse and next real login remain explicit acceptance gaps.

## Running state and rollback

Accepted source 379df037d1567f9ea3882f1f0e07902dd4d416e5 remains frozen in
hugin-button-target-mjolnir. Brian closed it normally; fresh receipt confirms
session_exited, exit_code 0, own_family_exited true and no old-app starts:
.runtime/pilot-session-e02be514-5fb9-412b-82ee-57f7f0bdb4bf.json. Never terminate
from a recorded PID. Normal tray Quit; no old-app auto-return. Deployment is
C:/Users/brian/Hugin -> C:/Users/brian/brian-projects/_repos/hugin.
No changes to models, runtime locks, voices or original cues.

Actual setup applied from the merged stable deployment with plan
50290df65bbaee97c45c9052008570e2acaedfa93c4ddf914e03b8f9a604d884.
Native WScript and Win32_StartupCommand readback show Hugin.lnk in current-user
Startup, with fixed installation pythonw/launch/root and no --pilot/--show;
PipPal.lnk and Whispering Local STT.lnk are absent. Activation profile is
mouse-back-dictation-v1. Exact originals under .runtime/desktop-setup-v1 match
their inspected SHA256 hashes (before-1.bin PipPal, before-2.bin Whispering).
No local backup binaries or personal contents are in Git.

Discovery also found Whispering's separate local STT service still running,
despite the application window being closed. Its live health proved the known
service identity, matching pidfile, unloaded model and active old forward hook.
The existing installation stop.ps1 validated executable/exact script/family
and stopped it; port 8178 no longer listened. No old config or code was edited.

Hugin was started normally from stable deployment with --show for Brian's
physical test, without --pilot. Native screenshot showed mode Lokal, the correct
Back/Forward hints and an already running recording; no agent input initiated
that recording. Do not interfere with the user's current speech/selection.
The production Startup link remains silent. Prior PR26 worktree ownership was
released after clean exit and remote proof; its recovery files are retained.
Restore after normal Quit with desktop_setup.py --root C:/Users/brian/Hugin
--restore; old apps are never automatically launched. See docs/desktop-startup.md.

## Pickup

Continue valhalla-hq/hugin from this exact handoff. Read AGENTS.md, CONTEXT.md,
the spec and current PR/head first. Setup and checked implementation integration
are done. Preserve the running stable installation. Record Brian's physical
Back/Forward acceptance and the next naturally occurring login separately;
do not reboot/logoff automatically. Production packaging is the next stage
after this input/startup prerequisite, not an already delivered installer.

## Clipboard rollout defect and follow-up

Physical mouse dictation failed with native_target_captured / target_captured /
format_unsupported. Observed OLE text metadata (including DataObject and
EnterpriseDataProtectionId) causes the old snapshot policy to reject before any
payload read. This does not prove a target-capture problem. User explicitly
requests completed text stay in the clipboard for Ctrl+V, including missed fields.

New spec/plan/tasks: specs/2026-10-21-dictation-clipboard/. Implementation owns
persistent publication in ClipboardService, before optional paste eligibility,
without reading old contents. Native current-generation and clipboard sequence
checks precede EmptyClipboard. One rendered Unicode publication with history
exclusion and transaction token remains; no later restore overwrites user copies.
Application preserves target errors and separately records publication. Reading
capture retains restoration. Existing target/commit/resource checks remain.

Initial red guards reproduced unsupported-original and missing-target failures.
Final checks: 500 contracts/integration passed in 20.707 s; 29 mocked Windows
ABI/producer and docs validation passed. Review found a misleading Ctrl+V hint
for a known newer-copy conflict and obsolete success-cue test fixtures; both
fixed with guards. Native fixture cleanup now tracks only returned owned
publications, checks sequence under its read lock and closes independently.

Latest steering explicitly replaces Ctrl+Alt+D with Alt+Y. The shared Binding
owns per-action Control modifier and visible shortcut; production UI, native
registration, pilot starter and design preview derive it. Mouse mapping and
reading Ctrl+Alt+V stay. Normal/pilot registration guards were red then green.
Brian confirmed normal Quit, and fresh process inventory showed no Hugin
pythonw launch. Three real registration/ownership checks passed in 0.327 s.

Native clipboard: publication and owner-close readable persistence passed on
the first run, but a plain hidden Edit did not consume WM_PASTE. Reused the
established RichEdit with explicit selection. A changed file clipboard was
refused before mutation; Brian supplied disposable Hugin Test text. The final
native fixture passed in 0.045 s: unsupported synthetic original replaced,
Unicode pasted into only the owned hidden RichEdit, rendered formats survived
writer close and original supported text/HTML/Chromium formats were restored.
The user has been told copying can resume. No native input reached user apps.

PR29 integrated as 7f288d4bf2021712f4e4d3283058a22311c31376 at
2026-10-21T13:44:15Z, exact reviewed source d5aa060f3fb6f408963703e1536a6c7442691335.
Both independent reviews clear; hosted checks 39609867294 / 39609951874 passed.
39609951730 required one rerun because GitHub reported a successful workflow
with a pending job; attempt 2 passed with all check runs complete. No bypass.
Remote context blobs were proven: 8cfcbfb312aa5c015d167b8f9cb169360d09ac86 and
b0738eaa6c76cca7605e3e61bc2aa899e12a9e9e (context / exact handoff).
Stable deployment fast-forwarded cleanly, runtime/model inputs unchanged,
activation retained. Normal launch at 15:44:38 Europe/Berlin; native UI readback
showed ready/Lokal and correct Alt+Y plus Back/Forward hints. Hugin runs from the
stable installation, not this task worktree. No old-app restart/setup rerun.

User physical retest: Ctrl+V works; automatic insertion fails with both Alt+Y
and mouse Back. Latest diagnosis shows native_target_captured,
capture_field=target_unverifiable, clipboard=copied, delivery=not_attempted.
The clipboard fallback is accepted; the exact failed UIA field condition is
still unknown. Preserve the live app and existing insertion safeguards.
Ignored .runtime/field_diagnostic.py reused the production isolated owner for
bounded, Codex-scoped read-only probes. Empty focused field passed. During the
45-second observation (55 samples), proof passed during Brian's dictation;
a later sample rejected a Document range in selection_probe.py:264 because
IsReadOnly did not explicitly return false. This does not establish the cause
of the earlier failed dictation: the probe was parallel, not its own capture.
The final separate sample passed with focused Edit type 50004. No text or
clipboard payload was recorded, no windows activated and no input/audio
generated by the probes. Observation and owned child cleanup completed.

Latest user feedback confirms keyboard/mouse dictation and explicitly the
Fertig & einfügen button work; Ctrl+V was independently confirmed. No product
source changed in this diagnostic session, and the intermittent rejection is
not claimed permanently fixed. On recurrence, collect exact failed-field facts
before changing the producing boundary. Hugin remains running from main7f288d4;
no restart required for this documentation-only checkpoint. Task ownership
stays active; production packaging and actual next login remain separate.

Pickup: Continue valhalla-hq/hugin on Mjolnir from this handoff and CONTEXT.md.
Preserve the live stable deployment and successful clipboard/binding behavior.
Latest physical insertion passes, but the earlier field-proof failure has no
proven cause. Do not infer it was fixed by clipboard publication or by the
read-only probe. Record a recurrence precisely before any further input fix.

## Click-away/return follow-up

PR30's documentation checkpoint is merged as7ac3cc6526d5cd85b5439b31cd273c8730e9ec91;
deployment has that clean head, with identical application source to PR29. Task
worktree fast-forwarded from its pushed checkpoint to that main before edits.
Preflight again confirms control05181f9a and exclusive same-task continuation.

Brian requests reliable clicking elsewhere during recording and returning to
the field before stop, using the last chosen cursor, and a Whispering source
comparison. The physical repetition again passed. A bounded read-only 45-second
observation completed55 samples, showing Group/Edit and Document/Edit changes.
At one Document rejection the whole range's read-only attribute was unknown/mixed
and its selected range explicitly false. Parallel observation is not the
historical failed capture; no direct cause is claimed from it. All probes exited.

Whispering7.11.0 pinned a6b15c28's desktop.ts invokes write_text; lib.rs195-240
publishes text, waits50ms and sends Ctrl+V to the current focus, then optionally
restores prior text. Hugin now adapts late capture timing while retaining the
native stop basis, exact field/selection proof, final commit guard and persistent
dictation clipboard. No foreign focus activation or unverified paste.
Important semantic consequence: only the native stop basis remains pinned.
UIA identity is first chosen at delivery. A Chromium surface sharing native
HWND/focus without native caret/selection may accept a different UIA field or
caret selected after stop. This is intentional late selection, not preservation
of the former pre-recognition UIA identity; test it through the real controller,
service and native capture boundary with synthetic provider I/O.

New spec/plan/tasks: specs/2026-10-21-late-field-capture/. Full field capture moves
from StopRecording's worker to StageDelivery's worker after final text; no second
probe/retry path is added. A public controller regression was red for unavailable
field at stop but recovered field at text completion (no insertion), now green.
After-stop target change/cancel, permanent failure, copy fallback and controller
responsiveness also pass. Updated cue test proves microphone/end cue precede
recognition and one later field probe. The same-native/UIA-switch guard passes
through Controller, ClipboardService and NativeClipboard.capture_target with
synthetic I/O, proving exactly one late capture and commit to field B.
504 contracts/integration passed in 22.627s; 2 own hidden RichEdit native UIA
fixtures passed in 0.590s; docs validation passes.
Only technical facts retained; no recordings/dictation/clipboard payload in Git.

Independent spec and standards reviews have no open findings. Live app is
unchanged. Next: checkpoint and exact-head CI/private merge, ask only for normal Hugin
Quit before code deployment, then restart for Brian's click-away/return test.
Whispering/PipPal stay disabled. Keep ownership active; packaging/login remain
separate. Do not call the intermittent physical bug fixed before live acceptance.
