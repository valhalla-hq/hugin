# Plan

1. Deadline-Kopplung und verlorene Capture-/Delivery-Gründe zuerst an den
   bestehenden öffentlichen Adapter-/Controller-Seams reproduzieren.
2. Frische Feldattestation besitzt der UIA-Produzent. Private IPC explizit
   versionieren, monotone Zeit strikt parsen. Den finalen Frame und beide
   Pipe-EOFs vor COM-/Native-Cleanup abschließen; Quelle hält dessen Besitz.
   Windows-venv-Redirector umgehen durch denselben geprüften Basisinterpreter
   mit CPython-Launcherkontext; exaktes venv und reale EOFs im eigenen Prozess
   prüfen. Keine persistierte Umgebung oder Änderung der Installation.
3. Deliveryworker bereitet die vollständige Bestätigung vor. Ownerclosure
   verbraucht sie nur einmal und prüft50ms-Frische, aktuelle native Identität,
   Clipboard-Token/Sequence, Nutzer-Modifier und Jobgeneration unmittelbar vor
   Übergabe. Kein zusätzlicher Provider-/Pipewait am Controllerowner.
4. Familie nach Übergabe auf dem Worker beenden/abwarten; keine Kill-/Exit-
   Annahme als Cleanup-Erfolg. Fehlgeschlossene Ressourcen behalten ihren
   Owner für Retry. Ein bekannter Fehlerexit mit vollständig geschlossenen
   Ressourcen bleibt gemeldet, hält aber keinen toten Owner unbegrenzt fest.
   Vor langsamem Unwind den nativen Clipboardlock freigeben; OneShotGate und
   Callbackdetachment vorher abschließen, submitted-Fakt erhalten.
5. Aufnahme-/Delivery-Status einmal in begrenzte Diagnosefelder normalisieren,
   passende kurze Fehlermeldungen behalten und gültiges Diktat im RAM erhalten.
   Feldprüfungs-Ausnahmen dürfen gültige Aufnahmebytes nicht verwerfen.
6. Bestehende und neue Guards, echte eigene Pipe-/Prozess-Fixture ohne Fremd-UI,
   getrennte Reviews, Context/Handoff/Tasks und privater Remotecheckpoint.
   Der eigene Prozessguard läuft zusätzlich in Windows-CI in frischem venv
   ohne pip, Providerpakete, Browser, Mikrofon oder Audio.
   Kein Live-Rollout während die neue native Feldmatrix ungeprüft ist.

Risiken: systemweit gemeinsame monotone Windows-/Python3.12-Zeitbasis nativ
prüfen; keine frische Zeit im Client erfinden. Der neue Frischevertrag darf
keinen UIA-Befund oder Prozessabschluss vortäuschen. Daten und alte private
IPC-Shapes fail-closed. Rückweg: unveränderte Mainfassung/Altstack behalten.

## Korrektur nach der Feldmessung

Die reale Google-Probe scheitert vor Delivery an der Kombination aus eigener
Edit-Enclosure und positiver Endrelation. Chromium155.0.8059.40 verbirgt Kinder
atomarer Textfelder und unterscheidet gleiche Textoffsets durch Affinität.
Der Produzent darf sichtbare Feldidentität deshalb nicht als Textankeridentität
interpretieren. Die widersprüchliche Sonderprüfung entfernen; bestehenden
Enclosure-/Präfix-/Frischevertrag einheitlich verwenden. Tests modellieren
Offset und Affinität getrennt. Ein nackter numerischer Offset außerhalb der
Textlänge mit gleichzeitig eigener Enclosure und abschneidendem GetText ist
kein getreues Chrome-Modell: Chromium normalisiert solche Offsets selbst.
Fremde und unbekannte Bereiche weiterhin über beobachtbare Enclosures prüfen.

Die laufende Diagnosesitzung ist auf eine unveränderte, ignorierte Kopie ihres
Sources94ee13b festgelegt. Neue Sourceänderungen gelangen erst mit dem nächsten
geprüften Start in eine Hugin-Sitzung. Vor der Abnahme: Regressionen, eigene
native Feldmatrix, getrennte Reviews und privater Kandidatencheckpoint.

## Dokumentfelder am 19.10.2026

Den real gemessenen Word-Ablehnungspunkt an der vorhandenen Providergrenze
zuerst rot absichern. Ein gemeinsamer Feldbinder besitzt Controltype,
TextPattern und den zutreffenden Schreibschutzvertrag: ValuePattern bei
Edit/ComboBox, expliziter TextRange-Schreibschutz bei Document. Der bestehende
Rangeproduzent und alle Bestätigungsverbraucher übernehmen diese geparsten
Fakten. Keine zusätzliche Klassenfreigabe, IPC-Version oder neue Eingabeart.
Auswahl, Dokumentbereich und späteste Auswahl nach letzter Textlesung prüfen.
Reale Word-Aufnahme/IPC und einmalige Clipboardübergabe getrennt belegen;
Codex-Ursache erst nach eigener manueller Fokusprobe bewerten. Sourcechecks,
native Regressionen, getrennte Spec-/Standardsreviews und exakter Handoff
vor Kandidatencheckpoint. Keine Autostart-/Mausmigration.
