# Hugin reading panel handoff

## Scope and identity

Brian requested completion/saving of all finished work, then accepted the
recommended reading stage. PR19/20 complete the first part. Main/deployment is
8fdd3e4bb2282014bdb6b841a08cfec77d51e416. Closeout ownership and the incorporated
inactive PR11-17 tasks were released with remote context/handoff proof; their
files/branches remain available. No runtime files or user content were deleted.

New task: codex/hugin-reading-panel-mjolnir, exclusive Mjolnir worktree
C:/Users/brian/brian-projects/worktrees/hugin/hugin-reading-panel-mjolnir.
Control/preflight e3deecae6673a024aa9015a4387737fbec04c795. Ownership active.
Spec/plan/tasks in specs/2026-10-21-reading-panel/ are the working contract.
Resolve current commit/PR from fresh Git state, not a historical launch helper.

## Candidate changes

Reducer owns generated section vs played section and pause intent. Output emits
the played section only on first native submission after previous-section drain.
Pause/restart is job-bound and uses the existing native audio lock; stop bypasses
backpressure. Normal local callback/credit wait no longer uses the unrelated
initialization timeout, while framing and cancel/fault cleanup retain deadlines.
Optional Obsidian panel shows section text/count, pause/continue, stop and hide.
Session toggle and keyboard controls live in the main window. Automatic mapping
uses no-activate native styles and monitor work area. Presentation text is RAM
only, cleared at job end/hide, and excluded from diagnostics.

## Candidate verification

Guard failures reproduced before implementation: section/pause API missing;
normal paused server credit incorrectly timed out; client success terminal
incorrectly failed while last local callback exceeded readiness timeout.
Focused guards pass after the changes. Initial full suite 468 had only the
probe Output override signature failure; that consumer was fixed and its full
10-test focused/native run passes. Seven native UI visual checks pass after
correcting high-DPI layout. New native no-focus/clear controls and silent
waveOut pause/resume pass. These are synthetic fixtures, not voice acceptance.
Final full run passes471 in18.458s;19 native UI/reading/motion plus pure geometry
checks pass in9.535s after optional placement-failure isolation. New controller
guards cover stale controls, actual section publication, failed pause and
dictation preemption. Synthetic preview was visually checked and normally
closed. Spec review at709623c plus the small placement delta has no findings
(95 focused pure tests); standards review also passed without material findings
(58 focused pure tests), including the optional placement-failure delta.
PR21 https://github.com/valhalla-hq/hugin/pull/21 has three green hosted checks
at709623c; final checkpoint CI is verified separately on the exact PR head. See
docs/reading-panel-2026-10-21.md for exact measured/unmeasured boundaries.

## Runtime and return path

Live source remains frozen at d1331da in hugin-screenshot-formats-mjolnir.
Never edit it or remove ignored .runtime helpers. Original normal Quit restores
Whispering/PipPal. Do not kill by PID/name. Candidate worker files differ from
deployment; keep deployment unchanged until normal pilot exit or use a reviewed
owned launcher explicitly binding candidate worker source and unchanged assets.
No autostart/input migration, model/environment changes, private source content
or clipboard mutations belong to this task. Native fixture tests used silence.

## Next steps and starter

Finish final exact-head CI/integration, then prepare the checked pilot switch.
Do not advance deployment workers until the old pilot has exited normally.
Brian's old acceptance is not acceptance of
the new reading feature. Live Freya/Tyr usefulness, physical multi-monitor/DPI
movement and pause listening remain open until actually tested.

Continue from handoffs/2026-10-21-reading-panel.md. Preserve the live d1331da
pilot and deployment worker source. Complete the guarded optional reading panel
candidate, exact-head reviews/checks and private save; only then prepare a normal
pilot restart and user listening test. Do not add estimated word highlighting.
