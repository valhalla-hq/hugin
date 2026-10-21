"""A real owned child exits; no application, clipboard, hotkeys or audio."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('native_pilot_session',ROOT/'tools/pilot_session.py')
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
    'explicit owned child lifecycle check')
class NativePilotSession(unittest.TestCase):
    def test_owned_child_exit_does_not_start_old_apps(self):
        reports=[]
        with patch.object(pilot.os,'startfile') as start:
            code=pilot.run_owned([sys.executable,'-c','raise SystemExit(0)'],ROOT,
                lambda state,**facts:reports.append((state,facts)))
        self.assertEqual(code,0)
        self.assertEqual([state for state,_ in reports],['pilot_running','session_exited'])
        self.assertTrue(reports[-1][1]['own_family_exited'])
        self.assertEqual(reports[-1][1]['started_shortcuts'],[])
        start.assert_not_called()
