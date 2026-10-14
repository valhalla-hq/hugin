import json
from pathlib import Path
import tempfile
import unittest

from hugin.errors import HuginError
from hugin.targets import load_target_approvals

ROOT=Path(__file__).resolve().parents[2]


class TargetApprovalContracts(unittest.TestCase):
    def test_shipped_profile_approves_no_unverified_target(self):
        profile=load_target_approvals(ROOT)
        self.assertEqual(profile.delivery,())
        self.assertEqual(profile.capture_fallback,())

    def test_invalid_approval_is_not_silently_used_or_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic test evidence',encoding='utf-8')
            for entry in ({'control_class':'*','restore_delay_seconds':.1,'evidence':'proof.md'},
                          {'control_class':'Edit','restore_delay_seconds':True,'evidence':'proof.md'},
                          {'control_class':'Edit','restore_delay_seconds':.1,'evidence':'missing.md'}):
                (root/'config/targets.json').write_text(json.dumps({'schema_version':1,'delivery':[entry],'capture_fallback':[]}),encoding='utf-8')
                with self.assertRaises(HuginError): load_target_approvals(root)

    def test_explicit_class_and_evidence_bind_one_measured_delay(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic test evidence',encoding='utf-8')
            (root/'config/targets.json').write_text(json.dumps({'schema_version':1,'delivery':[
                {'control_class':'Edit','restore_delay_seconds':.1,'evidence':'proof.md'}],'capture_fallback':[]}),encoding='utf-8')
            self.assertEqual(load_target_approvals(root).delivery,(('Edit',.1),))

    def test_duplicate_configuration_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'config/targets.json').write_text('{"schema_version":0,"schema_version":1,"delivery":[],"capture_fallback":[]}',encoding='utf-8')
            with self.assertRaises(HuginError): load_target_approvals(root)


if __name__=='__main__': unittest.main()
