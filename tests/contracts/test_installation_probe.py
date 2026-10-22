"""Probe framing and failed native-owner guards; no real processes or inputs."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import installation_probe as probe
from hugin.errors import HuginError


class ProbeContracts(unittest.TestCase):
    def setUp(self):
        self.assertFalse(probe._HELD);self.addCleanup(probe._HELD.clear)

    def test_fragmented_pipe_report_is_collected_to_eof_and_closed(self):
        chunks=[b'{"isolated":true,',b'"versions":{"fixture":"1"}}',b'']
        owner=NS(stdout=NS(read=lambda limit:chunks.pop(0)),closed=False,
            wait=lambda timeout:0,poll=lambda:0,metrics=lambda:{})
        owner.close=lambda:setattr(owner,'closed',True)
        with patch('hugin.windows.process.OwnedProcess',return_value=owner):
            result=probe.private_profile(Path('C:/synthetic'),'controller',{'fixture':'1'})
        self.assertTrue(result['isolated'] and owner.closed)
        self.assertFalse(probe._HELD)

    def test_partial_constructor_cleanup_failure_retains_exact_owner(self):
        error=HuginError('worker_failed','synthetic_create')
        def fail_close():raise HuginError('worker_failed','synthetic_close')
        owner=NS(process_created=False,close=fail_close,poll=lambda:None)
        error.owner=owner
        with patch('hugin.windows.process.OwnedProcess',side_effect=error):
            with self.assertRaises(HuginError):probe.private_profile(Path('C:/synthetic'),'stt',{})
        self.assertEqual(probe._HELD,[owner])
