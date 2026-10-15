# Hugin Pilotkorrekturen — Stand 15.10.2026

## Auftrag und Git

- Ziel: Codex-Diktat automatisch einfügen, Aussetzer bei Freya UND Tyr beheben,
  ersten Modellstart verständlich anzeigen. Vertrag:
  specs/2026-10-14-hugin-v1/pilot-fixes.md. Geordnete vorübergehende Pause der
  Altapps ist ausdrücklich autorisiert; Profile/Autostarts/Modelle erhalten.
- Repository valhalla-hq/hugin; aktiver Branch codex/hugin-pilot-fixes-mjolnir.
  Exklusiver Root-Worktree:
  C:/Users/brian/brian-projects/worktrees/hugin/hugin-pilot-fixes-mjolnir.
  Ownership bleibt aktiv auf Mjolnir, solange die native Abnahme offen ist.
- Preflight-Control e3deecae6673a024aa9015a4387737fbec04c795.
  PR5 und PR6 integriert; geprüfter Source/Main:
  2298f298c99e5f7491465b91b8a17eeef2575a69.
  https://github.com/valhalla-hq/hugin/pull/6
- Routinemäßige private Integration folgt dem zentralen Lifecycle-Vertrag;
  keine neue Policy, Veröffentlichung, Kosten oder Autostartänderung.

## Umsetzung und Verifikation

- Übergabemeldungen unterscheiden Zielwechsel, ungeprüftes und unprüfbares
  Ziel; Whisper-/Qwen-Laden sichtbar. Ownertickets, Widerruf und Shutdown-
  Barrieren geprüft. UIA-Fokus-/Edit-/Caret-Nachweis und warmer Einmal-Commit
  erhalten; keine private Textauswertung im produktiven Metadatenpfad.
- PCM-Doppelbuffer für beide Stimmen: Freya48/Tyr47 leere native Refills vorher,
  beide0 nachher, Bytes/Hashes identisch, alle eigenen Player geschlossen.
  Native Laufzeiten6,905→6,084s /6,697→5,921s; Stoppguard grün. Menschliches
  Hörurteil nach erneutem Abspielen beider Stimmen am15.10 fehlt weiterhin.
- Sourcec3bacfd ersetzt globale Chatprefix-Rundwege durch begrenzte lokale
  Vorwärtssuche mit exaktem Rückweg. Position0 per Endpunktgleichheit; lokale
  Grenze262144, Ordnung statt angenommener Zeichen-Distanz, Deadline50ms.
  Alte globale Produzentenfunktion und Prefixgrenze entfernt.
- Zwei neue Producer-Guards zuerst rot;312 Vertrags-/Integrationsprüfungen,
  29 Targetcontracts,16 Windows-ABI-Verträge und ein eigener nativer
  HiddenRichEdit-Test grün. Beide unabhängigen Reviews ohne offene Befunde;
  Boundaryreview über4621 Positionen/Grenzfälle, höchstens37 Move-Aufrufe.
- Readonly Codex-Position0: initial0,364/0,325s, warme Bestätigung35,4/50,3ms
  inklusive äußerem Messaufruf. Eigene EOF-/Writer-/Familienbarrieren bestätigt.
  Keine p95-Zusage oder Warmzeitprüfung anderer Positionen. Kuratierte Belege:
  docs/codex-delivery-2026-10-15.md und docs/pilot-fixes-2026-10-14.md.
- PR6-Head26296df mit frischen grünen Hosted-Checks und unverändertem Scope
  integriert; Merge2298f298c99e5f7491465b91b8a17eeef2575a69 remote bestätigt.

## Laufzustand und Daten

- Pilot normal beendet, Supervisor bestätigte eigenes Familienende und
  Altstack-Rückstart. Whispering/PipPal erneut normal pausiert, alter Qwen
  beendet. Profile und beide Startup-lnks hashidentisch.
- Neuer sichtbarer Pilot vom sauberen Main2298f298 gestartet. Exakte Receipt
  über Root.runtime/current-pilot-fixes-session.txt; zuletzt Supervisor5232,
  App-Launcher21684, tatsächliche App14688. Vor Aktionen frisch verifizieren.
- Einmaliger Supervisor ist Root.runtime/pilot_session.pyw, nicht im Main-
  Runtimeordner. Root-Worktree während seines Laufs erhalten. Tray-Beenden
  startet nach eigenem Job-Ende beide unveränderten Startup-lnks.
- Strg+Alt+D/V aktiv; normale Maus-/Alt+Y-Bindungen und vollständige Migration
  gesperrt. Alter STT-HTTP-Standby unverändert.
- Keine Diktate, UI-/Clipboard-Inhalte, Rohlogs oder Modelle in Git. Manuelle
  Fixture hält den Ausgangsinhalt nur im RAM und entfernt ausschließlich ihren
  verifizierten synthetischen Präfix; kein Enter und keine ganze Feldlöschung.

## Offener Nachweis und nächster Schritt

1. PF-001 ist offen, targets.json enthält weiterhin keine Freigabe. Brian
   bestätigte ein leeres Feld; beim Test war jedoch Teams im Vordergrund.
   Auch eine45s-Warteprobe fand keinen aktiven Codex-Composer. Kein Paste.
   Frage „Jetzt testen“ pending; bei Antwort vorbereitete Probe sofort starten.
2. Root.runtime/codex_paste_probe.py --ready-confirmed prüft echtes einmaliges
   Paste, Clipboard-Restore, echten Home-Caret-Gegenfall und Baseline-Erhalt.
   Gebundener Codex: ChatGPT.exe im WindowsApps-Paket26.1007.9446.0,
   PaketfamilieOpenAI.Codex_2p2nqsd0c76g0. Fixture prüft frische Bindung und
   aktiven Hauptcomposer; Rückfragekarten sind ausgeschlossen. Bei neuer
   Prozess-/Fensteridentität zuerst frisch binden, nie unbekannt weiterlaufen.
3. Erst bei vollständigem Erfolg exakte Codex-Klasse/Paketfamilie samt
   gemessener Restorezeit, Nachweis und shipped-profile Contract aktivieren.
   Unabhängig prüfen, Hosted-Checks am exakten Head, privat integrieren und
   Pilot geordnet neu starten. Keine globale Chromium-Freigabe.

Fortsetzen: Hugin AGENTS.md, CONTEXT.md, diesen exakten Handoff und
pilot-fixes.md lesen; Git/PR/Ownership/Laufzustand frisch prüfen. Dieselbe
Root-Ownership weiterverwenden, keine Helper-Ownership übernehmen. Nur eigene
gehaltene Ressourcen bereinigen, Altapps ausschließlich normal beenden, keine
parallele GPU. Native Paste-/Restore-Abnahme und Hörurteil bleiben erforderlich.
