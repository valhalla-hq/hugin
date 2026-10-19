# Klangkontrast nach Brians Test

Brian wünscht nach dem ersten Dreitonstand viel mehr Unterscheidung:
dumpfer Beginn, mittleres Aufnahmeende, helles Fertigklingeln beim Einfügen.
Diese Präzisierung ersetzt die frühere Erhaltung der Start-/Endtonbytes.
Auslösezeitpunkte, Deliveryvertrag, Escape, Capture-FIFO und Cleanup bleiben
identisch zum geprüften PR12-Stand380c4ec; application.py ist unverändert.

## Klangdesign und Referenz

Whispering v7.11.0 ordnet Manual-Start und Manual-Stop unterschiedlichen
Audiodateien und transcriptionComplete einem Bell-Synth-Success-Sample zu.
Quelle ist die [fixierte Upstream-Zuordnung](https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src/lib/services/isomorphic/sound/assets/index.ts).
Das bestätigt Ereignistrennung und Glockenreferenz; die Audiodateien wurden
nicht heruntergeladen, angehört oder übernommen. Keine Aussage über die
genauen akustischen Eigenschaften oder Brians installierte Whispering-Version.

Hugin synthetisiert eigene PCM-Signale in demselben begrenzten Audiopfad:

| Ereignis | Klang | PCM-Dauer |
| --- | --- | --- |
| Aufnahme beginnt | Weicher tiefer Sinusimpuls,196Hz, schneller Abfall | 120ms |
| Aufnahme endet | Schlichter mittlerer Sinuston,660Hz | 100ms |
| Text eingefügt | Helle Glocke,1568Hz und unharmonische Teiltöne, ausklingend | 280ms |

Die positiven Teiltongewichte summieren sich zu eins; Frequenzen bleiben unter
Nyquist. Fade an beiden Rändern und bestehende Amplitudengrenze bleiben erhalten.
Neue PCM-Größen:5760/4800/13440Bytes, gesamt24000Bytes gegenüber22800 zuvor.
Der Glockenklang ist100ms länger als der erste Abschlussentwurf; die vollständige
Summe aller drei Signale steigt um25ms. Die bestehende500ms-Deadline bleibt gleich.

## Verifikation

- Bestehenden Waveformguard vor Umsetzung erweitert, zunächst am alten
  Klangstand rot. Er prüft breite getrennte Tonlagen per Nulldurchgängen,
  begrenzte Dauer/Amplitude und ausklingende Energie des Abschlusses. Das
  prüft technische Kontraste, keine subjektive Klangqualität.
- 35 gezielte Capture-/Completiontests in0,231s und alle431 Source-/Integrations-
  tests in20,417s ohne Skips grün. Keine neuen Tests, kein Controllerumbau.
- Separate Spec-/Standardsreviews ohne Befund an cues.py-SHA256
  F6F9BE47DD343C888D6CC307C5903A821E28078ED9BF134CC963B9BFAE2649E1.
- Eigene native Outputprobe: alle drei Signale je zweimal vollständig
  abgespielt, Owner geschlossen, pending_cleanup=false. Keine Aufnahme,
  Eingabebindung, Clipboardaktion, GPU oder App-/Workerbeendigung.

| Nativer Aufruf | Erste Runde | Zweite Runde im selben Prozess |
| --- | --- | --- |
| Start | 0,315555s | 0,149994s |
| Aufnahmeende | 0,142699s | 0,129303s |
| Glockenabschluss | 0,319046s | 0,312898s |

Gesamtprobe einschließlich eigenem Kindstart und Abschluss:1,483620s;
Prozessfamilien-CPU0,156250s, Peak Job Commit15.618.048Bytes. Alle gemessenen
Aufrufe liegen unter der unveränderten Deadline. Das ist keine Worst-Case-
Garantie oder kalte Treiberbasis. Physischer Peak-RAM, Agenttokens und kompletter
Diktatworkflow nicht gemessen; kein äquivalenter nativer Vorhervergleich ausgeführt.

Die vergleichende WAV-Folge enthält nur die drei eigenen Signale mit650ms Pause.
Sie, Einzel-WAVs und Probehelfer liegen ignoriert unter .runtime. Brians Urteil
zur wahrgenommenen Dumpfheit, Tonhöhe und Glockenwirkung sowie ein echter Diktat-
test in einer neuen Sitzung sind noch offen. Die laufende PR12-Sitzung bleibt
unverändert; ihre neue native Diagnose meldete erfolgreiche Textübergabe ohne Fehler.
