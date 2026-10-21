"""Bounded source-character/sample facts shared by the worker and controller.

Only the producing adapter interprets provider tokens. Consumers receive immutable
spans into the unchanged Python string and the unchanged 24kHz mono PCM.
"""
from dataclasses import dataclass
import math
from numbers import Real
import re

from hugin.protocol import invalid
from hugin.errors import HuginError

SAMPLE_RATE = 24000
MAX_TEXT = 600
MAX_WORDS = 600
MAX_SECTION_SAMPLES = 60 * SAMPLE_RATE
MAX_SECTION_PCM_BYTES = MAX_SECTION_SAMPLES * 2
STATUSES = frozenset(('aligned', 'unavailable_duration', 'unavailable_tokens',
    'unavailable_text', 'unavailable_cancelled', 'rejected_path'))


@dataclass(frozen=True)
class WordTiming:
    start: int
    end: int
    start_sample: int
    end_sample: int


@dataclass(frozen=True)
class AlignmentResult:
    status: str
    words: tuple[WordTiming, ...]


def lexeme_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Keep punctuation attached to original non-space words; skip symbols alone."""
    return tuple((match.start(), match.end()) for match in re.finditer(r'\S+', text)
        if any(char.isalnum() for char in match.group()))


def _source(text, sample_count):
    if (not isinstance(text, str) or not 0 < len(text) <= MAX_TEXT
            or type(sample_count) is not int or not 0 < sample_count <= MAX_SECTION_SAMPLES):
        raise invalid()


def parse_alignment(payload: dict, text: str, sample_count: int) -> AlignmentResult:
    """Parse once at the receiving boundary against its retained original input."""
    _source(text, sample_count)
    if (not isinstance(payload, dict) or set(payload) != {'status', 'words'}
            or not isinstance(payload['status'], str) or payload['status'] not in STATUSES
            or not isinstance(payload['words'], list) or len(payload['words']) > MAX_WORDS):
        raise invalid()
    words = []
    previous_sample = 0
    for word in payload['words']:
        if (not isinstance(word, dict)
                or set(word) != {'start','end','start_sample','end_sample'}
                or any(type(value) is not int for value in word.values())):
            raise invalid()
        item = WordTiming(**word)
        if (not 0 <= item.start < item.end <= len(text)
                or not previous_sample <= item.start_sample < item.end_sample <= sample_count):
            raise invalid()
        words.append(item)
        previous_sample = item.end_sample
    if payload['status'] == 'aligned':
        if not words or tuple((word.start, word.end) for word in words) != lexeme_spans(text):
            raise invalid()
    elif words:
        raise invalid()
    return AlignmentResult(payload['status'], tuple(words))


def alignment_payload(result: AlignmentResult) -> dict:
    return dict(status=result.status, words=[dict(start=word.start, end=word.end,
        start_sample=word.start_sample, end_sample=word.end_sample) for word in result.words])


def bind_word_timing(text: str, records: list, tokens: list[int],
                     sample_count: int) -> AlignmentResult:
    """Bind provider word groups by full token/character coverage, never search.

    A group spanning several original lexemes cannot establish their individual
    timing. Reject it instead of dividing its interval or estimating durations.
    Token probabilities are deliberately not interpreted as timing confidence.
    """
    rejected = AlignmentResult('rejected_path', ())
    _source(text, sample_count)
    if (not isinstance(records, list) or len(records) > MAX_WORDS * 2
            or not isinstance(tokens, list) or not tokens
            or any(type(value) is not int for value in tokens)):
        return rejected
    spans = lexeme_spans(text)
    if not spans:
        return AlignmentResult('unavailable_text', ())
    pieces = []
    character = token = previous_sample = 0
    for record in records:
        if not isinstance(record, dict): return rejected
        word, group = record.get('word'), record.get('tokens')
        if (not isinstance(word, str) or not word or not isinstance(group, list) or not group
                or group != tokens[token:token + len(group)]
                or text[character:character + len(word)] != word):
            return rejected
        start, end = record.get('start'), record.get('end')
        if (isinstance(start, bool) or isinstance(end, bool)
                or not isinstance(start, Real) or not isinstance(end, Real)
                or not math.isfinite(start) or not math.isfinite(end)
                or not 0 <= start <= end <= sample_count / SAMPLE_RATE):
            return rejected
        next_character = character + len(word)
        start_sample, end_sample = round(start * SAMPLE_RATE), round(end * SAMPLE_RATE)
        if start_sample < previous_sample: return rejected
        previous_sample = end_sample
        covered = [index for index, (a, b) in enumerate(spans)
            if a < next_character and b > character
            and any(char.isalnum() for char in text[max(a,character):min(b,next_character)])]
        if len(covered) > 1: return rejected
        if covered:
            pieces.append((covered[0], start_sample, end_sample))
        character = next_character
        token += len(group)
    if character != len(text) or token != len(tokens): return rejected
    words = []
    for index, (start, end) in enumerate(spans):
        matched = [(a, b) for owner, a, b in pieces if owner == index]
        if not matched: return rejected
        words.append(WordTiming(start, end, min(a for a,b in matched), max(b for a,b in matched)))
    try:
        return parse_alignment(alignment_payload(AlignmentResult('aligned', tuple(words))),
            text, sample_count)
    except HuginError:
        return rejected
