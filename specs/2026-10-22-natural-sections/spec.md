# Natural reading sections

Brian authorizes implementation of sentence/clause-based section changes and
real Freya/Tyr verification of word timing and smooth transitions. Baseline is
main 1c598dbf90dd5aa1aebf9f47a358f9d87f83ac8f, including accepted codec batch16.

- REQ-001: Prefer complete sentences even when their end occurs before the old
  80-character opening floor. Use a60-character speech floor; short greetings
  should be grouped with more text. Up to40 extra characters may finish a sentence.
- REQ-002: When a sentence cannot fit the bounded preparation window, prefer
  semicolon/colon and then comma or a spaced dash before ordinary word boundaries.
  German/English common abbreviations, initials and numeric separators are not
  independent sentence/clause boundaries.
- REQ-003: Preserve original spoken content, Unicode and ordinary whitespace.
  Never split a normal word; only a token exceeding the existing hard limit can
  require a hard cut. Every engine section remains <=240 characters.
- NFR-001: Keep a small opening and conservative successor growth; at most one
  prepared successor and actual-audio forced alignment/native position remain.
  No new NLP/model dependency, estimated word timings or persistent audio.
- SEC-001: Synthetic-only real probe, no clipboard/microphone/input hooks or
  preferences; InstanceGuard excludes Hugin and owns all workers through cleanup.
- AC-001: Regression fixtures reproduce the early-sentence and ignored-comma
  defects before production changes; fixed outputs end at the expected punctuation.
- AC-002: Pure contracts cover greetings, abbreviations, quotes, decimals/dates,
  long sentences/words, Unicode, hard bounds and conservative growth.
- AC-003: Both real CUDA voices align and mark all words in synthetic sentence
  and clause paragraphs. In the mixed-abbreviation paragraph, record and compare
  any declared fallback rather than invent word times. Measure native transition gaps and
  start/CPU/peak-family memory against current section policy, separating cold
  initialization. Any gap/alignment regression must be addressed before deployment.

Scope is the section producer and directly affected tests/probes. Input bindings,
GUI style, voices, codec batching, startup and clipboard behavior are preserved.
Heuristics do not promise full linguistic parsing of every ambiguous abbreviation.
Overlong unpunctuated text retains a word-boundary safety fallback. Native silent
playback proves scheduling, not auditory prosody; user hearing feedback follows.

Evidence-driven adjustment: the first native trial's58-character opening lost
word marking for Tyr, so the speech floor increases from40 to60. The unchanged
alignment safety rule rejected Freya's number/abbreviation opening in both the
accepted baseline and candidate. AC-003 therefore distinguishes full normal-text
coverage from this pre-existing model limitation, documented since21 October.
No additional rejected section or invented timing is accepted as an improvement.
