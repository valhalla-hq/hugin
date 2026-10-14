# Hugin

Lokale Windows-App für Diktieren und Vorlesen mit den bestätigten Stimmen **Freya** und **Tyr**. Hugin soll Whispering und PipPal vollständig ersetzen.

Status am **14.10.2026**: Controller, native Oberfläche, Eingaben, Audio und lokale Worker sind verbunden. Echtes Whisper funktioniert in der eigenen CPU-Umgebung; GPU-/Hör-/Zielmatrix-Abnahme stehen noch aus. Whispering/PipPal und Autostarts bleiben unverändert. Quelle ist das private Repository valhalla-hq/hugin; Entwicklung folgt AGENTS.md und dem zentralen Brian-Projekt-Workflow.

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

`--pilot --show` startet das Interface mit Ctrl+Alt+Shift+F9/F10, ohne Maus-Hook.
Sprachaktionen in diesem Modus sind für den vorbereiteten Hardware-Pilot mit
exklusiv verfügbarer GPU gedacht. Normale Maus-/Alt+Y-Aktivierung ist derzeit
gesperrt. Der Benchmark-/Migrationsschritt folgt nach dem Pilot; fehlende
Nachweise werden nicht als erfolgreiche Tests gewertet.

Restore plant standardmäßig ohne Schreibwirkung. `--apply` materialisiert nur
die eigene Runtime eines validierten Ziel-Checkouts additiv. Siehe
[Worker-/Restore-Vertrag](docs/workers-api.md); vollständiger Offline-Paketrestore
wird gesondert geprüft.
