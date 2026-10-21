# Optional reading panel

## Goal and authority

Brian accepted the recommendation to add useful reading orientation after saving
the finished baseline. Main at 8fdd3e4 includes PR19/20; the confirmed d1331da
pilot remains frozen. This brownfield slice adds an optional compact Obsidian
panel and real pause/resume. It does not change dictation or migrate startup.

## Requirements

- REQ-001: Show the section currently entering playback, with its ordinal and
  total. Keep the original selected text. Do not imply word-level timing or a
  duration percentage. Selection capture must finish before showing any panel.
- REQ-002: Pause/resume holds and continues the existing audio position. Enable
  pause only after playback exists. Stop, Escape, voice changes, device events,
  quit and dictation retain their existing cancellation/priority behavior.
- REQ-003: The bottom reading panel is optional, can be hidden without stopping
  reading, and never automatically activates or replaces the foreground window.
  Provide keyboard-accessible pause/stop controls in the main window as well.
  The panel toggle is a session preference, initially enabled in this pilot.
  Unavailable native placement disables only the optional panel and leaves
  main-window controls and speech available; no focus-changing fallback.
- NFR-001: Preserve bounded streaming and one GPU owner. No full recording cache,
  extra alignment model, network service or word-rate heuristic. Paused local
  playback backpressure must not be mistaken for worker initialization failure.
- SEC-001: Reading text exists only in RAM and is cleared at finish/cancel/error/
  shutdown. Diagnostics contain no reading text. Stale controls/events cannot
  act on a newer reading job.
- OPS-001: Keep the current pilot and old runtime source intact. Verify the new
  candidate before a normal user-controlled restart; preserve the return path.

## Edge cases and acceptance

- AC-001 (REQ-001): Delaying audio acceptance keeps the previous section visible;
  preparing the next section does not advance the panel. Section changes occur
  only after prior PCM drains and new PCM is submitted (device latency remains).
- AC-002 (REQ-002/NFR-001): Pause freezes queued native audio, writes remain
  bounded, resume loses/repeats no PCM; cancellation releases a paused writer
  promptly. A pause exceeding the initialization timeout remains valid.
- AC-003 (REQ-003): Show/hide/update using an owned native fixture preserves its
  foreground handle. Controls fit at supported DPI/monitor work areas. Hiding
  the panel leaves speech running; main-window keyboard controls remain usable.
- AC-004 (SEC-001): Cancel/finish clears all presentation text; stale events and
  pause/stop commands are ignored. Existing diagnostics and dictation guards pass.
- AC-005 (OPS-001): Native fixture checks and independent review pass; Freya/Tyr
  live listening, real multi-monitor behavior and user preference are explicitly
  unverified until the new candidate is started and Brian accepts it.

## Non-goals and evidence

Exact word highlighting, seek/back navigation, persistent reading history,
production hotkey/autostart migration and a new UI framework are out of scope.
Inspected local PipPal Qwen uses characters/17 for duration and syllable-based
word distribution; these are estimates. Hugin's engine yields PCM and chunk
timings, not word alignment. A section is Hugin's existing <=400-character
synthesis span, not necessarily one sentence. Live usefulness is still a pilot
question; implementation will not label estimated timings as measured.

## Verification

Guard-first reducer/controller/audio/stream tests; full contracts + integration;
isolated own-window native UI and silent native playback checks; no user clipboard
or application interaction. Record exact commands/results in tasks and handoff.

## Change log

- 2026-10-21: Initial accepted direction, bounded to section orientation and pause.
