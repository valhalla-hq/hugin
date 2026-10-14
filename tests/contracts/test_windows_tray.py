"""Held tray lifecycle; no real tray, input, device, or model activation."""
import threading
import time
from types import SimpleNamespace as NS
import unittest

from hugin.errors import HuginError
from hugin.windows.tray import TrayOwner


class FakeTray:
    def __init__(self):
        self.title='initial';self.icon='image';self.menu='menu';self.visible=False


class FakeBackend:
    def __init__(self, icon):
        self.icon=icon;self.thread=None;self.stops=0;self.releases=0
        self.gate=threading.Event();self.gate.set()
        self.entered=threading.Event();self.native_ready=threading.Event()
        self.exit=threading.Event();self.show_gate=threading.Event();self.show_gate.set()
        self.show_entered=threading.Event();self.ignore_stop=False
        self.fail_release=False;self.fail_before_ready=False
    def validate(self):pass
    def run(self):
        self.thread=threading.current_thread();self.entered.set();self.gate.wait(3)
        if self.fail_before_ready:raise RuntimeError('PRIVATE native failure')
        self.native_ready.set();self.exit.wait(3)
    def ready(self,thread):return self.thread is thread and self.native_ready.is_set()
    can_stop=ready
    def show(self):
        self.show_entered.set();self.show_gate.wait(3);self.icon.visible=True
    def request_stop(self):
        self.stops+=1
        if not self.ignore_stop:self.exit.set()
    def finish(self,*,unstarted,completed):
        if self.fail_release:raise RuntimeError('PRIVATE release failure')
        self.releases+=1;self.icon.visible=False


class TrayContracts(unittest.TestCase):
    def owner(self, **kwargs):
        icon=FakeTray();backend=FakeBackend(icon)
        return TrayOwner(icon,backend=backend,**kwargs),backend
    def test_ready_is_owned_thread_and_close_is_confirmed_and_idempotent(self):
        owner,backend=self.owner();owner.start()
        self.assertTrue(owner.ready);self.assertFalse(owner.closed)
        owner.close();owner.close()
        self.assertTrue(owner.closed);self.assertFalse(owner.ready)
        self.assertFalse(owner._thread.is_alive());self.assertFalse(owner._setup.is_alive())
        self.assertEqual(backend.releases,1)
    def test_post_failure_cannot_report_closed_and_same_owner_retries(self):
        owner,backend=self.owner();owner.start();backend.ignore_stop=True
        with self.assertRaises(HuginError) as raised:owner.close(timeout=.03)
        self.assertIs(raised.exception.owner,owner);self.assertFalse(owner.closed)
        backend.ignore_stop=False;owner.close()
        self.assertEqual(backend.stops,2);self.assertTrue(owner.closed)
    def test_stop_before_ready_never_shows_late_icon(self):
        owner,backend=self.owner(timeout=.03);backend.gate.clear()
        with self.assertRaises(HuginError) as raised:owner.start()
        self.assertIs(raised.exception.owner,owner)
        with self.assertRaises(HuginError):owner.close(timeout=.03)
        self.assertFalse(owner.closed);self.assertFalse(backend.show_entered.is_set())
        backend.gate.set();owner.close()
        self.assertTrue(owner.closed);self.assertFalse(backend.show_entered.is_set())
    def test_close_waits_for_show_before_native_stop(self):
        owner,backend=self.owner(timeout=.03);backend.show_gate.clear()
        with self.assertRaises(HuginError):owner.start()
        self.assertTrue(backend.show_entered.is_set())
        with self.assertRaises(HuginError):owner.close(timeout=.03)
        self.assertEqual(backend.stops,0);self.assertFalse(owner.closed)
        backend.show_gate.set();owner.close();self.assertTrue(owner.closed)
    def test_cleanup_failure_retains_icon_and_is_retryable(self):
        owner,backend=self.owner();owner.start();backend.fail_release=True
        with self.assertRaises(HuginError):owner.close()
        self.assertFalse(owner.closed)
        backend.fail_release=False;owner.close()
        self.assertTrue(owner.closed)
    def test_close_without_start_releases_constructor_owned_resources(self):
        owner,backend=self.owner();owner.close()
        self.assertTrue(owner.closed);self.assertEqual(backend.releases,1)
        with self.assertRaises(HuginError):owner.start()
    def test_known_native_start_failure_is_sanitized_and_owned(self):
        owner,backend=self.owner();backend.fail_before_ready=True
        with self.assertRaises(HuginError) as raised:owner.start()
        self.assertIs(raised.exception.owner,owner)
        self.assertNotIn('PRIVATE',str(raised.exception))
        owner.close();self.assertTrue(owner.closed)
    def test_properties_delegate_to_same_held_icon(self):
        owner,backend=self.owner();owner.title='changed';owner.icon='new';owner.menu='new-menu'
        self.assertEqual((backend.icon.title,backend.icon.icon,backend.icon.menu),('changed','new','new-menu'))
        owner.close()
        with self.assertRaises(HuginError):owner.title='late'
    def test_native_thread_start_failure_still_closes_unstarted_owner(self):
        from unittest.mock import patch
        owner,backend=self.owner()
        with patch.object(threading.Thread,'start',side_effect=RuntimeError('PRIVATE thread failure')):
            with self.assertRaises(HuginError):owner.start()
        owner.close();self.assertTrue(owner.closed)
    def test_concurrent_close_obeys_callers_own_deadline(self):
        owner,backend=self.owner();owner.start();backend.ignore_stop=True
        entered=threading.Event()
        def close():
            entered.set()
            try:owner.close(timeout=.2)
            except HuginError:pass
        thread=threading.Thread(target=close);thread.start();entered.wait(1)
        while backend.stops==0:time.sleep(.001)
        started=time.monotonic()
        with self.assertRaises(HuginError):owner.close(timeout=.03)
        self.assertLess(time.monotonic()-started,.12)
        thread.join(1);backend.ignore_stop=False;owner.close()

    def test_setup_thread_start_failure_retains_native_runner_for_close(self):
        from unittest.mock import patch
        owner,backend=self.owner()
        original=threading.Thread.start
        def start(thread):
            if thread.name=='hugin-tray-setup':raise RuntimeError('PRIVATE setup start')
            return original(thread)
        with patch.object(threading.Thread,'start',start):
            with self.assertRaises(HuginError) as raised:owner.start()
        self.assertIs(raised.exception.owner,owner)
        owner.close();self.assertTrue(owner.closed)


if __name__=='__main__':unittest.main()
