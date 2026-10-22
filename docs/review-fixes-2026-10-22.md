# Full-review corrections before production packaging

Scope: five reproduced findings against accepted main `46f1578`, plus two
directly related error-lifecycle regressions found during independent review.
Production source reviewed and measured: `src` tree
`398876deda8bb06b4ee6b3ebbdf8fa3c484e61b9`, implementation head `4a5d46b`.

## Corrections and regression evidence

| Finding | Producing boundary and structural correction | Verification |
| --- | --- | --- |
| P1: focus can change during waiting proof before paste | NativeClipboard owns one cheap native-focus representation, rechecks after waiting reads and immediately before SendInput. No speculative paste or forced refocus. | Stable capture/commit succeeds; foreground, field and caret changes during native/UIA waits reject delivery. |
| P2: short sentences lose every natural boundary | Section producer retains the greeting preference, then falls back to available complete sentence groups before a word boundary. Existing size/speech limits remain. | Repeated short sentences, mixed punctuation and the accepted greeting cases; real Freya/Tyr comparison below. |
| P2: recoverable cue/copy errors poison later UI | Action errors have a lifecycle separate from runtime faults. Cue results carry their owning job; stale results cannot poison a later generation. | Failed cue/copy followed by successful recording, reading or copy restores the correct UI; held cleanup and current engine faults remain visible. |
| P2: failed creation plus failed handle close cannot retry | OwnedProcess exposes whether a process was actually created. WorkerClient skips impossible exit waits only for an explicit false creation fact and retries cleanup through the retained owner. | Real owner with a fake OS fails creation and two close attempts, then releases the same handles; unknown/live process paths still require exit proof. |
| P2: Controller fixtures consume/write installed preferences | All five fake-controller fixture families own temporary state directories. No save/restore of installed settings is needed. | Real fixture guards prove default voice and byte preservation; the full preference matrix below passes. |

Each initial finding was reproduced before its correction and passes afterward.
Related red/green guards also cover a transient error hiding a current engine
fault, and a held cleanup error remaining visible after its successful retry.
There are no known directly related cleanup changes deferred from this scope.

## Verification

- Full contracts/integration: 584 tests pass in 23.186 seconds.
- Three disposable exact-source snapshots simulate absent, Freya and Tyr
  installed preferences. Each runs all 584 tests; absence/original bytes are
  preserved (28.027 / 27.676 / 27.179 seconds of tests). The actual installed
  preference bytes also remain unchanged.
- Documentation check: 19 requirements, 17 acceptance criteria, no problems.
- Relevant Windows coverage: 51 distinct cases across ABI/hotkeys, private
  delivery IPC, owned processes, word drawing, UI motion and reading-panel
  placement. All pass across the final runs.
- The first native run exposed two incomplete test fakes, corrected to include
  the final focus check. Three placement cases initially stopped in setup
  because Windows denied automatic foreground activation. All eight panel
  cases then passed in 2.756 seconds after a normal click in the owned test
  launcher granted foreground eligibility. No security setting was changed.
- Independent spec and standards reviewers clear the exact production source.
  Hosted checks and deployment are recorded in the active handoff.

No personal clipboard, microphone input or user text was used. Native probes
use owned windows, synthetic text/handles, and silent playback. Raw reports
remain in ignored `.runtime`; no generated audio or traces are committed.

## Real voice comparison

`tools/probe_reading_start.py --root <stable-root> --review-fixes --run`
compares the candidate with the verbatim frozen section producer from
`46f1578`. Both use real CUDA Qwen/Whisper workers and the real Controller and
waveOut clock, with equal-duration zero PCM instead of audible speech. One
successor is prepared. Freya runs baseline first; Tyr runs candidate first.

| Warm case | First playback: old → fixed | Whole read: old → fixed | Marked words: old / fixed | Fixed scheduling gaps |
| --- | --- | --- | --- | --- |
| Freya, short sentences | 3.952 → 2.456 s | 19.082 → 16.383 s | 34 / 34 | 0.37 ms |
| Tyr, short sentences | 3.822 → 2.260 s | 18.002 → 15.307 s | 34 / 34 | 0.86 ms |
| Freya, clauses | 2.855 → 2.780 s | 17.855 → 17.781 s | 40 / 40 | 0.73, 0.26 ms |
| Tyr, clauses | 2.818 → 2.756 s | 17.009 → 16.933 s | 40 / 40 | 0.61, 0.50 ms |

Every section is aligned; marked-count and alignment-count checks cover all
source words for these fixtures. Short-sentence section lengths change from
115/108 to 66/157 characters, with complete sentence ends. Clause lengths stay
96/117/68. There is no added preparation stall in these measured transitions.
The silent clock probe does not establish perceived prosody or listening
accuracy; Brian's preceding both-voice hearing acceptance remains separate.

The nine-read session took 197.628 seconds, including the initial cold-model
baseline. Controller CPU was 5.453 seconds; worker CPU totaled 67.124 seconds
TTS and 14.297 seconds STT. Warm worker CPU per completed comparison:

| Case | TTS old → fixed | STT old → fixed |
| --- | --- | --- |
| Freya short sentences | 5.859 → 5.484 s | 0.188 → 0.422 s |
| Tyr short sentences | 5.547 → 5.156 s | 0.172 → 0.453 s |
| Freya clauses | 5.938 → 6.156 s | 0.312 → 0.172 s |
| Tyr clauses | 5.812 → 5.797 s | 0.422 → 0.156 s |

Cold baseline first playback was 42.358 seconds including model startup;
there is no paired cold candidate result. Workers share warm models and OS
caches are uncontrolled, so this is a bounded comparison, not a statistical
speed guarantee. Cumulative worker-family peak commit was 8,453,832,704 bytes
TTS and 3,246,931,968 bytes STT. These are not simultaneous working-set,
whole-session process-family peak, or GPU VRAM measurements. Those costs and
agent token usage were not instrumented. All workers closed successfully.

## Readiness and limits

The five confirmed review defects are corrected and regression-tested. This
supports the next production-packaging stage, not universal bug freedom.
Installer/build reproducibility, actual next-login acceptance, and the broader
device/target matrix remain explicit work for that stage. No dependency,
model, startup binding or accepted input profile changed in this correction.
PR45 passed exact-head hosted checks and merged as `5fab470`. The clean stable
main clone deployed under InstanceGuard on 22 October at 10:17:30 local;
preference and activation bytes stayed identical. Hugin restarted at 10:17:41,
and its own window was observed ready. The final receipt is Markdown only and
requires no further app restart.
Return path after normal Quit: accepted main `46f1578`, preserving runtime
assets and preferences; source deployment requires InstanceGuard ownership.
