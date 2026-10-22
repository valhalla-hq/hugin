"""Installation migration and repeat/uninstall guards use disposable Startup."""
import ast
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from desktop_setup import DesktopSetup
from install_setup import ProductionSetup


def shortcut(path,spec):path.write_bytes(repr(spec).encode())
def read_shortcut(path):return ast.literal_eval(path.read_text())


class ProductionSetupContracts(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.folder=Path(temporary.name);self.startup=self.folder/'Startup';self.startup.mkdir()
        self.old=self.fixture('Source');self.new=self.fixture('Installed')
        (self.startup/'Unrelated.lnk').write_bytes(b'untouched')
        self.previous=DesktopSetup(self.old,self.old/'.runtime/state',self.startup,make_shortcut=shortcut)
        self.previous.apply(self.previous.plan()['plan_sha256'])
        self.original_link=(self.startup/'Hugin.lnk').read_bytes()
        self.voice=b'{"schema_version":1,"voice":"tyr"}\n'
        (self.old/'.runtime/state/preferences.json').write_bytes(self.voice)
        self.setup=ProductionSetup(self.new,self.startup,make_shortcut=shortcut,read_shortcut=read_shortcut)

    def fixture(self,name):
        root=self.folder/name;(root/'tools').mkdir(parents=True)
        (root/'tools/launch.py').write_bytes(b'synthetic launcher')
        python=root/'.runtime/controller/Scripts/pythonw.exe';python.parent.mkdir(parents=True)
        python.write_bytes(b'synthetic private interpreter');(root/'Hugin.exe').write_bytes(b'synthetic exe')
        shutil.copytree(ROOT/'config',root/'config')
        return root

    def test_owned_migration_and_repeat_preserve_both_preferences_and_backups(self):
        self.setup.apply()
        self.assertEqual((self.new/'.runtime/state/preferences.json').read_bytes(),self.voice)
        self.assertEqual((self.old/'.runtime/state/preferences.json').read_bytes(),self.voice)
        backup=self.new/'.runtime/desktop-setup-v1/before-3.bin'
        self.assertEqual(backup.read_bytes(),self.original_link)
        spec=read_shortcut(self.startup/'Hugin.lnk')
        self.assertEqual(spec['target'],str(self.new/'Hugin.exe'))
        self.assertEqual(spec['arguments'],'--background')
        changed=b'{"schema_version":1,"voice":"freya"}\n'
        (self.new/'.runtime/state/preferences.json').write_bytes(changed)
        activation=(self.new/'.runtime/state/activation.json').read_bytes()
        self.setup.apply()
        self.assertEqual((self.new/'.runtime/state/preferences.json').read_bytes(),changed)
        self.assertEqual((self.new/'.runtime/state/activation.json').read_bytes(),activation)
        self.assertEqual(backup.read_bytes(),self.original_link)
        self.assertEqual((self.startup/'Unrelated.lnk').read_bytes(),b'untouched')

    def test_unknown_startup_refuses_before_activation_or_preference_writes(self):
        (self.startup/'Hugin.lnk').write_bytes(b'unknown owner')
        with self.assertRaises(RuntimeError):self.setup.apply()
        self.assertFalse((self.new/'.runtime/state').exists())
        self.assertEqual((self.startup/'Hugin.lnk').read_bytes(),b'unknown owner')

    def test_changed_source_ownership_backup_refuses(self):
        (self.old/'.runtime/desktop-setup-v1/after-3.bin').write_bytes(b'damaged')
        with self.assertRaises(RuntimeError):self.setup.apply()
        self.assertEqual((self.startup/'Hugin.lnk').read_bytes(),self.original_link)
        self.assertFalse((self.new/'.runtime/state').exists())

    def test_uninstall_repeat_and_reinstall_preserve_user_state_without_old_app_return(self):
        self.setup.apply();self.setup.uninstall();self.setup.uninstall()
        self.assertFalse((self.startup/'Hugin.lnk').exists())
        self.assertFalse((self.startup/'PipPal.lnk').exists())
        self.assertFalse((self.startup/'Whispering Local STT.lnk').exists())
        self.assertEqual((self.new/'.runtime/state/preferences.json').read_bytes(),self.voice)
        self.setup.apply()
        self.assertEqual(read_shortcut(self.startup/'Hugin.lnk')['target'],str(self.new/'Hugin.exe'))
        self.assertEqual((self.new/'.runtime/state/preferences.json').read_bytes(),self.voice)

    def test_changed_installed_shortcut_is_never_removed(self):
        self.setup.apply();(self.startup/'Hugin.lnk').write_bytes(b'foreign replacement')
        with self.assertRaises(RuntimeError):self.setup.uninstall()
        self.assertEqual((self.startup/'Hugin.lnk').read_bytes(),b'foreign replacement')

    def test_interrupted_preference_copy_resumes_original_migration(self):
        import install_setup
        real=install_setup.create_atomic
        def fail_preference(path,content):
            if path==self.new/'.runtime/state/preferences.json':raise OSError('synthetic interruption')
            return real(path,content)
        with patch.object(install_setup,'create_atomic',side_effect=fail_preference):
            with self.assertRaises(OSError):self.setup.apply()
        self.setup.apply()
        self.assertEqual((self.new/'.runtime/state/preferences.json').read_bytes(),self.voice)

    def test_reinstall_validates_all_backup_before_recreating_owned_link(self):
        self.setup.apply();self.setup.uninstall()
        (self.new/'.runtime/desktop-setup-v1/after-0.bin').write_bytes(b'damaged')
        with self.assertRaises(RuntimeError):self.setup.apply()
        self.assertFalse((self.startup/'Hugin.lnk').exists())

    def test_fresh_install_refuses_unproven_legacy_links_without_mutation(self):
        (self.startup/'Hugin.lnk').unlink()
        (self.startup/'PipPal.lnk').write_bytes(b'foreign startup owner')
        with self.assertRaises(RuntimeError):self.setup.apply()
        self.assertEqual((self.startup/'PipPal.lnk').read_bytes(),b'foreign startup owner')
        self.assertFalse((self.new/'.runtime/state').exists())

    def test_replacement_authority_is_not_refreshed_from_a_foreign_link(self):
        import install_setup
        real=install_setup.file_hash;changed=[]
        def replace_after_observation(path):
            value=real(path)
            if path==self.startup/'Hugin.lnk' and not changed:
                changed.append(True);path.write_bytes(b'foreign intervening owner')
            return value
        with patch.object(install_setup,'file_hash',side_effect=replace_after_observation):
            with self.assertRaises(RuntimeError):self.setup.apply()
        self.assertEqual((self.startup/'Hugin.lnk').read_bytes(),b'foreign intervening owner')
        self.assertFalse((self.new/'.runtime/state').exists())

    def test_completed_migration_preserves_intentional_preference_absence(self):
        self.setup.apply();(self.new/'.runtime/state/preferences.json').unlink()
        self.setup.apply()
        self.assertFalse((self.new/'.runtime/state/preferences.json').exists())
        self.setup.uninstall();self.setup.apply()
        self.assertFalse((self.new/'.runtime/state/preferences.json').exists())

    def test_reinstall_validates_completion_owner_before_any_link_write(self):
        self.setup.apply();self.setup.uninstall()
        (self.new/'.runtime/production-migration-v1/completed.json').write_bytes(b'damaged owner')
        with self.assertRaises((RuntimeError,ValueError)):self.setup.apply()
        self.assertFalse((self.startup/'Hugin.lnk').exists())

    def test_explicit_rollback_then_uninstall_keeps_exact_prior_owner(self):
        self.setup.apply();self.setup.restore_previous()
        self.assertEqual((self.startup/'Hugin.lnk').read_bytes(),self.original_link)
        self.setup.uninstall()
        self.assertEqual((self.startup/'Hugin.lnk').read_bytes(),self.original_link)
        self.assertFalse((self.startup/'PipPal.lnk').exists())
