from pathlib import Path
import shutil
import tempfile
import unittest

from hugin.config import load_settings, verify_voice_assets
from hugin.errors import HuginError

ROOT = Path(__file__).resolve().parents[2]


class ConfigurationContract(unittest.TestCase):
    def test_both_approved_voice_identities_are_preserved(self):
        settings = load_settings(ROOT)
        self.assertEqual(settings.default_voice, 'freya')
        self.assertEqual(settings.voices['freya'].source_id, 'deutsch-3')
        self.assertEqual(settings.voices['tyr'].source_id, 'deutsch-a')
        verify_voice_assets(settings)

    def test_invalid_budget_does_not_become_default(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'config', root / 'config')
            config = root / 'config/hugin.toml'
            config.write_text(config.read_text().replace('capture_bytes = 16777216', 'capture_bytes = true'))
            with self.assertRaises(HuginError) as error:
                load_settings(root)
            self.assertEqual(error.exception.code, 'config_invalid')

    def test_model_paths_cannot_depend_on_old_installations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'config', root / 'config')
            config = root / 'config/hugin.toml'
            config.write_text(config.read_text().replace('.runtime/models/stt', '../old/model'))
            with self.assertRaises(HuginError):
                load_settings(root)

    def test_modified_reference_is_rejected_before_worker_start(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / 'config', root / 'config')
            shutil.copytree(ROOT / 'assets', root / 'assets')
            (root / 'assets/voices/deutsch-3/referenz.wav').write_bytes(b'changed')
            with self.assertRaises(HuginError) as error:
                verify_voice_assets(load_settings(root))
            self.assertEqual(error.exception.code, 'asset_integrity')
