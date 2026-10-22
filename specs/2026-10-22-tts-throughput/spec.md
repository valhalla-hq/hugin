# Further reading-start investigation

Brian asks whether the accepted reading flow can start faster again. Baseline is
main 8f2c605 (the 120-character opening section), not the earlier 240-character
policy. This bounded investigation may adopt a measured safe improvement.

- REQ-1: Compare current codec batches of 8 with 16 and 24 in the installed Qwen
  provider, with unchanged voices, seed, text sections, model and audio alignment.
- REQ-2: Preserve original text coverage, actual-audio word timings, bounded
  cancellation, native playback, one-section lookahead and all input behavior.
- SEC-1: Use synthetic text only, offline existing assets, no microphone,
  clipboard, preferences, raw audio files or personal data. Acquire InstanceGuard
  before GPU use; close owned workers before releasing it.
- AC-1: Compare repeated warm TTS-plus-alignment duration in resident workers;
  report initialization separately, CPU and peak family commit with limitations.
- AC-2: Only adopt a candidate with repeatable benefit, complete alignment on
  both voices, acceptable cancellation and subsequent pipeline gap verification.
  A negative finding is a valid result; do not degrade quality for a small gain.

Larger codec batches may reduce repeated overlapping acoustic decoding but also
change chunk boundaries and cancellation latency. Neither gain nor perceptual
equivalence is assumed. No dependency upgrade, provider fork or production
packaging in this task. Return path is unchanged main after normal app Quit.
