# Persistent mouse controls and login startup

Brian requests this prerequisite before production packaging, after accepting
the PR26 panel flows. He explicitly authorizes replacing Whispering/PipPal at
login with silent Hugin startup. This supersedes the original V1 forward/back
mapping and the previous restriction against mouse/startup activation.

- REQ-001: Back (XBUTTON1) toggles dictation; Forward (XBUTTON2) toggles reading.
  Existing priority, target proofs, panel buttons and dynamic Escape remain.
  Ctrl+Alt+D/V remain additional controls; Alt+Y is retired.
- REQ-002: Ordinary launches use the same durable activation/profile. Explicit
  keyboard-only pilots never write or reset that profile. Unknown profiles fail
  visibly before input registration. UI hints reflect the actual mode.
- OPS-001: Replace only the two inspected current-user Startup links with Hugin.
  Back up exact bytes before changing them; preserve unrelated entries and all
  old app installations. Setup is explicit, repeatable and reversible; normal
  startup never edits Windows startup or Logitech configuration.
- OPS-002: Hugin starts silently from its stable installation after login, with
  existing single-instance and cleanup ownership. No temporary worktree path or
  --pilot in the shortcut. No login/reboot induced just for testing.
- SEC-001: No raw clipboard/text/audio logs, additional packages, drivers,
  registry remapping, elevation, scheduler or new model. Native hook remains a
  short bounded-queue producer; preserve injected-driver and cleanup semantics.

## Acceptance

- AC-001 (REQ-001, SEC-001): held/repeated Down emits once; Up is consumed;
  button one dictates, two reads; other buttons/lower-integrity input pass on.
  Native registration and real mouse behavior require distinct verification.
- AC-002 (REQ-002): separate normal CLI launches read the same profile without
  changing it; absent/invalid activation registers no input. Pilot is unchanged.
- AC-003 (OPS-001): plan is read-only; apply backs up before replacing links;
  second apply changes nothing; changed state is rejected; rollback restores
  exact original bytes and refuses to overwrite intervening changes.
- AC-004 (OPS-002): native shortcut readback has stable pythonw/launch/root,
  no --show/--pilot; normal app is ready with mouse controls, one instance, and
  its window hidden. Actual next-login success remains pending until observed.

Windows/Mjolnir only. Local backup/activation metadata stays ignored. Packaging
and a full device/target/performance matrix are not claimed by this increment.
