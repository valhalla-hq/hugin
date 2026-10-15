# Hugin Stream-Helper — 15.10.2026

## Auftrag und Git

- IA-004/005, IA-T06: reproduzierte Kopplung zwischen Qwen-Fortschritt und
  kreditgebremstem Audio beseitigen; Hardwareprobe nur vorbereiten.
- Repository valhalla-hq/hugin, Branch codex/hugin-stream-20261015-mjolnir.
- Eigener Worktree:
  C:/Users/brian/brian-projects/worktrees/hugin/hugin-stream-20261015-mjolnir.
- Control e3deecae6673a024aa9015a4387737fbec04c795; Preflight grün.
  Lifecycletool unterstützt origin/Branch statt SHA: neue eigene Branch von
  origin/mainbb700f0, danach ausschließlich eigener FF auf autorisierten
  Basishead5a238677ce0ff915b141f313e7960434cf92ad28.
- Sourcecommits: c2aeef69d5d10a851bc2b95412b4c82277e0b2bc (Worker/Guards),
  a8b8b479c327260532267c13b01c8d292b7991b7 (Probe/Guards).
- Kein Push, PR oder Merge gemäß Rootauftrag. Ownership aktiv auf Mjolnir;
  Remote-Nachweis/Freigabe steht aus. Metadatencheckpoint separat; Root soll
  ausschließlich beide Sourcecommits übernehmen.

## Umsetzung

- src/hugin/workers/server.py: ein wartender PCM-Providerchunk, ein separater
  kreditgebremster Writer. GPU-Generator und dessen close bleiben auf dem
  bisherigen Engineowner. Aktueller Writerchunk plus Queue plus produzierter
  blockierter Chunk höchstens4.320.000B, zusätzlich bestehendes begrenztes
  Framing-/Client-/Playerbudget. Kein größerer nativer Puffer, kein Silencefill.
- Cancel/Producerfehler wecken Queue-/Creditwartepfade. Partial-Writerfehler,
  fehlgeschlagener Generatorclose oder nicht beendeter Writer erlauben keinen
  Terminalnachweis. Gehaltener blockierter Writer bleibt erreichbar; eigener
  Familienexit ist dann die Release-Barriere. GPU-sync erst nach Writerexit.
- tests/contracts/test_worker_stream.py:9 Guards für Owner, verzögerte
  FIFO-Streams beider Stimmen, Capacity, Cancel, Threadctor/start, Pipefehler,
  Close-/Writer-/Sync-/Terminalbarrieren. Vorlaufguard zuerst rot, grün nach
  Fix; Producerfehler und Threadctor-Lifetime separat zuerst rot korrigiert.
- tools/probe_live_audio.py und test_probe_live_audio.py: explizites --root,
  Defaultplan read-only, --run für reale serielle Freya/Tyr-Pipeline, optional
  --cancel als dritter Tyr-Lauf. Echter EnginePool/Controller/PCMOutput;
  synthetische Selection/Input/Mic-Stubs, keine User-I/O-/Preferencewirkung.
  Spawnwrapper erhält Runtimeinterpreter/Handles und bindet SOURCE/src.
  Separate Source-/Runtimeheads; Provider-/IPC-/ACK-/Queuezeiten, bytegenaue
  Provider/Callback/Player-Hashes, CPU/PeakJobCommit. Queueunterläufe schlagen
  technisch fehl. Nur neue begrenzte numerische JSON-Traces unter eigenem
  Runtimepfad, keine Audio-/Textdateien oder Rohfehler.

## Verifikation und Grenzen

- Stable Interpreter C:/Users/brian/Hugin/.runtime/controller/Scripts/python.exe.
-345 Contracts/Integrationstests am Sourcehead a8b8b479 in23,835s grün.
  Private IPC ist real, Engines/Driver bleiben in diesen Tests Simulation.
  Die Vollsuite verwendet außerdem ihre eigenen temporären Offline-Fixtures;
  stabile Runtime, Modelle und Installationen wurden nicht geändert.
-7 Probescript-Guards: Defaultplan, Source/Runtime-Spawnbindung, typed failures,
  begrenzter numerischer Trace, Additivpfade, Executorretention und echter
  Controllerablauf mit simuliertem Pool/Driver einschließlich Unterlauf/Cancel.
- Syntax aller vier Source-/Testdateien, git diff --check, CLI --help und
  Default-Dry-run gegen C:/Users/brian/Hugin grün; starts_workers=false,
  plays_synthetic_audio=false, writes_technical_trace=false.
- Dokumentprüfung19 Anforderungen/17 AC, keine Probleme.
- Kein GPU-/Playback-/Mikrofon-/UI-/Paste-/Restartlauf. Keine Prozesse dieses
  Helpers bleiben laufen. Root besitzt App-/Altstackzustand und Hardwarefenster.
- Reale Qwen-Chunkzeiten, Familie-CPU/PeakJobCommit, physischer RAM/GPU-Peak,
  p95 und Hörurteil nicht durch diese Sourceprüfungen belegt. Native Probe ist
  vorbereitet und noch nicht ausgeführt. Root besitzt unabhängige Reviews.

## Fortsetzung

1. Root prüft und übernimmt genau die zwei Sourcecommits; kein Metadata-Merge.
2. Nur Root führt nach koordinierter exklusiver Pause die vorbereitete Probe
   mit stabilem Runtime-root aus. Erstplan ohne --run prüfen; technische
   JSON-Fakten einschließlich cleanup_confirmed und Samplegleichheit lesen.
3. Nach bestätigtem Abschluss eigener Ownership regulär freigeben; vorher
   Remote-/Context-/Handoff-Nachweis und ggf. separate Pushautorisierung klären.
   Keine Worktrees, Runtimes, Modelle oder ignorierten Caches löschen.

Starter: Lies Hugin AGENTS.md/CONTEXT.md, exakt diesen Handoff und
specs/2026-10-15-hugin-input-audio/{spec,plan,tasks}. Nur dieser eigene aktive
Helperworktree darf geändert werden. Kein Push/PR/Merge und keine Hardware-
oder Altstackaktion; Root besitzt Integration und reale Abnahme.
