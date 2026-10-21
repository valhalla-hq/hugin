# Reading panel, 21 October 2026

The accepted dictation/UI baseline is integrated through PR19/20. PR21 adds an
optional reading panel: original current-section text, section count, pause /
continue, stop and hide. The main window also provides keyboard controls and a
session visibility control. Hiding does not stop speech. Automatic appearance
preserves the foreground window; native placement failure disables only this
optional display. No reading history or word-time estimator is added.

## Actual implementation and limits

The existing <=400-character synthesis spans are sections. Preparing the next
span does not advance the display: prior audio drains before the next span's
first native submission posts its job-bound section. The display has UI/device
latency and the boundary can introduce a short refill interval; this is section
orientation, not exact sample/word alignment. Live perception remains unmeasured.

Native [waveOutPause](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/nf-mmeapi-waveoutpause)
and [waveOutRestart](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/nf-mmeapi-waveoutrestart)
preserve playback position. The existing PCM capacity and worker credit path
remain bounded. Normal local callback/credit waits belong to playback and may
remain paused beyond the initialization timeout; framing deadlines and bounded
cancel/fault cleanup remain. No second alignment model or audio-file cache.

## Verified candidate evidence

- Full contracts/integration: 471 passed, 18.458s at product head709623c.
- Final native UI/motion/reading subset: 19 passed, 9.535s. This includes one
  pure geometry check; the other checks use owned Windows windows/silent PCM.
- Real Windows waveOut silence remains queued during pause and drains after
  restart. Deterministic output guards also prove PCM preservation and prompt
  paused cancellation. This does not measure audible Freya/Tyr quality.
- Own foreground fixture remains active while panel shows, changes, hides and
  reappears; hidden-main case also passes. Small synthetic work area at scale4
  keeps buttons within the window. Physical mixed-DPI monitor changes are open.
- Before/after guards reproduced timeout misuse and optional placement failure.
  Main-window controls remain available on placement failure. Full visual
  checks retain existing high-DPI/native bounds and voice control appearance.
- A synthetic native preview was visually inspected using Computer Use, then
  closed normally; both main-window actions and the bottom section panel fit.
- Docs validator and diff whitespace check pass. Separate spec review passed
  at709623c and the optional-placement delta, with 95 focused pure tests.
  Standards review also passed without material findings (58 focused pure tests),
  including the optional-placement delta. Final CI evidence is retained in PR21.

No user clipboard, recording, text selection or live speech was used for these
checks. Model/GPU peak memory, agent tokens and live section-transition cost are
unmeasured.

## First pilot and visibility refinement

PR21 merged as a52a51c after all three hosted checks passed for head 5448c79.
After normal old-pilot exit and checked deployment update, that candidate
started at 11:25:18 MESZ. Brian reported that reading generally works, but the
checkbox for reopening the hidden panel was not discoverable enough. He chose
explicit reopening in Hugin over automatic reopening for each new selection.

The main window now has a styled keyboard-accessible button labelled
Mitleseleiste einblenden/ausblenden. Hiding persists across reading jobs within
the app session; showing restores the latest section, including paused state.
No audio/worker or selection changes. Native placement failure still disables
only the optional panel and retains main-window pause/stop.

The existing own-window scenario first failed on the missing button, then
passed using the real controls for hide, paused reopen, next-job retention and
current-text restoration without changing the owned foreground window. Fourteen
native UI/focus/motion checks passed in 7.568s. A synthetic preview was visually
inspected and both hide and reopen were clicked. Independent read-only spec and
standards review found no issues. This is not a new live voice acceptance.

## User pilot acceptance still required

Read a longer selection with Freya and Tyr; pause partway, wait, resume and stop.
Check that no words are lost/repeated, the displayed section is useful, hiding
keeps speech playing, and dictation still takes priority. Verify real monitor
placement and focus while working in the target application. Keep these open
until observed; the previous screenshot/dictation acceptance does not cover them.
