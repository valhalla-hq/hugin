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
- Vollständige Codex-/Browser-Auswahlmatrix und aktive eigene Win32-Delivery-
  Fixture bleiben manuelle Pilotabnahme. Keine universelle Feldkompatibilität.

## Reale Audiopipeline und Kosten

Geprüfter Source6f4897c16cec03ce37ae014f708271b5f7332f71, bestehende Runtime
bb700f0 nur für Interpreter/Modelle/Locks; Child-PYTHONPATH explizit an den
Task-Source gebunden. Festes synthetisches Deutsch, beide Stimmen seriell;
keine Mikrofon-/Clipboard-/Hotkeyeingabe im Pipelinewerkzeug.

Kontrolle: nur alten Server aus Gitbb700f0 im RAM ausgeführt; derselbe aktuelle
Provider, Client, Controller und native Player. Kein Vergleich mit der gesamten
alten App. Reihenfolge neu→alt→neu, pro Runde frischer CUDA-Worker; Freya
enthält Initialisierung, Tyr nutzt das geladene Modell. OS-/Kernelcaches nicht
isoliert. Einzelmessungen, keine p95-/Kaltstartgarantie.

| Messung | Alter Server | Neuer Server, Abschlussrunde |
| --- | ---: | ---: |
| Freya: leere Audio-Refills | 9 | 0 |
| Tyr: leere Audio-Refills | 8 | 0 |
| Freya: Gesamtzeit inkl. Initialisierung | 22,042s | 20,150s |
| Tyr: warme Operation | 7,711s | 6,326s |
| Zwei Operationen inkl. Cleanup | 30,642s | 27,344s |
| Workerfamilie CPU | 21,625s | 20,984s |
| Controller CPU | 0,797s | 0,391s |
| Familie PeakJobCommit | 8.455.290.880B | 8.454.057.984B |
| Native Audioqueue-Peak | 6.000B | 6.000B |

Freya291.840B/Tyr284.160B, je10 Providerchunks, vollständig beim Player.
Provider-/IPC-/Native-Hashes und Vorher-/Nachher-Hashes identisch. JobCommit
ist keine physische Working-Set-RAM-/GPU-Messung. Tokens, physische RAM-/GPU-
Peaks und akustische Qualität separat ungemessen. Providerkapazität ist code-/
guardbelegt maximal3×1.440.000B; Client-/Playerqueues unverändert. Gemessene
Providerberechnung ca.96–363ms je ca.640ms Audio erklärt die alte Kopplungslücke.

Zusätzliche native Abbruchprobe in erster neuer Runde: nach erstem akzeptiertem
Paket gestoppt, nur6.000B nativ gesendet, Cancellationterminal bestätigt,
Operation0,760s. Kurze dritte Probe zählt nicht zum normalen Stimmenvergleich.
Alle eigenen Worker/Threads/Handles/Familien geschlossen.

## Native Aufnahme-Cues und Gerätezeit

Zwei RAM-Proben auf MME liefern nur ADC0; nach1s42Callbacks und0B nach Gate.
Daher Native-Microphone korrigiert: eindeutiger Windows-WASAPI-Default,
Hostzugehörigkeit/Inputfähigkeit geprüft, Sharedmode auto_convert=True identisch
an Vorprüfung und Stream. ADC0 vor Gate-Discard als Clockfehler. Keine globale/
OS-Geräteeinstellung geändert, kein MME-Fallback.

Korrigierte reale Probe über Microphone.start(armed=False), factory=None;
RawInputStream nur delegierend beobachtet, Gerätewahl/Vorprüfung nicht umgangen.
109Callbacks,12 vor Freigabe verworfen,31.040B nach Freigabe im RAM;
kein akzeptierter ADC vor Cue-Drain+25ms-Cutoff, Bytezählung exakt, beide Cues
vollständig gespielt, Mic/Cue-Owner geschlossen. Gemeldete Latenz22,25ms.
Keine Aufnahme gespeichert oder transkribiert. Dies belegt das Gerätezeit-Gate,
keine physische Echofreiheit oder spätere Defaultgerätewechsel.

## Review und Abschlusschecks

Unabhängige begrenzte Spec-/Standards-Pässe für fremde Slices. Review-P2:
Clone-Collapse konnte falschen Endpunkt einfrieren; zuerst roter Guard,
Produzent prüft Gleichheit zum Originalendpunkt zusätzlich zur Kollabierung.
Originalrepro/Warmpfad unabhängig erneut geprüft. MME-Lücke führte zu sieben
Device-/ADC-/Cleanup-Guards. Keine offenen reproduzierten P1/P2 am Source6f4897c.

390 Source-/Integrationsprüfungen in18,418s und56 Windowsprüfungen in3,377s
ohne Skips grün, einschließlich native Mic-/Player-/Hotkey-/Mutex-/Idle-App-
Lifecycle und HiddenRichEdit. Hosted-CI/neuer Pilot folgen am unveränderten
geprüften Code. Hörurteil, reale Codex-Auswahl/Vollmatrix und Akustiknachlauf
bleiben Nutzerabnahme im Pilot; Maus-/Alt+Y-/Autostartmigration weiter gesperrt.

Keine Feldtexte, Diktate oder persönlichen Audioaufnahmen werden in diesen
Nachweisen oder im Repository gespeichert. Frühere native Restorebelege und
der dokumentierte frühere Verlust eines RAM-Clipboardstands gelten unverändert
mit ihren jeweiligen Grenzen.
