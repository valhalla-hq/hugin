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

- Aktiver Task codex/hugin-pilot-fixes-mjolnir: Brian meldet fehlende Codex-
  Übergabe bei unverändertem Ziel und abgehacktes Audio bei beiden Stimmen.
  Vertrag/Plan: specs/2026-10-14-hugin-v1/pilot-fixes.md.
- PR5 bis PR8 sind integriert. Geprüfter Main und aktuell gestarteter Pilot:
  bb700f0469dd3f75007041c430058c5bae368b47. Strg+Alt+D/V und einmaliger
  Rückweg erhalten. Laufzustand vor Eingriffen frisch prüfen.
- Audiofix für beide Stimmen nativ bestätigt: Freya48/Tyr47 leere Refills
  vorher, beide0 nachher, PCM vollständig identisch, alle eigenen Header/
  Handles geschlossen. Modellladen und Übergabeablehnungen werden präzise
  angezeigt. Kuratierte Nachweise: docs/pilot-fixes-2026-10-14.md.
- Source ce0c1cfeb498b31db8fbafc5bf5e38e8b2001396 ersetzt die frühere
  Character-Suche durch begrenzte lokale UTF-16-Präfixlänge, Caret-Kind-ID
  und Endrelation. Präfixzeichen nur kurz im isolierten RAM; keine Inhalte
  im IPC/Diagnose/Git. Objektgrenzen/Unklarheit vor Lesen ablehnen, Auswahl/
  Editierbarkeit nach letztem Textaufruf frisch prüfen.
- Clipboard-Veröffentlichung nach Close normalisiert; unbekannter Owner
  behält den RAM-Snapshot. Zwei exakte Chromium-Herkunftsformate opak sichern;
  unbekannte/OLE-Formate bleiben vor Mutation gesperrt.
- 328 Sourceprüfungen und23 Windowsprüfungen grün; zwei unabhängige Reviews,
  reproduzierte P1/P2 geschlossen. Nachweis: docs/codex-delivery-2026-10-15.md.
- Vollständige native Abschlussproben am Feldanfang UND echten Textende
  bestanden: genau ein Paste, alle Clipboardformate zurück, echter Home-
  Gegenfall abgelehnt, eigenes Literal entfernt, Baseline erhalten und eigener
  Service geschlossen. Warm40,7/42,0ms, Delivery0,476/0,483s; kein Enter.
- Der erste PR7-Pilot erkannte ein reales Diktat, wies Codex aber erneut als
  target_unverified ab. Brian bestätigt das Codex-Nachrichtenfeld. Win32-
  Messung ohne Fokusänderung: Chrome_WidgetWin_1 mit exakter Codex-Familie
  und UIA-Edit. Die bisherige Renderer-Einzelklasse deckte den Alltagspfad
  nicht ab. Keine pauschale Chromiumfreigabe aus diesem Befund ableiten.
- Zwei weitere vollständige native Proben ohne SetFocus für Chrome_WidgetWin_1
  bestanden: Feldanfang/End-Navigation, Restore aller Formate, Home-Gegenfall,
  eigenes Literal entfernt, Baseline/Familienabschluss bestätigt. Warm46,849/
  41,732ms; Delivery0,495/0,490s; kein Enter. Nur technische Receipts im RAM-/
  ignorierten Runtimepfad, keine Diktatinhalte im Repository.
- Review fand eine Nachweislücke: frühere End-Receipts belegten keine positive
  Vorabposition. Zwei zusätzliche Endproben mit eigener synthetischer Basis
  für BEIDE Klassen bestanden: vor Paste Position15, nichtleere Basis/kein
  Platzhalter, Restore/Home-Gegenfall und beide eigenen Literale entfernt,
  ursprüngliche Baseline/Serviceabschluss bestätigt. Widget Warm50,809ms/
  Delivery0,512s, Renderer44,926ms/0,503s. Protokollfrist unverändert; äußere
  Messung enthält Fixture-/Scheduling-Overhead, keine p95-Zusage.
- Integriertes Follow-up PR8 erweitert targets.json ausschließlich um diese
  zweite Codex-Klasse, gleiche exakte Familie und0,15s-Restore; Fallback leer.
  Profil→Service-Regression zunächst rot, danach329 Source-/Integrationschecks
  in25,114s grün. Fremde/fehlende/case-abweichende Familien und dritte Klasse
  bleiben vor Snapshot/Mutation/Paste gesperrt. Source ce0c1cf unverändert.
- PR7-Pilot am 15.10 geordnet beendet, Rückstart und erneute reguläre Pause der
  Altapps bestätigt. Neuer Pilot vom geprüften Main777c91c sichtbar gestartet;
  Sitzungsnachweis durch Root.runtime/current-pilot-fixes-session.txt.
  Profile und beide Startup-lnks hashidentisch. Normale Maus-/Alt+Y-Hooks
  bleiben gesperrt; Hörurteil für beide korrigierten Stimmen fehlt noch.
- PR8 am unveränderten Head3f4efaaf323c005038d6e2cc5e093ea7b9f1b964 nach zwei
  unabhängigen Reviews/drei erfolgreichen Hosted-Checks privat integriert;
  Merge bb700f0, identischer Tree/Ancestry remote bestätigt. Pilot normal
  beendet, eigener Familienabschluss und Altstack-Rückstart bewiesen; Main
  danach FF, alte Apps/Qwen regulär beendet und neuer geprüfter Pilot gestartet.
  Sichtbares Fenster536x679, Statussymbol Bereit, beide exakten Codex-Klassen,
  Profil/Links hashidentisch. Exakter Pointer zuletzt pilot-session-2b3d2475-
  04da-4175-87c1-a49e7825c86e.json; Supervisor41728/Launcher16868/App26056.
  Nachweis Root.runtime/pilot-rollout-final-2026-10-15.json. Vor Wirkung frisch
  binden. Erfolgreiche Alltagsübergabe über echtes Kürzel und Hörurteil offen.
- Eine frühe fehlgeschlagene Probe verlor ihren RAM-Clipboard-Ausgangsstand;
  dieser wurde nicht wiederhergestellt. Spätere Restorebelege gelten separat.
- PR7 https://github.com/valhalla-hq/hugin/pull/7 und PR8
  https://github.com/valhalla-hq/hugin/pull/8 integriert. Laufstand-Checkpoint
  https://github.com/valhalla-hq/hugin/pull/9 auf demselben Branch;
  Root-Ownership bleibt aktiv, laufender
  Supervisor benötigt den Worktree. Mikrofonerkennung beobachtet, erfolgreiche
  Alltagsübergabe nach zweiter Freigabe und Hörurteil Freya/Tyr noch offen.

## Active Handoff

- `handoffs/2026-10-14-pilot-fixes.md`
