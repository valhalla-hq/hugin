# Hugin: Originaltöne aus Whispering

## Objective und Git

Brian beauftragt ausdrücklich Originaldateien aus Whispering7.11.0 statt der
synthetischen Doppeltöne. Separate Umsetzung und neuer App-Test, kein Produktrollout.

- Repository valhalla-hq/hugin, privat; Mjolnir.
- Control-Preflight e3deecae6673a024aa9015a4387737fbec04c795.
- Branch codex/hugin-whispering-cues-mjolnir, aktive exklusive Ownership.
- Worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-whispering-cues-mjolnir.
- Basis codex/hugin-distinct-cues-mjolnir bei b58bb60ddac4e50db823bd5efae751925d73a2c6.
- Main/Deployment unverändert defe3d8f0ef9e564da1936a77b931476cbafc98a.
- Neuen gestapelten PR und finalen Remotehead über diesen Branch frisch lesen.
  Ein Commit kann seinen eigenen zukünftigen Dokumenthash nicht vorwegnehmen.
- Autorisierung: Originaltöne benutzen und in Hugin testen. Keine produktive
  Maus-/Alt+Y-/Autostartumstellung, Veröffentlichung oder Lizenzumschreibung.

## Ergebnis und Dateien

Produktionssynthese vollständig entfernt. cues.py lädt drei lokale externe
PCM-Dateien nach fester Größe/SHA256. Audioowner besitzt die gemeinsame
65536Bytes-Schreibgrenze; tatsächliche PCM-Dauer plus500ms ersetzt die zu
kurze alte500ms-Deadline. Application lädt vor nativen Besitzern. Sonstige
Delivery-/Escape-/Abbruch-/Cleanupsemantik identisch zur geprüften Basis.
tools/prepare_cues.py verarbeitet lokale geprüfte Original-MP3s mit av16.1.0
und dem bestehenden atomaren copy_locked-Produzenten. Keine neuen Pakete oder
Netzwerk im Lauf. Tests, Spec/Plan/Tasks und docs/whispering-cues-2026-10-19.md
geben Identitäten, Dateinamen, Grenzen und Decoderrezept an.

Originale im ignorierten .runtime/whispering-originals dieses Tasks; externe
fertige PCM samt NOTICE unter C:/Users/brian/Hugin/.runtime/cues/whispering-v7.11.0.
Keine Fremdaudiodateien, persönlichen Diktate, Modelle oder Rohlogs in Git.
Private lokale Nutzungsvorbereitung, keine pauschalen Weiterverbreitungsrechte
aus dem Upstream-Repository ableiten. Quellen und Rechtehinweise im Nachweis.

## Verification

438 Source-/Integrationstests in19,461s plus neuer isolierter CLI-Guard grün;
finalen Hostedcheck lesen. Beide unabhängigen Reviews ohne offene Befunde nach
struktureller Korrektur: atomar publizieren und denselben Outputbound verwenden.
Native komplette Originalfolge0,409/0,527/1,379s erfolgreich; eigene Familie
geschlossen und kein Cleanup offen. Lokale Vorbereitung und Wiederholung
ohne Änderung vorhandener verifizierter Dateien bestätigt. App-Abnahme offen.

## Running State

Der vorherige Doppeltonepilot288c835 aus dem anderen Worktree wurde regulär
beendet; Supervisor meldet exit0, eigene Familie beendet und Altstack-Rückkehr.
Danach keine passenden Hugin-/Whispering-/PipPal-Apps mehr beobachtet. Den
tatsächlichen Laufzustand vor Start frisch lesen; Source/Helfer früherer Tasks
nicht verändern oder entfernen. Neuer Pilot ist erst nach sauberen Checks und
genauem Planmodusnachweis zu starten. Rückweg bleibt der vorhandene Supervisor
mit geprüften Startupverknüpfungen. Keine Cleanupautorität aus PID ableiten.

Vorheriger Doppeltonepilot meldete audio_failed bei submitted, Cleanupfalse;
konkrete Aktion/Ursache unbekannt. Nicht als Abnahme oder bewiesene Ursache
der neuen Originalklänge umdeuten. Früheres eigenes Word-Testdokument nicht
geschlossen; dessen aktueller UI-Zustand unbekannt.

## Pick Up Here

1. AGENTS, CONTEXT, diesen Handoff, aktuellen PR/CI und Livezustand lesen.
2. Nur falls keine Vorgängersitzung/Altapps aktiv sind, neuen geprüften
   Originaltonpilot mit unverändertem Runtimeroot und normalem Rückweg starten.
3. Brian mit Strg+Alt+D kurz diktieren lassen; Originalstart, Originalstopp
   und vollständige Glocke erst nach sichtbarem Einfügen prüfen. Kein Enter/Absenden.
4. Nutzerabnahme getrennt von Source-/Nativechecks dokumentieren.

## Starter Prompt

Continue Hugin from handoffs/2026-10-19-whispering-cues.md. Brian explicitly
wants original Whispering7.11.0 sounds. They are verified local external PCM,
not Git audio assets; synthesis is removed. Check the stacked PR/CI and current
live state, verify the exact-head pilot and existing runtime assets, then test
the originals in Hugin. Preserve source/helper dependencies and old-stack return.
