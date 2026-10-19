# Dritter Diktatton: Umsetzung

## Ansatz

Der Controller konsumiert den bereits normalisierten erfolgreichen
DeliveryFinished-Abschluss genau einmal. Erst nachdem der Coordinator den
aktuellen Job abgeschlossen hat, startet der Bestätigungston auf dem vorhandenen
seriellen Capture-Executor. Die Oberfläche kann schon Bereit melden; der
Controllerowner wartet nicht auf Audio. Keine zweite Delivery und keine neuen
Provider-, Clipboard- oder Engineverträge.

Ein explizit gehaltener Completion-Cue-Owner (Job plus Abbruchtoken) reserviert
Escape vor den Finish-Effekten. Erst nach deren erfolgreicher Eingabereservierung
wird Audio eingereiht; auch ein sofort ausführender Executor kann bei einem
Registrierungsfehler keinen Ton starten. Die Freigabe erfolgt durch eine passende
Completion-Bestätigung auf dem Controllerthread und respektiert einen Folgejob.
Der Owner bleibt bis zu dieser Bestätigung erhalten. Neue Sprachaktion, Abbruch, Quit und
Systemwechsel setzen dieses Token und erreichen den existierenden Cue-Reset
direkt, auch wenn die Wiedergabe noch in der FIFO wartet. Die nachfolgende
Mikrofonöffnung steht in derselben FIFO; Cleanup und der vorhandene unarmed-
Startton-Gate liegen vor der Aufnahmefreigabe. Fehlgeschlossener Cleanup bleibt
im bestehenden Cue-Owner und blockiert eine weitere Aufnahme.

## Betroffene Grenzen

Präzisierung nach dem Test am 19.10.: Nur die PCM-Erzeugung in cues.py ändern;
Controller, Cueowner und Auslösezeitpunkte bleiben identisch. Ein gemeinsamer
begrenzter Sinus-/Partialgenerator mit abklingender Hüllkurve erzeugt einen tiefen
weichen Impuls, einen einfachen mittleren Ton und einen hellen Glockenklang mit
unharmonischen Teiltönen. Kein Sample, Audiopaket oder neuer Player. Maximal
300ms PCM bleibt mit Reserve unter der bestehenden 500ms-Cue-Deadline; tatsächliche
native Ausgabe prüfen. Einen gemeinsamen WAV-Ablauf mit Pausen zum Vergleichen
bereitstellen. Die zuletzt gestartete PR12-Sitzung bleibt im bisherigen Worktree.

- src/hugin/application.py: akzeptierter Deliveryabschluss, Completionbesitz
  und direkte Unterbrechung; vorhandene Capture-Task-/Shutdownverfolgung nutzen.
- src/hugin/cues.py: dritter kurzer eigener PCM-Ton, gemeinsamer Besitzer nun
  DictationCues. Die neu beauftragten Klangfarben ersetzen Start-/Endbytes; Grenzen bleiben erhalten;
  alle bisherigen Klassennamenverbraucher konsistent umstellen, kein Alias.
- Tests: Controllerablauf mit simuliertem Clipboard/Worker und kontrollierten
  Executoren; bestehende Cue-/Audio-/Cleanupregressionen. Diese Proben ersetzen
  keine echte Mikrofon-/Hörabnahme.

## Risiken und Prüfung

Erkennung allein ist kein Einfügeerfolg. Deshalb wird nur der tatsächlich
akzeptierte erfolgreiche Jobabschluss verwendet. Doppelte/späte Ereignisse
haben keinen aktuellen Job mehr. Eine nach erfolgreichem Paste eingehende
Abbruchaktion darf den Text erhalten und lediglich den Ton stoppen. Audiofehler
gehen über die vorhandene begrenzte Cue-Diagnose, ohne Ergebnisverlust.

Die frühere Beobachtung audio_failed ohne hörbares Symptom ist nicht als
Ursache reproduziert und wird nicht spekulativ geändert. Eigene neue Guards
stellen sicher, dass ein zusätzlicher Cuefehler keine neue Delivery auslöst.

## Auslieferung

Source-/Integrations-/Docschecks, getrennte Spec-/Standardsreviews und private
Draft-PR auf Basis des gesicherten PR11-Branches. Die laufende alte Sitzung und
ihr Sourcepfad bleiben unberührt. Neues kurzes WAV-Hörbeispiel ist ignorierter
Output. Neuer Pilotstart und menschliche Hör-/Diktatabnahme bleiben explizit
vom Sourcecheck getrennt; kein Maus-/Alt+Y-/Autostartrollout.
