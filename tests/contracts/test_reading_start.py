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
            'x' * 1001,
            ' \n\t' + 'Wörter und weitere Wörter. ' * 40 + '\n ',
        ):
            with self.subTest(text=text[:20]):
                chunks = list(c.Coordinator._split_selection(text))
                self.assertEqual(''.join(chunks), text)
                self.assertTrue(all(chunk.strip() for chunk in chunks))
                self.assertLessEqual(len(chunks[0]), 120)
                self.assertTrue(all(len(chunk) <= 240 for chunk in chunks))
                for previous, following in zip(chunks, chunks[1:]):
                    self.assertLessEqual(len(following), max(120, len(previous) * 3 // 2))

    def test_short_selections_stay_whole_and_empty_selections_have_no_work(self):
        for text in ('Hallo Welt.', '  Grüße 🐦.\n', 'Wort ' * 24):
            self.assertEqual(list(c.Coordinator._split_selection(text)), [text])
        self.assertEqual(list(c.Coordinator._split_selection('  \n\t')), [])
