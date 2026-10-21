# Screenshot clipboard preservation

Follow-up from the live PR17 source c378743; retain its UI, cues and field
guards. The manual 09:17:25 MESZ Codex attempt captured its field successfully,
then rejected the clipboard as format_unsupported. A fresh metadata-only copy
shows DataObject, CF_BITMAP, PNG, CanUploadToCloudClipboard,
CanIncludeInClipboardHistory, Ole Private Data, CF_DIB and CF_DIBV5. OLE's public
enumeration contains bitmap/GDI, PNG/IStream, and the two policy DWORDs/HGLOBAL.

- SF-01: Support this screenshot bundle for the existing transactional paste.
  Retain PNG/DIB/DIBV5 and policy bytes exactly; never re-encode the image or
  change the user's history/cloud choices. Windows regenerates bitmap from DIB.
  Mark Hugin's temporary paste payload as excluded from history/cloud processing;
  restoration keeps the original item's policy bytes, without changing OS settings.
- SF-02: OLE transport bookkeeping is not an opaque restorable payload. Omit it
  only after a complete bounded OLE enumeration proves a closed raster-only
  bundle with supported flat data and no hidden file/storage/object formats,
  target devices or indexed content. Unknown/incomplete evidence still rejects
  before materialization or mutation.
- SF-03: Bind OLE proof to the exact native clipboard sequence and format set.
  Materialize before stage; user changes, failed/oversized/delayed reads,
  cancellation, field changes and cleanup preserve existing fail-closed rules.
  Do not weaken the earlier focus guard or conflate the two failure paths.
- SF-04: Probe only metadata in a bounded owned helper. No clipboard writes,
  content, raw pointers or COM object transfer in its protocol. Retain failed
  cleanup ownership. Ordinary clipboard cases avoid the helper entirely.
- SF-05: Pure regressions plus real synthetic OLE raster roundtrip and text
  delivery/restore check. No personal images/logs in Git; no live-source edits.

Non-goals: general OLE object copying, arbitrary registered formats, direct key
typing fallback, production binding/autostart migration, older draft merges.

Acceptance: the observed producer model passes; unknown public OLE media, stale
sequence/set, malformed protocol, timeout/cleanup and unrelated formats reject
without paste. Native fixture preserves image/policy bytes across existing
stage/restore, including OLE access to the restored PNG stream. Final human
Codex screenshot/dictation confirmation remains an explicit acceptance step.
