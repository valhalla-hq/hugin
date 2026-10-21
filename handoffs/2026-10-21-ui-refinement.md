# Hugin UI refinement and focused-field diagnosis

## Objective and authorization

Brian resumed the paused task on 21 October: light-blue active workflow tiles,
seamless Freya/Tyr controls, and investigation of dictation after attaching a
screenshot in Codex. Preserve the approved logo, animation and original cues.
Routine implementation, verification, checkpoint and checked pilot preparation
are in scope. Do not integrate the older draft stack or migrate autostart/bindings.

## Git state

- Repository: `valhalla-hq/hugin`, private; runtime Mjolnir.
- Branch: `codex/hugin-ui-screenshot-fix-mjolnir`.
- Worktree: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-ui-screenshot-fix-mjolnir`.
- Base: PR16 `codex/hugin-obsidian-ui-mjolnir`, product head
  `d395f1e2afd02e5f0ff04a0c150b801da15fd5a7`.
- Reclaimed checkpoint: `eb99db9abbd562be30729b9b054247c8c1e5aad7`.
  Resolve the final checkpoint HEAD/remote freshly; this file belongs to it.
- PR17: https://github.com/valhalla-hq/hugin/pull/17, draft.
- Control/preflight: `e3deecae6673a024aa9015a4387737fbec04c795`.
- Deployment/main: `defe3d8f0ef9e564da1936a77b931476cbafc98a`, unchanged.
- Ownership: active, reclaimed through `open --continue-existing` after clean
  matching task/runtime/remote proof. Never edit `_state` manually.

## Changed files and verification

`application.py` owns the active action fact; `ui.py`, `branding.py` and
`ui_controls.py` render bounded tile/button frames with matching backgrounds.
`tools/preview_ui.py` supplies synthetic actions. Presentation/native tests,
`specs/2026-10-21-ui-refinement`, CONTEXT and
`docs/ui-refinement-2026-10-21.md` record the scope and proof.

- 453 contract/integration checks with Python 3.12.10 `-S`: pass, 27.513 s.
- 40 targeted UI/motion/startup/presentation checks: pass, 6.718 s; three
  additional native UI lifecycle/focus tests: pass, 0.807 s.
- Native fixtures check 100/150/200% layout, parent-matching corners during
  focus/hover, bounded image counts, native keyboard and disabled behavior.
- Synthetic recording and reading previews inspected: correct active tile,
  matching voice-button corners. Both previews exited automatically.
- Separate spec and standards reviews: no material findings; reviewers ran
  65 and 43 pure tests respectively. They did not certify native rendering.
- Docs validator: 19 requirements/17 acceptance criteria, no problems;
  `git diff --check` clean. Exact pushed-head CI must be checked before launch.

## Reproduced failure and unresolved question

Manual Codex attempt 08:46:21 MESZ: `capture_native=native_target_captured`,
`capture_field=target_changed`, `delivery=not_attempted`, no pending cleanup.
The old pilot's bounded rejection trace reports `_field_pattern`, line168,
producer SHA256 `588829e4aa16673711b1065b2c84fbdcd9bfc6de95495236fedf42d994dd0e93`.
That guard rejects a missing focused element or false HasKeyboardFocus flag.
No clipboard snapshot/paste was attempted. Do not conflate this with the
separate 19 October `format_unsupported` case.

Later read-only enumeration found stable CF_UNICODETEXT/CF_LOCALE/CF_TEXT/
CF_OEMTEXT only. The supplied diagnostic had already replaced the screenshot
clipboard, so original formats remain unknown. No clipboard bytes read/written.
Brian was asked whether the writing cursor remained in the composer after the
attachment and through stop; answer was still pending at checkpoint preparation.
Do not guess a target or loosen identity/editability guards.

## Running state and pilot preparation

The old Obsidian pilot was started at08:42:43 MESZ from
`C:/Users/brian/brian-projects/worktrees/hugin/hugin-obsidian-ui-mjolnir` after
fresh process checks found no matching voice apps. Observed supervisor37320,
app redirector35544 and actual app26100; these are historical observations,
not ownership proof. Read current receipt/status/process state freshly.
The current receipt among `.runtime/pilot-session-*.json` identifies that
supervisor; an older October19 receipt is stale. Preserve this live source and
helpers until normal family exit. Its source remains d395f1e, not the UI candidate.

Candidate `.runtime` contains copied pilot/diagnostic helpers. Pilot helper
SHA256 C1F967DE5DEDFD9B566F51D8ECD9E7AF21B7218DA349DE8BEC786CA6C6370F78;
diagnostic launcher F43685C031CDD2CB36165DC0AD8ACFEB1F5B81C78E4CC748A8CF4EA4C386E1D4.
The candidate-only trace adds bounded producer call stages and whether the
already-held focus pointer exists, with no additional provider queries or text.
SHA256 9912B6606B7653819AF06E8A07EC28F4DC4AA4D25768F160674E18A0630658A2.
Its isolated fixture passed for absent and unfocused elements, unchanged result
and no second provider-property query. Old live helper is untouched.

Before candidate launch, prove clean exact checked HEAD and run plan mode with
the existing runtime Python and `.runtime/pilot_candidate_session.pyw --head
<fullhead>`. It checks source/runtime/worker inputs and original shortcut hashes.
Brian must normally quit old Hugin and then the returned Whispering/PipPal;
do not kill by image name or stale PID. After normal completion and fresh no-
conflict proof, start the candidate `--run` hidden. New receipt and source then
become a live dependency; record actual start/status, keep source unchanged.

No credentials, screenshots, personal dictation, audio, clipboard content,
raw logs or generated previews belong in Git. No dependency or setting changes.

## Pick up here

1. Resolve Brian's focus answer and compare the same screenshot with an explicit
   composer click/visible cursor. Operate Codex manually only; leave original
   clipboard untouched if it fails again. Read sanitized status/trace.
2. Verify exact pushed-head CI and prepare/perform the checked UI pilot switch
   through normal exits. Do not report the new UI as live until verified.
3. If focus is confirmed yet still rejected, use the new bounded trace to narrow
   initial capture versus confirmation, reproduce that producer boundary and
   fix only when evidence justifies it. Preserve target and restoration guards.

## Starter prompt

Continue Hugin from `handoffs/2026-10-21-ui-refinement.md`. Read AGENTS, CONTEXT,
the current PR17 and exact Git/ownership/app state. UI fixes are implemented and
locally reviewed; the reproduced screenshot failure is missing field-focus
confirmation before clipboard delivery. Preserve the live old pilot source,
check CI and switch to the candidate through normal app exits, then finish the
manual focus comparison without inventing a clipboard fix.
