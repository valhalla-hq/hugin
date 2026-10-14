# Hugin V1 Spec

Stand: 14.10.2026. Arbeitsvertrag für die erste lokale Windows-Version. Funktionsumfang durch die Unterhaltung bestätigt; technische Standardwerte sind unten als Vorschläge gekennzeichnet. Umsetzung und Hardware-Abnahme stehen aus.

## Ziel und Kontext

Brian erhält eine einzige im Hintergrund laufende Anwendung für Diktieren und Vorlesen. Die Logitech MX Master 3, Alt+Y, lokale Whisper-/Qwen-Verarbeitung und beide bestätigten Stimmen bleiben nutzbar. Ein kleines Fenster erklärt die Bedienung und zeigt Zustand, Stimme, letztes Diktat und Diagnose. Technische Einstellungen pflegen Agents im Repository.

Arbeitsordner: C:/Users/brian/Hugin. Referenzhardware: Windows x64, RTX 4070 Laptop mit etwa 8 GB VRAM. Es existiert noch kein Hugin-Quellcode oder veröffentlichter Build. Quellen und Nachweisgrenzen stehen in [evidence.md](evidence.md).

## Begriffe und Eigentümer

| Begriff | Bedeutung |
| --- | --- |
| Diktat | Aufnahme, Transkription und einmaliger Versuch der Textübergabe als ein Auftrag. |
| Vorleseauftrag | Auswahl-Erfassung, Qwen-Erzeugung und Wiedergabe als ein Auftrag. |
| Freya | Anzeigename des unveränderten Profils deutsch-3; anfänglicher Standard. |
| Tyr | Anzeigename des unveränderten Profils deutsch-a; manuell wählbare Alternative. |
| Letztes Diktat | Genau ein fertig transkribierter Text im RAM; weder Verlauf noch Audiospeicher. |
| Einfügeziel | Vordergrundfenster und fokussiertes Eingabeelement beim Stoppen der Aufnahme. |
| Einfügeübergabe | Punkt, an dem Hugin die Einfügeeingabe an Windows sendet. Danach kann Hugin die Änderung nicht zuverlässig zurücknehmen. |
| Bereit | Die für eine Funktion erforderlichen Komponenten sind geprüft; keine Garantie für unbekannte Zielprogramme oder physische Tastenzustellung. |

Die Steuerung besitzt Auftragszustand, Eingaben, Mikrofon, Audioausgabe, Zwischenablage und Ergebnisspeicher. Sie unterscheidet den aktuellen Nutzerauftrag von entwerteten Engine-Operationen, deren Ressourcen noch nicht freigegeben sind. Worker besitzen ihre Engine-Ressourcen und melden geprüfte Ereignisse. Fenster und Tray stellen denselben Zustand dar und interpretieren keine Worker-Rohmeldungen erneut.

## Funktionale Anforderungen

| ID | Vertrag |
| --- | --- |
| REQ-001 | XBUTTON2/vordere Taste und Alt+Y rufen denselben Diktat-Toggle auf. Ein physischer Druck erzeugt eine Aktion; Halten/Wiederholung erzeugt keine zusätzlichen Toggles. Beide Seitentasten werden während Hugin-Betrieb für Hugin reserviert. |
| REQ-002 | Erster Toggle startet Aufnahme, zweiter beendet sie und transkribiert lokal. Aufnahme wartet nicht auf das Laden des Whisper-Modells. Sprache Auto und bisherige Decode-Parameter bleiben Standard. |
| REQ-003 | Ein fertiges Diktat wird höchstens einmal ins geprüfte Einfügeziel übergeben. Unmittelbar vor Übergabe müssen Ziel und die eigene Clipboard-Transaktion noch gültig sein. Hugin drückt kein Enter. Bei Änderung oder Unsicherheit erfolgt keine automatische Übergabe; der Text bleibt zum Kopieren verfügbar. |
| REQ-004 | XBUTTON1/hintere Taste liest die aktuelle kopierbare Textauswahl lokal vor. Ein weiterer Druck stoppt auch Erfassung, Vorbereitung und Erzeugung. Ohne aktuelle Auswahl keine Vorlesung von altem Zwischenablagetext. |
| REQ-005 | Diktat hat Vorrang: ausstehende TTS-Daten entwerten, Ausgabe stoppen, Stille der eigenen Audioausgabe bestätigen, dann Mikrofon öffnen. Während Aufnahme, Transkription oder Textübergabe startet kein Vorlesen. Kein automatisches Fortsetzen. |
| REQ-006 | Freya und Tyr verwenden die bisherigen Referenz-WAVs, Referenztexte, Modellrevision und Inferenzparameter unverändert. Anzeigename und Profilidentität bleiben getrennt. Kein automatischer Stimmwechsel bei Fehlern. |
| REQ-007 | Ein kleines Fenster zeigt Status, Tastenhinweise, Freya/Tyr-Auswahl, letztes Diktat mit Kopieren/Löschen und Diagnose kopieren. Schließen verbirgt das Fenster; Beenden im Tray beendet Hugin. Autostart öffnet kein Fenster. |
| REQ-008 | Stimmenwechsel stoppt einen aktiven Vorleseauftrag und gilt ab dem nächsten Auftrag. Während eines Diktats beeinflusst er die Aufnahme nicht. Die letzte Auswahl bleibt lokal gespeichert; initial Freya. |
| REQ-009 | Escape wird nur für einen aktiven Auftrag reserviert und bricht ihn ab. Vor der Einfügeübergabe darf danach kein Text eingefügt werden. Bereits übergebener Text wird nicht automatisch rückgängig gemacht. Außerhalb aktiver Aufträge bleibt Escape anderen Anwendungen verfügbar. |
| REQ-010 | Genau ein erfolgreich transkribiertes Ergebnis bleibt im RAM, auch wenn Einfügen misslingt. Kopieren ist eine ausdrückliche Zwischenablageaktion; Löschen, Ablauf, Ersetzen oder Beenden geben Hugins Referenzen frei. Ein Abbruch ersetzt das vorherige fertige Ergebnis nicht. |
| REQ-011 | Diagnose kopieren exportiert ausschließlich einen versionierten technischen Datensatz: App-/Engine-Versionen, Zustände, aktive Profil-ID, GPU/CPU-Modus, Eingaberegistrierung, letzter Ereigniszeitpunkt und Fehlercode. Keine Sprachinhalte, Fenstertitel, URLs, Roh-Exceptions oder Umgebungsdumps. |

## Zustände und Randfälle

Vordergrundzustand: STARTING, IDLE, RECORDING, TRANSCRIBING, DELIVERING, TTS_PREPARING, TTS_PLAYING, CANCELLING, ERROR, STOPPING. Komponentenbereitschaft wird separat geführt. Ein Qwen-Startfehler darf deshalb Diktieren nicht pauschal sperren; die Einschränkung muss sichtbar sein.

| Situation | Erwartetes Verhalten |
| --- | --- |
| Vorderer Toggle während TTS_PREPARING/TTS_PLAYING | TTS entwerten und Audio stoppen; Aufnahme nach bestätigtem Ausgabestopp starten. GPU-Abbruch darf parallel zur Aufnahme auslaufen. |
| Vorderer Toggle während TRANSCRIBING/DELIVERING oder Abbruch eines Diktats | Keine zweite Diktataufgabe anlegen. Status erklärt Verarbeitung; Escape bleibt Abbruchweg. |
| Vorderer Toggle während Abbruch eines Vorleseauftrags | Nach bestätigtem Ausgabestopp Aufnahme starten, auch wenn Qwen-GPU-Abbruch noch läuft. Der entwertete TTS-Auftrag bleibt nur für die Ressourcenbereinigung verfolgt. |
| Hintere Taste während eines Diktats | Keine neue Auswahl-Erfassung, Vorlesung oder Browsernavigation. |
| Escape während Aufnahme/Transkription/TTS | Aktuellen Auftrag entwerten, Mikrofon/Ausgabe schließen, verspätete Ergebnisse verwerfen. |
| Escape unmittelbar bei Textübergabe | Serialisierter Übergabepunkt entscheidet: vorher Abbruch ohne Einfügen, danach keine Rücknahmebehauptung. |
| Fokuswechsel innerhalb desselben Fensters | Eingabeelement und, soweit verfügbar, Auswahl-/Caret-Anker erneut prüfen. Bei Unsicherheit nur RAM-Ergebnis. Kein erzwungenes Zurückfokussieren. |
| Zwischenablage zwischenzeitlich vom Nutzer geändert | Keine alte Kopie darüber zurückschreiben. Nur eigene, noch gültige Transaktionen zurücksetzen. |
| Mikrofon fehlt, ist belegt oder fällt aus | Aufnahme nicht fälschlich als erfolgreich zeigen; sichtbarer Fehler, kein ungekennzeichneter Teiltext und keine automatische Übergabe. |
| Worker stirbt oder GPU-Inferenz scheitert | Auftrag ohne automatische Wiederholung beenden. Ein kontrollierter Wiederanlauf darf spätere Aufträge ermöglichen; Zustand bleibt ehrlich. |
| Qwen lässt sich nicht abbrechen | Eigene Ausgabe bleibt still. Vor neuer GPU-Inferenz tatsächliches Ende oder bestätigten Exit des ausschließlich eigenen Workers abwarten. |
| Zweitstart | Keine zweite Steuerinstanz, Hook-Kette oder Worker-Familie. Manueller Zweitstart darf das vorhandene Fenster zeigen; Autostart bleibt still. |
| Ruhezustand/Abmeldung/Gerätewechsel | Aktive Aufnahme/Wiedergabe beenden, Aufträge entwerten. Beim Fortsetzen Geräte und Komponenten prüfen, keine alte Aufnahme weiterführen. Neue Aktionen folgen den Windows-Standardgeräten. |

## Qualität, Daten und Betrieb

| ID | Vertrag |
| --- | --- |
| NFR-001 | Eingabe-, UI- und Audiopfad bleiben frei von Modellinferenz und blockierender Pipe-Verarbeitung. Statuswechsel werden ereignisgetrieben dargestellt. Reaktionsziele und Messung stehen im Plan. |
| NFR-002 | Aufnahme, Steuerprotokoll, PCM-Pakete, Ergebnis und Warteschlangen sind vor Allocation begrenzt. Die maximale Aufnahmedauer folgt dem tatsächlichen PCM-Pufferbudget. Überläufe melden Fehler und erzeugen keinen stillen Teil-Erfolg. |
| NFR-003 | GPU-Inferenzaufträge werden zentral serialisiert. Modellresidenz wird davon getrennt behandelt und mit beiden Engines geprüft; ein serieller Aufruf allein beweist keine ausreichende VRAM-Kapazität. |
| SEC-001 | Normalbetrieb läuft nach Einrichtung vollständig offline, ohne Telemetrie, Cloud-Fallback oder Laufzeitdownload. Standardmäßig keine persistenten Audio-, Diktat- oder Vorlese-Inhalte und keine History. Explizit kopierte Inhalte liegen anschließend in der vom Betriebssystem verwalteten Zwischenablage. |
| SEC-002 | Normaler Windows-Benutzer, private Worker-Verbindungen, nur eigene Prozesshandles/-familien bereinigen. Keine fremden Python-Prozesse anhand von PID, Namen oder Pfad beenden. |
| OPS-001 | Modelle, Stimmen und Laufzeiten gehören Hugin und bleiben nach Entfernen alter Installationen funktionsfähig. Versionen, vollständige Modell-/Stimmdateilocks und Herkunft sind reproduzierbar gesichert. Virtuelle Umgebungen werden neu hergestellt und nicht verschoben. |
| OPS-002 | Aktivierung und Rückweg sichern bisherige Konfiguration/Startverknüpfungen und prüfen die tatsächliche Windows-Dateisicht außerhalb Codex. Alte Hotkeys, Hooks und Autostarts sind beim produktiven Hugin-Test nicht gleichzeitig Eigentümer. |
| OPS-003 | Autostart pro Benutzer, genau eine Instanz, explizite stabile Pfade; unlesbare/ungültige Konfiguration erzeugt Fehler statt eines stillen Standardprofils. Keine Installation oder Aktualisierung fachfremder Software. |

Technische Standardwerte sind Implementierungsvorschläge aus dem Plan, keine neu behaupteten Nutzerentscheidungen. Die erste Version unterstützt kopierbaren Text, reguläre Eingabefelder und das normale Benutzerkonto. Gescannten PDFs fehlt ohne vorgelagertes OCR eine Textauswahl. Erhöhte Zielprogramme, geschützte Felder, unbekannte Clipboard-Formate und nicht prüfbare Caret-Positionen erhalten sichere Fehler-/Kopierwege statt universeller Erfolgszusagen.

## Abgrenzung

V1 enthält keine KI-Textkorrektur, Übersetzung, Sprachbefehle, dauerhafte Historie, Cloud-Anbieter, neuen Stimmen, Aufnahmebibliothek, Browseroberfläche, Plugin-System oder frei editierbare Hotkeys. Geschwindigkeitsregler, umfangreiche Einstellungen und Installer als einzelne EXE sind nicht Teil der ersten Abnahme. Kleine Status-/Fehlerhinweise ersetzen keine zusätzlichen Einstellungsseiten.

## Abnahmekriterien

| ID | Prüfbarer Fall | Deckt ab |
| --- | --- | --- |
| AC-001 | Physisches XBUTTON2 und Alt+Y starten/stoppen jeweils genau einmal; Halten erzeugt keine Doppelaktion; XBUTTON1/2 navigieren nicht im Browser. Flags der gemessenen Logitech-Eingaben sind enthalten. | REQ-001 |
| AC-002 | Deutsches Referenzdiktat wird nach Stop lokal erkannt; Aufnahmebeginn wartet weder auf Whisper-Laden noch Qwen-GPU-Abbruch. | REQ-002, NFR-001 |
| AC-003 | Ergebnis erscheint genau einmal im unveränderten Ziel ohne Enter. Fenster-/Control-Wechsel, geänderte Auswahl und unprüfbare Ziele erzeugen nur ein kopierbares RAM-Ergebnis. | REQ-003 |
| AC-004 | Auswahl aus Word, Browser und kopierbarem PDF wird gelesen; leere/fehlende Auswahl verwendet keinen alten Clipboard-Text. Hintere Taste stoppt auch vor dem ersten Ton. | REQ-004 |
| AC-005 | Diktat während Auswahl-Erfassung, Modellvorbereitung, Generierung und Wiedergabe stoppt hörbare Ausgabe vor Mikrofonaufnahme. Auch nach einem vorherigen hinteren Stopp beginnt Aufnahme ohne Warten auf Qwen-GPU-Abbruch. Ein terminales altes TTS-Ereignis darf nur dessen Ressourcen freigeben; alte Audioblöcke starten keinen Ton. TTS startet während Diktat nicht. | REQ-005, NFR-003 |
| AC-006 | Freya/Tyr-WAVs, Referenztexte und Modellhashes stimmen; beide Stimmen bestehen den Hörvergleich auf demselben synthetischen Text. Wechsel stoppt TTS und beeinflusst Diktat nicht; Auswahl überlebt Neustart. | REQ-006, REQ-008 |
| AC-007 | Fenster enthält exakt die vereinbarte Ansicht, bleibt bei Aktionen ohne Fokusübernahme und öffnet beim Login nicht. Tray, Fenster und Diagnose zeigen konsistenten Zustand; X verbirgt, Beenden beendet. Bei 100/150/200 Prozent DPI bleiben Bedienelemente erreichbar. | REQ-007, NFR-001 |
| AC-008 | Escape in allen aktiven Zuständen verhindert Ausgabe vor dem Übergabepunkt, stoppt Aufnahme/TTS und lässt verspätete Ergebnisse ins Leere laufen. Danach ist Escape in fremden Apps normal nutzbar. | REQ-009 |
| AC-009 | Fertiges Ergebnis bleibt trotz Einfügefehler kopierbar; es gibt genau einen Slot. Ablauf/Löschen/Beenden entfernen die App-Referenzen. Abbruch erhält das vorherige fertige Ergebnis. Keine Inhaltsdateien entstehen. | REQ-010, SEC-001 |
| AC-010 | Diagnose enthält nur das freigegebene Schema. Fixtures mit einzigartigen Sprachinhalten, Fenstertiteln und Exception-Payloads tauchen weder im Export noch in technischen Logs auf. | REQ-011, SEC-001 |
| AC-011 | Text-, HTML/RTF-, Bild- und Dateilisten-Clipboard-Fälle bleiben für die zugesicherten Formate erhalten. Nutzer-Kopieren während Capture/Delivery wird nicht überschrieben. Kopiert der Nutzer nach Bereitstellen des Transkripts, aber vor Einfügeübergabe, wird die Änderung am Commit-Punkt erkannt: kein Paste, RAM-Ergebnis bleibt. Nicht sicher kopierbare Formate werden abgewiesen. | REQ-003, REQ-004 |
| AC-012 | Fehlende/belegte Geräte, Pipe-Abbruch, malformed/zu große IPC-Daten, Queue-Überlauf, Worker-Crash und GPU-Fehler führen zu begrenztem, sichtbarem Fehlerverhalten. Ein gültiges Transkript über 64 KiB bis 256 KiB passiert den gerahmten Textweg; abgeschnittene, verdoppelte oder ungeordnete Textfragmente erzeugen kein Teilergebnis. Kein Wiederholen bereits übergebener Texte und kein falsches Bereit. | NFR-001, NFR-002, SEC-002 |
| AC-013 | Kalte/warme abgeschlossene Aufgaben auf Referenzhardware messen: Aufnahmebereitschaft, erster Ton, Textübergabe, Abbruch, CPU-Zeit, RAM-Prozessfamilie und GPU-Residenz. Zielabweichungen sind im Prüfbericht entschieden. | NFR-001, NFR-003 |
| AC-014 | Netzwerk deaktiviert und alte Installationspfade für einen isolierten Restore unzugänglich: STT und beide Stimmen funktionieren mit Hugin-eigenen Dateien; Locks prüfen vollständig. | SEC-001, OPS-001 |
| AC-015 | Gleichzeitiger Zweitstart, Escape-Registrierungskonflikt und belegtes Alt+Y erzeugen keine doppelten Owner und keine unbemerkte Teilaktivierung. Ein fremder Kontrollprozess bleibt bei Worker-Cleanup unangetastet. | REQ-001, REQ-009, SEC-002, OPS-003 |
| AC-016 | Regulärer Windows-Login, Explorer-Neustart, Ruhe/Fortsetzen und Standardgerätewechsel funktionieren ohne manuelles Skript. Fehler bleiben sichtbar; alte Aktionen werden nicht fortgesetzt. | REQ-007, OPS-003 |
| AC-017 | Aktivierungsprobe und Rückweg stellen jeweils exakt einen funktionierenden Stack her. Backups und tatsächliche externe Dateisicht sind geprüft; invalides Profil fällt sichtbar aus. | OPS-002, OPS-003 |

## Prüfstatus und offene technische Nachweise

Alle AC stehen auf **nicht ausgeführt für Hugin**. Aktuelle Bestandsnachweise sind keine Hugin-Abnahme. Hardware-Pilot muss insbesondere Hook-Zustellung, Clipboard-/Fokus-Abdeckung, Qwen-Abbruch und gemeinsame VRAM-Residenz entscheiden. Daraus darf ein begrenzter technischer Plan angepasst werden; bestätigte Produktanforderungen ändern sich nicht stillschweigend.

## Änderungslog

- 14.10.2026: V1 aus Grill-me, Bestandsaufnahme und akzeptiertem STORM-Vorschlag festgehalten. Kleines Interface, Freya/Tyr und die drei Ergänzungen Escape, letztes Diktat, Diagnose sind enthalten. Keine Implementierung ausgeführt.
