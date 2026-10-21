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

Preparation is bounded to one section at a time. TTS must confirm its native
terminal before ALIGN can own the central GPU slot; ALIGN must confirm terminal
before playback begins. Text sections are at most 240 characters. PCM has its own
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
claimed as calibrated timestamp confidence. Long-document preparation gaps,
physical working-set peak and broad timing-accuracy metrics remain unmeasured
until the candidate probe. Agent-token cost was not measured.

Rollback is accepted main 11216cc after normal Quit. Do not replace live runtime
files, alter the clipboard, re-enable Whispering/PipPal startup or use stored PIDs
as termination authority.
