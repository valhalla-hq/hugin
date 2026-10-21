# Hugin: Clipboard-Format abgelehnt, Wiederholung erfolgreich

## Objective und Git

Einfügeproblem nach dem Originaltonwechsel im Codex-Nachrichtenfeld untersuchen;
Brian fragt zusätzlich nach der Versionsbasis. Ergebnis ist ein kuratierter
Diagnosecheckpoint, kein behaupteter Codefix für ein unbekanntes Format.

- Repository valhalla-hq/hugin, privat; Mjolnir.
- Control-Preflight e3deecae6673a024aa9015a4387737fbec04c795.
- Branch codex/hugin-clipboard-format-mjolnir.
- Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-clipboard-format-mjolnir.
- Basis und laufender Source d3fd28df648b577a32c7cc61a6614b58c2206c5d aus PR14.
- Main/Deployment weiterhin defe3d8f0ef9e564da1936a77b931476cbafc98a.
- Ownership beim Save aktiv; nach sauberem überprüftem Remotecheckpoint nur
  über das Workspacewerkzeug freigeben. Tatsächlichen Release frisch prüfen.
- Scope: Diagnose und Sicherung; kein Rollback, Quellenwechsel oder Formatbypass.
  Finalen Dokumenthead/PR über Branch frisch lesen.

## Beobachtung, Ableitung und Grenzen

Brian meldet Input11:03:47 MESZ am19.10.2026: ERROR/clipboard_failed,
native_target_captured/target_captured/format_unsupported, pending_cleanup=false.
Betroffen ist das Codex-Nachrichtenfeld. Der tatsächliche Produzent liefert
format_unsupported beim Clipboard-Snapshot: nicht unterstütztes Format oder
ungültige/übermäßige Formatliste, vor Staging, SendInput und Clipboardmutation.
Der vorhandene Feldprüfer ist an diesem abgelehnten Durchlauf bereits passiert.

Die gesicherte funktionierende Basis5137477 ist bestätigter Vorfahr von d3fd28d.
Clipboarddatei in beiden Trees: Blob2932cfd442e60d4e0f05189880dd047e5f44941a;
selection_probe: Blob6e199b8ec4e20e7045351a4dd7c79c7d8dbb984a.
Keine Änderungen an diesen Produzenten durch die Tonarbeiten. Ein zeitlicher
Zusammenhang allein belegt deshalb keine neue Clipboard-Code-Regression.

Nach „Diagnose kopieren“ wurden rein lesend nur CF_UNICODETEXT, CF_LOCALE,
CF_TEXT und CF_OEMTEXT bei stabiler Sequenz beobachtet; alle sind zugelassen.
Kein GetClipboardData, kein Lesen persönlicher Inhalte und keine Datenmutation
für diese Untersuchung. Die vorherige Formatliste ist dadurch nicht rekonstruiert.
Brian bestätigt nun erfolgreiche Wiederholung. Dieselbe Appfamilie vom10:31:53-
Start meldet Input11:07:35 MESZ: IDLE/submitted, kein Fehler und kein Cleanup.
Keine Sourceänderung, kein Appneustart und kein Clipboardreset durch den Agenten.

Führende Erklärung: abgelehnter früherer Clipboardzustand; genauer Formatname,
Herkunft und Speichervertrag unbekannt. Keine allgemeine Feld-/Produktabnahme.
Nicht willkürlich unbekannte Formate überspringen oder als HGLOBAL lesen:
sonst drohen Verlust des vorherigen Inhalts oder falsche Handlebehandlung.

## Verifikation und laufender Zustand

59 Clipboard-/Application-Contracttests in0,295s grün. Zusätzlich zwei bestehende
Windows-ABI-Tests mit simuliertem OS: unbekannte Formate vor Materialisierung
ablehnen und bekannte Chromium-Metadaten vollständig erhalten; beide grün.
Kein Code-/Testdiff. Nur CONTEXT und dieser Handoff werden gesichert.
Der ignorierte lokale Helfer .runtime/read_clipboard_formats.py enumeriert nur
IDs/Namen und Zulassung, ohne Handles, Clipboardinhalte oder UI-Eingaben zu lesen.

Livepfad C:/Users/brian/brian-projects/worktrees/hugin/hugin-whispering-cues-mjolnir,
funktionaler Laufhead d3fd28d, eigener Supervisor mit unverändertem Altstack-
Rückweg. Diesen Source und seine Python-Helfer bis zum normalen Ende erhalten.
Nach vorigem Escape-Stopp wurden keine weiteren Computer-Use-Aktionen ausgeführt.

## Pick Up Here / Starter Prompt

Falls format_unsupported erneut auftritt: zuerst rein lesend nur Format-IDs und
-Namen erfassen, bevor „Diagnose kopieren“ die Liste ersetzt. Persönliche
Clipboardinhalte nicht auslesen, leeren oder protokollieren. Das konkrete Format
und seinen sicheren Speichertyp reproduzieren; erst danach eng begrenzt fixen
und Erhalt/Restore sowie Ablehnung unbekannter Formate prüfen. Bei Bedarf
Codexfeld nur manuell durch Brian bedienen; keine ChatGPT/Codex-UI-Automation.

Continue Hugin from handoffs/2026-10-19-clipboard-format.md. The same d3fd28d
pilot recovered after a clipboard format rejection without code changes or
restart. Saved base5137477 is present and clipboard/field code is identical.
Exact rejected format is unknown. Read Git/CI, ownership and live state first;
capture only technical format metadata on recurrence before diagnosis copy.
Do not weaken unknown-format preservation or modify the live source/helpers.
