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
handoffs/2026-10-22-tts-throughput.md. Release ownership after the final checkpoint.

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

Both independent review lenses cleared exact head6aa71f6530b9384eb60de1c25ae12072305f5123.
All three hosted checks passed, with fresh PR identity,11-file scope, head and
check readback immediately before squash merge. PR42 merged at07:17:24Z on22 October
as b79073c0e85c66faaea9ae11b45e2042daecd01d. A fresh InstanceGuard protected the
clean stable clone fast-forward from1c598db to that exact main. Reviewed source
tree5e0930eee9589b91c4bddaeb73e056f306e529f0 matches the deployment.

Normal pythonw/launch/root --show start at09:17:40 Europe/Berlin. The freshly
selected own Hugin window was activated and observed showing Bereit für dein
Diktat. No text, hotkey or clipboard was injected. PR43 recorded that deployment
and the pending hearing check; it merged as ed005aa89a3333e3e95cd33398718d495806bfaf.
Only three Markdown files changed, with identical runtime source and checked
main fast-forward while Hugin stayed running.

Brian then explicitly answered that section changes, word marking and transitions
fit both voices. This is user hearing acceptance, separate from the native silent
measurements. Implementation, verification, integration, deployment and acceptance
are complete. No further benchmark or source change is requested. Return path is base
main after normal Quit. Never kill by remembered PID. Whispering/PipPal remain off.
Commit only reviewed code/tests/specs/curated evidence/context/handoff, no raw
audio/model files, personal content or logs. Save and remotely prove both context
and this exact handoff before lifecycle release.

Starter: Hugin natural sections are accepted and complete. Implementation, real
comparison,571 checks, independent review, PR42 integration, guarded deployment
and Brian's both-voice hearing acceptance are finished. Do not repeat completed
GPU tests or reopen this task without a new request. Preserve the measured
limitations and the running source. Release ownership only after the final
checkpoint is clean and remotely proven through the control tool.
