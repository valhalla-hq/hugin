# Faster reading start

Brian requests a shorter wait before speech while preserving the accepted
audio-based word timing and avoiding distracting section gaps. Base: main
9ec85225cbc8786d0b6fcfe1da65e8a570d39147. The visual style A stays unchanged.

- REQ-001: Prepare a shorter first section for long selections. Keep natural
  boundaries where possible and avoid a tiny opening sentence followed by a
  much larger section. Short selections remain a single section. Start/growth
  budgets are soft: intact words and absorbing a small final remainder take
  precedence, within the unchanged 240-character hard limit.
- REQ-002: Preserve every spoken character, original word offsets and actual
  audio alignment before playback. No duration estimates or early unaligned audio.
- REQ-003: Keep one prepared successor during playback, serial GPU ownership,
  pause/resume, cancellation and dictation preemption. Do not add a document cache.
- NFR-001: Compare the same synthetic selections and both voices with the old
  and new policy, separating model initialization from warm start. Aim for at
  least 25% less warm preparation on long examples, with no preparation-induced
  gap above 100ms in the native playback probe. These are measured fixture gates,
  not a latency guarantee under arbitrary load.
- SEC-001: No personal text/audio, clipboard, microphone, hooks, preferences,
  model downloads or dependency changes in the measurements. Synthetic audio
  stays in RAM; reports retain counts, timing and resource metrics only.
- OPS-001: Exclusive real-GPU probe and stable deployment require normal Hugin
  Quit and InstanceGuard. Whispering/PipPal stay disabled. Return path is the
  reviewed base source after normal Quit; no settings migration.

Acceptance: splitter coverage plus public lifecycle tests protect REQ-001/002;
existing controller/native timing and cancellation tests protect REQ-003;
same-worker baseline/candidate measurements on Freya/Tyr check NFR-001. Native
silent playback measures scheduling gaps; final listening checks prosody and
word agreement. Unverified perceptual results must remain explicit.
Both ordinary synthetic fixtures must retain complete valid word alignment in
both voices; a new section-only fallback is not an acceptable latency win.
