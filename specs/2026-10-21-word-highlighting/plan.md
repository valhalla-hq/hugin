# Plan

1. Measure a bounded CPU forced-alignment prototype on existing approved synthetic
   voice references; inspect the exact installed API and timestamp quality.
2. Use an ALIGN action in the existing STT worker under the same central GPU
   slot, after confirmed TTS terminal. Collect one bounded section, align known
   text against its actual audio, then play/drain it before preparing the next.
   No third worker/model owner. Existing cancel escalation retains ownership
   until terminal or observed process-family exit.
3. Add guards before integrating per-section preparation, word-offset metadata,
   real native playback position and job-bound UI word tags. Use existing panel
   styling and controls; avoid independent wall-clock word timers.
4. Validate producer contracts, controller cancellation, native audio/UI fixtures
   and both independent reviews. Save through a private checked PR.
5. After normal Quit deploy and obtain the real voice/word listening acceptance.

No implementation path is assumed successful before the prototype. If the
existing model cannot provide useful timing at acceptable cost, record that
result before selecting a new dependency. Rollback: accepted main 11216cc after
normal Quit; no runtime replacement while the live app uses it.

Measured decision: existing Whisper forced alignment works on both approved
voice references. CPU model-loading peak is 4.81GB, so production reuses the
existing STT/GPU scheduling. Qwen PCM is 24 kHz mono16; the producing STT adapter
resamples to 16 kHz, enforces30s and decoder-token bounds and returns source
character spans with24 kHz sample intervals. Unsupported alignment retains full
speech with an explicit section-only indication. Never truncate audio/text to
fit an alignment window. One section is capped at 60s PCM, independent of the
30s alignment limit; common text sections are reduced to 240 characters to lower
preparation latency without claiming this proves audio/token limits.

Native waveOutGetPosition supplies samples (validated byte/ms alternatives),
reset with each device start. PCMOutput reports real progress during write/drain;
Controller posts job/section-bound word changes only. Tk tags the original text
and follows it without focus activation. Pause/hide/finish preserve their existing
meaning. No independent wall-clock word timer or third-party text rewriting.
