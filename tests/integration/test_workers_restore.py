"""Restore applies only to a named Hugin checkout and its owned runtime."""
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from hugin.errors import HuginError

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import prepare_engines
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

    def tearDown(self):
        self.temp.cleanup()

    def test_plan_has_no_writes_and_marks_network_restore_limit(self):
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
                mock.patch.object(prepare_engines.subprocess,'run') as run:
            prepare_engines.prepare_environment('stt',root=self.target)
            prepare_engines.prepare_environment('stt',root=self.target)
        installs=[call for call in run.call_args_list if 'install' in call.args[0]]
        self.assertEqual(len(installs),1)
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


if __name__=='__main__':
    unittest.main()
