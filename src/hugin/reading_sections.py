"""Bounded original-text sections at natural speech boundaries, without I/O."""
from bisect import bisect_right
from collections import deque
import re


# These deliberately conservative DE/EN forms must not start a new sentence.
_ABBREVIATIONS = frozenset(('dr', 'prof', 'nr', 'bzw', 'ca', 'inkl', 'usw', 'etc',
    'vgl', 'ggf', 'hr', 'fr', 'str', 'abs', 'art', 'st', 'co', 'mr', 'mrs', 'ms',
    'vs', 'z.b', 'd.h', 'u.a', 'u.u', 'v.a', 'z.t', 'e.g', 'i.e'))
_MONTHS = frozenset(('januar', 'februar', 'märz', 'april', 'mai', 'juni', 'juli',
    'august', 'september', 'oktober', 'november', 'dezember', 'jan', 'feb', 'mär',
    'apr', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dez'))
_CLOSERS = "\"'”’“‘»)]}"
_BREAKS = re.compile(r'[.!?…]+[' + re.escape(_CLOSERS) + r']*\s*|[;:,—–]['
                     + re.escape(_CLOSERS) + r']*\s+|\s+')


def _period_ends_sentence(text, start, end):
    prefix = text[max(0, start - 32):start + 1]
    token = re.search(r'([\w.]+)\.$', prefix)
    previous = token[1].casefold().strip('.') if token else ''
    initials = previous.split('.')
    if previous in _ABBREVIATIONS or all(len(part) == 1 and part.isalpha() for part in initials):
        return False
    # 12. Oktober / 1. weiterer Punkt: ordinals, not sentence endings.
    if previous.isdigit() and end < len(text):
        following = re.match(r'\w+', text[end:end + 16])
        if following and (following[0][0].islower() or following[0].casefold() in _MONTHS):
            return False
    return True


def _boundaries(text):
    sentences, strong, commas, words = [], [], [], []
    for match in _BREAKS.finditer(text):
        raw, end = match[0], match.end()
        first = raw[0]
        spaced = raw[-1].isspace()
        # Word separation exists even when punctuation is not a sentence end.
        if spaced:
            words.append(end)
        if '\n' in raw or '\r' in raw:
            sentences.append(end)
            continue  # Paragraph breaks also apply after an abbreviation.
        if first in '.!?…':
            if not spaced and end < len(text):
                continue  # Decimal, domain, or another within-token dot.
            punctuation = raw.rstrip().rstrip(_CLOSERS)
            if punctuation == '.' and not _period_ends_sentence(text, match.start(), end):
                continue
            sentences.append(end)
        elif first in ';:':
            strong.append(end)
        elif first == ',':
            commas.append(end)
        elif first in '—–':
            if match.start() and text[match.start() - 1].isspace():
                strong.append(end)
    return sentences, strong, commas, words


def _within(boundaries, start, end):
    return boundaries[bisect_right(boundaries, start):bisect_right(boundaries, end)]


def split_reading_sections(text: str) -> deque[str]:
    """Sentence first; clauses before word fallback, all slices <=240 characters.

    The opening soft budget is 120 with a 60-character speech floor. Later budgets
    grow by half the previous section, floor 120 and hard cap 240. Up to 40 extra
    characters may finish a natural phrase. Whitespace-only spans need no speech.
    Punctuation is parsed once; neither source text nor word offsets are rewritten.
    """
    sentences, strong, commas, words = _boundaries(text)
    chunks = deque()
    offset, budget = 0, 120
    while offset < len(text):
        hard_end = min(offset + 240, len(text))
        soft_end = min(offset + budget, hard_end)
        natural_end = min(offset + budget + 40, hard_end)
        if len(text) <= natural_end:
            end = len(text)
        else:
            floor = offset + 59
            nearby = _within(sentences, offset, natural_end)
            # Do not leave a short trailing sentence (e.g. a greeting) behind
            # when its following speech can start the next section with it.
            eligible = [end for index, end in enumerate(nearby)
                        if end > floor and (not index or end - nearby[index - 1] >= 40)]
            if not eligible:
                # Several short sentences can supply enough speech together.
                # Greeting preference must never erase every natural boundary.
                eligible = [end for end in nearby if end > floor]
            complete = [end for end in eligible if end <= soft_end]
            if complete:
                end = complete[0] if not chunks else complete[-1]
            else:
                after = [end for end in eligible if end > soft_end]
                end = after[0] if after else None
            if end is None:
                for kind in (strong, commas):
                    before = _within(kind, floor, soft_end)
                    after = _within(kind, soft_end, natural_end)
                    if before or after:
                        end = before[-1] if before else after[0]
                        break
            if end is None:
                before = _within(words, offset, soft_end)
                after = _within(words, soft_end, hard_end)
                end = before[-1] if before else after[0] if after else hard_end
        chunk = text[offset:end]
        if chunk.strip():
            chunks.append(chunk)
            budget = min(240, max(120, len(chunk) * 3 // 2))
        offset = end
    return chunks
