"""Section producer contract: bounded warm-up without losing spoken content."""
import unittest

from hugin import coordinator as c


class ReadingStartContracts(unittest.TestCase):
    def test_first_synthesis_request_is_short_without_isolating_greeting(self):
        text = ('Guten Tag. Hugin liest einen langen Absatz mit genauer Wortmarkierung. '
                'Die nächsten Sätze werden während der Wiedergabe vorbereitet. ') * 5
        core = c.Coordinator(instance_id='reading-start')
        core.dispatch(c.ReadToggle())
        job = core.snapshot().job
        core.dispatch(c.SelectionReady(job, text))
        init = core.snapshot().gpu_slot
        core.dispatch(c.EngineReady(init))
        effects = core.dispatch(c.EngineTerminal(init))
        first, = [e for e in effects if isinstance(e, c.BeginEngine)]
        self.assertEqual(first.operation.action, c.Action.SYNTHESIZE)
        self.assertLessEqual(len(first.payload), 120)
        self.assertGreaterEqual(len(first.payload), 80)
        self.assertTrue(text.startswith(first.payload))
        self.assertFalse(any(isinstance(e, c.PlayAudio) for e in effects))

    def test_chunks_preserve_unicode_and_bounded_successor_growth(self):
        for text in (
            ('Grüße! Hier lesen Freya und Tyr gemeinsam einen längeren Text mit Wörtern, '
             'Zahlen wie 12,50 und einem Emoji 🐦.\n') * 9,
            'Wort ' * 200,
            ' \n\t' + 'Wörter und weitere Wörter. ' * 40 + '\n ',
        ):
            with self.subTest(text=text[:20]):
                chunks = list(c.Coordinator._split_selection(text))
                self.assertEqual(''.join(chunks), text)
                self.assertTrue(all(chunk.strip() for chunk in chunks))
                self.assertLessEqual(len(chunks[0]), 120)
                self.assertTrue(all(len(chunk) <= 240 for chunk in chunks))
                for previous, following in zip(chunks, chunks[1:]):
                    self.assertLessEqual(len(following), max(120, len(previous) * 3 // 2) + 40)

    def test_word_boundary_survives_a_late_compound_word(self):
        text = ('Wort ' * 15 + 'Kraftfahrzeughaftpflichtversicherungsgesellschaften '
                'und weitere Worte für die nächste Abschnittsgrenze.')
        chunks = list(c.Coordinator._split_selection(text))
        self.assertEqual([word for chunk in chunks for word in chunk.split()], text.split())

    def test_long_single_word_uses_hard_limit_without_new_fragmentation(self):
        text = 'x' * 180 + ' Hallo.'
        chunks = list(c.Coordinator._split_selection(text))
        self.assertEqual([word for chunk in chunks for word in chunk.split()], text.split())
        self.assertEqual(''.join(chunks), text)
        hard = list(c.Coordinator._split_selection('x' * 1001))
        self.assertEqual(''.join(hard), 'x' * 1001)
        self.assertTrue(all(len(chunk) <= 240 for chunk in hard))

    def test_small_tail_is_kept_with_its_preceding_phrase(self):
        text = ('Bei dieser Sprachprobe lesen Freya und Tyr einen längeren Satz, '
                'während Hugin im Hintergrund den nächsten Abschnitt vorbereitet, '
                'damit die Wiedergabe flüssig bleibt und jedes Wort passend zur '
                'Stimme hervorgehoben wird, auch wenn der Text etwas länger ist '
                'und mehrere Gedanken miteinander verbindet. ')
        chunks = list(c.Coordinator._split_selection(text))
        self.assertEqual(''.join(chunks), text)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[-1].endswith('miteinander verbindet. '))

    def test_next_greeting_is_not_appended_after_a_complete_sized_section(self):
        paragraph = ('Guten Tag. Hugin markiert beim Vorlesen jedes gesprochene Wort. '
                     'Wir machen eine kurze Pause, und lesen dann weiter. ')
        self.assertEqual(list(c.Coordinator._split_selection(paragraph * 3)), [paragraph] * 3)

    def test_short_selections_stay_whole_and_empty_selections_have_no_work(self):
        for text in ('Hallo Welt.', '  Grüße 🐦.\n', 'Wort ' * 24):
            self.assertEqual(list(c.Coordinator._split_selection(text)), [text])
        self.assertEqual(list(c.Coordinator._split_selection('  \n\t')), [])
