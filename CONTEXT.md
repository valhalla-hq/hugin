# Hugin Context

Status: implementation
Owner: Brian
Type: application
Data boundary: Privater Quellcode, kuratierte Konfiguration, Paket-/Modelllocks und bestaetigte kleine synthetische Stimmreferenzen. Keine persoenlichen Diktate, Dokumente, Audioaufnahmen, Credentials, Rohlogs, Modellgewichte oder virtuellen Umgebungen in Git.
Source truth: `valhalla-hq/hugin`

## Goal

Brian hat am 14.10.2026 Spec und Plan unter C:/Users/brian/Hugin/specs/2026-10-14-hugin-v1 erstellt und die schrittweise Umsetzung beauftragt. Kleine native Oberflaeche, XBUTTON2 und Alt+Y fuer Diktat-Toggle, XBUTTON1 fuer Vorlesen-Toggle, Diktat stoppt Vorlesen, beide unveraenderten Stimmen Freya/deutsch-3 und Tyr/deutsch-a. Escape-Abbruch, ein letztes RAM-Diktat mit Kopieren/Loeschen, technische Diagnose ohne Inhalte. Whispering und PipPal laufen bis zur geprueften Umstellung weiter. Lokaler Einstieg C:/Users/brian/Hugin; vorhandene Planungsdateien erhalten und im ersten exklusiven Task uebernehmen.

## Current State

- Private Initialisierung und Katalogregistrierung abgeschlossen, main e555d7d76045dddde35cdeb2e63ce17f048df559.
- Aktiver Task codex/hugin-v1-mjolnir; Planungsunterlagen, Referenzstimmen, Locks und erste Controller-/Prüfgrundlage übernommen.
- Erste Konfigurations-/Asset-Guards wurden zuerst rot, dann grün geprüft. Controller-Pakete isoliert installiert; Sounddevice sieht Standardgeräte, Mikrofon noch nicht geöffnet.
- Whispering/PipPal und produktive Tasten/Autostarts sind unverändert. Keine Hugin-Gesamtabnahme behauptet.
- GitHub main-Protection-Abfrage liefert HTTP403 wegen Tarifgrenze; keine Policy geändert. Vertraglicher PR-/Review-/CI-Gate bleibt maßgeblich.

## Decisions

- Private by default.
- Weitere Arbeit und routinemäßige private Integration folgen dem aktuellen zentralen Lifecycle-Vertrag; keine abweichende lokale Autoritätsregel.

## Next Step

- T001 abschließen und die vertikalen Tasks der Spec abarbeiten; Prüfstatus je AC führen. Produktive Eingaben erst nach vorbereitetem, geprüftem Wechsel übernehmen.

## Active Handoff

- `handoffs/2026-10-14-hugin-workers.md`

## Bounded Engine Helper Checkpoint

- Executor for this helper: codex/hugin-workers-mjolnir, separate worktree; the parent Hugin task owns integration and completion. Ownership remains active, no helper PR or merge.
- Implemented bounded private IPC, atomic transcript completion, isolated Whisper/Qwen workers and parent-client API. See docs/workers-api.md. Parent centrally schedules initialization, inference and offload.
- Own .runtime/models/stt, .runtime/models/tts and .runtime/cuda were copied from exact existing local bytes and fully hash-verified. New STT/TTS venvs installed from 21/94 pinned dependency entries; both pip checks passed. Old runtimes and processes unchanged.
- 11 contract tests and 5 simulated worker integration tests passed. Real CPU Whisper completed silent-input cold/warm/offload/reload probes; real private IPC plus native Windows Job Object completed with observed family exit. No GPU model loaded, no microphone or playback.
- Native initialization must finish synchronously before starting the command reader: earlier reader placement reproduced a 60-second CPU initialization hang. Initialization cancellation therefore uses parent-held job watchdog/exit rather than an in-process acknowledgement.
- GPU inference/cancellation, both-voice hearing, combined residency, complete offline wheelhouse restore, speech accuracy and full hardware AC remain unverified. No T005/T006 completion or total Hugin acceptance claimed.

## Bounded Restore Follow-Up

- tools/restore.py now plans without writes and applies only to the selected Hugin checkout's owned .runtime. All source/target lock identities, hashes, destination conflicts and environment ownership are checked before writes. File-lock parsing is shared with workers; no old-stack paths or model downloads are built in.
- Parent runtime materialized at C:/Users/brian/brian-projects/worktrees/hugin/hugin-v1-mjolnir/.runtime: 6 STT, 11 Qwen and 12 CUDA files copied from this helper's verified runtime; new STT/TTS venvs created in place with 21/94 pinned packages and passing pip checks. Existing controller and tracked parent files were untouched.
- Effective free disk before materialization was 543,585,005,568 bytes. New environments have path/engine/pin ownership markers; repeat apply verifies versions and does not reinstall matching packages.
- 23 source tests pass, including 7 restore guards. Parent CPU speech probe used the approved synthetic Tyr reference (6.48625 seconds), resampled only in RAM from 22050 to 16000 Hz. Normalized comparison: 104 characters, 17 words, Hamming/character-edit/word-edit distances all 0. Worker family exit confirmed; separate sentinel preserved. No payload or recording written, no GPU model loaded.
- Controller restore, cryptographic wheel locks, offline wheelhouse/restore and native GPU/voice/pilot coverage remain open. Package-cache hits do not establish offline reproducibility.

## PCM Publication Barrier Correction

- Parent review found successful terminal futures could overtake the last PCM callback because framing receipt was counted as publication. Client now owns separate per-request received/accepted-audio counts. Non-canceled terminals wait for all callbacks; cancellation bypasses publication waits after framed bytes are drained. Returning old callbacks cannot acknowledge a newer request.
- Guard-first public WorkerClient regressions reproduced the last-callback and next-chunk race before the fix; 26 total tests now pass, including independent cancellation under backpressure and old/new request identities. No GPU or native actions used for this correction.
- Separate read-only Standards review of parent fixed head 8d604bb628898e96c2de5ecefee214356cdd040c reported three reproduced cleanup findings to the parent: lossy capacity handling for owner-close acknowledgements, pending capture shutdown, and sticky input-error cleanup. Parent owns those root fixes; no parent edits made here.

## Bounded T009 Windows Signals

- Parent fixed head 1a189d7b706afff3ba58705b0222f411290f1740 was merged into this exclusive helper (merge 9c2cd05); helper context retained. Overall integration still belongs to the parent.
- src/hugin/windows/signals.py implements WindowsSignals with a dedicated invisible top-level broadcast window, held class/callback lifetime, bounded dispatch of system_pause/system_resume/devices_changed, honest ready/closed/error, and retryable owner-thread cleanup. No existing WNDPROC is overwritten. Parent owns Application/UI wiring.
- Guard-first source/ABI tests: 10 signal contracts plus 7 mocked Win32 producer/ABI cases green; full source suite 133 passed. No actual native window, sleep/resume, device change, Explorer termination, microphone, playback or GPU model load performed for this slice.
- Installed pystray 0.19.5 already handles TaskbarCreated by re-adding a visible icon; static source hashes/findings and API are in docs/system-signals.md. No duplicate Explorer-recovery code added.
- Real broadcast delivery, Modern Standby, controller/device reopen timing and Explorer pilot remain unverified. Generic WM_DEVICECHANGE does not establish exhaustive default-audio-endpoint change coverage; AC016 remains open.

## Bounded Default Audio Endpoint Notifications

- Added AudioEndpointNotifications over pinned comtypes 1.4.17, explicit SDK IMMDeviceEnumerator/IMMNotificationClient declarations, and WindowsSignals composition. Render/capture changes for all three default roles emit only devices_changed. No polling, endpoint ID/name conversion, device query/settings or audio operations.
- Registration, exact held-pointer unregistration, COM reference release and balanced STA cleanup run on the original signal owner thread. Failed cleanup retains remaining COM references, callback and owner for explicit retry. WindowsSignals' existing total close deadline includes COM cleanup; blocked unregister cannot claim closed or destroy the wake window early.
- Guard-first endpoint contracts/composition guards reproduced missing implementation before source. Latest source suite: 151 passed; 12 endpoint contracts, 16 signal contracts, five COM ABI mocks plus seven Win32 ABI mocks. One real read-only COM registration/unregistration test passed with six synthetic real-vtable callback invocations and observed own thread exit. No real default-device change delivery claimed.
- Separate sequential Spec/Standards self-review followed the Code Review skill within the parent's no-subagent bound. No unresolved source finding; actual broadcasts/default-device changes/reopening, Modern Standby and Explorer pilot remain open. No root files, old stack, devices, microphone, playback or GPU touched. Ownership remains active.

## Bounded Worker Content Lifetime Correction

- Confirmed parent privacy finding: persistent worker run/reader locals retained completed provider text, encoded transcript, synthesis command/PCM and the client's last frame while blocking for later work. Producing boundaries now scope each operation/control event/data frame separately; consumed commands are cleared and dropped before idle. Input frames are released between reads.
- Guard-first public simulated WorkerClient checks reproduced retained provider str-subclass after terminal/offload and retained client STT/TTS frames at idle; both pass after the fix. A separate original-server comparison also reproduced retained synthesis input before synchronization/terminal. Latest source suite 154 passed, including 11 simulated worker integration tests; no real-provider memory-erasure claim.
- Client close/closed/closing were not changed (AST comparison verified close unchanged); parent owns that parallel fix. Active callback arguments and deliberately retained Core RAM results have their existing owners. Native provider caches/allocator erasure remain unverified. No GPU, native input, old-stack or parent tracked-file changes. Ownership remains active.

## Fixed Root Ops Review and Build Owner Correction

- Independently reviewed fixed root 94e5269433f3526c82466cb7478f12f2d5fdc055 read-only, excluding own Privacy/Signals sources from independent coverage. Four fake/temporary-fixture guards reproduced startup Thread.start cleanup omission, untracked PCM-transfer close, accepted odd frame_bytes, and build-Venv junction writes outside the owned runtime. Parent owns the first three fixes.
- Parent requested only the build-owner correction here. Fixed review head merged locally as 7a75860, helper CONTEXT retained; Root/runtime untouched. tools/prepare_engines.py now resolves and checks its dedicated build path before downloads/writes, rejects redirected marker/executable/requirements paths, and binds new schema-2 build owner markers to the canonical final runtime. Old pathless/moved markers fail closed without rewriting or adoption.
- Guard-first junction repro failed before the fix, then passed. Twelve package contracts pass, including unchanged old/moved markers and matching owned-build idempotence; full source suite 216 passed, docs/Ruff F/diff green. No wheel/source/package locks changed, no actual wheel built/downloaded/installed for this fix. Full suite's tiny temporary offline fixture remains its existing test behavior.
- Manual fixed-head review guards are intentionally outside acceptance suites at .runtime/reviews/root_94e526_ops_guards.py, compile exact git-show source from 94e5269 and remain red against that historical head. Actual full offline restore/native devices/production migration were not independently re-executed. No new independent finding in wheel hash/pin validation, default-deny target approvals or normal entry activation gate. Ownership remains active.

## Shared Inner Installation Destination Guard

- Windows delta review reproduced an inner Lib/site-packages junction despite a valid path-bound build marker. Corrected the producing boundary once for build and all profile environments: scan owned install trees for escaping links before interpreter probes, then consume pip's actual purelib/platlib/headers/scripts/data scheme and bind it plus sys.prefix to the owned runtime. Repeat after new venv creation; no cached live-path validity.
- Python probes and pip now share -I isolation so ambient PYTHONHOME/PYTHONPATH/cwd cannot change the checked layout. Base-Python stdlib is a read-only input outside the pip scheme and remains allowed. No lock, wheel, model, old-stack or parent runtime changed.
- Guard-first: 20 inner-redirection and 24 actual-prefix/scheme mismatch cases failed before the fix, then passed for wheel-build/controller/STT/TTS. Package fixtures canonicalize their temporary root once, addressing the hosted Windows short-path CI mismatch without relaxing producer checks. Fourteen package contracts and full source suite 218 passed in 20.732 seconds; docs/Ruff F/diff green.
- Real tiny offline fixture restore verifies own install destinations while Base stdlib lives outside the venv. A read-only preflight against this helper's existing STT environment passed in 0.552 seconds (one observation, filesystem cache state and child CPU/memory unmeasured). No model import or GPU use. Hosted CI rerun and Windows delta review belong to the parent; ownership remains active.
