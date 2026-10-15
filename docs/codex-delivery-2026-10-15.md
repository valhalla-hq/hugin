# Codex-Übergabe: Cursor und Clipboard-Rückweg

Stand 15.10.2026; geprüfter Source ce0c1cfeb498b31db8fbafc5bf5e38e8b2001396.
PR7 setzt die integrierten PR5/6 fort. Beide vollständigen nativen Proben
bestanden; config/targets.json enthält ausschließlich die dabei geprüfte
Codex-Fokusklasse/Paketfamilie mit0,15s-Restore. Der Ctrl+C-Fallback bleibt leer.

## Ursache und endgültiger Nachweis

Codex 26.1007.9446.0 läuft als ChatGPT.exe, Familie
OpenAI.Codex_2p2nqsd0c76g0. Beim normalen Accessibility-Fokus wurde die native
Fokusklasse Chrome_RenderWidgetHostHWND beobachtet; zuvor auch
Chrome_WidgetWin_1. Nur tatsächlich geprüfte Klasse und genaue Paketfamilie
kommen für eine Freigabe infrage.

Das leere Eingabefeld kann einen Caret im Platzhalterkind melden. Am Textende
liegt ein besitzbelegter Textkind-Punkt teils hinter der Parent-DocumentRange;
Character-Bewegung erreicht einen anders dargestellten Punkt. RangeFromChild
und Rundwege beseitigen diese Differenz nicht. Die frühere globale, später
lokale Character-Suche ist entfernt.

Der Produzent prüft den kollabierten Punkt und seine Zugehörigkeit zum
konkreten fokussierten, editierbaren, nicht geschützten Edit. Identität:
Edit-/Root-/Fokus-/Caret-Kind-RuntimeIDs, Prozess, lokale UTF-16-Position und
geordnete Relation zum deklarierten Dokumentende. Am Edit-Anfang kein Lesen.
Sonst wird nur der eigene Edit-Präfix bis zum Caret im isolierten Provider
kurz gelesen: Anforderung höchstens262145 Zeichen, akzeptiert höchstens262144
UTF-16-Einheiten. Zeichen werden nach Längenbildung freigegeben; IPC, Diagnose
und Dateien enthalten nur technische Metadaten. Kein Value/globaler Chatprefix.

Edit-Range und Präfix müssen objektfrei sein; unknown GetChildren bleibt
unprüfbar. Das verhindert gleiche Plaintext-Längen an verschiedenen Objekt-
grenzen. Nach dem letzten Textlesen Auswahl, Kind, Endrelation, Struktur und
Editierbarkeit frisch prüfen; danach native Identität und einmaliger Commit.
Die logische50ms-Deadline bleibt bestehen. Grundlagen:
[UIA-Objektgrenzen](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-textpattern-and-embedded-objects-overview),
[GetChildren](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-getchildren),
[begrenztes GetText](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-gettext).

## Zwischenablage

Reproduziert: Windows ergänzt beim Close Textformate; die zuvor beobachtete
Sequenz war unmittelbar veraltet. Der Produzent normalisiert die veröffentlichte
Sequenz über stabilen Sequenz-/Owner-/Sequenz-Nachweis am gehaltenen eigenen
HWND. NULL-Owner/instabile Werte/Teilfehler behalten den Originalsnapshot im
RAM; nur eine belegte fremde Nutzerkopie hat Vorrang. Recovery verwendet diese
Produzentenfakten ohne alten Raw-Sequence-Fallback.

Browserkopien enthalten Chromium internal source RFH token und Chromium
internal source URL. Genau diese HGLOBAL-Formate zusammen mit Text/HTML opak
im bestehenden32MiB-Snapshot erhalten. Andere unbekannte/OLE-/verzögerte
Formate verhindern jede Mutation. Quellen:
[Chromium-Formatvertrag](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/ui/base/clipboard/clipboard_format_type_win.cc),
[HGLOBAL-Schreibpfad](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/ui/base/clipboard/clipboard_win.cc).

Eine frühe fehlgeschlagene Testprobe beendete ihren Prozess, während der
vorherige Clipboardstand nur im RAM vorlag. Dieser Ausgangsinhalt wurde nicht
wiederhergestellt; entfernt wurde nur ein verifiziertes eigenes Testartefakt.
Spätere erfolgreiche Restores gelten für einen neuen Ausgangsstand.

## Tatsächlich geprüft

- Guards für UTF-16/Endaffinität, Objekt-Aliase, späte Caret-/Kind-/Readonly-
  Änderungen und Clipboard-Veröffentlichung zuerst rot, danach grün.
- 328 Source-Vertrags-/Integrationsprüfungen grün in19,016s.
- 23 Windows-Prüfungen grün in0,341s:22 ABI-/Producerverträge und ein echter
  eigener HiddenRichEdit-UIA-Test; keine Skips/fremden Eingaben dabei.
- Zwei unabhängige Source-/Spec-Reviews; reproduzierte P1/P2 geschlossen.
  Zusätzlicher Boundaryreview110 passende Source-/Mocktests grün.
- Vorstufe3fb625c: echtes einmaliges Paste, aktuelle Clipboardformate zurück,
  End-Caret erfasst, echter Home-Wechsel vor zweitem Paste mit target_changed/
  submittedFalse abgewehrt. Warm38,3ms/Delivery0,483s; keine p95-Zusage.
  Vollständiger Fixture-Cleanup damals noch offen; kein Ziel dadurch aktiviert.
- Abschlussfixture: reale Tastenauswahl, nur exakt bestätigtes eigenes Literal
  entfernen, Ausgangstext im RAM erhalten. Kein Enter/Absenden/Feldlöschen.
- Aktueller Sourcece0c1cf, vollständige native Probe am Feldanfang:
  Capture0,314s, Warm40,7ms, Übergabe0,476s. Genau einmal eingesetzt, sämtliche
  Ausgangsformate zurück, echter End-Caret erfasst/Home-Wechsel abgelehnt,
  Gegenfall-Clipboard zurück, nur eigenes Literal entfernt, Baseline erhalten,
  eigener Service samt Probe-Familie geschlossen. Kein Enter/Absenden.
- Derselbe Source, vollständige native Probe mit Anhängen am echten Textende:
  Capture0,306s, Warm42,0ms, Übergabe0,483s. Dieselben Paste-/Restore-/Caret-
  Gegenfall-/Literal-Cleanup-/Baseline-/Servicebelege erfolgreich.
  Dies sind zwei Einzelproben, keine p95- oder universelle Kompatibilitätszusage.
  Keine breitere Chromium-/Chrome_WidgetWin_1-Freigabe aus früheren Teilproben.

## Pilot und offene Abnahme

Sichtbarer Pilot weiterhin von sauberem Main2298f298c99e5f7491465b91b8a17eeef2575a69;
neue Source zur geprüften Integration vorbereitet. Exakte Sitzung über
Root.runtime/current-pilot-fixes-session.txt. Strg+Alt+D/V, normaler Tray-Rückweg,
alte Profile und Startup-lnks erhalten. Maus/Alt+Y/Gesamtmigration bleiben
gesperrt. Native Codex-Komponentenabnahme bestanden; nach geprüftem Merge
geordneten Pilot neu starten. Mikrofontest im neuen Pilot und das separate
menschliche Hörurteil Freya/Tyr sowie die Gesamtmigration bleiben offen.
