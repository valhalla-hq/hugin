"""Real native-capture/commit producers with fake Win32 APIs; no actual input."""
from contextlib import contextmanager
import ctypes as ct
from ctypes import wintypes as W
from dataclasses import replace
from types import SimpleNamespace as NS
import unittest

from hugin.windows.clipboard import NativeClipboard, WindowTarget, ClipboardFailure, _GuiThreadInfo


class NativeFocusConsistency(unittest.TestCase):
    def backend(self):
        state=dict(hwnd=100,focus=200,caret=1,after_selection=lambda:None)
        def out(pointer,kind,value):ct.cast(pointer,ct.POINTER(kind)).contents.value=value
        def thread(hwnd,pid):
            out(pid,W.DWORD,3 if hwnd in (100,200) else 5)
            return 4 if hwnd in (100,200) else 6
        def gui(thread_id,pointer):
            info=ct.cast(pointer,ct.POINTER(_GuiThreadInfo)).contents
            info.hwndFocus=state['focus'];info.hwndCaret=state['focus']
            info.rcCaret.left=state['caret'];info.rcCaret.top=2
            info.rcCaret.right=3;info.rcCaret.bottom=4
            return True
        def times(handle,created,*rest):
            ct.cast(created,ct.POINTER(W.FILETIME)).contents.dwLowDateTime=500
            return True
        def name(hwnd,buffer,capacity):buffer.value='Edit';return 4
        def selection(hwnd,message,wparam,lparam,*rest):
            out(wparam,W.DWORD,2);out(lparam,W.DWORD,2)
            state['after_selection']()
            return True
        native=NativeClipboard.__new__(NativeClipboard)
        native.user=NS(GetForegroundWindow=lambda:state['hwnd'],GetWindowThreadProcessId=thread,
            GetGUIThreadInfo=gui,GetClassNameW=name,GetWindowLongPtrW=lambda *a:0,
            IsWindowEnabled=lambda *a:True,SendMessageTimeoutW=selection,
            GetClipboardOwner=lambda:10,GetClipboardData=lambda *a:1)
        native.kernel=NS(OpenProcess=lambda *a:1,GetProcessTimes=times,
            CloseHandle=lambda *a:True,GlobalSize=lambda *a:5)
        native.hwnd=10;native.tx_format=900;native._token=b'owned';native.sequence=lambda:7
        native._read_handle=lambda *a:b'owned';native.modifiers_down=lambda:False
        @contextmanager
        def opened():yield
        native._opened=opened
        sent=[];native._chord=lambda key:sent.append((key,state['hwnd'],state['focus']))
        target=WindowTarget(100,200,3,4,500,'Edit',(200,1,2,3,4),(2,2),True)
        return native,target,state,sent

    def test_stable_native_capture_and_commit_remain_usable(self):
        native,target,state,sent=self.backend()
        self.assertEqual(native.capture_native_target(),target)
        native.commit_paste(7,lambda:True,lambda tx:True,commit=lambda tx,send:send())
        self.assertEqual(sent,[(0x56,100,200)])

    def test_focus_caret_or_foreground_change_during_waiting_capture_rejects_paste(self):
        for change in ({'hwnd':300,'focus':400},{'focus':201},{'caret':9}):
            with self.subTest(change=change):
                native,target,state,sent=self.backend()
                state['after_selection']=lambda:state.update(change)
                with self.assertRaises(ClipboardFailure):
                    native.commit_paste(7,lambda:True,lambda tx:True,
                        commit=lambda tx,send:send())
                self.assertEqual(sent,[])

    def test_focus_change_during_authorization_rejects_paste(self):
        native,target,state,sent=self.backend()
        def authorize(transaction):
            state.update(hwnd=300,focus=400);return True
        with self.assertRaises(ClipboardFailure):
            native.commit_paste(7,lambda:True,authorize,
                commit=lambda tx,send:send())
        self.assertEqual(sent,[])

    def test_switch_while_waiting_for_owner_chooses_new_window(self):
        native,target,state,sent=self.backend()
        def commit(transaction,send):
            state.update(hwnd=300,focus=400)
            send()
        actual=native.commit_paste(7,lambda:True,lambda tx:True,commit=commit)
        self.assertEqual(sent,[(0x56,300,400)])
        self.assertEqual((actual.hwnd,actual.focus),(300,400))
