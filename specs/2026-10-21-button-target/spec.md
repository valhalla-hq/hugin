# Preserve the target of a physical panel click

Brian's button-started dictation now stops, but insertion into Codex fails at
native capture with target_unverifiable. No field probe or delivery is attempted.
The physical-click diagnostic reproduces GetForegroundWindow returning NULL
already inside the button's WM_MOUSEACTIVATE callback, through release and
500 ms afterward. Returning MA_NOACTIVATE on the child alone is insufficient.
Synthetic SendMessage/Tk event tests did not cover this cross-application path.

- REQ-001: Clicking either action button preserves the external foreground and
  field/selection. Dictation still captures the field chosen at finish.
- REQ-002: Normal Hugin controls, title bar, taskbar and keyboard interaction
  remain usable; stopping without a valid target still stops and retains text.
- SEC-001: No remembered external target, forced external activation, input hook,
  relaxed target proof, clipboard change or persisted user content.
- OPS-001: Preserve the running source and no-return pilot launcher. Integrate
  only after review/checks; restart normally, with no Whispering/PipPal launch.

Acceptance: repeat the physical Codex-to-action click with technical native
capture success; cover native style/subclass lifecycle and ordinary control
activation, stale commands, stop/cancel and controller contracts. Final live
dictation/reading acceptance remains separate from the no-audio focus probe.

The proposed owning boundary is the top-level Windows activation policy, paired
with the existing child click suppression. WS_EX_NOACTIVATE prevents system
foreground activation; explicit user clicks on normal Hugin controls may activate
only Hugin itself. WS_EX_APPWINDOW retains the taskbar entry. This is a bounded
continuation of the requested buttons, with no target-selection policy change.

Primary reference: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw
and https://learn.microsoft.com/en-us/windows/win32/winmsg/extended-window-styles.
