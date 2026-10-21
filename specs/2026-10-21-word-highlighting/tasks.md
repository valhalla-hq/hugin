# Tasks

- [x] Measure and review real CPU alignment feasibility (REQ-001/NFR-001).
- [x] Finalize measured design and add failing production-boundary guards.
- [x] Implement owned preparation and validated original-word intervals.
- [x] Implement native playback progress and word-following panel.
- [x] Validate cancel/pause/hide/new-job/resource and compatibility boundaries.
- [x] Independent review, full checks, private integration and normal restart.
- [x] Real Freya/Tyr word-highlighting acceptance.
- [x] Apply and verify Brian's requested PipPal-inspired bold-word presentation.
- [x] Select and verify a stable reading style that removes bold-induced movement.
- [ ] Review, integrate and deploy the selected A style after normal Quit.

Final integrated checks: 546 passed in 23.637s; 5 native UI checks and 1 silent audio check passed.
Real GPU/Controller measurements and known Freya fallback are recorded in
docs/word-highlighting-2026-10-21.md. Independent review pause-race finding has a
red/green regression guard and producer-epoch fix. Both final delta reviews of
1db6e0a are clear. PR33 merged as fd81c169; the clean stable clone was updated
under InstanceGuard and Hugin started at 17:32:15 local on 2026-10-21.
Brian subsequently confirmed matching word timing with both voices. The final
presentation request changes only the active word styling; alignment is retained.
PR34 is reviewed, merged as f4bcc437 and deployed. Five native UI checks and
owned visual/font-scale verification passed; normal restart was at 17:41:27 local.
Brian subsequently reported that bold changes shift following text. A synthetic
native comparison reproduces that movement and verifies three alternatives with
unchanged glyph positions. Brian selected A. Its implementation removes active
font overrides; six native word-panel checks pass (1.353s), including a new
glyph-advance guard that first failed on the old bold style. Rollout is pending.
