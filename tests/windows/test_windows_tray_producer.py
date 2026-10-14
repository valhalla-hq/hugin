"""Pinned producer ownership facts; no native library or real tray is used."""
import threading
import unittest
from unittest.mock import patch

from hugin.errors import HuginError
from hugin.windows.tray import TrayOwner


class Producer:
    __module__='pystray._win32'
    def __init__(self):
        self._thread=None;self._hwnd=self._menu_hwnd=None;self._running=False
        self._atom=7;self._icon_handle=8;self.title='test';self.icon='image';self.menu=None
        self.visible=False;self.exit=threading.Event();self.ignore_stop=False
        self.stops=self.classes=self.icons=0;self.fail_before_window=False
    def _run(self):
        if self.fail_before_window:raise RuntimeError('PRIVATE producer payload')
        self._hwnd=1;self._menu_hwnd=2;self._running=True
        self._thread=threading.current_thread();self.exit.wait(3)
        self.classes+=1  # Successful _mainloop finally; fields remain set in pystray.
    def _stop(self):
        self.stops+=1
        if not self.ignore_stop:self.exit.set()
    def _release_icon(self):self.icons+=1;self._icon_handle=None
    def _unregister_class(self,atom):
        assert atom==self._atom
        self.classes+=1


class PinnedTrayProducer(unittest.TestCase):
    def setUp(self):
        self.version=patch('hugin.windows.tray.version',return_value='0.19.5')
        self.version.start()
    def tearDown(self):self.version.stop()
    def test_public_stop_false_flag_does_not_prevent_reposting_same_native_owner(self):
        icon=Producer();owner=TrayOwner(icon);owner.start();icon.ignore_stop=True
        try:
            with self.assertRaises(HuginError):owner.close(timeout=.03)
            icon._running=False  # What pystray public stop does even after PostMessage=0.
            self.assertFalse(owner.closed)
        finally:
            icon.ignore_stop=False;owner.close()
        self.assertEqual(icon.stops,2);self.assertEqual(icon.classes,1)
        self.assertIsNone(icon._icon_handle);self.assertTrue(owner.closed)
    def test_unstarted_constructor_class_is_released_once(self):
        icon=Producer();owner=TrayOwner(icon);owner.close();owner.close()
        self.assertEqual((icon.classes,icon.icons),(1,1))
    def test_failure_before_window_can_release_known_constructor_resources(self):
        icon=Producer();icon.fail_before_window=True;owner=TrayOwner(icon)
        with self.assertRaises(HuginError) as raised:owner.start()
        self.assertIs(raised.exception.owner,owner)
        self.assertNotIn('PRIVATE',str(raised.exception))
        owner.close();self.assertTrue(owner.closed);self.assertEqual(icon.classes,1)
    def test_foreign_producer_version_is_not_accepted(self):
        icon=Producer();owner=TrayOwner(icon)
        with patch('hugin.windows.tray.version',return_value='changed'):
            with self.assertRaises(HuginError):owner.start()
        owner.close();self.assertTrue(owner.closed)
    def test_an_existing_runner_is_not_adopted_or_stopped(self):
        icon=Producer();icon._thread=object();icon._running=True;owner=TrayOwner(icon)
        with self.assertRaises(HuginError):owner.start()
        self.assertEqual(icon.stops,0)
        # Only the fixture removes its simulated foreign ownership for teardown.
        icon._thread=None;icon._running=False;owner.close()


if __name__=='__main__':unittest.main()
