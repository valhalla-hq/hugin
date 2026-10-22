# Natural reading sections: verification

Source candidate8a50dd91927a6312dafc40a3c2e865daf6dad96f; accepted baseline
main1c598dbf90dd5aa1aebf9f47a358f9d87f83ac8f. Both use codec batch16. The old
120-character opening policy is frozen in natural_baseline, not confused with
the historical240-character baseline. Native command:
`tools/probe_reading_start.py --root C:/Users/brian/Hugin --natural-sections --run`.

Brian normally quit Hugin. InstanceGuard excluded the live app; existing real
CUDA Qwen/Whisper workers generated and aligned only the three fixed synthetic
fixtures in the probe. Real Controller/native waveOut progress played equal-length
zero PCM. No speech, clipboard, microphone, hooks or preference writes; no audio
was persisted. Workers, executors, output and guard closed after both comparisons.

## Final comparison

Warm first native-buffer submission in seconds, baseline to candidate. Each
pair uses identical text and voice. Clause order is reversed to reduce systematic
order bias. These are one paired full read per fixture/voice, not p95 estimates.

| Voice / fixture | First submission old → new | Complete job old → new | Marked words old → new | Maximum new scheduling gap |
| --- | --- | --- | --- | --- |
| Freya / sentences | 3.098 → 4.007 | 15.519 → 16.270 | 31/31 → 31/31 | 0.85ms |
| Tyr / sentences | 3.044 → 3.957 | 15.294 → 16.288 | 31/31 → 31/31 | 0.59ms |
| Freya / clauses | 3.049 → 2.844 | 18.422 → 17.826 | 40/40 → 40/40 | 0.60ms |
| Tyr / clauses | 3.006 → 2.724 | 18.214 → 16.902 | 40/40 → 40/40 | 1.73ms |
| Freya / mixed | 3.343 → 2.819 | 23.761 → 22.927 | 36/52 → 38/52 | 0.53ms |
| Tyr / mixed | 3.126 → 2.925 | 22.825 → 22.719 | 52/52 → 52/52 | 0.94ms |

The sentence fixture moves from lengths114/113 (cut inside the second sentence)
to152/75, ending after complete sentences. Preparing more first-section speech
costs about0.91s here. Clause lengths120/161 become96/117/68; mixed81/92/155
becomes74/99/155. A shorter first section is not promised for every paragraph.

All normal sentence/clause sections aligned every source word, and native view
publication marked every one. The mixed Freya paragraph exposes a pre-existing
model-derived fallback: baseline rejects original range[0,81), candidate rejects
only[0,74), with all later ranges aligned. Its14 unmarked candidate lexemes are
a subset of the16 baseline unmarked lexemes; this is not a count-only comparison.
Tyr marks the entire mixed text under both policies. No timing is stretched or
estimated. The earlier word-highlighting report documents the general limitation,
but does not establish an identical internal cause for this new rejected path.

First cold Freya baseline submission including model load:24.401s; complete cold
read36.822s. Warm cases share workers. Total comparison264.772s; Controller CPU
7.734s. Warm worker-family CPU totals39.438s baseline and39.782s candidate across
the six cases each; including cold initialization, workers consumed113.704s CPU.
Cumulative individual family peak committed memory: TTS8,454,144,000 bytes,
STT3,247,542,272 bytes. They are not simultaneous process-family working-set or
GPU VRAM peaks. OS cache, physical-memory peak and agent-token cost are unmeasured.

## Rejected prototype and bounded correction

The first40-character-floor trial used58/94/75 for the sentence fixture. Freya
marked31/31, but Tyr's first section returned rejected_path, marking24/31 overall.
That candidate was not deployed. A60-character floor now groups the first two
whole sentences inside the existing160-character natural opening allowance;
the final comparison restores31/31 for both. The60-character floor is a measured
preparation choice, not a guarantee that every text obtains valid model timing.

Independent review also caught discarded whitespace/paragraph facts after
abbreviations, contiguous initials such as J.R.R., and short greetings left at
later section tails. Regression guards failed first and pass after producer-side
corrections. The old Coordinator parser is removed; consumers do not reinterpret
punctuation. Common DE/EN punctuation is heuristic, not full linguistic parsing.
Overlong unpunctuated sentences retain whole-word fallback under the240 cap.

Native drain-to-next-submission measurements exclude any added preparation stall
in these cases. They do not measure acoustic device onset or prove agreeable
prosody; natural pauses inside generated speech remain. User hearing feedback
for both voices is the remaining perceptual check after guarded deployment.
