# Hugin: Auswahl, reguläre Eingabefelder und Audiofeedback

## Auftrag und bestätigte Ausgangslage

Brian bestätigt am 15.10.2026: Diktate erscheinen im fokussierten Codex-Feld.
Markierten Text möchte er ersetzen. Zwei verschiedene kurze Aufnahme-Signale
fehlen. Beide Stimmen klingen in vorbereiteten WAV-Proben flüssig, im echten
Strg+Alt+V-Pfad weiter abgehackt. Diktat in Chromes YouTube-Suche fehlt ebenfalls.
Bestehende Spec und Datenschutz-/Abbruch-/Rückwegregeln bleiben verbindlich.

Bestätigte Codegrenzen: UIA erlaubt nur kollabierte Carets; Delivery verlangt
bislang einzelne App-Klassen. Worker berechnet weitere Qwen-Chunks erst nach
kreditgebremstem Versand der vorherigen. Deterministischer Server/FIFO-Repro:
6×667ms Audio, 250/350ms Berechnung erzeugt 5×93/193ms Lücken trotz RTF<1.
Reale GPU-Zeiten und ein neuer Höreindruck sind noch nicht gemessen.

## Anforderungen

- IA-001: Diktat ersetzt genau die unveränderte markierte Auswahl im aktiven
  regulären Eingabefeld; ohne Auswahl weiter am Cursor einfügen. Beide
  Auswahlgrenzen prüfen; Markierungsrichtung ist für Ersetzen unerheblich.
- IA-002: Aktive editierbare Felder über Win32-/UIA-Fähigkeiten erkennen,
  statt für jede App einen neuen Klasseneintrag zu benötigen. Codex und
  Chromes YouTube-Suche nativ prüfen; keine universelle Kompatibilitätszusage.
  Passwort, readonly, disabled, Nicht-Eingabefeld, Mehrfachauswahl, eingebettete
  Objekte oder unklare Identität bleiben vor Mutation abgewiesen.
- IA-003: Zwei kurze eigene Töne unterscheiden bestätigten Aufnahmebeginn und
  normales Aufnahmeende. Startton nicht in das Diktat aufnehmen; Endton nach
  Mikrofonabschluss, vor langsamer Zielprüfung/Transkription. Abbruch und
  Start-/Stopfehler erzeugen keinen irreführenden Erfolgston.
  Native Ergänzung vor Produzentenkorrektur: Der bisherige MME-Default liefert
  auf diesem Rechner ausschließlich ADC-Zeitstempel0, trotz fortschreitender
  Streamzeit. Für das Gate deshalb den eindeutigen Windows-WASAPI-Default
  im Sharedmode mit Systemkonvertierung auf16k verwenden. Gerät/Hostzugehörigkeit
  prüfen, identische Optionen an Vorprüfung und Stream; keine OS-/Default-
  Einstellung schreiben oder still auf MME zurückfallen. Unbrauchbare ADC0
  als Clockfehler abbrechen. Reale WASAPI-Probe bestätigt kompatible Zeitbasis.
- IA-004: Kontinuierliches TTS über echte Worker-/IPC-/Controller-Backpressure
  prüfen und verursachende Kopplung beseitigen. Ein begrenzter Worker-Vorlauf
  darf nächste Berechnung parallel zum Versand vorbereiten; genau ein Writer,
  unveränderte Samples/Stimmen, Reihenfolge und priorisierter Stopp.
- IA-005: Clipboard-Original/neuere Nutzerkopie, Fokus-/Range-Commit, RAM-only,
  Offlinebetrieb, GPU-Serialisierung und normaler Altstack-Rückweg erhalten.
  Kein Enter, kein Cloudzugriff/Download im Appbetrieb, keine neuen Settings.

## Abnahme

- IAC-001 (IA-001/005): Synthetische Teil-/Gesamtauswahl in Codex ersetzt,
  unmarkierte Präfixe/Suffixe erhalten, genau ein Paste, alle unterstützten
  Clipboardformate zurück. Rangeänderung zwischen Aufnahmeende und Commit
  blockiert Paste; frühere Cursor-/Unicode-/Endaffinitätsfälle bleiben grün.
- IAC-002 (IA-002/005): Reguläres Chrome-Suchfeld und eigene native Edit-Fixture
  funktionieren ohne App-Sondereintrag. Passwort/readonly/disabled/fremder
  Fokus und unbekannte Grenzen führen zu keinem Paste. Keine Suche absenden.
- IAC-003 (IA-003/005): Geräte-/Cue-/Gate-Reihenfolge, alte ADC-Callbacks,
  schneller Doppel-Toggle, Cancel/Shutdown/Cuefehler geprüft; zwei Töne hörbar
  unterscheidbar, keine synthetischen Cue-Samples im erfassten Diktat.
- IAC-004 (IA-004/005): Verzögerter deterministischer Producer/FIFO-Guard erst
  rot, dann ohne Lücken bei RTF<1 grün. Native Modell→Controller→Player-Probe
  Freya/Tyr seriell, Samples unverändert, Queue/RAM endlich, Cancel/Drain und
  Familienabschluss belegt. Hörurteil getrennt von technischen Messungen.

## Gegenprüfung und Grenzen

Challenge/STORM kompakt: Nutzerwert ist Ersetzen und reguläres Diktieren ohne
App-Liste. Schwächste Annahmen sind konsistente Accessibility-Provider und
rechtzeitiger Clipboardverbrauch. Deshalb genaue Feld-/Prozess-/Range-Proofs
am Commit erhalten, keine blind ausgelöste Ctrl+V-Freigabe; tatsächliche
Chrome-/Codex-Proben erforderlich. Restore-Verzögerung ist keine universelle
Paste-Quittung. Security/Privacy: nur begrenzte temporäre Feldpräfixe im
isolierten RAM, keine Inhalte in Metadaten/Diagnose/Git. Betrieb: ein eigener
Cue-Owner und Writer-Barrieren; Kosten: begrenzter zusätzlicher Worker-RAM,
kein größerer nativer Playerpuffer. Entscheidung: implement-now in bestehendem
Pilot, normale Maus-/Alt+Y-/Autostartmigration bleibt separat offen.

Whispering v7.11.0/a6b15c28: Desktop-Textservice delegiert an write_text;
Rust sichert Clipboardtext, stellt Diktat bereit, simuliert Strg+V und
restauriert verfügbaren Clipboardtext nach Verzögerungen. Keine spezielle
Feldsuche. Soundservice spielt getrennte vorhandene Audios ab. Nur
Verhaltensvergleich, keine Übernahme fremder Assets/AGPL-Implementierung.

## Prüfstand

- Change-Spec vor Code geschrieben; Details/Messungen in plan.md und tasks.md.
- Native Chrome-Teilauswahl und echte TTS-/Cue-Gate-Pipeline belegt;
  Details/Messgrenzen in docs/input-audio-2026-10-15.md.
- Codex-/Browser-Vollmatrix, Cue-Echo und Hörabnahme noch offen; private
  Pilotintegration dient dieser Abnahme, keine Produktionsmigration.
