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
    def test_own_hidden_richedit_cursor_partial_full_unicode_and_changed_selection(self):
        fixture = str(Path(__file__).with_name('_uia_field_fixture_probe.py').resolve())
        def spawn(command, **options):
            return OwnedProcess([*command[:-1], fixture], **options)
        probe = SelectionProbe(spawn=spawn, timeout=2)
        try:
            target = WindowTarget(100, 200, 3, 4, 500, 'HuginSyntheticFixture', None, None)
            result = probe.read(target, lambda: False)
            self.assertEqual(result.status, 'captured')
            report = json.loads(result.text)
            self.assertEqual([case['case'] for case in report['cases']],
                             ['cursor', 'end_cursor', 'partial', 'full', 'unicode'])
            self.assertEqual([case['selection'] for case in report['cases']],
                             [[7,7], [23,23], [7,18], [0,23], [1,6]])
            self.assertTrue(all(case['replacement_verified'] for case in report['cases']))
            self.assertTrue(report['changed_selection_detected'])
            self.assertEqual(report['scope'], 'owned_textpattern_ranges')
            self.assertTrue(report['clipboard_untouched'])
        finally:
            probe.close()

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
