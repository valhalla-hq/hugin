# Umsetzungsplan

1. Windows: ein einheitliches eingefrorenes Auswahlintervall statt eines
   einzelnen Caretpunkts. Beide UTF-16-Grenzen, Endpoint-Kindidentitäten und
   Affinitätsrelationen prüfen; doppelte Edit-/Focus-Identität entfernen.
   IPC-Version explizit erhöhen, alte Shapes ablehnen, 4092-B-Metadatenlimit
   belegen. Kollabierter Fastpath, Objektfreiheit und finale frische Auswahl/
   Editierbarkeit nach Textaufrufen erhalten. Editierbare UIA-Combobox nur mit
   vollständigen Text-/Value-/Readonly-/Rootnachweisen unterstützen.
2. Root: Agentenkonfiguration auf explizite generische Verified-Edit-Fähigkeit
   umstellen. Appgebundene Restore-Overrides bleiben möglich; Standardwert
   zunächst0,25s im Pilot, erst mit nativen Clipboard-Proben aktivieren.
   Win32-/UIA-Proof ist Voraussetzung, kein Name/Pfad als Editierbarkeitsbeweis.
3. Capture: kurzer eigener PCM-Cue-Owner, getrennt von TTS. Mic zunächst
   unarmed öffnen, Startcue/Drain bestätigen, dann in gemeinsamer Gerätezeit
   arm_after setzen und alte/überlappende ADC-Blöcke verwerfen. Kleinen
   begrenzten Akustiknachlauf nativ prüfen. Stopcue nach Mic.close, vor UIA.
   Cancel erreicht Cue.stop ohne Warten hinter FIFO; Cleanup bleibt besessen.
4. Worker: GPU-Generator auf bisherigem Engineowner, ein separater Writer
   mit höchstens einem wartenden Providerchunk. Auch aktuellen Writer-Chunk
   und bereits erzeugten blockierten Producer-Chunk zählen: maximal drei
   PCM-Chunks à bestehendem1.440.000-B-Providerlimit, also höchstens4.320.000B
   zusätzlich/retained PCM; tatsächliche Kosten messen. Frame-/Client-/native
   Playergrenzen unverändert. Cancel weckt Wartende; kein Terminal vor
   Generatorclose, Writerbarriere und GPU-sync. Kein künstliches Silencefüllen.
5. Engste Guards erst rot; getrennte Helper-Worktrees für Windows, Cue/Capture
   und Worker. Root integriert und besitzt generische Policy/Spec/Review/
   Nativeproben. Keine parallele GPU/Audio/Clipboard-Probe.
6. Reale native Proben mit eigenen synthetischen Feldern/Sprachinhalten,
   darunter Selection-Ersetzen und echte Pipeline statt vorgenerierter WAV.
   Browseroberfläche über CUA; keine Umgehung deaktivierter Native-UI-Tools.
7. Gesamtdiff/Spec und Standards unabhängig reviewen, exakte Hosted-Checks,
   private Integration. Laufenden Pilot normal beenden, Familienabschluss/
   Altstack-Rückstart beweisen, Altapps normal pausieren, sauberen Main
   aktualisieren und geprüften neuen Pilot mit exaktem Receipt starten.

Rollback: unveränderte alte Profile/Startup-lnks; einmaliger Supervisor und
bestehende normale Beenden-Rückkehr. Keine dauerhaften Autostarts ändern.
