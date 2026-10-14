# Hugin Codex Target Helper Handoff

## Objective

Engste sichere UIA-Unterstützung für das unveränderte Codex-Diktatfeld.
Parent besitzt Application, Fehlerabbildung, Approvalconfig, Audio-Koordination
und tatsächliche Pasteabnahme. Helper ändert ausschließlich Windows-Producer
und direkte Vertrags-/ABI-Tests, keine Pakete/Locks/Modelle oder Root-Dokumente.

## Git State

- Repository `valhalla-hq/hugin`, Task `hugin-codex-target`, runtime Mjolnir.
- Branch `codex/hugin-codex-target-mjolnir`.
- Worktree `C:/Users/brian/brian-projects/worktrees/hugin/hugin-codex-target-mjolnir`.
- Base main `8c64029c8068a6fe3c58d177a1ed7b0c353ca773`.
- Control preflight `e3deecae6673a024aa9015a4387737fbec04c795`.
- Source commit **`59dce8ff4cd3d87c3f586d73551063576d29de96`**.
  Cherry-pick nur diesen Source-/Testcommit; anschließende Metadaten auslassen.
- Kein Helper-PR/Merge. Ownership aktiv bis expliziter Parent-Release.

## Diagnosis And Producer Rule

Win32 liefert im Codex-Hostfenster keinen nativen Caret und kein EM_GETSEL;
das bisherige Ziel blieb damit unabhängig von Approval unverifizierbar.
Readonly gemessen: fokussierter enabled/nonPassword UIA Edit, ValuePattern
mit IsReadOnly=False, TextPattern/Single und kollabierte Auswahl. TextPattern2
fehlt, deshalb sind nichtkollabierte Bereiche zunächst bewusst unverifizierbar.

Chromium kann MoveEndpointByUnit aus dem lokalen Edit-DocumentRange in das
Gesamtdokument bewegen. Globale Offsets drifteten bei laufender Chatausgabe,
die lokale Position blieb 0. Der Producer subtrahiert daher den Edit-Start,
prüft beide begrenzten Charakter-Roundtrips exakt und bestätigt Auswahl,
Focus/Root/Edit RuntimeIDs sowie native Prozess-/Windowfacts erneut. Kein
DocumentRange.GetText, Value, Select, SetFocus oder Providerfehlertext.

## Interfaces

- `WindowTarget` additive `uia: UiaTargetIdentity|None`, `package_family: str|None`;
  `.without_uia` ist die einzige native Basisprojektion. UIA-Identität enthält
  Focus/Root/Edit RuntimeIDs, Focus-PID und lokale kollabierte Einfügeposition.
- Service/Backend `capture_native_target()` ist schnell und UIA-frei. Service
  liefert `native_target_captured` plus Basis, ohne Verifizierbarkeitsbehauptung.
- `capture_target(*, expected=None, cancelled=...)` ergänzt diese Basis im
  bestehenden held-job Probeprozess; `expected` bindet die schnelle Basis.
  Probe und TTS lesen ausschließlich `capture_native_target` (keine Rekursion).
- `SelectionProbe.capture_target(base,cancelled)` nutzt einen getrennten
  kleinen v2-Metadatenarm. TTS v1-Textarm/COM-Lifetime und Cleanup bleiben erhalten.
- `approve_target_class(class,delay,*,package_family=None)` keyed `(class,family)`;
  scoped Einträge erfordern exakte AppModel-Family, unbekannt ist None.
  Explizite alte unscoped Edit-Aufrufer bleiben möglich. Keine Freigabe gesetzt.
- `deliver(...,authorize=...,commit=None)`/`commit_paste(...,commit=None)`:
  vor Staging nur native Basis/Approval; Worker prüft unter Clipboardlock
  Token und vollständige UIA genau einmal, ruft `commit(transaction,fast_commit)`
  synchron auf. Parent marshalt nur fast_commit zum Eingabe-Owner. Dieser macht
  native Basis/Modifier/current/authorize/SendInput, keine UIA/Wait/OpenClipboard.
  Closure ist single-use und vor Clipboard-Release widerrufen; späte Aufrufe
  bleiben gesperrt. Ohne commit bleibt der direkte synchrone Aufruf möglich.
- Neue Ergebnisse: target_probe_failed/timeout/busy, target_cleanup_failed/pending,
  target_unverifiable/changed, dependency_unavailable, cancelled.

## Verification

- Neue Guard-Datei zuerst rot; 16 Target/Owner/IPC/Family-Guards grün, darunter
  globale Chatausgabe versus lokaler Caret, Auswahl/Fokus/Processwechsel,
  Passwort/Readonly/disabled, degraded units, bounds/malformed frames,
  Cleanupretention, Ownerthread, Single-use/LateCommit und Restore bei Ablehnung.
- `python -S tools/dev.py check --group contracts`: **255 pass**.
- Windows ABI-Produzententests: **16 pass**, ausschließlich gemockte OS-Calls.
- Eigener HiddenRichEdit-UIA-Test: **1 pass**, echte COM/held-job-Kette ohne
  fremde Auswahl, Fokuswechsel oder Clipboardmutation.
- `python -S tools/dev.py check --docs`, `git diff --check`: grün.
- Zwei readonly vollständige Codex-Zielproben lieferten verifiable/UIA/local=0,
  eigene Familien bestätigt geschlossen. Native Basis 0,019–0,076ms;
  volle One-shot-Probe jeweils ca. 1,23s. Zwei Proben pro Diktat bedeuten grob
  2,5s Probeanteil; kein gemessener Gesamt-Diktat-/GPU-/Paste-Latenzclaim.
- Echte Family separat am gehaltenen bekannten Codex-Prozesshandle bestätigt:
  GetPackageFamilyName -> `OpenAI.Codex_2p2nqsd0c76g0` (27 WCHARs inkl. NUL).
  Produktcode nutzt AppModel-Fakten am Rootprozesshandle, keine Pfadheuristik.

## Primary References

- [GetSelection: degenerate insertion point](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextpattern-getselection)
- [MoveEndpointByUnit and coarser-unit fallback](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-moveendpointbyunit)
- [Edit control and Value.IsReadOnly](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-supporteditcontroltype)
- [GetPackageFamilyName](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagefamilyname)
- [AppModel identity limits](https://learn.microsoft.com/en-us/windows/win32/appxpkg/identity-constants)

## Boundaries And Running State

Keine echte Clipboard-/Paste-/Input-/Audio-/GPU-/Altstack-Aktion des Helpers.
Keine fremden Inhalte, Titel oder rohen Providerfehler gelesen/gespeichert.
Einmalige Parent-Erlaubnis für UIA SetFocus wurde nicht benötigt/verwendet.
Nur technische readonly Metadaten und eigene synthetische Fixturetexte.
Ignored Diagnose-Skripte unter `.runtime/target-qa/` bleiben erhalten; keine
Probes laufen weiter. Ownership bleibt aktiv, kein Cache-/Worktree-Löschen.

Offen: unabhängiger Parent-Review/Hostedchecks, App-Future-/Owner-Integration,
Family-Approval und tatsächliche synthetische Codex-Pasteprobe. Große globale
Providerpositionen über 262144 Einheiten, nichtkollabierte Auswahl sowie
fehlende/unsichere Patterns bleiben fail-closed.

## Starter Prompt

Read AGENTS.md, CONTEXT.md und diesen exakten Handoff. Parent integriert nur
Sourcecommit 59dce8ff4cd3d87c3f586d73551063576d29de96 in seinem exklusiven
Worktree, führt Review und koordinierte Codex-Pasteabnahme durch. Helper hat
keine Root-App-/Config-/Audio-/Deploymentautorität. Aktuelle Ownership bis
expliziter Freigabe behalten, Runtimeartefakte erhalten.
