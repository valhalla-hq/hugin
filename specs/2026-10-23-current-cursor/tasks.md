# Tasks

- [x] T001 Reproduce current-focus rejection with controller/native-boundary
  regression guards (REQ-001/002), retaining the precise observation limits.
- [x] T002 Move target capture to commit; remove early transport and UIA gate;
  preserve clipboard/cancel/input guards and diagnostics (REQ-001..004/OPS-001).
- [x] T003 Run focused and full CPU checks, native synthetic target checks,
  independently review both lenses, then checkpoint exact remote head.
- [x] T004 Prepare additive app-only candidate; verify all private runtimes,
  current-focus/native guards, two real hidden starts and preserved inputs.
  Immutable1.0.0 installer/installation/startup remain the return path (OPS-001).
- [ ] T005 Physical target-switch acceptance: Codex/Google confirmed, Teams
  fails at same-PID native gate despite verified cross-process child focus.
  Correct/review this boundary and repeat on a new immutable candidate. Login stays
  separately open. A new1.0.1 installer is blocked by automatic approval review
  of compiler provisioning; do not retry via another launcher (OPS-001).
- [x] T006 Reproduce Teams cross-process child focus, replace the PID gate at
  the native producer, preserve final guard and review both lenses.46 focused,
  536 full tests pass. Prepare new immutable1.0.2 and finish T005 separately.
