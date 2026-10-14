# Pilotkorrekturen vom 14.10.2026

## Erster Diktatstart

Whisper wird beim ersten Diktat und nach dem konfigurierten Idle-Offload neu
initialisiert. Der bisherige echte CUDA-Pilot maß 5,026/4,964 Sekunden für
Initialisierung, gegenüber 0,807/0,507 Sekunden für die Erkennung desselben
17-Wort-Texts. Das erklärt einen langsameren ersten Lauf; aktuelle einzelne
Nutzerlaufzeiten wurden nicht aufgezeichnet. Die vorhandene Statusanzeige
unterscheidet jetzt „Whisper wird geladen“ von der Erkennung. Modell-/GPU-
Serialisierung und die 90-Sekunden-Offload-Regel bleiben erhalten.

## Gemeinsame Audioaussetzer

Ein voller 6000-Byte-WAVEHDR blockierte Nachfüllen bis zum vollständigen
Leerlaufen der nativen Gerätequeue. PCMOutput teilt denselben Puffer jetzt
in höchstens 3000-Byte-Header. Der zweite Header spielt weiter, während der
erste nachgefüllt wird. Kein neuer Puffer und keine Stimm-/Modelländerung.

Nach einem zuerst roten, deterministischen FIFO-Guard für beide Stimmen wurde
derselbe Ablauf mit dem tatsächlichen Windows-waveOut-Player verglichen.
Quelle alt: main 8c64029; Quelle neu: Audiofix 8aad103/49145d5. Ausschließlich
die vorhandenen synthetischen Pilot-WAVs; keine Mikrofonaufnahme und keine
neue GPU-Inferenz. Der Probeplayer zählt Queue=0 beim Nachfüllen bereits
vorhandener PCM-Daten, prüft vollständige Byte-/Hashgleichheit und schließt
alle eigenen Header/Handles.

| Stimme | PCM / Dauer | Leere Queue alt → neu | Laufzeit alt → neu |
| --- | --- | --- | --- |
| Freya | 291840 Bytes / 6,08 s | 48 → 0 | 6,905 → 6,084 s |
| Tyr | 284160 Bytes / 5,92 s | 47 → 0 | 6,697 → 5,921 s |

Maximale native Queue jeweils 6000 Bytes, größter neuer Header 3000 Bytes.
Native Null-PCM-Resetprobe bestanden, inklusive Prüfschwelle unter 300 ms und
beendeter Writer-/Headerownership. Dies belegt Queue-/Samplekontinuität und
Cleanup; ein menschlicher Hörvergleich bleibt ein eigener Nachweis.

## Codex-Übergabe

Zwei Ursachen reproduziert: anfangs leere Delivery-Freigabe und fehlende native
Caret-/EM_GETSEL-Fakten für Chrome_WidgetWin_1. Der Controller stellte auch
ungeprüfte/unprüfbare Ziele und Clipboardfehler fälschlich als Zielwechsel dar.
Neue UIA-Metadaten prüfen das konkrete editierbare Element, Runtimeidentitäten
und seinen lokalen Einfügepunkt, ohne Texte/Value/Dokumenttitel zu lesen.
Chromium lässt Character-Bewegung über den Feldanfang hinaus zu; deshalb wird
der lokale Ursprung abgezogen. Laufende Chat-Ausgabe ändert den Einfügepunkt
dadurch nicht. Nichtkollabierte Auswahlen ohne aktiven Caret-Nachweis bleiben
unprüfbar.

Native readonly Providerprüfung: Codex 26.1007.9446.0, tatsächlicher Prozess
ChatGPT.exe im OpenAI.Codex-Paket. Windows AppModel bestätigt die Familie
OpenAI.Codex_2p2nqsd0c76g0. Eine künftige Freigabe bindet diese Familie und die
exakte native Klasse; andere Chromium-Anwendungen werden damit nicht freigegeben.
Die tatsächliche reversible Composer-Pasteprobe ist noch offen: ein vorhandener
Entwurf wurde erkannt und blieb unangetastet. Delivery-Konfiguration bleibt bis
zum erfolgreichen Nachweis leer. Kein Test darf eine Nachricht absenden.

Review fand zusätzlich eine Lücke zwischen UIA-Prüfung und gemarshalltem Commit
sowie gehaltene Callback-Inhaltsreferenzen nach Widerruf. Diese Befunde müssen
vor Integration geschlossen sein. Der endgültige Commit und native SendInput
bleiben auf demselben seriellen Owner. Lange Provider-/Restore-Arbeit läuft
außerhalb dieses Owners; eigene Deliverytickets sichern Submit-/Shutdownfälle.
