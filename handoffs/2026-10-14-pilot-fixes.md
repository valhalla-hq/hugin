# Hugin Pilotkorrekturen — Stand 16.10.2026

> Historischer Handoff, abgelöst durch
> [Codex-/Word-Fortsetzung](2026-10-16-codex-word-followup.md).
> Brian bestätigt Google-Diktat/Überschreiben am25d9c97 und beauftragt die
> Mainintegration als Zwischenbasis trotz offener Codex-/Word-Fehler.
> Die folgenden Lauf-/Mergeaussagen beschreiben den früheren Prüfzeitpunkt;
> aktueller Auftrag, Pilot25d9c97 und Laufabhängigkeiten stehen im neuen Handoff.

## Objective

Markierte Teil-/Gesamtauswahl sicher mit Diktat ersetzen und falsche
Feldablehnungen beheben. Brian bestätigt Freya/Tyr und die neuen Töne.
Kein weiterer Produktumfang. Aktueller Vertrag:
specs/2026-10-16-hugin-delivery-completion/{spec,plan,tasks}.md;
IA- und v1-Verträge gelten weiter.

## Git State

- Repository: valhalla-hq/hugin, privat. Runtime: Mjolnir.
- Branch: codex/hugin-pilot-fixes-mjolnir; Base: main.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/hugin-pilot-fixes-mjolnir.
- Stable Main:8e4ceabb718edb2c8d1b80e1b07b69e0f3b933bd. PR9 regulär
  integriert; drei Hostedchecks, Ancestry und gleicher Head-/Mergetree belegt.
- Vorheriger Checkpoint:94ee13bf61d057a10f20b19e64958621e0d6349e.
  Der neue Kandidatenhead ist der Commit, der diesen Handoff enthält;
  konkrete SHA beim Pickup frisch aus Git/PR lesen, nicht selbstreferenziell.
- PR: https://github.com/valhalla-hq/hugin/pull/10, Draft. Vorher docs-only,
  jetzt Einfügekandidat; Beschreibung/Titel auf finalen Sourceumfang geändert.
  Frühere Reviews/Hostedchecks an489ed2f und94ee13b sind historische Evidenz.
  Neuer Head-/Context-/Handoff-/CI-Nachweis wird nach dem Checkpoint geprüft.
- Ownership: aktiv beim selben Root-Executor/Task auf Mjolnir. Kein neuer
  Executor darf den aktiven Worktree übernehmen. Frühere Helper freigegeben.
- Autorisierung: begrenzter Umsetzungsauftrag und Fortsetzung. Routine private
  Integration nach zentralem Vertrag; keine Policyänderung oder UI-Umgehung.
  Dieser Kandidat bleibt bis zur echten Feldabnahme ohne Live-Rollout.
- Preflight: Control e3deecae6673a024aa9015a4387737fbec04c795 und aktiver
  Branch/Main frisch geprüft vor den Änderungen.

## Changed Files

- Neues Delta seit94ee13b: selection_probe.py entfernt die widersprüchliche
  Ablehnung eigener Edit-Enclosure plus positiver Endrelation. Feldbesitz
  folgt Enclosures; Endrelation bleibt Vergleichsfakt. Keine neue Textlesung
  oder Chrome-Ausnahme. Native Prozess/Root-, Endpunkt-, Objekt-, UTF-16-
  Präfix- und Frischeprüfungen bleiben erhalten.
- test_windows_field_ranges.py trennt gültigen Textoffset und Affinität;
  ersetzt zwei ungültige Affinitäts-Fixtures in test_windows_target.py.
  _uia_field_fixture_probe.py / test_windows_uia_native.py prüfen echte eigene
  RichEdit-Ranges und EM_REPLACESEL an ausschließlich eigenen verborgenen HWNDs.
- Nachweis: Nutzerprobe scheitert beim Capture, eigene Edit-Enclosure,
  positive Endrelation, Dokument-/Präfixlänge jeweils23. Chromium155.0.8059.40
  verbirgt atomare Feldkinder und ordnet gleiche Textoffsets auch nach Affinität.
  Konkretes internes Ankerpaar nicht beobachtet; öffentliche Implementierung
  und unabhängiges Modell erklären den falschen Guard. Pinned Quellen im Doc.
- Frühere Änderungen im selben PR, weiterhin enthalten:
- src/hugin/windows/selection.py, selection_probe.py, clipboard.py:
  Producerzeit, Request5/Response4, Worker-prepare/Owner-confirm ohne I/O,
  echte Pipe-EOFs vor COM-Unwind, direkter Basisinterpreter mit exaktem venv,
  gehaltenes Cleanup. Genau eine Auswahl auch bei Multiple-Fähigkeit.
- src/hugin/application.py, errors.py: Capture-Ausgang statt target-only,
  sichere Statusdiagnose und Fehlermeldungen; gültiges PCM bleibt erhalten.
- tests/contracts/test_delivery_attestation.py und betroffene Controller-/
  Target-/Selection-/Cue-Guards; tests/windows/test_delivery_process.py:
  neue Regressionen und echte eigene Windows-Pipe-/Prozess-Fixture.
- .github/workflows/check.yml: frische eigene venv ohne pip, ausschließlich
  synthetischer Windows-Prozessguard; lokal1Test0,476s grün.
- Specs, docs/delivery-completion-2026-10-16.md, README, CONTEXT und dieser
  exakte Handoff: bestätigtes Audio, Kandidat, Laufzustand und Abnahmegrenzen.

## Verification

- Guards zuerst rot: valide7..18+80ms Cleanup -> target_probe_timeout;
  fehlendes prepare/Zeitmetadatum; verlorener Capturegrund; Feldexception
  verhindert STT; Multiple-Fähigkeit+ein Bereich; echte Pipe-EOF-Verzögerung.
- Neues Delta zuerst rot an der tatsächlichen Capture-Ablehnung, danach grün.
- tools/dev.py check --group all:409Tests18,457s, grün ohne Skips.
- Neue Range-/Target-/Delivery-/Selection-Verträge:91Tests0,466s grün.
- Native eigene RichEdit-Matrix plus Selection-/IPC-Fixtures:3Tests0,794s,
  grün ohne Skips. Cursor, Endcursor, Teil-/Gesamtauswahl und Unicode korrekt
  vermessen und tatsächlich per EM_REPLACESEL ersetzt. Auswahlwechsel erkannt,
  Nutzerfokus/Clipboard unverändert. Kein voller Fokus-/Paste-/Chrome-Nachweis.
- Getrennte unabhängige Spec-/Standardsreviews am eingefrorenen Delta gegen
  94ee13b ohne offene Befunde; jeweils91 hardwarefreie Tests0,406s/0,413s grün.
  Producer-SHA256:7cafc36082deae40d289b85e0ca1775a4e4da67ca7a545cb6274ebd118a307da.
  Fünf Source-/Testdateien während Review unverändert; keine nativen Aktionen
  durch Reviewer. Die echte Matrix führte Root aus.
- Frühere Verifikation vor dem neuen Delta:
- Gezielte Controller/Cue/Attestation/Target/Selection/Process-Tests:
  144Tests1,205s, grün ohne Skips. Eine echte eigene native Windows-Fixture
  prüft gemeinsame monotone Zeit, venv, frühes EOF und120ms gehaltene Familie.
- tools/dev.py check --docs:19Anforderungen/17AC, keine Probleme.
- Getrennte Spec-/Standards-Pässe am73f7390: Clipboardlock während Unwind
  (P1) und Frischeverbrauch vor wartendem Nativecheck (P2) reproduziert und
  mit zuerst roten Commit-Seam-Guards korrigiert. Beide unabhängigen finalen
  Wiederprüfungen am489ed2f ohne offene Befunde; jeweils143 hardwarefreie
  Scopedtests grün0,834s/0,832s. Drei Hostedchecks an diesem Source grün,
  beide neuen Windows-IPC-Steps separat als success nachgewiesen.
  Malformed-Identity-Fixtures auf gültige Response4-Envelopes migriert.
- Historisch:390Source/56Windows aus15.10., echte Mic-/Audio-/GPU-/Cancel-
  Nachweise in docs/input-audio-2026-10-15.md. Keine Wiederholung/Erfolgs-
  Behauptung am neuen Kandidaten. Neue native Fixture ist kein Chrome-Test.

## Source And Data Boundary

Keine Diktate, Audio, Clipboardinhalte, Titel/URLs, IDs, Exception-Payloads,
Credentials, Umgebungsdumps, Rohlogs oder Runtimeartefakte in Git. Keine
Fremd-UI/SendInput/CDP nach Computer-Use-Ablehnung. Eigene synthetische
Prozesse, Pipes und verborgene HWNDs ausschließlich CPU; kein Mikrofon/GPU/
Clipboardzugriff. Native Feldtests verwenden nur eigenen synthetischen Text.

## Running State

- C:/Users/brian/Hugin ist Junction zum sauberen _repos/hugin-Mainclone.
  Dieser bleibt8e4ceab; kein Sourceupdate und kein Kandidatenstart hier.
- Brian hat Diagnosepilot94ee13b gestartet; App/Supervisor wurden frisch laufend
  beobachtet. Die frühere Abwesenheitsbeobachtung ist überholt. Ignorierte
  Receipt: .runtime/pilot-session-884da9d9-dd7b-4d5a-82c1-1d9e4f474018.json.
  Receipt/PID allein ist keine Cleanup-Autorität; Supervisor hält eigene Familie.
- Dessen neue Probeprozesse nutzen unveränderten Source94ee13b unter
  .runtime/pilot-source-94ee13bf61d0 mit Hashmanifest; trace_selection_probe.py
  ist darauf festgelegt. Keine halbe Liveaktualisierung während Codeänderungen.
- Neuer Kandidat benötigt geordneten Neustart. Normaler Starter ist
  .runtime/Hugin-Test-starten.cmd / pilot_candidate_session.pyw mit neuem Head;
  Planlauf muss sauber/runtimekompatibel sein. Nicht den alten Diagnose-
  Starter Hugin-Feldtest.cmd mit Head94ee13b verwenden.
- Normales Beenden des Diagnosepilots startet über seinen Supervisor die
  bestehenden Whispering-/PipPal-Startup-lnks. Diese vor dem neuen Pilottest
  normal beenden, damit keine doppelten Kürzel/Modellnutzer aktiv sind.
- Profile/Startup-lnks und alter STT-Standby in dieser Sitzung unverändert.
  Strg+Alt+D/V und Escape bleiben Pilotkürzel. Maus/Alt+Y/Autostartmigration
  folgt auf geprüfte Umstellung. Früherer RAM-Clipboardverlust nicht rückgängig.
- Alle drei alten Helperworktrees entfernt nach eigenem Remote-/Handoffbeweis
  und regulärer Freigabe. Private Remotebranches bleiben erhalten:
  Cues2f045e9fd4e6ba830a843c15bd5b74c35ba4d5a8,
  Range0a534632abdf19de98ee037fbe49ead234c6891d,
  Stream0cccf901d5f70040757f5b065d4680bfb3b3f4e0.

## Open Blockers

Computer Use hat die Google-Probe beendet, weil die aktuelle Browseradresse
auf Windows nicht zuverlässig genug bestimmt werden konnte. Diese automatische
Ablehnung wird nicht umgangen. Echte Google-/Codex-Teil-/Vollauswahl, Cursor,
Fokuswechsel und Schutzfelder bleiben DC-T07; nicht als behoben behaupten.
Zwei frühere automatische Appstarts wurden als blocked by policy abgewiesen,
ohne bekannte allgemeine OS-Regel. Kein indirekter Launch als Umgehung.
Manueller Start funktionierte; keine erneute Diagnose-/Fokus-/Clipboardfrageschleife.

## Pick Up Here

1. Frischen PR10-/Githead und Context-/Handoffblobs lesen. Der aktuelle
   Checkpoint enthält die Feldkorrektur und ihren Nachweis. Kein Merge
   oder Rollout dieser Kandidatenfassung bisher; Ownership bleibt aktiv.
2. Geordnet auf den neuen normalen Kandidaten starten, dann kurze reale
   Cursor-/Teil-/Gesamtauswahl-Abnahme mit Brian ohne Enter. Keine wiederholten Fokus-/Clipboardfragen.
   Keine Produktion/Autostartmigration ohne geprüfte Umstellung behaupten.
3. Nach Feldabnahme private Integration nach frischem exaktem Head-/Review-/
   Checkgate, kontrollierter Teststart/Rückweg und anschließend finale
   Maus-/Alt+Y-/Autostartumstellung gemäß Spec. Kein Zusatzumfang.

## Starter Prompt

Continue valhalla-hq/hugin from handoffs/2026-10-14-pilot-fixes.md. Read AGENTS,
CONTEXT, genau diesen Handoff, PR10 und Git frisch; Lifecycle/Preflight für
codex/hugin-pilot-fixes-mjolnir beachten. Ownership ist aktiv beim Root.
Einfügekandidat ist geprüft und privat checkpointed; laufender Diagnosepilot
ist noch94ee13b und auf diesen Source gepinnt. Nach geordnetem Neustart kurze
reale Feldabnahme fortsetzen. Bestätigte Stimmen/Töne erhalten; Altstack nicht ungeprüft stoppen,
keine gesperrte Computersteuerung umgehen und keinen Testtext absenden.
