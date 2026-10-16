# Einfügekorrektur: Kandidat vom 16.10.2026

> Aktualisierung nach Brians Abnahme: Google-Diktat und Überschreiben am
> normalen Pilot25d9c97 funktionieren. Codex und Word bleiben fehlgeschlagen.
> Brian beauftragt jetzt den Schnitt und die Mainintegration als bekannte
> Zwischenbasis. Aktueller [Integrationsstand](baseline-2026-10-16.md) und
> [Folgeauftrag](../handoffs/2026-10-16-codex-word-followup.md) ersetzen die
> historischen Lauf-/Mergeaussagen weiter unten. Keine Gesamtabnahme.

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

## Feldgrenze nach der realen Google-Probe

Die Nutzerprobe am16.10. scheitert bereits beim Capture, vor jeder Delivery:
Die Punkt-Enclosure gehört zum aktiven Feld, ihr Endpunkt sortiert jedoch
hinter DocumentRange.End. Dokument und Präfix melden jeweils23 UTF-16-Einheiten.
Der bisherige Produzent verwirft genau diese Kombination. Gleiche Längen
allein sind dabei kein Beweis für Feldzugehörigkeit.

Die installierte Chrome-Version155.0.8059.40 verbirgt Kinder atomarer
Textfelder vor UIA; GetEnclosingElement kann deshalb denselben sichtbaren
Edit-Knoten für unterschiedliche interne Textanker liefern.
[Chromium: ShouldHideChildrenForUIA und GetLowestAccessibleElementForUIA](https://chromium.googlesource.com/chromium/src/+/refs/tags/155.0.8059.40/ui/accessibility/platform/ax_platform_node_win.cc)
Gleiche Textoffsets können durch ihre Affinität unterschiedlich sortieren.
[Chromium: AXPosition::SlowCompareTo](https://chromium.googlesource.com/chromium/src/+/refs/tags/155.0.8059.40/ui/accessibility/ax_position.h)
Die konkreten internen Chrome-Anker wurden nicht beobachtet. Das öffentliche
Providerverhalten erklärt die falsche Annahme; das neue unabhängige Modell
bildet Offset und Affinität getrennt ab.

Die Korrektur entfernt nur die Kopplung von eigener Edit-Enclosure und
Endordnung. Feld-/Root-/Prozesszugehörigkeit, Objektfreiheit, exakt abgeleitete
Endpunkte, begrenzte UTF-16-Präfixe, beide Endrelationen und frische
Wiederholungsprüfungen bleiben erhalten. Es gibt keine zusätzliche Volltext-
Lesung, keine Zeichenwanderung und keine Chrome-Ausnahme. Die bisherige
Descendant-Sonderbehandlung wird damit ein einheitlicher Enclosure-Vertrag.

Zwei alte Affinitäts-Fixtures modellierten einen ungültigen numerischen Offset
mit still abschneidendem Python-Slicing. Sie sind durch gültige Textoffsets
und eine unabhängige Affinität ersetzt. Chromium normalisiert ungültige
Offsets bereits bei GetSelection und Endpunktbewegungen.
[TextProvider](https://chromium.googlesource.com/chromium/src/+/refs/tags/155.0.8059.40/ui/accessibility/platform/ax_platform_node_textprovider_win.cc),
[TextRangeProvider](https://chromium.googlesource.com/chromium/src/+/refs/tags/155.0.8059.40/ui/accessibility/platform/ax_platform_node_textrangeprovider_win.cc)
Unbekannte oder fremde Enclosures bleiben abgelehnt. Ein Provider, der
Feldbesitz und alle zugehörigen Bereichsfakten konsistent falsch meldet,
liegt weiterhin außerhalb des beweisbaren UIA-Vertrags.

## Verifikation

| Prüfung | Ergebnis | Grenze |
| --- | --- | --- |
| Source/Integration: tools/dev.py check --group all |409Tests,18,457s, keine Skips| simulierte Hardware/Provider |
| Neue Feldbereiche plus bestehende Target-/Delivery-/Selection-Guards |91Tests,0,466s, grün| vor Korrektur reproduzierte Endablehnung; synthetische Provider |
| Native eigene RichEdit-Matrix, bestehende Selection-Fixture und IPC-Fixture |3Tests,0,794s, keine Skips| echte TextPattern-Bereiche; Cursor, Endcursor, Teil-/Gesamtauswahl, Unicode, Auswahlwechsel und EM_REPLACESEL ausschließlich am eigenen verborgenen HWND |
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
kleiner isolierter CI-Step ergänzt. Getrennte Spec-/Standards-Wiederprüfungen
am festen Source489ed2ff44aa0b6e9f77a9d8a4b18f2f2ba5dca7 schließen beide
Befunde und finden keine weiteren konkreten Probleme. Beide prüfen jeweils
143 hardwarefreie Scopedtests am festen Source (0,834s/0,832s), keine
Nativeaktionen. Root prüft zusätzlich die oben genannte native IPC-Fixture.

Drei Hostedchecks am Source489ed2f sind grün, einschließlich des neuen
Windows-Prozesssteps in beiden Check-Hugin-Runs:
[Pushcheck](https://github.com/valhalla-hq/hugin/actions/runs/38863724113),
[PRcheck](https://github.com/valhalla-hq/hugin/actions/runs/38863728485),
[Baseline](https://github.com/valhalla-hq/hugin/actions/runs/38863728357).
PR10 bleibt Draft. Der damalige Dokumentcheckpoint änderte nur Context,
Handoff, Aufgaben und diesen Nachweis; sein frischer Head/Blob-/CI-Nachweis
wurde separat geprüft, ohne einen neuen Source- oder Browsererfolg abzuleiten.

Die neue Feldkorrektur wurde in getrennten Spec-/Standards-Pässen am
eingefrorenen Delta gegen94ee13b geprüft. Beide finden keine konkreten offenen
Befunde und bestätigen die Begrenzung der nativen Fixture auf eigene Ranges
und Ersetzung. Jeweils91 hardwarefreie Scopedtests sind grün (0,406s/0,413s).
Producer-SHA256:7cafc36082deae40d289b85e0ca1775a4e4da67ca7a545cb6274ebd118a307da.
Die fünf Source-/Testdateien blieben während der Reviews unverändert;
die Reviewer führten keine nativen Aktionen aus. Root führte die native
Matrix selbst aus. Neue Hostedchecks werden am frischen Remotehead geprüft;
die oben verlinkten Runs gelten ausschließlich für den früheren Source.

## Letzte Abnahme und Laufzustand

Computer Use stoppte die Google-Probe automatisch, weil es die aktuelle
Browseradresse auf Windows nicht zuverlässig genug feststellen konnte.
Kein alternativer UIA-/SendInput-/CDP-Weg wurde zur Umgehung verwendet. Die
vorhandene Testseite erhielt keinen Testtext und keine Suche wurde abgesandt.
Echte Google-/Codex-Teil-/Vollauswahl, Cursor, Fokuswechsel und Schutzfelder
bleiben am Kandidaten ungeprüft. Die reale Feldmatrix ist DC-T07.

Inzwischen hat Brian den Diagnosepilot94ee13b gestartet; Supervisor und App
wurden frisch als laufend beobachtet. Die alte Abwesenheitsbeobachtung ist
überholt. Seine neu gestarteten Probeprozesse verwenden nun eine unveränderte
lokale Sourcekopie dieses Heads mit Hashmanifest. Der laufende Pilot bekommt
dadurch keine halbe Sourceaktualisierung während dieser Korrektur.

Die neue native Matrix prüft die Range-Grenze und native Ersetzung am eigenen
verborgenen RichEdit. Sie prüft weder Fokusattestation noch Clipboard/SendInput
in Chrome oder Codex. Diese kurze reale Abnahme bleibt DC-T07. Die laufende
Diagnoseversion ist noch die alte Fassung; der neue Kandidat benötigt einen
geordneten Neustart. Der stabile Main bleibt8e4ceabb718edb2c8d1b80e1b07b69e0f3b933bd.
Private Draft-PR10 und aktiver Root-Worktree halten die Fortsetzung bereit.
Normale Maus-/Alt+Y-/Autostartmigration folgt erst auf die geprüfte Umstellung.
