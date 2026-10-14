# Hugin Context

Status: implementation
Owner: Brian
Type: application
Data boundary: Privater Quellcode, kuratierte Konfiguration, Paket-/Modelllocks und bestaetigte kleine synthetische Stimmreferenzen. Keine persoenlichen Diktate, Dokumente, Audioaufnahmen, Credentials, Rohlogs, Modellgewichte oder virtuellen Umgebungen in Git.
Source truth: `valhalla-hq/hugin`

## Goal

Brian hat am 14.10.2026 Spec und Plan unter C:/Users/brian/Hugin/specs/2026-10-14-hugin-v1 erstellt und die schrittweise Umsetzung beauftragt. Kleine native Oberflaeche, XBUTTON2 und Alt+Y fuer Diktat-Toggle, XBUTTON1 fuer Vorlesen-Toggle, Diktat stoppt Vorlesen, beide unveraenderten Stimmen Freya/deutsch-3 und Tyr/deutsch-a. Escape-Abbruch, ein letztes RAM-Diktat mit Kopieren/Loeschen, technische Diagnose ohne Inhalte. Whispering und PipPal laufen bis zur geprueften Umstellung weiter. Lokaler Einstieg C:/Users/brian/Hugin; vorhandene Planungsdateien erhalten und im ersten exklusiven Task uebernehmen.

## Current State

- Private Initialisierung und Katalogregistrierung abgeschlossen. Pilot-PR https://github.com/valhalla-hq/hugin/pull/1 am unveränderten geprüften Head b3ee07cb18b94764a1ea24b56179ae329382b868 integriert; Merge cf1c70570b790211b54ce27e8a93b8e641703d69.
- Restore-/Einstiegsnachweis aus PR2 integriert, main e762108bf189ce3428f6fba9cca6f2cbb412a7ce. Frühere Task-Ownership freigegeben.
- Aktiver Task codex/hugin-style-pilot-mjolnir: Darstellung nach drei Nutzerreferenzen in Nachtblau/Violett und eigenes Raben-Icon, ohne Funktionserweiterung. Erster GPU-/Sprachpilot und sichtbarer Teststart beauftragt; geordnete vorübergehende Altstack-Pause ausdrücklich freigegeben. Siehe specs/2026-10-14-hugin-v1/style-pilot.md.
- Nachtblau-/Violettoberfläche mit eigenem Raben-Icon integriert. 268 Vertrags-/Integrationsprüfungen und 48 Windows-Prüfungen ohne Skips grün. UI, GPU-Probe/Cancel-Racefix und Windows-cuBLAS-Fix unabhängig ohne offene Delta-Befunde geprüft. Nachweise/Grenzen: docs/pilot-2026-10-14.md.
- Main cf1c705 vollständig aus 29 echten Modell-/CUDA-Dateien und 122 lokalen Wheels wiederhergestellt: drei frische Umgebungen, Versionen/pip check grün; Apply 279,716s, Wiederholung ohne Neuinstallation 63,824s. 44 Windows-Prüfungen ohne Skips und echte CPU-Probe aus der finalen Installation grün; GPU-/Hör-/physische Zielmatrix-Abnahme offen.
- C:/Users/brian/Hugin ist ein geprüfter Junction zum sauberen _repos/hugin-Mainclone. Die sechs ursprünglichen Planungsdateien bleiben mit identischen Hashes in C:/Users/brian/Hugin-Planung-2026-10-14 erhalten. Keine venv verschoben.
- Autorisierte Pause über normale Appaktionen bestätigt: Whispering/PipPal und alter Qwen-Worker beendet, PipPal-Profil und beide Startup-lnks hashidentisch. Alter STT-HTTP-Dienst im Standby unverändert. Eigener serieller GPU-Test für Whisper und Freya/Tyr samt Cancel und Familienabschluss erfolgreich. Keine produktive Umstellung oder Gesamtabnahme.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Bounded Helper: Audio-Refill

- Auftrag: stark abgehackte/statische Wiedergabe bei beiden Stimmen untersuchen, engsten PCM-/Playerfix vorbereiten. Eigener Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-audio-fix-mjolnir, Branch codex/hugin-audio-fix-mjolnir, Basis main 8c64029c8068a6fe3c58d177a1ed7b0c353ca773; Preflight-Control e3deecae6673a024aa9015a4387737fbec04c795. Root besitzt Integration und echte Playback-/Stoppprüfung; laufenden Pilot nicht verändern.
- Befund an src/hugin/audio.py: Ein 6000-Byte-IPC-Paket belegte als einzelner WAVEHDR die komplette native 125ms-Queue. Ganze Header werden erst nach WHDR_DONE freigegeben; Nachfüllen wartete deshalb auf eine leere Queue. Kleinster Fix begrenzt jeden nativen Write auf höchstens die halbe vorhandene Kapazität, initial 3000 Bytes. Queuebudget bleibt 6000 Byte nativ plus höchstens 6000 Byte im Client.
- Sourcecommit 8aad103bd5174e0b145b46b8557d9b3f0ad9c482 enthält nur audio.py und test_audio.py. Beide bestätigten synthetischen Stimmen zuerst rot im deterministischen FIFO mit 10ms modelliertem Header-Rücklauf plus 1ms Dispatch; nach Fix grün. Kleine/Restframes, Drain, Resetfehler, Cancel/alte Jobidentität und 1/63/125/250ms Buffergrößen geprüft.
- 97 fokussierte Audio/Application/Coordinator/SimulatedIPC-Tests grün/4,381s; Docs 19 Anforderungen/17 AC, Syntax und Diff grün. Ruff ist im freigegebenen stabilen Controller nicht vorhanden und wurde weder installiert noch über eine andere venv gestartet.
- Beide vorhandenen echten Pilot-WAVs rein offline vollständig durch denselben FIFO gespielt: Freya 291840 Bytes, Tyr 284160 Bytes, PCM jeweils exakt; modellierte Queue-Lücken 48/47 vor Fix, beide null danach. Kein physischer Hör-/Latenz-/Treibernachweis daraus. Die WAVs sind 24kHz mono PCM16 mit normalen Peaks; keine neue Sprachgenerierung.
- Kein Rootworktree-/Runtime-/Paket-/Modell-/Profil-/Autostartedit und keine echte Audio-, GPU-, Mikrofon-, Eingabe- oder Appstopaktion durch diesen Helper. Metadaten werden separat gepusht; Sourcehash bleibt unverändert. Ownership aktiv bis regulärem Release, Worktree/Runtime/Caches erhalten.

## Pilot-Kürzel

- Nutzerauftrag: einfache Tasten ohne Fn. Strg+Alt+D toggelt Diktat,
  Strg+Alt+V toggelt Vorlesen. UI und aktuelle Anleitungen angepasst.
- 268 Vertrags-/Integrationsprüfungen, Dokumentprüfung und echte native
  Registrierung/Freigabe beider neuer Kürzel samt dynamischem Escape grün.
- Die laufende Testsitzung wird nach geprüfter Integration geordnet neu
  gestartet; Rückweg über die unveränderten Altstack-Verknüpfungen erhalten.

## Next Step

- Root prüft und integriert ausschließlich den engen Sourcecommit 8aad103 und koordiniert danach reales Hören beider Stimmen und Stopp/Drain. Der Helper startet keine Ausgabe und stoppt den laufenden Pilot nicht. Anschließend den sauberen gepushten Helper-Metadatacheckpoint regulär freigeben, nichts löschen.

## Active Handoff

- `handoffs/2026-10-14-hugin-audio-fix.md`
