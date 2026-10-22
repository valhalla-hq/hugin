# Further reading-start optimization, 22 October 2026

Baseline main 8f2c605 already uses the 120-character opening policy. The only
production change increases Qwen codec batches from 8 to 16. Section text,
seed, model, alignment, native position and one-section lookahead stay intact.
Installed faster-qwen3-tts 0.3.2 repeatedly decodes overlapping acoustic context;
fewer decodes reduce repeated work. Reference prompts are already cached there.

## Repeated warm preparation screen

`tools/probe_tts_batch.py --root C:/Users/brian/Hugin --run` uses production
WorkerClient/WorkerServer and a probe-only batch override. Two synthetic opening
sections (116 characters, 18/17 words), both voices, three repetitions per variant
in rotated 8/16/24 order, same resident CUDA workers. No playback/input devices.
All 36 normal runs aligned every expected word. Medians in seconds:

| Fixture | Voice | Batch 8 | Batch 16 | Batch 24 | 8 to 16 gain |
| --- | --- | ---: | ---: | ---: | ---: |
| Paragraph opening | Freya | 3.2012 | 2.8762 | 2.8217 | 10.2% |
| Paragraph opening | Tyr | 2.7630 | 2.4507 | 2.4456 | 11.3% |
| Long-sentence opening | Freya | 2.8332 | 2.4509 | 2.4569 | 13.5% |
| Long-sentence opening | Tyr | 2.6538 | 2.4019 | 2.4051 | 9.5% |

These measure TTS plus actual-audio alignment, not acoustic start latency.
First packet arrives later with larger batches; reading waits for a complete
aligned section. Batch 24 offers little additional benefit and cancels later.
Initialization: TTS 13.373s, STT 4.858s, separate from warm rows, not a cold 8/16
comparison. First baseline alignment included lazy warmup; repeated medians
reduce its effect. OS cache uncontrolled. Total 118.314s, controller CPU 0.156s.
Median combined worker CPU 8/16: Freya paragraph 3.1406/2.9531s; Tyr paragraph
2.6719/2.5469s; Freya long 2.8594/2.4063s; Tyr long 2.6562/2.4531s.
Peak family commit TTS 8,455,184,384 bytes; STT 3,251,421,184 bytes. These are
cumulative per-family, not simultaneous total, working set or GPU VRAM.

## Cancellation and ownership

The first screen cancelled before PCM. A final `--cancellation-only` run also
cancelled after its first received packet, with the next batch potentially in
progress. Batch 16 terminal latency before PCM 0.4534/0.4574s, after PCM
0.5592/0.5256s (Freya/Tyr). Batch 8 after PCM 0.3201/0.2956s; batch 24
0.7852/0.7791s. All 12 cases passed the existing 2s bound. This measures worker
release, not audible stop; production native stop/preemption logic is unchanged.

Independent review found that a cancelled callback could reach a reused screen
collector. Request-bound locked observations now reject closed/foreign events;
a deliberately delayed callback guard covers it. Final cancellation uses the
corrected collector. Original successful screen cases already waited for all
audio callbacks, and initial cancelled cases received no PCM; no contamination
was observed. Every probe held InstanceGuard until all owned workers closed.

## Full pipeline and isolated follow-up

`probe_reading_start.py --codec-batches --run` compares batch 8 with production 16
using current sections for both, actual alignment, native waveOut and equal-length
zero PCM. All 54/43 fixture words aligned and marked with both voices. Maximum
candidate scheduling gap (drain to successor submission) 0.84ms; generated silence
is excluded. No speech was played, so perceptual quality remains a hearing check.

First start 8/16: Freya paragraph 3.408/3.764s (regression), Freya long
3.307/3.122s, Tyr paragraph3.434/3.289s, Tyr long 3.302/3.183s. A local suite ran
during part of this first probe; its exact influence is unknown. The Freya
opening was therefore repeated alone with `--codec-recheck`, three warm pairs
in alternating order, no concurrent tests:

| Pair | Batch 8 | Batch 16 | Saved |
| --- | ---: | ---: | ---: |
| 1 | 3.884s | 3.586s | 0.298s |
| 2 | 3.793s | 3.445s | 0.348s |
| 3 | 3.695s | 3.463s | 0.232s |

All 18 opening words aligned/marked on every repeat. Median native start
3.793â†’3.463s (8.7%); individual paired gains 6.3â€“9.2%. Other full-text cases
saved 0.119â€“0.185s. These are synthetic warm results on this host, not a guarantee
for every text or the first model load. No speculative timing or weaker alignment.

Full native run: 217.536s elapsed, 6.562s controller CPU; cumulative family peak commit TTS 8,456,458,240 and STT 3,251,105,792 bytes. Isolated recheck: 96.903s elapsed, 1.938s controller CPU; peak commit TTS 8,454,156,288 and STT 3,250,847,744 bytes. Recheck median combined worker CPU fell from 3.703s to 3.140s. Cancellation run: 30.340s elapsed, 0.016s controller CPU. The same memory limitations above apply.

Raw technical reports stay ignored under `.runtime/tts-batch-screen.json`,
`tts-batch-cancel.json`, `codec-batch-native.json`, `codec-batch-recheck.json`.
They contain no text/audio; only curated evidence is committed. No microphone,
clipboard, personal dictation, startup or preference changes. Return path is
main 8f2c605 after normal Quit. Hearing feedback on both voices remains pending.
