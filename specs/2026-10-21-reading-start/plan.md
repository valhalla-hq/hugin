# Plan

Change only the text-section producer first. Start with a 120-character budget,
then grow toward the existing 240-character maximum in bounded steps based on
the preceding section. Prefer sentence boundaries in the latter portion of the
window, otherwise whitespace; do not isolate very short opening sentences.
Take the first suitably sized sentence boundary rather than attaching the next
greeting to an already complete section. Keep earlier whitespace as fallback;
a whole token can exceed the soft budget up to the unchanged 240-character hard
bound. Absorb a final remainder up to 40 characters within that hard bound.
This avoids jumping from a brief greeting straight to a full-size successor.

Retain the existing real-audio alignment, native clock and one-successor pipeline.
Tune the provisional bounds only with real synthetic measurements. A shorter
chunk can change prosody or create starvation; measure both voices and natural
sentences as well as a long sentence. Do not treat character counts as audio time.

Initial measurements improved warm starts by 42–50%, but Tyr rejected alignment
for a shifted 105-character remainder and a long sentence left one final word
isolated. The boundary/tail refinements above address these observed cases;
rerun real measurements before acceptance. Do not relax alignment validity.

Guard first with content/boundary and public first-request tests. Run the complete
contract/integration suite, then compare old/new policy in the same warm workers
using a bounded, explicitly invoked, silent Controller/native-clock probe. Record
CPU/process memory and model-load costs separately. Independently review against
spec and standards, save context/handoff, run hosted checks and integrate the exact
checked head. Deploy only after normal Quit. Hearing acceptance follows restart.
