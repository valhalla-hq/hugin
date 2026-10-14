"""Signal ownership and dispatch guards; no native system or device changes."""
import queue
import threading
import unittest
from unittest.mock import patch

from hugin.errors import HuginError
from hugin.windows.signals import WindowsSignals, SignalMessages, WM_POWERBROADCAST, WM_DEVICECHANGE


class FakeWindow:
    def __init__(self):
        self.closed=True
        self.notify=None
        self.owner=None
        self.messages=queue.Queue()
        self.close_failures=0
        self.open_failure=False
    def open(self,notify):
        self.owner=threading.get_ident()
        self.closed=False
        self.notify=notify
        if self.open_failure:raise HuginError('input_failed','signals_open')
    def dispatch_one(self):
        action=self.messages.get(timeout=2)
        if action is not None:self.notify(action)
        return True
    def wake(self):self.messages.put(None)
    def close(self):
        if threading.get_ident()!=self.owner:raise AssertionError('wrong cleanup thread')
        if self.close_failures:
            self.close_failures-=1
            raise HuginError('input_failed','signals_cleanup')
        self.closed=True
        self.notify=None


class WindowsSignalContracts(unittest.TestCase):
    def test_close_before_start_never_creates_an_owner_later(self):
        backend=FakeWindow();owner=WindowsSignals(lambda action:None,backend=backend)
        owner.close()
        with self.assertRaises(HuginError):owner.start()
        self.assertIsNone(backend.owner)
        self.assertTrue(owner.closed)

    def test_message_mapping_deduplicates_user_resume_after_automatic(self):
        actions=[]
        messages=SignalMessages(actions.append)
        self.assertTrue(messages.handle(WM_POWERBROADCAST,4))
        self.assertTrue(messages.handle(WM_POWERBROADCAST,18))
        self.assertTrue(messages.handle(WM_POWERBROADCAST,7))
        self.assertTrue(messages.handle(WM_POWERBROADCAST,18))
        self.assertTrue(messages.handle(WM_DEVICECHANGE,7))
        self.assertFalse(messages.handle(WM_DEVICECHANGE,0x8001))
        self.assertFalse(messages.handle(WM_POWERBROADCAST,0x8013))
        self.assertEqual(actions,['system_pause','system_resume','system_resume','devices_changed'])

    def test_callbacks_run_off_native_owner_and_close_is_idempotent(self):
        backend=FakeWindow()
        actions=[];delivered=threading.Event()
        def callback(action):actions.append((action,threading.get_ident()));delivered.set()
        owner=WindowsSignals(callback,backend=backend)
        self.assertTrue(owner.closed);self.assertFalse(owner.ready)
        owner.start()
        try:
            self.assertTrue(owner.ready)
            backend.messages.put('system_pause')
            self.assertTrue(delivered.wait(2))
            self.assertNotEqual(actions[0][1],backend.owner)
        finally:owner.close()
        owner.close()
        self.assertTrue(owner.closed);self.assertFalse(owner.ready)
        with self.assertRaises(HuginError):owner.start()

    def test_failed_cleanup_retains_owner_and_can_be_retried(self):
        backend=FakeWindow();backend.close_failures=1
        owner=WindowsSignals(lambda action:None,backend=backend);owner.start()
        with self.assertRaises(HuginError):owner.close()
        self.assertFalse(owner.closed);self.assertFalse(owner.ready)
        self.assertIsNotNone(backend.notify)
        owner.close()
        self.assertTrue(owner.closed)
        self.assertIsNotNone(owner.error,'operational failure is retained separately from cleanup')

    def test_partial_start_failure_retains_cleanup_until_retry(self):
        backend=FakeWindow();backend.open_failure=True;backend.close_failures=1
        owner=WindowsSignals(lambda action:None,backend=backend)
        with self.assertRaises(HuginError):owner.start()
        self.assertFalse(owner.closed)
        owner.close()
        self.assertTrue(owner.closed)

    def test_blocked_callback_does_not_claim_closed_after_native_cleanup(self):
        backend=FakeWindow();entered=threading.Event();release=threading.Event()
        def callback(action):entered.set();release.wait(3)
        owner=WindowsSignals(callback,backend=backend);owner.start()
        backend.messages.put('system_pause');self.assertTrue(entered.wait(2))
        try:
            with self.assertRaises(HuginError):owner.close(timeout=.05)
            self.assertTrue(backend.closed)
            self.assertFalse(owner.closed)
        finally:release.set();owner.close()
        self.assertTrue(owner.closed)

    def test_bounded_queue_overflow_is_visible_and_stale_notifications_are_ignored(self):
        backend=FakeWindow();entered=threading.Event();release=threading.Event();actions=[]
        def callback(action):actions.append(action);entered.set();release.wait(3)
        owner=WindowsSignals(callback,backend=backend,queue_size=1);owner.start()
        backend.messages.put('system_pause');self.assertTrue(entered.wait(2))
        notify=backend.notify
        try:
            notify('devices_changed');notify('system_resume')
            self.assertFalse(owner.ready)
            self.assertEqual(owner.error.code,'resource_limit')
        finally:release.set();owner.close()
        notify('system_pause')
        self.assertEqual(actions,['system_pause'])

    def test_callback_exception_is_sanitized_and_stops_readiness(self):
        backend=FakeWindow();failed=threading.Event()
        def callback(action):failed.set();raise RuntimeError('PRIVATE CONTENT MUST NOT BE RETAINED')
        owner=WindowsSignals(callback,backend=backend);owner.start()
        try:
            backend.messages.put('system_pause');self.assertTrue(failed.wait(2))
            for _ in range(100):
                if owner.error:break
                threading.Event().wait(.001)
            self.assertFalse(owner.ready)
            self.assertNotIn('PRIVATE',str(owner.error))
        finally:owner.close()

    def test_thread_creation_failure_has_no_native_owner_and_can_close(self):
        backend=FakeWindow();owner=WindowsSignals(lambda action:None,backend=backend)
        original=threading.Thread.start
        def start(thread):
            if thread.name=='hugin-signals-window':raise RuntimeError('simulated thread failure')
            return original(thread)
        with patch.object(threading.Thread,'start',start):
            with self.assertRaises(HuginError):owner.start()
        owner.close()
        self.assertTrue(owner.closed)
        self.assertTrue(backend.closed)

    def test_cleanup_return_without_resource_release_is_not_closed(self):
        backend=FakeWindow();owner=WindowsSignals(lambda action:None,backend=backend);owner.start()
        original=backend.close;backend.close=lambda:None
        try:
            with self.assertRaises(HuginError):owner.close()
            self.assertFalse(owner.closed)
        finally:backend.close=original;owner.close()


if __name__=='__main__':unittest.main()
