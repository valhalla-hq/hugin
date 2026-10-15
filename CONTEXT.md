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

## Next Step

- Aktiver Task codex/hugin-pilot-fixes-mjolnir, integrierte PR9:
  https://github.com/valhalla-hq/hugin/pull/9. User bestaetigt normalen
  Codex-Alltagspaste; neuer Auftrag: markierte Auswahl ersetzen, allgemeine
  Felder (YouTube/Chrome), zwei Aufnahme-Cues, echtes Streaming korrigieren.
- Change-Vertrag: specs/2026-10-15-hugin-input-audio/. Gepruefter Source
  Core6f4897c und Ton-Nachtrag9a470aca936d3dbc885935229a7eb434d0504c86;
  Root integriert getrennte Helper-
  Slices. UI/Stimmen/Kuerzel/Privacy/GPU-Serialisierung/Rueckweg erhalten.
- UIA-Intervall mit beiden geprueften Originalgrenzen; striktes IPC4/Response3.
  Verified-Edit-Profil0,25s, gemessene Codex-Overrides0,15s; keine Freigabe
  allein durch Appnamen. Native Chrome-Teilreplacement inkl. Clipboardrestore
  und leerer Baseline bestanden. Keine Suche/Enter. Codex-/Vollmatrix offen.
- Zwei eigene Cues + ADC-Gate. MME liefert nativ ADC0: Produzent auf eindeutig
  geprueften Windows-WASAPI-Default/Shared-Konvertierung korrigiert. Native
  Cue-Gate-Probe109Callbacks/31.040B/0alteADCs, Owner geschlossen; kein Audio
  gespeichert. Keine globale/OS-Geraeteeinstellung geaendert.
- Ein Worker-Writer + ein wartender Providerchunk, GPU-Owner unveraendert.
  Reale Kontrollmessung alter Server9/8 leere Refills Freya/Tyr, neu beide0,
  alle PCM-Hashes/Bytes identisch. Cancel und Familienabschluss belegt.
- 390 Source-/Integrationschecks und56 Windowschecks ohne Skips gruen.
  Unabhaengige Spec-/Standards-Paesse; reproduzierter Endpoint-P2 geschlossen.
  Kuratierte Nachweise/Kosten/Grenzen: docs/input-audio-2026-10-15.md.
- Pilotbb700f0 durch Nutzer normal beendet; Supervisorreceipt bestaetigt
  eigenen Familienabschluss und Altstack-Rueckstart. Nutzer hat Whispering/
  PipPal danach normal beendet; frisch keine alten Apps/Qwen beobachtet,
  Profil/Startup-lnks hashidentisch. Alter STT-HTTP-Standby unveraendert.
- PR9 am unveraenderten geprueften Head573ca3fa4c8c9e4d7b09b60772b9de022b66479d
  nach drei gruenen Hostedchecks und frischem Identitaets-/Scopegate regulaer
  integriert. Merge8e4ceabb718edb2c8d1b80e1b07b69e0f3b933bd ist remote auf
  main; Merge-/Headtrees identisch, Sourceancestry bewiesen. Deployment sauber FF.
- Neuer einmaliger Pilot auf genau diesem Main gestartet. Receipt:
  pilot-session-854cec59-a15a-44c1-8373-be2cd39273a8.json. Supervisor41332,
  Appwrapper42772, echte App16336 frisch mit gehaltenen Prozesshandles,
  Image/Creation/Elternkette gebunden. Sichtbares Hugin536x679, eigene Signal-
  /Trayfenster und belegte Instanz bestaetigt. Schema2/generisches Profil/
  zwei Codex-Overrides vorhanden; Startup-lnks und PipPal-Profil hashidentisch.
- Nativer Tk-/Tray-UIA-Leseweg exponiert den Statuswortlaut nicht; daraus
  keine sichtbare Bereit- oder Hoerabnahme abgeleitet. Kuratierter lokaler
  Rolloutbeleg Root.runtime/input-audio-rollout.json, keine Sprachinhalte.
- Dokumentarischer Rolloutcheckpoint: Draft PR10,
  https://github.com/valhalla-hq/hugin/pull/10. Er aendert nur Context, exakten
  Handoff und Aufgabenstatus. Naechster Schritt: Alltagstest mit neuem Pilot;
  Root-Ownership bleibt wegen laufendem Supervisor aktiv. Helperworktrees nach
  bewiesenem eigenen Remotecheckpoint regulaer freigeben.
- Brian meldet nach Wiederholung fluessige Sprache. Auf Wunsch deutlichere/
  lautere Töne: Start115ms tief doppelt, Ende180ms hell aufsteigend.82 passende
  Checks und NativeReplay/Gate114Callbacks/31.680B/0alteADCs gruen.
- Neue Tonabnahme/Cue-Echo und reale Auswahl-Vollmatrix sind Nutzerabnahme im Pilot;
  normale Maus-/Alt+Y-/Autostartmigration bleibt gesperrt. Frueherer Verlust
  eines RAM-Clipboardstands bleibt dokumentiert und ist nicht wiederhergestellt.

## Active Handoff

- `handoffs/2026-10-14-pilot-fixes.md`
