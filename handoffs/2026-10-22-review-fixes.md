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
584 full checks pass in23.186s; docs and29 Windows ABI checks pass.

PR45: https://github.com/valhalla-hq/hugin/pull/45. Initial native suite51 had
three foreground-eligibility setup failures and two incomplete ABI fakes; the
fakes now include final focus facts and all29 ABI checks pass. Worker/hotkey,
word-highlighting and UI-motion cases passed. Window placement will repeat in
an explicitly clicked owned test process. This is no permission-barrier bypass.

Brian normally quit Hugin. Real Freya/Tyr comparison is running using
probe_reading_start --review-fixes --run. Reference producer is frozen verbatim
from accepted46f1578 in tools/fixtures/reading_sections_46f1578.py. Only synthetic
short sentences and the unchanged clause fixture, silent native PCM, no input
or preference writes. Final evidence/review, CI/integration and deployment remain.

All probes synthetic. Hugin is still running accepted stable main; GPU/native
exclusive measurement and source deployment require normal Quit plus InstanceGuard.
Never kill by remembered PID; Whispering/PipPal stay disabled. Return path is
base46f1578 after normal Quit. Preserve runtime/model/voice assets and preferences.
No raw audio, clipboard, customer content, credentials or reports in Git.

Starter: Continue the five Hugin review fixes from this exact handoff. Keep
regressions guard-first, finish source fixes, run full checks and real both-voice
short-sentence verification, get independent review, then exact-head CI/merge and
guarded deployment. Record readiness and any actual production-build gates;
release only after the clean final checkpoint is remotely proven.
