# Production build and installer

Brian requests the productive Windows build including installer, autostart and
permanent Back/Alt+Y dictation and Forward/Ctrl+Alt+V reading verification.
Private valhalla-hq/hugin, Mjolnir, base5140213e6019f3b9f47025cd2f6ce08ba15cbce7;
control05181f9a99374ff8b298c626f903304f36ac8926. Task hugin-production-build,
branch codex/hugin-production-build-mjolnir, exclusive worktree
C:/Users/brian/brian-projects/worktrees/hugin/hugin-production-build-mjolnir.
Ownership active. Prior completed handoff: handoffs/2026-10-22-review-fixes.md.

Spec/plan/tasks: specs/2026-10-22-production-build/. Full offline per-user payload
with private relative CPython, locked wheels/models/CUDA and accepted voices/cues;
stable native starter, Inno installer, exact owned startup migration/backups.
No public upload, paid certificate, sign-out or OS/security/driver changes.

Portable Python3.12.10/Tk8.6.15 prototype passed with only private prefix and
relative paths. Three-engine runtime must retain Lib/site-packages outside the
Scripts interpreter home so the existing diagnostics owner stays correct.
Four initial package inventory/path guards pass. Inno7.1.0 x64 downloaded from
official linked GitHub release, Authenticode Valid/Pyrsys B.V.; compiler isolated
under ignored .runtime/build-tools/inno. csc is the existing Windows Framework64
compiler. No app installation/source change yet; accepted source Hugin remains
running, Whispering/PipPal disabled. Source assets include roughly12GB runtime;
stable .runtime also contains private test data and wheelhouse: never copy it whole.

Next: implement and verify the allowlisted build, owned setup migration and held
installer mutex. Save meaningful source checkpoint/Draft PR. Build and relocate
payload, run synthetic isolated install/update/uninstall/input checks, independent
review, exact-head CI/integration and final switch after normal Quit. Actual next
login remains explicitly pending; do not claim it from manual background launch.
Preserve all source runtime/preferences and old startup backups. Build outputs,
logs and raw probes stay ignored; only curated evidence in Git.

Starter: Continue Hugin production-build from this exact handoff. Follow the
spec/plan/tasks, preserve the accepted behavior, finish installer and local
verification before routine checked private integration. Do not develop in
the stable clone or overwrite settings. Release only from clean remote proof.
