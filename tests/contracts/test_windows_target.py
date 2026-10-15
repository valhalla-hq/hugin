"""Target metadata contracts; only bounded synthetic Edit prefixes are read."""
from dataclasses import replace
from contextlib import contextmanager
import io
import json
import queue
import struct
import threading
import weakref
from types import SimpleNamespace as NS
import unittest

from hugin.windows.clipboard import WindowTarget,UiaTargetIdentity,NativeClipboard,ClipboardFailure,ClipboardService
from hugin.windows.selection import (SelectionProbe,TargetResult,encode_request,decode_operation,
    encode_target_response,decode_target_response)
from hugin.windows.selection_probe import read_uia_target,_target_proof,confirm_uia_target
from test_windows_selection import FakeProcess

BASE=WindowTarget(100,100,3,4,500,'Chrome_WidgetWin_1',None,None)


class Range:
    def __init__(self,owner,start,end,model=None):
        self.owner,self.start,self.end=owner,start,end
        self.model=model or owner.pattern
    def Clone(self):return Range(self.owner,self.start,self.end,self.model)
    def CompareEndpoints(self,endpoint,other,other_endpoint):
        left=self.start if endpoint==0 else self.end
        right=other.start if other_endpoint==0 else other.end
        return 19 if left>right else -19 if left<right else 0
    def GetEnclosingElement(self):return self.owner
    def GetChildren(self):
        return NS(Length=sum(self.start<=self.model.origin+point<self.end for point in self.model.embedded))
    def MoveEndpointByRange(self,endpoint,other,other_endpoint):
        value=other.start if other_endpoint==0 else other.end
        if endpoint==0:self.start=value;self.end=max(self.end,value)
        else:self.end=value;self.start=min(self.start,value)
    def MoveEndpointByUnit(self,endpoint,unit,count):
        raise AssertionError('target proof must not walk character units')
    def GetText(self,limit):
        assert 0<limit<=262145
        text=self.model.text if self.model.text is not None else 'x'*self.model.extent
        return text[self.start-self.model.origin:self.end-self.model.origin][:limit]
    def Select(self):raise AssertionError('metadata must not change selection')


class Ranges:
    Length=1
    def __init__(self,selected):self.selected=selected
    def GetElement(self,index):return self.selected


class Pattern:
    SupportedTextSelection=1
    def __init__(self,owner):self.owner=owner;self.position=7;self.origin=900;self.extent=100;self.width=0;self.after=lambda:None;self.text=None;self.embedded=()
    def QueryInterface(self,*args):return self
    def GetSelection(self):
        selected=Range(self.owner,self.origin+self.position,self.origin+self.position+self.width,self)
        self.after();return Ranges(selected)
    @property
    def DocumentRange(self):return Range(self.owner,self.origin,self.origin+self.extent,self)


class Element:
    CurrentControlType=50004;CurrentIsEnabled=True;CurrentHasKeyboardFocus=True
    CurrentIsPassword=False;CurrentIsReadOnly=False;CurrentProcessId=9
    def __init__(self,identity,parent=None):self.identity,self.parent=identity,parent;self.pattern=Pattern(self)
    def GetRuntimeId(self):return (42,self.identity)
    def GetCurrentPropertyValue(self,identity):return True
    def GetCurrentPattern(self,identity):return self.pattern if identity==10014 else self
    def QueryInterface(self,*args):return self
    @property
    def CurrentValue(self):raise AssertionError('metadata must not read Value')


class Automation:
    class Walker:
        def GetParentElement(self,element):return element.parent
    RawViewWalker=Walker()
    def __init__(self):
        self.root=Element(1);self.root.CurrentProcessId=BASE.pid
        self.focus=Element(2,self.root)
    def GetFocusedElement(self):return self.focus
    def ElementFromHandle(self,hwnd):return self.root
    def CompareElements(self,left,right):return left is right


class Uia:
    UIA_EditControlTypeId=50004;UIA_IsTextPatternAvailablePropertyId=30040
    UIA_IsValuePatternAvailablePropertyId=30043;UIA_TextPatternId=10014;UIA_ValuePatternId=10002
    IUIAutomationTextPattern=object();IUIAutomationValuePattern=object();TextUnit_Character=0


class TargetContracts(unittest.TestCase):
    def test_owned_text_end_affinity_uses_the_logical_utf16_offset(self):
        automation=Automation();pattern=automation.focus.pattern
        child=Element(77,automation.focus);child.CurrentControlType=50020
        pattern.owner=child;pattern.extent=4;pattern.position=5;pattern.text='Test'
        result=self.read(automation)
        self.assertEqual(result.status,'target_captured')
        self.assertEqual(result.identity.position,4)
        self.assertEqual(result.identity.caret_id,child.GetRuntimeId())
        pattern.position=0
        self.assertEqual(self.read(automation).identity.position,0)

    def test_utf16_offset_does_not_assume_one_character_unit_per_python_character(self):
        automation=Automation();pattern=automation.focus.pattern
        pattern.text='A😀e\u0301';pattern.position=4
        result=self.read(automation)
        self.assertEqual(result.status,'target_captured')
        self.assertEqual(result.identity.position,5)

    def test_changed_end_affinity_cannot_alias_the_frozen_offset_and_child(self):
        automation=Automation();pattern=automation.focus.pattern;child=Element(77,automation.focus)
        pattern.owner=child;pattern.extent=4;pattern.position=5;pattern.text='Test'
        proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
        pattern.position=4
        self.assertEqual(confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof).status,'target_changed')

    def test_embedded_object_and_omitted_plaintext_cannot_prove_a_caret(self):
        from unittest.mock import patch
        automation=Automation();pattern=automation.focus.pattern
        pattern.text='AB\ufffcCD';pattern.extent=5;pattern.position=2;pattern.embedded=(2,)
        original=Range.GetText
        def plain(text_range,limit):return original(text_range,limit).replace('\ufffc','')
        with patch.object(Range,'GetText',plain):
            self.assertEqual(self.read(automation).status,'target_unverifiable')
            pattern.text='ABCD';pattern.extent=4;pattern.embedded=()
            proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
            pattern.text='AB\ufffcCD';pattern.extent=5;pattern.position=3;pattern.embedded=(2,)
            self.assertEqual(confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof).status,'target_unverifiable')

    def test_unknown_embedded_children_are_rejected_before_reading_text(self):
        from unittest.mock import patch
        for children in (None,NS(Length=True),NS(Length=-1),NS(Length=1)):
            with patch.object(Range,'GetChildren',return_value=children),patch.object(Range,'GetText',side_effect=AssertionError('unknown structure read')):
                self.assertEqual(self.read(Automation()).status,'target_unverifiable')

    def test_changes_during_last_warm_text_read_are_rejected(self):
        from unittest.mock import patch
        for kind in ('caret','readonly','disabled','child','embedded'):
            automation=Automation();pattern=automation.focus.pattern
            first=Element(77,automation.focus);second=Element(78,automation.focus);pattern.owner=first
            proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
            original=Range.GetText;calls=0
            def read(text_range,limit):
                nonlocal calls
                value=original(text_range,limit);calls+=1
                if calls==2:
                    if kind=='caret':pattern.position+=1
                    elif kind=='readonly':automation.focus.CurrentIsReadOnly=True
                    elif kind=='disabled':automation.focus.CurrentIsEnabled=False
                    elif kind=='child':pattern.owner=second
                    else:pattern.embedded=(2,)
                return value
            with patch.object(Range,'GetText',read):
                result=confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof)
            self.assertEqual(result.status,'target_unverifiable' if kind in ('readonly','disabled','embedded') else 'target_changed',kind)

    def test_full_proof_rechecks_caret_child_after_last_text_read(self):
        from unittest.mock import patch
        automation=Automation();pattern=automation.focus.pattern
        first=Element(77,automation.focus);second=Element(78,automation.focus);pattern.owner=first
        original=Range.GetText;calls=0
        def read(text_range,limit):
            nonlocal calls
            value=original(text_range,limit);calls+=1
            if calls==2:pattern.owner=second
            return value
        with patch.object(Range,'GetText',read):self.assertEqual(self.read(automation).status,'target_changed')

    def test_descendant_caret_is_owned_by_the_focused_edit(self):
        from unittest.mock import patch
        automation=Automation();child=Element(77,automation.focus)
        child.CurrentControlType=50026
        with patch.object(Range,'GetEnclosingElement',lambda selected:child):
            proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
            self.assertEqual(proof.identity.position,7)
            automation.focus.pattern.origin+=4000
            self.assertEqual(confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof).status,
                'target_captured')

    def test_foreign_protected_cyclic_or_unbounded_enclosure_never_proves_a_caret(self):
        from unittest.mock import patch
        for kind in ('foreign','orphan','password','cycle','depth'):
            automation=Automation();child=Element(77,automation.focus)
            if kind=='foreign':child.parent=automation.root
            elif kind=='orphan':child.parent=None
            elif kind=='password':child.CurrentIsPassword=True
            elif kind=='cycle':child.parent=child
            else:
                for identity in range(100,165):child=Element(identity,child)
            with patch.object(Range,'GetEnclosingElement',lambda selected:child):
                self.assertEqual(self.read(automation).status,'target_unverifiable',kind)

    def test_same_offset_in_another_owned_child_cannot_alias_the_frozen_caret(self):
        automation=Automation();first=Element(77,automation.focus);second=Element(78,automation.focus)
        automation.focus.pattern.owner=first
        proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
        automation.focus.pattern.owner=second
        self.assertEqual(confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof).status,'target_changed')

    def test_foreign_prefix_is_rejected_before_reading_its_text(self):
        from unittest.mock import patch
        automation=Automation()
        def enclosing(text_range):return automation.focus if text_range.start==text_range.end else automation.root
        with patch.object(Range,'GetEnclosingElement',enclosing),patch.object(Range,'GetText',side_effect=AssertionError('foreign prefix read')):
            self.assertEqual(self.read(automation).status,'target_unverifiable')

    def test_prefix_read_is_bounded_and_malformed_or_oversize_text_is_rejected(self):
        from unittest.mock import patch
        for text in (None,True,'bad\0value','\ud800','x'*262145,'😀'*131073):
            def read(prefix,limit):
                self.assertEqual(limit,262145)
                return text
            with patch.object(Range,'GetText',read):
                self.assertEqual(self.read(Automation()).status,'target_unverifiable')

    def test_prefix_provider_exception_does_not_leave_text_in_the_wire_response(self):
        from unittest.mock import patch
        with patch.object(Range,'GetText',side_effect=RuntimeError('private synthetic marker')):
            result=self.read(Automation())
        self.assertEqual(result.status,'target_probe_failed')
        self.assertIsNone(result.identity)
        self.assertNotIn(b'private synthetic marker',encode_target_response(result))

    def test_local_points_do_not_walk_before_the_edit_when_page_prefix_changes(self):
        from unittest.mock import patch
        for position in (1,7,20,100):
            automation=Automation();automation.focus.pattern.position=position
            automation.focus.pattern.origin=300000
            with patch.object(Range,'MoveEndpointByUnit',side_effect=AssertionError('character walk')):
                first=self.read(automation)
                self.assertEqual(first.status,'target_captured',position)
                self.assertEqual(first.identity.position,position)
                automation.focus.pattern.origin+=4000
                self.assertEqual(self.read(automation).identity,first.identity)

    def test_edit_start_is_proven_without_walking_unrelated_page_content(self):
        from unittest.mock import patch
        automation=Automation();automation.focus.pattern.position=0
        automation.focus.pattern.origin=300000
        with patch.object(Range,'GetText',side_effect=AssertionError('Edit start must not read text')):
            proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
            self.assertEqual(proof.identity.position,0)
            automation.focus.pattern.origin+=4000
            result=confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof)
            self.assertEqual(result.status,'target_captured')
            self.assertEqual(result.identity,proof.identity)

    def test_warm_proof_rechecks_selection_and_editability_after_measuring(self):
        for kind in ('position','edit','readonly'):
            automation=Automation();proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
            original=automation.focus
            def after():
                if kind=='position':original.pattern.position+=1
                if kind=='edit':automation.focus=Element(99,automation.root)
                if kind=='readonly':original.CurrentIsReadOnly=True
            original.pattern.after=after
            result=confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof)
            self.assertEqual(result.status,'target_unverifiable' if kind=='readonly' else 'target_changed',kind)

    def test_warm_proof_checks_current_edit_and_local_point_without_ancestor_walk(self):
        for kind in ('same','chat_shift','caret','edit','readonly'):
            automation=Automation()
            proof=_target_proof(automation,Uia,BASE,lambda:BASE,lambda:False)
            if kind=='chat_shift':automation.focus.pattern.origin+=4000
            if kind=='caret':automation.focus.pattern.position+=1
            if kind=='edit':automation.focus=Element(99,automation.root)
            if kind=='readonly':automation.focus.CurrentIsReadOnly=True
            automation.RawViewWalker=NS(GetParentElement=lambda element:(_ for _ in ()).throw(AssertionError('warm ancestor walk')))
            result=confirm_uia_target(automation,Uia,BASE,lambda:BASE,proof)
            expected='target_captured' if kind in ('same','chat_shift') else 'target_unverifiable' if kind=='readonly' else 'target_changed'
            self.assertEqual(result.status,expected,kind)
    def test_package_scoped_approval_never_grants_other_chrome_targets(self):
        from test_windows_clipboard import FakeClipboard
        family='OpenAI.Codex_2p2nqsd0c76g0'
        backend=FakeClipboard();service=ClipboardService(backend=backend)
        service.approve_target_class('Chrome_WidgetWin_1',.02,package_family=family)
        for observed in (None,'Other.Package_2p2nqsd0c76g0'):
            backend.target=replace(backend.target,control_class='Chrome_WidgetWin_1',package_family=observed)
            self.assertEqual(service.deliver('synthetic',backend.target,lambda:True).status,'target_unverified')
            self.assertEqual(backend.mutations,0)
        backend.target=replace(backend.target,package_family=family)
        self.assertEqual(service.deliver('synthetic',backend.target,lambda:True).status,'submitted')
        decoded=decode_operation(encode_request(backend.target,operation='target')[4:])[1]
        self.assertEqual(decoded.package_family,family)

    def test_package_family_query_is_bounded_and_unknown_is_not_absence_proof(self):
        import ctypes
        from ctypes import wintypes as W
        family='OpenAI.Codex_2p2nqsd0c76g0';native=NativeClipboard.__new__(NativeClipboard)
        calls=[]
        def query(handle,length,buffer):
            self.assertEqual(handle,77);capacity=ctypes.cast(length,ctypes.POINTER(W.UINT))
            calls.append(buffer is None)
            if buffer is None:capacity[0]=len(family)+1;return 122
            buffer.value=family;capacity[0]=len(family)+1;return 0
        native.kernel=NS(GetPackageFamilyName=query)
        self.assertEqual(native._package_family(77),family)
        self.assertEqual(calls,[True,False])
        for error in (15700,5):
            native.kernel=NS(GetPackageFamilyName=lambda *args:error)
            self.assertIsNone(native._package_family(77))
        def oversize(handle,length,buffer):
            ctypes.cast(length,ctypes.POINTER(W.UINT))[0]=66;return 122
        native.kernel=NS(GetPackageFamilyName=oversize)
        self.assertIsNone(native._package_family(77))

    def read(self,automation,native=lambda:BASE,cancelled=lambda:False):
        return read_uia_target(automation,Uia,BASE,native,cancelled)

    def test_collapsed_edit_returns_only_position_and_runtime_metadata(self):
        result=self.read(Automation())
        self.assertEqual(result.status,'target_captured')
        self.assertEqual(result.identity.position,7)
        self.assertFalse(BASE.verifiable)
        self.assertTrue(replace(BASE,uia=result.identity).verifiable)
        self.assertEqual(replace(BASE,uia=result.identity).without_uia,BASE)

    def test_provider_document_shift_preserves_edit_local_position(self):
        automation=Automation();first=self.read(automation)
        automation.focus.pattern.origin+=4000
        self.assertEqual(self.read(automation).identity,first.identity)

    def test_caret_or_edit_identity_change_changes_full_target(self):
        automation=Automation();first=self.read(automation)
        automation.focus.pattern.position+=1
        self.assertNotEqual(self.read(automation).identity,first.identity)
        automation.focus.identity=3
        self.assertNotEqual(self.read(automation).identity,first.identity)

    def test_noncollapsed_protected_readonly_disabled_and_nonedit_fail_closed(self):
        for change in ('selection','password','readonly','disabled','document'):
            automation=Automation()
            if change=='selection':automation.focus.pattern.width=1
            elif change=='password':automation.focus.CurrentIsPassword=True
            elif change=='readonly':automation.focus.CurrentIsReadOnly=True
            elif change=='disabled':automation.focus.CurrentIsEnabled=False
            else:automation.focus.CurrentControlType=50030
            self.assertEqual(self.read(automation).status,'target_unverifiable',change)

    def test_focus_native_range_and_cancel_changes_during_probe_are_rejected(self):
        for change in ('focus','range','native','cancel'):
            automation=Automation();state={'native':BASE,'cancelled':False}
            def mutate():
                if change=='focus':automation.focus=Element(99,automation.root)
                elif change=='range':automation.focus.pattern.position+=1
                elif change=='native':state['native']=replace(BASE,process_created=501)
                else:state['cancelled']=True
            automation.focus.pattern.after=mutate
            result=self.read(automation,lambda:state['native'],lambda:state['cancelled'])
            self.assertEqual(result.status,'cancelled' if change=='cancel' else 'target_changed')
            self.assertIsNone(result.identity)

    def test_metadata_operation_is_bounded_and_separate_from_selected_text(self):
        identity=self.read(Automation()).identity
        frame=encode_target_response(TargetResult('target_captured',identity))
        self.assertEqual(decode_target_response(io.BytesIO(frame)).identity,identity)
        operation,target=decode_operation(encode_request(BASE,operation='target')[4:])
        self.assertEqual((operation,target),('target',BASE))
        with self.assertRaises(ValueError):decode_target_response(io.BytesIO(frame+b'x'))
        process=FakeProcess(frame)
        probe=SelectionProbe(spawn=lambda *_,**__:process)
        self.assertEqual(probe.capture_target(BASE,lambda:False).identity,identity)
        self.assertTrue(process.closed)

    def test_unbounded_or_foreign_range_is_never_a_target_proof(self):
        for change in ('limit','enclosing','outside'):
            automation=Automation()
            if change=='limit':
                automation.focus.pattern.position=262145;automation.focus.pattern.extent=262145
            elif change=='enclosing':
                automation.focus.pattern.owner=automation.root
            else:automation.focus.pattern.position=101
            self.assertEqual(self.read(automation).status,'target_unverifiable',change)

    def test_metadata_failure_is_sanitized_and_never_drops_cleanup_ownership(self):
        process=FakeProcess(b'',blocked=True,kill_fails=True)
        probe=SelectionProbe(spawn=lambda *_,**__:process,timeout=.02)
        self.assertEqual(probe.capture_target(BASE,lambda:False).status,'target_cleanup_failed')
        self.assertEqual(probe.capture_target(BASE,lambda:False).status,'target_cleanup_pending')
        self.assertFalse(process.closed)
        process.kill_fails=False;probe.close()
        self.assertTrue(process.closed)

    def test_malformed_metadata_and_text_response_cannot_be_target_identity(self):
        from hugin.windows.selection import encode_response
        identity=self.read(Automation()).identity
        for field,bad in (('position',True),('focus_pid',0),('focus_id',[True]),('element_id',list(range(65))),('caret_id',[]),('caret_id',[True]),('end_relation',True),('end_relation',2)):
            value={'focus_id':list(identity.focus_id),'root_id':list(identity.root_id),
                'element_id':list(identity.element_id),'focus_pid':identity.focus_pid,'position':identity.position,'caret_id':list(identity.caret_id),'end_relation':identity.end_relation}
            value[field]=bad;data=json.dumps(value).encode('ascii')
            with self.assertRaises(ValueError):decode_target_response(io.BytesIO(struct.pack('!BBI',2,0,len(data))+data))
        with self.assertRaises(ValueError):decode_target_response(io.BytesIO(encode_response('captured','not metadata')))
        with self.assertRaises(ValueError):decode_target_response(io.BytesIO(struct.pack('!BBI',2,0,4093)))

    def test_full_native_capture_binds_basis_without_recursing_into_full_probe(self):
        identity=self.read(Automation()).identity
        native=NativeClipboard.__new__(NativeClipboard)
        native.capture_native_target=lambda:BASE
        calls=[]
        native._selection_probe=NS(capture_target=lambda basis,cancelled:calls.append(basis) or TargetResult('target_captured',identity))
        self.assertEqual(native.capture_target(expected=BASE).uia,identity)
        self.assertEqual(calls,[BASE])
        with self.assertRaises(ClipboardFailure) as failure:native.capture_target(expected=replace(BASE,process_created=501))
        self.assertEqual(failure.exception.status,'target_changed')
        self.assertEqual(calls,[BASE])
        service=ClipboardService(backend=native)
        self.assertEqual(service.capture_native_target().target,BASE)
        self.assertEqual(calls,[BASE])


class OwnerCommitContracts(unittest.TestCase):
    def test_owner_rechecks_held_clipboard_token_after_warm_confirmation(self):
        for changed in ('sequence','owner','size','token'):
            native,target,events,state=self.backend()
            original=native._selection_probe.begin_delivery
            def begin(basis,cancelled):
                lease=original(basis,cancelled);confirm=lease.confirm
                def changed_confirm():
                    result=confirm()
                    if changed=='sequence':native.sequence=lambda:8
                    if changed=='owner':native.user.GetClipboardOwner=lambda:11
                    if changed=='size':native.kernel.GlobalSize=lambda _:6
                    if changed=='token':native._read_handle=lambda *_:b'other'
                    return result
                lease.confirm=changed_confirm;return lease
            native._selection_probe.begin_delivery=begin
            with self.assertRaises(ClipboardFailure) as failure:
                native.commit_paste(7,target,lambda:True,lambda transaction:events.append(('authorize',0)) or True)
            self.assertEqual(failure.exception.status,'clipboard_changed')
            self.assertFalse(any(kind in ('input','authorize') for kind,_ in events))

    def test_same_native_window_cannot_hide_caret_or_edit_change_before_owner_commit(self):
        for kind in ('position','edit'):
            native,target,events,state=self.backend();state['uia']=target
            native.capture_target=lambda **kwargs:state['uia']
            def commit(transaction,fast):
                changed=replace(target.uia,position=target.uia.position+1) if kind=='position' else replace(target.uia,focus_id=(99,),element_id=(99,))
                state['uia']=replace(target,uia=changed)
                fast()
            with self.assertRaises(ClipboardFailure) as failure:
                native.commit_paste(7,target,lambda:True,lambda transaction:True,object(),commit=commit)
            self.assertEqual(failure.exception.status,'target_changed')
            self.assertFalse(any(kind=='input' for kind,identity in events))

    def test_revoked_commit_releases_transient_callback_contents(self):
        class Marker(str):pass
        for outcome in ('submit','decline','late'):
            native,target,events,state=self.backend();saved=[]
            marker=Marker('synthetic transient callback contents');reference=weakref.ref(marker)
            current=lambda held=marker:bool(held)
            authorize=lambda transaction,held=marker:outcome!='decline' and bool(held)
            def commit(transaction,fast):
                saved.append(fast)
                if outcome!='late':fast()
            try:native.commit_paste(7,target,current,authorize,object(),commit=commit)
            except ClipboardFailure:pass
            del current,authorize,marker
            self.assertIsNone(reference(),outcome)
            with self.assertRaises(ClipboardFailure):saved[0]()

    def test_service_restores_own_transaction_when_commit_is_declined(self):
        from test_windows_clipboard import FakeClipboard
        backend=FakeClipboard();service=ClipboardService(backend=backend)
        service.approve_target_class('Edit',.02);original=dict(backend.data)
        result=service.deliver('synthetic',backend.target,lambda:True,commit=lambda transaction,fast:None)
        self.assertEqual(result.status,'commit_rejected')
        self.assertFalse(result.submitted);self.assertEqual(backend.pastes,0)
        self.assertEqual(backend.data,original)

    def test_service_uses_fast_native_precheck_then_one_full_commit_probe(self):
        from test_windows_clipboard import FakeClipboard
        backend=FakeClipboard();service=ClipboardService(backend=backend)
        service.approve_target_class('Edit',.02)
        backend.capture_native_target=lambda:backend.target
        backend.capture_target=lambda **kwargs:(_ for _ in ()).throw(AssertionError('no pre-stage UIA probe'))
        result=service.deliver('synthetic',backend.target,lambda:True,commit=lambda transaction,fast:fast())
        self.assertEqual(result.status,'submitted');self.assertTrue(result.restored)

    def backend(self):
        native=NativeClipboard.__new__(NativeClipboard)
        native.hwnd=10;native.tx_format=900;native._token=b'owned'
        native.user=NS(GetClipboardOwner=lambda:10,GetClipboardData=lambda identity:1)
        native.kernel=NS(GlobalSize=lambda handle:5)
        native.sequence=lambda:7;native._read_handle=lambda *args:b'owned'
        target=replace(BASE,uia=UiaTargetIdentity((1,),(2,),(1,),9,0,(1,),-1))
        events=[];state={'held':False,'native':BASE}
        @contextmanager
        def opened():
            state['held']=True;events.append(('open',threading.get_ident()))
            try:yield
            finally:state['held']=False;events.append(('close',threading.get_ident()))
        native._opened=opened
        state['uia']=target
        native.capture_target=lambda **kwargs:state['uia']
        class Lease:
            def __init__(self):
                events.append(('uia',threading.get_ident()))
                self.result=TargetResult('target_captured',native.capture_target().uia)
            def confirm(self):
                events.append(('confirm',threading.get_ident()))
                return TargetResult('target_captured',native.capture_target().uia)
            def close(self):events.append(('lease_close',threading.get_ident()))
        native._selection_probe=NS(begin_delivery=lambda basis,cancelled:Lease())
        native.capture_native_target=lambda:state['native']
        native.modifiers_down=lambda:False
        def chord(key):
            assert state['held'];events.append(('input',threading.get_ident()))
        native._chord=chord
        return native,target,events,state

    def test_only_fast_closure_runs_on_input_owner_while_worker_holds_clipboard(self):
        native,target,events,state=self.backend();mailbox=queue.Queue();done=threading.Event();errors=[]
        owner=threading.get_ident()
        def commit(transaction,fast):
            mailbox.put(fast)
            if not done.wait(1):raise AssertionError('test owner did not respond')
        def worker():
            try:native.commit_paste(7,target,lambda:True,lambda transaction:True,object(),commit=commit)
            except BaseException as error:errors.append(error)
        thread=threading.Thread(target=worker);thread.start()
        try:mailbox.get(timeout=1)()
        finally:done.set();thread.join(1)
        self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
        self.assertEqual([identity for kind,identity in events if kind=='input'],[owner])
        self.assertTrue(all(identity!=owner for kind,identity in events if kind in ('uia','open','close')))

    def test_late_duplicate_rejected_and_cancelled_closures_never_submit(self):
        for kind in ('late','duplicate','native','cancel','reject'):
            native,target,events,state=self.backend();saved=[];current={'value':True}
            def commit(transaction,fast):
                saved.append(fast)
                if kind=='late':return
                if kind=='native':state['native']=replace(BASE,focus=101)
                if kind=='cancel':current['value']=False
                fast()
                if kind=='duplicate':fast()
            with self.assertRaises(ClipboardFailure):
                native.commit_paste(7,target,lambda:current['value'],lambda transaction:kind!='reject',object(),commit=commit)
            with self.assertRaises(ClipboardFailure):saved[0]()
            self.assertFalse(state['held'])
            self.assertEqual(sum(kind=='input' for kind,identity in events),1 if kind=='duplicate' else 0)


class LeaseProcess(FakeProcess):
    def __init__(self,identity,*,blocked=False,kill_fails=False):
        super().__init__(b'',kill_fails=kill_fails)
        self.identity=identity;self.initial_identity=identity
        self.command=threading.Event();self.confirm_release=threading.Event()
        if not blocked:self.confirm_release.set()
        self.responded=threading.Event();owner=self
        class Input:
            def write(self,data):
                if bytes(data)==b'\x01':owner.command.set()
                return len(data)
            def close(self):pass
        class Output:
            def __init__(self):
                self.stream=io.BytesIO(encode_target_response(TargetResult('target_captured',identity)));self.second=False
            def read(self,count):
                data=self.stream.read(count)
                if data:return data
                if self.second:return b''
                owner.command.wait(2);owner.confirm_release.wait(2)
                self.second=True
                if owner.killed:return b''
                self.stream=io.BytesIO(encode_target_response(TargetResult('target_captured',owner.identity)))
                owner.responded.set();return self.stream.read(count)
        self.stdin=Input();self.stdout=Output()
    def poll(self):return 0 if self.killed or self.responded.is_set() else None
    def kill(self):
        if self.kill_fails:raise OSError('synthetic owned kill failure')
        self.killed=True;self.command.set();self.confirm_release.set()


class DeliveryLeaseContracts(unittest.TestCase):
    ID=UiaTargetIdentity((1,),(2,),(1,),9,7,(1,),-1)
    def test_confirm_waits_for_writer_close_and_response_within_same_deadline(self):
        for kind in ('success','close_failure','timeout'):
            process=LeaseProcess(self.ID);eof=threading.Event();close_return=threading.Event()
            done=threading.Event();results=[]
            def close():
                eof.set()
                if not close_return.wait(1):raise OSError('synthetic blocked close')
                if kind=='close_failure':raise OSError('synthetic close failure')
            process.stdin.close=close
            output=process.stdout
            class Output:
                def read(self,count):
                    data=output.read(count)
                    if process.responded.is_set() and not eof.wait(1):raise OSError('missing EOF')
                    return data
            process.stdout=Output();probe=SelectionProbe(spawn=lambda *_,**__:process)
            lease=probe.begin_delivery(BASE,lambda:False)
            def confirm():
                results.append(lease.confirm());done.set()
            caller=threading.Thread(target=confirm);caller.start()
            try:
                self.assertTrue(eof.wait(.1));self.assertTrue(lease._confirmed.wait(.1))
                if kind!='timeout':
                    self.assertFalse(done.wait(.002),'response alone cannot finish confirmation')
                    close_return.set()
                self.assertTrue(done.wait(.1))
                self.assertEqual(results[0].status,{'success':'target_captured',
                    'close_failure':'target_probe_failed','timeout':'target_probe_timeout'}[kind])
            finally:
                close_return.set();caller.join(1)
                try:lease.close()
                except ClipboardFailure:
                    if kind!='close_failure':raise
            self.assertTrue(process.closed);self.assertIsNone(probe._process)

    def test_cleanup_failure_keeps_target_status_and_owned_retry(self):
        process=LeaseProcess(self.ID);close=process.close
        process.close=lambda:(_ for _ in ()).throw(ClipboardFailure('selection_cleanup_failed'))
        probe=SelectionProbe(spawn=lambda *_,**__:process)
        lease=probe.begin_delivery(BASE,lambda:False)
        self.assertEqual(lease.confirm().status,'target_captured')
        with self.assertRaises(ClipboardFailure) as failure:lease.close()
        self.assertEqual(failure.exception.status,'target_cleanup_failed')
        self.assertIs(probe._process,process);self.assertIs(probe._delivery,lease)
        process.close=close;probe.close()
        self.assertTrue(process.closed);self.assertIsNone(probe._process)

    def test_confirmation_never_succeeds_before_clean_family_exit(self):
        for kind in ('nonzero','trailing','stderr'):
            process=LeaseProcess(self.ID)
            if kind=='nonzero':process.wait=lambda timeout:1
            if kind=='stderr':process.stderr=io.BytesIO(b'synthetic provider error')
            if kind=='trailing':
                stream=process.stdout
                class Trailing:
                    def read(self,count):
                        chunk=stream.read(count)
                        return chunk or b'x'
                process.stdout=Trailing()
            probe=SelectionProbe(spawn=lambda *_,**__:process)
            lease=probe.begin_delivery(BASE,lambda:False)
            self.assertEqual(lease.confirm().status,'target_probe_failed')
            with self.assertRaises(ClipboardFailure):lease.close()
            self.assertTrue(process.closed);self.assertIsNone(probe._process)

    def test_exactly_one_confirmation_must_match_initial_identity(self):
        for change in ('same','position','edit'):
            process=LeaseProcess(self.ID);probe=SelectionProbe(spawn=lambda *_,**__:process)
            lease=probe.begin_delivery(BASE,lambda:False)
            try:
                self.assertEqual(lease.result.identity,self.ID)
                if change=='position':process.identity=replace(self.ID,position=8)
                if change=='edit':process.identity=replace(self.ID,focus_id=(99,),element_id=(99,))
                self.assertEqual(lease.confirm().status,'target_captured' if change=='same' else 'target_changed')
                self.assertEqual(lease.confirm().status,'commit_rejected')
            finally:lease.close()
            self.assertTrue(process.closed);self.assertIsNone(probe._process)

    def test_owner_confirmation_timeout_is_short_and_worker_retains_failed_cleanup(self):
        import time
        process=LeaseProcess(self.ID,blocked=True,kill_fails=True)
        probe=SelectionProbe(spawn=lambda *_,**__:process,cleanup_timeout=.02)
        lease=probe.begin_delivery(BASE,lambda:False)
        start=time.monotonic()
        self.assertEqual(lease.confirm().status,'target_probe_timeout')
        self.assertLess(time.monotonic()-start,.10)
        with self.assertRaises(ClipboardFailure):lease.close()
        self.assertIs(probe._process,process);self.assertFalse(process.closed)
        self.assertEqual(probe.capture_target(BASE,lambda:False).status,'target_cleanup_pending')
        process.kill_fails=False;probe.close()
        self.assertTrue(process.closed);self.assertIsNone(probe._delivery)

    def test_cancel_before_confirmation_and_revocation_emit_no_request(self):
        process=LeaseProcess(self.ID);probe=SelectionProbe(spawn=lambda *_,**__:process)
        state={'cancelled':False};lease=probe.begin_delivery(BASE,lambda:state['cancelled'])
        state['cancelled']=True
        self.assertEqual(lease.confirm().status,'cancelled')
        self.assertFalse(process.command.is_set())
        lease.close()
        self.assertEqual(lease.confirm().status,'commit_rejected')
        self.assertTrue(process.closed)


if __name__=='__main__':unittest.main()
