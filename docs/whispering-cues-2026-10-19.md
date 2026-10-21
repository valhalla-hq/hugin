# Originalklänge aus Whispering7.11.0

Brian ersetzt ausdrücklich die synthetischen Klangvarianten durch dieselben
Originaldateien wie Whispering. Installierte whispering.exe meldet7.11.0.
Fixierte [Upstream-Zuordnung](https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src/lib/services/isomorphic/sound/assets/index.ts):

| Hugin | Whispering | Originaldatei | PCM-Dauer |
| --- | --- | --- | --- |
| Start | manual-start | zapsplat_household_alarm_clock_button_press_12967.mp3 | 0,339833s |
| Aufnahmeende | manual-stop | sound_ex_machina_Button_Blip.mp3 | 0,500000s |
| Eingefügt | transcriptionComplete | zapsplat_multimedia_ui_notification_classic_bell_synth_success_107505.mp3 | 1,346208s |

MP3-SHA256 in tools/prepare_cues.py; Gitblobs gegen den fixierten Tag abgeglichen.
Die Dateirollen start.mp3/end.mp3/complete.mp3 sind lokale Dateinamen dieser
unveränderten Originale. Vor jeder Dekodierung wird die vollständige Quelle
begrenzt gelesen und geprüft. Der vorhandene av16.1.0 resampelt in PCM16/mono/
24kHz für Hugins bestehenden Player. Keine Lautheitsnormalisierung, zusätzliche
Wiederholung oder Kürzung. Quellenbytes und abgeleitete PCM-Digests bleiben getrennt.

## Lokale Vorbereitung und Dateigrenze

Quell-MP3s und PCM bleiben außerhalb Git. Originale liegen im Taskworktree
unter .runtime/whispering-originals. Endziel ist der vorhandene Runtimeroot
C:/Users/brian/Hugin/.runtime/cues/whispering-v7.11.0. Für geprüfte lokale Quellen:

```powershell
& C:/Users/brian/Hugin/.runtime/stt/Scripts/python.exe -I tools/prepare_cues.py --root C:/Users/brian/Hugin --source .runtime/whispering-originals
# Derselbe explizite Aufruf mit --apply führt den angezeigten Plan aus.
```

Plan, erste additive Vorbereitung und Wiederholung mit ausschließlich present
ausgeführt. Kein Netzwerk oder Decoder im Controllerlauf. Vorhandene abweichende
Dateien werden erhalten und gemeldet. Vorbereitung nutzt copy_locked mit
validiertem Staging, temporärer Kopie und atomarer additiver Veröffentlichung.
Schreibabbruch veröffentlicht kein finales Teilasset. Runtime-Loader prüft die
festen PCM-Größen16312/24000/64618 und SHA256 einmal vor Anlage nativer Besitzer.
Keine synthetische Rückfallwiedergabe bei fehlenden/veränderten Daten.

Urheberhinweise: ZapSplat und Sound Ex Machina, im lokalen NOTICE erhalten.
Der Upstream nennt AGPL-3.0 für das Repository und ZapSplat für Effekte. Die
[separaten ZapSplat-Bedingungen](https://www.zapsplat.com/license-type/standard-license/)
geben keine pauschale Erlaubnis zum Weiterverteilen eigenständiger Audiodateien.
Diese private lokale Vorbereitung behauptet keine geklärten Veröffentlichungs-
oder Weiterverbreitungsrechte; keine Fremdaudiodatei in Git oder Release aufgenommen.

## Player und Verifikation

Der Player übernimmt verifizierte Bytes unverändert. Cueguard und PCMOutput
konsumieren dieselbe65536Bytes-Grenze je Schreibaufruf. Deadline pro Signal:
PCM-Dauer plus500ms Gerätereserve; längste Datei passt vollständig. Escape,
direkter Reset, Capture-FIFO, Cleanup und Delivery-Trigger bleiben erhalten.
Native eigene Outputprobe: Start0,408742s, Ende0,527309s, Abschluss1,379000s;
alle vollständig, Owner geschlossen, kein Cleanup offen. Eigene Familie:
CPU0,171875s, Peak Job Commit14.233.600Bytes; gesamte Probe4,368345s einschließlich
650ms Pausen, Kindstart und Abschluss. Physischer Peak-RAM, Agenttokens,
kalte Treiberbasis und kompletter Diktatworkflow nicht gemessen. Kein äquivalenter
nativer Vorhervergleich; Originale sind bewusst länger als die Synthese.

438 Source-/Integrationstests in19,461s sowie zusätzlicher isolierter CLI-Guard
grün; finalen Hostedlauf einschließlich des CLI-Guards frisch prüfen. Zwei
getrennte Reviews ohne offene Befunde nach Korrektur von finalen Teilkopien und
abweichender Cue-/Outputgrenze. Bedeutungslose Synthesizer-/Pitchtests entfernt;
Assetidentität, Bounds, unveränderte Byteübergabe, lange Wiedergabe, Startupfehler,
Abbruch/Cleanup und Setupfehler durch passende Grenzenprüfungen ersetzt.

Der erste Versuch der Outputprobe wurde wegen STOPPING des vorherigen Piloten
gar nicht abgespielt. Dessen eigene Familie ist inzwischen regulär beendet,
Rückkehr ausgelöst und keine passende App mehr beobachtet. Danach obige Probe
ausgeführt. Beobachtetes audio_failed im früheren Doppeltonepilot bei submitted
und ohne offenes Cleanup bleibt unzugeordnet; nicht als Ursache rekonstruiert.
Neue menschliche App-Abnahme der Originaldateien steht aus.
