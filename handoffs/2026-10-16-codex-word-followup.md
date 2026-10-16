# Hugin: neue Basis, Codex und Word offen

## Objective

Brian bestätigt am16.10.2026 Google-Diktat und Überschreiben am Source25d9c97.
Codex und eine Word-Datei nehmen das Diktat weiterhin nicht an. Er beauftragt
bewusst den Schnitt: bestehende Commits prüfen, PR10 nach Main integrieren und
die beiden offenen Fälle anschließend in einer frischen PR bearbeiten.
Dies ist eine bekannte Zwischenbasis, keine vollständige Produktabnahme.

## Git und Einstieg

- Privates Repository: https://github.com/valhalla-hq/hugin.
- Abschluss-PR: https://github.com/valhalla-hq/hugin/pull/10.
  Vorintegration: main8e4ceabb718edb2c8d1b80e1b07b69e0f3b933bd;
  Google-Pilot25d9c97ce5af41cf866907e99cbbb4572ca3cb77, final geprüfter Source
  052751b2476250bd430f5c6c0272eebc91c5feb2 mit kleinem Launcher-Diagnosefix.
  Der letzte Dokumentcheckpoint enthält diesen Handoff. Merge-SHA, frischen
  Mainhead und Context-/Handoffblobs beim Pickup aus GitHub lesen.
- Runtime Mjolnir; Einstieg C:/Users/brian/Hugin ist Junction zu
  C:/Users/brian/brian-projects/_repos/hugin. Nach Merge sauber fast-forwarden.
- Alter Task: codex/hugin-pilot-fixes-mjolnir unter
  C:/Users/brian/brian-projects/worktrees/hugin/hugin-pilot-fixes-mjolnir.
  Weitere Entwicklung in einem neuen exklusiven Taskworktree von Main.
  Erst nach einem inhaltlichen Folgecommit eine neue Draft-PR öffnen.
- Alte Prüfhistorie: handoffs/2026-10-14-pilot-fixes.md. Aktueller Handoff ist
  dieses Dokument. Nachweis und Commitprüfung: docs/baseline-2026-10-16.md.

## Gesicherter Stand

- Freya/Tyr und Aufnahme-Töne von Brian bestätigt; Audioauftrag abgeschlossen.
- Google-Diktat und Überschreiben von Brian am laufenden25d9c97 bestätigt.
  Keine Behauptung einer separat abgenommenen Google-Gesamtauswahl-/Schutzmatrix.
- 412 Source-/Integrationstests18,399s,94 gezielte Vertragsprüfungen0,463s
  und3 eigene native Range-/IPC-Tests0,837s am Abschlussstand grün. Native Range-Fixture
  misst Cursor, Teil-/Gesamtauswahl und Unicode, ersetzt am eigenen HWND und
  erkennt Auswahlwechsel. Kein Beweis für Word-/Codex-Kompatibilität.
- Private IPC, frische einmalige Attestation, Clipboardfreigabe vor Cleanup,
  Statusdiagnose sowie Feldbesitz unabhängig von Endordnung sind enthalten.
- Der Gesamt-Review fand einen verlorenen dependency_unavailable-Status bei
  fehlendem/fremdem Basisinterpreter. Die gemeinsame Normalisierung beider
  Spawnverbraucher erhält ihn; partielle Prozessowner behalten Cleanupvorrang.
  Sechs öffentliche Gegenfälle zuerst rot, dann grün. Kein Codex-/Word-Fix.
- Kein blindes Paste, keine neue Feld-Whitelist und keine Produktionsbindings-
  oder Autostartmigration. Pilotkürzel bleiben Strg+Alt+D/V und Escape.

## Offener Folgeauftrag

1. Codex: Fehlgeschlagenes Diktat am25d9c97 reproduzieren; Capture- und
   Deliveryphase auseinanderhalten. Ursache und Regression gegenüber früher
   funktionierenden Versuchen sind noch nicht bewiesen.
2. Word: Erstmalig gemeldeter Fehlschlag in einer Word-Datei. Feldart,
   Providerfähigkeiten, genaue Phase und Fehlercode sind noch unbekannt.
3. Für beide: Cursor, Teil-/Gesamtauswahl, unveränderte Umgebung sowie
   Fokuswechsel und Schutzfelder prüfen. Google als funktionierende Regression
   mitnehmen. Keine neue Diagnose-Frageschleife mit Brian; zuerst eigene
   reproduzierbare Proben und vorhandene technische Statuswerte verwenden.
4. Bei einer nötigen Erweiterung des Feldvertrags zuerst die betroffenen
   Fähigkeiten/Identitäten abbilden und Spec präzisieren; keine pauschale
   Freigabe aller Document-Controltypes aus einer Vermutung ableiten.

## Laufzustand und Rückweg

- Neuer normaler Pilot25d9c97 wurde auf Brians ausdrücklichen Wunsch gestartet;
  frische Prozessabfrage bestätigt App/Supervisor. Das Hugin-Fenster reagiert.
- Lokale ignorierte Receipt im alten Worktree:
  .runtime/pilot-session-80dd4b63-870c-43b8-9e8f-b5e10ab69689.json.
  Receipt/PID allein verleiht keine Cleanup-Autorität. Supervisor hält eigene
  Familie über OwnedProcess und startet nach normalem Hugin-Quit die beiden
  unveränderten Whispering-/PipPal-Startup-lnks.
- Die laufende App benötigt den alten Worktree als Sourcepfad. Daher diesen
  und seine ignorierten Runtimeartefakte nicht löschen oder verschieben,
  solange die Sitzung läuft. Laufender Controller bleibt25d9c97; der kleine
  neue Launcher-Diagnosefix wirkt dort erst nach einem Neustart. Rangeproduzent
  und IPC sind unverändert. Folgeentwicklung gehört in einen neuen Worktree.
  Ownership erst passend zur echten
  Laufabhängigkeit freigeben und danach regulär aufräumen.
- Der alte manuelle Starter bindet Source25d9c97 und Main8e4ceab. Nach dem
  Abschlusscommit/Mainupdate ist er absichtlich nicht wiederverwendbar;
  vor einem weiteren Start exakten Head/Runtimebindung erneut prüfen.
  Den älteren Hugin-Feldtest.cmd nicht verwenden.
- Frühere automatische Startablehnungen sind keine aktuelle generelle Sperre:
  der ausdrücklich beauftragte Start25d9c97 per Start-Process gelang. Frühere
  Computer-Use-Ablehnung des Google-Zugriffs wird weiterhin nicht umgangen.
- Unveränderte Startup-lnks, Profile und vorhandene Umgebungen erhalten.
  Ein Rückweg auf Vorintegration8e4ceab ist als Git-Ref erhalten; normale
  Mainänderungen ausschließlich über geprüfte PR, keine direkte Rücksetzung.

## Fortsetzung

Aktuellen Main-/PR10-/Ownership-/Laufstatus lesen; nach bestätigtem Merge einen
neuen exklusiven Worktree mit frischer Branch für Codex/Word verwenden. Noch
keine neue PR nur für einen leeren Branch erstellen. Kein Testtext absenden.
Keine Rohdiktate, Dokumentinhalte, UIA-IDs, Clipboardtexte oder Logs in Git.

## Starter Prompt

Continue Hugin from handoffs/2026-10-16-codex-word-followup.md. Read AGENTS,
CONTEXT, diesen Handoff, PR10 und aktuellen Main frisch. Brian hat Google-
Diktat/Überschreiben bestätigt und den geprüften Zwischenstand ausdrücklich
zur Mainintegration freigegeben; Codex und Word bleiben offene Fehler für
eine frische PR. Keine Gesamtproduktabnahme behaupten. Laufender Pilot25d9c97
benötigt noch den alten Worktree; dort keinen neuen Source entwickeln.
