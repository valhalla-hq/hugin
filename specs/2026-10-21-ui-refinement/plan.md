# Plan

Add an explicit active_action to the presentation View, derived once from the
coordinator state. Cache normal/highlighted tile surfaces at layout time and
switch image references on mode changes. Compose rounded native button images
over exact parent-surface crops; draw focus within rounded geometry while
retaining Tk's native keyboard/click behavior. Keep caches bounded per layout.

Read current sanitized pilot status and clipboard format IDs/names after Brian's
manual reproduction. Then reproduce the confirmed failing boundary with a
synthetic fixture, verify the concrete format/storage contract if applicable,
and make only the narrow preservation-safe fix justified by that evidence.

Use the existing Python runtime. Test producers and native presentation, inspect
synthetic windows, run existing contracts/docs and separate code reviews. Save
PR17 and prepare source-pinned pilot through normal shutdown/return.
