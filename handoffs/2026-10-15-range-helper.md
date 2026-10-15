# Windows selection range helper

## Objective and Git

- IA-001/002/005 under specs/2026-10-15-hugin-input-audio, Spec before code.
- Repository valhalla-hq/hugin; branch codex/hugin-range-20261015-mjolnir.
- Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-range-20261015-mjolnir.
- Exact base5a238677ce0ff915b141f313e7960434cf92ad28. Lifecycle tool only
  accepts remote branch bases, so regular open from origin/codex/hugin-pilot-fixes-mjolnir
  followed by Root-authorized local fast-forward to this exact Spec head.
- Control/preflight e3deecae6673a024aa9015a4387737fbec04c795; main bb700f0.
- Source commit41253ed6af45813012dd59db75504521e9441c8d, metadata separate.
- Follow-up source/test bf67105905e30dd9d1e7c669472f50fd0c7e2942 only;
  do not cherry-pick helper metadata. Root independently reproduced Core-P2:
  faulty collapsed derived points1/2 could alias real selection7..10 and8..11.
  Each derived point now must equal its original requested endpoint as well
  as collapse. Both boundaries individually/together and warm proof guarded.
- Ownership active at this checkpoint on Mjolnir. Root has now explicitly
  authorized private push of only this helper branch, ordinary workspace
  release after exact remote/Context/handoff preservation, then removal of
  this worktree and local branch. No own PR or merge. Root remains accountable
  for integration, review, policy and actual pilot.

## Source scope and contracts

- src/hugin/windows/selection.py and selection_probe.py: one ordered interval
  replaces collapsed-only caret; both endpoint enclosures and affinities,
  bounded UTF-16 prefixes and final fresh text-free selection/editability check.
- clipboard.py: identity/native producer only; ClipboardService policy untouched.
- UiaTargetIdentity(focus_id,root_id,start_id,end_id,focus_pid,selection,
  start_relation,end_relation). Both relations compare to DocumentRange.End.
  Four IDs of at most64 signed32-bit parts; selection0<=start<=end<=262144.
  Largest tested JSON3211B within4092B. Invisible noncollapsed spans fail closed.
- Requestversion4 requires operation selection/target/delivery; target response3.
  Old versions and editable/position/caret_id/element_id shapes have no alias.
  TTS text response remains1; its ancestor-provider _Binding is unchanged.
- WindowTarget.native_editable defaultsFalse. Native proof requires enabled
  known standard Edit/RichEdit, no password/readonly, valid EM_GETSEL and caret
  owned by the actual focused Edit. Style is read again after EM_GETSEL.
  Native ComboBox itself is unproven; its truly focused Edit child uses this
  existing path. Direct focused UIA ComboBox needs the complete Text+Value,
  editable/enabled/nonpassword, root ancestry and single-range proof.
- SelectionProbe.capture_target(base,cancelled) returns TargetResult;
  begin_delivery(base,cancelled) returns held DeliveryLease with result.identity,
  one confirm() and worker-owned close(). NativeClipboard.capture_target keeps
  expected/cancelled keywords. Transient lease/Job/EOF/stderr/cleanup unchanged.

## Verification

- Three initial behavior guards red: selection7..10, default native capability,
  complete focused UIA ComboBox. Then green after producer changes.
- Last selected endpoint10->11 during final GetText rejected; both endpoint
  IDs, readonly, disabled, embedded/unknown, UTF-16, local limits and affinity
  regressions covered. Native readonly-during-EM_GETSEL guard red, then green.
- tools/dev.py check --group contracts:308 tests green,3.316s.
- Final scoped Clipboard/Selection/Target/ABI:121 tests green,0.308s;
  Win32 calls mocked, no native input/clipboard/microphone/provider action.
- git diff --check clean; source diff self-reviewed against bounded Spec.
- Follow-up Core-P2 guard first red(target_captured), then122 scoped checks
  green0.297s; diffcheck clean. Collapsed fastpath unchanged.
- Follow-up active-branch preflight refuses missing remote task branch:
  this was under the initial no-push instruction. Clean local branch and
  unchanged active exclusive lifecycle record were read and confirmed;
  no tool/state override and no ownership release.
- Root owns independent review and native Codex selection/Chrome search/HiddenEdit
  proof. New selected-range warm latency is unmeasured; logical50ms unchanged.
  Collapsed path deduplicates endpoint ownership and prefix reads; start0 reads
  no text. Metadata contains no text; bounded prefixes stay only in child RAM.

## Running state and next step

No helper product/runtime started. Existing pilot/Altstack were untouched.
Root-owned generic policy/config/application changes are not in this branch.
Root has integrated the range source and independently reproduced the narrow
follow-up. Only source belongs in integration; helper metadata stays here.
The ordinary workspace tool must prove release before removal. Worktree is
clean with no ignored or untracked runtime/fixture files at cleanup precheck.

Starter: Read AGENTS.md, CONTEXT.md and this exact handoff. Re-prove branch,
clean head, remote preservation and current lifecycle ownership; retain the
no-native boundary and do not reclaim a released/removed worktree implicitly.
Continue only the bounded Windows range task. Do not modify Root or other helpers.
