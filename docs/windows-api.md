# Windows boundary API

This is the bounded T003/T004 implementation slice, not a completed native
pilot or permission to activate Hugin. Whispering/PipPal remain unchanged.
Imports register no hooks, inject no input and open no clipboard.

## Inputs

`WindowsInputs(on_action, pilot=False, *, backend=None, queue_size=32)` calls
`on_action('dictation' | 'read' | 'cancel')` on a separate dispatch thread.
The callback must hand commands to the controller and return promptly. The
dedicated Windows message thread does no engine/audio/clipboard work. The
bounded command queue fails visibly on overflow; it never silently drops a
toggle and reports ready.

- `start()` registers the requested native inputs; failures raise sanitized
  `HuginError`. Read `.running` together with `.error` for readiness.
- `stop()` waits for loop/dispatch cleanup, raising on failed cleanup. A failed
  owner cannot be restarted in place. Keep its object when cleanup fails.
- `set_cancel_active(bool)` synchronously asks the message thread to register
  or release Escape with `MOD_NOREPEAT`. Failure stops the input owner and is
  explicit; Escape is absent while idle.
- Normal mode reserves XBUTTON1/2 and Alt+Y. One DOWN/UP pair emits one action;
  `INJECTED` is accepted and `LOWER_IL_INJECTED` is excluded.
- Pilot mode has **no mouse hook** and uses Ctrl+Alt+Shift+F9/F10 for
  dictation/read. Do not start normal mode while the old stack owns its keys.

Physical mouse delivery, browser navigation suppression, OS hook removal and
reaction latency still need interactive testing. The mocked suite proves none
of those hardware properties.

## Clipboard and target identity

`ClipboardService(backend=None)` owns serialized clipboard transactions.
`capture_target()` returns `ClipboardResult(status, target=WindowTarget(...))`.
The immutable target stores foreground/focus handles, PID/thread, process
creation time, control class, available caret rectangle and edit selection.
No window title or document content is retained as identity. Unknown custom
controls lack a verifiable selection and receive the manual copy path.

`capture_selection(cancelled)` returns `captured` with fresh text, or a reason
such as `selection_empty`, `cancelled`, `target_changed`, `clipboard_changed`,
`format_unsupported`, `format_delayed`, `snapshot_limit`, `clipboard_busy` or
`modifiers_active`. A private probe and new sequence are required; old
clipboard text is never substituted for a missing selection.
Capture also starts disabled per target class: a pilot must explicitly call
`approve_capture_target_class(control_class)` after checking copy-response
attribution and concurrency for that target. No class is approved by default.
This is distinct from approval of delivery/restore timing.

`deliver(text, target, still_current, *, authorize=None)` returns a result with
`status`, `submitted` and `restored`. It does not press Enter or refocus a
target. Automatic paste is disabled until the caller supplies an explicit
pilot finding using `approve_target_class(control_class, restore_delay)`.
No class is approved by default. The delay must be 20–2000 ms and must be
measured for that class; this is an internal pilot seam, not a product setting.

After staging, the native adapter holds the clipboard open and rechecks its
sequence, hidden owner window, private nonce, target, modifiers and
`still_current()`. It then calls `authorize(transaction)` synchronously on the
caller thread, immediately before SendInput. `ClipboardTransaction` contains
only `transaction_id`, `sequence` and `target`, no text. Returning false yields
`commit_rejected` without native submission. This is the controller's
serialized generation/commit seam; callers must not queue that callback.

Successful SendInput means `submitted`, not proof of text consumption by the
target. A partial Ctrl+V can be reported with `submitted=True`; it must never
be retried automatically. Only keys pressed by Hugin's injected prefix are
released on partial input failure. User-held modifiers prevent the operation
rather than being forcibly released.

`copy(text)` intentionally replaces the clipboard and returns `copied`. It
is the explicit user copy action; it does not restore old content.

The snapshot payload budget is 32 MiB, checked before Hugin copies memory or
empties the clipboard. Supported byte representations are CF_TEXT,
CF_OEMTEXT, CF_UNICODETEXT, CF_LOCALE, registered HTML Format/Rich Text Format,
CF_DIB, CF_DIBV5 and CF_HDROP. A synthesized CF_BITMAP is omitted only when its
DIB source is retained; GDI handles are never treated as HGLOBAL. All native
allocations for a replacement precede EmptyClipboard. Snapshot bytes and
restoration HGLOBALs coexist; 32 MiB is a payload limit, not total process RAM.

Restoration is compare-and-replace under the clipboard lock. A later user
sequence wins. Failed restoration retains the complete snapshot and its
current owned sequence (`recovery_pending`), blocks further automatic work,
and supports `recover()`. A new user copy supersedes that recovery. Explicit
`copy()` may intentionally supersede it. `close()` retries retained cleanup and
must succeed before its owner is discarded.

Important native limits remain open:

- Win32 does not expose an advertised format's pre-read delayed-render state.
  Unknown formats are rejected before GetClipboardData; null/non-HGLOBAL,
  zero-size or sequence-changing materialization is rejected before mutation.
  A supported format can still trigger foreign delayed rendering when read.
  OS-side synthesized allocations and renderer blocking are not bounded by
  Hugin's snapshot payload budget. The relevant target cases need a pilot.
- Sequence and bound owner attribution cannot distinguish a simultaneous user
  copy in the same target process from that target's Ctrl+C response. This is
  not a general native user-copy-preservation proof.
- Clipboard locking protects the final sequence check and SendInput handoff;
  it cannot make a foreign app's later clipboard read atomic. Unproved restore
  timing or target identity keeps automatic delivery disabled.
- Caret/selection APIs do not establish native Word/browser/Codex/PDF coverage.
  No target matrix is approved by this implementation slice.

## Instance and worker ownership

`InstanceGuard().acquire()` uses the current token's SID to derive a
`Local\\Hugin.v1.<hash>` mutex name. It returns false for an existing active
owner. `close()` releases only an acquired mutex on its owning thread, then
closes its held handle. The scope is the current Windows session and user;
it is not a cross-session single-instance promise.

`OwnedProcess(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, startupinfo=None,
close_fds=True, creationflags=CREATE_NO_WINDOW, cwd=None, env=None)` provides
`stdin/stdout/stderr`, `pid`, `poll()`, `wait(timeout)`, `terminate()`, `kill()`
and `close()`. Only PIPE/DEVNULL and explicit inherited handle lists are
supported; no shell, ambient process search or executable-name cleanup exists.
An optional `startupinfo.lpAttributeList['handle_list']` forwards the worker's
private data-pipe handles. Native executable paths must be explicit files.

Creation order is an unnamed KILL_ON_JOB_CLOSE Job Object, CreateProcessW with
CREATE_SUSPENDED and STARTUPINFOEX handle whitelist, assignment to that job,
then ResumeThread. No child can spawn a redirector family before assignment.
`terminate()`/`kill()` address the held job. `poll()`/`wait()` require both a
signaled root handle and zero job ActiveProcesses, so venv launcher exit is
not mistaken for family termination. Call `close()` after terminal observation
to release pipes/process/job handles. If failed construction cannot clean up,
the sanitized exception carries `.owner`; retain and recover it. A failed
cleanup must continue blocking the associated engine slot.

Job containment, inherited private handles, actual venv redirectors and a
foreign sentinel's survival require the parent's explicit native worker test.
The helper did not launch/kill any real worker.

## Verification

`tools/dev.py check --group contracts` runs fake input/clipboard/process
boundaries and configuration checks. `tests/windows/test_windows_abi.py`
verifies x64 structure sizes, exact ctypes signatures and mocked producer
behavior without native effects. It is not the interactive hardware suite.

Relevant primary contracts:
[RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey),
[clipboard operations](https://learn.microsoft.com/en-us/windows/win32/dataxchg/clipboard-operations),
[EnumClipboardFormats](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumclipboardformats),
[AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject),
[CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
