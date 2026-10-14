# Hugin Visual Helper Context

Status: helper checkpoint for parent integration
Owner: Brian; accountable executor `/root`, bounded helper `/root/hugin_windows`
Source truth: `valhalla-hq/hugin`

## Scope

Darstellung im eigenen Task `hugin-visual` auf Mjolnir: Navy/Violett, ruhige
Karten, eigener skalierbarer Rabe. Funktions-, Controller-, Thread-, Tray-
und Text-Lifetimeverträge unverändert. Keine Worker, Modelle, Eingabe-Hooks,
Zwischenablage, GPU oder Altstack-Aktionen in diesem Helper.

## Current State

- Branch: `codex/hugin-visual-mjolnir`; exclusive worktree:
  `C:/Users/brian/brian-projects/worktrees/hugin/hugin-visual-mjolnir`.
- Base main: `e762108bf189ce3428f6fba9cca6f2cbb412a7ce`; preflight control:
  `e3deecae6673a024aa9015a4387737fbec04c795`.
- Source commit: `82c619b706979c6ac6b68c3cf3a4a64dcaf6e8f2`.
  Parent cherry-picks ausschließlich diesen Source-/Testcommit. Diese
  Helfermetadaten gehören nicht in den Integrationsbranch.
- 223 Contracts auch mit Python `-S`, 7 native UI-Prüfungen und Docs grün.
  Eigene synthetische Fenster bei emulierten 100/150/200 Prozent DPI,
  kleinster Fenstergröße und zweizeiliger Diagnose geprüft. Screenshots
  einschließlich Stimmen-Popup unter `.runtime/visual-qa/` gesichtet.
- Native Betriebssystem-DPI-Wechsel und Gesamt-App-/GPU-Pilot bleiben beim
  Parent. Keine neue Dependency und keine fremden Logos/Assets.
- Ownership bleibt aktiv. Parent führt unabhängigen Review und Integration
  in PR <https://github.com/valhalla-hq/hugin/pull/3> durch.

## Active Handoff

- `handoffs/2026-10-14-hugin-visual-helper.md`
