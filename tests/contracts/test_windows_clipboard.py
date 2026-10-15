from dataclasses import replace
from pathlib import Path
import unittest

from hugin.targets import load_target_approvals
from hugin.windows.clipboard import (ClipboardService, WindowTarget, UiaTargetIdentity, ClipboardSnapshot,
                                     ClipboardFailure, MAX_SNAPSHOT_BYTES)


class FakeClipboard:
    def __init__(self):
        self.target = WindowTarget(100, 200, 3, 4, 500, 'Edit', (200, 1, 2, 3, 4), (2, 2), native_editable=True)
        self.data = {13: 'original\0'.encode('utf-16-le'), 0xC001: b'html', 8: b'dib'}
        self.seq = 1
        self.owner = 90
        self.mutations = 0
        self.pastes = 0
        self.injected = []
        self.modifiers = False
        self.selection = 'selected'
        self.after_stage = lambda: None
        self.before_commit = lambda: None
        self.snapshot_failure = None
        self.copy_owner = self.target.hwnd
        self.clipboard_locked = False
        self.direct_text = None
        self.after_direct = lambda: None

    def capture_native_target(self):
        return self.target.without_uia

    def capture_target(self,*,expected=None,cancelled=lambda:False):
        if cancelled():raise ClipboardFailure('cancelled')
        if expected is not None and self.target.without_uia!=expected.without_uia:
            raise ClipboardFailure('target_changed')
        return self.target

    def modifiers_down(self):
        return self.modifiers

    def read_direct_selection(self, target, limit, cancelled):
        self.after_direct()
        return self.direct_text

    def sequence(self):
        return self.seq

    def restorable_sequence(self,expected):
        return expected if self.seq==expected else None

    def snapshot(self, budget):
        if self.snapshot_failure:
            raise ClipboardFailure(self.snapshot_failure)
        if sum(map(len, self.data.values())) > budget:
            raise ClipboardFailure('snapshot_limit')
        return ClipboardSnapshot(self.seq, tuple(self.data.items()))

    def replace(self, formats, expected=None):
        if expected is not None and expected != self.seq:
            raise ClipboardFailure('clipboard_changed')
        self.data = dict(formats)
        self.seq += 1
        self.owner = 999
        self.mutations += 1
        return self.seq

    def stage(self, formats, expected):
        result = self.replace(formats, expected)
        self.after_stage()
        return result

    def copy_selection(self, target):
        self.injected.append('copy')
        if self.selection is not None:
            self.data = {13: (self.selection + '\0').encode('utf-16-le')}
            self.seq += 1
            self.owner = self.copy_owner

    def read_selection(self, expected, target, limit):
        if self.owner not in (target.hwnd, target.focus):
            raise ClipboardFailure('clipboard_changed')
        return self.data[13].decode('utf-16-le').rstrip('\0')

    def commit_paste(self, expected, target, still_current, authorize=None, transaction=None,commit=None):
        self.before_commit()
        submitted=False
        def fast_commit():
            nonlocal submitted
            if submitted:raise ClipboardFailure('commit_rejected',submitted=True)
            if self.seq != expected:raise ClipboardFailure('clipboard_changed')
            if self.target != target:raise ClipboardFailure('target_changed')
            if not still_current():raise ClipboardFailure('cancelled')
            if self.modifiers:raise ClipboardFailure('modifiers_active')
            if authorize is not None and not authorize(transaction):raise ClipboardFailure('commit_rejected')
            self.pastes+=1;submitted=True
        if commit is None:fast_commit()
        else:commit(transaction,fast_commit)
        if not submitted:raise ClipboardFailure('commit_rejected')

    def sleep(self, seconds):
        pass


class ClipboardContracts(unittest.TestCase):
    def test_shipped_profile_delivers_proven_fields_with_codex_delay_overrides(self):
        profile=load_target_approvals(Path(__file__).resolve().parents[2])
        family='OpenAI.Codex_2p2nqsd0c76g0'
        for control in ('Chrome_RenderWidgetHostHWND','Chrome_WidgetWin_1','Chrome_WidgetWin_2'):
            for package in (family,None,'Unrelated.Browser_2p2nqsd0c76g0',family.lower()):
                with self.subTest(control=control,package=package):
                    backend=FakeClipboard()
                    backend.target=replace(backend.target,control_class=control,package_family=package,
                        native_editable=False,uia=UiaTargetIdentity((1,),(2,),(3,),(3,),3,(2,2),-1,-1))
                    saved=backend.data.copy();snapshots=[];snapshot=backend.snapshot
                    backend.snapshot=lambda budget:snapshots.append(budget) or snapshot(budget)
                    delays=[];backend.sleep=delays.append
                    service=ClipboardService(backend=backend)
                    for approval in profile.delivery:
                        service.approve_target_class(approval.control_class,approval.restore_delay_seconds,
                            package_family=approval.package_family)
                    service.approve_verified_edits(profile.verified_edit.restore_delay_seconds)
                    result=service.deliver('synthetic',backend.target,lambda:True)
                    override=control!='Chrome_WidgetWin_2' and package==family
                    self.assertEqual((result.status,result.submitted,result.restored),
                        ('submitted',True,True))
                    self.assertEqual(delays,[.15 if override else .25])
                    self.assertEqual((backend.pastes,len(snapshots),backend.mutations),(1,1,2))
                    self.assertEqual(backend.data,saved)

    def test_shipped_generic_policy_does_not_approve_missing_field_proof(self):
        profile=load_target_approvals(Path(__file__).resolve().parents[2])
        backend=FakeClipboard();backend.target=replace(backend.target,native_editable=False)
        service=ClipboardService(backend=backend)
        service.approve_verified_edits(profile.verified_edit.restore_delay_seconds)
        result=service.deliver('synthetic',backend.target,lambda:True)
        self.assertEqual((result.status,backend.pastes,backend.mutations),('target_unverifiable',0,0))

    def service(self):
        backend = FakeClipboard()
        service = ClipboardService(backend=backend, selection_timeout=0.005)
        service.approve_capture_target_class('Edit')
        return backend, service

    def test_capture_is_gated_without_target_attribution_pilot(self):
        backend = FakeClipboard()
        service = ClipboardService(backend=backend)
        self.assertEqual(service.capture_selection(lambda: False).status, 'target_unverified')
        self.assertEqual(backend.mutations, 0)
        self.assertEqual(backend.injected, [])

    def test_direct_selection_needs_no_clipboard_fallback_approval(self):
        backend = FakeClipboard()
        backend.direct_text = 'selected directly'
        backend.snapshot_failure = 'format_unsupported'
        saved = backend.data.copy()
        service = ClipboardService(backend=backend)
        result = service.capture_selection(lambda: False)
        self.assertEqual((result.status, result.text), ('captured', 'selected directly'))
        self.assertEqual(backend.mutations, 0)
        self.assertEqual(backend.injected, [])
        self.assertEqual(backend.data, saved)

    def test_empty_direct_selection_never_uses_clipboard_text(self):
        backend = FakeClipboard()
        backend.direct_text = ''
        result = ClipboardService(backend=backend).capture_selection(lambda: False)
        self.assertEqual(result.status, 'selection_empty')
        self.assertIsNone(result.text)
        self.assertEqual(backend.mutations, 0)

    def test_cancel_or_target_change_after_direct_read_discards_text(self):
        for reason in ('cancel', 'target'):
            backend = FakeClipboard()
            backend.direct_text = 'must not publish'
            state = {'cancelled': False}
            if reason == 'cancel':
                backend.after_direct = lambda: state.update(cancelled=True)
            else:
                backend.after_direct = lambda: setattr(backend, 'target', replace(backend.target, focus=201))
            result = ClipboardService(backend=backend).capture_selection(lambda: state['cancelled'])
            self.assertEqual(result.status, 'cancelled' if reason == 'cancel' else 'target_changed')
            self.assertIsNone(result.text)
            self.assertEqual(backend.mutations, 0)

    def test_unknown_delayed_or_oversize_snapshot_never_mutates(self):
        for reason in ('format_unsupported', 'format_delayed', 'snapshot_limit'):
            with self.subTest(reason=reason):
                backend, service = self.service()
                backend.snapshot_failure = reason
                result = service.capture_selection(lambda: False)
                self.assertEqual(result.status, reason)
                self.assertEqual(backend.mutations, 0)
                self.assertEqual(backend.injected, [])

    def test_capture_never_falls_back_to_old_text_and_restores_supported_formats(self):
        backend, service = self.service()
        saved = backend.data.copy()
        result = service.capture_selection(lambda: False)
        self.assertEqual(result.status, 'captured')
        self.assertEqual(result.text, 'selected')
        self.assertEqual(backend.data, saved)
        backend.selection = None
        result = service.capture_selection(lambda: False)
        self.assertEqual(result.status, 'selection_empty')
        self.assertIsNone(result.text)
        self.assertEqual(backend.data, saved)

    def test_user_copy_during_capture_wins(self):
        backend, service = self.service()
        backend.copy_owner = 9999
        result = service.capture_selection(lambda: False)
        self.assertEqual(result.status, 'clipboard_changed')
        self.assertIn('selected', backend.data[13].decode('utf-16-le'))
        self.assertEqual(backend.mutations, 1)

    def test_changed_caret_control_or_window_prevents_staging(self):
        for change in ({'hwnd': 101}, {'focus': 201}, {'caret': (200, 2, 2, 3, 4)},
                       {'selection': (3, 3)}, {'process_created': 501}):
            backend, service = self.service()
            target = backend.target
            backend.target = replace(target, **change)
            result = service.deliver('dictation', target, lambda: True)
            self.assertEqual(result.status, 'target_changed')
            self.assertEqual(backend.mutations, 0)
            self.assertEqual(backend.pastes, 0)

    def test_paste_is_gated_until_restore_timing_is_proven(self):
        backend, service = self.service()
        result = service.deliver('dictation', backend.target, lambda: True)
        self.assertEqual(result.status, 'target_unverified')
        self.assertEqual(backend.mutations, 0)

    def test_user_copy_between_stage_and_commit_prevents_paste_and_restore(self):
        backend, service = self.service()
        service.approve_target_class('Edit', 0.02)
        def user_copy():
            backend.replace({13: b'user copy'})
        backend.after_stage = user_copy
        result = service.deliver('dictation', backend.target, lambda: True)
        self.assertEqual(result.status, 'clipboard_changed')
        self.assertEqual(backend.pastes, 0)
        self.assertEqual(backend.data[13], b'user copy')

    def test_cancel_at_serialized_commit_prevents_paste(self):
        backend, service = self.service()
        service.approve_target_class('Edit', 0.02)
        state = {'current': True}
        backend.before_commit = lambda: state.update(current=False)
        result = service.deliver('dictation', backend.target, lambda: state['current'])
        self.assertEqual(result.status, 'cancelled')
        self.assertEqual(backend.pastes, 0)

    def test_authorization_sees_staged_transaction_after_checks_and_can_reject(self):
        backend, service = self.service()
        service.approve_target_class('Edit', 0.02)
        saved = backend.data.copy()
        transactions = []
        def reject(transaction):
            self.assertEqual(backend.seq, transaction.sequence)
            self.assertEqual(backend.target, transaction.target)
            self.assertEqual(backend.pastes, 0)
            self.assertIn('dictation', backend.data[13].decode('utf-16-le'))
            self.assertNotIn('dictation', repr(transaction))
            transactions.append(transaction)
            return False
        result = service.deliver('dictation', backend.target, lambda: True, authorize=reject)
        self.assertEqual(result.status, 'commit_rejected')
        self.assertEqual(len(transactions), 1)
        self.assertEqual(backend.pastes, 0)
        self.assertEqual(backend.data, saved)

    def test_conflict_never_calls_authorization(self):
        backend, service = self.service()
        service.approve_target_class('Edit', 0.02)
        backend.after_stage = lambda: backend.replace({13: b'user'})
        calls = []
        result = service.deliver('dictation', backend.target, lambda: True,
                                 authorize=lambda transaction: calls.append(transaction) or True)
        self.assertEqual(result.status, 'clipboard_changed')
        self.assertEqual(calls, [])

    def test_success_submits_once_no_enter_and_restores(self):
        backend, service = self.service()
        service.approve_target_class('Edit', 0.02)
        saved = backend.data.copy()
        result = service.deliver('dictation', backend.target, lambda: True)
        self.assertEqual(result.status, 'submitted')
        self.assertTrue(result.submitted)
        self.assertEqual(backend.pastes, 1)
        self.assertEqual(backend.data, saved)

    def test_cancel_or_held_modifier_has_no_native_effect(self):
        backend, service = self.service()
        self.assertEqual(service.capture_selection(lambda: True).status, 'cancelled')
        backend.modifiers = True
        self.assertEqual(service.capture_selection(lambda: False).status, 'modifiers_active')
        self.assertEqual(backend.mutations, 0)
        self.assertEqual(backend.injected, [])

    def test_explicit_copy_does_not_restore(self):
        backend, service = self.service()
        self.assertEqual(service.copy('manual copy').status, 'copied')
        self.assertEqual(backend.data[13].decode('utf-16-le'), 'manual copy\0')

    def test_failed_restore_retains_snapshot_and_blocks_new_automatic_work(self):
        backend, service = self.service()
        service.approve_target_class('Edit', 0.02)
        saved = backend.data.copy()
        original = backend.replace
        broken = {'value': True}
        def replace_or_fail(formats, expected=None):
            if expected is not None and expected != backend.seq:
                raise ClipboardFailure('clipboard_changed')
            if len(formats) > 1 and broken['value']:
                backend.data = {13: b'partial restore'}
                backend.seq += 1
                raise ClipboardFailure('clipboard_write_failed', owned_sequence=backend.seq)
            return original(formats, expected)
        backend.replace = replace_or_fail
        result = service.deliver('dictation', backend.target, lambda: True)
        self.assertEqual(result.status, 'clipboard_restore_failed')
        self.assertTrue(result.submitted)
        self.assertTrue(service.recovery_pending)
        self.assertEqual(service.capture_selection(lambda: False).status, 'clipboard_recovery_pending')
        broken['value'] = False
        self.assertEqual(service.recover().status, 'restored')
        self.assertFalse(service.recovery_pending)
        self.assertEqual(backend.data, saved)

    def test_user_copy_supersedes_retained_restore(self):
        backend, service = self.service()
        service._pending_restore = (ClipboardSnapshot(1, ((13, b'old'),)), 1)
        backend.replace({13: b'user'})
        self.assertEqual(service.recover().status, 'clipboard_changed')
        self.assertEqual(backend.data[13], b'user')
        self.assertFalse(service.recovery_pending)

    def test_pending_restore_uses_producer_owned_publication_instead_of_raw_clock(self):
        backend,service=self.service();saved=backend.snapshot(1024)
        backend.replace(((13,b'own staged text'),))
        service._pending_restore=(saved,1)
        backend.restorable_sequence=lambda expected:backend.seq
        self.assertEqual(service.capture_selection(lambda:False).status,'clipboard_recovery_pending')
        self.assertTrue(service.recovery_pending)
        self.assertEqual(service.recover().status,'restored')
        self.assertEqual(backend.data,dict(saved.formats))

    def test_unknown_publication_keeps_ram_snapshot_until_recovery_is_proven(self):
        backend,service=self.service();saved=backend.snapshot(1024)
        backend.replace(((13,b'own staged text'),))
        service._pending_restore=(saved,1)
        def unknown(expected):raise ClipboardFailure('clipboard_busy')
        backend.restorable_sequence=unknown
        self.assertEqual(service.capture_selection(lambda:False).status,'clipboard_busy')
        self.assertTrue(service.recovery_pending)
        self.assertEqual(service.recover().status,'clipboard_restore_failed')
        self.assertTrue(service.recovery_pending)
        backend.restorable_sequence=lambda expected:backend.seq
        self.assertEqual(service.recover().status,'restored')
        self.assertEqual(backend.data,dict(saved.formats))

    def test_user_copy_after_recovery_observation_still_wins_atomic_replace(self):
        backend,service=self.service();saved=backend.snapshot(1024)
        backend.replace(((13,b'own staged text'),))
        service._pending_restore=(saved,backend.seq)
        def observe(expected):
            if backend.owner!=999:return None
            observed=backend.seq
            backend.replace(((13,b'new user copy'),));backend.owner=200
            return observed
        backend.restorable_sequence=observe
        self.assertEqual(service.recover().status,'clipboard_changed')
        self.assertEqual(backend.data,{13:b'new user copy'})
        self.assertFalse(service.recovery_pending)

    def test_budget_cannot_exceed_contract(self):
        with self.assertRaises(ValueError):
            ClipboardService(backend=FakeClipboard(), snapshot_budget=MAX_SNAPSHOT_BYTES + 1)
