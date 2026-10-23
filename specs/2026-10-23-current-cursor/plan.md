# Plan

Move destination ownership from coordinator/recording to NativeClipboard's
serialized fast commit. ClipboardService stages exactly once and binds only
transaction id/sequence; NativeClipboard selects the current native target
after the delivery worker reaches the owner queue. Remove the old stop target
transport and mandatory UIA proof from the dictation consumer. Preserve the
selection reader and its resource cleanup used by reading.

Use a parsed capture_status in ClipboardResult/ClipboardFailure so diagnostics
do not infer capture success from a later paste error. Keep the measured
post-paste settling delays, with the generic delay explicitly applying to
current-focus paste. No user preference or activation migration.

First regressions through Controller/ClipboardService/NativeClipboard; then
scoped/full CPU checks, native owned-target check and independent spec/standards
review. Build an additive1.0.1 candidate only after source checks; preserve all
1.0.0 binaries and installer. Automatic approval review rejected preparation of
the missing Inno compiler with only "blocked by policy". Do not retry that
action through another launcher. Prepare the app payload using existing native
compiler/offline wheels and the production builder's existing materialization,
asset and launcher functions; no new installer is claimed. Switch after normal Hugin Quit, preserving
preferences, cache, input profile and startup; never mutate an active release.
Real Codex acceptance and actual login are distinct pending observations.
