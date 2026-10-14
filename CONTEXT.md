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
- Task codex/hugin-v1-mjolnir dokumentiert anschließend den echten Restore und festen lokalen Einstieg; keine produktive Aktivierung.
- Coordinator, Windows-Adapter samt isoliertem UIA/COM-Gerätesignalen, bestätigtem Trayabschluss, Worker-IPC, eigene Audioadapter und kleines Interface verbunden. 252 Contracts/Integrationsprüfungen und 44 Windows-Prüfungen ohne Skips grün; docs/compile/diff geprüft.
- Main cf1c705 vollständig aus 29 echten Modell-/CUDA-Dateien und 122 lokalen Wheels wiederhergestellt: drei frische Umgebungen, Versionen/pip check grün; Apply 279,716s, Wiederholung ohne Neuinstallation 63,824s. 44 Windows-Prüfungen ohne Skips und echte CPU-Probe aus der finalen Installation grün; GPU-/Hör-/physische Zielmatrix-Abnahme offen.
- C:/Users/brian/Hugin ist ein geprüfter Junction zum sauberen _repos/hugin-Mainclone. Die sechs ursprünglichen Planungsdateien bleiben mit identischen Hashes in C:/Users/brian/Hugin-Planung-2026-10-14 erhalten. Keine venv verschoben.
- Whispering/PipPal und produktive Tasten/Autostarts sind unverändert. Keine Hugin-Gesamtabnahme behauptet.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Bounded Helper: GPU-Probe

- Eigener Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-gpu-probe-mjolnir, Branch codex/hugin-gpu-probe-mjolnir, Basis main e762108bf189ce3428f6fba9cca6f2cbb412a7ce. Preflight-Control e3deecae6673a024aa9015a4387737fbec04c795.
- Sourcecheckpoint c8bad0b5db0ee95e36869de5cf570ae51fa0b9fe ergänzt nur tools/probe_gpu.py und gezielte simulierte Ablaufguards; separater Sourcefix e1fc382e9ac34693e1a68416d2525fb93927bbff synchronisiert die Cancel-Callback-Fakten vor der Terminalauswertung. Beide sauber gepusht; dieser Kontext/Handoff folgt separat ohne Sourceänderung.
- Standardmodus plant lesend. Nur --run startet echte WorkerClient/private-IPC/OwnedProcess-Worker seriell: STT CUDA kalt/warm, Offload, bestätigter Abschluss, neuer CUDA-bestätigter STT-Worker und erneute Transkription, bestätigter Abschluss vor Qwen. Freya/Tyr gleicher synthetischer Text, bounded PCM und optional neue exklusive 24-kHz-PCM16-WAVs unter .runtime/pilot-audio. Cancel nach erstem Chunk; Callback und Terminal teilen die konfigurierte Cancel-Frist.
- Final 14 Probe-Guards grün, einschließlich zuerst rotem Terminal-vor-Callback-Regressionsguard; Ruff F/Syntax/Diff/CLI-Plan grün. Initialer Probecheckpoint: komplette Source-Suite 265 Fälle/23,154s, docs 19 Anforderungen/17 AC grün. Bestehender Restore-Suitetest installiert nur ein winziges Fixture im eigenen frischen Temp; keine echte Runtime-/Engineinstallation. Reine Assetprüfung: 17 Wörter, 207560 Bytes PCM16/16 kHz, 6,48625s; kein Worker gestartet.
- Keine GPU-/Mikrofon-/Playback-/Altstackaktion durch diesen Helper. Root ist für Altstack-Pause und den einzigen autorisierten Hardwarelauf verantwortlich. Same-process-STT-Reload, physisches RAM, GPU-Peak, p50/p95, Hörqualität und physische Zielmatrix bleiben ungemessen. Sourcefix wird vor Root-Integration unabhängig geprüft.
- Unabhängiger UI-Standardsreview: fester Fremdsourcehead 82c619b706979c6ac6b68c3cf3a4a64dcaf6e8f2 gegen e762108, nur ui.py/branding.py/tests/windows. Keine neuen Befunde; 7 native UI/Visual-Tests, 8 Cleanup-/Pump-Guards und eigener nativer Brand-Tray-Abschluss mit zwei beendeten Threads und freigegebenen Textreferenzen grün. Bestehende Grenze: 768px/150% lässt am Mindestmaß keine vollständige Diktatzeile zu; bereits Basis fehlerhaft. Kein Bestehen dieses zusätzlichen Falles behauptet. Eigene GPU-/Ops-Quellen zählen nicht als unabhängig geprüft.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Next Step

- Root schließt den unabhängigen Review von e1fc382, integriert ausschließlich die geprüften Sourcecommits und führt die gesondert autorisierte Altstack-Pause/GPU-Probe selbst aus. Dieser Helper startet keine Modelle. Ownership bleibt bis zum regulären Release des sauberen Metadatacheckpoints aktiv; keine Worktree-/Runtime-/Cachelöschung.

## Active Handoff

- `handoffs/2026-10-14-hugin-gpu-probe.md`
