# Obsidian interface and motion verification

Brian approved the Nocturne logo (01), Aurora layout/status treatment (03) and
Obsidian palette (02), then explicitly requested implementation with animation.
Implementation: `d7818648456480ef62ef852a74d8e1b941750b29`, including the producer
facts in `68dbbb73fa725a8f5460925dda85b9452a60a36a` and UI in `d521ddc`.

## Result and ownership

- The native Tk/Pillow window now uses a silver curved raven, charcoal surfaces,
  restrained indigo light, rounded gradient cards and Freya/Tyr voice buttons.
  Branding owns the vector geometry; no generated reference image is in Git.
- A recording waveform consumes one bounded microphone-owned RMS value from
  accepted PCM after the cue gate. A stale, stopped or faulted meter is zero;
  no PCM or level history is retained by the interface.
- Processing has a traveling particle wave, reading a quiet pulse, and idle a
  slow background light. Accepted successful delivery alone creates the short
  completion receipt. Repeated views and revealing a hidden window cannot
  restart it. A new action, cancellation or error invalidates the visual.
- One animation timer and 116 reused Canvas items remain bounded. Ten light
  frames and seven frames per button are replaced on layout changes, not
  accumulated. Hidden/minimized windows and reduced motion stop that timer.
  All timers are cancelled on normal stop.
- State text remains explicit. Native keyboard controls, result selection,
  scrolling, copy/delete, diagnostics and tray quit are retained. The two
  action cards describe the hotkeys; they do not start dictation into Hugin.
- Reduced motion is a window-session option; OS preference detection and
  persistent preferences are outside this change.

Clipboard/field guards, original Whispering sound files and their invocation,
Freya/Tyr, pilot hotkeys, worker/runtime inputs and the return path are unchanged.
The previous unknown clipboard-format rejection is not claimed fixed.

## Verification at the implementation

Existing controller Python 3.12.10; no dependency installation or upgrade.

| Check | Result |
| --- | --- |
| `tools/dev.py check --group all` | 452 contracts/integration tests, 19.318 s, pass |
| Same suite with `python -S` after import correction | 452 tests, 18.354 s, pass |
| `tools/dev.py check --docs` | 19 requirements, 17 criteria, no problems |
| Native `test_ui test_ui_visual test_ui_motion test_startup` | 27 tests, 4.855 s, pass |
| Native layout containment | Preferred/minimum sizes at Tk scales 100/150/200%, including error footer |
| Native visual inspection | Synthetic idle and reading windows inspected; no observed overflow |
| Spec review | Producer facts, stale/failed/cancelled receipts and hide/expire/show correction; no open findings |
| Standards review | Footer containment, bounded objects/timers, light cache and render coalescing; no open findings |

The UI/motion review target was SHA256
`B7A7E67ABBAD4C81C7B5B036403270FFA6D76A22070CBBEE123915643D1E6B62`.
The clean hosted environment exposed an eager Pillow import at `d521ddc`.
It was reproduced locally with `python -S`; raster dependencies now load only
at raster/window use, preserving the original partial-window cleanup guards.
The final import-only delta was independently reviewed with all 16 startup
guards passing under `-S`; `ui.py` SHA256 is
`53A0033C12C5FF36F37098B1A9FB95802E1CA4F7FC5E0709A9C3E5AAA19F81E6`.
Separate reviewers did not repeat the native visual/device checks. Root ran the
native fixtures and inspected the previews. The tests cover genuine own-window
controls and event loops, with synthetic state and text; they do not establish
a new live microphone, Word or Codex dictation acceptance.

All three hosted checks passed at `d781864`: both contract workflows and the
baseline validator. Runs: [push contracts](https://github.com/valhalla-hq/hugin/actions/runs/39234725218),
[PR contracts](https://github.com/valhalla-hq/hugin/actions/runs/39234733640),
[baseline](https://github.com/valhalla-hq/hugin/actions/runs/39234733441).
The final documentation checkpoint is rechecked before launch.

## Bounded UI cost sample

The same isolated fixture published synthetic views and serviced the Tk event
loop every 25 ms, comparing old `d3fd28d` and the new implementation. Each warm
phase lasted approximately 3 s. Cold here means a new process; filesystem caches
were not flushed. These short single samples are not a statistical benchmark.

| Phase | Old process CPU s | New process CPU s | New animation frames |
| --- | ---: | ---: | ---: |
| Visible idle | 0.266 | 0.172 | 38 |
| Recording | 0.375 | 0.172 | 55 |
| Processing | 0.391 | 0.156 | 55 |
| Reading | 0.297 | 0.172 | 55 |
| Hidden idle | 0.047 | 0.031 | 0 |
| Reduced-motion recording | unavailable | 0.250 | 0 |

New process startup wall/CPU was 0.303/0.297 s versus 0.225/0.203 s.
Peak observed working set increased from 37.51 to 47.82 MiB; peak private bytes
from 20.79 to 29.37 MiB. Canvas count remained 116 throughout the new sample.
The small extra surface cache trades retained memory for fewer repeated draws.

Working/private memory and CPU cover the UI process, not the launcher family,
GPU or full voice workflow. Agent token use and complete device costs were not
measured. Local synthetic measurement files and raw logs remain ignored in
`.runtime`; no personal dictation, recordings or screenshot payloads are saved.

## App test and return

The old original-tone pilot exited normally: its supervisor receipt reports
exit 0, its owned family exited and the original startup shortcuts were launched.
The new candidate uses unchanged local launcher/diagnostic helpers copied to its
own `.runtime`. Plan mode verifies the exact clean source head, deployment head,
unchanged worker inputs and both original startup-link hashes before a start.

After normal shutdown of Whispering/PipPal, use the source-pinned pilot with
`Ctrl+Alt+D` and `Ctrl+Alt+V`. On normal Hugin quit, its supervisor waits for its
owned process family and restores the original apps through those links.
No autostart or production binding migration. Actual launch status must be read
fresh from this candidate's `pilot-session-*.json` and `input-status.json`.

The next human check is one dictation through recording, processing and insertion,
plus a reading action and reduced-motion preference. Keep clipboard diagnostics
guidance in `handoffs/2026-10-19-clipboard-format.md` if the old rejection recurs.
