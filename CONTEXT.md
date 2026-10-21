# Hugin Context

Status: audio-based word highlighting is implemented in an exclusive candidate;
real GPU/voice checks, independent integration review and rollout are pending.
Owner: Brian. Private repository valhalla-hq/hugin; runtime Mjolnir.

## Current intent and authorization

Brian requests current-word highlighting in the existing movable reading panel.
He explicitly prioritizes agreement with audio and accepts additional preparation.
Use actual-audio forced alignment with the existing Whisper worker; do not invent
word durations. This supersedes the earlier deferral of exact word highlighting.
Routine checked private integration and normal deployment remain authorized.

## Active work and handoff

- Branch: codex/hugin-word-highlighting-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-word-highlighting-mjolnir.
- Base/main: 11216cc13171064cbfe3716e10977daefec881f0 (PR32).
- Exact handoff: handoffs/2026-10-21-word-highlighting.md.
- Spec/plan/tasks: specs/2026-10-21-word-highlighting/.
- Evidence/limits: docs/word-highlighting-2026-10-21.md.
- Control: 05181f9a99374ff8b298c626f903304f36ac8926.
- Ownership remains active; helpers have their own exclusive worktrees.

## Accepted deployment and preservation

C:/Users/brian/Hugin points to C:/Users/brian/brian-projects/_repos/hugin.
Running source is PR31 late field capture, merged as 4e18f746; PR32 only recorded
Brian's successful click-away/return dictation test and is current deployed main.
Do not replace running source/runtime. Normal tray Quit precedes candidate
validation on the exclusive GPU and deployment; no stored PID is termination
authority. Whispering and PipPal remain disabled and must not auto-return.

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

One prepared section: TTS actual terminal -> existing STT ALIGN actual terminal
-> native playback/drain. Central GPU ownership and cancellation remain serial.
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
