# Hugin: aktueller Cursor statt früherer Feldbindung

- Repository: valhalla-hq/hugin, private; runtime Mjolnir.
- Task: current-cursor-delivery; ownership active.
- Branch: codex/current-cursor-delivery-mjolnir.
- Worktree: C:/Users/brian/brian-projects/worktrees/hugin/current-cursor-delivery-mjolnir.
- Base: e82e9a625f897a0eda33479637a3a802bd2d2636.
- Control/preflight:46e362d1d3284d712757fc2f0e67a165dbf3a41c, current.
- PR: https://github.com/valhalla-hq/hugin/pull/50 (Draft; exact branch).
- Spec/plan/tasks: specs/2026-10-23-current-cursor/.
- Evidence/limits: docs/current-cursor-2026-10-23.md.

Brian requests reliable insertion at the current cursor despite target switches
and comparison with Whispering. Diagnose supplied23October: native capture,
UIA target_unverifiable, clipboard copied, no paste. Parallel technical samples
show transient non-text Codex focus and later valid Edit; do not claim the
specific failed internal sample was captured. No raw text/images/audio retained.
Whispering pinned source confirmed clipboard + current-focus Ctrl+V.

Implemented source candidate1.0.1: no stop-target transport, current native
focus selected on the serial commit owner after the queue, no UIA delivery gate.
Removed obsolete field proof/protocol; reading's selection reader remains.
Clipboard generation/transaction/token, cancel, modifiers, one-shot/partial
input and native focus guards preserved. config v3=current_focus; no preference
or activation migration. Tests now express the newly requested semantics.

Regression was red before production changes (no chord after window switch)
and green afterwards. Focused128 tests and33 selection/policy tests passed;
29 mocked Win32 ABI tests passed. Current-cursor/native focused12 pass.
First full run524 cases found stale fake signatures, a remaining removed
target-mode decoder and HEAD-export/config mismatch; corrected. Full531 cases
passed36.569s on16d0036. Independent spec/standards reviews found a native
password change/timeout race and two stale opt-in native fixtures. Corrected
with red/green password guards;41 focused current/native/ABI cases pass.
The real hidden RichEdit selection reader passes0.502s without clipboard/focus
changes. Coverage reinstates during-recording switches, owner/size/token
conflicts and callback weakref release; independent follow-up clears all eight
current-cursor cases. Final-source531 cases pass34.047s on9b2b40c, docs19/17
without problems; all three hosted checks succeed at that head. Real native
clipboard publication/owned-Edit consumption/restoration passes0.071s after
Brian explicitly loaned the diagnostic clipboard and quit Hugin normally.
The diagnostic clipboard is restored and Brian was told copying is free again.

App-only candidate built at
C:/Users/brian/Hugin-Releases/1.0.1-9b2b40c586ac/app.
Frozen source9b2b40c586ac0047ceb4bb64710368cd42233d50,
src b5a2047fc48a7c6314e32b5947c33081889ff6f9.40365 payload files,
11596014819bytes; build229.665s, builder CPU79.328s (family CPU/peak and agent
tokens unmeasured). All private runtimes verify: controller7, STT21, TTS94 fixed
packages; no mic/clipboard/audible output, no owned cleanup pending. Private
probe59.699s, CPU30.828s; per-profile peak job commit45.8/838.3/2720.4MB.
Using the actual candidate Python/source,43 tests pass4.960s with no skips:
eight current-cursor, four native-focus,29 mocked Win32 ABI, one real hidden
reading fixture, one two-start native profile/lifecycle fixture. No extra
physical mouse, spoken words or actual Windows-login result is claimed.

Candidate state preparation completed: activation/preferences bytes unchanged,
40 exact-producer DSP cache files preserved, session mutex held during prep,
no startup migration. Ready receipt: build-evidence/candidate-ready.json.
Hugin.exe --show launched23October08:45:47 CEST from the candidate root.
Own child and own Hugin window are observed; Canvas labels are not exposed by
UIA, so visible-ready/status/binding labels are unknown, not absent. The two
isolated real starts above did observe Ready and both binding hints. Existing
production root/start-menu/startup stay at1.0.0; no promotion without installer.

Physical feedback at06:48:57UTC: Brian confirms Codex and Google search work,
but switching from Codex to a Teams message field rejects.1.0.1 diagnosis:
capture_native=target_unverifiable, capture_field=not_required, clipboard=copied,
delivery=target_unverifiable. This is a native focus boundary, not UIA. Leading
hypothesis is a different process for Teams' focused WebView field versus outer
frame is now proven: after Brian's ready reply,22-second native-only observation
records110/110 samples of TeamsWebView with focused Chrome_WidgetWin_1.
GUI focus exists; IsChild and GA_ROOT both confirm embedding, while PID and
thread differ. All110 samples reject at the same-PID gate. No chat/title/
clipboard text was read. Observer: .runtime/native_focus_observe.py.

Teams source fix1.0.2: native producer now requires valid focus identity and
foreground==focus or IsChild(foreground,focus), not equal PIDs. The same guard
runs after native waiting reads and after authorization before the one chord.
No Teams-specific list, old-window activation, UIA delivery gate or retry.
Foreground process metadata retain their meaning; UIA reading has its separate
focus process identity; shipped clipboard-selection fallback remains empty.
Two controller/native repros red before fix;46 focused cases pass0.035s and
536 full contracts/integration cases pass40.866s. Docs19/17 no problems.
Independent spec and standards followups clear this exact source diff against
1207baf; standards reviewer independently ran8 native cases0.001s, no GUI/input.
An additional inactive-Teams structural probe could not obtain focus and is
not a pass; a later parallel22s sample was Codex only, also not Teams acceptance.
No content or clipboard reads and no focus/input changes by these probes.
Brian confirmed normal Quit. New immutable app-only candidate is built at
C:/Users/brian/Hugin-Releases/1.0.2-3fd3ca9988c2/app from
3fd3ca9988c20eb530d62f427e73ce78ce14e6d3, src13be3f870ab797c8ea6ebbd061821727c59a4be9.
40365 payload files,11596016330bytes; build226.692s wall/79.203s builder CPU.
Family CPU/peak and agent tokens unmeasured. All private runtime imports pass
(7/21/94 packages),35.950s wall/22.172s CPU; per-profile peak job commit
46342144/838729728/2721583104bytes, cleanup_pending=false, no audio/mic/clipboard.
Using actual candidate interpreter/source,48 tests pass1.590s, no skips,
including real hidden reading fixture and two normal hidden input-profile starts.
Activation/preferences bytes match1.0.1,40 same-producer DSP caches preserved.
Startup link remains1.0.0, identical SHA256
4ca885f37b7a2d001439761696ee44eacefa5e7dba41fe8daf764225e4e1db95.
Evidence retained in the candidate's build-evidence folder with per-file hashes.
Normal Hugin.exe --show launch09:10:34CEST observed wrapper40340 and own child
46076 with its Hugin window. Historical PIDs are not termination authority.
Canvas readiness labels are unknown for this visible launch; both isolated
normal starts above did verify Ready and both input bindings. Actual Teams
paste is now physically confirmed via Alt+Y. Brian reports rear mouse has no
effect only in Teams, while it still works in Codex. This is separate from paste.
All three hosted checks succeed at3fd3ca9. No installed/startup migration.

Read-only Options+ SQLite/JSON inspection finds application_id_microsoft_teams_new
overrides for MX Master3: c83=card_teams_win_toggle_mic (Ctrl+Shift+M),
c86=card_teams_win_toggle_camera (Ctrl+Shift+O). Base profile has
card_global_presets_win_back / win_forward (WIN_BACK/WIN_FORWARD).
No change to Hugin's hook is justified by this evidence. An unstarted passive
XBUTTON observer was removed once the profile explained the application split;
no mouse/keyboard hook probe executed, no extra recording/input generated.
Before-image of exactly the two relevant assignments saved outside Git at
C:/Users/brian/Hugin-Releases/1.0.2-3fd3ca9988c2/build-evidence/logi-teams-side-buttons-before.json.
This is not a whole user-settings DB copy. Source DB opened mode=ro/query_only.
Options+ native UI opened via its existing executable. Native UI control is
unavailable here; async question asks Brian to set rear=normal Back and
front=normal Forward in the Teams profile, then test Teams dictation start/stop.
Do not directly mutate its live SQLite DB or intercept Teams microphone/camera
shortcuts. On reply, read just these two profile assignments again and record
physical result; no new Hugin build is needed for the vendor-profile correction.

Build-tool constraint: previous isolated Inno compiler was removed with the
earlier worktree; automatic approval review rejected its re-provisioning
command with only "blocked by policy". Do not retry that action through a
different tool/launcher. App-only payload preparation uses already-present
Windows csc, pinned offline wheels and existing production materialization
functions. New1.0.1 installer is not claimed;1.0.0 installer remains retained.

Earlier installed1.0.0 remains unchanged at
C:/Users/brian/AppData/Local/Programs/Hugin/releases/1.0.0-3b6bc4304a87.
Immutable installer/build/rollback evidence remains under
C:/Users/brian/Hugin-Releases/1.0.0-3b6bc4304a87.
Whispering/PipPal stay disabled. Do not quit a live user app by remembered PID.
Normal Hugin Quit is required before a later update switches the installed app.
No logout, reboot, unrelated installation or new scheduler.

Separate open Save: PR49 / codex/input-login-acceptance-mjolnir at
e9e59a66f52e7bc2c49b60967d1d1451e8c7e72c contains Brian's manual restart and
four successful physical mouse/hotkey flows on22October. Keep its worktree and
ownership untouched. That did not prove a new Windows login; login stays open.

Next: await Brian's Options+ Teams side-button change and physical mouse result,
verify targeted configuration readback, then finish checked private source
integration under the central lifecycle. Paste via Alt+Y is accepted. If the
mouse still fails despite normal Back/Forward assignments, observe only bounded
technical side-button events before changing code; never patch a live release.
Do not promote the
app-only candidate into installer ownership or silently change1.0.0 shortcuts.
Preserve existing installed1.0.0/startup/profile and its installer; new installer
blocked as above. Teams mouse acceptance remains open until verified.
Routine checked private integration is within this fix request; no check bypass.
Paste still relies on target consumption of Ctrl+V and does not claim all apps.

Starter: continue this exact current-cursor-delivery handoff, inspect Git/PR
and ownership, finish the bounded cursor fix. Do not resume old production work
or confuse PR49's successful manual restart with Windows-login evidence.
