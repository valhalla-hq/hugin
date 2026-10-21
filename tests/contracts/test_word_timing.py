"""Original-text alignment boundary, independent of model/device execution."""
import unittest

from hugin.errors import HuginError
from hugin.word_timing import (AlignmentResult, WordTiming, bind_word_timing,
    parse_alignment, alignment_payload)


class WordTimingTests(unittest.TestCase):
    def test_original_offsets_preserve_repetitions_umlaut_emoji_and_punctuation(self):
        text = 'Grüße, Grüße! 🙂 Welt.'
        records = [dict(word=word, tokens=[i], start=start, end=end)
            for i, (word, start, end) in enumerate([
                ('Grüße', 0, .2), (',', .2, .2), (' Grüße', .3, .5),
                ('!', .5, .5), (' 🙂', .5, .6), (' Welt', .7, .9), ('.', .9, .9)])]
        result = bind_word_timing(text, records, list(range(7)), 24000)
        self.assertEqual(result, AlignmentResult('aligned', (
            WordTiming(0, 6, 0, 4800), WordTiming(7, 13, 7200, 12000),
            WordTiming(16, 21, 16800, 21600))))
        self.assertEqual(parse_alignment(alignment_payload(result), text, 24000), result)

    def test_no_string_search_or_partial_token_coverage(self):
        for word, tokens in [('else', [1]), ('word', [2]), ('word ', [1])]:
            with self.subTest(word=word, tokens=tokens):
                result = bind_word_timing('word', [dict(word=word, tokens=tokens,
                    start=0, end=.2)], [1], 24000)
                self.assertEqual(result.status, 'rejected_path')
                self.assertEqual(result.words, ())

    def test_invalid_or_missing_audio_intervals_never_become_estimates(self):
        for start, end in [(0, 0), (-.1, .2), (.3, .2), (0, 2),
                           (float('nan'), .2), (0, float('inf'))]:
            with self.subTest(start=start, end=end):
                result = bind_word_timing('word', [dict(word='word', tokens=[1],
                    start=start, end=end)], [1], 24000)
                self.assertEqual(result.status, 'rejected_path')
        self.assertEqual(bind_word_timing('word', [], [1], 24000).status, 'rejected_path')

    def test_one_alignment_group_cannot_invent_two_word_intervals(self):
        result = bind_word_timing('one\ntwo', [dict(word='one\ntwo', tokens=[1],
            start=0, end=.5)], [1], 24000)
        self.assertEqual(result.status, 'rejected_path')

    def test_reversed_subword_path_cannot_be_hidden_by_combining_intervals(self):
        result = bind_word_timing('word', [dict(word='wo', tokens=[1], start=.3, end=.4),
            dict(word='rd', tokens=[2], start=.1, end=.2)], [1,2], 24000)
        self.assertEqual(result.status, 'rejected_path')

    def test_parser_requires_full_original_lexeme_coverage_and_bounded_exact_fields(self):
        valid = dict(status='aligned', words=[dict(start=0, end=4,
            start_sample=0, end_sample=4800)])
        mutations = [dict(valid, status='unknown'), dict(valid, extra=True),
            dict(valid, words=[]), dict(valid, words=[dict(valid['words'][0], end=3)]),
            dict(valid, words=[dict(valid['words'][0], start=True)]),
            dict(valid, words=[dict(valid['words'][0], end_sample=24001)]),
            dict(valid, status='unavailable_duration'),
            dict(valid, words=[valid['words'][0]] * 601)]
        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(HuginError): parse_alignment(payload, 'word', 24000)

    def test_source_and_audio_bounds_are_checked_before_parsing(self):
        for text, samples in [('a' * 601, 1), ('word', 0), ('word', True),
                              ('word', 1440001)]:
            with self.assertRaises(HuginError):
                parse_alignment(dict(status='unavailable_duration', words=[]), text, samples)


if __name__ == '__main__': unittest.main()
