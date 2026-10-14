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

- `handoffs/2026-10-14-hugin-core.md` for this bounded helper branch.
- Overall accountable execution remains `handoffs/2026-10-14-hugin-v1.md`.

## Bounded Core Helper Checkpoint — 14 October 2026

- Exclusive helper worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-core-mjolnir; branch codex/hugin-core-mjolnir; foundation 9328f255980a5b896c3c7a356052a2b81bd25f20.
- T002 pure coordinator, typed events/effects, independent user/engine lifetimes, audio reset barrier, delivery commit guard, Freya/Tyr choice, single TTL RAM result and <=400-character TTS operation chunks implemented for parent review.
- Public API and adapter acknowledgement boundaries: docs/core-api.md. No I/O in reducer; owning adapters still prove actual silence, closure, delivery and native resource terminal/exit.
- Verification: 51 coordinator guards and 4 existing configuration checks pass; documentation check and compileall pass. Guard-first suite initially failed for the absent module; additional guards exposed and closed duplicate-selection and cancelled-init readiness gaps.
- Additional bounded STT idle-offload checkpoint follows 72fbd99715eb52463b86e3d7063d499e434fb048. `stt_idle_unload_seconds` comes from Settings.stt (initially 90); Tick schedules explicit `Action.OFFLOAD` with `Operation.job=None` through the same GPU slot only after all user/cleanup/resource work is free. New dictation capture may start, inference waits for matching terminal/observed exit. Successful offload preserves readiness for in-operation reload; failure blocks retry. Existing EnginePool.offload API was inspected only, not changed or called.
- Parent application integration, independent review, real IPC/providers, physical input/clipboard/audio and hardware/latency/VRAM acceptance remain pending. No full Hugin acceptance or production activation claimed.
- Ownership remains active. No helper PR, merge, global hooks, microphone, model loads or old-stack changes performed.
