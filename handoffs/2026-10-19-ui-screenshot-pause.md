# Hugin UI refinement and screenshot diagnosis: paused

## Objective and authorization

Brian requested two visual refinements and investigation of dictation after
attaching a screenshot in the Codex composer. He then explicitly paused work
for today and requested that the state be saved. No further reproduction,
implementation or app restart is authorized by this pause checkpoint itself.
Continue the requested fixes when Brian resumes. Logo and animation are liked
and should remain as implemented.

## Git State

- Repository: `valhalla-hq/hugin`, private, Mjolnir.
- Branch: `codex/hugin-ui-screenshot-fix-mjolnir`.
- Worktree: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-ui-screenshot-fix-mjolnir`.
- Base: `codex/hugin-obsidian-ui-mjolnir`, exact
  `d395f1e2afd02e5f0ff04a0c150b801da15fd5a7` (PR16).
- Product source is unchanged from that base. This task only saves CONTEXT and
  this handoff. Resolve the documentation checkpoint head freshly from Git.
- PR: create the draft after the initial meaningful checkpoint, then record its
  URL here. No integration of PR11-16 or main rollout is implied.
- Control/preflight: `e3deecae6673a024aa9015a4387737fbec04c795`.
- Main/deployment: `defe3d8f0ef9e564da1936a77b931476cbafc98a`.
- Ownership: active until the clean remote checkpoint is verified; then release
  this task through the workspace tool. Keep the checkout for continuation.

## User requests and source findings

1. Highlight the Diktieren tile light blue while dictation is active, and the
   Vorlesen tile while reading is active. Current `ui.py` layout hard-codes
   dictation `accent=True` and reading `False`, independent of actual activity.
   Add an explicit presentation fact from Controller state for dictation/read
   preparation and execution; clear it for idle, cancellation and errors.
   Do not infer mode from translated labels or keep dictation always highlighted.
2. Remove dark rectangular corners around Freya/Tyr. `SoftButton` combines a
   transparent rounded image with a native rectangular `FIELD` background and
   focus border, over a different parent gradient. This explains the visible
   mismatch from source; a corrected render still needs native inspection.
   Preserve native keyboard invocation/focus and bounded hover frames. A likely
   approach is to compose each button image over its exact parent surface crop,
   with a rounded focus indicator; avoid a second synthetic button framework.
3. Diagnose the screenshot/dictation case before changing clipboard contracts.
   The supplied diagnostic records RECORDING at 14:02:20 MESZ, no error and no
   capture/delivery check yet. It is not evidence of the subsequent failure.

## Observations and uncertainty

- The Obsidian pilot at `d395f1e` was started at 13:59:23 MESZ. Its initial native
  window showed ready, no error. Brian subsequently approved the logo and the
  animation below it; this does not certify every workflow.
- Latest retained sanitized input status: 14:04:26 MESZ, IDLE,
  native_target_captured/target_captured/submitted, no error or pending cleanup.
  It does not identify whether that successful input contained an attachment.
- A read-only format enumeration before the pause found a stable list containing
  only CF_UNICODETEXT, CF_LOCALE, CF_TEXT and CF_OEMTEXT, all allowed. No data
  handles/content were fetched; no clipboard mutation or input was performed.
- Brian was asked to reproduce once, leaving the failed clipboard intact before
  using Diagnose kopieren. He paused instead. This request is superseded for
  today; no reproduction occurred and no particular rejected format is known.
- Prior related evidence is in `handoffs/2026-10-19-clipboard-format.md`:
  format_unsupported once recovered without a source change. Do not conflate it
  with this new report or claim a proven common cause.

## Clipboard boundary for continuation

`NativeClipboard.snapshot` enumerates first and rejects unknown formats before
GetClipboardData or staging. CF_DIB/CF_DIBV5 are already allowed; synthesized
CF_BITMAP is omitted only when a DIB source exists. Registered HTML/RTF and two
Chromium provenance formats are allowed as HGLOBAL. A screenshot might expose
another registered format or hit another boundary; that is currently inference.
Do not skip unknown formats, treat arbitrary handles as HGLOBAL, clear the
clipboard, or enlarge limits merely to hide the symptom. Capture format IDs and
names after a failed attempt, prove the concrete storage contract, then protect
restoration, unknown-format rejection, cancellation and target identity in tests.

Existing ignored metadata helper:
`C:/Users/brian/brian-projects/worktrees/hugin/hugin-clipboard-format-mjolnir/.runtime/read_clipboard_formats.py`.
It enumerates formats only. Read it before reuse. Codex UI must remain manually
operated by Brian; do not automate the Codex/ChatGPT desktop UI.

## Verification, running state and preservation

- No production code or tests changed; no new implementation verification claim.
  The inherited PR16 tests/checks remain historical proof of that base only.
- Check this checkpoint's docs and exact remote head before releasing ownership.
- The saved old pilot receipt still says pilot_running, but fresh process queries
  at pause returned none of the four observed launcher/supervisor/app processes
  and no matching Hugin/Whispering/PipPal command lines. Receipt is stale or the
  current process state is unknown; no normal own-family completion/return
  receipt was observed. No process was stopped or restarted by this work.
- Preserve the old Obsidian source path and helpers; do not delete/release its
  separate ownership merely because a PID is absent. Recheck at continuation.
- Personal dictation, clipboard contents, screenshots and raw logs are excluded
  from Git. Only the curated state above is saved. No automation is scheduled.

## Pick Up Here

1. Resume this exact released task through preflight/open --continue-existing
   after verifying ownership, remote head and this handoff; otherwise create a
   new exclusive worktree. Read fresh app/receipt state before any restart.
2. Implement the two bounded UI fixes and verify both modes, idle/error states,
   focus/hover/selection and native 100/150/200% rendering.
3. With Brian present, reproduce screenshot then dictation once and read only
   technical failure/format metadata before the clipboard is overwritten.
4. Make a narrow evidence-based clipboard fix if established, run regressions
   and independent review, save the checkpoint, then prepare the checked pilot.

## Starter Prompt

Continue Hugin from `handoffs/2026-10-19-ui-screenshot-pause.md`. Brian requested
active-mode tile highlighting, clean Freya/Tyr corners and investigation of
dictation with an attached screenshot, then paused before implementation. Keep
the approved logo/animation and existing source basis. Recheck exact Git/PR and
app state, implement/test the UI refinements, reproduce the clipboard failure
without losing its format evidence, and preserve the normal pilot return path.
