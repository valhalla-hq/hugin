# Resolve the dictation field immediately before insertion

Brian reports intermittent target rejection after clicking elsewhere during a
recording and returning to the text field before stopping. He requests that the
latest chosen cursor receives the text and asks for a Whispering source comparison.
The physical repeat passed, so the exact historical failure remains unproven.

Observed: the separate bounded probe sees Group, Edit, and Document focus states
during the click flow. A Document snapshot can have unknown/mixed read-only for
the document and false for its selected range. These parallel samples do not
establish what Hugin itself saw at the failing stop.

Code evidence: Hugin resolves the full UIA field after microphone stop/cue but
before recognition. A failed field capture is retained for the entire job and
cannot recover even when the same native target is verifiable at delivery.
Whispering 7.11.0's pinned write_text path sends clipboard paste at delivery;
it does not bind an earlier UIA field. We adapt the timing, not unverified paste.

- REQ-001: Recording start and clicks during recording do not bind a destination.
  Stop captures the current native window/focus/process/caret basis. The expensive
  field proof runs once, in the delivery worker when final text is available.
- REQ-002: Before full field capture the current native basis must still equal
  the stop basis: HWND, native focus, process lifetime, class, native caret and
  selection where supplied. A change to that basis after stop is rejected.
  UIA field identity is intentionally first bound at delivery. In a Chromium
  surface sharing one native HWND/focus and exposing no native caret/selection,
  a different UIA field or caret after stop can therefore be chosen at delivery.
  There is no remembered window activation, global focus history, or fallback
  to an earlier field. This is a timing/selection change, not preservation of
  the former pre-recognition UIA field binding.
- REQ-003: Preserve full field/editability/selection/identity verification and
  final commit checks. A fresh field failure remains copy-only. No retries of a
  paste and no extra input injection.
- REQ-004: Publish the completed dictation to the clipboard even on target
  failure, as already requested. Cancel, shutdown and stale generation must
  prevent later insertion; no field probe should start for an already cancelled job.
- OPS-001: Keep capture_native and capture_field diagnostic phases accurate;
  capture_field is not_run during recognition, not_attempted with no native basis.
  Field work stays off the audio/controller owner; no extra UIA probe per job.

Acceptance: through Controller, A -> elsewhere -> B while recording must use B
at stop and fresh B proof at final text; an initially unavailable UIA field that
is valid by final text must insert. A different native target after stop rejects.
Same native Chromium basis with UIA field/selection A -> B after stop must use
the fresh B proof, never silently claim to have preserved A's early identity.
Persistent failure, missing native basis, cancellation/stale result, clipboard
persistence and the one-time delivery guards remain covered. Existing native
UIA fixtures prove unchanged proof behavior; physical Codex switch-back test
after loading the candidate remains a separate acceptance step.

Reference: https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src-tauri/src/lib.rs#L195-L240
