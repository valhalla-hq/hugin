"""Opt-in own hidden HWND probe; never reads the user's foreground selection."""
import os
import json
from pathlib import Path
import sys
import unittest

from hugin.windows.clipboard import WindowTarget
from hugin.windows.process import OwnedProcess
from hugin.windows.selection import SelectionProbe


@unittest.skipUnless(sys.platform == 'win32' and os.environ.get('HUGIN_NATIVE_UIA') == '1',
                     'explicit HUGIN_NATIVE_UIA=1 and installed comtypes required')
class NativeUiaFixture(unittest.TestCase):
    def test_own_hidden_richedit_textpattern_without_focus_or_clipboard_change(self):
        fixture = str(Path(__file__).with_name('_uia_fixture_probe.py').resolve())
        def spawn(command, **options):
            return OwnedProcess([*command[:-1], fixture], **options)
        probe = SelectionProbe(spawn=spawn)
        try:
            # Metadata is synthetic; the child selects only its created HWND.
            target = WindowTarget(100, 200, 3, 4, 500, 'HuginSyntheticFixture', None, None)
            result = probe.read(target, lambda: False)
            self.assertEqual(result.status, 'captured')
            self.assertEqual(result.text, 'A😀Z')
        finally:
            probe.close()
