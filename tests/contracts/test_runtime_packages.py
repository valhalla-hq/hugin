"""Wheel identity and offline inputs, without installing real engine packages."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from runtime_packages import (assemble_manifest, load_wheel_lock, package_pins,
                              validate_wheelhouse, wheel_metadata, write_requirements)


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
