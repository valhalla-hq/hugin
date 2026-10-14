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
- Source commit `59dce8ff4cd3d87c3f586d73551063576d29de96`; Parent nimmt nur
  diesen Source-/Testcommit, keine Helfermetadaten.
- Schnelle native Basis und vollständige UIA-Ergänzung getrennt; endgültige
  UIA-Prüfung genau einmal im Delivery-Worker, widerrufbarer single-use
  fast_commit ausschließlich auf dem Eingabe-Owner.
- Strenges fokussiertes enabled/nonPassword/Edit + Value.IsReadOnly=False
  + TextPattern; kollabierte Auswahl, exakte begrenzte Roundtrips, lokale
  Position relativ zum Edit-Provider statt beweglicher globaler Chatposition.
- Echte readonly Codex-Capabilities und zwei verifizierbare Zielproben grün;
  Paketfamilie am gehaltenen Codex-Rootprozesshandle separat bestätigt:
  `OpenAI.Codex_2p2nqsd0c76g0`. Keine globale Chrome-Freigabe.
- 255 Contracts mit Python -S, 16 gemockte Windows-ABI-Guards, ein echter
  HiddenRichEdit-UIA-Test, docs und diff grün. Vollständige Probe ca. 1,23s;
  Stop+Final sind zwei One-shots, grob 2,5s Probeanteil (kein GPU-/End-to-Endclaim).
- Parent besitzt Application/Approvalconfig/Diagnose/Pasteabnahme; Ownership
  dieses Helpers bleibt aktiv bis explizite Release-Anweisung.

## Active Handoff

- `handoffs/2026-10-14-hugin-codex-target-helper.md`
