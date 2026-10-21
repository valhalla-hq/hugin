"""Migration against temporary files, never the user's actual Startup folder."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import json
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
from desktop_setup import DesktopSetup


class DesktopSetupContracts(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)/'Hugin'
        self.startup = Path(self.folder.name)/'Startup'
        self.state = self.root/'.runtime/state'
        self.startup.mkdir(parents=True)
        (self.root/'tools').mkdir(parents=True)
        (self.root/'tools/launch.py').write_bytes(b'fixture launcher')
        python = self.root/'.runtime/controller/Scripts/pythonw.exe'
        python.parent.mkdir(parents=True)
        python.write_bytes(b'fixture interpreter')
        self.originals = {'PipPal.lnk':b'pippal fixture',
                          'Whispering Local STT.lnk':b'whispering fixture'}
        for name, data in self.originals.items():
            (self.startup/name).write_bytes(data)
        (self.startup/'Unrelated.lnk').write_bytes(b'leave alone')
        self.setup = DesktopSetup(self.root, self.state, self.startup,
                                  make_shortcut=lambda path, spec:path.write_bytes(repr(spec).encode()))

    def test_plan_apply_repeat_restore_and_repeat_preserve_exact_bytes(self):
        plan = self.setup.plan()
        self.assertFalse(self.setup.backup.exists())
        self.setup.apply(plan['plan_sha256'])
        self.assertTrue((self.startup/'Hugin.lnk').is_file())
        self.assertTrue((self.state/'activation.json').is_file())
        self.assertFalse((self.startup/'PipPal.lnk').exists())
        original_manifest = (self.setup.backup/'manifest.json').read_bytes()
        self.setup.apply(plan['plan_sha256'])
        self.assertEqual((self.setup.backup/'manifest.json').read_bytes(), original_manifest)
        self.setup.restore()
        self.setup.restore()
        for name, data in self.originals.items():
            self.assertEqual((self.startup/name).read_bytes(), data)
        self.assertEqual((self.startup/'Unrelated.lnk').read_bytes(), b'leave alone')
        self.assertFalse((self.startup/'Hugin.lnk').exists())
        self.assertFalse((self.state/'activation.json').exists())

    def test_plan_drift_refuses_before_any_change(self):
        plan = self.setup.plan()
        (self.startup/'PipPal.lnk').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'plan_changed'):
            self.setup.apply(plan['plan_sha256'])
        self.assertFalse(self.setup.backup.exists())
        self.assertFalse((self.state/'activation.json').exists())

    def test_restore_refuses_intervening_changes_before_any_write(self):
        self.setup.apply(self.setup.plan()['plan_sha256'])
        (self.startup/'Hugin.lnk').write_bytes(b'other owner')
        with self.assertRaisesRegex(RuntimeError, 'target_changed'):
            self.setup.restore()
        self.assertFalse((self.startup/'PipPal.lnk').exists())
        self.assertTrue((self.state/'activation.json').exists())

    def test_partial_apply_retains_recovery_and_can_resume(self):
        real = self.setup._set_entry
        calls = []
        def fail(entry, direction):
            calls.append(entry)
            if len(calls) == 2:raise OSError('synthetic write failure')
            return real(entry, direction)
        plan = self.setup.plan()
        with patch.object(self.setup, '_set_entry', side_effect=fail):
            with self.assertRaises(OSError):self.setup.apply(plan['plan_sha256'])
        self.assertTrue((self.setup.backup/'manifest.json').is_file())
        self.setup.apply(plan['plan_sha256'])
        self.setup.restore()
        self.assertEqual((self.startup/'PipPal.lnk').read_bytes(), self.originals['PipPal.lnk'])

    def test_preparation_failure_does_not_poison_retry_or_change_active_files(self):
        plan = self.setup.plan()
        with patch.object(self.setup, 'make_shortcut', side_effect=OSError('synthetic shell failure')):
            with self.assertRaises(OSError):self.setup.apply(plan['plan_sha256'])
        self.assertFalse(self.setup.backup.exists())
        self.assertEqual(self.setup.plan(), plan)
        self.setup.apply(plan['plan_sha256'])
        self.setup.restore()
        self.assertEqual((self.startup/'PipPal.lnk').read_bytes(), self.originals['PipPal.lnk'])

    def test_changed_backup_refuses(self):
        self.setup.apply(self.setup.plan()['plan_sha256'])
        (self.setup.backup/'before-1.bin').write_bytes(b'damaged backup')
        with self.assertRaisesRegex(RuntimeError, 'backup_changed'):
            self.setup.restore()
        self.assertFalse((self.startup/'PipPal.lnk').exists())

    def test_arbitrary_manifest_path_refuses_before_any_write(self):
        self.setup.apply(self.setup.plan()['plan_sha256'])
        path = self.setup.backup/'manifest.json'
        record = json.loads(path.read_text(encoding='utf-8'))
        record['entries'][0]['path'] = str(self.startup/'Unrelated.lnk')
        path.write_text(json.dumps(record), encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'invalid_manifest_path'):
            self.setup.restore()
        self.assertEqual((self.startup/'Unrelated.lnk').read_bytes(), b'leave alone')
