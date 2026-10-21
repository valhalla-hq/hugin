# Hugin Context

Status: panel stop correction and test-session exit under review
Owner: Brian
Repository: private `valhalla-hq/hugin`; runtime Mjolnir.
Data boundary: curated source, configuration, locks and approved synthetic voice
references. No personal dictation, clipboard/image contents, recordings,
credentials, raw logs, model weights or virtual environments in Git.

## Current objective and authorization

Brian accepted the movable rounded reading panel on 21 October ("passt perfekt").
He now requests buttons in Diktieren and Vorlesen alongside keyboard control:
start recording, choose the external field during recording, finish/insert;
select external text and click Vorlesen. This bounded request authorizes routine
implementation and checked private integration under the central lifecycle.
No global target history, forced foreground restoration or binding migration.

The first PR24 pilot exposed a stop bug: the UI required external focus before
dispatching Finish, leaving a recording running when Hugin was foreground.
Brian also reported ineffective Ctrl+Alt+D/Escape; their physical failure is not
reproduced. Normal tray Quit succeeded. Fix recording stop independently from
delivery readiness; retain failed-delivery text in RAM.

Brian explicitly requests that Whispering/PipPal no longer restart after Hugin
exits during testing. Use tools/pilot_session.py, which has no old-app launch
path. This supersedes the old automatic-return test arrangement. Login startup
shortcuts remain unchanged; manual old-app launch remains available.

On 21 October 2026 Brian requested completion and saving of all finished work,
then the recommended next reading stage. This authorizes consolidation of the
finished PR11-18 stack through the central checked private integration workflow.
It supersedes the former screenshot-task restriction against merging that stack.
It does not authorize autostart/mouse-binding migration or claiming every V1
hardware/target criterion passed. No new broad feature belongs in this baseline.

Brian then tried the reading pilot and requested a clear main-window button to
show the panel again. His preferred behavior is to keep it hidden across reading
jobs until explicitly shown. This bounded UI correction retains session-only
visibility and leaves audio, selection, workers and cancellation unchanged.

Brian accepted the show/hide function, then requested matching rounded Obsidian
styling, the visibility action centered at the bottom of the Vorlesen card, and
a draggable overlay that keeps its placement. Position is session-only and
clamped to a reachable monitor on show/drop; no permanent position file.

## Accepted baseline

- Source: d1331da7fa13573e23dd86a04ab4f3301c6b3fcf, PR18 tip.
- Includes Word document-range handling, confirmed Codex dictation/selection
  replacement, three original Whispering cues, Obsidian/Nocturne UI and motion,
  active-mode highlighting, rounded control fixes and screenshot clipboard support.
- Brian confirmed the Codex screenshot-plus-dictation scenario on 21 October.
  Technical status at 10:22:31 MESZ: IDLE, native_target_captured,
  target_captured, submitted, no error, no pending cleanup.
- 462 contract/integration checks, focused/native evidence and independent reviews
  passed. All three hosted checks passed at d1331da. See the closeout handoff for
  the final cumulative review/check and integration proof.
- Cumulative review found one additional wide-window clipping bug. The closeout
  binds window/initial/minimum/font geometry to the same explicit 2048-pixel
  raster bound; no silent cropped surfaces. Seven native visual checks pass.
- Screenshot support is shared across applications for the proved format bundle;
  other target applications/clipboard producers have not all been accepted.
- Earlier target_changed and unassigned audio_failed observations are retained as
  separate unproven causes. Do not label them fixed by the screenshot change.

## Running state and return path

The PR24 pilot source 751f088241f0d8e1403ba7737225c397df430b10 in
C:/Users/brian/brian-projects/worktrees/hugin/hugin-panel-actions-mjolnir is stopped.
Its .runtime/pilot-session-c29822b6-6ef2-4f0f-bc18-2159534d4b00.json proves
own_family_exited true, exit_code 0 and historical return_dispatched. Brian then
closed both old apps normally. All temporary synthetic test windows are closed.
Future sessions use the checked no-return starter; old automatic-return helpers
must not be replayed. Fresh receipts determine current state, never stale PIDs.
The last user-accepted UI source remains 6dd1bde105f0bac292f91e996f5933604adb7bb2
(PR23), retained in hugin-reading-layout-mjolnir; its pilot also exited cleanly.

C:/Users/brian/Hugin is a junction to the deployment clone _repos/hugin. Its
runtime/worker inputs must stay byte-identical when advancing the checked source.
No model, environment, voice, original sound asset or startup-link replacement.
Historical helper plans pin an old deployment head: revalidate/update an owned
launcher before any later restart; never blindly replay an old starter.

## Active work

PR19/20, reading panel PR21, visibility PR22, layout PR23 and panel actions PR24
are merged; base main/deployment is ad9b0a083c0472eda06fc42546f88fccca9eea9f.
PR11 is merged through ancestry;
incorporated PR12-18 are closed. Closeout and inactive PR11-17 source ownerships
were released through the workspace tool; their recovery files remain.

Exclusive branch: codex/hugin-panel-stop-mjolnir.
Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-panel-stop-mjolnir.
Spec/plan/tasks: specs/2026-10-21-panel-stop/.
Finish no longer depends on external foreground; read-start guidance remains.
Existing generation/state, clipboard and target proofs are unchanged. The new
checked pilot starter owns its child family and exits without starting old apps.
481 contracts/integration, 26 native UI/geometry/motion checks, two native input
dispatch tests and one real owned-child launcher exit test pass. An own Hugin UI
with synthetic I/O confirmed button stop, Ctrl+Alt+D and Escape via Windows input.
Original physical shortcut failure and real Codex/Word button acceptance remain
explicitly unverified. Independent review and exact-head hosted checks follow.
Physical mixed-DPI/monitor loss and full Freya/Tyr
long-pause acceptance remain unverified beyond the user's general UI acceptance.
Preflight/control: e3deecae6673a024aa9015a4387737fbec04c795.
Ownership remains active until clean remote checkpoint/release proof.

## Active Handoff

- `handoffs/2026-10-21-panel-stop.md`

## Reading direction retained

Optional compact reading panel with current-section orientation; exact word
highlighting deferred pending measured synchronization with Freya and Tyr.
Pause/resume is the highest-value related control, but must preserve bounded
streaming, prompt cancellation and dictation priority. No fixed-rate fake timing,
no focus stealing, no extra speech model solely for animation, no new text log.
The explicit button refines the existing session preference; a restart returns
to the enabled default. Preserve the frozen live source until normal restart.
Other proposed usability improvements: actionable errors and exact build identity.

## Evidence and retained limits

- docs/word-document-2026-10-19.md: native Word evidence and user dictation tests.
- docs/whispering-cues-2026-10-19.md: pinned original sound identity and native output.
- docs/obsidian-ui-2026-10-19.md and docs/ui-refinement-2026-10-21.md: UI/native checks.
- docs/screenshot-formats-2026-10-21.md: format proof, native restoration and limits.
- docs/baseline-closeout-2026-10-21.md: cumulative acceptance and integration scope.
- specs/2026-10-14-hugin-v1/tasks.md retains unverified full target/device matrix,
  performance, physical production bindings and autostart/login migration.
