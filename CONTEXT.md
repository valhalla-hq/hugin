# Hugin Context

Status: implementation
Owner: Brian
Type: application
Data boundary: Privater Quellcode, kuratierte Konfiguration, Paket-/Modelllocks und bestaetigte kleine synthetische Stimmreferenzen. Keine persoenlichen Diktate, Dokumente, Audioaufnahmen, Credentials, Rohlogs, Modellgewichte oder virtuellen Umgebungen in Git.
Source truth: `valhalla-hq/hugin`

## Goal

Brian hat am 14.10.2026 Spec und Plan unter C:/Users/brian/Hugin/specs/2026-10-14-hugin-v1 erstellt und die schrittweise Umsetzung beauftragt. Kleine native Oberflaeche, XBUTTON2 und Alt+Y fuer Diktat-Toggle, XBUTTON1 fuer Vorlesen-Toggle, Diktat stoppt Vorlesen, beide unveraenderten Stimmen Freya/deutsch-3 und Tyr/deutsch-a. Escape-Abbruch, ein letztes RAM-Diktat mit Kopieren/Loeschen, technische Diagnose ohne Inhalte. Whispering und PipPal laufen bis zur geprueften Umstellung weiter. Lokaler Einstieg C:/Users/brian/Hugin; vorhandene Planungsdateien erhalten und im ersten exklusiven Task uebernehmen.

## Current State

- Private Initialisierung und Katalogregistrierung abgeschlossen. Pilot-PR https://github.com/valhalla-hq/hugin/pull/1 am unveränderten geprüften Head b3ee07cb18b94764a1ea24b56179ae329382b868 integriert; Merge cf1c70570b790211b54ce27e8a93b8e641703d69.
- Restore-/Einstiegsnachweis aus PR2 integriert, main e762108bf189ce3428f6fba9cca6f2cbb412a7ce. Frühere Task-Ownership freigegeben.
- Aktiver Task codex/hugin-style-pilot-mjolnir: Darstellung nach drei Nutzerreferenzen in Nachtblau/Violett und eigenes Raben-Icon, ohne Funktionserweiterung. Erster GPU-/Sprachpilot und sichtbarer Teststart beauftragt; geordnete vorübergehende Altstack-Pause ausdrücklich freigegeben. Siehe specs/2026-10-14-hugin-v1/style-pilot.md.
- Coordinator, Windows-Adapter samt isoliertem UIA/COM-Gerätesignalen, bestätigtem Trayabschluss, Worker-IPC, eigene Audioadapter und kleines Interface verbunden. 252 Contracts/Integrationsprüfungen und 44 Windows-Prüfungen ohne Skips grün; docs/compile/diff geprüft.
- Main cf1c705 vollständig aus 29 echten Modell-/CUDA-Dateien und 122 lokalen Wheels wiederhergestellt: drei frische Umgebungen, Versionen/pip check grün; Apply 279,716s, Wiederholung ohne Neuinstallation 63,824s. 44 Windows-Prüfungen ohne Skips und echte CPU-Probe aus der finalen Installation grün; GPU-/Hör-/physische Zielmatrix-Abnahme offen.
- C:/Users/brian/Hugin ist ein geprüfter Junction zum sauberen _repos/hugin-Mainclone. Die sechs ursprünglichen Planungsdateien bleiben mit identischen Hashes in C:/Users/brian/Hugin-Planung-2026-10-14 erhalten. Keine venv verschoben.
- Whispering/PipPal und produktive Tasten/Autostarts sind unverändert. Keine Hugin-Gesamtabnahme behauptet.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Next Step

- Darstellungs-/Iconanpassung und begrenzte Probe prüfen, anschließend autorisierte geordnete Pilotpause und seriellen GPU-Test durchführen. Normale Eingaben bleiben technisch gesperrt; sichtbarer Pilot Ctrl+Alt+Shift+F9/F10. GPU-/Hör-/Zielmatrix-Gesamtabnahme und produktiver Wechsel bleiben offen.

## Active Handoff

- `handoffs/2026-10-14-style-pilot.md`
