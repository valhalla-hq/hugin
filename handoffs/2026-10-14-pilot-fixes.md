# Hugin Pilotkorrekturen

- Repository valhalla-hq/hugin; Basis main 8c64029c8068a6fe3c58d177a1ed7b0c353ca773.
- Executor Mjolnir, Branch codex/hugin-pilot-fixes-mjolnir, Worktree
  C:/Users/brian/brian-projects/worktrees/hugin/hugin-pilot-fixes-mjolnir.
- Preflight-Control e3deecae6673a024aa9015a4387737fbec04c795; Ownership aktiv.
- Auftrag/Prüfplan: specs/2026-10-14-hugin-v1/pilot-fixes.md. Automatisches
  Einfügen in Codex reparieren, Audioaussetzer bei Freya UND Tyr beheben,
  ersten Modellstart erklären. Bestehende Modelle/Autostarts/Profile erhalten.
- Root: Controller/Meldungen/Ladeanzeige, UIA-Integration, Abnahme, PR/Merge.
  Windowshelper: eigener hugin-codex-target-Worktree, begrenzte UIA-Target-
  Metadaten und unmittelbarer nativer Commit. Audiohelper: eigener
  hugin-audio-fix-Worktree, PCMOutput-Doppelbufferung. Keine parallele GPU.
- Erster Root-Guard: drei falsche Zielwechselmeldungen und fehlende Ladeanzeige
  zuerst rot, nach engem Mapping-/Statusfix 24 Controllerverträge grün.
- Nativer Codex-Prozess heißt ChatGPT.exe im OpenAI.Codex-WindowsApps-Paket;
  nicht aus dem Produktnamen Codex.exe ableiten. Keine privaten UI-Inhalte
  persistieren. Synthetische Eingabeprobe darf keine Nachricht absenden.
- Laufender vorheriger Pilot: Main.runtime/pilot-session-eb6211bb-4b98-459a-980b-7e3686849a9f.json.
  Zustand/Handles frisch prüfen. Einmaliger Supervisor im freigegebenen
  hugin-simple-hotkeys-mjolnir/.runtime; während dessen Lauf nicht entfernen.
- Geprüfte private Integration und geordneter Neustart folgen nach Source/
  Native-Abnahme und unabhängigen Reviews. Vollständige Produktabnahme offen.

Fortsetzen: AGENTS.md, CONTEXT.md, diesen Handoff und pilot-fixes.md lesen.
Exakten Branch-/PR-/Runtimezustand prüfen, nur eigene gehaltene Ressourcen
bereinigen. Kein Force-Stop alter Apps oder Modellparallelbetrieb.
