# Reading panel implementation plan

1. Extend the existing reducer with an immutable section descriptor and job-bound
   playback-start/pause events. Keep generation position separate from played
   position; clear both at the existing job ownership boundary.
2. At the serial audio executor, drain the previous section before submitting
   the first PCM of the next. Publish section identity only at successful output.
   Use native waveOutPause/Restart under the existing output lock, independently
   of a blocked audio writer. Preserve byte capacity and prompt reset.
3. Correct timeout ownership: initialization/framing retain deadlines, but a
   local playback callback and normal credit wait may legitimately last while
   paused. Cancellation/fault still wake both and retain bounded writer cleanup.
   No new IPC command or engine model dependency is needed.
4. Add a small native Tk panel using the existing Obsidian controls. Automatic
   display uses a checked no-activation Windows adapter and the foreground
   monitor's work area. Add a session visibility toggle and pause/stop controls
   to the main UI for keyboard operation. Controls carry reading-job identity.
5. Verify reducer and transport guards, synthetic controller flow, native own
   window focus/geometry, and silent native pause/resume. Review the full delta
   with separate spec/standards lenses, save an exact handoff and Draft PR.

## Compatibility and rollout

No config/preferences migration. Existing voice preferences, cues, clipboard and
dictation paths stay intact. New display data is RAM only. Do not update the
deployment worker sources while the old pilot can still start workers there.
The old source/helpers remain available; switch only after a checked candidate
and normal app exit. Live voice/multi-monitor acceptance is a separate explicit
test, not inferred from fake or native silent fixtures.

## Main risks

Native activation can steal selected text; test at the owning show boundary.
Paused backpressure must not be timed as failed initialization or prevent cancel.
The section boundary may have device latency; do not advertise word precision.
Pause failures surface as an audio error and use existing cancellation cleanup.
