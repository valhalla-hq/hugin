# Persistent dictation clipboard

Brian reports failed insertion after the mouse rollout and explicitly requests
that every finished dictation also remain in the clipboard for Ctrl+V when the
field was missed. Diagnosis proves native_target_captured, target_captured,
delivery format_unsupported. Read-only reproduction on the unchanged clipboard
returned format_unsupported before any payload read: text plus OLE metadata,
including EnterpriseDataProtectionId. No evidence of a target-capture failure.

- REQ-001: A current completed dictation publishes Unicode text to the clipboard
  before optional automatic insertion. It intentionally replaces the old
  clipboard and remains available if the target is absent/changed/unapproved.
- REQ-002: Automatic paste retains every existing target, generation, token,
  modifier and at-most-once check. A newer external copy after publication wins;
  no overwrite/retry of that user copy. Cancel before publication changes nothing.
- REQ-003: Report clipboard publication separately from insertion; show the
  manual Ctrl+V fallback only when publication succeeded. RAM result remains.
- SEC-001: Keep automatic text excluded from clipboard history/cloud monitoring;
  no new text logs. Explicit Copy button behavior is unchanged. Current rendered
  clipboard persistence is intentional; an expiry of Hugin's RAM result does not
  erase the user's clipboard.
- OPS-001: Selection capture/read-aloud preserves its existing backup/recovery
  rules. Never broaden preservation to arbitrary OLE contents to solve dictation.

Acceptance: unsupported/oversize old content does not block dictation publication;
valid target receives once, wrong/missing target receives zero times but Ctrl+V
text remains. Early cancel and external-copy races remain guarded. Failed writes
never claim publication. Native fixture verifies rendered Unicode survives
backend close, supports a following selection snapshot, and pastes into its own
Edit only. Actual Codex/mouse acceptance remains user-observed.

Additional explicit steering: replace dictation Ctrl+Alt+D with Alt+Y for the
user's existing automation. Back/XBUTTON1 remains dictation; Forward/XBUTTON2
and Ctrl+Alt+V remain reading. The shared binding definition owns both native
modifiers and visible hints, in normal and pilot mode; startup never rewrites
this definition or the persistent mouse activation. This is the latest request
and supersedes the earlier Ctrl+Alt+D retention in the mouse-startup spec.
