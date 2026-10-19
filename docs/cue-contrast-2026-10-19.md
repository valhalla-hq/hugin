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
| Aufnahme beginnt | Zwei weiche tiefe Sinusimpulse,196Hz,45ms Pause | 185ms |
| Aufnahme endet | Zwei schlichte mittlere Sinustöne,660Hz,45ms Pause | 165ms |
| Text eingefügt | Zwei helle Glockenanschläge,1568/2093Hz und unharmonische Teiltöne,35ms Pause | 295ms |

Die positiven Teiltongewichte summieren sich zu eins; Frequenzen bleiben unter
Nyquist, maximal8518,51Hz. Fade an beiden Rändern bleibt erhalten. Nach der
ersten Hörfolge wünschte Brian alle drei Töne stärker und dann Doppelanschläge.
Digitale Amplitude7500 auf15000 verdoppelt; Peaks12790/13841/12541 bleiben unter
Guard16000 und halber PCM16-Vollaussteuerung. Das entspricht ungefähr6dB mehr
Signalpegel, keiner behaupteten Verdopplung wahrgenommener Lautstärke.
Neue PCM-Größen:8880/7920/14160Bytes, gesamt30960Bytes gegenüber22800 zuvor.
Die Summe der Signaldauern steigt gegenüber PR12 um170ms. Die bestehende500ms-
Deadline bleibt gleich. Brian akzeptiert diese gehörte Doppelfolge und beauftragt
Einbau und anschließenden Test in der App; die App-Abnahme ist separat offen.

## Verifikation

- Bestehenden Waveformguard vor Umsetzung erweitert, zunächst am alten
  Klangstand rot. Er prüft breite getrennte Tonlagen per Nulldurchgängen,
  begrenzte Dauer/Amplitude und ausklingende Energie des Abschlusses. Das
  prüft technische Kontraste, keine subjektive Klangqualität.
- 35 gezielte Capture-/Completiontests in0,223s und alle431 Source-/Integrations-
  tests in19,036s ohne Skips grün. Keine neuen Tests, kein Controllerumbau.
- Separate Spec-/Standardsreviews ohne Befund an cues.py-SHA256
  85BE897075323962847EBF416F177C12ECC13E63D3A0E430FBBA20033629EB4F.
- Eigene native Outputprobe: die gewählte kräftige Doppelfolge vollständig
  abgespielt, Owner geschlossen, pending_cleanup=false. Keine Aufnahme,
  Eingabebindung, Clipboardaktion, GPU oder App-/Workerbeendigung.

| Nativer Aufruf der Doppelfolge | Dauer |
| --- | --- |
| Start, erster Output im Prozess | 0,269682s |
| Aufnahmeende | 0,201039s |
| Glockenabschluss | 0,333774s |

Gesamtprobe einschließlich eigenem Kindstart,650ms Pausen und Abschluss:2,898882s;
Prozessfamilien-CPU0,171875s, Peak Job Commit15.896.576Bytes. Alle gemessenen
Aufrufe liegen unter der unveränderten Deadline. Das ist keine Worst-Case-
Garantie oder kalte Treiberbasis. Physischer Peak-RAM, Agenttokens und kompletter
Diktatworkflow nicht gemessen; kein äquivalenter nativer Vorhervergleich ausgeführt.

Die vergleichende WAV-Folge enthält nur die drei eigenen Signale mit650ms Pause.
Sie, Einzel-WAVs und Probehelfer liegen ignoriert unter .runtime. Brian hat die
kräftige Doppelfolge akzeptiert. Ein echter Diktattest in einer neuen Sitzung
steht noch aus; den geordneten Testwechsel hat er ausdrücklich beauftragt.
Die PR12-Sitzung bleibt bis dahin unverändert; ihre native Diagnose meldete
erfolgreiche Textübergabe ohne Fehler.
