"""Current-focus paste policy and bounded app-specific settling delays."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from hugin.errors import HuginError
from hugin.targets import load_target_approvals
from hugin.windows.clipboard import ClipboardService
from test_windows_clipboard import FakeClipboard


class CurrentFocusPolicy(unittest.TestCase):
    def test_parsed_generic_policy_delivers_unknown_app_and_retains_dictation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            (root/'proof.md').write_text('Synthetic capability pilot proof',encoding='utf-8')
            (root/'config/targets.json').write_text(json.dumps({
                'schema_version':3,'delivery':[],'capture_fallback':[],
                'current_focus':{'restore_delay_seconds':.25,'evidence':'proof.md'}}),encoding='utf-8')
            profile=load_target_approvals(root)
            backend=FakeClipboard()
            backend.target=replace(backend.target,control_class='UnknownEditableApp',package_family=None)
            delays=[]
            backend.sleep=delays.append
            service=ClipboardService(backend=backend)
            service.approve_current_focus(profile.current_focus.restore_delay_seconds)
            result=service.deliver('synthetic',lambda:True)
            self.assertEqual((result.status,result.submitted,result.copied),('submitted',True,True))
            self.assertEqual((backend.pastes,delays,backend.data),(1,[.25],{13:'synthetic\0'.encode('utf-16-le')}))

    def test_package_override_precedes_generic_delay(self):
        backend=FakeClipboard();delays=[];backend.sleep=delays.append
        backend.target=replace(backend.target,control_class='Chrome_WidgetWin_1',
            package_family='OpenAI.Codex_2p2nqsd0c76g0')
        service=ClipboardService(backend=backend)
        service.approve_current_focus(.25)
        service.approve_target_class('Chrome_WidgetWin_1',.15,
            package_family='OpenAI.Codex_2p2nqsd0c76g0')
        self.assertTrue(service.deliver('synthetic',lambda:True).submitted)
        self.assertEqual(delays,[.15])

    def test_current_focus_without_native_caret_or_range_receives_paste(self):
        for current in ('no_range','changed_focus'):
            with self.subTest(current=current):
                backend=FakeClipboard();service=ClipboardService(backend=backend)
                service.approve_current_focus(.25)
                if current=='no_range':backend.target=replace(backend.target,caret=None,selection=None,native_editable=False)
                else:backend.target=replace(backend.target,focus=201)
                result=service.deliver('synthetic',lambda:True)
                self.assertEqual(result.status,'submitted')
                self.assertEqual((backend.mutations,backend.pastes),(1,1))

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
                    'schema_version':3,'delivery':[],'capture_fallback':[],
                    'current_focus':policy}),encoding='utf-8')
                with self.assertRaises(HuginError):load_target_approvals(root)

    def test_internal_seam_rejects_nonfinite_or_boolean_delay(self):
        service=ClipboardService(backend=FakeClipboard())
        for delay in (True,float('nan'),float('inf'),10**400,0,2.01,'0.25'):
            with self.assertRaises(ValueError):service.approve_current_focus(delay)


if __name__=='__main__':unittest.main()
