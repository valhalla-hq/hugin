"""Synthetic native presentation; no mic, clipboard, hooks or model work."""
import os
import time
import unittest
from hugin.ui import HuginWindow, View


@unittest.skipUnless(os.environ.get('HUGIN_INTERACTIVE_TESTS') == '1',
                     'Explicit isolated UI fixture required')
class NativeMotionContract(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.window = HuginWindow(lambda *args: self.calls.append(args), with_tray=False)
        self.addCleanup(self.window.stop)

    def pump(self, seconds=.18):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            self.window.root.update()
            time.sleep(.005)

    def test_hidden_reduced_and_closed_windows_do_not_run_animation_callbacks(self):
        window = self.window
        window.render(View(status='Aufnahme läuft', activity='recording', audio_level=.4))
        self.pump()
        self.assertIsNone(window._animation_after)
        window.show(); self.pump()
        self.assertGreater(window._frame_count, 1)
        window.hide(); self.pump()
        frames = window._frame_count
        self.pump()
        self.assertEqual(window._frame_count, frames)
        self.assertIsNone(window._animation_after)
        window.show(); self.pump()
        window.motion_toggle.invoke(); self.pump()
        frames = window._frame_count
        self.pump()
        self.assertEqual(window._frame_count, frames)
        self.assertIsNone(window._animation_after)
        window.stop()
        self.assertIsNone(window._animation_after)

    def test_completion_receipt_expires_without_replay_or_canvas_growth(self):
        window = self.window
        window.show(); self.pump()
        now = time.monotonic()
        receipt = View(status='Bereit', activity='idle', completion_id=1,
                       completion_until=now+.2)
        window.render(receipt)
        self.assertEqual(window.motion.phase(time.monotonic()), 'complete')
        window.render(receipt)
        self.assertEqual(window.scene.itemcget(window._labels['status'],'text'), 'Text eingefügt')
        count = len(window.scene.find_all())
        self.pump(.25)
        window.render(receipt)
        self.assertEqual(window.motion.phase(time.monotonic()), 'idle')
        self.assertEqual(window.scene.itemcget(window._labels['status'],'text'), 'Bereit')
        window.hide(); window.show(); self.pump()
        self.assertEqual(window.motion.phase(time.monotonic()), 'idle')
        self.assertEqual(len(window.scene.find_all()), count)

    def test_keyboard_controls_preserve_voice_copy_delete_and_diagnostics(self):
        window = self.window
        window.render(View(text='Synthetisches Diktat', voice='freya'))
        window.voice_buttons['tyr'].invoke()
        window.copy.invoke(); window.clear.invoke(); window.diagnose.invoke()
        self.assertEqual(self.calls, [('voice','tyr'), ('copy',None),
                                     ('clear',None), ('diagnose',None)])
        window.render(View(text=''))
        self.assertEqual(str(window.copy['state']), 'disabled')
        self.assertEqual(window.text.get('1.0','end-1c'), '')

    def test_reveal_after_hidden_completion_expiry_paints_current_static_state(self):
        window=self.window
        window.show();self.pump()
        window.motion_toggle.invoke()
        window.render(View(status='Bereit',activity='idle',completion_id=1,
                           completion_until=time.monotonic()+.1))
        self.assertEqual(window._painted_phase,'complete')
        window.hide();self.pump(.15)
        # No new View is necessary for the producer deadline to expire.
        window.show();window.root.update_idletasks()
        self.assertEqual(window._painted_phase,'idle')
        self.assertEqual(window.scene.itemcget(window._check,'state'),'hidden')
        self.assertEqual(window.scene.itemcget(window._labels['status'],'text'),'Bereit')
        self.assertIsNone(window._animation_after)


if __name__ == '__main__': unittest.main()
