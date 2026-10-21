# Tasks

- [x] T1 Reproduce exact format failure without payload access/mutation and obtain
  diagnosis proving target capture success.
- [x] T2 Implement persistent publication and honest fallback with regression
  guards for missing targets, unsupported originals, cancellation and newer copies.
- [ ] T3 Native producer/clipboard proof, full checks and independent review.
- [ ] T4 Checked integration, normal restart and physical Codex/mouse acceptance.

Verified: 500 contracts/integration passed in 20.707 s; 29 mocked Windows
ABI/producer checks and docs coverage (19 requirements, 17 acceptance criteria)
passed. Alt+Y normal/pilot tests first failed under the old binding, then passed.
Three actual Windows registration/ownership tests passed in 0.327 s after normal
Quit. Synthetic native RichEdit publication/paste/owner-close persistence and
exact original supported-text-format restoration passed in 0.045 s.

The first plain hidden Edit fixture did not consume WM_PASTE; publication and
restoration succeeded. Reused the established RichEdit fixture with explicit
selection. A later file clipboard was rejected without mutation; Brian then
provided disposable text. Supported Chromium text formats are accepted by the
fixture; arbitrary OLE/files/images are not read. Physical Codex acceptance
follows checked integration/restart. Production packaging and next login remain
separate work.
