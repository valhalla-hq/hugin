# Dritter Diktatton: Nachweise vom 19.10.2026

## Verhalten und Zuständigkeit

Der Controller akzeptiert den erfolgreichen DeliveryFinished-Abschluss des
aktuellen Diktatjobs genau einmal. Der bestehende Deliveryvertrag umfasst
Textübergabe und Clipboardabschluss. Erkennung allein, fehlgeschlagene/geblockte
Übergabe, Abbruch und manuelles RAM-Kopieren lösen keinen Erfolgston aus.
Duplikate und verspätete Abschlüsse besitzen keinen passenden aktuellen Job.

DictationCues hält drei eigene lokale PCM-Signale. Start-/Endbytes sind erhalten;
der dritte Ton steigt über 660/880/1320Hz an und dauert einschließlich zweier
Pausen 180ms: 8640Bytes, mono PCM16/24kHz. Vorhandene Amplituden-/Fadegrenzen,
native Deadline, Reset und fehlgeschlossene Cleanup-Zuständigkeit bleiben erhalten.

Ein Completion-Owner hält Job, Token und Escape-Reservierung über den
Domainabschluss hinaus. Er entsteht vor den Finish-Effekten; Playback wird erst
danach eingereiht. Das verhindert Tonstart bei gescheiterter Tastenregistrierung
auch mit sofortigem Executor. Nur die passende Completionbestätigung auf dem
Controllerthread löst die Reservierung; ein Folgejob behält sein Escape.
Neue Sprachaktion, Cancel, Quit und Systemwechsel invalidieren das Token und
erreichen den Cue-Reset direkt. Die serielle Capture-FIFO schließt den alten Ton
vor der nächsten Mikrofonöffnung. Ungeklärter Audio-Cleanup blockiert die Aufnahme.
Ein Cuefehler erhält fertigen Text und RAM-Ergebnis und löst keinen neuen Paste aus.

## Automatisierte Prüfung

- 431 Contract-/Integrationstests in 18,216s, ohne Skips, mit Python3.12.10:
  `tools/dev.py check --group all`. Davon 13 neue Completionprüfungen.
- Grenzen: erfolgreiche Übergabe/Reihenfolge, capture-/delivery-/restore-Fehler,
  Cancel am Commit, manuelles Kopieren, Duplikate, wartender/laufender Cue,
  Folgeaufnahme, Quit, Dispatchrace, enqueue-then-throw, Escape über die reale
  WindowsInputs-Implementierung mit Fake-Backend, alter Finish nach neuem Job,
  direkter Domain-Cancel und Registrierungsfehler mit sofortigem Executor.
- Gemeinsame Waveformprüfung: drei verschiedene kurze Signale, Fadegrenzen,
  begrenzte Amplitude und nativer Outputvertrag. Bestehende Audio-/Clipboard-/
  Worker-/Shutdownregressionen bleiben enthalten.
- Zwei getrennte lesende Spec-/Standardsreviews ohne offene Befunde am
  application.py-SHA256 D13BDA482F941FED77FDDCBF9E39ABE3BCA25CD385670128C4F70D94EEF2FF71.
  Gefundene Escape-Lücken an der Ownergrenze korrigiert und erst rot, dann grün
  reproduziert: Reservierung länger halten, Audiostart bis nach ihr verschieben.
- Dokumentprüfung validiert den bestehenden V1-Katalog und README-Links;
  sie ersetzt keine semantische Abnahme dieses Features. Hostedchecks separat
  am tatsächlichen Remotehead prüfen.

## Native Audioprobe und Kosten

Ein eigenes Kind in gehaltenem OwnedProcess-Job spielte ausschließlich den
neuen Cue zweimal ab; keine Tastatur, Clipboard, Aufnahme, GPU oder Appstarts.
Aufruf mit lokalem Controllerinterpreter und isoliertem Pythonmodus; Familie
auf 256MiB begrenzt und Abschluss beobachtet. Native Ausgabe erfolgreich,
Owner geschlossen und cleanup_pending=false. Zusätzlich bestand der vorhandene
native Zero-PCM-Reset-/Backpressuretest in 0,281s ohne Mikrofon.

| Messung | Ergebnis |
| --- | --- |
| Erster Cueaufruf, Prozess/Output zuvor frisch | 0,324017s |
| Zweiter Aufruf im selben Prozess | 0,206899s |
| Gesamte Zweiaufrufprobe samt Kindstart/-abschluss | 0,648515s |
| CPU der eigenen Prozessfamilie | 0,109375s |
| Peak Job Commit der Familie | 14.274.560Bytes |

Erster Aufruf ist keine behauptete kalte Windows-Geräte-/Treiberbasis. Job Commit
ist zugesicherter virtueller Speicher, kein gemessener physischer Peak-RAM-Wert.
Physischer Prozessfamilien-Peak, Agenttokens und kompletter Diktat-Durchlauf
sind nicht gemessen. Vorher existierte diese Bestätigung nicht; es gibt keinen
äquivalenten Vorher-Nachher-Zeitvergleich. Der Controller wartet nicht auf den
Ton, die Capture-FIFO erhält zusätzliche begrenzte Audiowork; bei Folgeaufnahme
wird sie abgebrochen und vor der Mikrofonöffnung abgeschlossen.

Das separate WAV-Hörbeispiel und lokale Probehelfer/-logs liegen ausschließlich
ignoriert in .runtime. Der native Erfolg beweist weder subjektive Hörbarkeit/
Unterscheidbarkeit noch das Timing eines neuen echten Diktats. Diese menschliche
Hör-/Diktatabnahme steht aus. Die laufende Zweitonversion blieb unverändert.
