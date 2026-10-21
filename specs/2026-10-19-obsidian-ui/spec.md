# Hugin Obsidian UI

Brian approved implementation of the combined design on 19 October 2026:
Nocturne (01) raven logo, Aurora (03) layout/status visuals, Obsidian (02)
colors. The supplied combined image is the visual reference, not an executable
UI. Reference is retained outside Git in the chat's generated image directory
as exec-7fcd1122-19d5-4e24-9607-54d3c28cf675.png.

## Requirements and acceptance

- UI-01: Recreate the swept Nocturne raven as a scalable, deterministic mark.
  Use it in the hero, window and tray. Charcoal #080B12, graphite #151A27,
  muted indigo #5166DD and silver #E9EEF7 own the palette. Curved backgrounds,
  softly lit cards, two shortcut tiles, Freya/Tyr selection and a large RAM-only
  last-dictation area follow the selected arrangement. Verify visually against
  the reference and at native 100/150/200% scale, including minimum size.
- UI-02: Idle has a subtle breathing light; recording has a real level-driven
  waveform; processing has a traveling particle wave; reading gently pulses;
  accepted delivery shows a single check/ripple. No success on recognition,
  copy, failure, cancellation, stale completion or cleanup-only events. Success
  shares the accepted delivery boundary with the existing completion cue.
  Verify actual Controller -> View -> native window seams with synthetic data.
- UI-03: Numeric microphone level only, bounded 0..1, calculated from accepted
  PCM after the cue gate. No new recording, audio retention, logs or queues.
  Reset on stop/cancel/fault/new session; retired callbacks cannot contaminate
  a new session. Silence has no fabricated voice activity. Verify gate/races.
- UI-04: Hover/press/focus transitions for usable controls; keyboard-accessible
  voice/copy/delete/diagnostics and reduced-motion toggle. Visible text describes
  every state independently of color/motion. Preserve text selection, scrolling,
  copy/delete, diagnostic access and tray quit. Shortcut tiles remain explicit
  hotkey instructions: clicking the app must not redirect dictation into itself.
- UI-05: One bounded animation timer, paused for hidden/minimized windows and
  cancelled on stop. Reduced motion uses static truthful state indicators.
  Completion has a producer deadline, never replays when revealing the window
  or on repeated view publication. Measure visible/hidden CPU and retained
  memory with synthetic states; inspect callback and item bounds.
- UI-06: Preserve the existing app lifecycle, target/clipboard checks, cues,
  Freya/Tyr, bindings, RAM expiry and fault messages. Old live source is not
  modified. No framework/runtime installation, cloud or history feature.

## Scope and checks

Build on 52816b2 (documentation above d3fd28d original-tone pilot). Existing
manual Word/Codex acceptance and unknown clipboard-format diagnosis remain
valid historical evidence, not universal compatibility claims. Native previews
use only synthetic text/state and no microphones, hooks, clipboard or models.
Run contracts/integration, dedicated native UI/lifecycle/DPI checks, docs,
independent spec and standards reviews, and hosted checks at the saved head.
Then prepare the source-pinned pilot for user testing using the established
normal shutdown/return path. No production binding/autostart migration.

## Change log

- 19 October: user selected exact combination and authorized implementation of
  the described state-dependent motion. Reduced motion is an accessibility
  default addition; saved OS/application preferences are outside this change.
