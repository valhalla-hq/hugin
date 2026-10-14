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
- Aktiver Task codex/hugin-v1-mjolnir, Draft PR https://github.com/valhalla-hq/hugin/pull/1.
- Coordinator, Windows-Adapter, Worker-IPC, eigene Audioadapter und kleines Interface verbunden. 132 Contracts/simulierte Integrationsprüfungen grün; docs/compile/diff geprüft.
- Eigene STT/TTS-Umgebungen/Modelle im Worker-Helper vorbereitet; CPU-Whisper über native private IPC geprüft. Parent-Runtime wird additiv vorbereitet. GPU-/Hör-/physische Abnahme offen.
- Whispering/PipPal und produktive Tasten/Autostarts sind unverändert. Keine Hugin-Gesamtabnahme behauptet.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Next Step

- Integrierten Controller unabhängig gegen Spec und Standards prüfen, UIA-Leseweg und Restore vervollständigen, danach native Pilotnachweise sammeln. Normale Eingaben bleiben technisch gesperrt; Pilot Ctrl+Alt+Shift+F9/F10.

## Active Handoff

- `handoffs/2026-10-14-hugin-v1.md`.
