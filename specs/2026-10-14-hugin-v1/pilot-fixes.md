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
