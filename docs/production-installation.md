# Hugin installieren und aktualisieren

Der private Offline-Installer ist für Brians geprüften Windows-x64-Rechner mit
NVIDIA/CUDA vorgesehen. Er enthält Hugin, Python, die drei festen Paketstände,
Sprachmodelle, Stimmen und Signaltöne. Er benötigt weder eine Entwicklungsumgebung
noch einen Paketdownload oder Administratorrechte. Der lokale Build ist unsigniert;
eine öffentliche Verteilung und allgemeine Gerätefreigabe sind nicht enthalten.

## Installation

Alle Dateien des Installer-Ordners zusammenlassen: Hugin-1.0.0-Setup.exe benötigt
seine benachbarten .bin-Dateien. Hugin vorher über sein Infobereich-Symbol regulär
beenden. Der Installer beendet keine laufende Anwendung automatisch.

Die Einrichtung legt einen eigenen Versionsordner unter
%LOCALAPPDATA%/Programs/Hugin/releases an. Der Startmenü-Eintrag heißt Hugin.
Die bekannte Hugin-Autostart-Verknüpfung wird mit exakter Sicherung auf die neue
Hugin.exe umgestellt. Hugin startet nach der Anmeldung still im Infobereich.
Whispering und PipPal werden nicht wieder aktiviert.

Die dauerhafte Belegung lautet:

- Maus zurück oder Alt+Y: Diktat starten, erneut drücken zum Beenden und Einfügen.
- Maus vorwärts oder Strg+Alt+V: markierten Text vorlesen, erneut drücken für Stopp.
- Escape: aktive Aktion abbrechen.
- Die Panel-Buttons bleiben zusätzlich verfügbar.

Während einer Aufnahme das gewünschte Textfeld auswählen. Der fertige Text bleibt
auch für Strg+V in der Zwischenablage. Beim ersten Vorlesen muss Hugin die Modelle
und Rechenroutinen vorbereiten; spätere Texte verwenden die geladenen Komponenten.
Die begrenzte Ladefrist beträgt dafür 120 Sekunden. Sie ist keine feste Wartezeit:
Sobald die Engine bereit ist, arbeitet Hugin weiter. Abbrechen und reguläres
Beenden behalten ihre eigenen kurzen Fristen.

## Aktualisierung und Deinstallation

Jeder neue Build erhält einen getrennten Versionsordner. Programmdateien werden
nicht mit einer älteren Version vermischt. Die eingerichtete Eingabeaktivierung
und die ausgewählte Stimme bleiben erhalten; eine erneute Installation desselben
Builds setzt die Einstellungen nicht zurück. Der normale App-Start liest die
Aktivierung und führt keine erneute Einrichtung aus.

Die Deinstallation über Windows entfernt die eigenen Programmdateien und nur die
belegte eigene Autostart-Verknüpfung. Einstellungen, Einrichtungs-Sicherungen und
Laufzeit-Caches bleiben erhalten. Frühere Apps starten dadurch nicht wieder.

Die bisherige Quellinstallation bleibt als Rückweg erhalten. Ihre ursprüngliche
Verknüpfung liegt zusätzlich in der exakten Einrichtungssicherung unter
.runtime/desktop-setup-v1 des installierten Versionsordners. Eine Rückkehr erfolgt
nach regulärem Beenden mit dem geprüften Wiederherstellungswerkzeug; Sicherungen
nicht von Hand überschreiben oder löschen.

## Prüfgrenzen

Die Prüfnachweise unterscheiden Paketintegrität, echte Windows-Registrierung,
wiederholte normale Hintergrundstarts und den tatsächlichen nächsten Login.
Verknüpfungsprüfung oder manueller Hintergrundstart beweisen keinen Windows-Login.
Die nächste reale Anmeldung und eine erneute Bedienprobe mit Brians physischen
Maustasten bleiben ausdrücklich eigene Abnahmen. Artefakt- und Messwerte stehen
im zugehörigen Produktions-Build-Bericht.
