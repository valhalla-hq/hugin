# Codex-Übergabe: lokale Cursorprüfung

Stand15.10.2026; Sourcec3bacfd4233eb0ab3a73dacefb6807d45cd86551,
Basis46e6a40a75f9e4889efeb731c8329d76a800242e.

## Ursache und Korrektur

Der bisherige UIA-Rundweg bewegte Range-Endpunkte über den globalen Chatprefix
zurück und wieder vorwärts. Während Chat-Ausgabe konnte er ein unverändertes
Feld ablehnen und die warme Bestätigung überschritt ihr50ms-Limit.

Die Positionsidentität beginnt jetzt am konkreten Edit-Anfang. Gleiche
Anfangsendpunkte beweisen Position0 direkt. Für andere Positionen sucht der
Produzent begrenzt vorwärts und verlangt einen exakten Rückweg. Er verwendet
nur die Ordnung von CompareEndpoints, keine angenommene Zeichen-Distanz.
Die lokale Grenze bleibt262144; die frühere globale Prefixgrenze entfällt.
Bei unbekannter/instabiler Position bleibt das Ziel unprüfbar. Kein GetText,
Value, Select oder Refokus im produktiven Metadatenpfad.

## Verifikation

- Zwei neue Producer-Guards zuerst rot, dann grün.312 Vertrags-/Integrations-
  prüfungen grün(23,082s), darin29 Targetcontracts.
- Eigener nativer HiddenRichEdit-Test und16 Windows-ABI-Verträge grün,
  ohne Fokus-/Clipboardänderung durch den nativen UIA-Test, keine Skips.
- Zwei unabhängige Reviews ohne konkrete offene Befunde. Zusätzliche
  Boundaryprüfung über4621 lokale Positionen/Grenzfälle: höchstens37
  Move-Aufrufe je Messung, kein Rückweg vor den Edit-Anfang.
- Reale readonly Codex-Prüfung, PaketfamilieOpenAI.Codex_2p2nqsd0c76g0:
  initialer Nachweis0,364/0,325s; erfolgreiche warme Bestätigung am Feldanfang
  35,4/50,3ms einschließlich äußerem Messaufruf. Die logische50ms-Deadline
  wurde nicht erweitert. Ein instrumentierter Lauf bestätigte Antwortframe
  nach9,8ms, EOF/stderr nach29,5ms, Rückkehr nach39,9ms; eigene Familie beendet.
  Dies belegt keine p95-Gesamtabnahme und keine Warmzeiten anderer Positionen.

## Offene Einfügeprobe

Die tatsächliche Paste-/Restore-/Caret-Gegenprobe ist noch offen. Codex meldet
einen Feldinhalt trotz bestätigter Leeranzeige. Die manuelle Testfixture
erhält deshalb ihren RAM-Ausgangszustand, prüft den synthetischen Text genau
einmal und entfernt nur dessen verifizierten Bereich. Kein Enter und keine
privaten Werte in Nachweis/Logs. Zwischenzeitlicher Vordergrundwechsel führte
zum sicheren Abbruch vor Paste.

`config/targets.json` bleibt bis zum vollständigen Nachweis leer. Erst danach
darf die exakte Codex-Paket-/Klassenfreigabe eingetragen werden. Freya/Tyr
wurden erneut seriell über den korrigierten Player abgespielt; ein menschliches
Hörurteil fehlt.

## Integration und laufender Pilot

PR6 wurde nach zwei unabhängigen Reviews, erfolgreichen lokalen Prüfungen und
frischen grünen Hosted-Checks am unveränderten Head26296df integriert. Main:
2298f298c99e5f7491465b91b8a17eeef2575a69. Der vorige Hugin-Pilot wurde normal
über Beenden geschlossen; sein eigener Supervisor bestätigte Familienende
und den Rückstart der unveränderten Altstack-Verknüpfungen. Whispering/PipPal
anschließend erneut über normale Appaktionen pausiert, alter Qwen beendet.
Profile und beide Startup-lnks blieben hashidentisch.

Der neue Pilot von genau diesem sauberen Main ist sichtbar gestartet; seine
exakte Receipt ist durch Root.runtime/current-pilot-fixes-session.txt benannt.
Strg+Alt+D/V und der einmalige Rückweg sind erhalten. Die tatsächliche Codex-
Pasteprobe bleibt offen: vor der Probe war Teams aktiv; eine zusätzliche
45s-Warteprobe fand keinen aktiven Codex-Composer und sendete keine Eingabe.
Dies ist kein weiterer Befund zur Codex-Cursorprüfung. Kein Einfügeziel wurde
freigegeben und die vollständige Produktabnahme bleibt offen.
