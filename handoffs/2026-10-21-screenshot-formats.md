# Hugin screenshot clipboard Handoff

## Objective and authorization

Fix Brian's reproduced screenshot-then-dictation failure in Codex while
retaining the approved UI, animation and original Whispering cues. Routine
diagnosis, implementation, reviewed checkpoint and checked pilot switch are
authorized. Older draft integration and product/autostart migration are outside
this follow-up. Native synthetic clipboard testing has explicit user setup;
never automate Codex input.

## Git State

- Repository: `valhalla-hq/hugin`, private; runtime Mjolnir.
- Branch: `codex/hugin-screenshot-formats-mjolnir`.
- Worktree: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-screenshot-formats-mjolnir`.
- Base: `codex/hugin-ui-screenshot-fix-mjolnir`, PR17,
  `c37874315876083b806951d659121f75dcd0e8e8`.
- HEAD: resolve this checkpoint's exact local and remote HEAD freshly.
- PR18: https://github.com/valhalla-hq/hugin/pull/18, stacked draft on PR17.
- Implementation checkpoint: `3bf2ef3d27b2d2dbe805d93b6600615642120788`;
  clean matching remote and both context files were verified after push.
- Ownership: active on Mjolnir through the workspace tool.
- Preflight/control: `e3deecae6673a024aa9015a4387737fbec04c795`.
- Deployment/main: `defe3d8f0ef9e564da1936a77b931476cbafc98a`, unchanged.

## Changed Files

`clipboard_formats.py` owns the closed raster policy, strict small proof
protocol and bounded helper lifetime. `clipboard_formats_probe.py` enumerates
public OLE metadata without image contents. `clipboard.py` binds that proof to
its native snapshot and preserves PNG/policy bytes; its staged text excludes
history/cloud monitoring. Tests cover protocol, races, ownership and byte
restoration, plus an opt-in C#/PowerShell synthetic OLE producer and native RichEdit
paste. The spec, curated evidence, CONTEXT and this exact handoff record scope.

## Verification

- 462 contracts/integration tests, Python 3.12.10 `-S`: pass, 20.769 s.
- 60 focused policy/ABI/clipboard tests: pass, 0.009 s.
- Separate spec/standards reviews: no product-path findings.
- Final fixture standards review: no new material findings; 69 pure checks pass.
  Stream/bitmap selfchecks also pass without any clipboard access. The final
  trace bound, bitmap selfcheck and added original-byte assertion were reviewed
  after the successful native run; no additional user-clipboard run was made.
- Fixture review corrected stale sequence adoption and long startup race;
  final publication still needs the explicit no-concurrent-copy test setup.
- Native synthetic roundtrip: pass, 0.708s; exact PNG/DIB/DIBV5/policy bytes,
  native RichEdit WM_PASTE with Unicode/selection replacement, restored PNG read
  independently as IStream, original text restored and provider family closed.
  Fixture defects were repaired at their owner: exact stream size/exit position,
  GetDataHere and explicit GDI lifetime, plus OLE ownership on delayed-render
  cleanup. One earlier failed run left the synthetic image; the replacement
  diagnosis copy supplied by Brian was restored on subsequent runs.
- Native production metadata helper: pass for the current eight-format raster
  bundle, 0.1469 s, owned helper closed. No image contents read or clipboard writes.
- Docs validator: 19 requirements/17 acceptance criteria, no problems; diff clean.
- Hosted baseline and both contracts passed at620fdde (runs39564818239,
  39564818247,39564813328). Recheck the final new head. Human Codex acceptance pending.

See `docs/screenshot-formats-2026-10-21.md` for exact observed formats, design,
source contracts and limits. The earlier focus rejection remains a distinct
unresolved observation; this fix addresses the demonstrated format rejection.

## Source And Data Boundary

Only curated metadata and synthetic fixture source enter Git. Exclude personal
screenshots, clipboard bytes, dictation, audio, raw logs, local `.runtime`,
generated media and environments. No new dependencies or Windows setting changes.

## Running State

The live UI pilot runs from
`C:/Users/brian/brian-projects/worktrees/hugin/hugin-ui-screenshot-fix-mjolnir`
at c378743, started09:16:07 MESZ after Brian confirmed normal exits. Keep that
source/helper path untouched. Historical observed supervisor13148 and app26476
are not ownership authority; reread receipts/process state. Its automatic normal
return uses the unchanged Whispering/PipPal startup shortcuts.

Candidate `.runtime` helper copies must match the existing reviewed helpers:
pilot C1F967DE5DEDFD9B566F51D8ECD9E7AF21B7218DA349DE8BEC786CA6C6370F78,
diagnostic F43685C031CDD2CB36165DC0AD8ACFEB1F5B81C78E4CC748A8CF4EA4C386E1D4,
trace 9912B6606B7653819AF06E8A07EC28F4DC4AA4D25768F160674E18A0630658A2.
Run plan mode for the exact clean checked candidate head before switching.
Normal old Hugin exit returns Whispering/PipPal; Brian normally closes those
before candidate start. No image-name or historical-PID termination.

## Open Blockers

No new clipboard setup is pending. Native verification passed; real Codex
screenshot/dictation confirmation remains after the checked pilot switch.
Brian additionally requested comparison with original Whispering: pinned7.11.0
write_text preserves only optional text, not images, then Ctrl+V after50ms and
restores after100ms. Details and exact sources are in the evidence document.

## Pick Up Here

1. Finish final fixture-delta review, update this exact handoff and CONTEXT,
   commit only reviewed files, push, update attached draft PR18, verify exact-head CI
   and remote presence of both context files.
2. Prepare checked helpers and perform the normal pilot switch, then request
   Brian's Codex screenshot/dictation test. Keep live source frozen afterward.

## Starter Prompt

Continue `valhalla-hq/hugin` from `handoffs/2026-10-21-screenshot-formats.md`.
Read AGENTS, CONTEXT, this exact handoff and fresh Git/ownership/app state. The
closed raster clipboard fix is implemented and native-verified; finish the
checked pilot switch, then obtain manual Codex acceptance.
Preserve the separate focus guard and existing live pilot; do not merge the
older draft stack or automate Codex input.
