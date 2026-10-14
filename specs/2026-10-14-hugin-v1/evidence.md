# Hugin Bestandsnachweise

Stand: 14.10.2026. Lokale Quellen wurden lesend untersucht. Bisherige Laufzeit-/Hashnachweise stammen aus der technischen Bestandsaufnahme in dieser Unterhaltung; die Modelle wurden für die Erstellung der Spec nicht erneut geladen oder transkribiert. Hugin selbst ist unimplementiert.

## Beobachtungen und ihre Grenzen

| ID | Nachweis | Aussage und Grenze |
| --- | --- | --- |
| E-001 | C:/Program Files/Whispering/whispering.exe; REA inspect_pe_resources, ev_288aa70d81ae2d326ddf09f3d716af9e5c0459d1a6ce2fb44233388d4df95279 | Installierte Version 7.11.0; 32.771.072 Bytes, SHA256 88ad7d66f8c8e99fbc531932626a06f0f533d0fce3f9d7d3a4b79d0478ca953a. Statische PE-Identität, kein Ausführungsnachweis für einzelne Funktionen. |
| E-002 | [Whispering v7.11.0](https://github.com/EpicenterHQ/epicenter/tree/v7.11.0/apps/whispering), Commit a6b15c28db9076742d7ae7014f8ec9f97aa615d1 | Aufnahme/Manual-Toggle, Speaches-Anschluss, Clipboard-Paste im Versionsquellcode gelesen. Binär-Reproduzierbarkeit zu diesem Quellstand wurde nicht bewiesen. |
| E-003 | [Aktiver STT-Server](C:/Users/brian/brian-projects/local-tools/whispering-local-stt/server.py) | 127.0.0.1:8178, eigener Speaches-kompatibler Adapter; aktiver Quellstand entspricht kuratiertem runtime. Lesender Health-Snapshot: cuda, model_loaded=false, offline=true, Hook registriert. Registrierung beweist keine physische Bedienung; ältere Handoff-Aktivierungsangaben sind teilweise überholt. |
| E-004 | [STT-Lock](C:/Users/brian/brian-projects/_repos/whispering-local-stt/config/model-lock.json) | Sechs aktive Modelldateien wurden vollständig gegen Größe/SHA256 geprüft. Whisper-Revision unten. |
| E-005 | [Reader-Modelllock](C:/Users/brian/brian-projects/_repos/local-voice-reader/config/model-lock.json) | Elf aktive Qwen-Dateien wurden vollständig gegen Größe/SHA256 geprüft. Acht fokussierte PipPal-/Qwen-Module entsprechen kuratierten Quellen bytegleich. |
| E-006 | [Reader-Stimmen](C:/Users/brian/brian-projects/_repos/local-voice-reader/runtime/tts-vergleich/reader-voices.json) | Beide Referenz-WAVs, Texte und Hörproben entsprechen gespeicherten Hashes. Aktive Profilpfade unterscheiden sich von portablen Quellen; Stimmenidentität stimmt. |
| E-007 | [PipPal-Clipboard](C:/Users/brian/brian-projects/local-tools/PipPal/src/pippal/clipboard_capture.py) und [Worker-Client](C:/Users/brian/brian-projects/local-tools/PipPal/src/pippal/qwen_worker.py) | Text-only-Backup mit bedingungslosem Restore; Cancel ohne Warten auf terminales Worker-Ende. Das begründet Hugins gemeinsame Clipboard-/Audio-Owner und Abbruchbarrieren. |
| E-008 | [STT-Herkunft](C:/Users/brian/brian-projects/_repos/whispering-local-stt/config/provenance.json) | STT nutzt CUDA-DLLs aus der alten Qwen-venv. Der aktive Downloader ist latest-orientiert; kuratierter Restore ist gepinnt. Hugin darf nur den gelockten Wiederherstellungsweg übernehmen. |
| E-009 | Vorhandenes Python 3.12.10, Import tkinter ohne Fenster | Tkinter vorhanden, Tk-API 8.6. Dies beweist noch keine fertige GUI, DPI-/Screenreader-Abdeckung oder Hugin-Packaging. |

Die relativen Bestandslinks oben werden bei Portabilisierung in T001 durch importierte Herkunftsmetadaten und vollständige Dateilocks ergänzt. Sie sind lokale Referenzen, keine Laufzeit-Abhängigkeiten des geplanten Hugin.

## Festzuhaltende Engine-Identitäten

- STT: dropbox-dash/faster-whisper-large-v3-turbo, Revision 0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf; faster-whisper 1.2.1, CTranslate2 4.8.2, PyAV 16.1.0, NumPy 2.5.3. CUDA int8_float16, CPU int8, sechs CPU-Threads, ein Worker. Sprache Auto, task transcribe, Beam 5, Temperatur 0, leerer Prompt, condition_on_previous_text=false, VAD mit 500 ms Mindeststille. Idle-Offload initial 90 Sekunden.
- TTS: Qwen/Qwen3-TTS-12Hz-0.6B-Base, Revision 5d83992436eae1d760afd27aff78a71d676296fc. Faster-Qwen3-TTS 0.3.2, Commit a70afc0f81f7f5f8801c3227968f1102f43f211c. Qwen-TTS 0.1.1, torch/torchaudio 2.9.1+cu128, transformers 4.57.3, accelerate 1.12.0, NumPy 2.2.6. ICL, bfloat16, SDPA, seed 42, chunk_size 8, max_seq_len 1024, max_new_tokens 640, warmup prefill 128. Ausgabe 24 kHz PCM16 mono. Deutsch Standard, Englisch technisch vorhanden und über Repo-Konfiguration wählbar.
- Modellgewichte und Laufzeiten werden nicht in Git abgelegt. Vollständige bestehende Modell-Dateilocks und Paketlocks müssen in T001/T005/T006 übernommen werden; Kurzangaben hier ersetzen keine Dateiverifikation.

## Stimmenidentität

| Hugin-Name | Ursprüngliche ID | Referenz-WAV SHA256 | Referenztext SHA256 |
| --- | --- | --- | --- |
| Freya | deutsch-3 | d85db7c94800a4d3b22a5fd2c05f825825a17c33c385cfa603c3d9fcaa9905dc | f9929eb90bc28e3ff42b64130597676d4a83148307cd09c368708c4eb294a0dc |
| Tyr | deutsch-a | 99322687550514995cb4451de956b225f94d857805f607b8307242e7ac649af6 | a64b31763b6b7f8b0997a1cdd1cf8988e51d3903ea87a19a5eaf00ae10f54ee0 |

Freya-Hörprobe: cd3d1d11bd09c354548d4b9da0a266b8301242c2ede53fe583658b53c2f5e447. Tyr-Hörprobe: 8544d40187c79ef04d99a0a1c55be0ff24e23a3866ac2fecdb465dabdbe93f77. Freya basiert auf einer synthetischen VoiceDesign-Referenz, Tyr auf synthetischer Piper-Thorsten-Sprache. Tägliche Wiedergabe benötigt die eingefrorenen Referenzen, nicht deren Erzeugungsprogramme.

## Primärquellen für Plattformentscheidungen

- [RegisterHotKey und MOD_NOREPEAT](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey)
- [LowLevelMouseProc: Message-Loop, Timeout und mögliche stille Hook-Entfernung](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelmouseproc)
- [SendInput: Rückgabewert, Modifier und Integrity-Grenzen](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [Clipboard-Sequence](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclipboardsequencenumber)
- [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
- [Tkinter/ttk](https://docs.python.org/3.12/library/tkinter.html)
- [sounddevice Raw Streams 0.5.1](https://python-sounddevice.readthedocs.io/en/0.5.1/api/raw-streams.html)

## Historische Messungen und Unbekannte

Historisch: 11,04 Sekunden synthetisches deutsches Audio etwa 0,5–0,7 Sekunden warm im alten STT-Stack; Qwen-Warmup etwa 12,38 Sekunden, erster Ton ungefähr 0,4 Sekunden. Das sind keine neuen Messungen und keine Hugin-Leistungsversprechen. Frische CPU-/RAM-Familienpeaks und kombinierte Modellresidenz fehlen.

Offen für den Pilot: physische Zustellung beider Maustasten mit realer Logitech-Software, Escape-Konflikte, Win32-/Tk-/Audio-Zusammenspiel, tatsächliche Caret-/Clipboard-Abdeckung pro Ziel, terminaler Qwen-Abbruch einschließlich GPU-Arbeit, kombinierte VRAM-Nutzung, regulärer Login und vollständiger unabhängiger Neuaufbau.
