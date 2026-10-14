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

## Active Handoff

- `handoffs/2026-10-14-hugin-workers.md`

## Bounded Engine Helper Checkpoint

- Executor for this helper: codex/hugin-workers-mjolnir, separate worktree; the parent Hugin task owns integration and completion. Ownership remains active, no helper PR or merge.
- Implemented bounded private IPC, atomic transcript completion, isolated Whisper/Qwen workers and parent-client API. See docs/workers-api.md. Parent centrally schedules initialization, inference and offload.
- Own .runtime/models/stt, .runtime/models/tts and .runtime/cuda were copied from exact existing local bytes and fully hash-verified. New STT/TTS venvs installed from 21/94 pinned dependency entries; both pip checks passed. Old runtimes and processes unchanged.
- 11 contract tests and 5 simulated worker integration tests passed. Real CPU Whisper completed silent-input cold/warm/offload/reload probes; real private IPC plus native Windows Job Object completed with observed family exit. No GPU model loaded, no microphone or playback.
- Native initialization must finish synchronously before starting the command reader: earlier reader placement reproduced a 60-second CPU initialization hang. Initialization cancellation therefore uses parent-held job watchdog/exit rather than an in-process acknowledgement.
- GPU inference/cancellation, both-voice hearing, combined residency, complete offline wheelhouse restore, speech accuracy and full hardware AC remain unverified. No T005/T006 completion or total Hugin acceptance claimed.
