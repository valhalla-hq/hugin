# Word-Korrektur und Codex-Probe

## Objective

Fortsetzung des expliziten Codex-/Word-Folgeauftrags nach PR10. Word-Ablehnung
reproduzieren, sicher korrigieren und separat nativ prüfen. Codex-Ursache
weiter eingrenzen; keine Gesamtproduktabnahme oder Produktionsmigration.

## Git State

- Repository: `valhalla-hq/hugin` (privat).
- Branch: `codex/hugin-codex-word-fix-mjolnir`.
- Base: main`defe3d8f0ef9e564da1936a77b931476cbafc98a` (PR10-Merge).
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-codex-word-fix-mjolnir.
- Ownership: aktiv auf Mjolnir für diesen Chat.
- PR: erste inhaltliche Änderung wird als neue Draft-PR gesichert; exakten
  Remotehead und PR-Link vor Fortsetzung frisch lesen.
- Authorization: Brian setzt den verlinkten Hugin-Chat fort. Die dort
  beauftragten Codex-/Word-Fälle sind der Scope. Kein Policy-/Public-/Autostartauftrag.

## Changed Files

- src/hugin/windows/selection_probe.py: gemeinsamer Feldbinder mit explizitem
  Document-Range-Schreibschutz, ohne ValuePattern für Documents.
- tests/contracts/test_windows_document_target.py und test_windows_target.py:
  neue öffentliche Document-Guards und bestehende Nichtfeldregression.
- specs/2026-10-16-hugin-delivery-completion/: DC-006/007, DCA-006 und Folgeaufgaben.
- docs/word-document-2026-10-19.md: realer Beleg, Messungen und Grenzen.
- README.md, CONTEXT.md, dieser Handoff: aktueller Fortsetzungsstand.

## Verification

- 418 Source-/Integrationstests in 24,322s; drei native Range-/IPC-Tests in 1,281s;
  Docscheck19 Anforderungen/17 Abnahmekriterien grün.
- Word 16.0.20430.20146, eigenes synthetisches Dokument: Aufnahme, fünf warme
  IPC-Bestätigungen, Einfügen am Ende sowie Ersatz von Teil-/Gesamtauswahl.
  Drei tatsächliche Pastes sichtbar bestätigt; jeweils Clipboardrestoration
  gemeldet und kein Recovery offen. Eigene Prüffamilien geschlossen.
- Codex 26.1013.4894.0, von Brian manuell fokussiertes leeres Feld: Aufnahme
  und je fünf Bestätigungen mit Main UND Kandidat erfolgreich. Rein lesend.
  Der berichtete Diktatfehler ist damit noch nicht reproduziert oder behoben.
- Unabhängige Spec-/Standardsreviews ohne Befund. Source-SHA256:
  588829e4aa16673711b1065b2c84fbdcd9bfc6de95495236fedf42d994dd0e93.

## Source And Data Boundary

Keine Benutzerdokumente geöffnet; eigenes ungespeichertes Word-Dokument nur mit
synthetischem Text. Keine Diktate, Rohlogs, UIA-IDs, Clipboardtexte oder Audio
in Git. Lokale begrenzte Probe-Skripte unter .runtime bleiben ignoriert.
Keine Codex-UI-Automation oder Umgehung der früheren Browserablehnung.

## Running State

Die alte Pilotsitzung läuft am19.10. nicht mehr; Main ist sauber auf defe3d8.
Der alte Pilotworktree wurde nicht verändert/entfernt, seine Ownership nicht
manuell angefasst. Whispering ist geöffnet. Keine Hugin-App, Aufnahme oder
Sprachworker durch diese Proben gestartet. Das eigene Word-Testdokument bleibt
ungespeichert offen. Bestehende Profile, Startup-lnks und Altstack erhalten.

## Open Blockers

- Codex: tatsächlicher Diktatablauf mit technischem Capture-/Delivery-Status
  muss reproduziert werden. Leere Feldproben bestehen bereits auf Main.
- Word: geschützte/mehrseitige/objektbehaftete Dokumentmatrix und echter
  Mikrofon-Diktatablauf nicht abgenommen. Keine universelle Word-Zusage.
- Google: kein erneuter Live-Test; bestehende Providerregressionen grün.
- Keine finale Maus-/Alt+Y-/Autostartumstellung; aktuelle Pilotkürzel bleiben.

## Pick Up Here

1. Exakten Branch-/PR-/CI-Zustand lesen. Source und Runtime getrennt halten;
   C:/Users/brian/Hugin bleibt Main-Deploymentclone.
2. Einen zum exakten Kandidaten passenden manuell gestarteten Piloten mit
   bestehendem Altstack-Rückweg vorbereiten; keine alten headgebundenen Starter
   ungeprüft wiederverwenden. Benutzer führt Codex-Eingaben selbst aus.
3. Capture-/Delivery-Status am tatsächlichen Fehler auswerten und erst danach
   eine weitere Ursache ändern. Den Word-Fix nicht als Codex-Fix deklarieren.

## Starter Prompt

Continue Hugin from handoffs/2026-10-19-word-document-codex-probe.md. Read AGENTS,
CONTEXT, exact PR and Git state. Word Document-without-ValuePattern rejection
is fixed and own cursor/partial/full paste probes passed. Codex empty-field
capture/confirmation passes on BOTH main and candidate; original dictation
failure remains open. Do not automate the Codex/ChatGPT UI or activate mouse,
Alt+Y or autostart bindings. Preserve old stack and user data.
