# Reading panel placement and appearance

Brian accepts explicit hide/show and requests matching Obsidian styling, the
visibility button centered at the bottom of the main Vorlesen card, and a freely
movable overlay that stays where placed. This refines the integrated PR21/22 UI.

## Requirements and acceptance

- REQ-001 / AC-001: Use existing Hugin gradients, rounded outer/text surfaces and
  correctly composited button corners. Keep text readable and controls inside
  their surfaces at supported DPI and the main-window minimum size.
- REQ-002 / AC-002: The main Vorlesen card contains the visible centered
  Einblenden/Ausblenden action below its existing content, in idle and reading
  states. Do not duplicate the footer control or overlap shortcuts/pause/stop.
- REQ-003 / AC-003: Drag the overlay by its clearly indicated header across
  monitor coordinates, including negative coordinates. Remember its last position
  across hide/show and reading jobs within the app session, independent of the
  foreground app. First show may use the foreground monitor; app restart resets.
- REQ-004 / AC-004: On show and drag release, fit the panel to the nearest current
  monitor work area; a removed monitor must not leave it unreachable. Preserve
  automatic no-activation behavior. Native placement/drag failure disables only
  the optional panel; main reading/audio controls remain usable.
- SEC-001 / AC-005: Clear reading text and drag state at job end/hide/error; keep
  only presentation coordinates. No new text persistence, clipboard, hooks,
  worker/audio changes, word estimates or startup migration.

## Verification and limits

Guard remembered/clamped geometry and own-window header dragging, focus, rounded
region and current-view restoration. Reuse existing native visual/motion checks.
Visually inspect a synthetic preview; independent spec/standards reviews and
exact-head hosted checks precede normal pilot restart. Physical mixed-DPI monitor
behavior and live speech acceptance remain separate from synthetic fixtures.

## Change log

- 2026-10-21: Bounded follow-up requested after accepted show/hide pilot.
