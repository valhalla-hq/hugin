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
5. Aufnahme-/Delivery-Status einmal in begrenzte Diagnosefelder normalisieren,
   passende kurze Fehlermeldungen behalten und gültiges Diktat im RAM erhalten.
   Feldprüfungs-Ausnahmen dürfen gültige Aufnahmebytes nicht verwerfen.
6. Bestehende und neue Guards, echte eigene Pipe-/Prozess-Fixture ohne Fremd-UI,
   getrennte Reviews, Context/Handoff/Tasks und privater Remotecheckpoint.
   Kein Live-Rollout während die neue native Feldmatrix ungeprüft ist.

Risiken: systemweit gemeinsame monotone Windows-/Python3.12-Zeitbasis nativ
prüfen; keine frische Zeit im Client erfinden. Der neue Frischevertrag darf
keinen UIA-Befund oder Prozessabschluss vortäuschen. Daten und alte private
IPC-Shapes fail-closed. Rückweg: unveränderte Mainfassung/Altstack behalten.
