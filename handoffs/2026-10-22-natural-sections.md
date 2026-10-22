# Hugin natural reading sections

Brian explicitly requests implementation of complete-sentence or suitable-clause
sections and tests with Freya/Tyr, preserving word timing and smooth transitions.
Routine checked private integration and normal guarded deployment are authorized.

Repository valhalla-hq/hugin, runtime Mjolnir; task hugin-natural-sections.
Exclusive worktree C:/Users/brian/brian-projects/worktrees/hugin/hugin-natural-sections-mjolnir,
branch codex/hugin-natural-sections-mjolnir. PR42:
https://github.com/valhalla-hq/hugin/pull/42. Base main
1c598dbf90dd5aa1aebf9f47a358f9d87f83ac8f. Control/preflight
05181f9a99374ff8b298c626f903304f36ac8926. No open PR at task start.
Specs: specs/2026-10-22-natural-sections/. Prior accepted throughput task:
handoffs/2026-10-22-tts-throughput.md. Ownership remains active.

The new pure reading_sections producer owns punctuation interpretation once;
Coordinator retains its existing producer seam and consumes original slices.
Sentence ends take precedence, then strong clauses/commas and bounded word fallback.
Opening soft target120, speech floor60, natural-boundary allowance40, hard240;
successors grow conservatively with one prepared successor. Short trailing
sentences stay with following speech where the natural window allows it.
Input/clipboard, models, codec batch16, startup, GUI and timing rules are unchanged.

Original early-sentence and comma guards failed before implementation. Reviews
found word/paragraph facts lost after abbreviation matches, contiguous initials,
and short greetings at later section tails. Each has a regression guard; word
and paragraph facts now exist independently of sentence interpretation. The17
focused guards pass. Final full suite571 passes in22.428s; docs check and diff
whitespace check pass. Source candidate8a50dd91927a6312dafc40a3c2e865daf6dad96f
is pushed and both context/handoff blobs are proven at the matching remote head.

Brian normally quit Hugin for exclusive synthetic GPU measurement. Initial40-floor
trial: all normal Freya words and clause words for both voices marked; Tyr's very
short58-character opening was rejected. Candidate was revised to group the whole
next sentence within160. The final native comparison restores all31 sentence
and40 clause words for both voices; maximum added scheduling gap1.73ms. Freya's mixed
number/abbreviation opening is rejected in both accepted baseline and candidate,
an existing documented alignment limitation. Preserve that negative evidence;
never stretch or estimate word times to obtain a pass. The baseline unmarked
source range[0,81) shrinks to[0,74); actual marked words36→38 of52. Tyr marks52/52.
Evidence, cold/warm times, CPU/memory and limits: docs/natural-sections-2026-10-22.md.
Whole-sentence preparation costs about0.91s extra startup in one fixture; clauses
start0.20–0.28s earlier. Both probes closed all workers/resources; raw reports ignored.

No deployment yet. Remaining: final evidence review, exact-head hosted CI,
checked merge, guarded deployment and user hearing.
No hearing acceptance is inferred from silent native playback. Return path is base
main after normal Quit. Never kill by remembered PID. Whispering/PipPal remain off.
Commit only reviewed code/tests/specs/curated evidence/context/handoff, no raw
audio/model files, personal content or logs. Save and remotely prove both context
and this exact handoff before lifecycle release.

Starter: Continue Hugin natural sections from this exact handoff. Finish revised
Freya/Tyr validation and preserve any negative evidence. Finalize review/checks,
integrate the exact checked head, deploy under InstanceGuard, then obtain hearing
feedback for sentence/clause transitions and word marking. Do not reopen unrelated
performance, clipboard, shortcut or packaging work.
