# Plan

Move the owning full field-capture call from StopRecording's audio worker to
StageDelivery's existing delivery worker. Carry the native stop result through
recognition; re-use capture_target(expected=...) for native identity and fresh
UIA verification. Do not introduce a second retry path, protocol, timer or cache.
Preserve publication on failed target and the original failure reason.
Native stop identity remains exact; UIA field/selection is intentionally late.
Prove the same-native/different-UIA consequence through real Controller,
ClipboardService and NativeClipboard.capture_target with synthetic provider I/O.

Guard first at Controller's public command/worker-event seam with a mutable
synthetic focus and UIA readiness, asserting the exact capture/delivery targets.
Check after-stop target change, late persistent failure and cancellation.
Run contracts/integration and docs, then independent reviews and hosted checks.
After normal Hugin Quit deploy from merged main; retain existing runtime/model
inputs and activation. Rollback is the previous code at main7ac3cc6 after Quit.
