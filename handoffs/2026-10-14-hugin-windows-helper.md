# Hugin Windows Helper Handoff

## Objective

Bounded T003/T004 Windows-Grenzen liefern, ohne produktive Aktivierung. Der
Accountable Executor besitzt Integration, Audio/UI/Core/Worker-Verbindungen
und die native Abnahme. Whispering und PipPal bleiben unverändert am Laufen.

## Git State

- Repository: private `valhalla-hq/hugin`.
- Branch: `codex/hugin-windows-mjolnir`.
- Implementation source commit: `7d10c31`.
- Base: `9328f255980a5b896c3c7a356052a2b81bd25f20`.
- Worktree: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-windows-mjolnir`.
- PR: kein Helper-PR; Integration über bestehenden Haupt-PR1 durch Parent.
- Ownership: active auf Mjolnir; keine Freigabe, kein Merge.
- Authorization: bounded Helper-Auftrag des Accountable Executor; eigene private
  Checkpoint-Branch pushen, keine Produktaktivierung/Altstack-Migration.

## Changed Files

- `src/hugin/windows/{__init__,input,clipboard,instance,process}.py`: dedizierter
  Eingabeowner, Pilotmodus ohne Maushook, begrenzte Clipboard-/Zieltransaktionen,
  user/session mutex und suspended-create/assign/resume Worker Job Object.
- `tests/contracts/test_windows_*.py`: fake OS-Grenzen für Fehler/Abbruch,
  Clipboard-Konflikte und eigene Ressourcenfamilien.
- `tests/windows/test_windows_abi.py`: x64 ABI und native Producer mit Mocks;
  keine echten Windows-Seiteneffekte.
- `docs/windows-api.md`: genaue API, Integration und ausdrücklich offene
  Plattform-/Pilotgrenzen.
- `CONTEXT.md`, dieser Handoff: Helper-spezifischer Checkpoint, getrennt vom
  Hauptbranch-Kontext. Parent soll den Implementierungscommit übernehmen und
  den eigenen Kontext/Haupthandoff selbst fortschreiben.

## Verification

- Python 3.12.10 über `C:/Users/brian/AppData/Local/Python/bin/python3.12.exe`.
- `tools/dev.py check --group contracts`: 33 grün, davon 29 neue Windows-Guards.
- `python -m unittest discover -s tests/windows`: 11 grüne ABI-/Producer-Mocks.
- `tools/dev.py check --docs`: 19 Requirements, 17 AC, keine Probleme.
- `python -m compileall -q src/hugin/windows ...`: grün.
- `git diff --check`, gezielte Daten-/Secret-Musterprüfung: keine Befunde.
- Guard-first: Tests zuerst wegen fehlender Windows-Module rot, dann grün.
- Review gegen Spec und Besitz-/Fehlergrenzen sequentiell lokal durchgeführt;
  unabhängige Parent-Prüfung und native Abnahme bleiben offen.

## Source And Data Boundary

PipPal MIT-Maus-/Clipboard-Code wurde nur lesend als Verhaltensreferenz
betrachtet; keine vollständige Altapp übernommen. Keine Sprachinhalte,
Aufnahmen, Rohlogs, Secrets, Modellgewichte oder Runtime-Verzeichnisse in Git.
Win32-Verträge in docs/windows-api.md verweisen auf Microsoft-Primärquellen.

## Running State

Keine echten Hugin-Hooks/Hotkeys/Clipboard-Transaktionen/Worker/Mikrofone/Modelle
gestartet. Altstack weder gestoppt noch konfiguriert. Kein Hintergrunddienst
dieses Helpers gestartet.

## Open Blockers

- Capture-/Delivery-Klassen bleiben ohne expliziten Zielpilot gesperrt.
- Direktes Standard-Edit-Lesen ist der nächste kleine Schritt ohne neue Runtime;
  UIA TextPattern für Browser erfordert einen eigenen geprüften COM-Adapter.
- Same-target Benutzer-Copy-Attribution, Foreign Delayed Rendering, asynchrones
  Paste/Restore, physische Tasten und Zielmatrix sind nicht durch Mocks bewiesen.
- Echte Job-/Redirector-/Sentinel-Prüfung gehört zum Parent/Worker-Harness.
- Keine Gesamt-AC/T003/T004-Abnahme oder Leistungsbehauptung; Tokenkosten,
  CPU-Zeit und native Prozessfamilien-RAM-Spitze hier ungemessen.

## Pick Up Here

1. Parent übernimmt `7d10c31` für API-Integration, ohne Helper-Kontext zu mergen.
2. Standard-Edit-Auswahl über bounded EM_GETSEL/WM_GETTEXT ergänzen, ohne
   Zwischenablage-Mutation; Browser-UIA konkret planen.
3. Native Abnahme nur explizit und isoliert; keine produktiven Altbindungen
   übernehmen. Ownership dieses Helpers bleibt bis Parent-Steuerung aktiv.

## Starter Prompt

Continue the bounded Windows helper in
`C:/Users/brian/brian-projects/worktrees/hugin/hugin-windows-mjolnir` on
`codex/hugin-windows-mjolnir`. Read AGENTS.md, CONTEXT.md, this exact handoff and
docs/windows-api.md. Parent owns integration. Preserve its core/worker API
coordination and leave the old stack running. Add only the agreed direct
Standard-Edit-selection slice inside the Windows write scope, with fake native
guards first. Do not enable real hooks, inject input, mutate the real clipboard
or kill processes during helper tests. Keep ownership active; checkpoint and
push only reviewed source/tests/docs plus this helper context.
