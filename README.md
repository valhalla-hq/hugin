# Hugin

Lokale Windows-App für Diktieren und Vorlesen mit den bestätigten Stimmen **Freya** und **Tyr**. Hugin soll Whispering und PipPal vollständig ersetzen.

Status am **14.10.2026**: Umsetzung nach Spec begonnen. Konfiguration, bestätigte Stimmreferenzen und eine isolierte Python-/Prüfgrundlage sind vorhanden. Bestehende Sprachprogramme und Autostarts bleiben unverändert. Quelle ist das private Repository valhalla-hq/hugin; Entwicklung folgt AGENTS.md und dem zentralen Brian-Projekt-Workflow.

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

Der Nutzer hat die schrittweise Implementierung beauftragt. Produktive Aktivierung folgt erst nach Prüfung. Der aktuelle Arbeitsstand ist ausdrücklich noch kein fertig abgenommener Ersatz.

## Entwicklung

Python 3.12.10, eigene Umgebung unter .runtime/controller. Nach Installation der gelockten Controller-Pakete:

```powershell
& .runtime/controller/Scripts/python.exe tools/dev.py check --docs
& .runtime/controller/Scripts/python.exe tools/dev.py check --group contracts
& .runtime/controller/Scripts/python.exe tools/restore.py --target C:/Tools/Hugin-Probe
```

Der Restore-Befehl ist zunächst ein schreibfreier Plan. Nicht implementierte Prüfgruppen und Apply geben einen Fehlerstatus statt eines falschen Grünlaufs zurück. Audio-, Eingabe- und Engine-Tests werden mit ihren Umsetzungsschritten ergänzt.
