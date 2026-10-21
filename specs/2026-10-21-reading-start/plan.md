# Plan

Change only the text-section producer first. Start with a 120-character budget,
then grow toward the existing 240-character maximum in bounded steps based on
the preceding section. Prefer sentence boundaries in the latter portion of the
window, otherwise whitespace; do not isolate very short opening sentences.
This avoids jumping from a brief greeting straight to a full-size successor.

Retain the existing real-audio alignment, native clock and one-successor pipeline.
Tune the provisional bounds only with real synthetic measurements. A shorter
chunk can change prosody or create starvation; measure both voices and natural
sentences as well as a long sentence. Do not treat character counts as audio time.

Guard first with content/boundary and public first-request tests. Run the complete
contract/integration suite, then compare old/new policy in the same warm workers
using a bounded, explicitly invoked, silent Controller/native-clock probe. Record
CPU/process memory and model-load costs separately. Independently review against
spec and standards, save context/handoff, run hosted checks and integrate the exact
checked head. Deploy only after normal Quit. Hearing acceptance follows restart.
