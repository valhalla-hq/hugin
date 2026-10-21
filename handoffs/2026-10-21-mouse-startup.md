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
- Control e3deecae6673a024aa9015a4387737fbec04c795; task ownership active.
- PR: pending first checkpoint; resolve branch head and checks freshly.
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
  No speech/input injection/clipboard data used. Actual Startup mutation,
  physical mouse and next real login remain explicit acceptance gaps.

## Running state and rollback

Accepted source 379df037d1567f9ea3882f1f0e07902dd4d416e5 remains frozen in
hugin-button-target-mjolnir. Brian closed it normally; fresh receipt confirms
session_exited, exit_code 0, own_family_exited true and no old-app starts:
.runtime/pilot-session-e02be514-5fb9-412b-82ee-57f7f0bdb4bf.json. Never terminate
from a recorded PID. Normal tray Quit; no old-app auto-return. Deployment is
C:/Users/brian/Hugin -> C:/Users/brian/brian-projects/_repos/hugin.
No changes to models, runtime locks, voices or original cues.

The inspected current-user Startup contains PipPal.lnk and Whispering Local
STT.lnk, no Hugin link. Exact originals will be backed up locally under
.runtime/desktop-setup-v1 before any removal. No personal content or machine
backup binaries go to Git. Restore after normal Quit with desktop_setup.py
--root C:/Users/brian/Hugin --restore; old apps are not automatically launched.
See docs/desktop-startup.md for commands and recovery boundaries.

## Pickup

Continue valhalla-hq/hugin from this exact handoff. Read AGENTS.md, CONTEXT.md,
the spec and current PR/head first. Finish checks/review, integrate unchanged
checked head, quit the old pilot normally, apply the inspected plan from stable
deployment, verify actual startup readback and normal hidden launch. Then ask
for physical Back/Forward acceptance; do not reboot/logoff automatically.
