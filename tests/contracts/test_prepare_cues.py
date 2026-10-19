"""Setup uses synthetic PCM and the existing atomic runtime copy boundary."""
from pathlib import Path
import hashlib
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import prepare_cues
from hugin.cues import ASSET_DIRECTORY


class PrepareCueContracts(unittest.TestCase):
    def test_isolated_cli_can_show_plan_options_without_optional_decoder(self):
        result=subprocess.run([sys.executable,'-I',str(ROOT/'tools/prepare_cues.py'),'--help'],
            capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('--source',result.stdout)

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/'runtime';self.source=Path(self.temporary.name)/'originals'
        self.signals={kind:bytes((index,0))*100 for index,kind in enumerate(('start','end','complete'),1)}
        identities={kind:(len(pcm),hashlib.sha256(pcm).hexdigest()) for kind,pcm in self.signals.items()}
        patcher=patch('hugin.cues.CUE_FILES',identities);patcher.start();self.addCleanup(patcher.stop)
        patcher=patch.object(prepare_cues,'CUE_FILES',identities);patcher.start();self.addCleanup(patcher.stop)
        patcher=patch.object(prepare_cues,'decode',side_effect=lambda path,kind:self.signals[kind])
        patcher.start();self.addCleanup(patcher.stop)

    def test_plan_has_no_writes_then_apply_is_idempotent(self):
        result=prepare_cues.prepare(self.root,self.source)
        self.assertEqual(result['status'],'planned');self.assertFalse(self.root.exists())
        prepare_cues.prepare(self.root,self.source,True)
        result=prepare_cues.prepare(self.root,self.source,True)
        self.assertTrue(all(item['action']=='present' for item in result['files']))

    def test_foreign_destination_is_preserved(self):
        folder=self.root/ASSET_DIRECTORY;folder.mkdir(parents=True)
        path=folder/'start.pcm';path.write_bytes(b'foreign')
        with self.assertRaisesRegex(ValueError,'cue_existing_mismatch'):
            prepare_cues.prepare(self.root,self.source,True)
        self.assertEqual(path.read_bytes(),b'foreign')
        self.assertFalse((folder/'end.pcm').exists())

    def test_failed_copy_never_publishes_partial_final_and_retry_succeeds(self):
        def fail(origin,destination):
            Path(destination).write_bytes(b'xx');raise OSError('synthetic disk failure')
        with patch('prepare_engines.shutil.copyfile',side_effect=fail):
            with self.assertRaises(OSError):prepare_cues.prepare(self.root,self.source,True)
        folder=self.root/ASSET_DIRECTORY
        self.assertFalse((folder/'start.pcm').exists())
        self.assertEqual(list(folder.iterdir()),[])
        prepare_cues.prepare(self.root,self.source,True)
        self.assertEqual((folder/'start.pcm').read_bytes(),self.signals['start'])
