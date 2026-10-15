# Hugin Pilotkorrekturen — Stand 15.10.2026

## Auftrag und feste Punkte

- Brian bestaetigt normalen Paste in Codex. Folgeauftrag: markierten Text
  ersetzen, regulaere Felder inklusive YouTube/Chrome, zwei Aufnahme-Cues,
  echtes TTS-Streaming Freya/Tyr korrigieren. Keine neue Produkteinstellung.
- Vertrag: specs/2026-10-15-hugin-input-audio/{spec,plan,tasks}.md; bisherige
  v1-Spec/Privacy/Cancel/Altstack-Rueckweg gelten weiter.
- Repository valhalla-hq/hugin; Branch codex/hugin-pilot-fixes-mjolnir.
  Root C:/Users/brian/brian-projects/worktrees/hugin/hugin-pilot-fixes-mjolnir.
  Root-Ownership aktiv; laufender Supervisor benoetigt diesen Worktree.
- Control e3deecae6673a024aa9015a4387737fbec04c795. Stable Main
  8e4ceabb718edb2c8d1b80e1b07b69e0f3b933bd;
  CoreSource6f4897c; abschliessenderTon-Source9a470aca936d3dbc885935229a7eb434d0504c86.
  https://github.com/valhalla-hq/hugin/pull/9 ist regulaer integriert.
  Routineintegration im bekannten privaten Scope autorisiert; kein Bypass.

## Umsetzung und Nachweise

- UIA selection(start,end), je Endpoint-ID/Endaffinitaet; Default-Nativeproof
  false. Native Edit/RichEdit und direkt fokussierte voll editierbare UIA-
  Edit/Combo-Felder. Alte IPC-Shapes weg; Request4 mit operation, Response3,
  maximal3211B innerhalb4092B. TTS-Providerbinding bleibt getrennt.
- Verified-Edit-Profil0,25s, Codex-Overrides0,15s; keine Klassen-/Namensheuristik
  fuer Editierbarkeit. Alle Clipboard-/Fokus-/UserCopy-/RAM-Ownerregeln erhalten.
- Echte Chrome-/YouTube-Teilreplacement6..11 erfolgreich, Praefix/Suffix
  unveraendert, alle3Clipboardformate zurueck, eigenes Literal entfernt und
  leere Baseline bestaetigt. Warm46,482ms/Delivery0,585s, kein Enter. Spaetere
  Vollauswahl wegen wechselndem OS-Fokus unverifizierbar; kein Paste. Nativ
  unbestaetigte Vollmatrix bleibt offen, kein Erfolg daraus abgeleitet.
- Eigene115ms-tiefeStartdoppelimpuls-/180ms-aufsteigendeEnd-Cues, unabhaengiger Outputowner,
  priorisierter Cancel. Mic zuerst unarmed, Cue/Drain, Geraetezeit+25ms Gate;
  Endcue nach Micclose, vor UIA/STT. Endcuefehler verliert valides PCM nicht.
- Native Untersuchung: MME liefert42×ADC0/0B trotz fortschreitender Streamzeit.
  Producer waehlt eindeutig WASAPI-Default, prueft globale Device-/Host-ID,
  Sharedmode auto_convert identisch an Check/Open. ADC0 ist Clockfault.
  NativeProbe ueber wirkliche factory=None109Callbacks/12gated/31.040B,
  0akzeptierte ADCs vorCutoff, beideCues+Cleanup bestaetigt. Kein PCM gespeichert.
- Worker: Generator bleibt GPU-Owner, genau ein Writer/ein Pendingchunk;
  hoechstens3×1.440.000B Provider-PCM, Client-/native Queue unveraendert.
  Normalterminal erst nach Generatorclose/Writerbarriere/GPU-sync; Fehler-
  Cleanup bleibt gehalten. Verzogerter FIFO-Guard zuerstrot, dann lueckenfrei.
- Reale Vergleichsprobe: nur alter Serverbb700f0 gegen sonst identische
  Provider/Client/Controller/Nativepipeline. Freya9/Tyr8 leere Refills vorher,
  nachherbeide0; Freya291.840B/Tyr284.160B, alle Provider-/IPC-/Player-/Cross-
  Hashes gleich. NativeQueuepeak6.000B. Neue zweiOperationen27,344s, alte30,642s;
  frischeWorker, FreyainklInit/Tyrwarm; Cacheeffekte/p95 nicht kontrolliert.
  WorkerCPU20,984vs21,625s; PeakJobCommit8.454.057.984vs8.455.290.880B.
  Kein physischer RAM-/GPU-/Tokenmessnachweis. NativeCancel0,760s/6.000B
  bisReset/Terminal/Familienabschluss bestaetigt.
- 390 Source-/Integrationschecks18,418s und56 Windowschecks3,377s ohneSkips;
  native Mic/Player/Hotkeys/Mutex/Idle-App/HiddenRichEdit. Zwei unabhaengige
  Linsen fuer fremde Slices, Originalendpoint-P2 reproduziert/geschlossen,
  sieben Device-/ADC-/Cleanup-Guards fuer reale MME-Luecke. Keine offenen
  reproduzierten P1/P2 amSource6f4897c. Alle drei Hostedchecks am festen
  finalen Head573ca3fa4c8c9e4d7b09b60772b9de022b66479d gruen.
- Kuratierte Quellen, Versionen und Messgrenzen: docs/input-audio-2026-10-15.md.
  Fruehere Codex-/Restorebelege: docs/codex-delivery-2026-10-15.md. Eine fruehe
  fehlgeschlagene Probe verlor RAM-Clipboardinhalt; nicht wiederhergestellt.

## Laufzustand und Rueckweg

- C:/Users/brian/Hugin ist Junction zum sauberen _repos/hugin Main. Nach
  bestaetigtem Pilotende FF auf8e4ceab, dann neuer Pilot; keine gemischten
  Livequellen. Main waehrend dieser Sitzung nicht fuer Sourceupdates verwenden.
- Nutzer hat Hugin normal beendet. Alter Pointer Root.runtime/current-pilot-
  fixes-session.txt -> pilot-session-2b3d2475-04da-4175-87c1-a49e7825c86e.json
  bestaetigt return_dispatched/exit0/own_family_exited und beideStartup-lnks.
- Nutzer danach Whispering/PipPal normal beendet; Apps/alterQwen frisch
  abwesend. PipPal-Profil und beideStartup-lnks gleiche bekannteSHA256.
  Alter STT-HTTP-Standby unveraendert. Kein fremdesKill/parallelGPU.
- Root.runtime/pilot_session.pyw dry-run --head <checked-main>, --run verborgen
  starten: eigenerJob/Familienabschluss, danach unveraenderteStartup-lnks.
  Keine dauerhafte Autostartaenderung. Neuer Receipt:
  C:/Users/brian/brian-projects/_repos/hugin/.runtime/pilot-session-854cec59-a15a-44c1-8373-be2cd39273a8.json.
  Aktueller Root.runtime/current-pilot-fixes-session.txt zeigt darauf.
- PR9 am festen573ca3f nach frischer privater Repo-/PR-/28Dateien-/Check-
  Pruefung mit normalem Merge integriert. RemoteMerge8e4ceab/Ancestry/
  identischer GitTree belegt; Main sauber. Dry-run und unique-neuerReceipt
  statt Dateiname-/PID-Raten; Zustandpilot_running. Supervisor41332,
  Appwrapper42772, echteApp16336; vier frische gehaltene Image-/Creation-
  Bindings und Elternkette bestaetigt. Sichtbares Hugin536x679, eigene Signal-
  /Trayfenster und belegteInstanz. GenericEdit+zweiCodex-Overrides geladen;
  Schutzdateien hashidentisch. Root.runtime/input-audio-rollout.json.
- NativeTk-/Tray-UIA exponiert den Bereit-Wortlaut nicht; keine direkte
  Status-/Hoerabnahme daraus behauptet. Bei Fortsetzung PIDs/Handles und
  Receipt frisch pruefen; gespeicherte Zahlen sind keine kuenftige Autoritaet.
- Kuerzel bleiben Strg+Alt+D und Strg+Alt+V, Escape imVorgang. NormaleMaus-
  /Alt+Y-/Autostartmigration gesperrt. UI/Rabenicon/Stimmen unveraendert.

## Offen / Fortsetzen

1. PR9 und gepruefter Pilotneustart abgeschlossen. Aktueller dokumentarischer
   Rolloutcheckpoint auf codex/hugin-pilot-fixes-mjolnir ist Draft PR10:
   https://github.com/valhalla-hq/hugin/pull/10. Nur Context, dieser exakte
   Handoff und Aufgabenstatus; Branch/Draftstatus und Context-/Handoffblobs
   bei Fortsetzung frisch lesen.
2. Pilot laeuft auf8e4ceab; Root wegen Supervisor nicht freigeben/entfernen.
   Keine weiteren Sprach-/Fokus-/Clipboardproben ohne konkreten Testbedarf.
3. Brian meldet fluessige Sprache. Lautere/distinktereTöne aufWunsch umgesetzt;
   82 passendeChecks+NativeReplay/Gate114Callbacks/31.680B/0alteADCs gruen.
   NeueTonabnahme, Cue-Echo sowie reale Codex-
   /Browser-/Win32-Delivery-Vollmatrix als Nutzerabnahme weiterfuehren.
   TechnischerNativebeleg ist keine Hoer-/Produktionsgesamtabnahme.
4. Root-Worktree/Ownership bei laufendemSupervisor behalten. HelperSource
   ist separat integriert; derenOwnership nur ueber regulaerenLifecycle
   nach eigenemRemotecheckpoint freigeben, keine fremdenStateeingriffe.

Starter: Hugin AGENTS.md, CONTEXT.md und genau diesen Handoff lesen; zentralen
Lifecycle/Preflight mit aktivemBranch, Git/PR/Ownership und Runtime frisch
pruefen. Source6f4897c plusTon9a470ac geprueft und ueberPR9/Main8e4ceab im
laufendenPilot. Nutzerfeedback/Alltagstest fortsetzen, ohne alte Fokus-/
Clipboardfragen zu wiederholen.
Keine Rohinhalte inGit, kein Enter/Send, keineProduktionsmigration behaupten.
