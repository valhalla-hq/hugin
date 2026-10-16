# Einfügekorrektur: Kandidat vom 16.10.2026

## Bewiesene Fehler und Grenzen

Brian bestätigt die beiden Stimmen Freya/Tyr und die deutlicheren Aufnahme-
Töne. Offen sind Teilersetzung in Chrome/Google und gelegentlich abgelehnte
Feldprüfungen. Diese Änderung bearbeitet die Einfügefunktion; Audio und
Produktumfang bleiben beim bestätigten Stand.

Eine hardwarefreie Adapterprobe reproduziert eine falsche Ablehnung eines
unveränderten Bereichs7..18:80ms Prozessabwicklung nach erfolgreicher
Feldprüfung überschreiten die bisherige50ms-Schlussfrist; Ergebnis
target_probe_timeout statt Pastefreigabe. Das belegt einen Deadlinefehler,
nicht die Ursache jedes vom Nutzer beobachteten Chrome-Falls.

Weitere zuerst rote Guards belegen verworfene Capture-Statuswerte und eine
Zielprüfungs-Ausnahme, die gültige Aufnahmebytes an der Transkription hindert.
Ein Provider mit SupportedTextSelection=Multiple wurde auch bei genau einem
aktuellen Bereich verworfen. Die Fähigkeit beschreibt unterstützte Auswahl,
nicht deren aktuelle Anzahl. [Microsoft-Enum](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationcore/ne-uiautomationcore-supportedtextselection)

## Strukturelle Korrektur

- Der isolierte Produzent setzt nach seiner letzten Fokus-/Rangeprüfung einen
  monotonen Prüfzeitpunkt. Request5 und Response4 ersetzen die alten privaten
  Shapes vollständig; fehlende, boolesche, nicht endliche oder zusätzliche
  Metadaten werden abgelehnt.
- Der Deliveryworker bereitet genau eine Bestätigung samt vollständigem Frame,
  stdout-EOF, leerem stderr-EOF und geschlossenem Writer vor. Der Controller-
  Commit konsumiert nur parsed facts ohne COM, Pipe-Lesen, Join oder Prozesswait.
  Er lehnt zukünftige und über50ms alte Nachweise ab. Native Zielidentität,
  Clipboard-Token/Sequence, Nutzer-Modifier, Cancel und Jobgeneration werden
  unmittelbar vor Übergabe weiterhin geprüft. Keine Fristverlängerung.
- Der Produzent schließt seine privaten stdout-/stderr-Deskriptoren vor COM-
  und Interpreterabwicklung. Die eigene echte Windows-Fixture war zuerst rot:
  venv-Redirector und closefd=False der Standardstreamwrapper hielten EOF bis
  zum Prozessende zurück. Derselbe Basisinterpreter startet nun direkt mit
  CPythons __PYVENV_LAUNCHER__ und exakt erhaltenem venv. Der Launcher prüft
  dessen Lage im Basisruntime; die Fixture prüft das aufgelöste sys.prefix.
  Geerbte Umgebung bleibt nur im Speicher, Installation und OS unverändert.
  [CPython3.12.10 getpath.py](https://raw.githubusercontent.com/python/cpython/v3.12.10/Modules/getpath.py)
- Der Probeowner hält Familie, Pipes und Threads bis zum bestätigten Abschluss.
  Fehler beim Schließen behalten Ressourcen für Retry. Ein später bekannter
  Fehlerexit bleibt gemeldet, auch wenn der Paste bereits übergeben wurde;
  vollständig geschlossene tote Owner bleiben nicht dauerhaft blockiert.
  Der native Clipboardlock endet vor langsamem Unwind; das Zielfeld kann
  die übergebene Einfügeanforderung währenddessen lesen. Callbackdetachment
  und OneShotGate enden vor der Freigabe, submitted bleibt auch bei Fehlerexit.
- Genau ein aktueller Bereich ist auch bei Mehrfachauswahlfähigkeit zulässig.
  Mehrere tatsächliche Bereiche und alle bisherigen Schutzfeld-/Identitäts-
  /Endpunkt-/Objektprüfungen bleiben ablehnend.
- Der Controller erhält einen normalisierten Capture-Ausgang statt nur target.
  Zielprüfungsfehler verwerfen keine gültigen Aufnahmebytes; STT und letztes
  RAM-Ergebnis bleiben verfügbar. Diagnose ergänzt input_checks mit genau
  capture_native, capture_field und delivery sowie begrenzten Statuswerten.
  Keine Texte, URLs, Titel, UIA-IDs, Clipboardinhalte oder Exception-Payloads.

## Verifikation

| Prüfung | Ergebnis | Grenze |
| --- | --- | --- |
| Source/Integration: tools/dev.py check --group all |404Tests,21,392s, keine Skips| simulierte Hardware/Provider |
| Gezielte Controller/Cue/Lease/Target/Selection/Process-Tests |144Tests,1,205s, keine Skips|1 echte eigene Windows-Prozess-/Pipe-Fixture, synthetisches UIA |
| Bestehender Docscheck |19Anforderungen/17Abnahmekriterien, keine Probleme| prüft v1-Dokumente und Locks; keine native Produktabnahme |
| Eigene native Prozess-Fixture | grün: zeitlich frischer Nachweis, Familie während120ms Abwicklung noch gehalten, später Exit0| kein fremdes Fenster, Clipboard, Mikrofon, Audio oder GPU |
| Hosted-Step lokal in frischer venv ohne pip nachvollzogen |1Test,0,476s, grün| eigens gehaltene synthetische Pipe-/Prozess-Fixture; Hosted-Ergebnis separat prüfen |

Neue Guards decken alte/future/ungültige Zeitwerte, verzögerte Ownerqueue,
Trailingbytes, einmaligen Commit, späteren Fehlerexit, Ressourcenabschluss,
Mehrfachauswahlfähigkeit und tatsächliche Mehrfachauswahl ab. Bestehende
Endpoint-, UserCopy-, Cancel-, Readonly-/Password- und Clipboardrestore-Guards
laufen weiter. Die alte vollständige Windowsmatrix56Tests ist historische
Evidenz aus15.10.; sie wurde am neuen Kandidaten nicht erneut als nativ grün
behauptet. CPU, Peakmemory, GPU, p95 und Agenttokens dieses Deltas sind nicht
gemessen. Aus der Testlaufzeit wird kein Produktlatenzgewinn abgeleitet.

## Review und Folgerungen

Getrennte Spec-/Standards-Pässe am festen Source73f7390 fanden einen
Clipboardlock während des neuen langsamen Prozessunwinds und eine mögliche
Alterung der Attestation während des abschließenden nativen Zielreads.
Beide wurden am tatsächlichen Commit-Seam mit zuerst roten Guards belegt.
Cleanup liegt nun außerhalb OpenClipboard; der einmalige Frischeverbrauch
liegt hinter dem potentiell wartenden nativen Zielread. Malformed-Identity-
Guards verwenden gültige Response4-Envelopes, damit sie die Metadaten statt
nur eine alte Wireversion prüfen. Der echte Windows-Prozessguard wurde als
kleiner isolierter CI-Step ergänzt. Abschließende Reviews folgen am neuen Head.

## Letzte Abnahme und Laufzustand

Computer Use stoppte die Google-Probe automatisch, weil es die aktuelle
Browseradresse auf Windows nicht zuverlässig genug feststellen konnte.
Kein alternativer UIA-/SendInput-/CDP-Weg wurde zur Umgehung verwendet. Die
vorhandene Testseite erhielt keinen Testtext und keine Suche wurde abgesandt.
Echte Google-/Codex-Teil-/Vollauswahl, Cursor, Fokuswechsel und Schutzfelder
bleiben am Kandidaten ungeprüft. Die reale Feldmatrix ist DC-T07.

Die alte Receipt-Datei nennt noch pilot_running; das ist kein aktueller
Laufnachweis. Frisch am16.10. wurden kein Hugin-App-/Supervisorprozess,
aber PipPal samt altem Qwen-Worker beobachtet. Kein fremder Prozess wurde
beendet. Der stabile Main bleibt8e4ceabb718edb2c8d1b80e1b07b69e0f3b933bd;
dieser Kandidat ist nicht ausgerollt. Private Draft-PR10 und aktiver Root-
Worktree halten die Fortsetzung bereit. Normale Maus-/Alt+Y-/Autostart-
Migration folgt erst auf die geprüfte Umstellung.
