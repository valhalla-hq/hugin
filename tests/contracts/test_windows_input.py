import queue
import unittest

from hugin.errors import HuginError
from hugin.windows.input import (WindowsInputs, MousePresses, WM_XBUTTONDOWN,
                                WM_XBUTTONUP, WM_HOTKEY, WM_QUIT, MOD_NOREPEAT)


class FakeInputs:
    def __init__(self, conflict=None):
        self.messages = queue.Queue()
        self.keys = {}
        self.conflict = conflict
        self.mouse = None
        self.closed = False

    def open(self, mouse):
        self.mouse = mouse

    def register(self, identity, modifiers, key):
        if identity == self.conflict:
            raise HuginError('input_conflict', 'registration')
        self.keys[identity] = (modifiers, key)

    def unregister(self, identity):
        self.keys.pop(identity)

    def next_message(self):
        return self.messages.get(timeout=3)

    def post(self, message, value=0):
        self.messages.put((message, value))

    def close(self):
        self.closed = True
        self.keys.clear()


class WindowsInputContracts(unittest.TestCase):
    def test_one_press_accepts_injected_and_rejects_lower_integrity(self):
        actions = []
        presses = MousePresses(actions.append)
        self.assertTrue(presses.handle(WM_XBUTTONDOWN, 2, 1))
        self.assertTrue(presses.handle(WM_XBUTTONDOWN, 2, 1))
        self.assertTrue(presses.handle(WM_XBUTTONUP, 2, 1))
        self.assertTrue(presses.handle(WM_XBUTTONDOWN, 1, 0))
        self.assertFalse(presses.handle(WM_XBUTTONDOWN, 2, 2))
        self.assertFalse(presses.handle(WM_XBUTTONDOWN, 3, 0))
        self.assertEqual(actions, ['dictation', 'read'])

    def test_pilot_has_no_mouse_hook_and_escape_is_dynamic(self):
        backend = FakeInputs()
        inputs = WindowsInputs(lambda _: None, pilot=True, backend=backend)
        inputs.start()
        try:
            self.assertIsNone(backend.mouse)
            self.assertEqual(backend.keys, {
                1: (1 | 2 | MOD_NOREPEAT, ord('D')),
                2: (1 | 2 | MOD_NOREPEAT, ord('V')),
            })
            inputs.set_cancel_active(True)
            self.assertIn(3, backend.keys)
            inputs.set_cancel_active(False)
            self.assertNotIn(3, backend.keys)
        finally:
            inputs.stop()
        self.assertTrue(backend.closed)

    def test_registration_conflict_closes_partial_owner(self):
        backend = FakeInputs(conflict=2)
        inputs = WindowsInputs(lambda _: None, pilot=True, backend=backend)
        with self.assertRaises(HuginError) as failure:
            inputs.start()
        self.assertEqual(failure.exception.code, 'input_conflict')
        self.assertTrue(backend.closed)
        self.assertFalse(inputs.running)

    def test_escape_conflict_is_reported_and_does_not_claim_active(self):
        backend = FakeInputs(conflict=3)
        inputs = WindowsInputs(lambda _: None, pilot=True, backend=backend)
        inputs.start()
        with self.assertRaises(HuginError):
            inputs.set_cancel_active(True)
        with self.assertRaises(HuginError):
            inputs.stop()
        self.assertTrue(backend.closed)
        self.assertTrue(inputs.closed)

    def test_queue_overflow_is_a_visible_failure(self):
        inputs = WindowsInputs(lambda _: None, backend=FakeInputs(), queue_size=1)
        inputs._enqueue('read')
        inputs._enqueue('dictation')
        self.assertEqual(inputs.error.code, 'resource_limit')

    def test_callback_failure_is_not_a_green_loop(self):
        import threading
        done = threading.Event()
        def fail(_):
            done.set()
            raise RuntimeError('PRIVATE CONTENT MUST NOT LEAK')
        backend = FakeInputs()
        inputs = WindowsInputs(fail, pilot=True, backend=backend)
        inputs.start()
        backend.post(WM_HOTKEY, 1)
        self.assertTrue(done.wait(2))
        with self.assertRaises(HuginError):
            inputs.stop()
        self.assertEqual(inputs.error.code, 'input_failed')
        self.assertNotIn('PRIVATE', str(inputs.error))
        self.assertTrue(inputs.closed)


if __name__ == '__main__':
    unittest.main()
