"""Natural speech boundaries through the production section-producer seam."""
import unittest
from pathlib import Path
import sys
from hugin.coordinator import Coordinator
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from probe_reading_start import NATURAL_SENTENCES as SENTENCES, NATURAL_CLAUSES as CLAUSES


class NaturalSectionContracts(unittest.TestCase):
    def assert_natural(self, text):
        chunks = list(Coordinator._split_selection(text))
        self.assertEqual(''.join(chunks), text)
        self.assertTrue(all(part.strip() and len(part) <= 240 for part in chunks))
        self.assertEqual([word for part in chunks for word in part.split()], text.split())
        return chunks

    def test_early_complete_sentence_is_not_followed_by_part_of_next_sentence(self):
        opening = 'Dieser kurze erste Satz soll beim Vorlesen vollständig zusammenbleiben. '
        self.assertLess(len(opening), 80)
        text = opening + SENTENCES
        chunks = self.assert_natural(text)
        self.assertEqual(chunks[0], opening)
        self.assertTrue(all(part.rstrip().endswith(('.', ',', ';', ':')) for part in chunks))

    def test_very_short_first_sentence_gets_more_complete_speech_context(self):
        chunks = self.assert_natural(SENTENCES)
        sentence_ends = [i + 2 for i in range(len(SENTENCES) - 1) if SENTENCES[i:i+2] == '. ']
        self.assertEqual(chunks[0], SENTENCES[:sentence_ends[1]])

    def test_long_sentence_uses_a_comma_before_an_arbitrary_space(self):
        chunks = list(Coordinator._split_selection(CLAUSES))
        self.assertEqual(chunks[0], CLAUSES[:CLAUSES.rfind(', ', 0, 120) + 2])
        self.assertEqual(''.join(chunks), CLAUSES)
        self.assertTrue(all(part.rstrip().endswith(('.', ',', ';', ':')) for part in chunks))

    def test_common_abbreviations_initials_and_numeric_punctuation_stay_in_the_sentence(self):
        examples = (
            'Dr. Müller beschreibt hier z. B. die neue Funktion für 12,50 Euro ausführlich. ',
            'Am 12. Oktober erklärt A. Müller die Funktion und nennt weitere Beispiele. ',
            'In dieser kurzen Lesung beschreibt uns J.R.R. Tolkien eine neue Geschichte ausführlich. ',
            'Prof. Smith explains e.g. the next reading feature with precise word timing. ',
            'Der Hinweis nennt d. h. und u. a. als Beispiele für gebräuchliche Kürzel. ',
        )
        for opening in examples:
            with self.subTest(opening=opening):
                text = opening + 'Ein weiterer Satz macht diesen synthetischen Absatz ausreichend lang. ' * 3
                self.assertEqual(self.assert_natural(text)[0], opening)

    def test_quotes_and_paragraph_breaks_remain_attached_to_complete_speech(self):
        for opening in (
            'Sie sagt: „Dieser erste Satz ist für unsere Leseprobe vollständig.“ ',
            'Dieser erste Absatz enthält eine vollständige Aussage ohne Schlusspunkt\n\n',
            'Dieser erste Absatz nennt eine Bezeichnung und endet mit einer Abkürzung usw.\n\n',
        ):
            with self.subTest(opening=opening):
                text = opening + 'Danach folgt ein weiterer vollständiger Satz für die nächste Anzeige. ' * 3
                self.assertEqual(self.assert_natural(text)[0], opening)

    def test_abbreviation_whitespace_remains_a_word_fallback(self):
        for text in ('Dr. ' + 'x' * 238 + ' und weitere Worte. ' * 20,
                     'Dr. Dr. Prof. ' * 30):
            with self.subTest(prefix=text[:15]):
                self.assert_natural(text)

    def test_short_greeting_belongs_to_following_speech_in_later_sections(self):
        text = ('Dieser erste Satz ist für die synthetische Probe vollständig. '
                'Dieser nächste Satz ist ebenfalls schon vollständig. Guten Tag. '
                'Der weitere Gedanke soll mit dieser Begrüßung zusammenbleiben '
                'und nicht getrennt werden. ') * 3
        chunks = self.assert_natural(text)
        self.assertFalse(any(part.endswith('Guten Tag. ') for part in chunks))

    def test_strong_clause_break_precedes_comma_and_word_fallback(self):
        for punctuation in (';', ':', ' —', ' –'):
            prefix = 'Wir erklären zunächst die neue Funktion und ihre Möglichkeiten ausführlich' + punctuation + ' '
            text = prefix + ('danach folgen noch weitere zusammengehörige Gedanken, ' * 5) + 'bis zum Ende.'
            with self.subTest(punctuation=punctuation):
                self.assertEqual(self.assert_natural(text)[0], prefix)

    def test_close_sentence_end_can_exceed_soft_target_without_splitting_a_word(self):
        opening = 'Wir lesen ' + 'dieses Wort ' * 10 + 'vollständig. '
        self.assertGreater(len(opening), 120)
        self.assertLess(len(opening), 160)
        text = opening + 'Ein weiterer Satz wird währenddessen vorbereitet und später vorgelesen. ' * 3
        self.assertEqual(self.assert_natural(text)[0], opening)

    def test_unicode_long_unpunctuated_input_and_empty_whitespace_stay_bounded(self):
        for text in ('Grüße 🐦 und Wörter ' * 100, 'x' * 180 + ' und weitere normale Wörter. ' * 30):
            with self.subTest(text=text[:10]):
                self.assert_natural(text)
        self.assertEqual(list(Coordinator._split_selection(' \n\t')), [])
        long_token = 'x' * 1001
        chunks = list(Coordinator._split_selection(long_token))
        self.assertEqual(''.join(chunks), long_token)
        self.assertTrue(all(len(part) <= 240 for part in chunks))
