"""Metadata-only target proofs. No native input, clipboard or provider text."""
from dataclasses import replace
from contextlib import contextmanager
import io
import json
import queue
import struct
import threading
from types import SimpleNamespace as NS
import unittest

from hugin.windows.clipboard import WindowTarget,UiaTargetIdentity,NativeClipboard,ClipboardFailure,ClipboardService
from hugin.windows.selection import (SelectionProbe,TargetResult,encode_request,decode_operation,
    encode_target_response,decode_target_response)
from hugin.windows.selection_probe import read_uia_target
from test_windows_selection import FakeProcess

BASE=WindowTarget(100,100,3,4,500,'Chrome_WidgetWin_1',None,None)


class Range:
    def __init__(self,owner,start,end):self.owner,self.start,self.end=owner,start,end
    def Clone(self):return Range(self.owner,self.start,self.end)
    def CompareEndpoints(self,endpoint,other,other_endpoint):
        left=self.start if endpoint==0 else self.end
        right=other.start if other_endpoint==0 else other.end
        return 19 if left>right else -19 if left<right else 0
    def GetEnclosingElement(self):return self.owner
    def MoveEndpointByUnit(self,endpoint,unit,count):
        assert unit==0
        old=self.start if endpoint==0 else self.end
        new=max(0,min(1_000_000,old+count))
        if endpoint==0:self.start=new;self.end=max(self.end,new)
        else:self.end=new;self.start=min(self.start,new)
        return new-old
    def GetText(self,*args):raise AssertionError('metadata must not read content')
    def Select(self):raise AssertionError('metadata must not change selection')


class Ranges:
    Length=1
    def __init__(self,selected):self.selected=selected
    def GetElement(self,index):return self.selected


class Pattern:
    SupportedTextSelection=1
    def __init__(self,owner):self.owner=owner;self.position=7;self.origin=900;self.width=0;self.after=lambda:None
    def QueryInterface(self,*args):return self
    def GetSelection(self):
        selected=Range(self.owner,self.origin+self.position,self.origin+self.position+self.width)
        self.after();return Ranges(selected)
    @property
    def DocumentRange(self):return Range(self.owner,self.origin,self.origin+100)


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

    def test_collapsed_edit_is_verifiable_without_reading_any_text(self):
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

    def test_unbounded_degraded_or_foreign_range_is_never_a_target_proof(self):
        for change in ('limit','roundtrip','enclosing','outside'):
            automation=Automation()
            if change=='limit':automation.focus.pattern.origin=300000
            elif change=='roundtrip':
                original=Range.MoveEndpointByUnit
                def degrade(selected,endpoint,unit,count):
                    return original(selected,endpoint,unit,count//2 if count>0 else count)
                from unittest.mock import patch
                with patch.object(Range,'MoveEndpointByUnit',degrade):
                    self.assertEqual(self.read(automation).status,'target_unverifiable')
                continue
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
        for field,bad in (('position',True),('focus_pid',0),('focus_id',[True]),('element_id',list(range(65)))):
            value={'focus_id':list(identity.focus_id),'root_id':list(identity.root_id),
                'element_id':list(identity.element_id),'focus_pid':identity.focus_pid,'position':identity.position}
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
        target=replace(BASE,uia=UiaTargetIdentity((1,),(2,),(1,),9,0))
        events=[];state={'held':False,'native':BASE}
        @contextmanager
        def opened():
            state['held']=True;events.append(('open',threading.get_ident()))
            try:yield
            finally:state['held']=False;events.append(('close',threading.get_ident()))
        native._opened=opened
        native.capture_target=lambda **kwargs:events.append(('uia',threading.get_ident())) or target
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


if __name__=='__main__':unittest.main()
