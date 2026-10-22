# Plan

Use Inno Setup with a stable per-user AppId and immutable per-build roots under
LocalAppData/Programs/Hugin/releases/<version>-<commit>. Stable shortcuts select
the current release. New builds never merge with old executable files; old roots
retain preferences/backups as return paths. Native preflight holds root/ancestor
directory identities and permits only the authenticated same-build repair.
Bundle full private CPython trees with isolated relative search paths; keep
existing .runtime/{profile}/Scripts/python.exe worker paths. Rebuild package
trees from SHA256-locked local wheels, not copied live venvs. Models/CUDA/cues
use existing validated owners/locks. A small .NET Framework launcher uses the
Windows desktop runtime, dispatches the private interpreter and reports failure.

Keep setup ownership in one Python setup adapter, reusing existing DesktopSetup
transaction/backups and the one activation profile. Explicitly prove old link
ownership before migration. Updates never copy user state from the bundle.
An installer guard holds the existing instance mutex across mutation; helper
observes its parent handle and exits without killing anything. Inno does not
force-close applications. Installer UI explains its local/offline payload.

Guard-first slices: portable runtime and artifact inventory; setup migration and
idempotence; native launcher/installer; isolated install/update/uninstall and
input persistence; independent review; exact-head checked integration; final
installation switch after normal Quit; receipts and verified ownership release.

Pressure review: biggest traps are non-relocatable venv executables, payloads
accidentally including recordings, updates resetting settings, an old shortcut
overriding the new install, and app start racing a setup check. Relative private
interpreters, tracked input allowlists, excluded state, exact ownership backups
and a held mutex address those boundaries. Operator, privacy, maintenance and
skeptical passes support this bounded local implementation. Full login evidence
and public signing/distribution stay separate; no paid tool or hidden updater.

Return path: normally quit installed Hugin, restore only the exact owned prior
startup link from retained backup, then launch the preserved source installation.
No backup/data deletion is part of the final migration. Keep build outputs ignored.

Installer success requires configuration and guard release; failed post-install
configuration returns exit11, shows failure and never offers app launch. Uninstall
configuration runs in InitializeUninstall before Inno deletes payload files.
All payload, icon/native and installer recipe inputs use the pinned Git commit.
