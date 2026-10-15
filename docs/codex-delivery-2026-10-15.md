# Codex-Übergabe: Cursor und Clipboard-Rückweg

Stand 15.10.2026; geprüfter Source ce0c1cfeb498b31db8fbafc5bf5e38e8b2001396.
PR7 ist als 777c91cede02352eeb782f93488eb670824d8295 integriert. Native Proben
für beide beobachteten Codex-Fokusklassen einschließlich positivem Textende bestanden;
config/targets.json enthält ausschließlich diese Klassen mit der genauen
Codex-Paketfamilie und0,15s-Restore. Der Ctrl+C-Fallback bleibt leer.

## Ursache und endgültiger Nachweis

Codex 26.1007.9446.0 läuft als ChatGPT.exe, Familie
OpenAI.Codex_2p2nqsd0c76g0. Die gesteuerte Accessibility-Probe lieferte die native
Fokusklasse Chrome_RenderWidgetHostHWND. Nach dem ersten geprüften Neustart
meldete Brian erneut target_unverified beim Diktieren im Codex-Nachrichtenfeld.
Der reale Fokus lieferte Chrome_WidgetWin_1 mit derselben Paketfamilie, einem
UIA-Edit und fehlender Profilfreigabe. Die bisherige Einzelklassenfreigabe
erklärte daher nicht den alltäglichen Eingabepfad. Beide konkreten Klassen
benötigen ihren eigenen vollständigen Nachweis; keine generelle Chromiumfreigabe.

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
- Derselbe Source, vollständige native Probe nach End-Navigation:
  Capture0,306s, Warm42,0ms, Übergabe0,483s. Dieselben Paste-/Restore-/Caret-
  Gegenfall-/Literal-Cleanup-/Baseline-/Servicebelege erfolgreich.
  Diese beiden Proben betreffen Chrome_RenderWidgetHostHWND. Der zweite
  Receipt friert keine Vorabposition ein; allein daraus folgt kein positiver
  Einfügepunkt hinter nichtleerem Text.
- Zusätzliche vollständige Probe am unveränderten realen Hauptcomposer-Fokus
  ohne SetFocus: Chrome_WidgetWin_1 mit exakter Codex-Familie. Am Feldanfang
  Capture0,317s, Warm46,849ms, Delivery0,495s; nach End-Navigation Capture0,316s,
  Warm41,732ms, Delivery0,490s. Beide: genau ein Paste, alle Ausgangsformate
  wiederhergestellt, echter Home-Wechsel vor zweitem Paste abgelehnt, eigenes
  Literal entfernt, Baseline erhalten und Service-/Familiencleanup bestätigt.
  Kein Enter/Absenden, keine privaten Inhalte in den technischen Receipts.
  Root.runtime/codex-paste-widget-proof.json und codex-paste-widget-end-proof.json.
- Separater P2-Reviewbefund geschlossen durch explizite nichtleere Endproben
  für BEIDE Klassen: eigenen synthetischen15-UTF-16-Einheiten-Präfix einsetzen,
  dessen exakten Inhalt/Restore bestätigen, per Ctrl+End zum Dokumentende.
  Vor positivem Paste Position15, nichtleere/nichtblanke Basis und
  placeholder_baseline=false bestätigen. Widget Capture0,319s, Warm50,809ms,
  Delivery0,512s; Renderer Capture0,323s, Warm44,926ms, Delivery0,503s.
  Jeweils genau ein zusätzlicher Paste, sämtliche Formate zurück, Home-
  Gegenfall abgewehrt, sowohl Testliteral ALS AUCH eigene Basis entfernt,
  ursprünglicher Feldwert erhalten und Service/Familie geschlossen. Kein Enter.
  Receipts: Root.runtime/codex-paste-widget-seeded-end-proof.json und
  codex-paste-seeded-end-proof.json. Die50ms-Protokollfrist wurde nicht geändert;
  der äußerlich gemessene Bestätigungsaufruf enthält Scheduling/Fixture-Overhead.
- Konfigurations-/Service-Regression zuerst rot: der tatsächlich verwendete
  Chrome_WidgetWin_1-Pfad wurde als target_unverified abgewiesen. Profil um
  genau diese zweite Codex-Klasse ergänzt. Beide erlaubten Klassen prüfen;
  fehlende/andere/Groß-Kleinschreibung abweichende Familien und eine dritte
  Klasse bleiben vor Snapshot, Clipboardmutation und Paste gesperrt.
  Vier Basisproben plus zwei explizite positive Endproben; keine p95- oder
  universelle Kompatibilitätszusage.

## Pilot und offene Abnahme

PR7 wurde mit drei erfolgreichen Hosted-Checks am unveränderten Head
ba5700c6cae9c29d1b6ed56bbfc9bb140ce9a62f integriert. Main777c91c wurde erst nach
normalem Hugin-Ende/Familienabschluss aktualisiert. Beide alten Startup-lnks
starteten Whispering/PipPal; beide Apps danach normal erneut beendet. Profil
und Links hashidentisch, alter Qwen beendet, STT-HTTP-Standby unverändert.
PR7-Pilot vom sauberen Main777c91c sichtbar gestartet (536x679), Sitzung damals
über Root.runtime/current-pilot-fixes-session.txt. Ein danach erkanntes reales
Diktat wurde wegen der zweiten Fokusklasse abgewiesen; Mikrofon/Erkennung
damit beobachtet, alltägliche Übergabe nach zweiter Klassenfreigabe noch offen.
PR8 inzwischen am unveränderten Head3f4efaaf323c005038d6e2cc5e093ea7b9f1b964 mit
zwei geschlossenen Reviews/drei erfolgreichen Hosted-Checks integriert;
Merge bb700f0469dd3f75007041c430058c5bae368b47 mit gleichem Tree remote belegt.
Erneuter normaler Quit/Familienabschluss, alter Rückstart und reguläre Pause
bestätigt; Main erst danach FF. Neuer Pilot vom sauberen Mainbb700f0 sichtbar
536x679, Statussymbol Bereit, beide exakten Codex-Klassen beim Start geladen.
Aktuelle Sitzung über Root.runtime/current-pilot-fixes-session.txt und kuratierten
pilot-rollout-final-2026-10-15.json. Profil/Startup-lnks weiterhin hashidentisch,
alter Qwen abwesend, STT-HTTP-Standby unverändert. Strg+Alt+D/V und einmaliger
Rückweg erhalten. Alltagsübergabe über echtes Kürzel nach diesem Neustart,
Maus/Alt+Y/Gesamtmigration und menschliches Hörurteil Freya/Tyr bleiben offen.
