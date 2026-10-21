# Hugin faster reading start

Brian explicitly requests earlier first speech while preserving accepted word
timing/style A and smooth section transitions. Routine private implementation,
review, checked integration and normal deployment are authorized.

Repo valhalla-hq/hugin; runtime Mjolnir. Exclusive active task
hugin-reading-start, branch codex/hugin-reading-start-mjolnir, worktree
C:/Users/brian/brian-projects/worktrees/hugin/hugin-reading-start-mjolnir.
Base/main 9ec85225cbc8786d0b6fcfe1da65e8a570d39147. Control preflight verified
05181f9a99374ff8b298c626f903304f36ac8926. No initial open PRs.

Candidate changes only the section producer: first budget 120, later budget at
most 1.5 times preceding section length, floor 120, ceiling 240. Natural boundaries
in the last third avoid tiny greetings followed by oversized successors. Existing
serial worker/alignment/native-clock pipeline and one-successor bound stay intact.
No model, input, UI, startup or preferences changes.

Three section/start guards first failed on old policy (five assertions), then
passed on candidate. Full contracts/integration: 549 passed in 24.528 seconds;
docs check clean. The explicit tools/probe_reading_start.py compares frozen old
policy with current in the same workers; synthetic paragraphs and long sentences,
both voices, real alignment and native output with equal-length zero PCM.
No personal input, clipboard, hooks or audible speech. Reports only counts,
timing and process metrics under ignored .runtime.

Brian confirmed normal Quit for the exclusive measurement. Probe running under
InstanceGuard; real results not yet claimed. Stable C:/Users/brian/Hugin points
to _repos/hugin and remains at reviewed main. Whispering/PipPal stay disabled.
Never terminate via remembered PID. Prior word-highlight handoff retains history.

Initial real run closed all workers. Warm starts improved 42–50%, gaps <=1.04ms,
but Tyr's shifted 105-character remainder rejected alignment. A long sentence
also left a lone final word. Candidate refinements keep the first suitable sentence
boundary and absorb <=40-character final remnants. Independent reviews caught
word fragmentation when early whitespace was discarded and probe guard release
despite cleanup failure. Earlier whitespace/whole-token fallback now preserves
words; probe retains session/guard and retryable owners on failure, keeping
executors alive until controller cleanup, then closing all independently.
Ten focused boundary and cleanup checks pass after red/green reproductions.
Final real rerun and review remain pending; initial metrics are not acceptance.

Next: inspect real measurements and tune only if evidence requires it; independent
spec/standards reviews, hosted checks, exact-head merge and guarded stable update.
Return path: base main after normal Quit. Listening acceptance remains necessary
for changed sentence prosody; native silent playback proves only scheduling.

Starter: Continue faster reading start from this exact handoff and the matching
spec. Preserve accepted word timing and style A. Finish the real old/new probe,
then review/integrate/deploy only the checked scope. No repeated model downloads
or startup changes, and no return of Whispering/PipPal.
