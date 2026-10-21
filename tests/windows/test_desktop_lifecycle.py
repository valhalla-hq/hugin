"""Real idle CLI/tray/input startup twice; no speech, clipboard or UI injection.

Requires the installed Hugin runtime and all other input owners closed. Only
this fixture's own window callback requests ordinary application shutdown.
"""
from dataclasses import replace
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from hugin.__main__ import main
from hugin.activation import activation_record
from hugin.config import load_settings
from hugin.ui import HuginWindow


@unittest.skipUnless(os.name == 'nt' and os.environ.get('HUGIN_INTERACTIVE_TESTS') == '1'
                     and os.environ.get('HUGIN_RUNTIME_ROOT'), 'explicit installed runtime probe')
class NativeDesktopLifecycle(unittest.TestCase):
    def test_two_hidden_normal_launches_preserve_profile_and_release_owners(self):
        root = Path(os.environ['HUGIN_RUNTIME_ROOT'])
        settings = load_settings(root)
        observed = []
        class ObservedWindow(HuginWindow):
            def __init__(self, action):
                super().__init__(action)
                deadline = time.monotonic()+10
                def finish_when_ready():
                    if self._view.status == 'Bereit für dein Diktat' or time.monotonic() >= deadline:
                        observed.append((self._view.status, self.root.state(),
                                         self._view.mode, self._view.dictation_shortcut,
                                         self._view.reading_shortcut))
                        action('quit')
                    else:self.root.after(50, finish_when_ready)
                self.root.after(50, finish_when_ready)
        with TemporaryDirectory() as folder:
            state = Path(folder)
            activation = state/'activation.json'
            original = json.dumps(activation_record()).encode()
            activation.write_bytes(original)
            isolated = replace(settings, paths=dict(settings.paths, state=state))
            for _ in range(2):
                with patch('sys.argv', ['hugin', '--root', str(root)]), \
                     patch('hugin.__main__.load_settings', return_value=isolated), \
                     patch('hugin.ui.HuginWindow', ObservedWindow):
                    self.assertEqual(main(), 0)
                self.assertEqual(activation.read_bytes(), original)
        self.assertEqual(len(observed), 2)  # A surviving singleton cannot pass.
        for status, visibility, mode, dictation, reading in observed:
            self.assertEqual(status, 'Bereit für dein Diktat')
            self.assertEqual(visibility, 'withdrawn')
            self.assertEqual(mode, 'Lokal')
            self.assertIn('Maus zurück', dictation)
            self.assertIn('Maus vorwärts', reading)
