# Pilotkorrekturen: Codex-Übergabe und Vorlesen

Brian meldet am 14.10.2026: Diktat flüssig und inhaltlich gut, erster Lauf
langsamer; automatische Übergabe in Codex fehlt bei unverändertem Ziel und
behauptet einen Zielwechsel. Vorlesen klingt bei Freya und Tyr abgehackt.

## Vertrag und Prüfweg

- **PF-001 / AC-003/011:** Ein synthetisches Diktat erscheint genau einmal im
  unveränderten Codex-Eingabefeld, ohne Absenden. Nur tatsächlich geprüfte
  Ziele aktivieren. Fenster-/Control-/Auswahl-/Caret-Wechsel und Nutzerkopien
  vor dem Commit verhindern Paste; unprüfbare Ziele bleiben kopierbar.
- **PF-002 / AC-009/010:** Die Anzeige unterscheidet tatsächlichen Zielwechsel,
  ungeprüfte Zielklasse und nicht prüfbares Eingabefeld. Fertiger Text bleibt
  im RAM. Diagnose enthält keine Sprach-/Fenster-/Clipboard-Inhalte.
- **PF-003 / AC-005/006/012:** Freya und Tyr passieren denselben PCM-Pfad ohne
  Paketlücken, vertauschte oder verworfene Samples. Engste reproduzierbare
  Grenze zuerst rot, danach grün; nativen Output und Stopp seriell prüfen.
  Ein Hörurteil bleibt als menschlicher Nachweis getrennt.
- **PF-004 / AC-002/013:** Den ersten Modellstart von der eigentlichen Erkennung
  unterscheiden und im vorhandenen Status sichtbar machen. Keine ungeprüfte
  Änderung an Modellresidenz, Warmup oder GPU-Serialisierung.

## Plan und Aufgaben

1. Ursachen an Clipboard-Zielprüfung/Controller-Meldung und PCM-Produzent/
   Player trennen und reproduzieren. Vorhandene GPU-Messungen für Kaltstart
   gegen den aktuellen Initialisierungspfad prüfen.
2. Präzise Übergabemeldungen und Ladeanzeige mit Controller-Guards korrigieren.
3. Den engsten UIA-Zielnachweis für Codex implementieren; COM-/Provideraufrufe
   weiter isolieren, Zeit-/Speichergrenzen und Cleanup erhalten. Native
   synthetische Codex-Übergabe und Gegenfälle prüfen, erst dann freigeben.
4. Gemeinsamen Audiofehler am erzeugenden Boundary beheben; beide Stimmen,
   kontinuierliche Samples, Drain und priorisierten Stopp prüfen.
5. Source-/Native-Checks, unabhängige Reviews und exakte Hosted-Checks.
   Privat integrieren und sichtbaren Pilot geordnet neu starten. Bestehenden
   einmaligen Rückweg, alte Profile/Startverknüpfungen und Modelle erhalten.

Root besitzt Integration, Controller/Meldungen, Konfiguration und Abnahme.
Begrenzte Helper besitzen getrennte UIA- und Audio-Worktrees. Keine parallelen
GPU-/Audioaktionen; Tests mit tatsächlicher Ausgabe werden koordiniert.
Normale Maus-/Alt+Y-Aktivierung und vollständige Migration bleiben offen.

## Prüfstand

- PF-003: deterministische Guards und echte Windows-Wiedergabe für beide
  Stimmen grün; menschlicher Hörvergleich noch offen.
- PF-002/004: Controller-Guards und bestehende Ladeanzeige grün.
- PF-001: Source-Guards/Review grün, reale Codex-Paste-/Restore-Probe noch
  offen. Leeres aktives Nachrichtenfeld nötig; kein Entwurf wird verändert.
  targets.json bleibt bis zu diesem Nachweis leer. Audio-/Statuskorrekturen
  können als geprüfter Pilot bereitgestellt werden; dies erfüllt PF-001 noch
  nicht und ist keine vollständige Abnahme.

## Fortsetzung 15.10.2026: echte Codex-Prüfung

- Brian hat ein leeres aktives Nachrichtenfeld bestätigt. Die manuelle
  Testfixture muss das aktive Composer-Feld von Rückfragefeldern unterscheiden;
  Windows-Value allein gilt bei widersprüchlicher Leeranzeige nicht als Beweis.
- Reproduziert: der globale UIA-Character-Rundweg kann während Chat-Ausgabe
  scheitern, obwohl der lokale Einfügepunkt unverändert bleibt. Position0 ist
  durch gleiche Anfangsendpunkte direkt bewiesen; übrige Positionen werden
  begrenzt vorwärts vom Edit-Anfang gesucht und wiederholt mit geordneten
  Nachbareinheiten bestätigt. Den
  globalen Rundweg samt alter Prefixgrenze entfernen; lokale Grenze262144
  behalten. Editierbarkeit, Identität, Auswahl-/Fokus-/Token-Gegenprüfungen
  bleiben vollständig erhalten. Guard-first, dann nativ messen.
- Zwei echte warme Bestätigungen liefen bei55/62ms in das50ms-Limit. Erst die
  einzelnen Antwort-/EOF-/Cleanupzeiten messen, danach den Produzenten ändern;
  keine Freigabe allein aufgrund eines vergrößerten Timeouts. Der tatsächliche
  Paste-/Restore-/Caret-Gegenfall entscheidet über die Codex-Konfiguration.

## Ergänzung aus der tatsächlichen Codex-Probe

- Das aktive leere Feld liefert einen kollabierten UIA-Punkt innerhalb eines
  Platzhalter-Kindelements. GetEnclosingElement darf laut UIA ein Kind des
  Textproviders liefern. Zugehörigkeit zum konkreten fokussierten Edit über
  begrenzte Elternkette beweisen; fremde, geschützte, zyklische und zu tiefe
  Ketten bleiben unprüfbar. Keine CSS-/Klassenheuristik für die Freigabe.
- Reproduziert: vorwärts19 Einheiten trifft den Punkt exakt; rückwärts19
  landet vor dem ursprünglichen Edit-Anfang. Die Annahme eines symmetrischen
  Character-Rundwegs ist an dieser Providergrenze falsch. Sie wird durch
  wiederholte Vorwärtsmessung desselben Punktes und strikt geordnete direkte
  Nachbareinheiten ersetzt. Kein Weg rückwärts vor den Edit, keine Erhöhung
  der Deadline. Mehrdeutige oder instabile Abbildungen bleiben unprüfbar.
- Guards zuerst rot, dann Source-/native Prüfung. Die manuelle Fixture darf
  keine lokale UIA-Nullposition für ein visuell leeres Feld voraussetzen;
  sie bestätigt den tatsächlichen synthetischen Inhalt und den RAM-Ausgangs-
  zustand. Erst vollständiges Paste/Restore/Caret/Erhalten-Löschen aktiviert
  ausschließlich die genaue Codex-Paket-/Klassenkonfiguration.
- Native Reproduktion am Clipboard-Produzenten: nach Close ergänzt Windows
  seine Textformate; zurückgegebene Sequenz9 war bereits Sequenz12, während
  eigenes HWND und Nonce unverändert waren. Veröffentlichung erst danach
  über stabilen Sequenz-/Owner-/Sequenz-Nachweis normalisieren. Kein bloßes
  Übernehmen eines beliebigen späteren Zählers. Teilfehler ebenfalls behandeln;
  unklare eigene Veröffentlichung hält den Originalsnapshot im RAM, bestätigte
  fremde Nutzerkopien haben Vorrang. Alle Recovery-Verbraucher verwenden diese
  Produzentenfakten statt eine Zählerabweichung selbst als Besitzverlust zu deuten.
- Eine geänderte Sequenz mit NULL-Owner bleibt ausdrücklich unbekannt und
  hält den RAM-Snapshot. Die Produzenten-API ist verbindlich, ohne alten
  Raw-Sequence-Fallback im Consumer. Beim Cursor darf ein erschöpfter
  Vorwärtsschritt denselben Punkt mit derselben tatsächlich bewegten
  Einheitenzahl melden, auch vor einer äußeren strukturellen Range-Grenze;
  verschiedene vollständig bewegte Einheitenzahlen bleiben verboten.
- Browserkopien enthalten zusätzlich `Chromium internal source RFH token`
  und `Chromium internal source URL`. Diese beiden dokumentierten HGLOBAL-
  Formate unverändert im bestehenden begrenzten RAM-Snapshot sichern und
  wiederherstellen; weder dekodieren noch protokollieren. Andere unbekannte
  Formate und komplexe OLE-Dateiobjekte bleiben vor jeder Mutation gesperrt.

## Eindeutige lokale Cursorposition

Die reale End-Taste zeigt einen weiteren Providerfall: GetSelection meldet
einen kollabierten Punkt im Textkind des Edits, der mit keinem vorwärts
erreichbaren Character-Endpunkt exakt vergleichbar ist. Auch RangeFromChild
und ein Einheiten-Rundweg lösen diese Darstellungsdifferenz nicht.

Die Character-Suche wird deshalb durch die UTF-16-Länge des begrenzten
Präfixes vom gebundenen Edit-Anfang zum aktuellen kollabierten Punkt ersetzt.
Vor jedem Lesen müssen Caret und Präfix dem konkreten, nicht geschützten Edit
zugeordnet sein. Ein Punkt hinter der deklarierten DocumentRange benötigt
zusätzlich ein eindeutig besitzbelegtes Kindelement. Dessen Runtimeidentität
wird Teil des eingefrorenen Nachweises; Geschwister dürfen nicht aliasen.

Am Edit-Anfang wird ohne Textlesen Position0 bestätigt. Sonst liest allein
der isolierte Provider höchstens262145 Zeichen, akzeptiert höchstens262144
UTF-16-Einheiten und verwirft die Zeichen sofort nach der Längenbildung.
Kein Value, keine Ausgabe von Präfixtext und keine Übernahme in IPC, Diagnose,
Dateien oder den folgenden blockierenden Read. Die Auswahl-/Fokus-/Readonly-
und native Identitätsprüfung sowie die50ms-Commitdeadline bleiben bestehen.
Dies ersetzt die bisherige Annahme eines ausschließlich textfreien numerischen
Character-Nachweises; der Datenschutzvertrag bleibt lokaler, flüchtiger RAM.
