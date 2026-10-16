# Hugin: Einfügen bis zur abschließenden Abnahme

## Ziel und Belege

Diktat ersetzt die unveränderte markierte Teil- oder Gesamtauswahl; ohne
Auswahl bleibt Einfügen am Cursor möglich. Die bestehende IA-001/002/005-Spec
gilt weiter. Brian bestätigt die neuen Töne und beide Vorlesestimmen.

Reproduziert ohne Hardware: DeliveryLease lehnt ein unverändertes Intervall
7..18 als target_probe_timeout ab, wenn allein der abgeschlossene Hilfsprozess
80ms für seinen Familienabschluss benötigt. Die 50ms-Schlussfrist enthält
derzeit Feldprüfung, EOF und Prozessabschluss. Dies ist ein bewiesener
Deadline-Fehler; die genaue Ursache jedes gemeldeten Chrome-Falls ist offen.
Zusätzlich verwirft der Controller den Status der Zielaufnahme und reduziert
Probe-Timeouts auf dieselbe Meldung wie ein tatsächlich unbekanntes Feld.
Eine geworfene Zielprüfungs-Ausnahme verhindert zudem die Transkription bereits
gültiger Aufnahmebytes. Alle drei Fehler sind an öffentlichen Adapter- bzw.
Controller-Seams zuerst mit roten Guards belegt.

Die echte eigene Windows-Prozess-Fixture zeigt zwei weitere Grenzen: Der
venv-Redirector hält geerbte Pipehandles bis zum Kindende; alleiniges Schließen
der Python-Standardstreamwrapper publiziert wegen closefd=False kein EOF.
Der Launcher muss deshalb denselben Basisinterpreter mit exakt erhaltenem
venv-Kontext starten, der Produzent seine privaten Deskriptoren schließen.
Dies verändert keine Installation und speichert keine Umgebungswerte.

Der native Chrome-Test wurde vom Computer-Use-Sicherheitscheck wegen nicht
zuverlässig feststellbarer Browseradresse gestoppt. Diese Sperre wird nicht
umgangen. Quellcode, private IPC und eigene synthetische Fixtures sind prüfbar;
die echte Feldmatrix bleibt ein separater letzter Abnahmeschritt.

## Anforderungen

- DC-001: Langsame Feldprüfung und Prozessabwicklung laufen außerhalb des
  Controllerowners. Der letzte Owner-Commit wartet nicht auf COM oder Pipes.
  Er verbraucht genau eine vollständige, höchstens50ms alte Feldattestation.
  Deren monotoner Prüfzeitpunkt stammt vom isolierten Produzenten nach seiner
  letzten Fokus-/Rangeprüfung; ungültige, zukünftige oder alte Zeiten ablehnen.
- DC-002: Beide unveränderlichen UTF-16-Auswahlgrenzen, Feld-/Root-/Prozess-
  Identität, Endaffinität, readonly/password/disabled und Objektfreiheit bleiben
  geprüft. Die Attestation wird vor langsamer COM-/Prozessabwicklung versandt.
  Ein Provider mit Mehrfachauswahlfähigkeit ist bei genau einem aktuellen
  Bereich zulässig; mehrere tatsächliche Bereiche bleiben abgelehnt.
  Private Framing-/EOF-/stderr-Prüfung bleibt vollständig; Prozessbesitz bleibt
  bis bestätigtem Familienabschluss erhalten. Fehler nach Übergabe dürfen
  keinen zweiten Paste und keine falsche Cleanup-Erfolgsmeldung erzeugen.
  Der native Clipboardlock endet vor dem langsamen Familienabschluss, damit
  das Zielfeld die bereits übergebene Einfügeanforderung lesen kann.
- DC-003: Zielaufnahme und Delivery behalten einen begrenzten technischen
  Status samt Phase für Diagnose. Timeout, unzugängliche Abhängigkeit,
  Feldwechsel und nicht prüfbares Feld bleiben unterscheidbar. Keine Texte,
  UIA-IDs, Fenstertitel, URLs, Clipboardformate oder Exception-Payloads darin.
- DC-004: Stimmen, Töne, Mikrofon, GPU, Kürzel, RAM-Ergebnis, Clipboardrestore,
  neue Nutzerkopien und normaler Altstack-Rückweg bleiben erhalten. Kein Enter,
  kein OS-/Browser-Setting, keine Produktionsmigration und keine Zusatz-UI.
- DC-005: Feldzugehörigkeit folgt den geprüften UIA-Enclosures, nicht der
  Reihenfolge eines Endpunkts gegenüber DocumentRange.End. Ein eigener
  Endpunkt darf auch bei derselben sichtbaren Edit-Enclosure dahinter
  sortieren. Beide Endrelationen, Identitäten und begrenzten UTF-16-Präfixe
  bleiben eingefroren und frisch geprüft. Keine zusätzliche Volltextlesung,
  Zeichenwanderung oder App-Ausnahme. Fremde/unklare Enclosures und geänderte
  Auswahl bleiben abgelehnt.

## Abnahme

- DCA-001 (DC-001/002): Verzögerter Familienabschluss80ms blockiert einen
  frischen gültigen Bereich nicht. Abgelaufene/future/ungültige Attestation,
  veränderte Endpunkte oder UserCopy/Cancel ergeben keinen Paste.
- DCA-002 (DC-001/002): Echte eigene Prozess-/Pipe-Fixture belegt die Trennung
  von frischer Attestation und weiter gehaltenem Cleanup. Fehlerhafte Frames,
  trailing bytes, stderr, Exit-/Closefehler und verlorene Cleanup bleiben
  sichtbar; keine Provider-/Chrome-Erfolgsbehauptung daraus.
- DCA-003 (DC-003/004): Originaler Capture-/Delivery-Status bleibt in der
  technischen Diagnose erhalten, auch wenn später das RAM-Ergebnis angezeigt
  wird. Fremde Werte werden normalisiert, keine Rohinhalte gespeichert.
- DCA-004 (alle): Source-/Integrations-/Docschecks und getrennte Spec-/Standards-
  Reviews. Private prüfbare Kandidatenfassung; reale Google-/Codex-Auswahl,
  Fokuswechsel und geschützte Felder bleiben bis zum wirklichen Test offen.
- DCA-005 (DC-002/005): Cursor, Teil- und Gesamtauswahl mit gleicher sichtbarer
  Feld-Enclosure und abweichender Endaffinität zuerst rot, dann grün; Unicode,
  veränderte Grenzen/Affinität und fremdes Feld prüfen. Eigene verborgene
  Windows-RichEdit-Matrix prüft echte Providerbereiche ohne Nutzerfokus oder
  Zwischenablage zu verändern. Sie ersetzt keine reale Chrome-Abnahme.

## Nichtziele

Keine neue Feld-Whitelist, kein blindes Ctrl+V, kein Wiederherstellen fremden
Fokus, kein Browserplugin und keine Umgehung gesperrter UI-Steuerung.
