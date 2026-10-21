# Plan

1. Add guards for state-bound controller button intents, native mouse activation
   and bounded card layout before implementation.
2. Own per-button SetWindowSubclass registrations on Tk's UI thread. Return
   MA_NOACTIVATE only for these buttons; otherwise DefSubclassProc. Explicit
   removal before root destruction; keep owners on failed cleanup. Check external
   foreground only as an early UI hint, never as delivery proof.
3. Project button availability and a (generation,state) token from Controller.
   Bind mouse intent at press; keyboard invocation stays independent. Validate
   token at ingress. Start/finish revalidate on dispatch; accepted interruptions
   are exact-job-bound so prompt cancellation survives that job's phase change.
   Reuse existing dictation/read effects and shortcuts.
4. Add native SoftButtons to the cards. Keep title, shortcuts and visibility;
   move glyphs to title row, action row below shortcut, visibility at bottom.
5. Run contract/integration, native synthetic and visual checks; review both
   lenses, checkpoint and exact-head private PR integration. Prepare launcher
   only in the new worktree and switch after normal application exits.

Risks: native callbacks must outlive registration; a normal activating click
before an action has no external source and must not use a stale window. Old UI
updates can race keyboard state changes; tokens make these requests harmless.
Rollback: normal Quit, restore checked prior launcher/source/runtime alignment.
No changes to workers, models, audio, source selection or clipboard formats.
