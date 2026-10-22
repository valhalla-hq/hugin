# Hugin 1.0.0 — lokaler Produktionsbuild

Stand: 22. Oktober 2026. Privater Offline-Build für Brians bestehenden
Windows-x64-/NVIDIA-Rechner. Öffentliche Verteilung ist nicht freigegeben.
Installer und reguläre Benutzerinstallation sind geprüft. PR47 wurde mit
unverändertem geprüftem Head3009998 nach bestandenen CI-/Review-Gates als
c17b35818b0ac47a0dae6b20b78528ac9d0e74b9 nach Main übernommen. Die saubere
Quellkopie wurde unter InstanceGuard aktualisiert; sämtliche eingefrorenen
Artefaktinputs und ursprünglichen Source-Einstellungen blieben identisch.
Hugin wurde normal aus dem Installationsordner gestartet. Computer Use zeigt
das eigene Fenster „Bereit für dein Diktat“, Modus Lokal, Stimme Freya sowie
die richtigen Maus-/Tastenhinweise. Die App bleibt für Brian geöffnet.

Dieser Markdown-Abschluss ändert keine Programm- oder Installerinputs. PR48 ist
als e82e9a625f897a0eda33479637a3a802bd2d2636 integriert; der zentrale Workspace-
Release wurde am22.10.2026 um13:18Uhr MESZ bestätigt und der alte Arbeitsbaum entfernt.
Nachweise und Original-Sicherungen liegen zusätzlich geprüft im Releaseordner
unter `verification/`, damit sie beim Worktree-Abschluss erhalten bleiben.

Installer: `C:/Users/brian/Hugin-Releases/1.0.0-3b6bc4304a87/`.
Installiert: `%LOCALAPPDATA%/Programs/Hugin/releases/1.0.0-3b6bc4304a87/`.

## Identität und Umfang

- Eingefrorener Artefaktcommit: `3b6bc4304a871c05c98980160b257709db2e2fed`.
- Anwendungsbaum: `4a2c67ae21141f8879de092fc929f6d51d56df34`.
- Release-Manifest SHA256: `c39d033bfbbe3fb729617dd38f147c2f805707e73d58c863e8f358c9e2796083`.
- 40.364 erfasste Programmdateien, 11.596.044.542 Bytes, zuzüglich Manifest.
- Vollständiges privates CPython 3.12.10 mit Tk 8.6.15; 7/21/94 gesperrte
  Distributionen für Controller/STT/TTS. Modelle, CUDA-Dateien, freigegebene
  Stimmen und Originalsignale werden anhand ihrer SHA256-Locks übernommen.
- Keine Entwicklungsumgebung, Paketdownloads oder Administratorrechte nötig.
- Unsignierter lokaler Build; Authenticode meldet `NotSigned`.

Die fünf Installerdateien umfassen zusammen 7.666.086.289 Bytes und müssen
nebeneinander bleiben:

| Datei | Bytes | SHA256 |
| --- | ---: | --- |
| Hugin-1.0.0-Setup.exe | 6107608 | 63b863b0f324cb289833cbdc4d3d5530895bd2fa902b883607e898731b3ca7de |
| Hugin-1.0.0-Setup-1.bin | 2093892352 | 19b26a2332aa0c858b8b5c780df9deb7f78a51d153db0327e0cb4b194322f126 |
| Hugin-1.0.0-Setup-2.bin | 2100000000 | e6d840f669e51d5bf39fbffe7a8585dda8355c1db65be430d82d52d1069fdfd7 |
| Hugin-1.0.0-Setup-3.bin | 2100000000 | 2d032be4a633eaaf87ff49f2584a799146cc5af9b11074a09d11252eaa789fea |
| Hugin-1.0.0-Setup-4.bin | 1366086329 | 98ad9f9bba9127e24cd1afe4d4dd13da8e37baa4184be6e60ea8732e5c911801 |

## Tatsächlich geprüft

- 607 lokale Vertrags-/Integrationstests bestanden, zuletzt in 30,439s;
  Dokumentationsprüfung ohne Befund. Unabhängige Spec-/Standards-Reviews mit
  behobenen Befunden; die Abschlussprüfung nach Reparatur ist ebenfalls grün.
- Echter Offline-Build mit Inno Setup 7.1.0. Die drei privaten Laufzeiten
  importieren aus eigenen Pfaden; echte UIA-Typbibliothek und Dokumentfreigaben
  werden durch die produktiven Loader geprüft.
- Echte Installation im regulären Benutzer-Versionsordner beendet mit Code0
  in 482,367s; Autostart-Ziel und Argument `--background` zurückgelesen.
  Aktivierung und Stimme wurden exakt übernommen; Quellzustand blieb identisch.
- Sechs native Prüfungen aus der installierten Laufzeit bestanden in 3,563s:
  UIA-Feld/Unicode/Markierung, Ressourcen-/Eingabebesitz und zwei vollständige
  normale Hintergrundstarts mit unveränderter installierter Aktivierung/Stimme.
- `Hugin.exe --check-inputs` beendet mit Code0 in 56,384s. Back/Alt+Y,
  Forward/Strg+Alt+V und temporäres Escape werden real unter Windows registriert
  und wieder freigegeben. Kein verbleibender Ressourcenbesitz.
- Echte Wiederholungs-/Reparaturinstallation: Code0 in484,824s. Ein zuvor
  geprüftes, gezielt entferntes eigenes Icon wurde korrekt ersetzt. Geänderte
  Stimme, Aktivierung, Autostartbytes, synthetischer Zustandsmarker und46 echte
  DSP-Cachedateien blieben erhalten. Danach wurde die ursprüngliche Stimme exakt
  zurückgesetzt und nur der eigene synthetische Marker entfernt.
- Nach Reparatur nochmals sechs native Fälle in3,691s sowie die echte
  Launcher-Integritäts-/Eingabeprüfung in62,846s bestanden; keine offenen Owner.
  Insgesamt vier normale Hintergrundstarts mit unveränderten installierten
  Einstellungen. Die zweite Integritätsprüfung lief gleichzeitig mit der
  Auslieferungskopie; ihre Wandzeit ist kein ungestörter Vergleichswert.
- Alle fünf ausgelieferten Installerdateien wurden nach dem Kopieren erneut
  gegen die Build-SHA256-Werte geprüft. Vier `.bin`-Dateien gehören zur `.exe`.
- Erste echte Lesekette nach Installation, vor zusätzlichem TTS-Importtest,
  mit dem normalen produktiven Workerkommando: Freya34/34 und Tyr40/40 Wörter
  passend markiert; beide Engines auf CUDA und vollständig geschlossen.
  Synthetische Texte, stumme PCM-Ausgabe mit gleicher Länge und echter Audiouhr;
  weder Mikrofon noch Zwischenablage oder persönliche Texte verwendet.

| Lesefall | Abschnitte | Erstes Audio | zusätzliche Abschnittslücken |
| --- | ---: | ---: | --- |
| Freya, prozesskalt, kurze Sätze | 2 | 46,629s | 0,97ms |
| Tyr, bereits geladene Engines, Kommasätze | 3 | 2,801s | 0,42 / 0,59ms |

Die Texte und Stimmen unterscheiden sich; dies ist kein Geschwindigkeitsvergleich.
Betriebssystem-Caches wurden nicht kontrolliert. Die gemessenen Übergänge belegen
die Ablaufplanung, keine neue subjektive Hörabnahme.

## Schutz, Rückweg und verworfener Kandidat

Installation und Reparatur verwenden einen exklusiven aktuellen Benutzer-Lock,
authentifiziertes Manifest sowie gehaltene Root-/Verzeichnishandles. Unbekannte
oder geänderte Programmdateien und umgeleitete Verzeichnisse werden abgewiesen.
Negative native Eigentums-/Pfadprüfungen sowie eine echte Inno-Fehlereinrichtung
bestanden; letztere gibt Code11 statt falschen Erfolg zurück. Programmversionen
werden in getrennten Buildordnern installiert. Einstellungen/Sicherungen bleiben
erhalten; fremde Autostarteinträge werden nicht übernommen oder entfernt.

Der frühe Kandidat `9c8ac49320fc` wurde wegen fehlender referenzierter
Freigabedokumente verworfen und lokal klar als nicht freigegeben markiert.
Der jetzige Build exportiert diese Dokumente und prüft die tatsächliche
Konsumentengrenze bereits vor der Paketierung und im installierten Selbsttest.
Seine frühere synthetische Installation wurde regulär deinstalliert: Code0,
32,927s, alle40.333 erfassten Programmdateien entfernt, Einstellungen/Sicherungen
erhalten und ursprünglicher Autostart exakt wiederhergestellt. Der native
Installer-/Deinstaller-Code ist im jetzigen Build unverändert; die finale
Benutzerinstallation wird nicht für eine zusätzliche Deinstallationsprobe entfernt.

Zwei frühere kalte Staging-Proben brachen nahe der alten60s-Ladegrenze ab.
Ein Watchdog-Abbruch ist die führende Hypothese; die genaue auslösende kalte
I/O-Kostenkomponente wurde nicht nachgewiesen. Die begrenzte Bereitschaftsfrist
beträgt jetzt120s, einschließlich dreier IPC-Abschlusswartezeiten. Cancel2s und
Exit5s bleiben unverändert. Der Guard prüft die echten geladenen Werte und sowohl
Überleben nach61s als auch Freigabe bei120s; die frische installierte Lesekette
ist erfolgreich. Es wird keine universelle Kaltstartgarantie abgeleitet.

Die Quellinstallation mit ihren ursprünglichen Einstellungen und Sicherungen
bleibt als Rückweg erhalten. Whispering und PipPal werden nicht zurückgestartet.

## Kosten und Prüfgrenzen

Manuelle Abnahme am22.10.2026: Brian hat Hugin regulär beendet und manuell neu
gestartet. Anschließend bestätigt er alle vier Abläufe erfolgreich: Diktatstart,
Aufnahmeende und automatisches Einfügen sowohl mit hinterer Maustaste als auch
Alt+Y; Vorlesestart und Stopp sowohl mit vorderer Maustaste als auch Strg+Alt+V.
Dies ist eine direkte Nutzerbestätigung der physischen Bedienung, kein neuer
automatischer Testlauf. Die automatischen Messwerte unten bleiben unverändert.

Build: 812,357s Wandzeit (608,109s Installerkompilation), 71,172s Controller-CPU.
Privater Import-/Integritätstest: 45,902s Wandzeit, 26,781s Controller-CPU.
Lesekette: 78,839s Wandzeit, 1,047s Controller-CPU; Workerfamilien zusammen
61,156s CPU. Einzelne gemessene Spitzen der Job-Commit-Größe: TTS8.484.360.192,
STT3.249.823.744 Bytes. Das sind weder gemeinsamer Spitzen-RSS noch GPU-VRAM.
Compiler-/Pip-Gesamt-CPU und Familien-Spitzenspeicher, Installer-CPU/Spitzenspeicher,
Agenttokens und bitidentische Reproduktion sind ungemessen.

Der echte Windows-Login bleibt offen: Heute gab es nur den manuellen App-Neustart.
Brian verschiebt den Anmeldetest wegen laufender Arbeit auf23.10.2026. Dann prüfen,
ob Hugin ohne manuellen Start still im Infobereich läuft und die Belegung auch
nach Anmeldung gilt. Heute weder Abmelden/Neustart noch weitere Tests auslösen.
Breite Geräte-, erhöhte Fremdprozess- oder Zielsoftware-Freigabe und öffentliche
Verteilung werden nicht behauptet.
