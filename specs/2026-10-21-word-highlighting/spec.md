# Audio-based word highlighting

Brian requests the postponed word highlighting in the existing movable reading
panel. He explicitly prioritizes agreement with the audio and accepts additional
preparation over immediate approximate highlighting. This supersedes the former
reading-panel exclusion of alignment work. The source document is not modified.

- REQ-001: Mark the current original-text word using alignment against generated
  audio, never a characters-per-second or evenly distributed word estimate.
- REQ-002: Drive the displayed position from actual native playback progress.
  Pause freezes it; resume continues; hide/show restores the current word.
  Stop, new job, voice change and dictation clear stale text/marks and retain
  existing priority/cancellation. Follow the active word into view.
- REQ-004: Preserve the position and width of all glyphs while the current word
  changes. Brian selected variant A after finding active bold caused text to
  shift: normal inherited font, white current word and a soft blue background.
  Do not change font weight/size at word transitions. Preserve accepted timing,
  original offsets, scroll-follow, pause/resume and hide/show behavior.
- REQ-003: Preserve Freya/Tyr speech and the original selected text. On unavailable
  or rejected alignment retain useful section display and speech, explicitly
  showing that word marking is unavailable rather than inventing timestamps.
  Expected duration/token/text limits are section-only outcomes. A broken worker,
  malformed protocol or failed cleanup retains the existing error/cancel path.
- NFR-001: Local processing, one GPU owner, bounded per-section PCM and metadata,
  no full-document audio cache. Alignment uses the existing owned STT worker
  after the TTS operation releases the single GPU slot, with bounded shutdown.
  Measure cold/warm preparation and memory before
  choosing the production path; new heavyweight dependencies are not assumed.
- SEC-001: Text/audio/alignment stay in RAM; no content in diagnostics or logs.
- OPS-001: Preserve the running accepted app until reviewed integration and normal
  restart. Return path is main 11216cc. Input, clipboard and startup remain intact.

Acceptance: known-text synthetic voice fixtures produce ordered word intervals
bound to exact source offsets; pauses/gaps and Unicode punctuation do not invent
words. Production-boundary tests cover invalid/missing intervals, cancellation,
stale jobs, bounded buffering and preparation failures. Native owned-window and
silent-audio fixtures verify position, highlight/follow, pause/resume and focus.
Real Freya/Tyr listening and perceived alignment remain distinct acceptance.

Known: installed faster-qwen3-tts returns PCM and generation/chunk telemetry, no
word timestamps. Existing PipPal estimates word duration. Candidate to measure:
the already locked Whisper model's forced alignment on CPU in its own environment,
using the known text rather than re-transcribing or adding another GPU model.
The CPU API probe passed within a 5-GiB job cap after the 4-GiB cap rejected model
loading: 2.392s load; Tyr 6.49s audio / 0.729s alignment, Freya 8.72s / 0.994s,
warm Tyr 0.721s; process-family peak committed memory 4,808,503,296 bytes.
This establishes the installed API on approved synthetic references, not timing
accuracy or GPU performance. Production reuses the STT worker and GPU slot;
there is no additional model or resident CPU owner. Token probabilities are not
treated as calibrated timing confidence. Brian confirmed perceived timing with
both voices after PR33 deployment; this does not prove all texts or model paths.
