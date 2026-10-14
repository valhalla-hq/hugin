# Hugin Audio-Refill Helper Handoff

## Objective

Brian hört beide Stimmen im laufenden Hugin-Pilot stark abgehackt/statisch. Gemeinsamen PCM-/Ausgabepfad offline untersuchen, engsten reproduzierten Fix vorbereiten. Root bearbeitet parallel Codex-Paste und besitzt Integration sowie echte Playback-/Stoppprüfung; sein Worktree bleibt unverändert.

## Git State

- Repository valhalla-hq/hugin, privat; Branch codex/hugin-audio-fix-mjolnir.
- Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-audio-fix-mjolnir.
- Basis main 8c64029c8068a6fe3c58d177a1ed7b0c353ca773.
- Sourcecheckpoint 8aad103bd5174e0b145b46b8557d9b3f0ad9c482, sauber gepusht und ls-remote-identisch bestätigt. Dieser Handoff/CONTEXT folgt als eigener Metadatencommit ohne Sourceänderung.
- Preflight-Control e3deecae6673a024aa9015a4387737fbec04c795.
- PR: keiner, bounded Helper ohne Merge-/Deployautorität. Root cherry-pickt nur den Sourcecommit.
- Ownership aktiv auf Mjolnir bis regulärem project_workspace.py release; nichts löschen, keine venv verschieben oder neu installieren.
- Autorisierter Schreibscope: tatsächlich src/hugin/audio.py (windows/audio.py existiert nicht; Root bestätigte den Pfad), fokussierte Tests, eigener Kontext/Handoff. Application-/Workeränderungen wären vorher mit Root abzustimmen; keine waren nötig.

## Diagnosis And Changed Files

- src/hugin/audio.py: Ein volles 6000B-IPC-Paket ging als ein einziger 125ms-WAVEHDR an die auf 6000B begrenzte native Queue. queued_bytes sinkt erst, wenn ganze Header als DONE zurückkommen. Somit konnte auch schon bereitliegendes Folge-PCM erst nach Queue-Leerlauf eingereiht werden.
- Kleinster Producerfix: Jeder native Write höchstens halbe vorhandene Kapazität, an PCM16 ausgerichtet; bei 125ms 3000B. Der zweite Header bleibt spielbereit, während der erste gesammelt/nachgefüllt wird. Kapazität, Jobidentität, Cancel, native Header-/Datenownership, Drain und Cleanup bleiben beim bestehenden Owner. Kein Packet-/Protokoll-/Applicationumbau, keine größere Queue.
- Microsoft beschreibt die notwendige Vorausfüllung und mindestens zwei Blöcke für kontinuierliche Ausgabe: [Audio Data Blocks](https://learn.microsoft.com/en-us/windows/win32/multimedia/audio-data-blocks). Das stützt den Producerbefund; es ist kein Messnachweis für diesen physischen Treiber.
- Consumer gelesen: Application startet PCMOutput einmal pro Lesauftrag, bestätigt jeden angenommenen Write und drainiert erst am finalen TTS-Terminal. WorkerClient hält maximal ein 6000B-Paket bis Callbackabschluss; WorkerServer wartet auf Credits. Diese Grenzen bleiben unverändert: höchstens 6000B nativer PCM-Vorrat plus 6000B im Client, initial insgesamt 250ms.
- tests/contracts/test_audio.py: deterministischer FIFO mit ganzer Header-Freigabe, beide kleinen bestätigten synthetischen Voice-WAVs, byteexakte Übertragung, Unterlauf-/Kapazitätsprüfung. Weitere Guard für kleine/Restframes, Drain und Stop/alte Jobidentität bei 1/63/125/250ms. Simulation etabliert keine native Treiber-/Provider-/Hörabnahme.
- CONTEXT.md und dieser Handoff sind separat; keine Rootdocs oder fremden Worktrees geschrieben.

## Verification

- Guard zuerst rot: beide Stimmen zeigen sieben modellierte Lücken à 11ms bei 10ms Header-Rücklauf plus 1ms Dispatch, obwohl PCM bereitliegt. Derselbe Guard nach Producerfix grün, Queuepeak höchstens 6000B und PCM byteidentisch.
- 97 fokussierte Tests in 4,381s grün: test_audio, test_application, test_coordinator, test_workers_simulated. Sechs Audiofälle einschließlich Resetfehler und alten Writer/Job-Abbruch. Keine neue Paketinstallation.
- Docs 19 Anforderungen/17 AC ohne Probleme; AST-Syntax und git diff --check grün. Ruff nicht im freigegebenen Controller verfügbar; nicht installiert und keine andere venv benutzt. Keine komplette Source-/Windows-Suite neu behauptet.
- Root lieferte vorhandene synthetische Pilot-WAVs unter C:/Users/brian/Hugin/.runtime/pilot-audio/17b60c74-0a73-4c37-8852-ab530a94fb8d. Beide 24kHz mono PCM16 ohne Vollskalenclipping: Freya 6,08s/291840 PCM-Bytes, Tyr 5,92s/284160 PCM-Bytes. Reine PCM-Metadatenprüfung, nichts angehört oder verändert.
- Vollständiger Offline-Replay dieser WAVs im identischen simulierten FIFO: Basis Freya 48 Lücken/528ms gesamt, Tyr 47/517ms; Fix beide null. Native-Queuepeak bleibt 6000B, größter Header 3000 statt 6000B. Dieselben Bytes/PCM-SHA256: Freya 9f781639e471bd0fff2f352bb3a00de38c99ee32bd57828ff9e65c52dac3d8d0, Tyr b38007fd57b17fffd5b0e101b2232b1b576d86f1ae8b79af3e9c397ddcbb0366.

## Source And Data Boundary

Nur enger Source, Tests und kuratierte technische Metadaten in Git. Vorhandene große WAVs bleiben ignoriert und unverändert. Keine Sprach-/PCM-Payloads, Rawlogs, Modellgewichte, venvs oder Credentials gespeichert. Native CPU/Working-Set-/Stopplatenz und tatsächliche Header-Rücklaufzeiten wurden nicht gemessen. Die Gap-Zahlen sind ausdrücklich simuliert; natürliche Synthesepausen oder langsamere Erzeugung sind kein damit behobener Providerfehler.

## Running State And Open Checks

- Kein echter GPU-/Audio-/Mikrofon-/Input-/Appstop durch diesen Helper. Alle eigenen simulierten IPC-Testfamilien geordnet abgeschlossen; keine Helferdienste.
- Laufender sichtbarer Pilot nicht beeinflusst; aktueller Hardware-/Altstackzustand bleibt Root-verantwortlich und wurde hier nicht verändert oder neu ermittelt.
- Root führt unabhängigen Review, reale Wiedergabe beider Stimmen sowie Stopp/Drain und Headercleanup nach koordinierter Integration aus. Der reproduzierte Producerdefekt ist behoben; die menschliche Symptomabnahme bleibt offen.

## Pick Up Here

1. Root prüft/cherry-pickt ausschließlich 8aad103bd5174e0b145b46b8557d9b3f0ad9c482, Metadaten bleiben separat.
2. Playback/Stopp ausschließlich durch Root koordinieren; dieses Helpercheckpoint startet weder Ausgabe noch Modelle. Keine Paket-/Modell-/Profil-/Autostartänderung.
3. Nach sauberem remote-proven Metadatacheckpoint und Root-Abschluss regulärer Lifecycle-Release; Worktree, Runtime und Caches erhalten.

## Starter Prompt

Continue valhalla-hq/hugin from C:/Users/brian/brian-projects/worktrees/hugin/hugin-audio-fix-mjolnir/handoffs/2026-10-14-hugin-audio-fix.md. Read AGENTS.md, CONTEXT.md, this exact handoff and fresh ownership/Git state. Sourcefix is 8aad103bd5174e0b145b46b8557d9b3f0ad9c482, metadata separate. Root owns integration and all real output/model/Altstack actions; do not act on the running pilot. Preserve existing runtimes/caches. If released, follow the central verified continuation path or open a new exclusive task worktree before edits.
