# Hugin Implementierungsnachweis

Stand 14.10.2026. Kein produktiver Wechsel. Whispering/PipPal, Tasten und
Autostarts bleiben unverändert. Hugin läuft zunächst ausschließlich im Pilot
mit Ctrl+Alt+Shift+F9/F10; normale Eingaben sind bis T011/T012 gesperrt.

## Implementiert und geprüft

- Eigenes privates Repository, Controller-Umgebung, beide unveränderten
  Stimmreferenzen, vollständige Modell-/CUDA-Dateilocks und Paketpins.
- Deterministischer Coordinator: Diktat-Toggle, TTS-Prioritätsabbruch,
  eigenständige GPU-Operationen, Generationen, vollständiges Terminal vor
  Ressourcenfreigabe, zentral geplanter 90-Sekunden-STT-Offload.
- Native Windows-Adapter für Eingaben, Einzelinstanz, gehaltene Jobfamilien,
  Clipboard-Transaktionen, direkten Standard-Edit-Leseweg und begrenzte
  UIA-Auswahl in einer eigenen isolierten Prozessfamilie.
- Kleines Tkinter-/Tray-Interface; Stimmenwechsel, ein RAM-Ergebnis,
  Ablauf/Kopieren/Löschen und Diagnose mit festem inhaltsfreiem Schema.
- Controller verbindet diese Grenzen; nativer Audioreset wird vor neuer
  Aufnahme bestätigt. Worker-Audio bleibt über Credits/Backpressure begrenzt.
- Eigenständige private Worker-IPC mit fragmentierten, gehashten Transkripten.
  Echtes CPU-Whisper wurde im Helper über private IPC und Windows Job Object
  gestartet und mit bestätigtem Familienende geschlossen (7,995 s Startup).
  Noch kein GPU-/Hörnachweis.

## Prüfungen am integrierten Controllerstand

`tools/dev.py check --group all`: zuletzt 252 erfolgreiche Prüfungen, darunter
Verträge und simulierte IPC-/Restore-Integrationsfälle. Simulation ist kein
Nachweis für native Modell-/Hardwareeigenschaften.

`tools/dev.py check --docs`: 19 Anforderungen, 17 AC, keine gefundenen
Zuordnungs-/Link-/Stimm-/Lock-Probleme. Compileall und Git-Diff-Check grün.
`windows --interactive` mit expliziten UIA-/Audio-/Endpoint-Testflags:
44 Prüfungen ohne Skips erfolgreich. Darunter sind ABI-/Producer-Mocks und
eigene native Fixtures; dies beweist keine vollständige produktive Zielmatrix.

Die Controller-Guards liefen zuerst wegen fehlender application.py rot, dann
grün: Initialisierung vor Inferenz, Fremdidentität, Abbruch unmittelbar am
Clipboard-Commit, Reset vor Mikrofon sowie Diagnose/RAM-Ablauf.

Die eigene CPU-Probe durch den integrierten Controller benötigt 13,862 s für
den ersten abgeschlossenen Ablauf: 17 Wörter normalisiert exakt, genau eine
Übergabe an ein RAM-Testziel, danach null eigene Worker und kein offenes
Mikrofon. Kein GPU-/physischer Eingabe-/nativer Clipboard-Nachweis. Spätere
kalte/warme Messung und Grenzen von CPU-/Job-Commit-Zahlen stehen in
[performance.md](../../docs/performance.md). Nach dem Cleanup-Fix wurde der
echte CPU-Ablauf erneut erfolgreich geprüft: 13,125 s, 17 Wörter exakt,
eine RAM-Übergabe, null eigene Worker. Nach Registrierung der PCM-Transfer-
Threads erneut 16,089 s, 17 Wörter exakt und null verbleibende Worker; parallel
liefen Vertragsprüfungen. Dies ist ein Korrektheitsnachweis, kein Latenzvergleich.

Native Geräteproben: kurze Mikrofonaufnahme ausschließlich im RAM, Schließen
bestätigt; waveOut mit synthetischem Null-PCM, Reset/Backpressure/Headers und
Schließen bestätigt. Pilot-Hotkeys/Escape registriert und wieder freigegeben,
Einzelinstanz in einem zweiten echten Prozess geprüft. Versteckter
App-/Tray-Pilot startet und beendet samt Mutex-Freigabe. UI bei 200 Prozent
DPI gerendert und visuell geprüft; ein Größenfehler wurde korrigiert. Ein
verstecktes eigenes RichEdit lieferte über echtes UIA die Unicode-Auswahl,
ohne Fokus oder Zwischenablage zu verändern. Native Registrierung und
Freigabe von IMMNotificationClient sowie sechs kontrollierte VTable-Aufrufe
geprüft; keine echten Geräte umgeschaltet. Physische
Tasten, hörbare Stimmen und DPI 100/150 bleiben offen.

Unabhängige Spec-/Standards-Reviews am festen Stand 8d604bb fanden Rennen
zwischen letztem PCM-Callback und Terminal, eine alte Ready-Frist sowie
Cleanup-/Queue-/Capture-Abschlussfehler. Die produzierenden Grenzen wurden
korrigiert; jeder reproduzierte Fall erhielt einen zuerst roten Guard.
Expliziter Cleanup-Retry erhält die ursprüngliche Ressourcenidentität und
wiederholt keine Textübergabe. Audio-Terminal wartet auf angenommene Blöcke;
Cancel bleibt davon unabhängig. Nachfolgeprüfung und Gesamtpilot bleiben
eigene Gates. Weitere Gegenprüfungen fanden einen verfrühten `closed`-Status
bei fehlgeschlagenem Worker-Kill und einen Abschlussfehler bei lautloser TTS
nach einem alten Audioauftrag. Beide wurden am erzeugenden Owner mit zuerst
roten Guards korrigiert. Worker-Reader und Operations-Scopes geben beendete
Text-/PCM-Nachrichten vor dem nächsten blockierenden Idle-Read frei.
Ein nachfolgendes Domain-Review reproduzierte die verlorene Escape-Bindung
beim Übergang Vorlesen→Diktat. Das Audioreset-ACK läuft jetzt nach Abschluss
des alten Effectbatches über die Eigentümer-Mailbox; der zuerst rote Guard
prüft die aktive Escape-Bindung der neuen Aufnahme.
Fehlgeschlagene und später bestätigte Audioreset-Versuche bleiben getrennte
geordnete Fakten. Fehlgeschlagene Threadstarts, laufende PCM-Transferthreads,
UI-loop-Ausnahmen und unbestätigter Cleanup halten ihre Owner; die
Einzelinstanz wird erst nach Controller- und Fensterabschluss freigegeben.
Zusätzliche Guards wurden jeweils vor dem Fix reproduziert. Build-Umgebungen
binden den endgültigen Pfad; ein Junction darf keine fremde Runtime beschreiben.
Die Venv-Prüfung umfasst innere Umleitungen und die tatsächlichen Pip-
Schreibziele; gelesene Base-Stdlib wird davon getrennt. Ein Hosted-CI-
Fixturefehler durch Windows-Kurzpfade wurde am Fixture-Eingang korrigiert.
Für pystray 0.19.5 hält ein schmaler Adapter native Runner und Setupthread
und bestätigt beide Enden vor Freigabe. Native App-/Tray-Proben bestätigen
dies samt HICON-Freigabe. Teilstart und KeyboardInterrupt behalten den
Windowowner. Ein voller Nutzerpuffer kann Quit nicht verwerfen.
Die UI besitzt zusätzlich ein unabhängiges Stop-Signal. Fehler beim Rendern
und beim Trayabschluss bleiben typisiert und lassen den geordneten Stop-
 beziehungsweise Retrypfad offen. Angezeigte und wartende Python-Textobjekte
werden bei Stop/Fehler freigegeben; ein zuerst roter nativer Weakref-Guard
prüft dies. Keine Aussage über sichere Löschung nativer Caches.

Finales unabhängiges UI-/Tray-Deltareview am Sourcehead `adb4187`: keine
weiteren Befunde; die gemeldeten Queue-/Retry-/Renderfehler sind geschlossen.
Installationspfad-Delta `07c3759` ebenfalls unabhängig ohne offene Befunde.
Die privaten PR-Checks müssen vor Integration am unveränderten finalen
Dokumentcheckpoint erneut grün sein. Dies ist kein T900-Hardware-Gesamtgate.
Die Nachprüfung `f54e156` bestätigt zusätzlich für KeyboardInterrupt und
SystemExit: Typ/Argumente/Owner bleiben erhalten, inhaltsführende Traceback-,
Context- und Cause-Verweise werden vor Speicherung getrennt. Der zuerst rote
Weakref-Guard gibt den abgeschlossenen View frei; kein offener Befund im Delta.

Der Offline-Paketrestore wurde mit allen 122 echten Wheels in drei frischen
Umgebungen geprüft: exakte Versionen und `pip check`, 266,20 s; idempotente
Wiederholung 22,16 s. Socket-blockierte Kindprozesse meldeten null
Netzversuche. Die Modell-/CUDA-Dateien dieser Helper-Probe waren 25-Byte-
Fixtures: ein vollständiger Restore echter Modelldateien und anschließende
GPU-Inferenz sind gesondert nachzuweisen. Beide Source-Wheels wurden erneut
bitidentisch gebaut. [Vertrag und Grenzen](../../docs/offline-restore.md).

Windows-Leistungs-/Geräteereignisse werden über ein eigenes unsichtbares
Fenster und gehaltene COM-Lebenszeiten verarbeitet. Resume/Gerätewechsel
entwerten alte Aufträge und schließen eigene Modellworker. Reale Suspend-,
Geräte- und Explorer-Neustarts bleiben offen.

## Noch keine Abnahme

| Bereich | Offener Nachweis |
| --- | --- |
| AC-001/015 | Physische Maus/Alt+Y, Navigation, aktive Escape-Bindung und Login |
| AC-002/012 | Eigene GPU-Whisper-Inferenz, native CUDA-Cancel-/Cleanup-Fälle |
| AC-003/011 | Echte Zielmatrix Word/Browser/Codex/PDF, Fokus/Caret und Clipboard-Rennen |
| AC-004/006 | Qwen auf GPU mit beiden Stimmen, Hörvergleich und Streaming |
| AC-005/008 | Reale Priorität/Abbruch während nativer GPU-Arbeit |
| AC-007/009/010 | Native UI-Pilot; RAM-/Diagnoseverträge sind separat geprüft |
| AC-013 | Vergleichsmessung kalt/warm mit Altstack, CPU/Familien-RAM und Latenzen |
| AC-014/016 | Vollständig unabhängiger Offline-Restore, Resume/Geräte/Explorer |
| AC-017 | Geprüfte produktive Migration mit Rückweg |

## Präzisierungen aus der Umsetzung

1. Windows-Clipboard-APIs können fremdes verzögertes Rendering auslösen und
   fremde asynchrone Paste-Verarbeitung nicht atomar machen. Automatisches
   Paste und Ctrl+C-Fallback bleiben je Zielklasse bis zum Pilot gesperrt.
   Direkte Auswahl soll bevorzugt ohne Clipboard-Mutation gelesen werden.
2. Ein Leserthread vor nativer DLL-/Modellinitialisierung ließ den echten
   Worker wiederholt hängen. Der Worker liest Initialize auf dem Hauptthread,
   importiert/lädt/wärmt dort vollständig auf und startet erst danach Leser.
   Init-Abbruch benutzt den gehaltenen eigenen Job und dessen Watchdog.
3. Das 250-ms-Ausgabebudget ist geteilt: höchstens 6000 Bytes beim Client und
   6000 Bytes nativ bei PCM16/24 kHz/Mono. Keine unbeschränkte Audio-Queue.
4. Restore darf nur die .runtime eines validierten Hugin-Checkouts additiv
   materialisieren. Ein gemeinsamer Wheel-Artefaktlock prüft Metadaten,
   Versionen, Herkunft und SHA256; Installation ausschließlich lokal,
   `--no-index --no-deps --require-hashes`, ohne Umgebungen zu verschieben.

Diese Präzisierungen ändern die vereinbarten Funktionen nicht. Offene native
Nachweise und eingeschränkte Zielabdeckung bleiben Freigabebedingungen.
