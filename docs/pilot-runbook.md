# Kontrollierter Hardware-Pilot

Der private Pilotstand ist noch kein abgenommener Ersatz. Whispering und PipPal
bleiben bis zum geprüften Wechsel eingerichtet; normale Hugin-Maus-/Alt+Y-
Aktivierung und Änderungen an Autostarts sind technisch beziehungsweise
vertraglich gesperrt.

## Vorbereiten

1. Exakten Git-/Review-/CI-Stand und den aktiven Handoff lesen. Restore zunächst
   ohne `--apply` planen und lokale SHA256-Dateilocks prüfen.
2. Die drei eigenen Umgebungen am endgültigen Installationspfad aus lokalen
   Wheels herstellen. Keine venv verschieben und keine alten Pakete benutzen.
3. Den Altstack über seine geordneten Beenden-Wege pausieren. Brian hat am
   21. Oktober ausdrücklich verlangt, Whispering und PipPal während der
   weiteren Tests nach Hugin-Ende geschlossen zu lassen.
   Keine alten Prozesse erzwingen, keine Autostarts oder Profile ändern.
4. GPU-Belegung neu messen. Inferenz, Initialisierung, Warmup und Offload
   ausschließlich über den einzelnen Hugin-Slot ausführen. Keine zweite
   Sprachprüfung parallel starten.

## Start und Prüfung

```powershell
& .runtime/controller/Scripts/python.exe tools/launch.py --preview
& .runtime/controller/Scripts/python.exe tools/launch.py --pilot --show
```

Die Vorschau hat keine Sprachaktionen. Der Pilot verwendet
Strg+Alt+D für Diktat und Strg+Alt+V für Vorlesen und registriert
keinen Maus-Hook. Escape gilt nur während einer aktiven Aktion. Beide
Startbefehle nacheinander ausführen und die vorherige Instanz zuerst beenden.

Zuerst GPU-Whisper mit synthetischem Audio sowie Qwen mit Freya und Tyr prüfen;
anschließend Aufnahme, leere/kurze/lange Auswahl, wiederholtes Stoppen,
Vorlesen→Diktat, Fehler/Abbruch und bestätigtes Ende eigener Prozessfamilien.
Für Textübergabe mit einer eigenen synthetischen Testauswahl beginnen.
Automatisches Paste und Ctrl+C-Fallback bleiben bis zum dokumentierten
Einzelnachweis der Zielklasse gesperrt. Der RAM-Kopierweg bleibt verfügbar.

Word, Browser, Codex und kopierbare PDFs mit Fokus-/Caret-Wechsel,
Nutzer-Kopieren und zugesicherten Clipboard-Formaten messen. Versions-/
Zielabdeckung und Restore-Verzögerung in einem kuratierten Nachweis festhalten;
erst dann `config/targets.json` entsprechend pflegen. Keine privaten Inhalte
oder Aufnahmen in Git. Beide Stimmen hörbar vergleichen; simulierte Audio-
Callbacks ersetzen diesen Nachweis nicht.

Danach kalte/warme Vergleichsaufgaben, echte Geräte-/Resume-/Explorer-Fälle
und die AC-Matrix abarbeiten. Normale Maus-/Alt+Y-Bindungen sind erst Teil der
gesondert geprüften Aktivierung; ein guter Pilot aktiviert sie nicht selbst.

## Ende und Rückweg

Hugin über das Tray beenden und bestätigten eigenen Cleanup abwarten.
**Whispering und PipPal bleiben geschlossen.** Der geprüfte Starter
`tools/pilot_session.py --root <Installation> --head <Quell-SHA>
--runtime-head <Installations-SHA>` plant zunächst; erst `--run` startet Hugin.
Sein Sitzungsbericht meldet `old_stack_return: disabled`. Die früheren lokalen
Starter mit automatischer Rückkehr dürfen nicht erneut verwendet werden.
Bei Bedarf kann Brian die alten Apps weiterhin selbst normal starten. Diese
Änderung betrifft den Teststarter, nicht die Windows-Login-Autostarts. Bei offenem
Hugin-Cleanup den gehaltenen Owner gezielt erneut beenden; keine PID-/
Namenssuche als Ersatz für Eigentumsnachweise verwenden. Produktiver Wechsel,
Autostart-/Login-Abnahme und Rückweg bleiben T011/T012/T900/T901.
