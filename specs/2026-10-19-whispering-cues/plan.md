# Umsetzung der Originalklänge

Die MP3s aus dem fixierten Upstreamtag werden lokal beschafft, gegen die
beobachteten Gitblobs und SHA256 geprüft und mit dem vorhandenen av16.1.0 in
PCM16/mono/24kHz dekodiert. Keine neue Installation. Originale und PCM bleiben
unter ignoriertem .runtime; die Quellcodegrenze besitzt feste Größe und Digest
der drei erwarteten PCM-Dateien. Ein kleines explizites Vorbereitungstool
validiert lokale Quelldateien und schreibt fehlende eigene Runtimeassets nur
additiv. Abweichende vorhandene Dateien nicht überschreiben.

Die Vorbereitung verwendet den vorhandenen copy_locked-Produzenten mit
vollständiger Stagingvalidierung und atomarer additiver Veröffentlichung per
Hardlink. Fehlgeschlagene Kopie veröffentlicht keine partielle Zieldatei.
DictationCues erhält die vom Loader geprüften Bytes explizit. Der bisherige
Synthesizer und seine Klangtests entfallen; Output-, Abbruch-, Cleanup- und
Controllertests bleiben. Loader-/Datengrenzen mit eigenen synthetischen
Fixtures prüfen, echte Assets separat nativ. Deadline pro Ton aus PCM-Dauer
plus Gerätereserve. Der Cueguard konsumiert die vom Audioowner benannte
65536Bytes-Einzelschreibgrenze; keine größere Cuegröße versprechen. Die
Application liefert nur den vorhandenen Runtimeroot.

Getrennte Reviews, Checks, Remotecheckpoint und exakter Pilotplan vor neuem
Appstart. Aktueller PR13-Pilot am funktionalen Head288c835 bleibt bis zum
normalen Wechsel unberührt. Fremdaudio wird weder in Git noch in ein Release
übernommen; ungeklärte Weiterverbreitungsrechte nicht als geklärt darstellen.
