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
- Darstellungsauftrag umgesetzt: drei Nutzerreferenzen in Nachtblau/Violett und eigenes Raben-Icon, ohne Funktionserweiterung. Erster GPU-/Sprachpilot und sichtbarer Teststart beauftragt; geordnete vorübergehende Altstack-Pause ausdrücklich freigegeben. Siehe specs/2026-10-14-hugin-v1/style-pilot.md.
- Nachtblau-/Violettoberfläche mit eigenem Raben-Icon integriert. 268 Vertrags-/Integrationsprüfungen und 48 Windows-Prüfungen ohne Skips grün. UI, GPU-Probe/Cancel-Racefix und Windows-cuBLAS-Fix unabhängig ohne offene Delta-Befunde geprüft. Nachweise/Grenzen: docs/pilot-2026-10-14.md.
- Main cf1c705 vollständig aus 29 echten Modell-/CUDA-Dateien und 122 lokalen Wheels wiederhergestellt: drei frische Umgebungen, Versionen/pip check grün; Apply 279,716s, Wiederholung ohne Neuinstallation 63,824s. 44 Windows-Prüfungen ohne Skips und echte CPU-Probe aus der finalen Installation grün; GPU-/Hör-/physische Zielmatrix-Abnahme offen.
- C:/Users/brian/Hugin ist ein geprüfter Junction zum sauberen _repos/hugin-Mainclone. Die sechs ursprünglichen Planungsdateien bleiben mit identischen Hashes in C:/Users/brian/Hugin-Planung-2026-10-14 erhalten. Keine venv verschoben.
- Autorisierte Pause über normale Appaktionen bestätigt: Whispering/PipPal und alter Qwen-Worker beendet, PipPal-Profil und beide Startup-lnks hashidentisch. Alter STT-HTTP-Dienst im Standby unverändert. Eigener serieller GPU-Test für Whisper und Freya/Tyr samt Cancel und Familienabschluss erfolgreich. Keine produktive Umstellung oder Gesamtabnahme.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Pilot-Kürzel

- Nutzerauftrag: einfache Tasten ohne Fn. Strg+Alt+D toggelt Diktat,
  Strg+Alt+V toggelt Vorlesen. UI und aktuelle Anleitungen angepasst.
- 268 Vertrags-/Integrationsprüfungen, Dokumentprüfung und echte native
  Registrierung/Freigabe beider neuer Kürzel samt dynamischem Escape grün.
- Die laufende Testsitzung wird nach geprüfter Integration geordnet neu
  gestartet; Rückweg über die unveränderten Altstack-Verknüpfungen erhalten.

## Aktuelle Zwischenbasis und Folgeauftrag

- Brian bestätigt am16.10. Google-Diktat einschließlich Überschreiben am
  laufenden Source25d9c97ce5af41cf866907e99cbbb4572ca3cb77. Codex und Word
  funktionieren laut seiner neuen Probe noch nicht; Ursachen sind offen.
- Er beauftragt ausdrücklich, die vorhandenen Commits vollständig zu prüfen,
  den aktuellen Stand über PR10 nach Main zu integrieren und die offenen
  Fälle anschließend mit einer frischen PR fortzuführen. Dieser Schnitt
  ersetzt die bisherige Bedingung, PR10 erst nach der gesamten Feldmatrix zu
  mergen. Die Produktumstellung selbst bleibt an die Gesamtabnahme gebunden.
- PR10: https://github.com/valhalla-hq/hugin/pull/10. Sieben geprüfte Commits
  seit Main8e4ceabb718edb2c8d1b80e1b07b69e0f3b933bd, zuletzt Source25d9c97.
  Die Gesamtprüfung fand zusätzlich einen verlorenen Dependency-Status beim
  Probestart; Source052751b2476250bd430f5c6c0272eebc91c5feb2 korrigiert diesen
  eng begrenzten Diagnosefehler. Aktuellen
  Merge-/Mainhead und Checkstatus beim Pickup frisch aus GitHub lesen.
- Funktionsumfang: frische einmalige Feldattestation unabhängig vom langsamen
  Prozessabschluss; Clipboardfreigabe vor Cleanup; Capturestatus erhält gültige
  Aufnahmebytes/RAM-Ergebnis; Feldbesitz folgt Enclosures statt Endordnung.
  Nachweise: docs/delivery-completion-2026-10-16.md und docs/baseline-2026-10-16.md.
- 412 Source-/Integrationsprüfungen18,399s,94 gezielte Checks0,463s und3 eigene
  native Range-/IPC-Tests0,837s am Abschlussstand grün. Cursor, Teil-/Gesamtauswahl und Unicode sind im
  Providermodell sowie eigenen Windows-Textfeld geprüft. Das beweist keine
  Codex-/Word-Kompatibilität. Beide Fälle gehören in den nächsten Task.
- Audio, Freya/Tyr und Aufnahme-Töne sind von Brian bestätigt. Keine neue
  Audio-/UI-Funktion. Strg+Alt+D/V und Escape bleiben Pilotkürzel; Maus,
  Alt+Y und Autostart erst nach geprüfter vollständiger Umstellung.
- Laufzustand: neuer normaler Pilot25d9c97 gestartet, App/Supervisor frisch
  beobachtet. Alter Diagnosepilot94ee13b ist beendet. Die laufende Sitzung
  benötigt weiterhin den alten Taskworktree
  C:/Users/brian/brian-projects/worktrees/hugin/hugin-pilot-fixes-mjolnir.
  Dort keinen neuen Source entwickeln und den Pfad bis zum normalen Ende
  erhalten. Die Rückkehr zu Whispering/PipPal erfolgt über den Supervisor.
- Nach dem Merge Main-Deploymentclone sauber fast-forwarden; Worker-/Runtime-
  Inputs sind unverändert. Laufender Controller bleibt25d9c97; der neue
  Launcher-Diagnosefix wird dort erst nach einem Neustart aktiv. Rangeproduzent
  und IPC sind gegenüber25d9c97 unverändert.
  Seine alten Starter sind an alte Head-/Runtimewerte gebunden und müssen vor
  späterem Neustart neu geprüft werden. Weitere Entwicklung in neuem exklusiven
  Worktree ab Main; neue Draft-PR erst nach erstem inhaltlichem Folgecommit.
- Ownership des alten Roots bleibt solange aktiv, wie die laufende App den
  Sourcepfad benötigt. Danach reguläre Freigabe/Bereinigung. Andere alte
  Helperworktrees werden nicht aus einem allgemeinen Aufräumwunsch gelöscht.
- Alte Installationen, Profile, Startup-lnks und STT-Standby erhalten. Frühere
  UI-Werkzeugablehnung nicht umgehen; der spätere autorisierte Appstart war
  erfolgreich. Früherer RAM-Clipboardverlust ist nicht rückgängig gemacht.

## Active Handoff

- `handoffs/2026-10-19-word-document-codex-probe.md`

## Fortsetzung am 19.10.2026

Diese Beobachtungen ersetzen den historischen Laufstatus oben. PR10 ist als
defe3d8f0ef9e564da1936a77b931476cbafc98a integriert; Main frisch geprüft sauber.
Die alte Hugin-Pilotsitzung läuft nicht mehr. Neuer exklusiver Taskworktree:
C:/Users/brian/brian-projects/worktrees/hugin/hugin-codex-word-fix-mjolnir,
Branch codex/hugin-codex-word-fix-mjolnir, aktive Ownership auf Mjolnir.

Word scheitert bewiesen am fokussierten Document ohne ValuePattern. Der neue
gemeinsame Feldbinder fordert dort explizit boolesches IsReadOnly=false auf
Dokument UND Auswahl, einschließlich letzter Bestätigung. Edit/ComboBox bleiben
unverändert. Eigene Word16.0.20430.20146-Probe: Cursor, Teil-/Gesamtauswahl
tatsächlich ersetzt, Clipboardrestoration gemeldet, Prüffamilien geschlossen.
418 Source-/Integrationstests,3 native Tests, Docscheck und beide unabhängigen
Reviews grün. Grenzen/Messungen: docs/word-document-2026-10-19.md.

Codex26.1013.4894.0: Brian hat das leere Nachrichtenfeld manuell fokussiert.
Rein lesende Aufnahme und je5 Bestätigungen bestehen auf Main UND Kandidat.
Der echte Diktatfehler ist weiterhin nicht reproduziert oder behoben. Kein
Codex-Paste/Absenden/automatisches Fokussieren. Weitere Proben müssen den
tatsächlichen Ablauf samt Capture-/Delivery-Status erfassen. Kein neuer Hugin-
Pilot gestartet; eigenes ungespeichertes Word-Testdokument bleibt offen.
Altstack, Profile und Startup-lnks unverändert. Keine Produktionsumstellung.
