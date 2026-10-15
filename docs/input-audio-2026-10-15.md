# Eingabefelder und Audio: Prüfstand 15.10.2026

Change-Vertrag: [Spec](../specs/2026-10-15-hugin-input-audio/spec.md),
[Plan](../specs/2026-10-15-hugin-input-audio/plan.md),
[Aufgaben](../specs/2026-10-15-hugin-input-audio/tasks.md).

## Nutzerrückmeldung und Ursachen

Brian bestätigt die alltägliche Übergabe in das fokussierte Codex-Feld. Eine
markierte Auswahl wird noch abgewiesen, weil die bisherige UIA-Grenze nur
kollabierte Carets akzeptiert. YouTube läuft in Chrome. Das DOM der tatsächlichen
Suche weist ein aktiviertes, schreibbares INPUT/text mit role=combobox aus;
das ist noch kein Nachweis seiner nativen Windows-UIA-Fähigkeiten.

Die flüssigen vorbereiteten WAV-Proben prüfen den Player mit bereits fertigen
Samples. Der echte Qwen-Pfad berechnet den nächsten Providerblock erst nach
dem kreditgebremsten Versand des vorherigen. Ein deterministischer Server-/
FIFO-Repro mit 6×667ms PCM und 250/350ms Berechnung zeigt 5×93/193ms Lücken.
Damit ist eine zusätzliche Lückenursache reproduziert; echte GPU-Zeiten und
das neue Hörurteil bleiben getrennte, offene Nachweise.

## Verhaltensvergleich mit Whispering

Untersucht ist die zur installierten Version7.11.0 passende feste Revision
a6b15c28db9076742d7ae7014f8ec9f97aa615d1. Ihr
[Desktop-Textservice](https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src/lib/services/isomorphic/text/desktop.ts)
delegiert an den nativen Befehl. Die
[Rust-Implementierung](https://github.com/EpicenterHQ/epicenter/blob/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src-tauri/src/lib.rs)
sichert Text aus der Zwischenablage, stellt das Diktat bereit, wartet50ms,
simuliert unter Windows Strg+V, wartet100ms und stellt verfügbaren vorherigen
Clipboardtext zurück. Sie sucht dabei nicht nach einem speziellen YouTube-
oder Codex-Feld. Das erklärt die allgemeine Zielnutzung, belegt jedoch weder
die vollständige Formaterhaltung noch eine Paste-Quittung.

Hugin behält seinen bestehenden Clipboard-/Fokus-/Prozess-/Range-Commit und
prüft reguläre Feldfähigkeiten. Fremde Implementierung und Soundassets werden
nicht übernommen. Die beiden Aufnahme-Cues werden aus eigenen PCM-Tönen
erzeugt.

## Implementierung und noch offene Abnahme

- Konfigurationsschema2 trennt eine optionale Verified-Edit-Freigabe von
  gemessenen App-Verzögerungen. Codex behält seine0,15s-Overrides. Generische
  Freigabe wird nach der erfolgreichen echten Chrome-Teil-Auswahlprobe mit
  0,25s im neuen Pilotprofil aktiviert. Das live gestartete Main bleibt bis
  zur geprüften Integration unverändert.
- Parser→Service-Guard zunächst rot, danach49 passende Sourceprüfungen grün:
  unbekannte App mit Feldnachweis akzeptiert, Codex-Override bevorzugt,
  unbekannte Range und veränderter Fokus ohne Clipboardmutation abgewiesen.
- Native Chrome-/YouTube-Probe: ursprüngliches leeres Feld bestätigt, eigenes
  synthetisches17-Zeichen-Literal gesetzt und6..11 markiert. Tatsächliche
  Delivery über den neuen Service ohne App-Sondereintrag ersetzt exakt diesen
  Bereich durch4Zeichen, Präfix/Suffix bleiben erhalten. Warm46,482ms,
  Delivery0,585s, drei Clipboardformate bytegenau zurück, Service geschlossen.
  Kein Enter/keine Suche abgesendet. Eigene Feldbasis anschließend entfernt,
  ursprüngliches leeres Feld bestätigt. Receipt nur im ignorierten Runtimepfad.
- Eine anschließende Gesamtauswahlprobe wurde als unverifizierbar abgewiesen;
  kein Paste. Der Windows-Vordergrund wechselte während der Diagnose zurück
  zu Codex. Gesamtauswahl dadurch nicht nativ bestätigt; kein Produktfehler
  aus diesem unkontrollierten Fokuswechsel abgeleitet.
- 30 scoped Windowsprüfungen grün, darin24 ABI-/Producerprüfungen und eigene
  HiddenRichEdit-TextPattern-Fixture; keine Nutzerfokus-/Clipboardänderung.
- Native Codex-Auswahl, aktive eigene Win32-Fixture, echte serielle
  Modell→Controller→Player-Proben, Cue-Gate/Echo und Hörurteil offen.

Keine Feldtexte, Diktate oder persönlichen Audioaufnahmen werden in diesen
Nachweisen oder im Repository gespeichert. Frühere native Restorebelege und
der dokumentierte frühere Verlust eines RAM-Clipboardstands gelten unverändert
mit ihren jeweiligen Grenzen.
