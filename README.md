# Hugin

Lokale Windows-App für Diktieren und Vorlesen mit den bestätigten Stimmen **Freya** und **Tyr**. Hugin soll Whispering und PipPal vollständig ersetzen.

Status am **21.10.2026**: Diktat, Vorlesen, Screenshot-Zwischenablage, Obsidian-Oberfläche, verschiebbare Mitleseleiste und Panel-Buttons sind integriert. Brian hat die Buttonabläufe einschließlich des Wechsels vom Vorlesen zum Diktat bestätigt. Die nächste beauftragte Stufe aktiviert Maussteuerung und stillen Windows-Autostart. [Einrichtung und Rückweg](docs/desktop-startup.md), [aktueller Handoff](handoffs/2026-10-21-mouse-startup.md). Vollständige Geräte-/Zielmatrix, nächster echter Login und Produktionspaket bleiben gesonderte Nachweise.

Der lokale Einstieg `C:\Users\brian\Hugin` zeigt auf den sauberen Main-Deploymentclone. Alle drei eigenen Umgebungen und echten Modell-/CUDA-Dateien sind dort aus geprüften lokalen Dateien wiederhergestellt. Die sechs ursprünglichen Planungsdateien bleiben mit identischen SHA256-Hashes unter `C:\Users\brian\Hugin-Planung-2026-10-14` erhalten. Dies aktiviert noch keine produktiven Bindungen.

## Verbindlicher Funktionsumfang

Die Panels enthalten jetzt zusätzlich **Diktat starten / Fertig & einfügen**
und **Vorlesen starten / Stopp**. Beim Diktat das Zielfeld während der Aufnahme
wählen; beim Vorlesen den Text vor dem direkten Buttonklick markieren. Die Buttons
erhalten den Fokus der anderen Anwendung. [Bedienung und Prüfgrenzen](docs/panel-actions-2026-10-21.md).

Die integrierte Pilotstufe aus PR21 ergaenzt eine optionale Mitleseleiste mit
Abschnittsanzeige, Pause/Fortsetzen und Stopp. Im Vorlesen-Panel laesst sie sich
mit "Mitleseleiste einblenden/ausblenden" steuern. Ausblenden gilt auch fuer
weitere Texte bis zum bewussten Einblenden; beim App-Neustart ist sie wieder
aktiviert. Die abgerundete Leiste laesst sich am Kopfbereich verschieben und
behaelt ihre Position waehrend der App-Sitzung. Details und verbleibende Hoerprobe:
[Mitleseleiste](docs/reading-panel-2026-10-21.md).

- Hintere Daumentaste / Zurück (XBUTTON1) oder Strg+Alt+D: Diktat starten/stoppen und Text einfügen.
- Vordere Daumentaste / Vorwärts (XBUTTON2) oder Strg+Alt+V: markierten Text vorlesen/stoppen.
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
exklusiv verfügbarer GPU gedacht. Der normale Start liest die explizit eingerichtete
Aktivierung; fehlt sie oder ist sie ungültig, startet kein Hook. Ein Pilot verändert
diesen dauerhaften Stand nicht. Alt+Y gehört nicht mehr zur Hugin-Belegung.
Fehlende Hardware-/Login-Nachweise werden nicht als erfolgreiche Tests gewertet.

Restore plant standardmäßig ohne Schreibwirkung. `--apply` materialisiert nur
die eigene Runtime eines validierten Ziel-Checkouts additiv, aus SHA256-geprüften
lokalen Dateien. Siehe [Offline-Restore](docs/offline-restore.md),
[Pilotverträge für Zielklassen und Diagnose](docs/pilot-contracts.md) und
[gemessene CPU-Pilotkosten](docs/performance.md). Der
[Hardware-Pilot](docs/pilot-runbook.md) beschreibt Start, Prüfung und Rückweg.
