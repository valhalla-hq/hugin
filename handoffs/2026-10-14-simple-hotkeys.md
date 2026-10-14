# Hugin: einfache Pilot-Kürzel

Auftrag: Fn-freie, merkbare Testkürzel. Strg+Alt+D für Diktat, Strg+Alt+V
für Vorlesen; beides weiter Toggle, Escape weiter nur bei aktiver Aktion.

- Repository valhalla-hq/hugin, Basis main 60eb70117ca7cc5d4afc33013a7d9bcff75a6a73.
- Executor Mjolnir, Branch codex/hugin-simple-hotkeys-mjolnir,
  Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-simple-hotkeys-mjolnir.
- Preflight-Control e3deecae6673a024aa9015a4387737fbec04c795.
- PR https://github.com/valhalla-hq/hugin/pull/4. Ownership bis zum geprüften
  Remote-Checkpoint aktiv, danach über project_workspace.py freigeben.
- Änderung: input.py, application.py, zwei vorhandene Tests, README und
  aktuelle Pilot-Anleitungen und zwei Spec-Verweise. Modell-/Paketlocks unverändert.
- Prüfung: 268 Vertrags-/Integrationstests ohne Skips, docs und diff --check
  grün. Echte isolierte Windows-Register/Release-Probe für D/V und dynamisches
  Escape sowie vier native Darstellungsprüfungen grün, während der vorherige
  Pilot noch F9/F10 hält. Unabhängiger Review ohne funktionale Befunde;
  zwei veraltete Spec-Verweise aus dem Review ebenfalls korrigiert.
- Geplanter Neustart: Hugin über normale Tray-Beenden-Aktion, bisherigen
  Supervisor-Rückstart bestätigen, Altapps über ihre normalen Beenden-Wege
  wieder pausieren, geprüften Main über denselben lokalen Supervisor starten.
  Keine erzwungenen Altapp-Stops, Autostart- oder Profiländerungen.
- Keine neue Produktabnahme: physische Eingabe, Hör-/Zielmatrix und spätere
  Maus-/Alt+Y-Aktivierung bleiben wie im style-pilot-Handoff offen.

Fortsetzen: AGENTS.md, CONTEXT.md und diesen Handoff lesen; exakte PR-/Main-
Identität und lokalen .runtime/pilot-session-*.json Status frisch prüfen.
Der vorherige style-pilot-Handoff enthält die Runtime-/Rückwegdetails.
