"""Native Shell Link roundtrip in a temporary folder; no actual login changes."""
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
from desktop_setup import DesktopSetup, native_shortcut


@unittest.skipUnless(sys.platform == 'win32', 'Windows Shell required')
class NativeDesktopSetup(unittest.TestCase):
    def test_native_link_creation_migration_and_restore_in_private_fixture(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)/'Installation with spaces'
            startup = Path(folder)/'Synthetic Startup'
            startup.mkdir()
            python = root/'.runtime/controller/Scripts/pythonw.exe'
            python.parent.mkdir(parents=True)
            python.write_bytes(b'not executed')
            (root/'tools').mkdir()
            (root/'tools/launch.py').write_bytes(b'not executed')
            old = startup/'PipPal.lnk'
            native_shortcut(old, {'target':str(python), 'arguments':'--synthetic',
                                  'working_directory':str(root)})
            original = old.read_bytes()
            setup = DesktopSetup(root, root/'.runtime/state', startup)
            plan = setup.plan()
            setup.apply(plan['plan_sha256'])
            self.assertNotIn('--pilot', setup.shortcut['arguments'])
            self.assertNotIn('--show', setup.shortcut['arguments'])
            self.assertTrue((startup/'Hugin.lnk').is_file())
            setup.apply(plan['plan_sha256'])
            setup.restore()
            self.assertEqual(old.read_bytes(), original)
            self.assertFalse((startup/'Hugin.lnk').exists())
