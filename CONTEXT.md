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

- `handoffs/2026-10-21-screenshot-formats.md`

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

Brian hat danach den Kandidaten ebe832dc9bda4ae9880dd5c35c425bf414888beb
manuell gestartet. Der Pilot läuft seit 08:28 Uhr am Sourcepfad dieses Tasks;
App/Supervisor sind beobachtet. Am 19.10. bestätigt Brian mehrere erfolgreiche
echte Diktat- und Überschreibtests im zuvor angeleiteten Codex-Test und beauftragt
ausdrücklich das Sichern dieses Zwischenstands. Die Diagnose um 08:30:28 MESZ
meldet native_target_captured/target_captured/submitted, STT bereit auf CUDA,
keinen Fehler und kein offenes Cleanup. Damit ist der aktuelle Diktatdurchlauf
auch sichtbar von Brian bestätigt; die historische Codex-Fehlerursache ist
dadurch nicht rekonstruiert. Keine universelle Feld-/Produktabnahme.

Spätere einzelne Diagnosebeobachtung um 08:35:28 MESZ: audio_failed, IDLE,
weiterhin delivery=submitted und pending_cleanup=false. Die konkrete Audioaktion
ist unbekannt; Brian meldet dazu ausdrücklich keinen wahrgenommenen Audiofehler.
Als Beobachtung behalten, nicht als reproduzierte Ursache oder fehlgeschlagene
Textübergabe interpretieren. Keine zusätzlichen Probeaktionen im laufenden Pilot.

PR11: https://github.com/valhalla-hq/hugin/pull/11 (Draft), funktionaler Commit
70c874f90580e5962074ec663aaa528df23055ce, laufender Kandidat ebe832d; alle drei
Hostedchecks daran grün. Der neue Savepoint ändert nur kuratierte Dokumentation.
Produktcode und lokale Diagnosehelfer des laufenden Pilots bleiben unverändert;
Ownership bleibt wegen der Laufabhängigkeit aktiv. Main bleibt defe3d8.

## Dritter Bestätigungston: Umsetzung am 19.10.2026

Brian beauftragt mit „weitermachen“ die Umsetzung des aufgenommenen dritten
Tons. Neuer exklusiver Worktree:
C:/Users/brian/brian-projects/worktrees/hugin/hugin-completion-cue-mjolnir,
Branch codex/hugin-completion-cue-mjolnir, Basis 5137477f0f1e66408934c13a56b92629431285e5
aus PR11. Ownership auf Mjolnir aktiv; laufender alter Sourcepfad bleibt erhalten.

Implementiert: kurzer eigener Dreiklang mit 180ms PCM nach akzeptiertem
erfolgreichem DeliveryFinished. Kein Ton bei Fehler, Abbruch oder RAM-only;
keine zweite Textübergabe. Separater Completion-Owner hält Escape bis zur
Controllerbestätigung. Audiostart folgt erst der erfolgreichen Eingabereservierung.
Neue Sprachaktion/Abbruch/Quit invalidiert auch den wartenden Ton unmittelbar;
derselbe Capture-Executor hält Cueabschluss vor einer neuen Mikrofonöffnung.
Start-/Endtonbytes, Stimmen, Bindungen und Rückweg sind unverändert.

431 Source-/Integrationstests in 18,216s grün, beide getrennten Reviews ohne
offene Befunde. Native reine Audioprobe und vorhandene native Zero-PCM-Reset-
Prüfung grün; keine neue Aufnahme, GPU-/UI-/Clipboardprobe. Kosten und Grenzen:
docs/completion-cue-2026-10-19.md. Neuer menschlicher Hör-/Diktattest steht aus.
Main bleibt defe3d8; PR11 bleibt Draft. Neuer gestapelter Feature-PR:
https://github.com/valhalla-hq/hugin/pull/12 (Draft), funktionaler Commit
183959e9b5890e5b91924df580d439eb6dd3d35c. Kein Rollout in die laufende Sitzung
und keine Maus-/Alt+Y-/Autostartmigration. Finalen Dokumenthead, CI und den
Planmodus des lokalen .runtime/Hugin-Dritter-Ton-Test.cmd frisch prüfen.

## Deutlich getrennte Klangfarben

Brian hat PR12 gestartet; App und Supervisor seit 09:55:36 Uhr im bisherigen
Completion-Cue-Worktree beobachtet. Diagnose 09:56:26 MESZ: IDLE,
native_target_captured/target_captured/submitted, error_code=null und kein
offenes Cleanup. Brian bewertet den Stand positiv, wünscht aber erheblich
unterschiedlichere Töne. Das ist eine Klangpräzisierung, keine vollständige Abnahme.

Neuer exklusiver Worktree:
C:/Users/brian/brian-projects/worktrees/hugin/hugin-distinct-cues-mjolnir,
Branch codex/hugin-distinct-cues-mjolnir, Basis PR12 bei
380c4ec1bae265578362172e4eca89c35746c12e. Aktive Ownership auf Mjolnir.
Die laufende Version und ihre Helfer bleiben unverändert. Neue PCM-Folge:
zwei dumpfe Startimpulse196Hz/185ms, zwei mittlere Endimpulse660Hz/165ms,
zwei helle Glockenanschläge1568/2093Hz samt unharmonischen Teiltönen/295ms.
Nach Hörfeedback nominale digitale Amplitude aller drei auf15000 verdoppelt,
weiterhin unter Guard16000. Brian akzeptiert die Doppelfolge und beauftragt
Einbau samt anschließendem Test in der App ausdrücklich.
Controller, Auslösezeitpunkte, Abbruch und Cleanup sind identisch zu PR12.
CC-006 ersetzt ausdrücklich die bisherige Erhaltung der Start-/Endtonbytes.

431 Source-/Integrationstests in19,036s, beide getrennten Reviews und native
Ausgabe der gewählten Doppelfolge grün, Owner sauber geschlossen. Hörfolge zum
Vergleich ignoriert in .runtime/Hugin-Klangfolge-Doppeltoene.wav; Hörbeispiel
akzeptiert, echter Diktattest mit neuen Klangfarben steht aus. Details und
Whispering-Referenz: docs/cue-contrast-2026-10-19.md. Main bleibt defe3d8,
PR11/12 bleiben Draft; neuer gestapelter Klang-PR:
https://github.com/valhalla-hq/hugin/pull/13. Finalen Head und CI frisch lesen.
Neuer Pilot wird nach regulärem Ende der vorherigen Sitzung samt Pause der
zurückgekehrten Altapps am geprüften Klanghead gestartet. Tatsächlichen
Laufzustand und eigene .runtime/pilot-session-*.json frisch prüfen.

Der beauftragte Wechsel ist ausgeführt: Brian hat die drei alten Apps regulär
beendet bestätigt; der alte Supervisor meldet exit0/eigene Familie beendet und
Rückkehr ausgelöst. Keine passende alte App mehr beobachtet. Neuer Klangpilot
am geprüften funktionalen Head288c8357df5a31812441bb6e87d8d433f4d53a7e seit
10:13:33 MESZ im aktuellen Klangworktree gestartet. App/Supervisor frisch
beobachtet, UI zeigt Bereit, Diagnose IDLE ohne Fehler/Cleanup; noch kein neuer
Input. Alle drei Hostedchecks am Laufhead grün. Der neue Worktree samt Python-
Helfern ist jetzt ebenfalls eine Liveabhängigkeit; keine Sourceänderung im
laufenden Pfad. Echter Diktat-/Hörtest in der App durch Brian steht aus.

## Originaltöne als neuer Auftrag

Brian wünscht nach der Probe ausdrücklich genau die Originaldateien aus
Whispering. Installiertes Whispering7.11.0 und fixierter Upstreamtag stimmen
überein. Die Synthese wird ersetzt, kein zusätzliches Verdoppeln oder Ändern
der Originalklänge. Neuer exklusiver Worktree hugin-whispering-cues-mjolnir,
Branch codex/hugin-whispering-cues-mjolnir, Basis b58bb60 aus PR13; Ownership aktiv.

Original-MP3s hashgeprüft lokal beschafft, av16.1.0 dekodiert ohne Gain/Kürzung
in vorhandenes PCM24k/mono16. Externe lokale Runtimeassets additiv vorbereitet,
Wiederholung idempotent; keine Fremdaudiodateien in Git. Produktion lädt feste
Größen und Digests vor nativen Besitzern; Dauerdeadline lässt die ganze1,346s-
Glocke zu. Gemeinsame Audio-Schreibgrenze65536Bytes, atomarer vorhandener
Kopierproduzent statt Teilzieldateien. Details: docs/whispering-cues-2026-10-19.md.

438 Tests plus isolierter CLI-Guard, zwei getrennte Reviews und native volle
Originalfolge grün. Vorheriger Doppeltonepilot regulär beendet, Rückkehr bestätigt;
danach keine passenden Altapps beobachtet. Neuer Pilot nach finalem CI-/Plan-
Nachweis starten, echte App-Abnahme offen. Main bleibt defe3d8; keine Migration.

## Clipboard-Ablehnung und erfolgreiche Wiederholung

Originaltonpilot d3fd28df648b577a32c7cc61a6614b58c2206c5d wurde am19.10.
um10:31:53 MESZ gestartet; App/Supervisor weiterhin beobachtet. PR14 enthält
den bestätigten Savepoint5137477 als Vorfahren. Clipboard- und Feldbinder sind
dazu bytegleich. Brian meldete im Codex-Nachrichtenfeld um11:03:47 MESZ:
capture_native/field erfolgreich, delivery=format_unsupported, clipboard_failed,
kein offenes Cleanup. Die Ablehnung liegt vor der Clipboardmutation und Paste.

Nach Diagnosekopie sind nur die vier erlaubten normalen Textformate beobachtet.
Brian bestätigt, dass es wieder funktioniert; dieselbe laufende App meldet
um11:07:35 MESZ submitted, IDLE, keinen Fehler/Cleanup. Keine Sourceänderung,
kein Neustart, kein Rücksetzen und kein Löschen der Zwischenablage durch diese
Diagnose. Exaktes vorher abgelehntes Format nicht mehr vorhanden; unbekannt.
59 gezielte Contracttests und2 simulierte native ABI-Grenztests grün. Keinen
Format-Whitelistfix ohne Reproduktion oder sichere Typzuordnung durchführen.

Separater Diagnosecheckpoint: codex/hugin-clipboard-format-mjolnir, BasisPR14,
Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-clipboard-format-mjolnir.
Nur Dokumentation. Die neue Originalton-Livesitzung hängt weiterhin an ihrem
alten Worktree; dessen Produktcode und Python-Helfer unverändert erhalten.

## Obsidian-Oberfläche mit zustandsabhängiger Bewegung

Brian hat Logo01, Oberfläche/Status03 und Farbe02 ausgewählt und die Umsetzung
mit Animation ausdrücklich beauftragt. Neuer exklusiver Worktree:
C:/Users/brian/brian-projects/worktrees/hugin/hugin-obsidian-ui-mjolnir,
Branch codex/hugin-obsidian-ui-mjolnir, Basis52816b2 aus PR15; Ownership aktiv.
PR16: https://github.com/valhalla-hq/hugin/pull/16. Produktstand d781864 enthält
silbernen Raben, Obsidian-Verläufe, native Sprach-/Textsteuerung, Mikrofonpegel,
Verarbeitungswelle, Vorlesepuls und einmalige bestätigte Einfügeanimation.
Reduzierte Bewegung und unsichtbare Fenster stoppen den Animationstimer.

452 Vertrags-/Integrationstests und27 native UI-/Startupchecks grün; unabhängige
Reviews ohne offene Befunde. Hosted CI fand einen frühen Pillow-Import; nach
Korrektur bestehen alle452 Tests auch ohne Site-Packages. Finalen Checkstatus
am unveränderten PR-Head frisch lesen. Nachweise und gemessene Kosten:
docs/obsidian-ui-2026-10-19.md. Neue echte Diktat-/Vorleseabnahme steht aus.

Der bisherige Originaltonpilot endete regulär mit exit0/eigener Familie beendet;
Altapps wurden zurückgerufen. Der neue Sourcepilot wird mit unveränderten,
hashgeprüften lokalen Helfern vorbereitet. Tatsächlichen späteren Laufstatus in
.runtime/pilot-session-*.json dieses neuen Worktrees frisch lesen; nach Start
ist sein Sourcepfad unverändert zu erhalten. Main bleibt defe3d8, ältere Drafts
unintegriert, keine produktive Bindungs-/Autostartmigration. Originaltöne und
Clipboard-/Feldprüfungen bleiben unverändert. Der frühere unbekannte
Clipboardformatfall gilt weiterhin nicht als reproduziert oder behoben.

## Pause: aktive Kacheln, Stimmfelder und Screenshot-Diktat

Brian bestätigt Logo und Animation des Obsidian-Piloten. Offen sind eine
hellblaue Hervorhebung der jeweils aktiven Diktieren-/Vorlesen-Kachel und die
dunklen Ecken um Freya/Tyr. Die Kachelfarbe ist derzeit statisch; transparente
runde Schaltflächen liegen auf einem abweichenden rechteckigen Hintergrund.
Noch keine Umsetzung dieser Folgeänderungen.

Neuer Bericht: Diktieren nach Screenshot-Anhang im Codexfeld scheitert. Die
beigefügte Diagnose zeigt nur RECORDING ohne Fehler. Letzter gespeicherter
Inputstatus14:04:26 MESZ meldet submitted ohne Fehler; Attachmentkontext unbekannt.
Rein lesend wurden später nur erlaubte normale Textformate beobachtet. Brian
pausiert vor einer erneuten Reproduktion. Ursache und konkretes Fehlerformat
bleiben offen; keine Lockerung der Clipboard-/Feldprüfungen.

Neuer exklusiver Task codex/hugin-ui-screenshot-fix-mjolnir basiert auf dem
unveränderten PR16-Head d395f1e. Dieser Checkpoint enthält nur CONTEXT und den
exakten Handoff handoffs/2026-10-19-ui-screenshot-pause.md. Nach sauberem Push
Ownership über das Workspacewerkzeug freigeben; Checkout für Fortsetzung
behalten. Produktstand und ältere Taskpfade unverändert. Der alte Pilotreceipt
meldet noch running, frische Prozessabfragen bestätigen die frühere Familie
jedoch nicht mehr; normaler Abschluss/Rückkehr unbekannt. Kein App-Neustart oder
Stop durch diesen Folgeauftrag. Arbeit auf ausdrücklichen Nutzerwunsch pausiert.

Pausencheckpoint als Draft-PR17 gesichert:
https://github.com/valhalla-hq/hugin/pull/17.

## Fortsetzung am 21.10.2026

Brian hat den Task wieder aufgenommen; die exakt freigegebene Branch wurde nach
Preflight/Remote-Nachweis regulär zurückübernommen. Ownership bleibt aktiv auf
Mjolnir. Die folgenden Fakten ersetzen den Pausenstatus oben.

Die aktive Diktieren-/Vorlesen-Kachel wird jetzt hellblau hervorgehoben, aus dem
Controllerzustand einschließlich Vorbereitung/Verarbeitung abgeleitet. Idle,
Abbruch und Fehler heben keine Kachel hervor. Runde native Buttons übernehmen
den exakten Elternhintergrund und einen gerundeten Tastaturfokus; dunkle Ecken
um Freya/Tyr entfallen. Logo, Animation und Originaltöne bleiben erhalten.
453 Vertrags-/Integrationstests mit -S sowie 43 gezielte/native UI-Prüfungen
grün; zwei unabhängige Reviews ohne materielle Befunde. Native Vorschauen für
Diktat und Vorlesen visuell geprüft, Skalierungsfixtures 100/150/200% grün.

Die manuelle Screenshotprobe um08:46:21 MESZ scheitert schon bei capture_field:
target_changed, delivery=not_attempted, kein Cleanup offen. Technische Spur:
_field_pattern Zeile168, fehlendes UIA-Feld oder keine bestätigte Tastaturfokus-
Eigenschaft. Das ist kein nachgewiesener Clipboardformatfehler. Später nur
unterstützte Textformate beobachtet; Kopieren der Diagnose hatte ursprüngliche
Screenshotformate bereits ersetzt. Ursache der fehlenden Fokusbestätigung noch
offen, keine Lockerung oder vorgetäuschte Behebung. Brian bestätigt anschließend,
dass der Schreibcursor im Textbereich sichtbar blieb. Der neue lokale passive
Trace unterscheidet deshalb Aufrufstufe und vorhandenen Fokuspointer, ohne
zusätzliche Providerabfragen oder Inhaltszugriff; isolierter Test/Review grün.

Aktuell läuft der unveränderte alte Obsidian-Pilot d395f1e seit08:42:43 MESZ aus
hugin-obsidian-ui-mjolnir. Neuer UI-Stand liegt ausschließlich im Taskworktree
hugin-ui-screenshot-fix-mjolnir. Geprüften Pilotwechsel erst nach sauberem
Checkpoint/CI und regulärem Ende der alten Sitzung samt zurückgekehrter Altapps.
Aktueller Stand und genaue Fortsetzung: handoffs/2026-10-21-ui-refinement.md.

## Nachgewiesener Screenshotformat-Fall am 21.10.2026

Die folgenden Fakten ersetzen den Laufstatus oben. Der UI-Pilot c378743 wurde
nach bestaetigtem regulaerem Ende der vorherigen Apps um09:16:07 MESZ gestartet
und bleibt im Worktree hugin-ui-screenshot-fix-mjolnir unveraendert. Die neue
manuelle Codexprobe um09:17:25 meldet erfolgreiche Feldaufnahme, anschliessend
format_unsupported/clipboard_failed. Das ist von der frueheren Fokusablehnung
zu unterscheiden. Frische technische Enumeration einer Screenshotkopie belegt
PNG, DIB/DIBV5, abgeleitetes Bitmap, zwei History-/Cloudrichtlinien und OLE-
Verwaltungsformate; public OLE liefert PNG als IStream und Bitmap als GDI.

Neuer exklusiver Taskworktree hugin-screenshot-formats-mjolnir, Branch
codex/hugin-screenshot-formats-mjolnir, Basis PR17/c378743. Ownership Mjolnir
aktiv. Die Implementierung bewahrt Bild-/Richtlinienbytes und laesst OLE-
Verwaltungsformate nur nach vollstaendiger, sequenzgebundener Pruefung des
geschlossenen Bildformatsatzes weg. Unbekannte Formate bleiben abgelehnt.
Metadatenhelper begrenzt und besitzgefuehrt, temporaerer Diktattext vom Verlauf/
Cloud ausgeschlossen. Oberflaeche, Animation, Originaltoene und Feldschutz
unveraendert. 462 reine Tests und60 gezielte Checks gruen, getrennte Reviews
ohne Produktbefund. Native Endpruefung und menschliche Abnahme noch offen;
keine Behebung behaupten und laufenden Source nicht aendern.

Details: docs/screenshot-formats-2026-10-21.md. Exakter aktiver Handoff:
handoffs/2026-10-21-screenshot-formats.md. Main bleibt defe3d8; keine Integration
des alten Draftstapels und keine Bindungs-/Autostartmigration.
