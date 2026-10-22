# Hugin further reading-start optimization

Brian asks whether current faster reading can improve further, preserving
audio-matched words and smooth transitions. This continues the bounded speed
implementation request; no packaging, model/dependency, UI or input change.

Repo valhalla-hq/hugin, Mjolnir; task hugin-tts-throughput. Exclusive worktree
C:/Users/brian/brian-projects/worktrees/hugin/hugin-tts-throughput-mjolnir,
branch codex/hugin-tts-throughput-mjolnir. Base main
8f2c605d84bcaea79ea120e8f7486e97e0cc9ee7. Control/preflight
05181f9a99374ff8b298c626f903304f36ac8926; no initial open PRs.
Exact spec/plan/tasks: specs/2026-10-22-tts-throughput/. Evidence:
docs/tts-throughput-2026-10-22.md. Prior section-policy history and hearing
boundary: handoffs/2026-10-21-reading-start.md. No hearing acceptance inferred.

Production changes only Qwen codec batch8→16. Installed provider repeatedly
decodes overlapping context. A36-run screen shows9.5–13.5% median warm preparation
gain with complete alignment. Larger24 offers little gain with slower cancellation.
Final pre/post-PCM cancellation probe: all12 pass, candidate<=0.56s. Review found
a late-cancel callback collector race in the screen; request-bound observations
and a held-callback guard fix it. No production transport change.

Full native silent pipeline preserves all54/43 words and scheduling gaps<=0.84ms.
One Freya opening was slower in the first run with partial local-suite overlap.
Isolated three-pair repeat: candidate earlier in all, saves0.232–0.348s,
median3.793→3.463s. Other complete cases save0.119–0.185s. Evidence preserves the
negative first result and measurement limits; do not equate screen time with
acoustic onset. Workers closed and GPU guard released after every measurement.

Brian confirmed normal Hugin Quit. Stable C:/Users/brian/Hugin remains clean
main8f2c605; no deployment yet. Never terminate by remembered PID. Whispering
and PipPal remain off. Synthetic PCM stays in bounded RAM. Raw reports ignored.

Final local suite: 561 checks pass in22.752s; docs check and diff whitespace clean.

Next: two final review lenses, remote checkpoint, unchanged-head
hosted CI and merge. Deploy under fresh InstanceGuard and start normally. Then
receive listening feedback for both voices; silent playback is not hearing
acceptance. Return path base main after normal Quit. Ownership active.
