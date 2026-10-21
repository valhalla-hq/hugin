# Audio-based reading words

Brian requests word highlighting in the existing reading panel and explicitly
accepts additional preparation for closer agreement with the spoken audio.
The selected source text remains unchanged. Existing panel placement, hide/show,
pause/resume, voices, shortcut/mouse bindings and dictation priority remain.

The existing Whisper worker aligns the known original text against Qwen's
generated PCM. Its producer binds complete token/character coverage to original
word offsets; repeated words are not located by text search. The controller uses
the native waveOut sample position, including pause/resume, to select the active
word. Only changed word spans reach the panel; the main controls are not rebuilt
for each word. Windows Tcl UTF-16 columns are handled separately from Python
code-point offsets.

Preparation is bounded to one successor beside the playing section. TTS must confirm its native
terminal before ALIGN can own the central GPU slot; ALIGN must confirm terminal
before that section can play, after its predecessor drains. Text sections are at most 240 characters. PCM has its own
60-second transport bound, independent of Whisper's 30-second alignment window
and 448-position decoder limit. No text/audio is truncated to fit alignment.
Expected limits or rejected paths preserve complete section speech with
"Wortmarkierung nicht verfügbar". Worker/protocol failures keep the existing
owned error/cancel path. No word-rate estimate is substituted.

Audio/text/timings stay in RAM; diagnostics do not contain them. There is no new
model/package/download or third GPU worker. Stop/new job/dictation discard old
marks. Native cancellation retains the worker slot until actual terminal or
observed owned-family exit, even if recording can already start.

## Evidence and limits

The installed API probe on approved Freya/Tyr references established forced
alignment availability. CPU model loading took 2.392s; Tyr 6.49s audio aligned in
0.729s, Freya 8.72s in0.994s, and warm Tyr in0.721s. Family CPU 16.859s;
peak committed memory 4,808,503,296 bytes. The4-GiB trial cap was insufficient;
the 5-GiB trial completed and closed its owned process. OS file cache was not
controlled. This supports reuse of the existing STT worker instead of another
resident CPU model; it does not establish perceptual accuracy or GPU cost.

Native fixture evidence covers sample positions, pause/resume/reset and hidden
Tk tags/following without changing foreground focus. Pure controller guards
cover terminal barriers, cancelled/stale jobs, unsupported alignment, audio
bounds and actual sample-driven word/gap updates. Full integrated checks and
real GPU measurements are recorded in the active handoff as they complete.

Forced alignment is a model-derived mapping, not a guarantee that generated
speech matches every source word. Numbers, abbreviations, repetitions and
pronunciation still need real Freya/Tyr listening. Token probabilities are not
claimed as calibrated timestamp confidence. Physical working-set peak and broad timing-accuracy metrics remain unmeasured.
Agent-token cost was not measured. The candidate probe measures preparation and
section transitions separately from perceptual word accuracy.

Rollback is accepted main 11216cc after normal Quit. Do not replace live runtime
files, alter the clipboard, re-enable Whispering/PipPal startup or use stored PIDs
as termination authority.

The first real GPU trial exposed approximately three seconds of generation delay
per section, despite fast warm alignment. A bounded lookahead now prepares the
next section during native playback, retaining one current and one successor at
most. There is still only one GPU operation at a time. A review also reproduced
a pause race where a queued word was discarded but remained cached as posted;
pause/resume now invalidate progress coalescing, with a red/green Controller guard.
Outer whitespace consumed the initial word interval in one real forced path.
The alignment adapter excludes only non-spoken outer whitespace and explicitly
maps every returned span back to the unchanged original source. It still rejects
zero-duration lexical words rather than stretching their times.

## Real candidate measurements

Both existing workers ran on CUDA and closed successfully. On the corrected
adapter, the repeated normal 18-word sentence aligned for both Freya and Tyr;
generation took 2.694–3.381s for 6.4–6.8s audio. Alignment took 0.244s on the first
call and 0.038–0.060s for warm cases. Worker/model startup in that trial was
19.109s TTS and 6.083s STT (OS cache uncontrolled). Family CPU: 38.375s TTS and
15.438s STT; individual peak committed memory: 8,451,969,024 and 3,246,796,800
bytes. These individual peaks are not a simultaneous working-set/GPU peak.

A numbers/abbreviation/name fixture aligned all 17 words for Tyr. Freya's same
fixture was correctly rejected because the derived Weber interval had zero
duration; complete audio and section-only display remained available. This is
an explicit model limitation, not a claim that the requested word was absent
from the speech. No timing was invented to force success.

The real Controller/worker/native-clock probe used generated audio in RAM and
sent equal-length zero PCM to the native output, avoiding audible speech while
checking actual playback progress. Its two-section Freya passage marked all
54 original words; observed drain-to-next-start gap 0.55ms. Initial preparation
including worker/model load was 26.965s; total job 50.181s. A warm numbers case
started after 4.497s and completed with the declared no-word fallback. Total
probe elapsed 65.020s; Controller CPU 1.375s; worker-family CPU 29.641s TTS and
13.250s STT; individual peak committed memory 8,453,869,568/3,247,951,872 bytes.
Both workers and native/executor resources closed. This establishes real
pipeline/clock behavior, not perceptual voice/word accuracy or a p95 guarantee.

## Hearing acceptance and visual refinement

After PR33 deployment on 2026-10-21, Brian confirmed that word timing fits both
Freya and Tyr. He then requested PipPal-inspired bold typography instead of the
filled current-word highlight. PipPal's local webui/css/theme.css uses white,
bold current-word text; webui/js/overlay.js applies the current-word class.
Hugin's refinement uses its own Segoe UI bold tag, without a background fill,
and scales it with the normal text. Original spans, audio alignment and native
playback timing stay unchanged. This is a styling refinement of the accepted
feature; it does not broaden the measured alignment coverage.

Brian subsequently found that the normal-to-bold change moved subsequent text.
Equal font size was insufficient: the native word aktuelle measured 54px normal
and 62px bold. The synthetic mapped Tk comparison reproduced movement of 84
character boxes. Three alternatives retained every box over 19 word changes.
Brian selected A: normal font with a soft blue fill and white current word.
The final style removes both active-font overrides; the Text widget owns the
single scalable font. Foreground/background change without changing glyph
advances. A new native regression guard failed on the bold implementation and
passes with A at normal and small scales. All six native word-panel checks pass.
