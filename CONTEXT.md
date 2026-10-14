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
- Coordinator, Windows-Adapter, Worker-IPC, eigene Audioadapter und kleines Interface verbunden. 108 Contracts/simulierte Integrationsprüfungen grün; docs/compile/diff geprüft.
- Eigene STT/TTS-Umgebungen/Modelle im Worker-Helper vorbereitet; CPU-Whisper über native private IPC geprüft. Parent-Runtime wird additiv vorbereitet. GPU-/Hör-/physische Abnahme offen.
- Whispering/PipPal und produktive Tasten/Autostarts sind unverändert. Keine Hugin-Gesamtabnahme behauptet.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Next Step

- Integrierten Controller unabhängig gegen Spec und Standards prüfen, UIA-Leseweg und Restore vervollständigen, danach native Pilotnachweise sammeln. Normale Eingaben bleiben technisch gesperrt; Pilot Ctrl+Alt+Shift+F9/F10.

## Active Handoff

- `handoffs/2026-10-14-hugin-core.md`

## Bounded Core Helper Checkpoint — 14 October 2026

- Exclusive helper worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-core-mjolnir; branch codex/hugin-core-mjolnir; foundation 9328f255980a5b896c3c7a356052a2b81bd25f20.
- T002 pure coordinator, typed events/effects, independent user/engine lifetimes, audio reset barrier, delivery commit guard, Freya/Tyr choice, single TTL RAM result and <=400-character TTS operation chunks implemented for parent review.
- Public API and adapter acknowledgement boundaries: docs/core-api.md. No I/O in reducer; owning adapters still prove actual silence, closure, delivery and native resource terminal/exit.
- Verification: 51 coordinator guards and 4 existing configuration checks pass; documentation check and compileall pass. Guard-first suite initially failed for the absent module; additional guards exposed and closed duplicate-selection and cancelled-init readiness gaps.
- Additional bounded STT idle-offload checkpoint follows 72fbd99715eb52463b86e3d7063d499e434fb048. `stt_idle_unload_seconds` comes from Settings.stt (initially 90); Tick schedules explicit `Action.OFFLOAD` with `Operation.job=None` through the same GPU slot only after all user/cleanup/resource work is free. New dictation capture may start, inference waits for matching terminal/observed exit. Successful offload preserves readiness for in-operation reload; failure blocks retry. Existing EnginePool.offload API was inspected only, not changed or called.
- Parent application integration, independent review, real IPC/providers, physical input/clipboard/audio and hardware/latency/VRAM acceptance remain pending. No full Hugin acceptance or production activation claimed.
- Ownership remains active. No helper PR, merge, global hooks, microphone, model loads or old-stack changes performed.

## Bounded Cleanup Retry Checkpoint — 14 October 2026

- Parent `1a189d7b706afff3ba58705b0222f411290f1740` fast-forwarded into this exclusive helper branch before the bounded producer fix. Root's normal launch remains gated.
- `RetryCleanup()` owns explicit Quit retries for retained audio-reset/capture-close jobs, including STOPPING. It clears pending dictation intent, emits only identity-bound cleanup effects and requires real matching closure acknowledgements. No new user generation, GPU release or repeated delivery.
- Six guards began red because RetryCleanup was absent; 57 Core guards and 129 total contracts/simulated integration tests now pass. Docs and diff checks pass. The isolated adapter seam probe flips shutdown readiness from false to true only when RetryCleanup is bound before Shutdown and the emitted reset is acknowledged after success.
- Root owns actual adapter wiring and native retry/device checks. Offline wheelhouse work is authorized next but remains unimplemented in this checkpoint. Ownership stays active.

## Bounded Offline Package Restore Checkpoint — 14 October 2026

- Follows cleanup source commit fa6141dd62fa372ebc87d17a50085389eedc199c on helper basis 1a189d7. Parent's later integration fixes are outside this helper delta. Scope is preparation/restore tooling, shared package facts, exact artifact locks, tests and curated handoff only.
- tools/runtime_packages.py owns package/wheel semantics once. locks/runtime-wheels.json binds controller 7 / STT 21 / TTS 94 wheels (3,205,420,299 bytes), exact existing versions and source-build provenance. All seven original controller artifact hashes match; superseded controller-wheels.json removed, no alias retained.
- Network is confined to explicit wheelhouse preparation Apply. Offline Restore defaults to a read-only validated plan; Apply uses local hash requirements, no index/dependency resolution/source build, in-place owned environments and Python 3.12.10 x64/Tk 8.6. Ambient pip configuration cannot redirect installs. No system upgrade or old-path dependency introduced.
- Faster Qwen at a70afc0f81f7f5f8801c3227968f1102f43f211c and Sox 1.5.0 were built with pinned tooling and source hashes; independent rebuilds yielded identical wheel SHA256. Runtime artifacts/build receipts/logs remain ignored.
- Full real-wheel probe: fresh controller/STT/TTS environments, exact installed versions plus pip check; first restore 266.20s, repeat 22.16s, unchanged installation proofs, socket block loaded in 39 child processes, zero network attempts. Model/CUDA files were synthetic 25-byte fixtures, no model imports/inference. Final isolated pip invocation separately reinstalled the seven real controller wheels with deliberately divergent ambient target/config: 7.08s, no external install and zero network attempts.
- Automated guards include real tiny-wheel pip/venv installation and read-only/hash/version/identity/ownership/preflight/no-op cases. Exact final count/checks and artifact hashes in handoffs/2026-10-14-hugin-core.md; operating instructions in docs/offline-restore.md.
- GPU/native model operation, independent offline copy of actual model/CUDA weights, physical devices, resume/recovery, real target insertion and production migration remain parent acceptance work. No full T009 or Hugin acceptance claimed. Ownership remains active; no helper PR/merge/production change.
