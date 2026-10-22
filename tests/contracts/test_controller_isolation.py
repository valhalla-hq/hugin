"""Fake-controller fixtures must not consume or overwrite installation state."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import test_application as app


class ControllerIsolationContracts(unittest.TestCase):
    def fixture(self, state):
        settings=app.load_settings(app.ROOT)
        settings=replace(settings,paths={**settings.paths,'state':state})
        fixture=app.ApplicationContracts()
        self.addCleanup(fixture.doCleanups)
        with patch.object(app,'load_settings',return_value=settings):
            fixture.setUp()
        return fixture

    def test_installed_tyr_preference_cannot_change_fake_controller_default(self):
        with TemporaryDirectory() as folder:
            state=Path(folder)
            (state/'preferences.json').write_text('{"schema_version":1,"voice":"tyr"}',encoding='utf-8')
            fixture=self.fixture(state)
            self.assertEqual(fixture.controller.core.snapshot().voice,'freya')
            self.assertNotEqual(fixture.controller.settings.paths['state'],state)

    def test_fake_voice_action_cannot_overwrite_installation_preferences(self):
        with TemporaryDirectory() as folder:
            state=Path(folder);preferences=state/'preferences.json'
            original=b'{"schema_version":1,"voice":"tyr"}'
            preferences.write_bytes(original)
            fixture=self.fixture(state)
            fixture.controller.command('voice','tyr');fixture.pump()
            fixture.controller.command('voice','freya');fixture.pump()
            self.assertEqual(preferences.read_bytes(),original)
