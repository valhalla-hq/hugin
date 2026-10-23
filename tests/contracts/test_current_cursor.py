"""Current focus is selected by the native commit, not a past recording event."""
from dataclasses import replace
import ctypes as ct
import json
import unittest

import test_application as app
from hugin.windows.clipboard import ClipboardService,ClipboardFailure,_GuiThreadInfo
from test_windows_clipboard import FakeClipboard
from test_native_focus_consistency import NativeFocusConsistency


class CurrentCursorContracts(unittest.TestCase):
    setUp=app.ApplicationContracts.setUp
    pump=app.ApplicationContracts.pump
    dictation_ready=app.ApplicationContracts.dictation_ready

    def test_switch_after_stop_uses_current_native_focus_without_uia(self):
        backend=FakeClipboard()
        native,_,state,sent=NativeFocusConsistency().backend()
        native.sequence=backend.sequence
        native._probe=lambda:self.fail('dictation must not depend on UIA')
        original_gui=native.user.GetGUIThreadInfo
        def gui(thread,pointer):
            result=original_gui(thread,pointer)
            ct.cast(pointer,ct.POINTER(_GuiThreadInfo)).contents.hwndCaret=None
            return result
        native.user.GetGUIThreadInfo=gui
        def name(hwnd,buffer,capacity):
            buffer.value='Chrome_WidgetWin_1';return len(buffer.value)
        native.user.GetClassNameW=name
        initial=backend.target
        last=replace(initial,hwnd=300,focus=400,pid=5,thread=6,control_class='Chrome_WidgetWin_1',
                     native_editable=False,caret=None,selection=None)
        backend.commit_paste=native.commit_paste
        service=ClipboardService(backend=backend)
        service.approve_current_focus(.02)
        self.controller.clipboard=service
        self.dictation_ready()
        state.update(hwnd=300,focus=400)
        request,generation=self.pool.inference[-1]
        self.controller.worker_event(dict(type='result',engine='stt',engine_instance='actual-stt',
            request_id=request,generation=generation,text='current native destination'))
        self.pump()
        self.assertEqual(sent,[(0x56,300,400)])
        self.assertEqual(backend.data[13].decode('utf-16-le'),'current native destination\0')
        self.assertIsNone(self.controller.core.snapshot().error)
        checks=json.loads(self.controller.diagnostic())['input_checks']
        self.assertEqual((checks['capture_native'],checks['capture_field'],checks['delivery']),
                         ('native_target_captured','not_required','submitted'))


class NativeCommitGuards(unittest.TestCase):
    def backend(self):return NativeFocusConsistency().backend()

    def test_missing_focus_keeps_published_text_and_reports_native_failure(self):
        backend=FakeClipboard();native,_,state,sent=self.backend()
        native.sequence=backend.sequence
        native.user.GetForegroundWindow=lambda:0
        backend.commit_paste=native.commit_paste
        service=ClipboardService(backend=backend);service.approve_current_focus(.02)
        result=service.deliver('manual fallback',lambda:True)
        self.assertEqual((result.status,result.capture_status,result.copied,result.submitted),
                         ('target_unverifiable','target_unverifiable',True,False))
        self.assertEqual(sent,[])
        self.assertEqual(backend.data[13].decode('utf-16-le'),'manual fallback\0')

    def test_commit_is_one_shot_and_saved_closure_is_revoked(self):
        for kind in ('no_send','double','reject','cancel','modifier','user_copy'):
            with self.subTest(kind=kind):
                native,_,state,sent=self.backend();saved=[];current=[True]
                def commit(transaction,send):
                    saved.append(send)
                    if kind=='no_send':return
                    if kind=='cancel':current[0]=False
                    if kind=='modifier':native.modifiers_down=lambda:True
                    if kind=='user_copy':native.sequence=lambda:8
                    send()
                    if kind=='double':send()
                with self.assertRaises(ClipboardFailure) as failure:
                    native.commit_paste(7,lambda:current[0],lambda tx:kind!='reject',commit=commit)
                self.assertEqual(len(sent),int(kind=='double'))
                self.assertEqual(failure.exception.submitted,kind=='double')
                with self.assertRaises(ClipboardFailure):saved[0]()
                self.assertEqual(len(sent),int(kind=='double'))

    def test_partial_input_is_reported_without_replay(self):
        native,_,state,sent=self.backend();calls=[]
        def chord(key):
            calls.append(key);raise ClipboardFailure('input_partial',submitted=True)
        native._chord=chord
        with self.assertRaises(ClipboardFailure) as failure:
            native.commit_paste(7,lambda:True,lambda tx:True)
        self.assertTrue(failure.exception.submitted)
        self.assertEqual(failure.exception.capture_status,'native_target_captured')
        self.assertEqual(calls,[0x56])


if __name__=='__main__':unittest.main()
