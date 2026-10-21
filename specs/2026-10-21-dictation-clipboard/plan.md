# Plan

The clipboard service owns one persistent publication per completed dictation;
remove delivery's obsolete old-content snapshot/restore. Keep selection capture
unchanged. Publish through the existing marked native transaction, preserving its
exclusion policy; recognize Hugin's own documented flat transaction format when
a later selection needs a snapshot. New transactions always mint a fresh token.
Native replacement checks cancellation under OpenClipboard before EmptyClipboard.

The application always asks this service to publish a current finished result,
even when target capture failed. It passes no target in that case, retains the
original capture error, and records separate publication/paste outcomes. Keep the
existing measured post-submit delay and all native/UIA proof checks.

Guard-first pure tests, producer ABI checks and isolated native clipboard fixture;
then full tests and separate reviews. Source stays in this task worktree while
the currently running main deployment remains frozen. Checked PR integration
and normal restart precede Brian's final real-field test. Startup links/profile
and mouse mapping stay as already migrated; no return of the old apps.
