# Plan

1. Reproduce the physical click using the shipped Hugin UI and technical-only
   capture, without audio/models/clipboard payloads. Compare top-level protection.
2. Extend the existing ActionFocus owner, rather than introducing target history.
   Own and restore the wrapper style and subclass; preserve normal activation on
   ordinary clicks, and retain callback ownership if cleanup fails.
3. Add native lifecycle/interaction coverage and run relevant controller/input
   regressions. Separate native messages from physical cross-app evidence.
4. Independent spec/standards review, checked private PR integration, frozen live
   source until normal exit, then exact-source no-return pilot restart.

Rollback: restart the preceding checked pilot. No runtime, model, startup-link
or worker-input migration. Diagnostic traces stay ignored and contain no text.
