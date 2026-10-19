# Hugin

Lokale Windows-App für Diktieren und Vorlesen mit den bestätigten Stimmen **Freya** und **Tyr**. Hugin soll Whispering und PipPal vollständig ersetzen.

Status am **19.10.2026**: Der von Brian erfolgreich getestete Diktat-/Überschreibstand ist in [PR11](https://github.com/valhalla-hq/hugin/pull/11) gesichert. Darauf baut der [dritte Ton nach erfolgreichem Einfügen](specs/2026-10-19-dictation-completion-cue/spec.md) in [PR12](https://github.com/valhalla-hq/hugin/pull/12) auf: kurzer aufsteigender Dreiklang, genau einmal nach erfolgreicher Textübergabe samt Clipboardabschluss. 431 Source-/Integrationstests, getrennte Reviews und eine native Audioprobe bestehen; menschlicher Hör-/Diktattest der neuen Version steht aus. Die laufende Zweiton-Sitzung bleibt unverändert. Nachweise: [Completion-Cue-Prüfung](docs/completion-cue-2026-10-19.md), aktueller Einstieg: [Handoff](handoffs/2026-10-19-completion-cue.md). Keine vollständige Produktabnahme oder Maus-/Alt+Y-/Autostartumstellung. Quelle: privates Repository valhalla-hq/hugin.

Der lokale Einstieg `C:\Users\brian\Hugin` zeigt auf den sauberen Main-Deploymentclone. Alle drei eigenen Umgebungen und echten Modell-/CUDA-Dateien sind dort aus geprüften lokalen Dateien wiederhergestellt. Die sechs ursprünglichen Planungsdateien bleiben mit identischen SHA256-Hashes unter `C:\Users\brian\Hugin-Planung-2026-10-14` erhalten. Dies aktiviert noch keine produktiven Bindungen.

## Verbindlicher Funktionsumfang

- Vordere Daumentaste oder Alt+Y: Diktat starten/stoppen und Text einfügen.
- Hintere Daumentaste: markierten Text vorlesen/stoppen.
- Diktat unterbricht Vorlesen; Escape bricht eine aktive Aktion ab.
- Kleines Fenster und Statussymbol, Stimmenauswahl Freya/Tyr.
- Ein letztes Diktat vorübergehend im RAM, mit Kopieren/Löschen.
- Technische Diagnose kopieren, ohne Sprachinhalte.

## Planungsunterlagen

1. [Spec und Abnahme](specs/2026-10-14-hugin-v1/spec.md)
2. [Architektur und Umsetzungsplan](specs/2026-10-14-hugin-v1/plan.md)
3. [Aufgaben mit Abhängigkeiten](specs/2026-10-14-hugin-v1/tasks.md)
4. [Bestandsnachweise und feste Modellidentitäten](specs/2026-10-14-hugin-v1/evidence.md)
5. [Gegenprüfung und Planungsstatus](specs/2026-10-14-hugin-v1/review.md)
6. [Aktuelle Implementierung und offene Abnahme](specs/2026-10-14-hugin-v1/implementation.md)
7. [Darstellung und erster GPU-Pilot](docs/pilot-2026-10-14.md)

Der Nutzer hat die schrittweise Implementierung beauftragt. Produktive Aktivierung folgt erst nach Prüfung. Der aktuelle Arbeitsstand ist ausdrücklich noch kein fertig abgenommener Ersatz.

## Entwicklung

Python 3.12.10, eigene Umgebung unter .runtime/controller. Nach Installation der gelockten Controller-Pakete:

```powershell
& .runtime/controller/Scripts/python.exe tools/dev.py check --docs
& .runtime/controller/Scripts/python.exe tools/dev.py check --group contracts
& .runtime/controller/Scripts/python.exe tools/dev.py check --group integration
& .runtime/controller/Scripts/python.exe tools/launch.py --preview
& .runtime/controller/Scripts/python.exe tools/probe_cpu.py
```

Die Vorschau startet keine Eingaben, Aufnahme oder Sprachmodelle. Die CPU-Probe
erkennt ausschließlich das bestätigte synthetische Tyr-Referenzaudio, übergibt
an ein RAM-Testziel und schließt eigene Worker; sie verändert keine Zwischenablage.

`--pilot --show` startet das Interface mit Strg+Alt+D für Diktat und
Strg+Alt+V für Vorlesen, ohne Maus-Hook. Erneutes Drücken beendet die Aktion.
Sprachaktionen in diesem Modus sind für den vorbereiteten Hardware-Pilot mit
exklusiv verfügbarer GPU gedacht. Normale Maus-/Alt+Y-Aktivierung ist derzeit
gesperrt. Der Benchmark-/Migrationsschritt folgt nach dem Pilot; fehlende
Nachweise werden nicht als erfolgreiche Tests gewertet.

Restore plant standardmäßig ohne Schreibwirkung. `--apply` materialisiert nur
die eigene Runtime eines validierten Ziel-Checkouts additiv, aus SHA256-geprüften
lokalen Dateien. Siehe [Offline-Restore](docs/offline-restore.md),
[Pilotverträge für Zielklassen und Diagnose](docs/pilot-contracts.md) und
[gemessene CPU-Pilotkosten](docs/performance.md). Der
[Hardware-Pilot](docs/pilot-runbook.md) beschreibt Start, Prüfung und Rückweg.
