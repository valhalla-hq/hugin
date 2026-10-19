# Geprüfter Word-Dokumentpfad am 19.10.2026

Main `defe3d8f0ef9e564da1936a77b931476cbafc98a` lehnt ein eigenes,
synthetisches Word-Dokument in `_edit_pattern` ab: Fokus-Controltype Document
(50030), TextPattern vorhanden, ValuePattern fehlt. Die beiden Bereiche
liefern explizit boolesches `IsReadOnly=false`, keine eingebetteten Kinder und
eine unter dem fokussierten Dokument liegende Edit-Enclosure. Word-Version:
16.0.20430.20146. Keine bestehenden Benutzerdokumente wurden geöffnet.

Der gemeinsame Feldbinder unterscheidet nun den Schreibschutzvertrag:
Edit/ComboBox behalten ValuePattern; Document braucht den expliziten
TextRange-Schreibschutz für DocumentRange UND aktuelle Auswahl. Unbekannte,
gemischte und typfremde Werte bleiben gesperrt. Jede Aufnahme und warme
Bestätigung prüft dies einschließlich der abschließenden Prüfung nach der
letzten Textlesung. Enclosures, Identitäten, UTF-16-Auswahlgrenzen,
Objektfreiheit und die bestehende 50ms-Attestation bleiben erhalten.
Keine Klassenfreigabe, zusätzliche Eingabeart oder IPC-Änderung.

Grundlagen: Microsofts [Document-Vertrag](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-supportdocumentcontroltype)
und [GetAttributeValue-Vertrag](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-getattributevalue).

## Eigene reale Word-Probe

Ein neues, ungespeichertes, einseitiges Dokument enthält ausschließlich
synthetischen Testtext. Über den echten ClipboardService, NativeClipboard,
SelectionProbe und private IPC wurden jeweils genau einmal geprüft:

- Einfügen am Textende (UTF-16-Auswahl 23..23).
- Ersetzen der markierten Teilmenge (0..7).
- Ersetzen der Gesamtauswahl einschließlich Absatzende (0..36).

Alle drei Ergebnisse: `submitted=true`, `restored=true`, kein ausstehender
Clipboard-Restore; das sichtbare Ergebnis wurde nach jedem Schritt geprüft.
Die eigenen Prozessfamilien wurden abgeschlossen. Kein Enter/Absenden.
Das eigene Testdokument bleibt ungespeichert geöffnet. Word-Automation nutzte
den Computer-Use-Skill; die Anwendung selbst führte ihre normale Einfügetransaktion
aus. Die ignorierten lokalen Probe-Skripte gehören nicht zur Produktinstallation.

## Messungen und Grenzen

- Erste gemessene Aufnahme des neuen Word-Pfads: 0,427s.
- Fünf neue Prüffamilien am gleichen Ziel: initiale Aufnahme 0,358–0,420s;
  vorbereitete warme Bestätigung 28,4–34,6ms, jeweils gleiche Identität und
  erfolgreiche einmalige Frischeprüfung. Keine p95-Zusage aus fünf Stichproben.
- CPU-Zeit pro Prüffamilie 0,281–0,328s; Peak-Job-Commit 40,6–42,5MB.
  Job-Commit ist keine Messung des physischen Working Sets.
- Die drei vollständigen Aufnahme-/Einfüge-/Restoreproben: 1,106s, 1,196s und
  1,121s; zwei Prüffamilien je Probe, CPU jeweils 0,281–0,344s und Peak-Job-Commit
  40,5–41,2MB pro Familie. Mikrofon, Whisper, GPU und Benutzerreaktion sind
  nicht Teil dieser Zeiten. Main konnte denselben Word-Task nicht abschließen;
  ein gleichwertiger abgeschlossener Vorhervergleich fehlt.
- Agenttokens und physischer Peak-Prozessfamilien-RAM wurden nicht gemessen.

418 Source-/Integrationstests in24,322s, drei eigene native Range-/IPC-Tests
in1,281s und Dokumentcheck grün. Die neue Document-Probe war vor dem Fix rot;
unbekannter/gemischter Schreibschutz, späte Änderungen, fremde Enclosures,
Objekte und Unicode sind abgedeckt. Beide unabhängigen Reviews ohne Befund;
Reviewchecks:57 Tests0,268s und100 Tests0,503s. Geprüfter Produzenten-SHA256:
588829e4aa16673711b1065b2c84fbdcd9bfc6de95495236fedf42d994dd0e93.

Geschützte/mehrseitige Word-Dokumente, Tabellen, Bilder und die vollständige
Alltagsmatrix sind nicht nativ abgenommen. Objektbehaftete oder anderweitig
nicht eindeutig prüfbare Dokumente bleiben geschlossen. Google wurde nicht
erneut gesteuert; sein bestehender Edit-Vertrag und die Providerregressionen
bleiben erhalten. Keine produktiven Maus-/Alt+Y-Bindungen oder Autostartänderung.

## Codex-Leseprobe vor der Nutzerabnahme

Codex26.1013.4894.0: Brian hat das leere Nachrichtenfeld manuell fokussiert.
Eine rein lesende Probe fand Edit50004, Text-/ValuePattern, eine leere Auswahl,
keine eingebetteten Kinder und bestätigte die Feldidentität. Main UND Kandidat
haben die echte Aufnahme sowie jeweils fünf private IPC-Bestätigungen bestanden.
Main-Aufnahme0,379s, Kandidat0,357s; warme Aufrufe12,5–60,2ms bzw.12,6–18,4ms.
Diese Aufrufzeiten enthalten Scheduling; die unveränderte50ms-Regel misst das
Alter der vom Produzenten frisch ausgestellten Attestation. Alle Frischeprüfungen
bestanden. CPU/Prüffamilie Main0,250–0,375s/Kandidat0,250–0,344s;
Peak-Job-Commit Main40,7–42,4MB/Kandidat40,6–41,4MB. Kleine aufeinanderfolgende
Stichproben erlauben keine belastbare Geschwindigkeitsverbesserungsbehauptung.

Kein Codex-Paste, kein automatisches Fokussieren und kein Testtextversand.
Der frühere Codex-Diktatfehler ist an diesem leeren Feld nicht reproduziert;
der Word-Fix ändert den Edit-Vertrag nicht. Diese Leseprobe allein belegte noch
keinen echten Diktatablauf oder eine vollständige Produktabnahme.

## Bestätigter Diktat-Zwischenstand

Brian startet den Kandidaten ebe832dc9bda4ae9880dd5c35c425bf414888beb manuell
und bestätigt anschließend ausdrücklich mehrere erfolgreiche echte Diktat-
und Überschreibtests im zuvor angeleiteten Codex-Test. Er beauftragt, diesen
gut funktionierenden Zwischenstand zu sichern. Das ist eine Nutzerabnahme der
ausgeführten Versuche, keine Behauptung der vollständigen Schutz-/Feldmatrix.

Die von Brian mitgeteilte Diagnose zum Input vom 19.10.2026 um 08:30:28 MESZ
(06:30:28 UTC) passt zur lokalen begrenzten Statusdatei der Kandidatensitzung:
capture_native=native_target_captured, capture_field=target_captured,
delivery=submitted, state=IDLE, error_code=null, pending_cleanup=false,
STT bereit auf CUDA. Die tatsächlich sichtbare Übernahme bestätigt Brian
zusätzlich. Die frühere Codex-Fehlerursache wird daraus nicht nachträglich
abgeleitet; es gab keinen separat nachgewiesenen Codex-Sourcefix.

Beim Sichern wird später ein einzelner neuer Status um 08:35:28 MESZ beobachtet:
audio_failed bei weiter bestehendem delivery=submitted, IDLE und ohne offenes
Cleanup. Die Audioaktion ist nicht zugeordnet. Brian meldet dazu ausdrücklich
keinen wahrgenommenen Audiofehler. Dieser technische Hinweis bleibt getrennt
von seiner positiven Diktatabnahme offen; ohne Reproduktion keine Ursachenbehauptung.

Die laufende Sitzung und ihr Source bleiben erhalten. Der Savepoint ändert
keinen Produktcode. Der gewünschte dritte Bestätigungston ist als
[nächste Änderung](../specs/2026-10-19-dictation-completion-cue/spec.md)
festgehalten und gehört noch nicht zu diesem abgenommenen Zwei-Ton-Kandidaten.
