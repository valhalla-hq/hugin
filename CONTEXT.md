# Hugin Context

Status: physical panel-button focus correction under review
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

PR19/20, reading panel PR21, visibility PR22, layout PR23, panel actions PR24
and stop/no-return PR25 are merged. Current base main/deployment is
392977f2fc824dff30522f645156bc855bc0bf26.
PR11 is merged through ancestry;
incorporated PR12-18 are closed. Closeout and inactive PR11-17 source ownerships
were released through the workspace tool; their recovery files remain.

Exclusive branch: codex/hugin-button-target-mjolnir.
Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-button-target-mjolnir.
Spec/plan/tasks: specs/2026-10-21-button-target/.
Brian confirms recording now stops, but native target capture fails before any
field probe or delivery. Physical Codex-to-button tracing reproduced a NULL
foreground at WM_MOUSEACTIVATE and through 500 ms after release. Protecting the
owned top-level with WS_EX_NOACTIVATE and retaining child MA_NOACTIVATE preserved
Codex focus and produced native capture success in the same physical probe.
ActionFocus now owns this wrapper policy; ordinary clicks activate only Hugin.
No external history/refocus, clipboard or input-proof changes. Cleanup restores
only added style bits and retains ownership on failure. 483 contracts/integration
(26.496 s) and 32 native UI/focus/geometry/motion tests (12.818 s) pass. Native
tests require their own foreground-eligible test window; background activation
denial is not a product success. Reviews and exact-head CI pending. Full live
dictation/reading acceptance is still pending; the probe used no audio or payloads.
The live PR25 source remains frozen at 0e283ac3ded9e34e34514ce8af884500fc5e47e7
in hugin-panel-stop-mjolnir. Its no-return receipt is
.runtime/pilot-session-e9462fe7-0c69-4eb2-ba0f-d6b1cb1cf343.json. Fresh receipt
state governs restart; normal Hugin Quit is sufficient, with no old-app return.
Physical mixed-DPI/monitor loss and full Freya/Tyr
long-pause acceptance remain unverified beyond the user's general UI acceptance.
Preflight/control: e3deecae6673a024aa9015a4387737fbec04c795.
Ownership remains active until clean remote checkpoint/release proof.

## Active Handoff

- `handoffs/2026-10-21-button-target.md`

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
