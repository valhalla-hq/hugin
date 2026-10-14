# Hugin UIA Helper Handoff

## Objective

Windows UIA TextPattern.GetSelection als direkten, begrenzten Leseweg ergänzen.
Foreign Provider dürfen den Controller nicht blockieren: eigene held-job Probe,
Deadline/Abbruch und bestätigte Familienbereinigung. Keine globale Capture-
Freigabe, Clipboard-Mutation, Fokusänderung oder Altstack-Migration.

## Git State

- Repository: privat `valhalla-hq/hugin`.
- Branch: `codex/hugin-windows-mjolnir`.
- UIA source commit: `c97cabe`.
- Frühere Sourcecommits: `7d10c31`, `7dad3ad`; frühe Metadaten nicht integrieren.
- UIA-Basis: `dbfa8b86381828174c50fa83c059939b68aaa924` (voriger Helper-Checkpoint).
- Worktree: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-windows-mjolnir`.
- PR: keiner vom Helper; Parent besitzt Haupt-PR1 und Integration.
- Ownership: aktiv auf Mjolnir, nicht freigegeben; kein Merge.
- Autorisierung: expliziter bounded Folgeauftrag des Parent, eigener privater
  Checkpoint; zusätzlich eigene native read-only Fixture nach Parentauftrag.

## Changed Files

- `src/hugin/windows/selection.py`: One-shot SelectionProbe, private begrenzte
  Frames, Deadline/Cancel, Prozess-/Pipe-Ownership mit close/retry.
- `src/hugin/windows/selection_probe.py`: comtypes MTA, generierte OS-Typelib,
  Fokus-/Window-Anker, ein TextPattern-Auswahlbereich, positive GetText-Grenze,
  frische Schutz-/Fokusprüfung und Bereich-/Text-Nachprüfung.
- `src/hugin/windows/clipboard.py`: Nicht-Edit-Directread an Probe anbinden;
  kein impliziter Clipboard-Fallback bei Fehler/Timeout.
- `src/hugin/windows/process.py`: optionales Job-Commitlimit vor Prozessstart;
  Modellworker-Default None unverändert. Parent-Metriken sind in dessen Branch
  separat ergänzt und beim 3-way-Import zu erhalten.
- `tests/contracts/test_windows_selection.py`, Prozess-Guard, ABI-/Native-Tests:
  Semantik, Framing, Schutzfelder, Ressourcenfehler und eigene RichEdit-Fixture.
- `docs/windows-api.md`: API, Ressourcen, Primärquellen und Native-Grenzen.
- `CONTEXT.md`, dieser Handoff: nur Helper-Metadaten, vom Sourcecommit getrennt.

## API / Integration

`NativeClipboard.read_direct_selection` nutzt für eigene Standard-Edit-Ziele
weiter WM_GETTEXT; sonst lazy `SelectionProbe.read(target, cancelled)`.
`ClipboardService.capture_selection` veröffentlicht erst nach erneuter nativer
Ziel-/Cancel-Prüfung. Parent führt den synchronen Capture-Aufruf im separaten
Single-Worker aus, nicht auf dem serialOwner; unmittelbar gesetzter CancelToken
wird alle 10 ms beobachtet. MicStart wartet nicht auf UIA-Cleanup.

Eine Probe besitzt genau einen OwnedProcess mit 256 MiB Job-Commitlimit und
2 s initialer Deadline. Timeout/Cancel: ausschließlich gehaltene Familie killen,
Exit bis 3 s bestätigen, Pipe-Threads mit gemeinsamem 1-s-Budget joinen und
Handles schließen. Bei Fehler bleiben _process/_threads gehalten; weiterer
Read liefert selection_cleanup_pending, close() wiederholt dieselbe Bereinigung.

UIA bindet das fokussierte Element über seine tatsächliche HWND-Root-Abstammung
(max. 64 Eltern); ein Renderer-PID wird nur damit akzeptiert. Nächster
TextPattern-Vorfahre, genau eine zusammenhängende Auswahl, GetText(262145),
max. 256 KiB UTF-8. Kein DocumentRange/ValuePattern/Volltext-Fallback.
CurrentIsPassword, Focus-/RuntimeID-/PID und native Fensteridentität werden
unmittelbar vor jedem GetText geprüft; der umschließende Bereich muss ebenfalls
explizit nicht geschützt sein. Anschließend Auswahlendpunkte/Text/Identität erneut
prüfen. Fehlend, unsicher, veraltet oder mehrfach bedeutet failclosed.

## Dependency / Cache

- Gewählt und im Parent-Controller als installiert gelesen: `comtypes==1.4.17`.
- PyPI-Wheel SHA256: `4e0a221dde2c589b82977bed802efd71cd5eb67a380347b732e02735e597f586`.
- Pin/Installation und Offline-/Hashnachweis bleiben beim Parent.
- Client-Import erst nach kontrolliertem Gen-Namespace unter dem aufgelösten
  Hugin `.runtime/controller`-Prefix; bestehende Namespace-Datei bleibt erhalten.
  Fremde/readonly oder umgeleitete Gen-Pfade fallen vor Cache-Initialisierung aus.
- `gen_dir=None`, `-I -B`; generierte Interfaces nur im Child-RAM. Keine eigenen
  COM-VTables. MTA-Referenzen werden bei normalem Exit gepaart freigegeben.

## Verification

- Parent-Controller: `C:/Users/brian/brian-projects/worktrees/hugin/hugin-v1-mjolnir/.runtime/controller/Scripts/python.exe`.
- `tools/dev.py check --group contracts`: 61 grün (Guard-first zunächst rot).
- `python -m unittest discover -s tests/windows` mit `HUGIN_NATIVE_UIA=1`:
  17 grün = 16 ABI/Producer-Mocks + 1 echte eigene native RichEdit-Fixture.
- Native Fixture: unsichtbares eigenes STATIC/RICHEDIT50W-HWND, synthetische
  Auswahl nur darin setzen, Eigentümer-PID bestätigen, UIA ElementFromHandle,
  GetSelection/GetText/CompareEndpoints mit realem comtypes. Keine fremde
  GetFocusedElement-Auswahl lesen, keine Eingabe injizieren. Vordergrund-HWND
  und Clipboard-Sequence unverändert. Held Job/Framing/Normalexit real geprüft.
- Erstes unsichtbares Standard-Edit meldete TextPattern unsupported; daher die
  explizite RichEdit-UIA-Fixture. Kein Value-/Volltext-Fallback dafür ergänzt.
- Ein Fixture-Lauf: 0,357 s einschließlich eigener Probe; kein p50/p95, keine
  Produktlatenzbehauptung. Native CPU-Zeit/Familien-Commitspitze/Agenttokens
  ungemessen. Parent-Metriken nicht hier dupliziert.
- Docs: 19 Requirements, 17 AC, keine Probleme. Compile/diff/data-boundary grün.
- Native Browser-/Codex-/Word-/PDF-Matrix und echtes erzwungenes UIA-Cleanup
  mit fremdem Sentinel nicht durch diese Fixture bewiesen.

## Boundaries / Running State

Kein Core, ApplicationRoot, UI, Input oder Root-Code verändert. Alter Stack
unverändert; keine produktiven Hooks/Hotkeys/Autostarts, keine Modelle oder
Mikrofone gestartet. Nur eigener native Fixture-Child wurde gestartet und
normal beendet; keine laufende Helper-Probe bleibt. Keine privaten Diktate,
Dokumente, Rohlogs, Credentials, Modellgewichte oder Runtime-Dateien committed.

## Complexity And Remaining Work

Zwei kleine Windows-Module statt eigener COM-ABI: der zusätzliche Aufwand liegt
in einmaligem Prozess-/Pipe-/COM-Lifetime-Ownership. Ein Prozess pro Auswahl
vermeidet einen residenten UIA-Worker und veraltete Providerobjekte, kostet
aber kalten Start/Typelib-Generierung; repräsentative Browserkosten sind offen.
Die native Fixture bestätigt SDK und eigenes TextPattern, ausdrücklich nicht
die produktive Fokus-/Ancestor-Bindung. Delivery-verifizierbare UIA-/Caret-
Identität gehört zum späteren Zielpilot, diese Erweiterung dient TTS-Lesen.

## Pick Up Here

1. Parent importiert `c97cabe` mit 3-way; dessen additive process.metrics()-
   Erweiterung erhalten, Input/Core/ApplicationRoot nicht überschreiben.
2. Offline-Hashpins, Root-API-Integration und unabhängigen Review abschließen.
3. Browser/Codex-Matrix in explizitem eigenen Testprofil prüfen; keine pauschale
   Clipboard-/Delivery-Freigabe und keine Altstack-Umstellung ableiten.

## Starter Prompt

Continue only parent-assigned Windows follow-up in
`C:/Users/brian/brian-projects/worktrees/hugin/hugin-windows-mjolnir`, branch
`codex/hugin-windows-mjolnir`. Read AGENTS.md, CONTEXT.md, this exact handoff,
docs/windows-api.md and current parent messages. UIA source c97cabe is ready
for parent integration; keep its Core/ApplicationRoot and process metrics.
Leave Whispering/PipPal running. No foreign selection/focus/clipboard changes.
Ownership is active; do not merge, create a PR or release it independently.
