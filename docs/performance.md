# Gemessene Pilotkosten

Die folgenden CPU-Werte stammen aus dem früheren Implementierungsstand.
Aktuelle eigene CUDA-Einzelmessungen und ihre Grenzen stehen im
[ersten GPU-Pilot](pilot-2026-10-14.md). Ein fairer Altstack-Vergleich fehlt weiterhin.

Noch kein Altstack-/GPU-Leistungsvergleich. Die CPU-Probe benutzt das
bestätigte synthetische Tyr-Audio (6,48625 s), eigene Modell-/DLL-/Paketdateien
und die reale private Worker-Verbindung über gehaltene Windows-Jobhandles.
Aufnahme und Einfügeziel sind RAM-Fixtures. Keine Sprachinhalte im Bericht.

```powershell
& .runtime/controller/Scripts/python.exe tools/dev.py benchmark --scenario own-cpu --cold-warm
```

Eine Messung vom 14.10.2026 mit zwei abgeschlossenen Aufgaben:

| Kosten | Beobachtet |
| --- | --- |
| Neuer Worker / neues Modell | 20,771 s bis RAM-Übergabe |
| Zweiter Auftrag im residenten Modell | 11,900 s bis RAM-Übergabe |
| Beide Aufträge zusammen | 32,671 s vor anschließendem Shutdown |
| Controller-CPU einschließlich Shutdown | 0,266 s |
| Eigene Workerfamilie, CPU einschließlich Init/Cleanup | 177,234 s über alle Threads |
| Workerfamilie, höchste Job-Commit-Belegung | 4.809.555.968 Bytes |
| Ergebniskontrolle | Je 17 Wörter normalisiert exakt, genau zwei Übergaben |
| Nach Cleanup | Null eigene Worker, kein gehaltenes Mikrofon |

Kalt bedeutet hier einen neuen Prozess und ein neu geladenes Modell.
Windows-Dateicache, andere Prozesse und gleichzeitig laufende
Paketvorbereitung waren nicht kontrolliert. Ein früherer einzelner erster
CPU-Ablauf dauerte 13,862 s. Diese Einzelmessungen erlauben keine p50-/p95-
oder Optimierungsaussage.

`OwnedProcess.metrics()` liest ausschließlich den gehaltenen eigenen Job.
CPU ist die Summe aus User-/Kernelzeit aller zugeordneten Prozesse und wird
vor Handle-Freigabe gesichert. Die Speicherzahl ist Job-Commit und kein
gemessener physischer Working-Set-Peak. Grundlagen:
[Job accounting](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information),
[extended job limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

In diesen CPU-Proben ungemessen: physische Prozessfamilien-RAM-Spitze, Agent-Tokens, GPU-Init/
Inferenz/Residenz/Cancel, physische Eingabe bis Stopp/Aufnahme, erster Ton,
echte Zielübergabe, p50/p95 und vergleichbare Altstack-Aufgaben. Der vollständige
`baseline-and-hugin`-Benchmark bleibt bis zum exklusiven Hardware-Pilot offen.

Am 14.10.2026 wurde der integrierte Main-Stand `cf1c705` mit allen echten
Modell-/CUDA-Dateien und 122 lokalen Wheels frisch am endgültigen Pfad
wiederhergestellt: 279,716 s; Wiederholung ohne Paketneuinstallation 63,824 s.
CPU/Familien-RAM/Agent-Tokens des Restores wurden nicht gemessen. Während
des ersten Restores liefen die kurzen nativen Controllerprüfungen; keine
Vergleichs- oder Optimierungsaussage aus diesen Einzelwerten.

Die anschließende CPU-Probe aus dieser Installation benötigte 18,352 s bis
zur einmaligen RAM-Übergabe, 17 Wörter normalisiert exakt. Controller-CPU
einschließlich Cleanup: 0,203 s; Workerfamilie: 80,094 s CPU und
4.810.272.768 Bytes höchster Job-Commit. Danach null eigene Worker und kein
gehaltenes Mikrofon. Neuer Prozess/neues Modell, unkontrollierter OS-Dateicache,
Altstack weiter aktiv; kein physisches RAM-Peak, p50/p95 oder GPU-Nachweis.
