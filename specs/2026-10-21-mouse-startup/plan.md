# Plan

1. Guard mouse dispatch and normal-launch persistence before code changes.
2. One binding definition supplies native dispatch and UI hints. Retain the
   existing message-loop owner; both modes register Ctrl+Alt+D/V, only explicit
   pilot omits the mouse hook.
3. A strict activation record in the configured state directory enables normal
   launches. A versioned profile names this exact mapping; startup only reads it.
4. A small explicit setup tool stages the native shortcut and activation record,
   retains original bytes/manifest under installation .runtime, and checks
   before/after hashes on apply and rollback. No automatic old-app relaunch.
5. Pure file/CLI fixtures, native shortcut roundtrip and isolated input tests;
   full contracts/integration, separate spec/standards reviews and hosted checks.
6. Integrate checked private PR, advance stable deployment, then quit the old
   app normally and apply reviewed migration. Launch normally; physical mouse
   acceptance follows. Rollback requires normal Quit, guarded restore, then
   explicit manual old-app launch if wanted. Never kill by historical PID.

Installation model/voice/runtime inputs and accepted focus/clipboard behavior
remain unchanged. A real login test is deferred to Brian's next normal login.
