# Review fixes before production packaging

Brian authorizes fixing all five confirmed findings from the full review of
main46f157844917bbd601538b67413427f5129139e2, then independently reviewing and
verifying the corrected result. Prepare readiness for the later production
build; this task does not claim an installer or next-login acceptance.

- REQ-001: A native target read must reject foreground, focus or caret changes
  during waiting queries. Paste must recheck the native focus basis after all
  waiting proof steps, before SendInput. No forced refocus or speculative paste.
- REQ-002: Multiple short normal sentences form complete bounded groups rather
  than losing every sentence boundary to the greeting heuristic. Preserve the
  accepted greeting grouping,60 speech floor,240 hard limit and original words.
- REQ-003: Transient cue/copy/diagnostic errors belong to their action lifecycle.
  Valid later actions restore truthful highlights and the reading panel; current
  input, worker and native cleanup faults remain visible until actually resolved.
- REQ-004: A failed-start process owner with no created process can retry owned
  handle cleanup, without waiting for a nonexistent exit or releasing a live
  family. Failed cleanup retains the same owner and shutdown barrier.
- REQ-005: Fake Controller tests use their own temporary preference state, never
  read or alter live voice preferences. Whole-suite outcome is identical with
  absent/Freya/Tyr live preferences, and original bytes remain unchanged.
- SEC-001: Regression probes use synthetic targets/text/handles. No personal
  clipboard/audio, downloaded models, startup changes or persistent content.
- NFR-001: Keep serial native ownership, bounded queues and actual-audio timing;
  no new dependency or unbounded retry, guessed word timing or increased cache.
- OPS-001: Check both voices on short-sentence groups with exclusive owned GPU
  resources, no audible speech. Normal Quit and InstanceGuard protect source
  deployment; rollback is accepted base46f1578 after normal Quit.

AC-001–005: Each REQ has a production-boundary regression that fails before its
fix and passes afterward. REQ001 also exercises the real commit seam with fake
native APIs; REQ004 uses the real OwnedProcess with a fake OS backend.
AC-006: Full contracts/integration, docs, relevant isolated Windows checks and
independent spec/standards review pass; no unresolved material review finding.
AC-007: Real Freya/Tyr short-sentence playback preserves word coverage versus
the baseline and has no added preparation stall. Any known model rejection is
reported by original source ranges, never hidden with invented timings.

Existing keyboard/mouse/panel actions, screenshot plus dictation, clipboard
fallback, reading-to-dictation preemption and accepted panel style remain.
Actual login, broad target/device matrix and production packaging stay explicit
verification boundaries; do not claim universal bug freedom from finite checks.
