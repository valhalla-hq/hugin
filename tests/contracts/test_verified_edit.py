"""Delivery policy follows proven field capabilities, independently of app names."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from hugin.errors import HuginError
from hugin.targets import load_target_approvals
from hugin.windows.clipboard import ClipboardService
from test_windows_clipboard import FakeClipboard


class VerifiedEditPolicy(unittest.TestCase):
    def test_parsed_generic_policy_delivers_unknown_app_and_preserves_clipboard(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic capability pilot proof',encoding='utf-8')
            (root/'config/targets.json').write_text(json.dumps({
                'schema_version':2,'delivery':[],'capture_fallback':[],
                'verified_edit':{'restore_delay_seconds':.25,'evidence':'proof.md'}}),encoding='utf-8')
            profile=load_target_approvals(root)
            backend=FakeClipboard()
            backend.target=replace(backend.target,control_class='UnknownEditableApp',package_family=None)
            baseline=backend.data.copy();delays=[]
            backend.sleep=delays.append
            service=ClipboardService(backend=backend)
            service.approve_verified_edits(profile.verified_edit.restore_delay_seconds)
            result=service.deliver('synthetic',backend.target,lambda:True)
            self.assertEqual((result.status,result.submitted,result.restored),('submitted',True,True))
            self.assertEqual((backend.pastes,delays,backend.data),(1,[.25],baseline))

    def test_package_override_precedes_generic_delay(self):
        backend=FakeClipboard();delays=[];backend.sleep=delays.append
        backend.target=replace(backend.target,control_class='Chrome_WidgetWin_1',
            package_family='OpenAI.Codex_2p2nqsd0c76g0')
        service=ClipboardService(backend=backend)
        service.approve_verified_edits(.25)
        service.approve_target_class('Chrome_WidgetWin_1',.15,
            package_family='OpenAI.Codex_2p2nqsd0c76g0')
        self.assertTrue(service.deliver('synthetic',backend.target,lambda:True).submitted)
        self.assertEqual(delays,[.15])

    def test_unknown_field_and_changed_focus_never_stage_or_paste(self):
        for invalid in ('no_target','no_range','changed_focus'):
            with self.subTest(invalid=invalid):
                backend=FakeClipboard();service=ClipboardService(backend=backend)
                service.approve_verified_edits(.25)
                target=backend.target
                if invalid=='no_target':target=None
                elif invalid=='no_range':target=replace(target,caret=None,selection=None)
                else:backend.target=replace(target,focus=201)
                result=service.deliver('synthetic',target,lambda:True)
                self.assertEqual(result.status,'target_changed' if invalid=='changed_focus' else 'target_unverifiable')
                self.assertEqual((backend.mutations,backend.pastes),(0,0))

    def test_generic_policy_requires_bounded_delay_and_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic proof',encoding='utf-8')
            for policy in (True,{}, {'restore_delay_seconds':True,'evidence':'proof.md'},
                    {'restore_delay_seconds':.01,'evidence':'proof.md'},
                    {'restore_delay_seconds':float('inf'),'evidence':'proof.md'},
                    {'restore_delay_seconds':10**400,'evidence':'proof.md'},
                    {'restore_delay_seconds':.25,'evidence':'missing.md'},
                    {'restore_delay_seconds':.25,'evidence':'../proof.md'},
                    {'restore_delay_seconds':.25,'evidence':'proof.md','wildcard':True}):
                (root/'config/targets.json').write_text(json.dumps({
                    'schema_version':2,'delivery':[],'capture_fallback':[],
                    'verified_edit':policy}),encoding='utf-8')
                with self.assertRaises(HuginError):load_target_approvals(root)

    def test_internal_seam_rejects_nonfinite_or_boolean_delay(self):
        service=ClipboardService(backend=FakeClipboard())
        for delay in (True,float('nan'),float('inf'),10**400,0,2.01,'0.25'):
            with self.assertRaises(ValueError):service.approve_verified_edits(delay)


if __name__=='__main__':unittest.main()
