# Dictation follows the current cursor

Brian reports repeated target_unverifiable after changing windows/fields and
returning while dictating. The transcript is copied; no paste is attempted.
He requests Whispering's current-cursor behavior. This supersedes the earlier
stop-target and mandatory UIA delivery-proof requirements for dictation.

Observed: a 45-second read-only probe saw Codex report both a non-text focused
element and a valid Edit; it also saw other applications during switching.
These are parallel samples, not proof of the exact failed internal snapshot.
Pinned Whispering7.11.0 writes clipboard text and sends Ctrl+V at current focus:
https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src-tauri/src/lib.rs#L195-L240

- REQ-001: Bind no dictation destination at recording start or stop. Choose
  Windows' current foreground/focus immediately at the serialized paste commit,
  after transcription/publication, including switches after recording stops.
- REQ-002: UIA Edit/Document/selection availability must not gate dictation.
  One Ctrl+V goes to the actual current focus; never activate a remembered
  window or send Enter. Native focus must remain stable through that short
  commit. No retry after an uncertain or partial input submission.
  Focus may belong to an embedded child from another process/thread (Teams
  WebView). Validate its actual foreground-window relationship rather than
  equating process IDs. Unrelated focus windows remain invalid.
- REQ-003: Preserve one-shot generation/cancel/shutdown arbitration, clipboard
  ownership/token/sequence checks, modifier checks and partial-key cleanup.
  No usable native foreground/focus or detected native password remains an error.
  Like manual paste, the current target app decides whether it consumes Ctrl+V;
  submission is not proof that text was accepted. UIA-only protection is no
  longer promised by this dictation path.
- REQ-004: Completed current dictation remains available for Ctrl+V, even on
  paste failure; a later user copy wins. Reading selection, audio, voices,
  animation, hotkeys/mouse profile and startup remain unchanged.
- OPS-001: Diagnostic capture_native describes the commit-time capture;
  capture_field is not_required. No content logs or raw UIA/clipboard payloads.
  Preserve1.0.0 installer/build as rollback; actual login acceptance stays open.

Acceptance: controller/service/native-boundary tests must fail on the former
implementation and pass for A -> B during recording, after stop, and while
delivery waits on the owner. A Chromium native focus without UIA text support
must receive the chord. Cancellation, duplicate/rejected commit, newer clipboard,
missing focus, modifier/partial input remain covered. Native test targets only
owned synthetic fields; physical Codex switch test after candidate restart is
separate. No sign-out or startup claim is implied.
