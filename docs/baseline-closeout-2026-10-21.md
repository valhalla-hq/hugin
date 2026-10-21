# Accepted pilot baseline closeout

Brian requested completion/saving of the finished work on 21 October, followed
by the recommended reading expansion. This checkpoint consolidates the final
PR11-18 result, not each superseded sound prototype as a separate release.
The accepted d1331da baseline is retained with one additional integration-review
fix: the resizable main window now shares its explicit 2048-pixel size bound with
the raster producer. Previously a larger window silently received cropped
surfaces. Initial/minimum dimensions and font scale fit the same bounded space;
unsupported raster sizes fail explicitly. The live source remains frozen.

## Acceptance and coverage

| Area | Evidence | Remaining limit |
| --- | --- | --- |
| Word/Codex delivery | Native Word tests; Brian's repeated dictation/overwrite tests | Not the entire field/protection matrix |
| Original Whispering cues | Exact asset hashes, original native playback, controller/cancel tests; subsequent pilot use | No new timed human three-cue study in this closeout |
| Obsidian UI/motion | Native scaling/state checks; Brian confirmed logo/animation | Separate real-device coverage is not inferred |
| Active mode/rounded controls | Native visual fixtures and independent reviews; later live pilot | No blanket accessibility certification |
| Screenshot plus Codex dictation | Brian's success report; 10:22:31 MESZ metadata says submitted/no error/no cleanup | Other image producers/target apps not all accepted |
| Screenshot preservation | Synthetic native PNG/DIB/DIBV5/policy roundtrip; restored PNG read independently | Unknown formats still fail closed |

Whispering's pinned implementation preserves optional clipboard text only.
PipPal's local Qwen reading overlay estimates duration as text length / 17, then
uses syllable/punctuation weights. The accepted next stage is an optional section
reader, not a claim of accurate word synchronization. No reference app is changed.

## Verification

Accepted source d1331da has 462 passing contracts/integration tests; the current
closeout reran that suite: 462 pass in 20.511s before the size fix; documentation
validation passes (19 requirements/17 acceptance criteria). Two new pure geometry
guards pass, and seven native own-window visual checks pass in 3.047s, including
high DPI, requested oversized window, exact canvas/raster dimensions and opacity.
Existing native clipboard evidence remains applicable because that path is
unchanged. No user clipboard mutation, GPU workload or live app input occurs.
Two independent cumulative spec/standards reviews examine main defe3d8..d1331da.
The spec review found no material issues; standards review found the size
contract mismatch, corrected as described above. Independent fix/document reviews
have no remaining findings. Final complete suite: 464 tests pass in 19.000s;
docs validation and diff checks pass. Exact hosted merge proof is in the PR.

## Integration and recovery

Integrate the reviewed final source and closeout docs through one PR to main,
preserving ancestry with a merge commit. PR11-18 become historical incorporated
checkpoints. Retain branches/source/runtime paths while referenced by the live
pilot or needed for recovery; do not erase ignored local assets.
The deployment update may change checked source only after proving config, locks,
assets, workers, protocol/config and process/instance ownership inputs unchanged.
No automatic startup/input migration. The current pilot can keep running at its
exact source head; future launch helpers must be revalidated against new main.

The old target_changed observation and a historical audio_failed without audible
symptom have no newly demonstrated root cause. Full V1 target/device/performance
and login migration remain explicitly open; this is a completed feature baseline,
not a manufactured whole-product acceptance.
