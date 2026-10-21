# Reading visibility handoff

## Objective and authority

Brian tried the reading panel and requests an explicit main-window Einblenden
button. His final preference keeps hiding across reading jobs until deliberately
shown again. Bounded routine UI work; no new persistence, audio, workers, input
hooks, autostart or model changes. Exact word highlighting remains deferred.

## Git and ownership

- Repository: private valhalla-hq/hugin, runtime Mjolnir.
- Branch: codex/hugin-reading-visibility-mjolnir, base main a52a51c.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-reading-visibility-mjolnir.
- Ownership active. Resolve exact checked commit and PR from fresh Git state.
- Control/preflight: e3deecae6673a024aa9015a4387737fbec04c795.

## Change and evidence

src/hugin/ui.py replaces the small visibility checkbox with a SoftButton,
keeps one plain UI boolean, and routes panel hide and main-button show/hide
through the same operation. Reopening renders the latest view immediately;
no audio action is dispatched. Existing native tests now invoke that button,
retain hidden state across a new job, and check current text and focus.
Spec, README and reading-panel evidence clarify app-session visibility.

The own-window scenario failed first on the missing native button. Then 14
native UI/focus/motion checks passed in 7.568s. Synthetic preview hide/show was
visually checked. Independent read-only spec and standards review: no findings.
No personal text, clipboard, live audio, models or GPU used by these checks.
Final docs/hosted checks and integration must be resolved from the exact PR head.

## Running state and return path

The unchanged live source is 5448c79 in hugin-reading-panel-mjolnir, started
21 October at 11:25:18 MESZ. It uses deployment a52a51c and reports technical
IDLE with no error/cleanup pending. Brian reports general success; complete
Freya/Tyr, long-pause and physical monitor coverage is not claimed.
Keep its source and ignored helpers frozen until normal user-controlled Quit.
Normal Quit returns Whispering/PipPal via unchanged original startup shortcuts.
Never stop applications by stale PID/name. Prepare the checked replacement
launcher in this new worktree; verify current source/deployment/shortcut identity.

## Pick up / starter

Continue from this exact handoff, AGENTS.md and CONTEXT.md. Review current Git
and PR state. Complete authorized checked integration, prepare the new launcher
and switch only after normal pilot/old-app exits. Ask Brian to try Ausblenden,
then Mitleseleiste einblenden during reading and across a new selected text.
Preserve all unrelated runtime files and the original return path.
