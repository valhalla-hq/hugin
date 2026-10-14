# Pilot: Zielklassen und Diagnose

`config/targets.json` ist agentengepflegte Konfiguration. Beide Listen sind
anfangs leer: automatische Textübergabe und der Ctrl+C-Lesefallback sind damit
für alle Zielklassen gesperrt. Direkte Standard-Edit-/UIA-Auswahl und das
manuelle Kopieren eines vollständigen RAM-Diktats bleiben verfügbar.

Eine Freigabe benennt die exakte `control_class` und eine vorhandene Markdown-
Datei im Repository als `evidence`. Für `delivery` kommt
`restore_delay_seconds` (0,02 bis 2 Sekunden) hinzu. Ein vorhandener Dateipfad
beweist keine Abnahme: Die Datei muss die tatsächlich geprüften Anwendungen,
Versionen, Auswahl-/Fokus-/Caret- und Clipboard-Rennen sowie Einschränkungen
festhalten. Eine Klassenfreigabe ist keine universelle Kompatibilitätszusage.
Vor dem Pilot werden keine Einträge aktiviert. Doppelte Schlüssel, Wildcards,
ungültige Typen und fremde Nachweispfade führen zu einem Konfigurationsfehler.

Die kopierbare Diagnose enthält ausschließlich das feste Schema aus
`Controller.diagnostic`: App-Version, Zustand, Freya/Tyr und technische
Profil-ID, ausgewählte installierte Paketversionen, Zeitpunkt/Alter der
letzten Eingabe, technische Komponenten-, Fehler- und Bereinigungszustände.
Paketversionen stammen aus Metadaten der eigenen STT-/TTS-Umgebungen beim
App-Start; unbekannte Werte bleiben `null`. Sie beweisen weder einen geladenen
Treiber noch eine erfolgreiche Inferenz. Es werden dafür keine Engines importiert.

Text, Audio, Dokumenttitel, Zielpfade, Gerätebezeichnungen, Umgebungsvariablen
und rohe Ausnahmen gehören nicht in diese Diagnose. Das letzte vollständige
Diktat wird separat ausschließlich im RAM gehalten und nach 300 Sekunden,
Löschen oder Beenden freigegeben. Abgeschlossene Worker-Nachrichten und
Operationsdaten bleiben nicht im folgenden blockierenden Idle-Read erhalten.
Dies ist keine Zusage einer sicheren Löschung nativer Speicher-Caches.
