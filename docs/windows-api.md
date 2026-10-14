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
Read-only controls are tracked separately from editable delivery targets.
No window title or document content is retained as identity. Unknown custom
controls lack a verifiable selection and receive the manual copy path.

`capture_selection(cancelled)` returns `captured` with fresh text, or a reason
such as `selection_empty`, `cancelled`, `target_changed`, `clipboard_changed`,
`format_unsupported`, `format_delayed`, `snapshot_limit`, `clipboard_busy` or
`modifiers_active`. Standard Edit selections are read directly with bounded
EM_GETSEL/WM_GETTEXT messages, preserving UTF-16 selection offsets and checking
the bound target before and after reading. They never touch the clipboard;
read-only Edit controls can be read, password controls cannot. The whole
control buffer is bounded before allocation; large controls fail explicitly
even when their selection is short. This is simulated-boundary coverage until
the native target pilot.

Other controls use UI Automation TextPattern in an isolated selection probe.
The implementation uses **comtypes==1.4.17**, a Windows-only dependency with no
required transitive packages. The parent owns its controller lock/installation;
the helper did not change the lock/installation. No custom COM vtable
declarations are added. An explicitly enabled native probe has read only an
owned hidden RichEdit fixture; it has not read the user's foreground selection.

The probe binds GetFocusedElement to the foreground window's UIA ancestor
(at most 64 parents), permitting a renderer PID only when that ancestry is
proven. It uses the nearest TextPattern on that path and GetSelection, requiring
one contiguous range. GetText always receives the positive character bound
`262145` and the UTF-8 result must fit 256 KiB. Multiple/unknown ranges,
password controls and missing identities fail closed. There is no DocumentRange,
ValuePattern or document-full-text fallback. Runtime IDs, focused process,
cloned range endpoints, selected text and the native window target are read
again before returning the text. The service rechecks the caller
target/cancellation after the probe as well.
Immediately before each GetText, the current focused element/runtime ID,
process/foreground target and password status are checked again. The selected
range's enclosing element must also explicitly report non-password status.

`SelectionProbe.read(target, cancelled)` is synchronous and belongs in the
existing capture-effect worker, never the serial controller/UI/input owner.
COM and foreign provider calls run exclusively in its own suspended/assigned/
resumed OwnedProcess family. Initial deadline is 2 seconds including normal
startup; cancellation is polled every 10 ms. Timeout/cancel terminates only the
held job, confirms family exit (up to 3 seconds) and joins its private pipe
threads (one shared 1-second budget) before releasing handles. OS process
creation itself is not an interruptible foreign-provider call. No hard
end-to-end latency is claimed before native measurement.

The probe job has a 256 MiB committed-memory limit; this is not a measured
working-set figure and does not limit memory in a foreign provider's process.
Its request is at most 4092 bytes plus a four-byte length. Its response has a
fixed six-byte version/status/length header and at most 256 KiB of raw UTF-8,
without JSON expansion. Private stderr is discarded and makes the result fail;
malformed/trailing/truncated output never becomes partial selected text.
Failure to terminate/close retains the process owner and blocks another probe.

COM uses an MTA in the child. The explicit CoInitializeEx/CoUninitialize pair
surrounds provider object use, which ends before collection/apartment teardown;
comtypes also balances its own import-time MTA reference at process shutdown.
Before importing comtypes.client, its static `gen` namespace is provisioned
additively only beneath the active Hugin `.runtime/controller` package, and
its resolved paths/writability are checked. A foreign/read-only runtime fails
before client cache initialization, preventing the SDK's user-profile cache
fallback. Existing namespace files are preserved. UIA interface generation then
uses `gen_dir=None` and Python `-B`, so generated interface/bytecode content is
not written by this probe. The static runtime namespace contains no text.
No selection/history files, focus changes or clipboard mutations are added.

Only when direct reading reports an unsupported pattern may the caller use
a private clipboard probe and new sequence;
old clipboard text is never substituted for a missing selection. Clipboard
capture starts disabled per target class: a pilot must explicitly call
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
- Standard Edit/UIA implementations and caret/selection APIs do not establish
  native Word/browser/Codex/PDF coverage. The browser matrix remains unproved.
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
Optional `memory_limit=<bytes>` applies a job committed-memory limit before
creation; its default is None, preserving the model workers' existing contract.
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

`HUGIN_NATIVE_UIA=1` enables `test_windows_uia_native.py` explicitly. Its child
creates only a hidden owned RichEdit, selects synthetic `A😀Z` by EM_SETSEL in
that control, and calls UIA ElementFromHandle/GetSelection/GetText and
CompareEndpoints. It checks its HWND/PID ownership before reading and observes
unchanged foreground HWND/clipboard sequence. No ShowWindow, SetFocus,
SetForegroundWindow, injected keys, clipboard mutation or foreign selection is
used. The child is supervised with the actual OwnedProcess job and private
framing; normal exit/handle cleanup was observed. The first hidden Standard-Edit
attempt reported unsupported TextPattern, so RichEdit is the explicit UIA
fixture (Standard Edit uses WM_GETTEXT in production). This does not test the
production focused-element/ancestor binding or browser/Codex target matrix.
Native timeout/forced family cleanup and a foreign sentinel remain separate.

Relevant primary contracts:
[WM_GETTEXT](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-gettext),
[EM_GETSEL](https://learn.microsoft.com/en-us/windows/win32/controls/em-getsel),
[SendMessageTimeoutW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessagetimeoutw),
[UIA GetSelection](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextpattern-getselection),
[UIA GetText](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-gettext),
[UIA CompareEndpoints](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationtextrange-compareendpoints),
[UIA threading](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-threading),
[comtypes 1.4.17](https://pypi.org/project/comtypes/1.4.17/),
[RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey),
[clipboard operations](https://learn.microsoft.com/en-us/windows/win32/dataxchg/clipboard-operations),
[EnumClipboardFormats](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumclipboardformats),
[AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject),
[CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).

## Tray ownership

`TrayOwner(fresh_pystray_icon).start()` owns a new Win32 pystray 0.19.5 icon.
`close(timeout=2)` confirms closure; `closed`, `ready`, `error`, and forwarded
`title`/`icon`/`menu` are available. Every lifecycle failure is a sanitized
`HuginError` with `owner` pointing to the same retained adapter. Start/close are
single-use; close is idempotent after successful cleanup. Root UI integration
must keep that owner on failure and call `close` again, including constructor
failure before the window has been assigned. No input or engine owner is started.

The pinned producer's public `Icon.stop()` posts a native message, joins only
its setup thread and clears `_running`. It neither checks the post result nor
joins its native message thread. The adapter therefore uses the exact Win32
`_run` in its own held runner and its own held readiness/visibility thread;
it does not call `run_detached` or create pystray's untracked setup thread.
No pystray method is replaced. An existing running icon or another producer
version is rejected before adopting its resources.

Close invalidates visibility, waits for its own visibility thread, waits for
the native runner to establish its own windows, reposts `_stop` to the same
icon regardless of `_running`, and joins that runner. Successful `_run` return
means the pinned native loop's checked window/menu/class cleanup completed.
The adapter then explicitly calls `_release_icon`, which pystray otherwise
defers to a destructor. A silent failed PostMessage, late native startup,
blocked visibility call, thread-start failure or release failure cannot report
closed. The total wait/lock budget is at most the supplied 0–5 second deadline;
this does not forcibly interrupt a stuck native DLL call.

A strong live-owner registry preserves the icon and callbacks even if a caller
loses its exception. Failure before any native window was created can release
the known constructor class. A native loop exception after partial window
creation has no proven cleanup fact: it remains owned and fails closed rather
than manipulating a potentially stale HWND from another thread. No PID/HWND
lookup or foreign-window cleanup is used.

The contracts cover timeout/retry, stop before ready, blocked visibility,
concurrent close deadlines, setup/native thread-start failures, constructor
resource cleanup, sanitized errors and property forwarding. Producer mocks
cover the false `_running` retry and exact constructor/HICON release. The
explicit `HUGIN_NATIVE_TRAY=1` smoke creates only a small synthetic Hugin tray,
then observes both owned threads ended, its own HWND absent from pystray's
registry, released HICON and unchanged foreground HWND/clipboard sequence.
It does not establish Explorer restart, suspend/resume or Shell failure
behavior. Source facts were read from the pinned installed `_base.py` and
`_win32.py`; upstream library internals are deliberately version-bound here.
