"""Idle native application lifecycle; never starts speech models or a recording."""
import os
from pathlib import Path
from unittest.mock import patch
import unittest

from hugin.application import Application
from hugin.config import load_settings
from hugin.ui import HuginWindow
from hugin.windows.instance import InstanceGuard


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
    'explicit idle pilot lifecycle')
class NativeApplication(unittest.TestCase):
    def test_idle_pilot_tray_hotkeys_quit_and_mutex_release(self):
        original=HuginWindow.run
        def brief(window):
            self.assertEqual(window.root.state(),'withdrawn')
            window.root.after(250,lambda:window.on_action('quit',None))
            original(window)
        root=Path(__file__).resolve().parents[2]
        with patch.object(HuginWindow,'run',brief):
            self.assertEqual(Application(load_settings(root),pilot=True).run(),0)
        guard=InstanceGuard()
        try: self.assertTrue(guard.acquire())
        finally: guard.close()


if __name__=='__main__': unittest.main()
