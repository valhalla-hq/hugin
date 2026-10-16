"""Real owned Windows pipes/processes; synthetic UIA, no app/clipboard/UI input."""
from pathlib import Path
import sys
import unittest

from hugin.windows.process import OwnedProcess
from hugin.windows.selection import SelectionProbe
from hugin.windows.clipboard import WindowTarget


ROOT=Path(__file__).resolve().parents[2]
SCRIPT='''
import sys,time,struct
from types import SimpleNamespace
from pathlib import Path
assert Path(sys.prefix).resolve()==Path(EXPECTED_PREFIX).resolve()
sys.path[:0]=[SOURCE,CONTRACTS]
from hugin.windows.selection import read_exact,decode_operation
from hugin.windows.selection_probe import _com_delivery
from test_windows_target import Automation,Uia,BASE
length=struct.unpack('!I',read_exact(sys.stdin.buffer,4))[0]
operation,target=decode_operation(read_exact(sys.stdin.buffer,length))
assert operation=='delivery' and target==BASE
automation=Automation();automation.focus.pattern.width=11
Uia.CUIAutomation=object();Uia.IUIAutomation=object()
class Client:
    def CreateObject(self,*a,**k):return automation
_com_delivery(Client(),Uia,target,SimpleNamespace(capture_native_target=lambda:BASE))
assert sys.stdout.closed and sys.stderr.closed
time.sleep(.12)
'''.replace('SOURCE',repr(str(ROOT/'src'))).replace('CONTRACTS',repr(str(ROOT/'tests/contracts'))).replace('EXPECTED_PREFIX',repr(sys.prefix))


@unittest.skipUnless(sys.platform=='win32','Windows process-family proof')
class DeliveryProcessContracts(unittest.TestCase):
    def test_producer_closes_attestation_channel_before_real_family_unwind(self):
        import time
        processes=[]
        def spawn(command,**options):
            process=OwnedProcess([command[0],'-I','-B','-u','-c',SCRIPT],**options)
            processes.append(process);return process
        probe=SelectionProbe(spawn=spawn)
        target=WindowTarget(100,100,3,4,500,'Chrome_WidgetWin_1',None,None)
        lease=probe.begin_delivery(target,lambda:False)
        try:
            self.assertEqual(lease.result.status,'target_captured')
            began=time.monotonic()
            prepared=lease.prepare()
            self.assertEqual(prepared.status,'target_captured')
            self.assertGreaterEqual(prepared.verified_at,began)
            self.assertLessEqual(prepared.verified_at,time.monotonic())
            self.assertEqual(lease.confirm().status,'target_captured')
            self.assertIsNone(processes[0].poll(),'family must still be held during unwind')
        finally:lease.close();probe.close()
        self.assertIsNone(probe._process)
        self.assertEqual(processes[0].returncode,0)


if __name__=='__main__':unittest.main()
