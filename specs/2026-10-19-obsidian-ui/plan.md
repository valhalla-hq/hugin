# Implementation plan

Keep Tk/Pillow and existing owners. Replace the flat presentation with bounded
Pillow-rendered surfaces and an animation canvas. Draw the approved logo using
curves at the owning branding boundary, not a screenshot crop. Static surfaces
are redrawn only on layout; canvas items are reused for motion. Native text and
keyboard controls remain in the layout. Do not infer status from display text.

Extend View with numeric audio_level, monotonic completion_id and producer-owned
completion_until. The microphone owns one scalar meter per capture gate;
Controller publishes it at the existing update cadence. Accepted DeliveryFinished
owns a one-shot visual receipt independently of cue device availability. New
actions/cancellation/errors invalidate the visual while the original sound
ownership and clipboard behavior remain intact. UI consumes that receipt without
inventing/restarting its duration. Status animation and the reduced-motion
preference belong only to the UI. Hidden windows do not paint frames.

Files: branding.py, ui.py and small presentation helpers; audio.py/application.py
for bounded presentation facts; contracts and native UI verification; synthetic
preview entry point; project context/handoff and validation report.

Verify with existing Python 3.12 controller interpreter; no package changes.
Review spec and standards separately. Preserve the current running pilot and
all source/helper dependencies; switch only through the normal own-family quit
and previously established source-pinned launcher. Rollback is the saved d3fd28d
pilot with its unchanged runtime assets. No merges of the earlier draft stack
are inferred from this UI request.
