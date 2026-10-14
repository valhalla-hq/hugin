"""Restore applies only to a named Hugin checkout and its owned runtime."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from hugin.errors import HuginError

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import prepare_engines
from runtime_packages import assemble_manifest,load_wheel_lock
sys.path.insert(0,str(ROOT/'tests/contracts'))
from test_runtime_packages import fixture_wheel
spec=importlib.util.spec_from_file_location('hugin_restore',ROOT/'tools/restore.py')
restore=importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class RuntimeRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.source=Path(self.temp.name)/'source'
        self.target=Path(self.temp.name)/'target'
        for root in (self.source,self.target):
            shutil.copytree(ROOT/'config',root/'config')
            shutil.copytree(ROOT/'assets',root/'assets')
            shutil.copytree(ROOT/'locks',root/'locks')
            (root/'src/hugin').mkdir(parents=True)
        for kind in ('stt','tts','cuda'):
            path=self.source/('.runtime/cuda' if kind=='cuda' else '.runtime/models/'+kind)
            path.mkdir(parents=True)
            (path/'payload.bin').write_bytes(b'synthetic runtime fixture')
            lock={'files':[{'file':'payload.bin','size':25,
                'sha256':hashlib.sha256(b'synthetic runtime fixture').hexdigest()}]}
            filename='cuda.json' if kind=='cuda' else kind+'-model.json'
            for root in (self.source,self.target):
                (root/'locks'/filename).write_text(json.dumps(lock),encoding='utf-8')
        house=self.source/'.runtime/wheelhouse'
        for profile in ('controller','stt','tts'):
            for root in (self.source,self.target):
                (root/'locks'/f'{profile}.txt').write_text('fixture-pkg==1.0\n',encoding='utf-8')
            fixture_wheel(house/profile)
        manifest=assemble_manifest(self.source,house)
        for path in (house/'manifest.json',self.source/'locks/runtime-wheels.json',self.target/'locks/runtime-wheels.json'):
            path.write_text(json.dumps(manifest),encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_plan_without_package_install_has_no_writes(self):
        before={p.relative_to(self.target):p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        plan=restore.plan_restore(self.source,self.target,install=())
        self.assertFalse(plan['writes'])
        self.assertFalse(plan['offline_package_restore_verified'])
        self.assertFalse((self.target/'.runtime').exists())
        after={p.relative_to(self.target):p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_apply_is_additive_idempotent_and_preserves_tracked_files(self):
        before={p.relative_to(self.target):p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        restore.apply_restore(self.source,self.target,install=())
        restore.apply_restore(self.source,self.target,install=())
        for path,raw in before.items():
            self.assertEqual((self.target/path).read_bytes(),raw)
        self.assertEqual((self.target/'.runtime/models/stt/payload.bin').read_bytes(),b'synthetic runtime fixture')

    def test_divergent_destination_fails_before_any_other_copy(self):
        existing=self.target/'.runtime/models/tts/payload.bin'
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b'preserve owned divergent bytes')
        with self.assertRaises((HuginError,ValueError)):
            restore.apply_restore(self.source,self.target,install=())
        self.assertEqual(existing.read_bytes(),b'preserve owned divergent bytes')
        self.assertFalse((self.target/'.runtime/models/stt').exists())

    def test_uninitialized_target_and_mismatched_locks_fail_without_writes(self):
        empty=Path(self.temp.name)/'empty'
        with self.assertRaises((HuginError,ValueError)):
            restore.apply_restore(self.source,empty,install=())
        self.assertFalse(empty.exists())
        (self.target/'locks/stt-model.json').write_text('{"files":[]}',encoding='utf-8')
        with self.assertRaises((HuginError,ValueError)):
            restore.apply_restore(self.source,self.target,install=())
        self.assertFalse((self.target/'.runtime').exists())

    def test_environment_is_created_in_place_and_repeat_does_not_reinstall(self):
        pins=prepare_engines.package_pins(self.target,'stt')
        def create(directory):
            executable=directory/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b'simulated interpreter')
        with mock.patch.object(prepare_engines.venv.EnvBuilder,'create',side_effect=create), \
                mock.patch.object(prepare_engines,'_installed_versions',side_effect=[dict.fromkeys(pins),pins,pins]), \
                mock.patch.object(prepare_engines,'_python_facts',return_value={'python':'3.12.10','bits':64,'tk':'8.6'}), \
                mock.patch.dict(os.environ,{'PIP_TARGET':'foreign-installation','PIP_CONFIG_FILE':'foreign-config'}), \
                mock.patch.object(prepare_engines.subprocess,'run') as run:
            prepare_engines.prepare_environment('stt',root=self.target,wheelhouse=self.source/'.runtime/wheelhouse')
            prepare_engines.prepare_environment('stt',root=self.target,wheelhouse=self.source/'.runtime/wheelhouse')
        installs=[call for call in run.call_args_list if 'install' in call.args[0]]
        self.assertEqual(len(installs),1)
        self.assertIn('--no-index',installs[0].args[0])
        self.assertIn('--require-hashes',installs[0].args[0])
        self.assertIn('--isolated',installs[0].args[0])
        self.assertNotIn('PIP_TARGET',installs[0].kwargs['env'])
        self.assertEqual(installs[0].kwargs['env']['PIP_CONFIG_FILE'],os.devnull)
        marker=self.target/'.runtime/stt/hugin-environment.json'
        self.assertEqual(json.loads(marker.read_text())['runtime'],str((self.target/'.runtime/stt').resolve()))

    def test_same_files_with_different_model_identity_are_rejected(self):
        path=self.target/'locks/stt-model.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        data['revision']='different locked model identity'
        path.write_text(json.dumps(data),encoding='utf-8')
        with self.assertRaises(ValueError):
            restore.apply_restore(self.source,self.target,install=())
        self.assertFalse((self.target/'.runtime').exists())

    def test_unowned_existing_environment_is_preserved(self):
        runtime=self.target/'.runtime/stt'
        runtime.mkdir(parents=True)
        sentinel=runtime/'foreign.txt'
        sentinel.write_text('preserve',encoding='utf-8')
        with self.assertRaises(ValueError):
            prepare_engines.prepare_environment('stt',root=self.target)
        self.assertEqual(sentinel.read_text(),'preserve')
        self.assertFalse((runtime/'hugin-environment.json').exists())
        with self.assertRaises(ValueError):
            restore.apply_restore(self.source,self.target,install=('stt',))
        self.assertFalse((self.target/'.runtime/models').exists())

    def test_offline_plan_validates_all_selected_wheels_without_writes(self):
        plan=restore.plan_restore(self.source,self.target,install=('controller','stt','tts'))
        self.assertFalse(plan['downloads'])
        self.assertTrue(plan['offline_package_inputs_verified'])
        self.assertFalse(plan['offline_package_restore_verified'])
        self.assertFalse((self.target/'.runtime').exists())

    def test_tampered_wheel_fails_before_model_or_environment_copy(self):
        lock=load_wheel_lock(self.source)
        (self.source/'.runtime/wheelhouse'/lock.profiles['tts'][0].file).write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            restore.apply_restore(self.source,self.target)
        self.assertFalse((self.target/'.runtime').exists())

    def test_wheelhouse_destination_outside_owned_runtime_is_rejected(self):
        foreign=Path(self.temp.name)/'foreign-wheelhouse'
        foreign.mkdir()
        (self.target/'.runtime').mkdir()
        try:
            (self.target/'.runtime/wheelhouse').symlink_to(foreign,target_is_directory=True)
        except OSError:
            if os.name!='nt':
                self.skipTest('directory symlinks require OS permission')
            # Windows junctions need no symlink privilege. Both endpoints are
            # fresh fixture directories inside this test's temporary root.
            subprocess.run(['cmd','/c','mklink','/J',str(self.target/'.runtime/wheelhouse'),str(foreign)],
                check=True,capture_output=True)
        self.assertEqual((self.target/'.runtime/wheelhouse').resolve(),foreign.resolve())
        with self.assertRaises(ValueError):
            restore.plan_restore(self.source,self.target)
        self.assertEqual(list(foreign.iterdir()),[])
        self.assertFalse((self.target/'.runtime/models').exists())

    def test_mismatched_python_tk_fails_before_model_or_environment_copy(self):
        with mock.patch.object(restore,'_python_facts',side_effect=ValueError('python_version_or_tk_mismatch')):
            with self.assertRaises(ValueError):
                restore.apply_restore(self.source,self.target)
        self.assertFalse((self.target/'.runtime').exists())

    def test_preparation_rejects_changed_manifest_before_network_or_writes(self):
        house=self.source/'.runtime/wheelhouse'
        (house/'manifest.json').write_text('{}',encoding='utf-8')
        with mock.patch.object(prepare_engines,'_download') as download:
            with self.assertRaises(ValueError):
                prepare_engines.prepare_wheelhouse(root=self.source,apply=True)
        download.assert_not_called()
        self.assertFalse((house/'preparation.json').exists())

    def test_complete_preparation_is_noop_without_download_or_build(self):
        with mock.patch.object(prepare_engines,'_download') as download, \
                mock.patch.object(prepare_engines,'_build_source_wheel') as build:
            result=prepare_engines.prepare_wheelhouse(root=self.source,apply=True)
        self.assertTrue(result['already_complete'])
        self.assertFalse(result['writes'])
        self.assertFalse(result['downloads'])
        download.assert_not_called()
        build.assert_not_called()

    def test_existing_source_wheel_requires_its_own_build_receipt(self):
        house=self.source/'.runtime/wheelhouse'
        archive=house/'fixture-pkg.tar.gz'
        archive.write_bytes(b'locked source fixture')
        source=dict(kind='pypi-sdist',version='1.0',archive_url='https://files.pythonhosted.org/packages/fixture-pkg-1.0.tar.gz')
        with self.assertRaises(ValueError):
            prepare_engines._build_source_wheel(self.source,house,'fixture-pkg',source,hashlib.sha256(archive.read_bytes()).hexdigest())

    def test_real_fixture_wheels_install_offline_in_fresh_env_without_model_imports(self):
        # Tiny synthetic wheel, actual pip/venv. No controller/native/model import.
        result=restore.apply_restore(self.source,self.target,install=('controller',))
        self.assertTrue(result['offline_package_restore_verified'])
        proof=self.target/'.runtime/controller/hugin-wheel-installation.json'
        before=proof.read_bytes(),proof.stat().st_mtime_ns
        again=restore.apply_restore(self.source,self.target,install=('controller',))
        self.assertTrue(again['offline_package_restore_verified'])
        self.assertEqual(before,(proof.read_bytes(),proof.stat().st_mtime_ns))
        self.assertEqual((self.target/'.runtime/models/stt/payload.bin').read_bytes(),b'synthetic runtime fixture')


if __name__=='__main__':
    unittest.main()
