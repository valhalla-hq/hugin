# Hugin1.0.2 installer and startup upgrade

Initial task state: Brian requests the productive1.0.2 installer and startup migration. The
accepted app-only payload pins3fd3ca9988c20eb530d62f427e73ce78ce14e6d3;
source13be3f870ab797c8ea6ebbd061821727c59a4be9 is merged in Main772bf1e.
At task start, installed productive startup selected1.0.0. The completed upgrade
selects installed1.0.2; see tasks and retained receipts. No app behavior change.

- REQ-001: Package only the authenticated immutable1.0.2 manifest records and
  pinned Inno recipe. Never include candidate state, dictation, caches or logs.
  Preserve app/source/recipe/compiler/artifact identities and hash all slices.
- REQ-002: Install into a separate owned1.0.2 release root using the existing
  guarded installer; retain1.0.0 and its immutable installer as rollback.
  Preserve active preferences, activation, mouse/keyboard profile and cues.
- REQ-003: Back up and migrate the owned Hugin startup shortcut to the installed
 1.0.2 Hugin.exe --background; verify actual target/arguments/working directory.
  Whispering/PipPal stay disabled; no Logitech profile change or legacy restart.
- OPS-001: The old compiler was installed in a deleted task worktree. Registry
  registration alone does not prove availability. Compiler must have a durable
  path outside worktrees and match trusted Inno7.1.0x64 provenance.
- OPS-002: Automatic review rejected provisioning with only blocked by policy.
  Brian then explicitly requested agent installation; one normal same-channel
  reviewed attempt also rejected. No retry via other tools, scripts or shell;
  only a user-performed compiler installation/environment change resolves it.
  Brian's subsequent manual installation has resolved this dependency.
- OPS-003: Existing Hugin may run during preparation/compilation. Actual update
  and real input-start checks require Brian's normal Quit. No force-stop,
  logout/reboot, extra fees, unrelated software or CI-policy change.

Acceptance: closed file-list and payload verification; installer compiler exit0
and all output hashes; successful guarded upgrade, preserved state and exact
startup readback; repeat normal hidden starts with the fixed input profile.
Actual Windows-login acceptance remains separate from shortcut/manual starts.
