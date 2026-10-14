# Hugin Codex Target Helper Context

Status: bounded helper checkpoint for Parent integration
Owner: Brian; accountable executor `/root`, helper `/root/hugin_windows`
Source truth: `valhalla-hq/hugin`

## Scope

Enger UIA-Metadatenweg für verifizierbare editierbare Codex-Diktatziele.
Keine Inhalte/Titel/Value/GetText im Metadatenarm; keine reale Paste, Eingabe,
Clipboardmutation, Audio-/GPU-/Altstack-Aktion durch diesen Helper.

## Current State

- Task `hugin-codex-target`, Mjolnir, Branch `codex/hugin-codex-target-mjolnir`.
- Worktree `C:/Users/brian/brian-projects/worktrees/hugin/hugin-codex-target-mjolnir`.
- Base main `8c64029c8068a6fe3c58d177a1ed7b0c353ca773`; control
  `e3deecae6673a024aa9015a4387737fbec04c795`.
- Initialer Sourcecommit `59dce8ff4cd3d87c3f586d73551063576d29de96` bereits
  beim Parent integriert. Reviewfixes separat:
  `2d7976cc5c410954cca9de3922506ba1b556a7de`,
  `3dd42559d29cb182ab20cebd5b6a79b7bda6a458` und
  `fc61601929420d879b1fc0371d08869f65649fef` und
  `add0ed2dd9c403be717962f921a6a798c738b7a6`; Parent nimmt nur
  Source-/Testcommits, keine Helfermetadaten.
- Schnelle native Basis und vollständige UIA-Ergänzung getrennt. Delivery
  hält genau eine transiente Zwei-Stufen-Probe mit initialisierten COMfacts;
  single-use fast_commit auf dem Eingabe-Owner fordert die frische lokale
  Position/Focus/Edit/Root-Identität an, maximal 50ms private IPC inklusive
  EOF/stderr/clean family exit, danach held-Token/native/Modifier/current/
  authorize/SendInput. Kein COM/Provideraufruf auf dem Owner.
- Writer-close-Erfolg und bestätigte Antwort sind getrennte Completionfacts;
  Confirm wartet auf beide innerhalb derselben 50ms, auch wenn Child/EOF
  schneller als die Rückkehr von stdin.close sind. Fehler/Timeout schließen.
- Cleanupfehler behalten Probe/Lease/Threads für Retry; widerrufene Closures
  leeren Callback-/Transaction-/Lease-Referenzen. Legacy-Fakefallback entfernt.
- Strenges fokussiertes enabled/nonPassword/Edit + Value.IsReadOnly=False
  + TextPattern; kollabierte Auswahl, exakte begrenzte Roundtrips, lokale
  Position relativ zum Edit-Provider statt beweglicher globaler Chatposition.
- Echte readonly Codex-Capabilities und zwei verifizierbare Zielproben grün;
  Paketfamilie am gehaltenen Codex-Rootprozesshandle separat bestätigt:
  `OpenAI.Codex_2p2nqsd0c76g0`. Keine globale Chrome-Freigabe.
- 266 Contracts mit Python -S, 27 scoped Targetguards; 16 gemockte ABI-Guards
  und ein echter
  HiddenRichEdit-UIA-Test, docs und diff grün. Vollständige Probe ca. 1,23s;
  Stop+Final initialisieren je eine Probe, grob 2,5s Probeanteil plus Warmconfirm
  (kein GPU-/End-to-Endclaim). Aktuelles Codex-Warmtiming offen: Windows lehnte
  die erlaubte gebundene Foregroundaktivierung ab. UI-Slot an Parent zurück,
  keine weiteren GUIproben ohne neue Freigabe; echtes Paste bleibt Parentaufgabe.
- Parent besitzt Application/Approvalconfig/Diagnose/Pasteabnahme. Helperarbeit
  abgeschlossen; Parent hat regulären Release nach clean/remote/Handoff-Proof
  beauftragt. Verbindlicher Ownershipstatus steht im zentralen Workspace-Record.

## Active Handoff

- `handoffs/2026-10-14-hugin-codex-target-helper.md`
