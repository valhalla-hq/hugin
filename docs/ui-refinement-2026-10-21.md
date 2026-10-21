# Active workflow and rounded control refinement

Brian resumed the paused UI/screenshot task on 21 October. The approved logo,
animation and original Whispering cues remain unchanged.

## Behavior

The Controller exposes `active_action` from coordinator state. Dictation stays
light blue through start, recording, transcription and delivery; reading stays
light blue during preparation and playback. Idle, cancellation and error clear
both tiles. The canvas switches between two cached images per tile.

Rounded native buttons now composite over an exact crop of their parent
surface, including every hover and focused frame. Focus is drawn inside the
rounded outline. Native keyboard activation, disabled state and voice selection
remain intact. Frames are bounded at seven normal plus seven focused images
per button, replaced on layout; no per-update raster cache accumulates.

## Screenshot/dictation evidence

The existing source-pinned d395f1e pilot was restarted at 08:42:43 MESZ after
fresh process checks found no matching Hugin, Whispering or PipPal family.
Its product source and diagnostic helpers were kept unchanged.

Brian's manual screenshot/dictation attempt at 08:46:21 MESZ failed with
`capture_native=native_target_captured`, `capture_field=target_changed`,
`delivery=not_attempted`, no pending cleanup. The bounded rejection trace
identifies `selection_probe.py`, `_field_pattern`, line 168. Producer SHA256:
`588829e4aa16673711b1065b2c84fbdcd9bfc6de95495236fedf42d994dd0e93`.

That branch rejects an absent focused UIA element or a false keyboard-focus
flag. It runs before clipboard snapshot/paste. The trace does not distinguish
those two conditions or prove whether the user-visible cursor stayed in the
composer. The precise cause is therefore still unresolved. Do not conflate
this observation with the separate 19 October `format_unsupported` report.

The later read-only format enumeration found a stable list of CF_UNICODETEXT,
CF_LOCALE, CF_TEXT and CF_OEMTEXT, all supported. It fetched no data handles
or clipboard contents and changed nothing. The supplied diagnostic had already
been copied, so this is not proof of the original screenshot formats.

No target guard or clipboard contract is relaxed. The next comparison is a
manual attempt with the same attachment, explicit click into the composer,
visible writing cursor, then dictation without changing focus. An absent
focus is not authorization to guess another input field.

## Verification

- 453 contract/integration tests with the existing Python 3.12.10 runtime and
  `-S`: pass in 27.513 s. No dependency changes.
- 40 focused UI/motion/startup/presentation checks: pass in 6.718 s. Additional
  three native window lifecycle/focus guards: pass in 0.807 s.
- Native fixtures cover preferred/minimum layouts at 100/150/200% scale,
  mode alternation without image-count growth, corner pixels matching their
  parents during hover/focus, and native keyboard/disabled behavior.
- Two independent read-only reviews: no material findings. Spec lens ran
  65 pure checks; standards lens ran 43. These reviewers did not inspect
  native rendering or operate devices.
- Docs validator: 19 requirements, 17 acceptance criteria, no problems.

Native synthetic recording and reading previews showed the correct active tile
and parent-matching voice-button corners. Both exited automatically. Exact-head
CI is checked before pilot launch. These checks do not certify the unresolved live Codex case.
Personal screenshots, dictation, clipboard contents and raw logs stay out of Git.
