# Hugin Pilotkorrekturen — Stand 15.10.2026

## Auftrag und Git

- Codex-Diktat einfügen, Aussetzer bei Freya UND Tyr beheben, ersten Modellstart
  anzeigen. Vertrag: specs/2026-10-14-hugin-v1/pilot-fixes.md.
- Repository valhalla-hq/hugin; Branch codex/hugin-pilot-fixes-mjolnir.
  Root-Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-pilot-fixes-mjolnir.
  Ownership aktiv auf Mjolnir; einmaliger Supervisor braucht diesen Worktree.
  Keine fremde Helper-Ownership übernehmen.
- Control e3deecae6673a024aa9015a4387737fbec04c795. PR5/6 integriert;
  Main/aktuell laufender Pilot2298f298c99e5f7491465b91b8a17eeef2575a69.
- Geprüfter Source ce0c1cfeb498b31db8fbafc5bf5e38e8b2001396,
  Draft/Fortsetzung https://github.com/valhalla-hq/hugin/pull/7.
  Routineintegration unter zentralem Lifecycle autorisiert; keine neue Policy,
  Kosten, Veröffentlichung oder dauerhafte Autostartänderung.

## Umsetzung und Prüfstand

- Audiofix/Ladeanzeige/präzise Meldungen integriert. Freya48/Tyr47 leere Refills
  vorher, beide0 nachher; PCM-Bytes/Hashes identisch. Native Laufzeiten6,905→
  6,084s /6,697→5,921s, Stoppguard grün. Menschliches Hörurteil beider offen.
- Character-Suche entfernt: reale Codex-Endaffinität war damit nicht exakt
  darstellbar. Lokale UTF-16-Präfixlänge, Caret-Kind-ID und Endrelation bilden
  jetzt den Nachweis. Höchstens262145 Zeichen lesen/262144 UTF-16-Einheiten
  akzeptieren; nur kurz im isolierten RAM, kein Value/Inhalt in IPC/Diagnose/
  Dateien. Position0 ohne Textlesen. Die frühere Aussage eines vollständig
  textfreien produktiven Metadatenpfads ist ausdrücklich ersetzt.
- Edit-Range und Präfix müssen GetChildren.Length0 beweisen; Objekte/unknown
  vor Lesen sperren. Nach letztem GetText Auswahl/Kind/Endrelation/Struktur/
  Editierbarkeit frisch prüfen.50ms-Deadline unverändert.
- Windows ergänzt Formate beim Close: veröffentlichte Sequenz am Produzenten
  einmal mit stabilem Sequenz-/Owner-Nachweis normalisieren. NULL-Owner bleibt
  unknown, RAM-Snapshot erhalten; belegte fremde Nutzerkopie gewinnt.
- Zwei exakte Chromium-Herkunftsformate opak als HGLOBAL erhalten. Andere
  unbekannte/OLE-/verzögerte Formate bleiben vor Clipboardmutation gesperrt.
- 328 Sourcechecks in19,016s und23 Windowschecks in0,341s grün, keine Skips.
  Windowsumfang22 ABI-/Producerguards + eigener nativer HiddenRichEdit.
  Zwei unabhängige Reviews, reproduzierte P1/P2 geschlossen. Zusätzlicher
  Boundaryreview110 passende Source-/Mocktests grün. Keine native Freigabe
  allein aus simulierten Prüfungen ableiten.
- Vorstufe3fb625c nativ: einmaliges Paste, aktuelle Clipboardformate zurück,
  End-Caret erfasst, echter Home-Wechsel mit target_changed/noSubmit abgewehrt.
  Warm38,3ms/Delivery0,483s; Fixture-Cleanup noch nicht vollständig bestätigt.
  Aktueller vollständiger Abschlussbeleg weiterhin offen.
- docs/codex-delivery-2026-10-15.md ist der aktuelle kuratierte Nachweis;
  docs/pilot-fixes-2026-10-14.md hält den früheren Source-/Prüfstand fest.

## Laufzustand und Daten

- C:/Users/brian/Hugin zeigt auf sauberen Mainclone. Exakte Sitzung über
  Root.runtime/current-pilot-fixes-session.txt frisch lesen; zuletzt
  pilot-session-b758c2ec-768c-42bf-8b42-310597fcfd23.json,
  Supervisor5232/App-Launcher21684/tatsächliche App14688. Vor Wirkung frisch
  binden; PIDs allein sind keine Autorität.
- Einmaliger Supervisor Root.runtime/pilot_session.pyw. Normaler Tray-Beenden-
  Pfad wartet eigenes Familienende ab und startet beide unveränderten alten
  Startup-lnks. Main erst nach Appende aktualisieren; kein Live-Source-Mix.
- Whispering/PipPal und alter Qwen regulär pausiert, alter STT-HTTP-Standby
  unverändert. Profil/Startup-lnks hashidentisch. Alte Apps nur regulär
  beenden; keine fremden Killaktionen oder parallele GPU.
- Strg+Alt+D/V aktiv; Maus/Alt+Y/Gesamtmigration gesperrt.
- Eine frühe fehlgeschlagene Testprobe verlor den RAM-Clipboard-Ausgangsstand
  bei Prozessende. Dieser wurde nicht wiederhergestellt; nur eigenes geprüftes
  Testartefakt entfernt. Spätere Restores gelten separat. Keine Rohinhalte in Git.

## Offen und nächste Schritte

1. PF-001 offen, targets.json leer. Letzte Abschlussprobe stoppte vor Mutation
   wegen einer inzwischen ersetzten fremden App-Kopie. Frage „Test kopiert“
   pending; bei Antwort sofort Root.runtime/focus_codex_probe.py starten.
   Normaler UIA-SetFocus aktiviert den eindeutig gebundenen Hauptcomposer;
   keine weitere Fokus-Rückfrage oder Rückfragekarte als Nachrichtenfeld.
2. Fixture prüft Paste/Restore/End-Caret/Home-Gegenfall/Baseline. Cleanup über
   echte Tastenauswahl, nur exakt bestätigtes eigenes Literal löschen. Kein
   Enter/Absenden/ganze Feldlöschung. Snapshot/Ausgangstext im RAM; bei
   Clipboard-Cleanupfehler Prozess/Owner erhalten. Gebundener Codex
   ChatGPT.exe26.1007.9446.0, FamilieOpenAI.Codex_2p2nqsd0c76g0. Identität vor
   jedem Lauf frisch prüfen und bei Wechsel neu binden.
3. Nur bei vollständiger aktueller Probe exakte native Klasse/Paketfamilie und
   .15s-Restore samt Evidence/shipped-profile Guard aktivieren. Source geprüft;
   Konfigurationsdelta separat prüfen.
4. Kontext/Handoff/PR aktualisieren, gepushten Head/CI prüfen, routine-privat
   integrieren. Hugin normal beenden, Rückweg beweisen, Main FF, alte Apps
   regulär pausieren und geprüften Pilot neu starten. Exakten Receiptpfad
   wählen, kein beliebiges neuestes JSON.
5. Menschliches Hörurteil Freya/Tyr und weitere Produktabnahme.

Fortsetzen: Hugin AGENTS.md, CONTEXT.md, exakt diesen Handoff und pilot-fixes.md
lesen; Preflight mit aktivem Branch, Git/PR/Ownership/Sitzung frisch prüfen.
Dieselbe Root-Ownership weiterverwenden. Native Gesamtabnahme/Hörurteil offen
halten, keine Freigabe aus älteren Teilproben ableiten.
