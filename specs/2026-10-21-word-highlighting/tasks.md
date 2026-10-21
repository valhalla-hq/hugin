# Tasks

- [x] Measure and review real CPU alignment feasibility (REQ-001/NFR-001).
- [x] Finalize measured design and add failing production-boundary guards.
- [x] Implement owned preparation and validated original-word intervals.
- [x] Implement native playback progress and word-following panel.
- [x] Validate cancel/pause/hide/new-job/resource and compatibility boundaries.
- [x] Independent review, full checks, private integration and normal restart.
- [ ] Real Freya/Tyr word-highlighting acceptance.

Final integrated checks: 546 passed in 23.637s; 5 native UI checks and 1 silent audio check passed.
Real GPU/Controller measurements and known Freya fallback are recorded in
docs/word-highlighting-2026-10-21.md. Independent review pause-race finding has a
red/green regression guard and producer-epoch fix. Both final delta reviews of
1db6e0a are clear. PR33 merged as fd81c169; the clean stable clone was updated
under InstanceGuard and Hugin started at 17:32:15 local on 2026-10-21.
