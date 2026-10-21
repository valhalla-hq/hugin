# Diktieren und Vorlesen per Button

Hugin bietet beide Aktionen zusätzlich zu den vorhandenen Tastenkürzeln an.
Das Hugin-Fenster muss dafür neben dem gewünschten Textfeld sichtbar sein.

## Diktieren

1. Im Panel Diktieren auf **Diktat starten** klicken.
2. Während der Aufnahme in das gewünschte Eingabefeld klicken.
3. Direkt auf **Fertig & einfügen** klicken und bis zum Einfügen im Zielfeld bleiben.

Der Button übernimmt beim Klicken nicht den Fokus. Der Schreibcursor bleibt im
Zielfeld. Statt des Buttons kann weiterhin Strg+Alt+D benutzt werden; Button und
Tastatur lassen sich innerhalb einer Aufnahme kombinieren. Während das Mikrofon
öffnet, steht **Abbrechen** bereit. Bei der Verarbeitung ist der Button gesperrt.

## Vorlesen

Text in der anderen Anwendung markieren und direkt auf **Vorlesen starten**
klicken. **Stopp** ist schon während der Vorbereitung verfügbar; nach Beginn des
ersten Abschnitts kommt **Pause/Fortsetzen** hinzu. Die Mitleseleiste lässt sich
weiterhin separat ein- und ausblenden.

Ein vorheriger Klick auf Hugins Titel oder Hintergrund aktiviert Hugin normal.
In diesem Fall beim Diktat wieder ins Zielfeld klicken beziehungsweise den Text
erneut markieren und dann direkt den Aktionsbutton wählen. Hugin zeigt dafür
einen Hinweis; es aktiviert kein früheres Fenster aus einer gespeicherten Liste.

## Technische Prüfung und Grenzen

Der Controller bindet Buttonaktionen an Generation und Zustand. Mausaktionen
werden schon beim Drücken gebunden. Bereits akzeptierte Abbrüche gelten für ihren
konkreten Auftrag auch bei einem Wechsel von Vorbereitung zu Wiedergabe.
Wiederholte oder verspätete Klicks können keine spätere Aufnahme stoppen. Die vorhandenen
Feldprüfungen, Zwischenablagesicherung und Einfügefreigabe bleiben unverändert.

Die native Windows-Anbindung verarbeitet
[WM_MOUSEACTIVATE](https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-mouseactivate)
an den beiden eigenen Aktionsbuttons mit MA_NOACTIVATE. Die Registrierung folgt
[SetWindowSubclass](https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass)
und wird auf demselben UI-Thread wieder entfernt. Fehlgeschlagene Freigaben
behalten ihren Besitzer bis zum erneuten Schließversuch.

477 Contract-/Integrationstests und 26 native Darstellungs-/Fenstertests bestanden.
Die native Probe verwendet eigene synthetische Fenster, die tatsächliche
Aktivierungsnachricht und Tk-Klickbindungen; sie prüft erhaltenen Fokus und
Textauswahl. Die GUI-Vorschau bestätigt normale und aktive Karten. Kein echter
Text, keine Aufnahme und keine Sprachmodelle wurden dafür verwendet; ein bereits
vorhandener Audiotest spielt nur stille PCM-Daten.

Ein erster direkter Hintergrund-Testlauf konnte seine eigenen Fenster unter
Windows nicht aktivieren. Der vollständige native Wiederholungslauf wurde über
einen normalen Klick in einem eigenen Testfenster gestartet und bestand.
Die echte Buttonprobe in Codex und Word nach dem Pilotwechsel bleibt gesonderte
Nutzerabnahme; diese Prüfung ersetzt sie nicht.
