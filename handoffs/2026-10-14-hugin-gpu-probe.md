# Hugin GPU-Probe Helper Handoff

## Objective

Kleine explizite serielle CUDA-Probe mit unveränderten realen WorkerClient-/IPC-/OwnedProcess-Verträgen vorbereiten. Standardmodus lesend, Hardwareausführung ausschließlich durch Root nach dessen autorisierter Altstack-Pause. Zusätzlich unabhängige Standards-Linse auf den festen visuellen Fremdsourcehead.

## Git State

- Repository: valhalla-hq/hugin, privat.
- Branch: codex/hugin-gpu-probe-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-gpu-probe-mjolnir.
- Base: main e762108bf189ce3428f6fba9cca6f2cbb412a7ce.
- Source HEAD: e1fc382e9ac34693e1a68416d2525fb93927bbff; vorheriger Featurecommit c8bad0b5db0ee95e36869de5cf570ae51fa0b9fe. Beide remote-identisch nach ls-remote bestätigt.
- Dieser Kontext/Handoff ist ein separater Metadatacheckpoint; Sourcefixhash und Sourcebytes unverändert. Root cherry-pickt ausschließlich die geprüften Sourcecommits.
- PR: keiner für den bounded Helper; Gesamtintegration und Review bleiben bei Root.
- Ownership: aktiv auf Mjolnir bis regulärem project_workspace.py release; Worktree, Runtime und Caches erhalten.
- Authorization: Root delegiert nur tools/probe_gpu.py und gezielte Tests, anschließend eigenen Kontext/Handoff. Kein Produkt-/Protokollumbau, keine echten GPUläufe, kein Altstack-Start/Stopp oder Paket-/Runtimeumbau durch diesen Helper.
- Preflight-Control: e3deecae6673a024aa9015a4387737fbec04c795.

## Changed Files

- tools/probe_gpu.py: --root (Standard C:/Users/brian/Hugin), --run, optionale --samples. Plan startet keine Worker und schreibt nichts. Ausführung seriell mit CUDA-Ready-Prüfung und Fehler bei CPU-Fallback, 17 normalisierten Referenzwörtern, kalter/warmer STT-Inferenz, Offload und bestätigtem Familienende vor neuem CUDA-STT-Worker und später TTS. Beide Stimmen gleicher fest codierter synthetischer deutscher Text. Pro Sample höchstens 30s PCM, 24kHz mono PCM16, exklusive neue Dateien in einem neuen UUID-Unterordner von .runtime/pilot-audio; innere Pfadumleitungen abweisen. Kein Audio abspielen.
- tests/contracts/test_probe_gpu.py: simulierte Clients prüfen nur Orchestrierung, Fristen, CPU-Fallback, Inhaltfreiheit, PCM-/Schreibgrenzen und Cleanupbarrieren. Keine Provider-/CUDA-Abdeckung daraus ableiten.
- CONTEXT.md und dieser Handoff: ausschließlich Helper-Metadaten, eigener separater Commit.

## Verification

- Finaler Sourcefix: 14 Probe-Guards grün (0,141s), Ruff F, Syntax, git diff --check und echter CLI-Standardplan grün. Neues Terminal-vor-Callback-Szenario zuerst rot: cancelled Future konnte vor verzögerter cancel()-Rückkehr fertig werden; Probe meldete fälschlich kein Audio. Fix wartet Callback-Fakten und Terminal innerhalb einer gemeinsamen cancel_seconds-Frist, sonst worker_timeout/tts_cancel_callback. Keine ProductClientänderung.
- Initialer Probecheckpoint: vollständige Source-Suite 265 Tests grün/23,154s; nach dem Callbackfix nur die betroffenen 14 Guards erneut ausgeführt. Docs: 19 Anforderungen/17 AC ohne Probleme. Bestehender Restoretest der Suite installiert ein winziges Offline-Fixture ausschließlich in einem frischen eigenen Temp, keine echten Enginepakete oder vorhandene Runtime verändert.
- Reine verifizierte Referenzaufbereitung: 17 Wörter, 207560 Bytes PCM16 mono/16kHz, 6,48625s. Kein Transkriptinhalt im Bericht, kein Worker-/GPUstart.
- Fremd-UI-Standardsreview: Sourcehead 82c619b706979c6ac6b68c3cf3a4a64dcaf6e8f2 gegen e762108; nur src/hugin/ui.py, src/hugin/branding.py und tests/windows. Worktree-HEAD 44e428b enthielt identische relevante Sourcebytes; kein Edit durch den Reviewer.
- UI-Verifikation: 7 native UI-/Visual-Tests und 8 Cleanup-/Pump-Guards grün. Eigener synthetischer nativer Fenster-/Brand-Tray-Check: Fenster/Tray geschlossen, beide Traythreads beendet, angezeigte und wartende Weakref-Textobjekte freigegeben. Kein Hook, Modell, Mikrofon, Playback oder Clipboardzugriff.
- Keine neuen UI-Delta-Befunde. Zusätzliche Grenze bewusst nicht grün gewertet: 768px Bildschirmhöhe bei 150% Skalierung liefert am Mindestmaß keine vollständige Diktatzeile mit Padding. Basis e762108 scheitert ebenfalls (1px Textfeld), neuer Head verbessert im direkten Vergleich auf 35px, benötigt 48px. Bei 125%/768px und 150%/900px war die vollständige Textzeile im zusätzlichen Vergleich vorhanden. Root hat den Befund als bestehende Abdeckungsgrenze erhalten.

## Source And Data Boundary

Nur Source, kleine simulierte Fixtures und kuratierte Metadaten in Git. JSON-Bericht enthält technische Zahlen und HuginError code/phase, keine Transkript-/Text-/PCM-/Rawexception-Payloads. Eigene gehaltene Windows-Jobs liefern CPU und Peak-Job-Commit einschließlich Cleanup; Job-Commit ist kein physischer Working-Set-Peak. Fehlende Metrics bleiben ungemessen. Bei unbestätigtem Cleanup bleiben dieselben Client-Owner erreichbar, ein erneuter Probeaufruf startet keinen nächsten GPU-Slot.

## Running State

Keine Worker oder Hilfsprozesse dieses Auftrags mehr aktiv. Native Reviewfenster und Tray bestätigt geschlossen. Keine Altstackaktion, GPU-Modellladung oder bestehende Runtimeänderung durch diesen Helper. Root führt gegebenenfalls parallel eigene Vorbereitungen durch; daraus wird hier kein aktueller Hardwarezustand abgeleitet.

## Open Blockers

- Root/Core prüft Sourcefix e1fc382 vor Integration; kein eigener Unabhängigkeitsnachweis für diesen Helpercode.
- Echter GPU-/Sprachpilot, beide Stimmen anhören, physische Zielmatrix und Produktivwechsel stehen aus; Root ist accountable.
- Same-process-STT-Reload kann seinen Gerätetyp nicht erneut melden. Probe nutzt deshalb ausdrücklich neuen Worker nach Offload und bestätigtem Familienende mit neuer CUDA-Ready-Bestätigung; keine Same-process-GPU-Reloadabdeckung behaupten.
- Physisches Familien-RAM, GPU-Peak, p50/p95, OS-Cachekontrolle und vergleichbare Altstackmessung ungemessen.

## Pick Up Here

1. Root übernimmt nach unabhängigem Review nur c8bad0b und e1fc382; Metadaten bleiben im Helpercheckpoint.
2. Hardwarelauf ausschließlich Root nach autorisierter Altstack-Pause, mit stabiler Controllerumgebung: tools/probe_gpu.py --root C:/Users/brian/Hugin --run --samples. Ohne --run bleibt der Aufruf lesend.
3. Nach sauberem gepushtem Metadatacheckpoint die Ownership über project_workspace.py release freigeben, sobald Root den Helper abschließt. Nichts löschen oder venvs verschieben.

## Starter Prompt

Continue valhalla-hq/hugin from C:/Users/brian/brian-projects/worktrees/hugin/hugin-gpu-probe-mjolnir/handoffs/2026-10-14-hugin-gpu-probe.md. Read AGENTS.md, CONTEXT.md, this exact handoff and fresh Git/ownership state first. Sourcefix is e1fc382e9ac34693e1a68416d2525fb93927bbff, metadata separate. Root owns integration and the only authorized GPU/Altstack pilot; do not execute it as this helper. Keep existing runtimes/caches and old-stack processes untouched. If ownership is released, use the central verified continuation path or a new exclusive task worktree before edits.
