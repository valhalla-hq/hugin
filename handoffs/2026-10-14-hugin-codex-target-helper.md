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
- Initialer Sourcecommit **`59dce8ff4cd3d87c3f586d73551063576d29de96`**
  bereits beim Parent integriert. Reviewfixes chronologisch separat:
  **`2d7976cc5c410954cca9de3922506ba1b556a7de`**,
  **`3dd42559d29cb182ab20cebd5b6a79b7bda6a458`** und
  **`fc61601929420d879b1fc0371d08869f65649fef`** und final
  **`add0ed2dd9c403be717962f921a6a798c738b7a6`**.
  Nur diese Source-/Testcommits cherry-picken; Helfermetadaten auslassen.
- Kein Helper-PR/Merge. Helperarbeit abgeschlossen; Parent hat Release nach
  clean/remote/Handoff-Proof beauftragt. Workspace-Record besitzt Ownershipstatus.

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
  Token und startet eine transiente `SelectionProbe.begin_delivery(base,cancelled)`
  Lease. Initiale vollständige UIA-Identität muss zum ursprünglichen Ziel passen.
  Danach synchroner `commit(transaction,fast_commit)` wie bisher; Parent marshalt
  nur fast_commit zum Eingabe-Owner. Dieser fordert genau eine frische warme
  Metadatenbestätigung an: neue Focus/Root/Edit RuntimeIDs und neu berechnete
  lokale Position gegen den eingefrorenen Integer, keine mitwandernde Range
  als alleiniger Beweis. Nach erster Messung frisches Editpattern und zweite
  lokale Integerposition/Auswahl prüfen, damit ein Wechsel innerhalb der
  Providermessung ebenfalls schließt. Kein erneuter Ancestorwalk, COMimport,
  Text-/Valuezugriff.
- `DeliveryLease.confirm()` signalisiert gehaltene private IO-Threads und wartet
  maximal 50ms insgesamt einschließlich Antwort, EOF, stderr-Barriere und sauberem
  Familienexit. Keine Pipe-Reads/Writes oder COMcalls direkt auf dem Owner;
  Timeout/Cancel/Unbekannt bleiben geschlossen, kein Nativefallback. Danach
  Owner-Nachchecks von sequence/Clipboardowner/Größe/Inhalt am gehaltenen
  Token-HGLOBAL, native Basis/Modifier/current/authorize/SendInput ohne Ownerqueue.
  Kein OpenClipboard/GetClipboardData auf dem Eingabe-Owner.
- Writer-close-Erfolg und Response/EOF/stderr/Familienexit sind unabhängige
  Completionfacts. Confirm wartet auf beide innerhalb derselben 50ms, sodass
  eine schnelle Childantwort vor stdin.close-Rückkehr keine falsche Ablehnung
  erzeugt. _sent bleibt nach erfolgreichem close; Closefehler wird nicht grün.
- Worker hält Clipboardlock bis OwnerACK, Widerruf und `lease.close()`/bestätigtem
  Probeabschluss. Fehlgeschlagener Abschluss behält Probe/Lease/Threads und meldet
  `target_cleanup_failed`; Probe.close kann denselben Owner später erneut schließen.
  Closures sind single-use, vor Clipboard-Release widerrufen und leeren dabei
  current/authorize/transaction/Lease-Referenzen. Gespeicherte LateClosures halten
  keine Inhaltscallbacks. Ohne commit bleibt direkter synchroner Aufruf möglich.
- Produktions-Fallbacks nur für alte Fakeadapter entfernt; Fakes erfüllen dieselbe
  native/full API. Kein Test-Kompatibilitätszweig im Produkt.
- Neue Ergebnisse: target_probe_failed/timeout/busy, target_cleanup_failed/pending,
  target_unverifiable/changed, dependency_unavailable, cancelled.

## Verification

- Ursprüngliche Guard-Datei zuerst rot; nun 27 Target/Owner/IPC/Family-Guards,
  P1 staleCaret/staleEdit und P2 Callback-Inhaltsretention zuerst rot/grün. Dazu
  warme neue lokale Position trotz mitwandernder Range, kein Ancestorwalk,
  Deadline/Cancel/Single-use, nonzero/trailing/stderr, failed cleanup mit Retention
  und Retry, Tokenwechsel nach Confirm und genaue Cleanupstatusableitung. Weiterhin
  globale Chatausgabe versus lokaler Caret, Auswahl/Fokus/Processwechsel,
  Passwort/Readonly/disabled, degraded units, bounds/malformed frames,
  Cleanupretention, Ownerthread, Single-use/LateCommit und Restore bei Ablehnung.
- Ordering-P2 am öffentlichen Probe/Lease-Seam zuerst rot/grün: EOF/valide
  Antwort vor Writer.close-Rückkehr, Freigabe innerhalb Deadline -> captured,
  Closefehler -> failed, keine Freigabe -> timeout. Keine native Runtimeaktion.
- `python -S tools/dev.py check --group contracts`: **266 pass**.
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
- Native Warmconfirm noch nicht bestätigt: bekannte Codex-Paketidentität gültig,
  genau ein enabled/nonPassword Edit mit CSS-Token ProseMirror gefunden (CurrentClassName
  enthält weitere CSS-Klassen, deshalb kein exakter Stringvergleich fürs native QA).
  Fremdes Foregroundfenster und UIA SetFocus ergaben keinen stabilen aktiven
  Codex-Fokus; die ausdrücklich erlaubte gebundene SetForegroundWindow-Anfrage
  wurde von Windows abgelehnt. Kein positiver Timingclaim; keine Texte gelesen.
  UI-Slot an Parent zurückgegeben, weitere GUIproben nur nach neuer Freigabe.

## Primary References

- [GetSelection: degenerate insertion point](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextpattern-getselection)
- [MoveEndpointByUnit and coarser-unit fallback](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-moveendpointbyunit)
- [Edit control and Value.IsReadOnly](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-supporteditcontroltype)
- [GetPackageFamilyName](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagefamilyname)
- [AppModel identity limits](https://learn.microsoft.com/en-us/windows/win32/appxpkg/identity-constants)

## Boundaries And Running State

Keine echte Clipboard-/Paste-/Tastatur-/Mausinjektion/Audio-/GPU-/Altstack-Aktion
des Helpers. Ausdrücklich erlaubte UIA-/Window-Fokusanfragen siehe Nachweis oben.
Keine fremden Inhalte, Titel oder rohen Providerfehler gelesen/gespeichert.
Die einmalige Parent-Erlaubnis für UIA SetFocus wurde bei der Warmmessung versucht;
stabiler eigener UIA-Fokus war nicht nachweisbar, entsprechend kein blinder Restore.
Weitere GUI-/Fokus-/Timingaktionen nach Slotrückgabe gesperrt bis Parentfreigabe.
Nur technische readonly Metadaten und eigene synthetische Fixturetexte.
Ignored Diagnose-Skripte unter `.runtime/target-qa/` bleiben erhalten; keine
Probes laufen weiter. Parent autorisiert abschließenden regulären Release nach
remote-proven clean checkpoint; kein Cache-/Worktree-/Runtime-Löschen.

Offen: unabhängiger Parent-Review/Hostedchecks, App-Future-/Owner-Integration,
Family-Approval und tatsächliche synthetische Codex-Pasteprobe. Große globale
Providerpositionen über 262144 Einheiten, nichtkollabierte Auswahl sowie
fehlende/unsichere Patterns bleiben fail-closed.

## Starter Prompt

Read AGENTS.md, CONTEXT.md und diesen exakten Handoff. Parent integriert nur
die vier getrennten Reviewfix-Sourcecommits nach dem bereits integrierten 59dce8f
in seinem exklusiven Worktree, führt Review und koordinierte Codex-Pasteabnahme
durch. Helper hat
keine Root-App-/Config-/Audio-/Deploymentautorität. Nach freigegebenem Workspace-
Record nicht weiter schreiben; Runtimeartefakte erhalten. Root besitzt finale
native Warm-/Pasteprobe nach Nutzerbereitschaft des leeren aktiven Composers.
