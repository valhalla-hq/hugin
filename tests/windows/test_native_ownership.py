"""Real registrations and handles; no injected or physical key claims."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

from hugin.windows.input import WindowsInputs
from hugin.windows.instance import InstanceGuard
from hugin.windows.process import OwnedProcess


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
    'explicit isolated native ownership probe')
class NativeOwnership(unittest.TestCase):
    def test_pilot_hotkeys_and_temporary_escape_release(self):
        inputs = WindowsInputs(lambda action:None,pilot=True)
        try:
            inputs.start()
            self.assertTrue(inputs.running)
            inputs.set_cancel_active(True)
            inputs.set_cancel_active(False)
            self.assertIsNone(inputs.error)
        finally: inputs.stop()
        self.assertFalse(inputs.running)

    def test_desktop_hook_and_hotkeys_release_before_next_launch(self):
        # No synthetic input: register, release, and reacquire the real owners.
        for pilot in (False, True, False):
            inputs = WindowsInputs(lambda action:None, pilot=pilot)
            try:
                inputs.start()
                self.assertTrue(inputs.running)
                inputs.set_cancel_active(True)
                inputs.set_cancel_active(False)
                self.assertIsNone(inputs.error)
            finally:inputs.stop()
            self.assertTrue(inputs.closed)

    def test_native_second_instance_does_not_claim_mutex(self):
        # Windows mutexes are recursive on their owning thread. A second
        # instance means another process, not two handles on that same thread.
        first,second = InstanceGuard(),None
        try:
            self.assertTrue(first.acquire())
            code = 'import sys;sys.path.insert(0,sys.argv[1]);from hugin.windows.instance import InstanceGuard;g=InstanceGuard();print(g.acquire());g.close()'
            root = Path(__file__).resolve().parents[2]
            second = OwnedProcess([sys.executable,'-c',code,str(root/'src')],
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                cwd=str(root),creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(second.wait(timeout=5),0)
            self.assertEqual(second.stdout.read(16).strip(),b'False')
        finally:
            if second:
                if second.poll() is None: second.kill(); second.wait(timeout=5)
                second.close()
            first.close()


if __name__=='__main__': unittest.main()
