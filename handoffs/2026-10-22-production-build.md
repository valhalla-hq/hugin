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

PR47: https://github.com/valhalla-hq/hugin/pull/47 (Draft). Initial package/path
guards and spec saved as4c772fe. Native .NET starter and Inno syntax compilation
pass; guard returns busy while accepted Hugin runs, proving the shared mutex.
Setup slice has12 synthetic migration/reinstall/rollback/unknown-owner guards,
plus7 existing DesktopSetup cases. Four independently found edge cases were
reproduced red/green: unowned Legacy links, refreshing replacement authority,
preference reset after completed migration, recovery owner validation before
link recreation. Pending voice migration is plan-bound and completion ends its
active restoration role. Both reviewer lenses clear that slice. Initial full
suite599 passes in26.636s; the later rollback guard is additional.

Builder, private installation probe and launcher/installer are implemented for
the first real build; version1.0.0. No final artifact or real installer run yet.
Only src production change so far is the version; input/audio owners stay intact.
Next: checkpoint current source, build and relocate
payload, run synthetic isolated install/update/uninstall/input checks, independent
review, exact-head CI/integration and final switch after normal Quit. Actual next
login remains explicitly pending; do not claim it from manual background launch.
Preserve all source runtime/preferences and old startup backups. Build outputs,
logs and raw probes stay ignored; only curated evidence in Git.

Starter: Continue Hugin production-build from this exact handoff. Follow the
spec/plan/tasks, preserve the accepted behavior, finish installer and local
verification before routine checked private integration. Do not develop in
the stable clone or overwrite settings. Release only from clean remote proof.

Update before next build: first experimental stage failed before installer
compilation because isolated Python did not include its tools directory. Fixed
both entrypoint search paths; all three staged private profiles now import and
match 7/21/94 locked distributions. No installer installed. Full suite602 passes
in25.357s. Native target ownership3 cases pass, including redirected ancestor,
unknown/changed payload refusal and held root/ancestor rename refusal. A genuine
Inno negative post-install fixture returns11 rather than false success. Separate
review found old-payload mixture, path-string authority, false success, fragmented
stdout, partial owner retention and mutable late recipe reads; candidate fixes
use immutable per-build roots, authenticated manifest/root native lease, explicit
success facts, bounded pipe reads and pinned Git sources. Repeated native/full
review and actual offline artifact/install/voices/persistence remain pending.

Follow-up review corrections: never-published desktop setup can uninstall its
native-owned payload without touching unknown Startup links (new red/green guard,
13setup cases pass). Native guard now precreates/holds every manifest parent,
including initially absent nested paths; native3cases pass. Portable CPython
sys.prefix=Scripts exposed a real UIA owner mismatch: selection_probe now maps
only its own Scripts executable to the existing .runtime/controller package
owner. Builder provisions static COM namespace and import probe generates UIA
interfaces in memory. Native field/clipboard workflow remains to test. Inventory
now examines every entry's lstat/reparse facts once rather than resolving all
ancestors for every file; hashing/full coverage remain mandatory. Attempt2 uses
old checkpoint368a709 and is experimental; rebuild final candidate after review.
Brian confirmed normal Quit; Hugin is now stopped. No startup migration yet.

Real packaged probe: hidden native UIA2cases pass using actual package imports.
First contended cold voice probe failed generically during simultaneous full
build/hash IO; direct TTS initialization passed, then second real candidate read
passed Freya34/34 and Tyr40/40 words, section gaps0.57/0.84/1.23ms, workers closed.
That probe exposed Librosa/Numba .nbc/.nbi runtime caches. Native repeat-install
now retains only those cache types under TTS site-packages/__pycache__, still
rejecting foreign executables. Installer inputs now come from explicit manifest
records, so post-inventory probe caches cannot enter via a wildcard. New native
cache/refusal guard passes. SHA256 verification now uses at most8 workers and
64pending files, with complete coverage retained; prior sequential artifact
verification cost350s for about11.6GB/40332files. A fresh final rebuild and quiet
installed cold-voice check are required; do not ship either experimental build.
CI fixture short-path aliases corrected only in tests; e0941b6 hosted checks pass.
