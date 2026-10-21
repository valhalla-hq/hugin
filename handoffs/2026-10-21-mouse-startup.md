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

Stable deployment still clean PR28, no app currently running. Next: reviewed
checkpoint/private PR, exact-head hosted checks and merge, stable deployment
fast-forward and normal --show launch. Physical Codex/mouse/Alt+Y/Strg+V
acceptance remains pending. Keep current task ownership active; no old-app
return and no repeat startup migration. Production packaging follows acceptance.
