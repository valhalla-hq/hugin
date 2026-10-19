# Dritter Diktatton: Text eingefügt

Status: von Brian am 19.10.2026 beauftragt; Umsetzung in eigenem Taskworktree
ab dem gesicherten 5137477. Die bereits laufende abgenommene Version behält
ihre beiden vorhandenen Töne, bis eine neue geprüfte Sitzung gestartet wird.

## Ziel

Die vorhandenen Töne melden Aufnahmebeginn und Aufnahmeende. Ein dritter,
kurzer und davon unterscheidbarer Bestätigungston soll melden, dass die
Erkennung abgeschlossen und der Text erfolgreich in das Zielfeld übergeben
wurde. Ein eigener Ton genügt; es wird kein Whispering-Klang übernommen.

## Anforderungen und Abnahme

- CC-001: Ein erfolgreicher Diktatjob spielt den dritten Ton genau einmal nach
  erfolgreicher Textübergabe und Abschluss der Clipboardtransaktion. Maßgeblich
  ist der vorhandene Delivery-Erfolgsvertrag; kein zusätzlicher Paste und kein
  neues Auslesen des Zielinhalts zur Tonsteuerung.
- CC-002: Aufnahmeende und Abschluss der Erkennung allein lösen den Ton nicht
  aus. Bei Abbruch, fehlgeschlagener/geblockter Übergabe oder ausschließlich im
  RAM gehaltenem Ergebnis bleibt er aus. Manuelles Kopieren ist kein erfolgreicher
  automatischer Diktatabschluss.
- CC-003: Start-/Stoppton, Stimmen, Kürzel, RAM-Ergebnis, Clipboardrestore und
  Altstack-Rückweg bleiben erhalten. Der neue Ton verwendet den bestehenden
  begrenzten lokalen Audiopfad, ohne Modell, Download oder Systemklangänderung.
- CC-004: Veraltete/doppelte Completion-Ereignisse erzeugen keine weiteren
  Töne. Neue Aufnahme, Abbruch und Beenden dürfen den Ton unterbrechen; er darf
  nicht in eine folgende Mikrofonaufnahme geraten. Audioressourcen behalten
  bei fehlgeschlagenem Cleanup ihren Owner.
- CC-005: Ein Fehler des Bestätigungstons darf die erfolgreiche Textübergabe
  nicht rückgängig machen, einen zweiten Paste auslösen oder das RAM-Ergebnis
  verwerfen. Er bleibt als technischer Audiofehler diagnostizierbar.

Prüfen: erfolgreicher Ablauf und Reihenfolge, ausbleibender Ton bei Fehler/
Abbruch/RAM-only, doppelte/späte Ereignisse, neue Aufnahme während Ton,
Audiofehler und Cleanup. Danach eigener Hörtest zur Unterscheidbarkeit und
kurzer Diktattest durch Brian. Keine vollständige Produktabnahme daraus ableiten.

## Umsetzungshinweise und Grenzen

Der bestehende lokale Cue-Owner liegt in src/hugin/cues.py; die Übergabe und
deren Ergebnis werden in src/hugin/application.py verarbeitet. Den Produzenten
und die betroffenen Verbraucher vor Umsetzung gemeinsam prüfen. Dies ist eine
Orientierung, kein bereits geprüfter Implementierungsplan.

Neue Entwicklung benötigt einen eigenen exklusiven Taskworktree vom gesicherten
Kandidaten. Der laufende Pilot hängt an seinem bisherigen Sourcepfad; dort
keinen Produktcode oder Diagnosehelfer verändern. Kein Maus-/Alt+Y-/Autostart-
Rollout und keine Änderung der bestehenden Installationen in diesem Auftrag.
