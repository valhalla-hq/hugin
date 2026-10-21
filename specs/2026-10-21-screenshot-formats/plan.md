# Plan

Add a small raster-format policy and isolated OLE FORMATETC reader. The child
enumerates native IDs and public OLE capabilities, applies the closed-bundle
policy, and returns only stable sequence/IDs in at most 2048 bytes. The parent
holds its OwnedProcess through terminal exit and cleanup, with a fixed timeout
and memory budget. No COM references survive the helper.

NativeClipboard registers PNG and documented history/cloud byte formats. Its
snapshot enumerates and classifies once; only OLE screenshot candidates invoke
the proof outside OpenClipboard. After reacquiring the clipboard, exact sequence
and raw formats must match. The existing snapshot/stage/commit/restore contract
then handles the materialized flat bytes; OLE metadata and derived HBITMAP are
excluded by the proven plan, not by a global name whitelist.

Start with pure failing policy/ABI tests, then implement the producer and run
native read-only metadata against the still-available screenshot. Synthetic
native mutation tests run only with a safely restorable initial clipboard and
restore it in finally; never overwrite unsupported initial content. Preserve
the running PR17 worktree. Review independently, save new stacked PR and use
normal app exits for a checked pilot switch.
