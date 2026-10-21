# Stop recording reliably

Brian reports that a button-started recording cannot be finished; shortcuts and
Escape also appeared ineffective. Normal tray Quit succeeded. The live UI showed
the own-foreground finish guard; no subsequent shortcut reached the controller's
last-input timestamp. The reason for missing physical shortcuts is not proved.

- REQ-001: Finish must stop recording even without an external editable target.
  Keep the transcript in RAM; delivery still requires the existing target proof.
- REQ-002: Preserve strict stale-click protection, external selection/focus,
  normal shortcut dispatch and cancellation. No remembered/forced target.
- OPS-001: Future test sessions must leave Whispering/PipPal closed after Hugin
  exits. Brian explicitly requests removal of automatic old-app return. Windows
  login startup settings remain outside this change; manual launch is the return.

Acceptance: native UI invocation with own foreground reaches finish; the actual
controller stops its synthetic microphone and retains text without a target;
native input message dispatch stops/cancels a button-started synthetic recording;
pilot launcher exits its owned family without dispatching either old app.
Physical keyboard and external mouse-only acceptance remain a user pilot check.
