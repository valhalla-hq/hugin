# Movable reading panel handoff

## Objective and authority

Brian accepts the show/hide feature. New bounded work: cohesive rounded Obsidian
overlay, show/hide centered at the bottom of the main Vorlesen card, header drag
and session position retention across jobs/hide/show. Existing audio, workers,
input, startup links and personal-data boundaries remain unchanged.

## Git state

- Private repository valhalla-hq/hugin; Mjolnir.
- Branch codex/hugin-reading-layout-mjolnir, base main a7404d8.
- Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-reading-layout-mjolnir.
- Ownership active; resolve exact head/PR/checks from fresh Git state.
- Control/preflight e3deecae6673a024aa9015a4387737fbec04c795.
- Spec/plan/tasks: specs/2026-10-21-reading-layout/.

## Changes and verification

reading_ui.py owns the canvas, size-bounded images, coordinates and drag state.
windows/reading_panel.py owns no-activate native movement, monitor selection and
rounded window region; failed region cleanup retains the handle until explicit
window-close retry. ui.py moves the existing visibility button into the reading
card and adjusts compact layout. Tests guard geometry, native focus, real rounded
region, text clearing, retained position and cleanup failure, plus card bounds.

Initial guards failed before implementation. Full contracts/integration passed
471 in 20.629s. Final native/geometry/UI/motion subset passed 19 in 9.482s after
the reviewed region-cleanup correction. Docs validator and whitespace check pass.
Synthetic preview: clicked, dragged from (600,788) to (380,760), hidden, reopened
at exactly (380,760), then closed normally. No user clipboard, speech or GPU.
Independent spec review: no P1/P2. Standards review identified lost region
ownership on deletion failure; implementation and regression guard corrected it.
Final standards re-review confirms the structural fix with no remaining material
findings or directly related cleanup. CI/integration must be resolved at the
exact saved PR head.

## Running state and boundaries

Live source 9d6273f in hugin-reading-visibility-mjolnir started 21 October
12:08:15 MESZ, deployment a7404d8. It is frozen; source/helpers must not be edited
or removed while live. Normal Quit returns original Whispering/PipPal shortcuts;
never kill applications by name or old PID. The previous reading pilot has an
owned-family exit receipt. Models/environments/startup links stay unchanged.

New code still needs the checked normal pilot switch and user layout/drag trial.
Physical mixed-DPI monitors and real monitor loss are unverified. Position and
visibility reset on app restart. Exact word timing remains deferred.

## Pick up / starter

Read this handoff, AGENTS.md and CONTEXT.md; resolve current Git/PR state. Complete
the reviewed routine private integration and prepare the owned launcher with
exact source/deployment/shortcut identity. After normal pilot and old-app exits,
start the candidate and ask Brian to drag the panel, hide/show it, and verify the
new action inside Vorlesen. Preserve the original return path and live source.
