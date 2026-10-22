# Hugin full-review fixes

Brian explicitly authorizes fixing all five confirmed findings and reviewing
the result again so the next stage can prepare a production build. Routine
checked private integration and guarded deployment are authorized.

Repository valhalla-hq/hugin, runtime Mjolnir; task hugin-review-fixes. Active
exclusive worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-review-fixes-mjolnir,
branch codex/hugin-review-fixes-mjolnir. Base46f157844917bbd601538b67413427f5129139e2;
control/preflight05181f9a99374ff8b298c626f903304f36ac8926. Specs and tasks are in
specs/2026-10-22-review-fixes/. Prior exact accepted handoff:
handoffs/2026-10-22-natural-sections.md. No PR was open initially.

Five independently reviewed and reproduced failures: native focus changes during
waiting proof can permit paste in another field; all short sentences lose natural
boundaries; transient cue/copy errors poison later UI; failed process creation plus
handle cleanup cannot retry; Controller tests consume and overwrite real preferences.

All five fixes have red/green guards. Native focus facts are rechecked after
waiting reads and at the last commit boundary; short sentences can form complete
groups; transient error lifecycle and held cleanup-owner errors are distinct;
the process owner exposes creation as an explicit fact; all five fake-controller
fixtures use disposable preferences. The old Coordinator parser stays removed.
Independent review also reproduced/fixed transient errors hiding current engine
faults and held cleanup failures remaining after a proven successful retry.
584 full checks pass in23.186s. Three exact-source disposable snapshots with
absent/Freya/Tyr synthetic installed preferences each pass all584 tests and
preserve the sentinels. Actual stable preference bytes are unchanged.
Docs check19requirements/17AC is clean; all29 Windows ABI checks pass.

PR45: https://github.com/valhalla-hq/hugin/pull/45. All51 relevant native cases
pass across final runs. Initially two ABI fakes lacked final focus facts; these
are corrected. Three panel cases initially stopped in setup when Windows
denied automatic foreground activation. After a normal click in an owned
launcher, all8 panel cases pass in2.756s. No security setting changed.

Real CUDA Freya/Tyr comparison completed using probe_reading_start --review-fixes
--run. Reference producer is frozen verbatim from accepted46f1578 plus provenance
comment, benchmark-only. Both voices preserve34/34 short-sentence and40/40 clause
word marks; every section aligns. Warm short-sentence start3.952->2.456s Freya
and3.822->2.260s Tyr; clause start2.855->2.780s and2.818->2.756s. Candidate
gaps<=0.86ms, no measured added preparation stall. Silent native PCM establishes
no new hearing/prosody claim. All workers closed. Nine reads total197.628s;
controller CPU5.453s, TTS67.124s, STT14.297s. Cumulative worker-family peak commit
TTS8,453,832,704/STT3,246,931,968bytes is not simultaneous whole-family working
set or VRAM. Cold baseline42.358s includes startup; no paired cold candidate.
Details and limits: docs/review-fixes-2026-10-22.md.

Implementation head4a5d46b618f2d2758d31fb00d6c08060b198f05e; src tree
398876deda8bb06b4ee6b3ebbdf8fa3c484e61b9. Independent spec and standards
review clear that source and final checked head97ebd0313ca630c8ca01b3c46ec4719667a64737.
PR45 merged as5fab470877f09510e23bd24c8e157f4f623f8bfb on22October08:17:10UTC;
the checked head and squash commit have identical complete trees.

All probes synthetic. After Brian's normal Quit, the clean stable main clone
updated from46f1578 to5fab470 under a freshly acquired InstanceGuard at
10:17:30 local. Junction C:/Users/brian/Hugin resolves to the stable clone.
Preference and activation bytes are unchanged. Normal non-pilot launch at
10:17:41 local loaded that source; its own Hugin window shows ready, Freya,
Alt+Y/mouse Back and the accepted panels. No app input was sent. The final
receipt checkpoint changes only Markdown; src remains398876de and the app
can keep running during its verified metadata-only FF.
Never kill by remembered PID; Whispering/PipPal stay disabled. Return path is
base46f1578 after normal Quit. Preserve runtime/model/voice assets and preferences.
No raw audio, clipboard, customer content, credentials or reports in Git.

This bounded correction is technically complete. Final documentation review,
checked receipt integration and verified workspace release close the session.
Ownership stays active until the tool proves a clean remote checkpoint with
CONTEXT and this handoff; then release through project_workspace.py. Retain
ignored synthetic reports in this worktree. Production packaging, actual next
login and the wider device/target matrix remain separate.

Starter: The five Hugin review fixes are complete and deployed from PR45. Read
CONTEXT, this exact handoff and docs/review-fixes-2026-10-22.md. Verify final
workspace release status before opening a new exclusive task for the next
explicitly requested production-build stage. Preserve runtime assets and the
accepted input, UI and audio word-timing behavior; do not restart review fixes
without a new reproduced finding.
