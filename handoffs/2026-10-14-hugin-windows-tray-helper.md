# Hugin Tray Helper Handoff

## Scope and Git

Bounded Parentauftrag: native Tray-Ownership nach unabhängigem Review des
pystray-Stop-Producers korrigieren. Keine App-/UI-/Input-/Core-Integration hier.

- Repository: privat `valhalla-hq/hugin`.
- Branch: `codex/hugin-windows-mjolnir`, Mjolnir.
- Worktree: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-windows-mjolnir`.
- Sourcecommit: `8e1e37982f80ea3572212b549da5b80a948217e0`, gepusht.
- Basis: Helpercheckpoint `dcf7fe9fc7de63754791a84f04ef331e67913e89`.
- PR/Integration: Parent besitzt Haupt-PR; Helper erstellt keinen PR/Merge.
- Ownership: weiterhin aktiv; nicht freigegeben.
- Preflight: Control `e3deecae6673a024aa9015a4387737fbec04c795`, Project main
  `e555d7d76045dddde35cdeb2e63ce17f048df559`, aktiver exklusiver Helper bewiesen.

## Producer Finding

Gelesener installierter pystray-0.19.5-Producer: `_base.Icon.stop` postet
`_stop`, joint nur den Setupthread und setzt `_running=False`.
`_win32.Icon._stop` prüft PostMessage nicht. Die tatsächliche NativeLoop räumt
Fenster/Menü/Klasse erst später in `_mainloop.finally` auf; HICON-Release liegt
sonst im Destructor. Ein Rückkehrwert von Icon.stop ist keine Cleanup-Bestätigung.
Ein nativer-freier Repro mit tatsächlichen AST-Stopmethoden und PostMessage=0
bestätigte falsches HuginWindow-closed bei noch lebendem Fake-NativeLoop.

## Source/API

- `src/hugin/windows/tray.py`: `TrayOwner(fresh_icon).start()` und
  `close(timeout=2)`, separate `ready`, `closed`, `error` Fakten;
  `title`, `icon`, `menu` werden an dasselbe gehaltene Icon weitergereicht.
- Jeder Lifecyclefehler ist sanitisiertes `HuginError`, `error.owner` ist der
  gleiche Adapter. Keine Roh-Ausnahmen oder Nutzdaten werden geloggt.
- NativeProducer auf pystray 0.19.5 und `pystray._win32` begrenzt; bereits
  laufende Icons werden nicht übernommen. Kein Methoden-Monkeypatch.
- Eigener bekannter Runner ruft gepinntes `_run`, eigener gehaltener Showthread
  wartet auf genau dessen native Readiness. Kein unbesitzter run_detached- oder
  pystray-Setupthread. Start zeigt nur das eigene Icon.
- Close entwertet Show, joint diesen Thread zuerst, wartet auf eigene native
  Fenster, postet `_stop` unabhängig von `_running`, joint NativeRunner und
  ruft `_release_icon` explizit. Gemeinsamer Wait-/Lock-Budget höchstens 5 s,
  Default 2 s. Close ist nach bestätigter Bereinigung idempotent.
- Bei Postfehler/Timeout/Threadstart-/Releasefehler bleibt derselbe Besitzer
  einschließlich Threads/Icon in einer starken Live-Registry. Retry verwendet
  keine PID-/HWND-Suche und bricht keine Threads gewaltsam ab.
- NativeLoop-Fehler nach teilweise erzeugten Fenstern bleiben mangels sicherer
  Cleanup-Fakten gehalten. Fehler vor jedem Fenster können die bekannte
  Constructor-Klasse sicher freigeben. Kein universeller Recovery-Erfolg.

Root sollte `TrayOwner(pystray.Icon(...))` halten, `.start()` statt
`.run_detached()` und `.close()` statt `.stop()` aufrufen. Root behandelt die
Window-Constructor-Ownership und behält Window/Mutex bei fehlgeschlagenem Close;
die Lifecycle-Ausnahme enthält den Adapter für diesen Fehlerpfad.

## Verification

- Guard-first: Import des fehlenden tray.py zunächst rot, dann grün.
- `tools/dev.py check --group contracts`: 72 bestanden, darunter 11 neue
  Tray-Lifecycleguards (Timeout/Retry, Start-vor-Ready, blockierte Sichtbarkeit,
  gemeinsame Close-Deadline, beide Threadstartfehler, Properties, Ownership).
- Default `unittest discover -s tests/windows`: 23 Fälle, 21 bestanden,
  UIA-/Tray-Native-Opt-ins erwartungsgemäß übersprungen. Fünf neue Producer-
  Mocks prüfen falsches `_running`, Constructor/HICON-Cleanup und Producerpin.
- Separat `HUGIN_NATIVE_TRAY=1` mit Parentcontroller: eigener Tray-Smoke
  bestanden, letzter Lauf 0,176 s. Echte eigene Win32-Loop, zwei eigene Threads
  beendet, eigenes HWND aus pystrayRegistry entfernt, HICON None;
  Vordergrund-HWND und Clipboard-Sequence unverändert.
- Docs: 19 Anforderungen, 17 AC, keine Probleme; Git-Diff-Check grün.
- NativeSmoke ist kein p50/p95, keine Kosten-/Lastmessung und kein Explorer-,
  Suspend-/Resume- oder echter Shell-Fehlernachweis. Agenttokens/CPU/Peak-RAM
  wurden hier nicht separat gemessen.

Nur ein kleines synthetisches eigenes Icon wurde nativ gezeigt/geschlossen.
Whispering/PipPal wurden nicht verändert; keine globalen Eingaben, Mikrofone,
Modelle, fremde Auswahl, Clipboard-Mutation oder Autostarts benutzt. Keine
laufende Probe bleibt. Keine privaten Inhalte, Rohlogs oder Runtime-Dateien
in Git. Diese Metadaten nicht in Root übernehmen; nur Sourcecommit integrieren.

## Next / Starter

Parent integriert/reviewt Source `8e1e379` und verbindet dessen UI-Ownership.
Nach diesem Checkpoint nur den erneut zugewiesenen Ops-Installationspfad-Delta
read-only prüfen; keine weitere Root- oder Produktaktivierung ableiten.

Continue only parent-assigned Windows work in
`C:/Users/brian/brian-projects/worktrees/hugin/hugin-windows-mjolnir`, branch
`codex/hugin-windows-mjolnir`. Read AGENTS.md, CONTEXT.md, this exact handoff and
docs/windows-api.md. Tray source `8e1e379` is ready; Parent owns App/UI integration.
Keep old Whispering/PipPal untouched. No merge, PR or ownership release by helper.
