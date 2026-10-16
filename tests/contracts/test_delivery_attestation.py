"""Public private-IPC seams with synthetic fields; no browser/provider claim."""
import io
import json
import struct
import threading
import time
import unittest

from hugin.windows.clipboard import UiaTargetIdentity, ClipboardFailure
from hugin.windows.selection import SelectionProbe, TargetResult, encode_target_response,decode_target_response
from test_windows_target import BASE, Automation, Uia
from hugin.windows.selection_probe import read_uia_target


IDENTITY=UiaTargetIdentity((1,),(2,),(1,),(1,),9,(7,18),-1,-1)


class AttestationProcess:
    def __init__(self, *, stamp=lambda:time.monotonic(), trailing=False, cleanup_error=False):
        self.command=threading.Event();self.cleanup_release=threading.Event()
        self.cleanup_entered=threading.Event();self.closed=False;self.killed=False
        self.cleanup_error=cleanup_error;self.stderr=io.BytesIO();owner=self
        class Input:
            def write(self,data):
                if bytes(data)==b'\x01':owner.command.set()
                return len(data)
            def close(self):pass
        class Output:
            def __init__(self):
                self.data=io.BytesIO(encode_target_response(TargetResult(
                    'target_captured',IDENTITY,time.monotonic())))
                self.final=False
            def read(self,count):
                value=self.data.read(count)
                if value:return value
                if self.final:return b''
                if not owner.command.wait(1):raise OSError('no confirmation')
                self.final=True
                data=encode_target_response(TargetResult('target_captured',IDENTITY,stamp()))
                self.data=io.BytesIO(data+(b'x' if trailing else b''))
                return self.data.read(count)
        self.stdin=Input();self.stdout=Output()
    def poll(self):return (2 if self.cleanup_error else 0) if self.cleanup_release.is_set() or self.killed else None
    def wait(self,timeout=None):
        self.cleanup_entered.set()
        if not self.cleanup_release.wait(timeout):
            import subprocess
            raise subprocess.TimeoutExpired(['owned-synthetic-probe'],timeout)
        return self.poll()
    def kill(self):self.killed=True;self.cleanup_release.set();self.command.set()
    def close(self):
        if self.poll() is None:raise OSError('owned family remains live')
        self.closed=True


class DeliveryAttestationContracts(unittest.TestCase):
    def lease(self,process):
        probe=SelectionProbe(spawn=lambda *a,**k:process)
        lease=probe.begin_delivery(BASE,lambda:False)
        self.assertEqual(lease.result.status,'target_captured')
        return probe,lease

    def test_slow_family_unwind_is_held_after_fresh_selection_confirmation(self):
        process=AttestationProcess();probe,lease=self.lease(process)
        try:
            self.assertEqual(lease.prepare().status,'target_captured')
            self.assertFalse(process.cleanup_entered.is_set())
            from unittest.mock import patch
            with (patch.object(process,'wait',side_effect=AssertionError('owner process wait')),
                    patch.object(process.stdout,'read',side_effect=AssertionError('owner pipe read'))):
                self.assertEqual(lease.confirm().identity.selection,(7,18))
            self.assertIs(probe._process,process);self.assertFalse(process.closed)
            done=threading.Event();errors=[]
            def close():
                try:lease.close()
                except Exception as error:errors.append(error)
                finally:done.set()
            thread=threading.Thread(target=close);thread.start()
            self.assertTrue(process.cleanup_entered.wait(.5))
            self.assertFalse(done.wait(.08),'family cleanup must remain held')
            process.cleanup_release.set();thread.join(1)
            self.assertEqual(errors,[]);self.assertTrue(process.closed)
            self.assertIsNone(probe._process)
        finally:
            process.cleanup_release.set();lease.close();probe.close()

    def test_stale_or_future_attestation_cannot_authorize_paste(self):
        for offset,status in ((-1,'target_probe_timeout'),(1,'target_probe_failed')):
            process=AttestationProcess(stamp=lambda:time.monotonic()+offset)
            probe,lease=self.lease(process)
            try:
                self.assertEqual(lease.prepare().status,'target_captured')
                self.assertEqual(lease.confirm().status,status)
            finally:process.cleanup_release.set();lease.close();probe.close()

    def test_owner_queue_delay_invalidates_prepared_attestation(self):
        from unittest.mock import patch
        process=AttestationProcess();probe,lease=self.lease(process)
        try:
            result=lease.prepare();self.assertEqual(result.status,'target_captured')
            with patch('hugin.windows.selection.time.monotonic',return_value=result.verified_at+.051):
                self.assertEqual(lease.confirm().status,'target_probe_timeout')
            self.assertEqual(lease.confirm().status,'commit_rejected')
        finally:process.cleanup_release.set();lease.close();probe.close()

    def test_trailing_confirmation_remains_a_protocol_failure(self):
        process=AttestationProcess(trailing=True);probe,lease=self.lease(process)
        try:
            self.assertEqual(lease.prepare().status,'target_probe_failed')
            self.assertNotEqual(lease.confirm().status,'target_captured')
        finally:
            process.cleanup_release.set()
            with self.assertRaises(ClipboardFailure):lease.close()
        self.assertTrue(process.closed)

    def test_late_exit_failure_is_reported_after_closing_owned_resources(self):
        process=AttestationProcess(cleanup_error=True);probe,lease=self.lease(process)
        try:
            lease.prepare();self.assertEqual(lease.confirm().status,'target_captured')
            process.cleanup_release.set()
            with self.assertRaises(ClipboardFailure) as failure:lease.close()
            self.assertEqual(failure.exception.status,'target_cleanup_failed')
            self.assertIsNone(probe._process)
            self.assertTrue(process.closed)
        finally:process.cleanup_error=False;process.cleanup_release.set();lease.close();probe.close()

    def test_multiple_selection_capability_with_one_current_range_is_valid(self):
        automation=Automation();pattern=automation.focus.pattern
        pattern.SupportedTextSelection=2;pattern.width=3
        result=read_uia_target(automation,Uia,BASE,lambda:BASE,lambda:False)
        self.assertEqual(result.status,'target_captured')
        self.assertEqual(result.identity.selection,(7,10))

    def test_multiple_capability_still_rejects_multiple_current_ranges(self):
        from types import SimpleNamespace
        automation=Automation();pattern=automation.focus.pattern
        pattern.SupportedTextSelection=2;pattern.GetSelection=lambda:SimpleNamespace(Length=2)
        self.assertEqual(read_uia_target(automation,Uia,BASE,lambda:BASE,lambda:False).status,'target_unverifiable')

    def test_clock_boundary_rejects_missing_boolean_integer_and_nonfinite_values(self):
        for stamp in (None,True,1,0.0,-1.0,float('nan'),float('inf')):
            with self.subTest(stamp=stamp):
                with self.assertRaises(ValueError):encode_target_response(TargetResult('target_captured',IDENTITY,stamp))
                from dataclasses import asdict
                data=json.dumps(dict(identity=asdict(IDENTITY),verified_at=stamp)).encode('ascii')
                with self.assertRaises(ValueError):
                    decode_target_response(io.BytesIO(struct.pack('!BBI',4,0,len(data))+data))

    def test_prepare_and_commit_each_consume_their_capability_once(self):
        process=AttestationProcess();probe,lease=self.lease(process)
        try:
            self.assertEqual(lease.prepare().status,'target_captured')
            self.assertEqual(lease.prepare().status,'commit_rejected')
            self.assertEqual(lease.confirm().status,'target_captured')
            self.assertEqual(lease.confirm().status,'commit_rejected')
        finally:process.cleanup_release.set();lease.close();probe.close()


if __name__=='__main__':unittest.main()
