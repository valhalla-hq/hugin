"""Current focus is selected by the native commit, not a past recording event."""
import ctypes as ct
import json
import gc
import weakref
import unittest

import test_application as app
from hugin.windows.clipboard import ClipboardService,ClipboardFailure,_GuiThreadInfo
from test_windows_clipboard import FakeClipboard
import test_native_focus_consistency as native_cases


class CurrentCursorContracts(unittest.TestCase):
    setUp=app.ApplicationContracts.setUp
    pump=app.ApplicationContracts.pump
    dictation_ready=app.ApplicationContracts.dictation_ready

    def run_switch(self,phase,*,cross_process=False):
        backend=FakeClipboard()
        native,_,state,sent=native_cases.NativeFocusConsistency().backend()
        state['cross_process']=cross_process
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
        backend.commit_paste=native.commit_paste
        service=ClipboardService(backend=backend)
        service.approve_current_focus(.02)
        self.controller.clipboard=service
        self.controller.command('dictation');self.pump()
        if phase=='recording':state.update(hwnd=300,focus=400)
        self.controller.command('dictation');self.pump()
        self.assertEqual(sent,[])
        self.pool.future.set_result({'engine_instance':'actual-stt','device':'cpu'});self.pump()
        if phase=='after_stop':state.update(hwnd=300,focus=400)
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

    def test_switch_after_stop_uses_current_native_focus_without_uia(self):
        self.run_switch('after_stop')

    def test_switch_during_recording_uses_current_native_focus_without_uia(self):
        self.run_switch('recording')

    def test_switch_to_cross_process_webview_after_stop_uses_current_focus(self):
        self.run_switch('after_stop',cross_process=True)


class NativeCommitGuards(unittest.TestCase):
    def backend(self):return native_cases.NativeFocusConsistency().backend()

    def test_clipboard_owner_size_and_token_rechecked_after_native_capture(self):
        for kind in ('owner','size','token'):
            with self.subTest(kind=kind):
                native,_,state,sent=self.backend();capture=native.capture_native_target
                owner=[10];size=[5];token=[b'owned'];authorized=[]
                native.user.GetClipboardOwner=lambda:owner[0]
                native.kernel.GlobalSize=lambda handle:size[0]
                native._read_handle=lambda *args:token[0]
                def changed_capture():
                    target=capture()
                    if kind=='owner':owner[0]=11
                    elif kind=='size':size[0]=6
                    else:token[0]=b'other'
                    return target
                native.capture_native_target=changed_capture
                with self.assertRaises(ClipboardFailure) as failure:
                    native.commit_paste(7,lambda:True,lambda tx:authorized.append(tx) or True)
                self.assertEqual(failure.exception.status,'clipboard_changed')
                self.assertEqual(authorized,[])
                self.assertEqual(sent,[])

    def test_saved_rejected_callback_does_not_retain_transaction_or_application_callbacks(self):
        native,_,state,sent=self.backend();saved=[]
        class Callback:
            def __call__(self,*args):return True
        current=Callback();authorize=Callback();transaction=Callback()
        references=[weakref.ref(item) for item in (current,authorize,transaction)]
        with self.assertRaises(ClipboardFailure):
            native.commit_paste(7,current,authorize,transaction,commit=lambda tx,send:saved.append(send))
        del current,authorize,transaction
        gc.collect()
        self.assertTrue(all(reference() is None for reference in references))
        with self.assertRaises(ClipboardFailure):saved[0]()
        self.assertEqual(sent,[])

    def test_native_password_change_during_timed_out_range_or_authorization_rejects(self):
        for phase in ('timeout','authorize'):
            with self.subTest(phase=phase):
                native,_,state,sent=self.backend();style=[0]
                native.user.GetWindowLongPtrW=lambda *args:style[0]
                if phase=='timeout':
                    def timeout(*args):style[0]=0x20;return False
                    native.user.SendMessageTimeoutW=timeout
                def authorize(transaction):
                    if phase=='authorize':style[0]=0x20
                    return True
                with self.assertRaises(ClipboardFailure) as failure:
                    native.commit_paste(7,lambda:True,authorize)
                self.assertEqual(failure.exception.status,'target_unverifiable')
                self.assertFalse(failure.exception.submitted)
                self.assertEqual(sent,[])

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
