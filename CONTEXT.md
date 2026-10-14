# Hugin Context

Status: implementation
Owner: Brian
Type: application
Data boundary: Privater Quellcode, kuratierte Konfiguration, Paket-/Modelllocks und bestaetigte kleine synthetische Stimmreferenzen. Keine persoenlichen Diktate, Dokumente, Audioaufnahmen, Credentials, Rohlogs, Modellgewichte oder virtuellen Umgebungen in Git.
Source truth: `valhalla-hq/hugin`

## Goal

Brian hat am 14.10.2026 Spec und Plan unter C:/Users/brian/Hugin/specs/2026-10-14-hugin-v1 erstellt und die schrittweise Umsetzung beauftragt. Kleine native Oberflaeche, XBUTTON2 und Alt+Y fuer Diktat-Toggle, XBUTTON1 fuer Vorlesen-Toggle, Diktat stoppt Vorlesen, beide unveraenderten Stimmen Freya/deutsch-3 und Tyr/deutsch-a. Escape-Abbruch, ein letztes RAM-Diktat mit Kopieren/Loeschen, technische Diagnose ohne Inhalte. Whispering und PipPal laufen bis zur geprueften Umstellung weiter. Lokaler Einstieg C:/Users/brian/Hugin; vorhandene Planungsdateien erhalten und im ersten exklusiven Task uebernehmen.

## Current State

- Private Initialisierung und Katalogregistrierung abgeschlossen, main e555d7d76045dddde35cdeb2e63ce17f048df559.
- Aktiver Task codex/hugin-v1-mjolnir; Planungsunterlagen, Referenzstimmen, Locks und erste Controller-/Prüfgrundlage übernommen.
- Erste Konfigurations-/Asset-Guards wurden zuerst rot, dann grün geprüft. Controller-Pakete isoliert installiert; Sounddevice sieht Standardgeräte, Mikrofon noch nicht geöffnet.
- Whispering/PipPal und produktive Tasten/Autostarts sind unverändert. Keine Hugin-Gesamtabnahme behauptet.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Next Step

- T001 abschließen und die vertikalen Tasks der Spec abarbeiten; Prüfstatus je AC führen. Produktive Eingaben erst nach vorbereitetem, geprüftem Wechsel übernehmen.

## Windows Helper Checkpoint

- Bounded Helper auf Mjolnir: `codex/hugin-windows-mjolnir`, exklusiver Worktree `C:/Users/brian/brian-projects/worktrees/hugin/hugin-windows-mjolnir`; Ownership bleibt aktiv. Integration bleibt beim Accountable Executor auf `codex/hugin-v1-mjolnir`.
- Implementierungscommit `7d10c31`: direkte native Eingaben/Pilotmodus, fail-closed Clipboard-/Zieltransaktionen, benutzergebundener Instanzmutex und Job-Object-Workerfamilien. API und Plattformgrenzen: `docs/windows-api.md`.
- Folgecommit `7dad3ad`: Standard-Edit-Auswahl wird direkt mit bounded EM_GETSEL/WM_GETTEXT gelesen, ohne Clipboard-Mutation, mit UTF-16-Auswahlgrenzen sowie Abbruch-/Zielprüfungen. Read-only und editable sind getrennt; Passwortfelder werden nicht gelesen.
- Stand vor UIA-Folgeauftrag: 36 contracts (32 neue Windows-Guards und 4 Konfigurationschecks), 13 Windows-ABI-/Producer-Mocks, Docs-Check und Compile. Keine produktiven Eingaben, Clipboard-Mutationen, Mikrofone oder Modelle aktiviert.
- Clipboard-Auswahl- und Paste-Fallback bleiben pro Zielklasse gesperrt, bis deren Pilotnachweis vorliegt. Browser/UIA, native Standard-Edit-Prüfung und die echte Zielmatrix bleiben offen; Integration der beiden Sourcecommits durch Parent.

## UIA Helper Checkpoint

- UIA-Sourcecommit `c97cabe`: comtypes TextPattern-Auswahl in einer eigenen held-job One-shot-Probe, 2 s Initialdeadline, 256 MiB Job-Commitlimit, begrenztes privates UTF-8-Framing. Keine Dokumentvolltext-Fallbacks, kein Fokussetzen oder Clipboard-Schreiben.
- Vor jedem GetText werden aktuelle Fokus-/Fensteridentität und Password-Status erneut geprüft; auch das umschließende Element des gewählten Bereichs muss explizit nicht geschützt sein. Auswahl-/Endpunkt-/Text-Nachprüfung verwirft veränderte Ergebnisse.
- comtypes 1.4.17 ist durch Parent installiert; Version im gepinnten Controller gelesen. Gen-Namespace ausschließlich unter .runtime/controller, Interfaces in Memory (gen_dir=None), fremde/read-only Runtime failclosed vor Client-Cache-Initialisierung.
- Geprüft: 61 contracts, 16 ABI-/Producer-Mocks plus eine echte native RichEdit-Fixture, Docs und Compile. Native Fixture liest nur synthetische Auswahl aus eigenem unsichtbaren HWND, ohne fremde Auswahl/Fokusänderung/Clipboard-Mutation; tatsächlicher Job-/Pipe-/Normalexit geprüft. Browser/Codex und produktive GetFocusedElement-Bindung bleiben unbewiesen.
- Parent übernimmt Sourcecommit `c97cabe` gezielt; dessen additive Prozess-Metriken in process.py erhalten, Input/Core/ApplicationRoot nicht überschreiben. UIA close/retry behält Besitzer bei Fehlern. Ownership bleibt aktiv.

## Tray Helper Checkpoint

- Sourcecommit `8e1e37982f80ea3572212b549da5b80a948217e0`: bounded `TrayOwner` für den exakt gepinnten pystray-0.19.5-Win32-Producer. Root übernimmt UI-/Application-Integration; hier kein Root-/Input-/Core-Diff.
- Eigener gehaltener NativeRunner und eigener Visibility-Thread, Stop-Retry derselben Icon-Identität unabhängig von `_running`, bestätigtes Threadende und explizites HICON-Release. Fehler tragen `owner=self`; Live-Owner-Registry und fehlgeschlagene Ressourcen bleiben für Retry erhalten.
- Guard-first: zunächst fehlendes tray.py rot; 72 Contracts, 21 Windows-Mocks plus zwei standardmäßig übersprungene Native-Opt-ins grün. Separater eigener NativeTray-Smoke im Parent-Controller grün (0,176 s ein Lauf): eigene Threads beendet, eigenes HWND aus pystrayMap entfernt, HICON freigegeben, Fokus/Clipboard-Sequence unverändert. Keine Mikrofone, Modelle, globalen Tasten oder Altstack-Aktionen.
- Grenzen: private Producer-ABI ist versionsgebunden. Teilweise fehlgeschlagene NativeLoop-Bereinigung wird ohne sichere Schließungsfakten weiter gehalten; kein fremdes HWND und kein erzwungener Threadabbruch. Explorer-/Suspend-/Shell-Fehler-Pilot bleibt offen.
- Parent integriert nur Sourcecommit `8e1e379`; diese Context-/Handoff-Metadaten gehören ausschließlich zum Helper. Ownership bleibt aktiv, kein PR/Merge durch Helper.

## Active Handoff

- `handoffs/2026-10-14-hugin-windows-tray-helper.md`

Dieser Helper-Branch; vorheriger UIA-Handoff `handoffs/2026-10-14-hugin-windows-uia-helper.md`.
Haupthandoff weiterhin `handoffs/2026-10-14-hugin-v1.md` auf dem Integrationsbranch.
