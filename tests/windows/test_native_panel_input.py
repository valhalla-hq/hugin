"""Real Windows message dispatch into the controller, synthetic audio/clipboard.

Posted WM_HOTKEY messages prove dispatch, not physical keyboard acceptance.
"""
import os
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'contracts'))
import test_application as app
from hugin import coordinator as c
from hugin.windows.input import WindowsInputs,WM_HOTKEY


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
    'explicit isolated native input check')
class NativePanelInput(unittest.TestCase):
    setUp=app.ApplicationContracts.setUp
    pump=app.ApplicationContracts.pump

    def check_dispatch(self,identity,expected):
        inputs=WindowsInputs(self.controller.command,pilot=True)
        self.controller.inputs=inputs
        inputs.start()
        try:
            self.controller.command('panel_dictation',self.controller.view().panel_token)
            self.pump()
            self.assertEqual(self.controller.core.snapshot().state,c.State.RECORDING)
            self.assertTrue(self.controller.microphone.owned)
            inputs._backend.post(WM_HOTKEY,identity)
            deadline=time.monotonic()+2
            while self.controller.core.snapshot().state==c.State.RECORDING and time.monotonic()<deadline:
                self.controller.pump_once(.01)
            self.pump()
            self.assertEqual(self.controller.core.snapshot().state,expected)
            self.assertFalse(self.controller.microphone.owned)
            self.assertIsNone(inputs.error)
        finally:
            self.controller.command('quit');self.pump()
            inputs.stop()

    def test_native_dictation_dispatch_finishes_button_started_capture(self):
        self.check_dispatch(1,c.State.TRANSCRIBING)

    def test_native_escape_dispatch_cancels_button_started_capture(self):
        self.check_dispatch(3,c.State.IDLE)
