# Panel actions

Brian accepted the movable reading panel and requests mouse buttons for dictation
and reading, supplementing the existing keyboard shortcuts. Bounded routine
implementation and checked private integration are authorized. Previous accepted
source 6dd1bde remains frozen while running; main is 35528f4.

## Requirements

- REQ-001: Diktieren offers start, cancellation while starting, and finish/insert
  while recording. The target is the field selected during recording, at finish.
- REQ-002: Vorlesen starts the externally selected text and offers stop throughout
  preparation/playback, retaining pause/resume and reading-panel visibility.
- REQ-003: Mouse activation of these actions preserves the other application's
  foreground/focus/selection. No remembered target or forced reactivation.
- SEC-001: Existing capture, target validation, clipboard restoration and final
  delivery authorization remain authoritative. No content persistence or global
  input interception. Missing external target explains how to continue.
- NFR-001: Obsidian rounded controls fit compact/DPI layouts; normal keyboard
  activation/accessibility remains. Repeated/stale UI commands cannot toggle a
  subsequent state/job. Subclass callbacks retain ownership until native removal.
- OPS-001: Isolated worktree, independent review, exact-head CI/integration and
  normal pilot switch; preserve runtime, original applications and return path.

## Acceptance and verification

- AC-001: Start button -> choose external field -> finish button, or finish with
  shortcut, uses the field at finish. Controller synthetic lifecycle and native
  focus fixture; final real Codex/Word acceptance by Brian. Covers REQ-001/SEC-001.
- AC-002: Selecting external text then clicking Vorlesen retains focus and reads
  that selection; stop works before first audio, pause/visibility remain. Covers
  REQ-002/REQ-003; native owned fixture plus controller tests.
- AC-003: Hugin already foreground at finish/read-start does not select an old
  target. Clear hint; recording continues until field chosen. Existing shortcuts
  keep their behavior. Covers SEC-001/REQ-003.
- AC-004: Duplicate and stale button commands have no extra effect. Native
  subclass install/removal failure is explicit and retains callback ownership;
  unrelated controls still activate normally. Covers NFR-001.
- AC-005: Minimum window and 100/150/200% layouts contain readable nonoverlapping
  controls, matched rounded backdrops. Synthetic preview. Covers NFR-001.
- AC-006: Saved context/handoff, independent review, exact-head hosted checks and
  normal restart evidence; report real hardware acceptance separately. OPS-001.

## Known facts and limits

Dictation already captures native target in StopRecording. Selection capture uses
current foreground and revalidates it. Windows WM_MOUSEACTIVATE permits delivering
a click without activation (MA_NOACTIVATE). Tk's Windows ButtonDown binding does
not set focus. Actual native click chain still requires an owned-window probe.
Buttons must be visible beside the target; title-bar/background clicks still
activate Hugin. No new floating control, global focus history or autostart change.
