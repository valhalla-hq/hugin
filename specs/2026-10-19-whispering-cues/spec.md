# Originalklänge aus Whispering

Brian beauftragt ausdrücklich die drei Originaldateien statt der bisherigen
synthetischen Varianten. Installierte Whispering-Version7.11.0 und öffentlicher
Upstreamtagv7.11.0 stimmen überein. Bestehender Doppeltontest bleibt erhalten.

- WC-001: Manual-Start, Manual-Stop und transcriptionComplete aus fixiertem
  Whisperingtag a6b15c28db9076742d7ae7014f8ec9f97aa615d1 verwenden. Keine neuen
  Tonfolgen, Verdopplung, Kürzung oder Lautheitsnormalisierung; notwendige
  Dekodierung in das vorhandene PCM16/mono/24kHz-Ausgabeformat offenlegen.
- WC-002: Originaldateien, Zuordnung, Digests und Decodierrezept festhalten.
  Fremdaudio bleibt lokal außerhalb Git; Quellen-/Rechtehinweise erhalten.
  Kein Download und kein Decoder im normalen Controllerlauf.
- WC-003: Genau dieselben Auslöse-, Escape-, Abbruch-, Capture-FIFO- und
  Cleanupverträge wie PR12/13. Die alte500ms-Grenze muss der längsten Datei
  von1,346s Platz geben; neue Grenze ergibt sich aus tatsächlicher PCM-Dauer
  plus500ms Gerätereserve; maximal65536Bytes je Cue gemäß dem bestehenden
  PCMOutput-Einzelschreibvertrag. Fehlende/veränderte Assets melden
  Fehler statt unbemerkt wieder synthetische Töne zu verwenden.
- WC-004: Laufenden Source und Helfer nicht ändern. Separate geprüfte
  Pilotsitzung mit unveränderten Stimmen, Kürzeln und Altstack-Rückweg.
  Keine produktive Maus-/Alt+Y-/Autostartmigration.

Abnahme: nachweisbare Originalzuordnung; echte lokale Assets vollständig ohne
Abschneiden wiedergeben; geänderte/fehlende/übergroße Daten ablehnen; längeren
Ton abbrechen und vor Folgeaufnahme schließen. Hörprobe bereits bereitgestellt;
anschließenden Appwechsel und Nutzertest getrennt dokumentieren.
