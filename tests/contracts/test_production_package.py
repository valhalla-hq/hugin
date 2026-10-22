"""Public packaging guards use synthetic trees, never installed runtime state."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import production_package as package


class ProductionPackage(unittest.TestCase):
    def test_runtime_search_path_is_relative_and_contains_own_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();scripts=root/'.runtime/controller/Scripts'
            scripts.mkdir(parents=True)
            package.write_search_path(scripts)
            lines=(scripts/'python312._pth').read_text().splitlines()
            self.assertEqual(lines,['.','Lib','../Lib/site-packages','DLLs','../../../src','import site'])
            self.assertEqual((scripts/lines[4]).resolve(),root/'src')

    def test_inventory_excludes_state_and_rejects_redirected_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();(root/'src').mkdir();(root/'src/main.py').write_text('synthetic')
            records=package.inventory(root)
            self.assertEqual([r['file'] for r in records],['src/main.py'])
            (root/'.runtime/state').mkdir(parents=True)
            (root/'.runtime/state/preferences.json').write_text('private synthetic sentinel')
            with self.assertRaisesRegex(ValueError,'state_in_payload'):package.inventory(root)

    def test_exact_payload_verification_detects_changed_missing_and_extra_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();file=root/'value';file.write_bytes(b'original')
            records=package.inventory(root);package.verify_inventory(root,records)
            file.write_bytes(b'modified')
            with self.assertRaises(ValueError):package.verify_inventory(root,records)
            file.unlink()
            with self.assertRaises(ValueError):package.verify_inventory(root,records)
            file.write_bytes(b'original');(root/'extra').write_bytes(b'extra')
            with self.assertRaises(ValueError):package.verify_inventory(root,records)

    def test_manifest_rejects_traversal_duplicate_and_boolean_size(self):
        for record in [dict(file='../foreign',size=1,sha256='a'*64),
                       dict(file='safe',size=True,sha256='a'*64)]:
            with self.subTest(record=record),self.assertRaises(ValueError):package.parse_records([record])
        valid=dict(file='safe',size=1,sha256='a'*64)
        with self.assertRaises(ValueError):package.parse_records([valid,valid])

    def test_installer_uses_manifest_records_instead_of_live_directory_wildcards(self):
        records=[dict(file='src/app.py',size=1,sha256='a'*64)]
        text=package.installer_file_list(records)
        self.assertIn('src\\app.py',text)
        self.assertIn('release-manifest.json',text)
        self.assertNotIn('*',text)
        self.assertNotIn('__pycache__',text)
        self.assertEqual(len(text.splitlines()),2)
