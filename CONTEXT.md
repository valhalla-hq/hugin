# Hugin Context

Status: Brian requests reading sections at sentence ends or suitable clause
punctuation, preserving accurate words and smooth transitions. The pure producer
and regression guards are implemented. Both real voices mark every word in the
normal sentence/clause fixtures; additional scheduling gaps are <=1.73ms. An
initial very-short-opening regression was corrected before deployment. The
existing Freya mixed-abbreviation fallback shrinks from[0,81) to[0,74), with no
previously marked range lost. Whole sentences can cost extra startup time
(about0.91s for the longer opening fixture). PR42 merged as b79073c and was
deployed under InstanceGuard. Hugin restarted at09:17:40 local on22 October;
its own window shows ready. Brian's both-voice hearing feedback is pending.
Owner: Brian. Private repository valhalla-hq/hugin; runtime Mjolnir.

## Current intent and authorization

Implement natural section boundaries against accepted main1c598db, including
codec batch16. Preserve actual-audio alignment, native playback and one-section
lookahead. The frozen comparison baseline is the current120-character policy.
Routine checked private integration and normal deployment remain authorized.

## Active Handoff

- `handoffs/2026-10-22-natural-sections.md`
- Branch: codex/hugin-natural-sections-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-natural-sections-mjolnir.
- Base: 1c598dbf90dd5aa1aebf9f47a358f9d87f83ac8f.
- Spec/plan/tasks: specs/2026-10-22-natural-sections/.
- Evidence/limits: docs/natural-sections-2026-10-22.md.
- PR: https://github.com/valhalla-hq/hugin/pull/42.
- Control: 05181f9a99374ff8b298c626f903304f36ac8926.
- Ownership remains active for the pending hearing feedback.
- Prior accepted codec optimization: handoffs/2026-10-22-tts-throughput.md.

## Accepted deployment and preservation

C:/Users/brian/Hugin points to C:/Users/brian/brian-projects/_repos/hugin.
The previously accepted source is PR31 late field capture, merged as 4e18f746;
PR32 recorded Brian's successful click-away/return dictation test. After Brian's
normal Quit, exclusive GPU/clock probes passed and closed their resources.
PR33 was deployed under InstanceGuard to the clean stable clone; Hugin started
at 17:32:15 local on 2026-10-21. Brian then confirmed that word timing fits both
Freya and Tyr. He requests a visual refinement following PipPal: the current
word should be bold rather than shown on a filled highlight. PR34 changes only
the word tag to white bold text, with matching font size at each panel scale.
It passed independent review and exact-head hosted checks, deployed under
InstanceGuard and started at 17:41:27 local. The own window was observed preparing
reading with Tyr. Brian then confirmed function but rejected the shifting text
layout caused by changing word weight. He selected A after the synthetic native
comparison. PR35 uses the same inherited font for all words and changes only
foreground/background for the active span. After normal Quit, the clean stable
clone updated under InstanceGuard and Hugin restarted at 18:41:03 local on
2026-10-21. Its own window showed Bereit für dein Diktat. No app input was sent.
No stored PID is termination authority. Whispering and PipPal remain disabled and must not auto-return.

Accepted: screenshot plus dictation in Codex, clipboard fallback for Ctrl+V,
Alt+Y and mouse Back for dictation, Ctrl+Alt+V and mouse Forward for reading,
panel buttons, reading-to-dictation preemption, original Whispering cues,
Obsidian UI, movable rounded reading panel, hide/show and pause/resume.
Startup Hugin.lnk points to stable pythonw/launch/root without pilot/show;
old links are backed up under ignored .runtime/desktop-setup-v1. Actual next-login,
production packaging and full device/target matrix remain separate tasks.
Historical mouse/startup and late-field receipts remain in
handoffs/2026-10-21-mouse-startup.md; do not treat that as this feature's handoff.

## Current implementation boundaries

One prepared successor beside the playing section: TTS actual terminal ->
existing STT ALIGN actual terminal -> playback after predecessor drain.
Central GPU ownership and cancellation remain serial.
Text sections <=240 characters; PCM <=60 seconds; alignment <=30 seconds and
448 decoder positions, with explicit unavailable/rejected section-only fallback.
No truncation, new model/dependency or full-document audio cache. Original word
offsets come from complete provider token/character coverage. Display follows
waveOut sample position, freezes on pause and clears on stop/new job/dictation.
UI uses original text tags and native-Tcl offsets without foreground activation.

All text/audio/timings stay in RAM. No personal dictation/clipboard/image data,
credentials, model weights, virtual environments, local traces or generated
media in Git. Only curated source/configuration/locks and approved synthetic
voice references are tracked. Latest measurements and review state belong in
the exact handoff. Do not claim perceptual word accuracy from synthetic IPC tests.
