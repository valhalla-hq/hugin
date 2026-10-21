# Panel actions handoff

## Objective and authority

Brian accepts PR23's movable Obsidian reading panel and requests explicit action
buttons: dictate, choose target during recording, finish/insert; select external
text then click Vorlesen. Implement and integrate this bounded routine private
change under the current central lifecycle. No new binding/autostart policy.

## Git state

- Repository: private valhalla-hq/hugin; runtime Mjolnir.
- Branch: codex/hugin-panel-actions-mjolnir; base main 35528f4ab8315b23e3fb848aacfc6bbcc343d4b9.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-panel-actions-mjolnir.
- Ownership active. Resolve exact checkpoint/PR/checks from fresh Git state.
- Preflight/control e3deecae6673a024aa9015a4387737fbec04c795.
- Spec/plan/tasks: specs/2026-10-21-panel-actions/.

## Changes and verification

application.py projects button state and binds intents to generation/state,
checking at ingress and queued owner dispatch. ui.py adds rounded panel actions
and local guidance when Hugin is already foreground. windows/action_focus.py owns
SetWindowSubclass registrations on the UI thread; no target history or forced
focus. Exact registration verification handles Tk's native procedure replacement
on destruction; failed removal retains ownership for retry. Existing native
field/selection, clipboard, audio, worker and input mechanisms are unchanged.

Initial controller guards failed on the missing API. Focus/cleanup tests exposed
a native test message with an invalid top-level parameter and Tk's destruction
behavior; message fixture and registration ownership were corrected. Full suite
initially identified __new__ fixtures missing the new constructor-owned field;
those fixtures were updated. Final full check: 477 tests in 22.505s, green.
Docs validator: 19 requirements/17 AC, no problems. Native GUI harness: 26 tests
green, including actual activation messages/Tk click bindings, owned
selection/focus retention, cleanup retry and compact/DPI placement. Earlier
background activation was blocked by Windows; ordinary own-window activation
allowed the repeated run. No global input, personal clipboard or speech models.
Existing silent PCM test ran. Synthetic preview visually checked idle/recording.
Independent spec review found a held mouse press being reinterpreted on release;
press-time binding and separate keyboard invocation fix it, including modifier
events while holding the mouse. Standards review found accepted cancellation
being rejected after same-job phase transition; exact-job _PanelInterruption
preserves the accepted cleanup/preemption. Both reviewed fixes have red-to-green
guards and no remaining material findings. Hosted exact-head CI remains pending.

## Running state and data boundary

Last accepted source 6dd1bde105f0bac292f91e996f5933604adb7bb2 in
C:/Users/brian/brian-projects/worktrees/hugin/hugin-reading-layout-mjolnir started
21 October 13:06:45 MESZ, deployment 35528f4. Receipt
.runtime/pilot-session-87ca3a44-f36c-4109-9c03-8dc199092351.json now confirms
return_dispatched, own_family_exited true, exit_code 0 and both startup shortcuts
dispatched. It is no longer running; preserve its source/helpers. Normal Quit returns original Whispering
and PipPal. Never stop processes by stale PID/name. No model/environment/startup
shortcut changes. Curated source/docs only; no user speech/text/screenshots,
credentials, raw logs or generated runtime artifacts in Git.

## Pick up / starter

Read AGENTS.md, CONTEXT.md and this exact handoff. Finish independent review and
checked private integration, prepare the owned launcher for the exact source and
deployment commits. After normal Hugin and returned-app exits, advance deployment
and start candidate. Then ask Brian for mouse-only dictation/selection tests with
Hugin visible beside the target. Real Codex/Word acceptance and physical monitor
matrix must not be inferred from synthetic tests. Keep ownership active until
normal rollout/acceptance and safe release conditions are proved.
