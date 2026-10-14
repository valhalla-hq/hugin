# Darstellung und erster GPU-Pilot

Auftrag 14.10.2026: Die drei vom Nutzer gezeigten Referenzen bestimmen die
Darstellung: dunkles Nachtblau, blaue/violette Lichtakzente, ruhige Karten und
ein eigenes Hugin-Icon. Nur der Stil wird übernommen, keine fremden Logos,
Navigation oder zusätzlichen Funktionen. Der bestehende Funktionsvertrag gilt.

## Abnahme und Plan

- **S001 / AC-007:** Native kleine Oberfläche in Nachtblau/Violett; Status,
  Stimmen, Kurzbefehle, RAM-Diktat und Diagnose bleiben gut lesbar und
  bedienbar. Sichtprüfung mit synthetischen Inhalten bei 100/150/200 Prozent
  DPI. Kein neuer UI-/Web-Framework und keine zusätzliche Paketabhängigkeit.
- **S002 / AC-007:** Eigenes skalierbares Rabenzeichen für Fenster und Tray.
  Im kleinen Tray bleiben Zustände sichtbar unterscheidbar. Assets sind
  eigenständig gezeichnet; keine Kopie des Referenzlogos.
- **S003 / AC-009/010/015:** UI-Ereignisse, Texte im RAM, Abbruch, Sichtbarkeit,
  Thread-/Trayabschluss und Einzelinstanz behalten ihre bestehenden Verträge.
  Vorhandene Vertrags- und native UI-Prüfungen bleiben grün.
- **P001 / AC-002/006/012/013:** Echte lokale GPU-Worker seriell prüfen:
  Whisper mit bestätigtem synthetischem Audio kalt/warm/Offload/Wiederladen,
  Qwen mit Freya/Tyr und Abbruch. CPU-Fallback gilt nicht als GPU-Nachweis.
  Jede Familie muss vor dem nächsten Engine-Slot bestätigt geschlossen sein.
  Hörvergleich und physische Zielmatrix bleiben eigene menschliche Nachweise.
- **P002 / OPS-002/003:** Nutzer hat die vorübergehende geordnete Pause von
  Whispering/PipPal für diesen Pilot ausdrücklich erlaubt. Keine erzwungene
  Beendigung, Profil-/Autostartänderung oder produktive Migration. Vor der
  Pause Startwege/Identitäten prüfen, nach dem Pilot den bestehenden Stack
  über dieselben Startwege wieder verfügbar machen. Der sichtbare Hugin-Pilot
  benutzt weiter ausschließlich Ctrl+Alt+Shift+F9/F10 ohne Maus-Hook.

Reihenfolge: UI/Branding und begrenzte Probe vorbereiten; relevante Guards
prüfen; bestehenden Stack geordnet pausieren; seriellen GPU-Pilot ausführen;
unabhängigen Spec-/Standardsreview und Hosted-Checks schließen; privat
integrieren, sauberen Mainclone aktualisieren und sichtbaren Pilot starten.
Produktive Maus-/Alt+Y-Aktivierung bleibt T011/T012 und gesondertem Nachweis
vorbehalten. Keine Gesamt-Abnahme aus Teilprüfungen ableiten.

## Aufgaben

- [ ] T020 S001/S002: Darstellungsanpassung und Icon mit nativer Sichtprüfung.
- [ ] T021 S003: Bestehende UI-/Cleanupverträge gegenprüfen.
- [ ] T022 P001: Kleine synthetische Probe und serieller Hardwarelauf.
- [ ] T023 P002: Geordnete Pilotpause, sichtbarer Teststart und Rückweg.
- [ ] T024: Review, CI, Integration und ehrlicher Prüf-/Übergabestand.
