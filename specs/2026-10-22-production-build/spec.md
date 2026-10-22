# Hugin production build and installer

Brian requests the productive Windows build, including installer and verification
that autostart and mouse/keyboard bindings persist. Base main5140213; accepted
source398876de. Scope includes local installation/migration and routine checked
private integration. No public distribution, purchased certificate or sign-out.

- REQ-001: Produce a versioned x64 Windows offline installer and SHA256 manifest,
  including the pinned Python3.12.10, all three locked package profiles, local
  locked models/CUDA files, accepted voices/cues and the existing Hugin UI.
- REQ-002: Install per user without administrator rights or a development checkout,
  globally installed Python, Git, package download, PATH change or unrelated tools.
  Start-menu entry and Hugin.exe provide stable normal and background entry points.
- REQ-003: Enable current-user autostart through a stable installed entry point.
  Updates/reinstallation preserve activation and voice preferences byte-for-byte.
  Runtime startup only reads setup state; bindings remain Back/Alt+Y dictation,
  Forward/Ctrl+Alt+V reading and panel controls, using the one existing profile.
- REQ-004: Migrate the known source installation's owned autostart link and voice
  preference with exact-byte backup. Unknown/changed links or data fail closed;
  never recreate Whispering/PipPal autostart. Retain source install as return path.
- OPS-001: Installation/update/uninstall obtain the existing current-user instance
  mutex for their mutation window. Do not kill processes or force-close apps.
  Interrupted setup must report failure; it must not report ready before setup
  and integrity checks succeed. User preference/backups survive uninstall.
- SEC-001: Only tracked allowlisted application files and verified runtime inputs
  enter artifacts. Exclude clipboard/audio captures, state, logs, credentials,
  development environments and machine-specific venv launchers. Offline runtime.
- NFR-001: Keep input/audio/UI semantics and bounded worker ownership unchanged.
  Record provenance, artifact hashes, build/installed size, measured startup and
  verification costs; label unsigned artifacts and unmeasured properties honestly.

Acceptance: build from a clean pinned source; inspect payload and relocate it;
verify private runtimes/imports and no development-prefix dependency; install to
an isolated user target, repeat/repair, verify activation/preference preservation,
owned shortcut readback and still-hidden background launch. On the final installed
app, register real mouse/hotkeys exclusively, check profile after repeated starts,
verify real Freya/Tyr initialization/reading with synthetic input and silent output,
and exercise uninstall only against a separately owned synthetic installation.
Use contracts/integration, public build/setup seams, native isolated probes and
independent spec/standards review; keep negative/conflict/recovery guards.

A real next Windows login remains explicitly unverified until Brian logs in.
Do not infer that receipt from shortcut readback or a manual background start.
No OS restart, login interception, driver/security changes or background scheduler.
The local installer is for Brian's existing NVIDIA/CUDA-compatible machine; no
claim of broad device support or public redistribution approval.
