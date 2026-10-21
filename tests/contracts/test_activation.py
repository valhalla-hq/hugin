"""Public CLI startup guards; no native input, device or model initialization."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import unittest
from unittest.mock import patch

from hugin.__main__ import main


class ActivationContracts(unittest.TestCase):
    def invoke(self, state, *args):
        settings = SimpleNamespace(paths={'state': state})
        with patch('sys.argv', ['hugin', *args]), \
             patch('hugin.__main__.load_settings', return_value=settings), \
             patch('hugin.__main__.verify_voice_assets'), \
             patch('hugin.application.Application') as app:
            app.return_value.run.return_value = 0
            result = main()
            return result, app.call_args

    def test_normal_launch_persists_and_pilot_never_overwrites(self):
        with TemporaryDirectory() as folder:
            state = Path(folder)
            path = state/'activation.json'
            original = b'{"schema_version":1,"input_profile":"mouse-back-dictation-v1"}\n'
            path.write_bytes(original)
            for args in ((), ('--pilot', '--show'), ()):
                result, call = self.invoke(state, *args)
                self.assertEqual(result, 0)
                self.assertEqual(call.kwargs['pilot'], '--pilot' in args)
                self.assertEqual(call.kwargs['show'], '--show' in args)
                self.assertEqual(path.read_bytes(), original)

    def test_unactivated_and_unknown_profiles_never_construct_application(self):
        with TemporaryDirectory() as folder:
            state = Path(folder)
            for payload in (None, {}, {'schema_version':1, 'input_profile':'old'},
                            {'schema_version':True, 'input_profile':'mouse-back-dictation-v1'}):
                if payload is not None:
                    (state/'activation.json').write_text(json.dumps(payload), encoding='utf-8')
                result, call = self.invoke(state)
                self.assertEqual(result, 1)
                self.assertIsNone(call)
            result, call = self.invoke(state, '--pilot')
            self.assertEqual(result, 0)
            self.assertTrue(call.kwargs['pilot'])
