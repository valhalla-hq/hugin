"""Runtime cue boundary uses synthetic local bytes, no third-party audio."""
from pathlib import Path
import hashlib
import tempfile
import unittest
from unittest.mock import patch

from hugin.cues import ASSET_DIRECTORY,DictationCues,load_cue_signals
from hugin.errors import HuginError


class CueAssetContracts(unittest.TestCase):
    def test_loader_retains_exact_bytes_and_rejects_missing_changed_or_oversized_assets(self):
        signals={kind:bytes((index,0))*100 for index,kind in enumerate(('start','end','complete'),1)}
        identities={kind:(len(pcm),hashlib.sha256(pcm).hexdigest()) for kind,pcm in signals.items()}
        with tempfile.TemporaryDirectory() as temporary,patch('hugin.cues.CUE_FILES',identities):
            root=Path(temporary);folder=root/ASSET_DIRECTORY;folder.mkdir(parents=True)
            def reset():
                for kind,pcm in signals.items():(folder/(kind+'.pcm')).write_bytes(pcm)
            reset();self.assertEqual(load_cue_signals(root),signals)
            for failure in ('missing','changed','oversized'):
                with self.subTest(failure=failure):
                    reset();path=folder/'complete.pcm'
                    if failure=='missing':path.unlink()
                    else:path.write_bytes(b'\0'*(len(signals['complete'])+(1 if failure=='oversized' else 0)))
                    with self.assertRaises(HuginError) as caught:load_cue_signals(root)
                    self.assertEqual(caught.exception.code,'audio_failed')

    def test_owner_rejects_incomplete_odd_empty_and_unbounded_pcm_before_output_creation(self):
        for invalid in ({},{'start':b'\0\0','end':b'\0\0','complete':b'x'},
                {'start':b'','end':b'\0\0','complete':b'\0\0'},
                {'start':b'\0\0','end':b'\0\0','complete':b'\0'*(65536+2)}):
            with self.subTest(invalid_keys=list(invalid)):
                with patch('hugin.cues.PCMOutput') as output:
                    with self.assertRaises(HuginError):DictationCues(invalid)
                    output.assert_not_called()

    def test_largest_advertised_cue_passes_real_output_boundary_without_truncation(self):
        from hugin.audio import PCMOutput,MAX_PCM_WRITE_BYTES
        from test_audio import Device
        class Collected(Device):
            def collect(self):self.queued_bytes=0
        device=Collected(24000);output=PCMOutput(factory=lambda rate:device)
        signals={kind:b'\0\0' for kind in ('start','end','complete')}
        signals['complete']=b'\x01\0'*(MAX_PCM_WRITE_BYTES//2)
        owner=DictationCues(signals,output=output)
        try:
            self.assertTrue(owner.play('complete','fixture',lambda:False))
            self.assertEqual(b''.join(device.writes),signals['complete'])
        finally:owner.close()
