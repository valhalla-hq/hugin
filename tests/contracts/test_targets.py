import json
from pathlib import Path
import tempfile
import unittest

from hugin.errors import HuginError
from hugin.targets import load_target_approvals, DeliveryApproval

ROOT=Path(__file__).resolve().parents[2]


class TargetApprovalContracts(unittest.TestCase):
    def test_shipped_profile_retains_measured_codex_overrides_and_no_capture_fallback(self):
        profile=load_target_approvals(ROOT)
        self.assertEqual(profile.delivery,(
            DeliveryApproval('Chrome_RenderWidgetHostHWND',.15,'OpenAI.Codex_2p2nqsd0c76g0'),
            DeliveryApproval('Chrome_WidgetWin_1',.15,'OpenAI.Codex_2p2nqsd0c76g0')))
        self.assertEqual(profile.capture_fallback,())

    def test_invalid_approval_is_not_silently_used_or_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic test evidence',encoding='utf-8')
            for entry in ({'control_class':'*','restore_delay_seconds':.1,'evidence':'proof.md'},
                          {'control_class':'Edit','restore_delay_seconds':True,'evidence':'proof.md'},
                          {'control_class':'Edit','restore_delay_seconds':.1,'evidence':'missing.md'}):
                (root/'config/targets.json').write_text(json.dumps({'schema_version':2,'verified_edit':None,'delivery':[entry],'capture_fallback':[]}),encoding='utf-8')
                with self.assertRaises(HuginError): load_target_approvals(root)

    def test_explicit_class_and_evidence_bind_one_measured_delay(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic test evidence',encoding='utf-8')
            (root/'config/targets.json').write_text(json.dumps({'schema_version':2,'verified_edit':None,'delivery':[
                {'control_class':'Edit','restore_delay_seconds':.1,'evidence':'proof.md'}],'capture_fallback':[]}),encoding='utf-8')
            self.assertEqual(load_target_approvals(root).delivery,(DeliveryApproval('Edit',.1),))

    def test_package_scoped_delivery_is_preserved_and_invalid_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic test evidence',encoding='utf-8')
            entry={'control_class':'Chrome_WidgetWin_1','restore_delay_seconds':.15,
                'package_family':'OpenAI.Codex_2p2nqsd0c76g0','evidence':'proof.md'}
            def write():
                (root/'config/targets.json').write_text(json.dumps(
                    {'schema_version':2,'verified_edit':None,'delivery':[entry],'capture_fallback':[]}),encoding='utf-8')
            write()
            self.assertEqual(load_target_approvals(root).delivery,(
                DeliveryApproval('Chrome_WidgetWin_1',.15,'OpenAI.Codex_2p2nqsd0c76g0'),))
            for invalid in (None,True,'','*','bad\0scope','short','x'*65):
                entry['package_family']=invalid;write()
                with self.assertRaises(HuginError):load_target_approvals(root)

    def test_duplicate_configuration_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'config/targets.json').write_text('{"schema_version":0,"schema_version":2,"verified_edit":null,"delivery":[],"capture_fallback":[]}',encoding='utf-8')
            with self.assertRaises(HuginError): load_target_approvals(root)

    def test_null_generic_policy_is_explicitly_disabled_and_old_shape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            profile={'schema_version':2,'verified_edit':None,'delivery':[],'capture_fallback':[]}
            path=root/'config/targets.json'
            path.write_text(json.dumps(profile),encoding='utf-8')
            self.assertIsNone(load_target_approvals(root).verified_edit)
            for old in ({'schema_version':1,'delivery':[],'capture_fallback':[]},
                    {key:value for key,value in profile.items() if key!='verified_edit'},
                    dict(profile,schema_version=True)):
                path.write_text(json.dumps(old),encoding='utf-8')
                with self.assertRaises(HuginError):load_target_approvals(root)


if __name__=='__main__': unittest.main()
