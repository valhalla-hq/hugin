# Hugin word-highlighting handoff

## Scope and state

Brian explicitly requests the postponed word highlighting and chooses actual
audio alignment over estimated immediate timing. Existing reading panel, voices,
input/startup, dictation focus/clipboard and cancellation must be preserved.
Source document remains unchanged. No additional confirmation is needed for
this bounded feature; normal Quit is needed for exclusive real-GPU verification.

Parent task hugin-word-highlighting / runtime mjolnir:
C:/Users/brian/brian-projects/worktrees/hugin/hugin-word-highlighting-mjolnir,
branch codex/hugin-word-highlighting-mjolnir. Base/main 11216cc13171064cbfe3716e10977daefec881f0.
Control 05181f9a99374ff8b298c626f903304f36ac8926. Active ownership; merged PR33 https://github.com/valhalla-hq/hugin/pull/33.
Helper tasks hugin-word-alignment-worker and hugin-word-playback-ui are clean,
active and exclusively owned; their changes have been cherry-picked into parent
as 040b144,442fa2c,4f06100. No helper publication/deployment authority.

## Implementation and evidence

See specs/2026-10-21-word-highlighting/ and docs/word-highlighting-2026-10-21.md.
Existing STT worker now has bounded ALIGN input and typed original-word timings.
It resamples 24 k PCM to 16 k, checks duration/decoder limits and binds full token
coverage; no string search or interval interpolation. Central lifecycle buffers
a section, waits actual TTS terminal, aligns, waits actual ALIGN terminal and
plays/drains. One successor prepares during playback, with separate ownership. Native waveOut progress drives tag changes; pause/job identity and
Unicode/Tcl offset guards are explicit. Expected unsupported/rejected alignment
plays complete audio with an unavailable indication. Hard faults retain existing
error/cancel/ownership behavior. No new runtime/model dependency.

Real offline CPU feasibility: 2.392s model load; Tyr 6.486s ->0.729s alignment,
Freya 8.720s ->0.994s; warm Tyr 0.721s. Family CPU 16.859s and peak committed
4,808,503,296 bytes. First 4-GiB cap rejected loading; second 5-GiB cap succeeded
and owned process closed. This measured API behavior, not perceptual accuracy.
Production reuses existing STT/GPU slot instead of a third resident model.

Parent focused 130 checks passed 0.441s. Hidden native UI 5 checks passed 1.101s;
native silent PCM position/pause/resume/reset passed 0.418s. Full integrated run
initially found two legacy live-audio-probe fixture failures: the probe assumed
streaming TTS playback and one worker. It now handles prepared playback, keeps
TTS trace ownership separate from STT, and checks playback cancellation after a
bounded packet independently of the already successful synthesis terminal.
Full rerun: 544 passed in 23.704s. Independent reviews of 14d2c58 found one
pause/progress-dedup race. Both reviewers reproduced it through the Controller;
pause/resume now invalidate the producer epoch, and the red/green callback guard
confirms the same current word is republished on resume. Final integrated suite
after these corrections: 546 passed in 23.637s.

Real GPU candidate probe is prepared at ignored .runtime/probe_word_workers.py.
It claims the same InstanceGuard, uses current candidate worker source with the
stable verified runtime/assets, only synthetic text and RAM PCM, no audible
output/clipboard/input. It records timing/counts/owned-family metrics only.
Brian subsequently confirmed normal Quit; both real GPU probes ran exclusively
under InstanceGuard and closed their workers. Results are in
docs/word-highlighting-2026-10-21.md. A measured approximately 3s per-section
generation gap changed the plan to one prepared successor beside the playing
section, with no overlapping GPU operations or document-wide cache. Public
guards protect the lookahead bound and separate display/preparation ownership.
Outer whitespace is omitted only from alignment, with original offsets retained.
The repeated standard sentence aligns with both voices; Tyr's numbers fixture
aligns 17 words; Freya's produces a zero-duration lexical word and honest fallback.
A real Controller/native silent-clock run marks 54 words across 2 sections with
0.55ms observed drain-to-next-start gap. Initial cold preparation 26.965s includes
both worker/model loads; this measurement itself did not establish heard timing.

## Integration, running state and next work

Both independent final delta reviews of 1db6e0a are clear; pause/progress race
closed. All three exact-head hosted checks succeeded. Immediately before merge,
PR identity, 30-file scope, unchanged head and checks were read back. PR33 merged
at 2026-10-21T15:31:51Z as fd81c169a0440e705301508039a51ad03a860071.
The clean stable main clone fast-forwarded under a freshly acquired InstanceGuard;
source tree is 6974b5699053b8db06e5981ba26ee99448f7e1a6. Hugin launched normally
with stable pythonw/launch/root and --show at 17:32:15 local. Its own visible
window was checked and showed Qwen loading for reading. No UI input was sent.
This observation confirms deployment/start only. Brian subsequently confirmed
that word marking and timing fit both Freya and Tyr in his hearing test.

Never terminate via remembered PID. Whispering/PipPal stay disabled. Stable
root is C:/Users/brian/Hugin junction to C:/Users/brian/brian-projects/_repos/hugin.
No setting/runtime/startup change. Parent/helper ownership remains active for
this savepoint; no cleanup or release has been claimed.

Next: finish Brian's visual follow-up, which replaces the filled highlight with
bold white current-word text like PipPal. The source read is local PipPal
webui/css/theme.css (current-word rule) and webui/js/overlay.js (current class).
Candidate touches only reading_ui.py's tag/font styling; accepted audio/word
selection remains unchanged. Five existing hidden native word-panel checks pass
after the styling edit (1.138s). An owned synthetic panel was visually checked:
the active word is white and bold, without a filled highlight. Native font
readback at normal and small scales confirms matching normal/bold font sizes.
The preview uses a standard discoverable wrapper only for inspection; the
production panel wrapper and focus behavior are unchanged. Finish independent
review, checked PR34 integration and normal restart. Source rollback for this styling is
PR33 fd81c169; whole-feature rollback is 11216cc after normal Quit.
Packaging and next-login proof remain separate.

Starter: Continue Hugin word highlighting from this exact handoff. PR33 is
merged, deployed and hearing-accepted. Complete the requested bold-word styling
from this active parent worktree and preserve the accepted
input/clipboard/startup behavior. Do not repeat completed GPU/native probes
without new evidence or claim perceptual acceptance from those probes.
