"""Wheel identity and offline inputs, without installing real engine packages."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_packages import (assemble_manifest, load_wheel_lock, package_pins,
                              validate_wheelhouse, wheel_metadata, write_requirements)
import prepare_engines


def fixture_wheel(folder, name='fixture_pkg', version='1.0', *, tag='py3-none-any', metadata_extra=''):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{name}-{version}-{tag}.whl'
    metadata = f'{name}-{version}.dist-info'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(metadata + '/METADATA', f'Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n'+metadata_extra)
        archive.writestr(metadata + '/WHEEL', 'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: ' + tag + '\n')
        archive.writestr(metadata + '/RECORD', '')
        archive.writestr(name + '.py', 'VALUE = 1\n')
    return path


class RuntimePackageContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'locks').mkdir()
        self.house = self.root / '.runtime/wheelhouse'
        for profile in ('controller', 'stt', 'tts'):
            (self.root / 'locks' / f'{profile}.txt').write_text('fixture-pkg==1.0\n', encoding='utf-8')
            fixture_wheel(self.house / profile)
        self.manifest = assemble_manifest(self.root, self.house)
        (self.root / 'locks/runtime-wheels.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_build_environment_junction_outside_runtime_fails_before_any_build_work(self):
        foreign=self.root/'other-installation';foreign.mkdir()
        runtime=self.root/'.runtime/wheel-build'
        owner={'schema_version':1,'python':prepare_engines.PYTHON,
            'build_tools':dict(prepare_engines.BUILD_TOOLS),'source_date_epoch':prepare_engines.SOURCE_DATE_EPOCH}
        (foreign/'hugin-build.json').write_text(json.dumps(owner),encoding='utf-8')
        try:runtime.symlink_to(foreign,target_is_directory=True)
        except OSError:
            if os.name!='nt':self.skipTest('directory links unavailable')
            # These absolute endpoints are both fresh children of this fixture.
            assert runtime.parent.resolve().is_relative_to(self.root) and foreign.resolve().is_relative_to(self.root)
            subprocess.run(['cmd','/c','mklink','/J',str(runtime),str(foreign)],check=True,capture_output=True)
        self.assertEqual(runtime.resolve(),foreign.resolve())
        spec={'kind':'pypi-sdist','version':'1.5.0',
            'archive_url':'https://files.pythonhosted.org/packages/sox-1.5.0.tar.gz'}
        with patch.object(prepare_engines,'_fetch_source',return_value='a'*64) as fetch,\
                patch.object(prepare_engines,'_download') as download,\
                patch.object(prepare_engines,'inspect_wheels',return_value=()),\
                patch.object(prepare_engines,'_python_facts'),\
                patch.object(prepare_engines,'_pip',side_effect=ValueError('stop_before_install')) as pip:
            with self.assertRaisesRegex(ValueError,'build_environment_outside_runtime'):
                prepare_engines._build_source_wheel(self.root,self.house,'sox',spec,'a'*64)
        fetch.assert_not_called();download.assert_not_called();pip.assert_not_called()
        self.assertFalse((foreign/'build-requirements.txt').exists())

    def test_build_environment_rejects_pathless_or_other_path_owner_before_download(self):
        runtime=self.root/'.runtime/wheel-build';runtime.mkdir()
        marker=runtime/'hugin-build.json'
        old={'schema_version':1,'python':prepare_engines.PYTHON,
            'build_tools':dict(prepare_engines.BUILD_TOOLS),'source_date_epoch':prepare_engines.SOURCE_DATE_EPOCH}
        moved=dict(old,schema_version=2,runtime=str(self.root/'other-installation'))
        spec={'kind':'pypi-sdist','version':'1.5.0',
            'archive_url':'https://files.pythonhosted.org/packages/sox-1.5.0.tar.gz'}
        for owner in (old,moved):
            with self.subTest(owner=owner):
                original=json.dumps(owner)
                marker.write_text(original,encoding='utf-8')
                with patch.object(prepare_engines,'_fetch_source') as fetch:
                    with self.assertRaisesRegex(ValueError,'build_environment_ownership_conflict'):
                        prepare_engines._build_source_wheel(self.root,self.house,'sox',spec,'a'*64)
                fetch.assert_not_called()
                self.assertEqual(marker.read_text(encoding='utf-8'),original)
                self.assertFalse((runtime/'build-requirements.txt').exists())

    def test_owned_build_marker_binds_final_path_and_matching_reuse_does_not_reinstall(self):
        runtime=self.root/'.runtime/wheel-build'
        executable=runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        def create(path):
            self.assertEqual(path,runtime.resolve())
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b'synthetic interpreter fixture')
        def pip(_executable,*arguments,**kwargs):
            self.assertEqual(_executable,executable)
            if arguments[0]=='wheel':fixture_wheel(self.house/'tts',name='sox',version='1.5.0')
        spec={'kind':'pypi-sdist','version':'1.5.0',
            'archive_url':'https://files.pythonhosted.org/packages/sox-1.5.0.tar.gz'}
        with patch.object(prepare_engines,'_fetch_source',return_value='a'*64),\
                patch.object(prepare_engines,'_download'),\
                patch.object(prepare_engines,'inspect_wheels',return_value=()),\
                patch.object(prepare_engines,'_python_facts'),\
                patch.object(prepare_engines.venv,'EnvBuilder') as builder,\
                patch.object(prepare_engines,'_installed_versions',return_value=dict(prepare_engines.BUILD_TOOLS)),\
                patch.object(prepare_engines,'_pip',side_effect=pip) as installed:
            builder.return_value.create.side_effect=create
            first=prepare_engines._build_source_wheel(self.root,self.house,'sox',spec,'a'*64)
            again=prepare_engines._build_source_wheel(self.root,self.house,'sox',spec,'a'*64)
        owner=json.loads((runtime/'hugin-build.json').read_text(encoding='utf-8'))
        self.assertEqual(owner['schema_version'],2)
        self.assertEqual(owner['runtime'],str(runtime.resolve()))
        self.assertEqual(first,again)
        self.assertEqual(builder.return_value.create.call_count,1)
        self.assertEqual([call.args[1] for call in installed.call_args_list],['install','wheel'])

    def test_lock_covers_exact_profile_pins_and_keeps_wheel_identity(self):
        lock = load_wheel_lock(self.root)
        records = validate_wheelhouse(self.house, lock, ('controller', 'stt', 'tts'))
        self.assertEqual(len(records), 3)
        for item in records:
            self.assertEqual(item.name, 'fixture-pkg')
            self.assertEqual(item.version, '1.0')
            self.assertEqual(item.sha256, hashlib.sha256((self.house/item.file).read_bytes()).hexdigest())

    def test_wheel_hash_failure_prevents_requirements_creation(self):
        lock = load_wheel_lock(self.root)
        path = self.house / lock.profiles['controller'][0].file
        path.write_bytes(b'tampered wheel')
        target = self.root / 'requirements.txt'
        with self.assertRaises(ValueError):
            write_requirements(self.house, lock, 'controller', target)
        self.assertFalse(target.exists())

    def test_offline_requirements_contain_only_local_uri_and_sha256(self):
        target = self.root / 'requirements.txt'
        lock = load_wheel_lock(self.root)
        write_requirements(self.house, lock, 'controller', target)
        content = target.read_text(encoding='utf-8')
        self.assertIn('file:///', content)
        self.assertIn('--hash=sha256:', content)
        self.assertNotIn('https:', content)

    def test_changed_package_pin_rejects_previously_valid_wheel_lock(self):
        (self.root/'locks/stt.txt').write_text('fixture-pkg==2.0\n',encoding='utf-8')
        with self.assertRaises(ValueError):
            load_wheel_lock(self.root)

    def test_unknown_extra_wheel_and_path_escape_fail_closed(self):
        fixture_wheel(self.house/'controller','extra')
        with self.assertRaises(ValueError):
            assemble_manifest(self.root,self.house)
        self.manifest['profiles']['controller'][0]['file'] = '../foreign.whl'
        (self.root/'locks/runtime-wheels.json').write_text(json.dumps(self.manifest),encoding='utf-8')
        with self.assertRaises(ValueError):
            load_wheel_lock(self.root)

    def test_metadata_and_filename_must_agree(self):
        path = fixture_wheel(self.root/'bad')
        renamed = path.with_name('different-1.0-py3-none-any.whl')
        path.rename(renamed)
        with self.assertRaises(ValueError):
            wheel_metadata(renamed)

    def test_vendored_distribution_metadata_does_not_replace_wheel_owner(self):
        path=fixture_wheel(self.root/'vendored')
        with zipfile.ZipFile(path,'a') as archive:
            archive.writestr('fixture_pkg/_vendor/other-2.dist-info/METADATA','Name: other\nVersion: 2\n')
        self.assertEqual(wheel_metadata(path),('fixture-pkg','1.0'))

    def test_foreign_platform_and_oversized_metadata_are_rejected(self):
        foreign = fixture_wheel(self.root/'foreign',tag='cp312-cp312-manylinux_x86_64')
        with self.assertRaises(ValueError):
            wheel_metadata(foreign)
        path = fixture_wheel(self.root/'oversized',metadata_extra='X-Extra: '+'X'*(1024*1024))
        with self.assertRaises(ValueError):
            wheel_metadata(path)

    def test_direct_git_source_is_not_a_runtime_requirement(self):
        (self.root/'locks/faster-qwen.txt').write_text('faster-qwen3-tts @ https://github.com/example/repo/archive/'+'a'*40+'.zip\n')
        (self.root/'locks/engines-provenance.json').write_text(json.dumps({'tts':{
            'faster_qwen_repository':'https://github.com/example/repo',
            'faster_qwen_revision':'a'*40,'faster_qwen_version':'0.3.2'}}))
        (self.root/'locks/tts.txt').write_text((self.root/'locks/faster-qwen.txt').read_text())
        self.assertEqual(package_pins(self.root,'tts'),{'faster-qwen3-tts':'0.3.2'})


if __name__ == '__main__':
    unittest.main()
