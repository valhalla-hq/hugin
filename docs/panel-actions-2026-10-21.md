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
Für automatisches Einfügen wieder ins Zielfeld klicken beziehungsweise den Text
zum Vorlesen erneut markieren und dann direkt den Aktionsbutton wählen. Der
Diktat-Button beendet die Aufnahme auch ohne gültiges Zielfeld: Der fertige Text
bleibt dann in Hugin zum Kopieren erhalten. Nur beim Start des Vorlesens zeigt
Hugin den Auswahlhinweis. Es aktiviert kein früheres Fenster aus einer Liste.

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

## Korrektur nach der ersten Buttonprobe

Brian meldete eine nicht stoppbare Aufnahme. Der Diktat-Button hatte bei Hugin
im Vordergrund keinen Befehl weitergegeben; ein nativer Regressionstest zeigte
dies vor der Korrektur rot und danach grün. Die Zielprüfung darf nur die Übergabe
blockieren, nicht das Ende der Aufnahme. Der Controller bewahrt den Text bei
fehlendem Ziel unverändert im RAM auf; dies ist zusätzlich geprüft.

Strg+Alt+D und Escape funktionierten im separaten synthetischen Hugin-Fenster
über Windows-Tastatureingaben. Auch native WM_HOTKEY-Nachrichten durchlaufen
die echte Eingabeschleife bis zum Controller erfolgreich. Kein Mikrofon,
Sprachmodell oder privater Zwischenablageinhalt wurde dabei benutzt. Warum die
physischen Tasten im gemeldeten Versuch nicht ankamen, bleibt ungeklärt.
Die bestehende Aktivierungsbehandlung wurde nicht spekulativ verändert; Tk's
[nativer Button-Handler](https://github.com/tcltk/tk/blob/core-8-6-branch/win/tkWinButton.c)
und die vorhandenen nativen Fokusprüfungen wurden als Gegenprüfung herangezogen.
