# Diktat am aktuellen Cursor

Brian meldet erneut target_unverifiable in Hugin1.0.0 nach Zielwechseln.
Die Diagnose belegt: Text kopiert, native Erfassung erfolgreich, UIA-Feld
abgewiesen, keine automatische Übergabe. Die genaue interne UIA-Eigenschaft
dieses Fehlversuchs ist unbekannt. Eine parallele45-Sekunden-Leseprobe ergab
110 technische Stichproben:23 nicht textfähige Codex-Fokusmeldungen,
29 gültige Edit-Meldungen sowie58 andere Fokusmeldungen beim Wechseln.
Es wurden keine Sprach-, Feld-, Zwischenablageinhalte oder Fenstertitel gespeichert.

Whispering7.11.0s fixierter [Textservice](https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src/lib/services/isomorphic/text/desktop.ts)
ruft [write_text](https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src-tauri/src/lib.rs#L195-L240)
auf: Text publizieren,50ms warten, Strg+V an den aktuellen Fokus,100ms warten,
vorherigen Zwischenablagetext gegebenenfalls wiederherstellen. Es hält dort
keine frühere UIA-Feldidentität fest. Das ist ein Quellvergleich dieses Pins,
keine neue Laufzeitprobe von Whispering oder Aussage über alle Versionen.

Hugin1.0.1 übernimmt die Wahl des aktuellen Fokus am serialisierten
Einfügepunkt. Aufnahmeende und Transkription transportieren kein altes Ziel
mehr. Auch ein Wechsel nach Aufnahmeende oder während der Übergabe-Warteschlange
darf das neue Ziel wählen. Die UIA-Feldprüfung entfällt für Diktat; Vorlesen
behält seine eigene unveränderte Auswahl-Erfassung. Die frühere UIA-Delivery-
Attestierung einschließlich Integer-Offsets und separatem Prozessprotokoll wird
zusammen mit ihren abgelösten Tests entfernt.

Die native Erfassung erfolgt unmittelbar vor Strg+V. Ändert sich der native Fokus
während dieses kurzen Commit, erfolgt keine Eingabe. Abbruch/Auftragsgeneration,
einmaliger Commit, Transaktions-Token, Zwischenablagesequenz und Modifikatoren
bleiben geprüft; erkannte native Passwortfelder bleiben gesperrt. Eine fehlende
UIA-Feldmeldung ist kein Ablehnungsgrund mehr. Wie bei manuellem Einfügen bestimmt
das Zielprogramm die Annahme; submitted beweist die Windows-Übergabe, nicht den
Textverbrauch. Eine allgemeine Erkennung geschützter Browserfelder wird nicht
behauptet. Es gibt weder Enter noch Fokusaktivierung noch wiederholtes Paste.

Der Diktattext bleibt weiterhin für Strg+V erhalten. Späteres Kopieren hat
Vorrang. capture_native beschreibt nun die Erfassung beim Commit;
capture_field=not_required beschreibt den bewusst entfallenen UIA-Schritt.
config/targets.json v3 benennt die generische Paste-Freigabe current_focus.
Die bestehenden gemessenen Nachlaufzeiten werden weiterverwendet, ohne eine
weitere Veröffentlichung oder Wiederherstellung der Diktat-Zwischenablage.

Verifikation und Auslieferungsstand werden im
[exakten Handoff](../handoffs/2026-10-23-current-cursor-delivery.md) fortgeführt.
Der unveränderte1.0.0-Installer bleibt der Rückweg. Die echte Windows-Anmeldung
ist weiterhin eine eigenständige offene Abnahme; die Bestätigung der vier
physischen Maus-/Tastenabläufe vom22.10.2026 bleibt auf PR49 gespeichert.

Nachtrag1.0.2: Brian bestätigt1.0.1 mit Codex und Google-Suche, meldet aber
native Ablehnung in Teams. Die daraufhin freigegebene22-Sekunden-Leseprobe
zeigt110/110-mal TeamsWebView mit fokussiertem Chrome_WidgetWin_1 als echtem
Kindfenster (auch GA_ROOT passend). Prozess und Thread unterscheiden sich.
Die bisherige PID-Gleichheit ist daher eine falsche Voraussetzung. Der native
Produzent prüft jetzt die Zugehörigkeit zum aktuellen Vordergrundfenster mit
IsChild, oder identischen Fokus-/Vordergrund-Handles, und weiterhin gültige
PID/TID. Derselbe kurze Abschlussguard erkennt auch ein inzwischen abgelöstes
Kindfenster. Es gibt keine Teams-Sonderregel oder erinnerte Zielfensterliste.
Vorlesen behält seinen eigenen UIA-Auswahlweg; die unfreigegebene Clipboard-
Auswahlfallback-Liste bleibt leer. Positive Fensterbeziehung ist keine allgemeine
Textfeld-/Passworterkennung.

Zwei neue Reproduktionsfälle scheitern vor der Korrektur;46 gezielte Prüfungen
und536 vollständige Vertrags-/Integrationstests bestehen danach. Die zusätzliche
physische Eingabeprobe wird getrennt von diesen automatischen Tests bewertet.

Anschließende physische Rückmeldung: Einfügen in Teams funktioniert mit Alt+Y
problemlos. Die hintere Maustaste reagiert nur in Teams nicht, in Codex weiterhin.
Die schreibgeschützt gelesene Options+-Konfiguration erklärt den Unterschied:
Im Teams-Profil ist hinten Mikrofon-Umschaltung (Strg+Umschalt+M), vorne
Kamera-Umschaltung (Strg+Umschalt+O) zugewiesen. Die globalen Zuordnungen sind
WIN_BACK/WIN_FORWARD. Das passt zu Logitechs dokumentierten
[anwendungsspezifischen Belegungen](https://www.logi.com/en-us/software/logi-options-plus).
Für Hugins Seitentasten werden auch im Teams-Profil die normalen Mausfunktionen
Zurück/Vorwärts benötigt. Die zwei bisherigen Zuordnungen sind lokal außerhalb
Git gesichert; Options+ ist zur gezielten manuellen Änderung geöffnet.
Konfigurations-Readback und physischer Teams-Maustest stehen noch aus.
Keine direkte SQLite-Änderung, kein Eingabe-Hook-Probeprogramm gestartet,
kein weiterer App-Neubau oder Neustart durch diesen Befund erforderlich.
