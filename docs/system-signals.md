# Windows operating signals

Bounded T009 source adapter; Application/UI integration belongs to the parent.
No real suspend, device change or Explorer restart was performed for this slice.

```python
from hugin.windows.signals import WindowsSignals

signals = WindowsSignals(lambda action: controller.command(action))
signals.start()
# Keep signals alive, inspect signals.ready / signals.error in component health.
# During application teardown, retain the object until signals.closed is True.
signals.close(timeout=2)
```

`WindowsSignals(on_action, *, backend=None, queue_size=32)` owns an invisible
top-level broadcast window on its own dedicated message thread. No Tk HWND is
required and no existing WNDPROC is read, replaced or restored. Native creation
passes parent `None`, with neither `WS_CHILD` nor `WS_VISIBLE`; it never uses
`HWND_MESSAGE`. Each owned class has a fresh UUID name and current module
instance. Normal-user APIs suffice; no privilege or message-filter changes.

The native callback classifies messages and enqueues only these strings:

| Native observation | Callback action |
| --- | --- |
| WM_POWERBROADCAST / PBT_APMSUSPEND (4) | system_pause |
| WM_POWERBROADCAST / PBT_APMRESUMEAUTOMATIC (18) | system_resume |
| WM_POWERBROADCAST / PBT_APMRESUMESUSPEND (7) | system_resume only if no automatic-resume notification already covered the cycle |
| WM_DEVICECHANGE / DBT_DEVNODES_CHANGED (7), DBT_CONFIGCHANGED (0x18), DBT_DEVICEARRIVAL (0x8000), DBT_DEVICEREMOVEPENDING (0x8003), DBT_DEVICEREMOVECOMPLETE (0x8004) | devices_changed |

Every automatic-resume event starts a fresh notification; the subsequent
user-resume event is deduplicated. The system's suspend event resets that
deduplication state. Device queries and custom events are passed to default
processing, so Hugin never denies a hardware query. No native lParam payload
is dereferenced, retained or logged. No engine, microphone, audio, clipboard,
UI or user-input operation occurs in the window callback.

The caller callback runs on a separate bounded dispatch thread and must only
enqueue its command and return promptly. Queue overflow or callback failure
sets a sanitized `HuginError`, stops action dispatch and makes `ready=False`;
events are not silently dropped while reporting ready. An operational error
is retained independently of cleanup completion.

`ready` means the native window and both owned threads are active and no error
or close request has invalidated them. `closed` means native window/class/
callback resources are released and both threads have actually exited. It is
true before first start because there are no resources. `close()` before
start is final; an owner instance cannot be restarted.

`close(timeout=2)` may be called from the application/UI owner, not from either
signal callback thread. The request executes DestroyWindow and UnregisterClass
on the original native owner thread. The timeout bounds the combined wait for
that acknowledgement and both thread exits. A failed DestroyWindow retains
the HWND, class and callback; a failed UnregisterClass retains the class and
callback after successful window destruction. A live-owner registry prevents
ctypes callback collection while native ownership remains. No PID, HWND search
or foreign-window modification is used to infer cleanup authority.

Keep the owner after a failed close and call `close()` again to retry only its
remaining resources. A healthy retained message thread continues answering
broadcasts even after cleanup failure; an already failed message loop waits for
explicit recovery requests. Cleanup success is checked against the backend's
closed fact. A blocked caller callback keeps `closed=False` even after all native
resources have been released. No forced thread termination or hidden restart
is provided. Late queued actions are discarded after close invalidates dispatch.

## Explorer tray finding

Installed pystray 0.19.5 already registers `TaskbarCreated`, dispatches it to
`Icon._on_taskbarcreated`, and calls `_show()` if the icon is visible. Its Win32
backend deliberately uses a top-level window to receive that broadcast. No
second Explorer recovery implementation was added.

Read-only source observation on 14 October 2026, from the parent controller's
installed package (historical evidence, not an application runtime path):

- pystray/_win32.py SHA256 `de4a968ac1cd519291fde5b13716446a8e5bd8805ab4d9e428ea2e3d66f37fb5`;
  handler mapping near line 46, re-add handler near line 226, top-level creation
  near line 242.
- pystray/_util/win32.py SHA256 `4a3c2d0c81040632f2fb1777644ba8214d58eec1861343a8ce2ca205366d3dff`;
  registered message near line 338.

This static source finding does not establish native Explorer restart behavior.

## Verification and limits

Ten contract guards cover mapping, dispatch thread, queue capacity, callback
failure, stale events, partial start, thread-start failure, cleanup retries and
blocked callbacks. Seven Win32 ABI/producer mocks verify pointer widths, typed
functions, top-level creation, callback lifetime, partial cleanup, foreign-thread
refusal and exception sanitization. Run the ABI file alone with unittest; no
interactive flag is required because every native library is mocked.

These simulations establish adapter behavior only. Actual broadcast delivery,
suspend/resume ordering and latency, modern standby, controller cancellation,
device reopening, and Explorer restart remain native pilot work. Generic
WM_DEVICECHANGE does not provide complete default-audio-endpoint coverage;
IMMNotificationClient::OnDefaultDeviceChanged is the specific endpoint-change
contract and is outside this WM-only slice. Resume notifications are observations,
not an acknowledgement that Windows waited for application cleanup. Old actions
must be invalidated by the parent, never automatically resumed by this adapter.

Primary Windows contracts: [WM_POWERBROADCAST](https://learn.microsoft.com/en-us/windows/win32/power/wm-powerbroadcast),
[automatic resume](https://learn.microsoft.com/en-us/windows/win32/power/pbt-apmresumeautomatic),
[WM_DEVICECHANGE](https://learn.microsoft.com/en-us/windows/win32/devio/wm-devicechange),
[CreateWindowExW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw),
[RegisterClassW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerclassw),
[DestroyWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-destroywindow),
[UnregisterClassW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-unregisterclassw),
[default endpoint changes](https://learn.microsoft.com/en-us/windows/win32/api/mmdeviceapi/nf-mmdeviceapi-immnotificationclient-ondefaultdevicechanged).
