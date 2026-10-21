# Maussteuerung und Windows-Anmeldung

Die neue Belegung ist **Zurück = Diktat**, **Vorwärts = Vorlesen**.
Alt+Y (Diktat) und Strg+Alt+V (Vorlesen) und die Panel-Buttons bleiben verfügbar. Erneutes Drücken beendet
die jeweilige Aktion; Diktat hat Vorrang vor Vorlesen. Während Hugin läuft,
führen die Seitentasten keine Browsernavigation aus. Logitech muss weiterhin
seine normalen Zurück-/Vorwärtsereignisse liefern; Hugin schreibt keine
Logitech-Einstellungen und erzeugt keine künstlichen Tastenkürzel.

## Einmalige Einrichtung

Vorher Hugin und die alten Eingabe-Apps regulär beenden. Die Einrichtung erfolgt
aus dem geprüften Hauptstand an der festen Installation, nicht aus einem
temporären Arbeitsverzeichnis. Es werden keine Modelle/Pakete installiert.

```powershell
& C:/Users/brian/Hugin/.runtime/controller/Scripts/python.exe C:/Users/brian/Hugin/tools/desktop_setup.py --root C:/Users/brian/Hugin
# Plan prüfen; dessen plan_sha256 unverändert verwenden:
& C:/Users/brian/Hugin/.runtime/controller/Scripts/python.exe C:/Users/brian/Hugin/tools/desktop_setup.py --root C:/Users/brian/Hugin --apply PLAN_SHA256
```

Der Plan liest nur. Apply sichert die exakten bisherigen Bytes unter
`.runtime/desktop-setup-v1`, schreibt den Aktivierungsstand in die konfigurierte
State-Ablage, entfernt genau `PipPal.lnk` und `Whispering Local STT.lnk` aus dem
Autostart des aktuellen Benutzers und legt `Hugin.lnk` an. Fremde Einträge bleiben
erhalten. Ein vorhandener unbekannter Hugin-Eintrag wird nicht überschrieben.

Die Verknüpfung verwendet die feste eigene pythonw.exe, tools/launch.py und
--root; ohne --pilot und ohne --show. Daher startet sie still im Infobereich.
Die bestehende Instanzsperre verhindert doppelte Eingabe-/Sprachinstanzen.
Normale Starts lesen activation.json nur; weder Autostart noch Tastenprofil
werden bei jedem Start neu geschrieben. Der separate Teststarter bleibt ein
ausdrücklicher Tastaturpilot und ist kein produktiver Einstieg.

Erneutes Apply mit **dem ursprünglichen Plan-Hash aus manifest.json** ist
idempotent und kann eine unterbrochene Anwendung fortsetzen. Fremde Änderungen
an Zielen oder Sicherungen führen vor weiteren Schreibzugriffen zum Abbruch.
Ein Fehler während der Vorbereitung hat noch keine aktiven Dateien verändert.
Die unvollständige Sicherung bleibt in einem eigenen desktop-prepare-Verzeichnis;
ein erneuter Aufruf kann die Vorbereitung frisch beginnen. Erst die vollständige
und validierte Sicherung wird als desktop-setup-v1 veröffentlicht. Der normale
App-Start führt nie Setup aus.

## Manueller Start und Rückweg

```powershell
# Mit Fenster; für stillen Start --show weglassen:
& C:/Users/brian/Hugin/.runtime/controller/Scripts/pythonw.exe C:/Users/brian/Hugin/tools/launch.py --root C:/Users/brian/Hugin --show
```

Vor dem Rückweg Hugin regulär beenden. Dann:

```powershell
& C:/Users/brian/Hugin/.runtime/controller/Scripts/python.exe C:/Users/brian/Hugin/tools/desktop_setup.py --root C:/Users/brian/Hugin --restore
```

Restore prüft zuerst alle aktiven Dateien und Sicherungen, stellt dann die
Originale bytegleich wieder her und behält die Sicherung. Ein inzwischen
geänderter Eintrag wird nicht überschrieben. Whispering/PipPal werden dabei
nicht gestartet; bei Bedarf anschließend bewusst manuell starten. Keine alten
Auto-Return-Hilfen verwenden. Ein Restore beendet keine laufenden Prozesse.

## Prüfgrenzen

Dateitransaktion, CLI-Persistenz und native Shell-Link-Erstellung haben getrennte
Tests. Native Hook-Registrierung beweist noch keinen physischen Mausklick.
Verknüpfungs-Readback und stiller Start beweisen noch keinen neuen Windows-Login.
Die erste echte Anmeldung und Brians Mausprobe werden ausdrücklich nachgetragen.

Stand 21.10.2026: PR28 ist integriert; die Umstellung wurde auf Mjolnir angewandt
und über Windows-Verknüpfung und Startup-Inventar zurückgelesen. Nur Hugin ist
von diesen drei Apps im Autostart. Die Original-Links sind bytegleich gesichert.
Auch der noch laufende separate Whispering-STT-Dienst mit altem Maus-Hook wurde
über sein bestehendes Stoppskript beendet. Hugin läuft aus der festen Installation
im normalen Mausmodus; für die aktuelle Probe wurde das Fenster bewusst gezeigt.
Zwei isolierte echte Starts ohne --show waren bereit und verborgen. Ein echter
neuer Windows-Login wurde nicht ausgelöst.
