import unittest
import io
import subprocess
from types import SimpleNamespace as NS
from contextlib import nullcontext

from hugin.windows.clipboard_formats import raster_plan,decode_proof,ClipboardFormatProbe
from hugin.windows.clipboard_formats_probe import inspect
from hugin.windows.clipboard import ClipboardFailure

NAMES={'PNG':50001,'DataObject':50002,'Ole Private Data':50003,
       'CanUploadToCloudClipboard':50004,'CanIncludeInClipboardHistory':50005,
       'ExcludeClipboardContentFromMonitorProcessing':50006}
IDS=(50002,2,50001,50004,50005,50003,8,17)
OLE=((2,1,-1,16,False),(50001,1,-1,4,False),
     (50004,1,-1,1,False),(50005,1,-1,1,False))

class ScreenshotPolicy(unittest.TestCase):
    def test_observed_ole_image_retains_flat_image_and_original_policy_order(self):
        self.assertEqual(raster_plan(IDS,NAMES,OLE),(50001,50004,50005,8,17))

    def test_unknown_hidden_media_and_incomplete_enumerations_fail(self):
        for descriptors in (OLE+((50007,1,-1,1,False),),OLE[:-1],
                OLE+OLE[:1],(),OLE[:1]+((50001,1,-1,8,False),)+OLE[2:],
                OLE[:1]+((50001,1,0,4,False),)+OLE[2:],
                OLE[:1]+((50001,1,-1,4,True),)+OLE[2:],
                OLE[:1]+((50001,2,-1,4,False),)+OLE[2:]):
            with self.subTest(descriptors=descriptors),self.assertRaises(ValueError):
                raster_plan(IDS,NAMES,descriptors)

    def test_no_global_skip_for_ole_or_bitmap_and_no_unknown_registered_bytes(self):
        for ids in (IDS+(50007,),IDS+(13,),tuple(x for x in IDS if x==50002),
                    tuple(x for x in IDS if x not in (8,17)),IDS+IDS[:1],
                    tuple(x for x in IDS if x!=50001)):
            with self.subTest(ids=ids),self.assertRaises(ValueError):raster_plan(ids,NAMES,OLE)

    def test_native_dib_source_can_supply_derived_bitmap(self):
        descriptors=((8,1,-1,1,False),)+OLE[1:]
        self.assertEqual(raster_plan(IDS,NAMES,descriptors),(50001,50004,50005,8,17))

    def test_proof_protocol_is_small_exact_and_does_not_coerce_unknowns(self):
        raw=b'{"sequence":42,"formats":[50002,2,50001,50004,50005,50003,8,17]}'
        self.assertEqual(decode_proof(raw),(42,IDS))
        for data in (raw+b'x',raw.replace(b'42',b'true'),raw.replace(b'42',b'0'),
                raw.replace(b'42',b'4294967296'),raw.replace(b'[50002',b'[50002,50002'),
                raw.replace(b'"sequence":42',b'"sequence":42,"sequence":42'),
                raw.replace(b'"formats"',b'"extra":null,"formats"'),b'x'*2049):
            with self.subTest(data=data[:100]),self.assertRaises(ValueError):decode_proof(data)

    def test_producer_rejects_sequence_or_set_changes_after_ole_enumeration(self):
        for change in ('same','sequence','formats'):
            state=NS(seq=42,ids=IDS)
            backend=NS(_opened=nullcontext,sequence=lambda:state.seq,
                       _format_ids=lambda:state.ids,registered=NAMES)
            def enumerate_ole():
                if change=='sequence':state.seq=43
                if change=='formats':state.ids=IDS[:-1]
                return OLE
            if change=='same':self.assertEqual(inspect(backend,enumerate_ole),dict(sequence=42,formats=IDS))
            else:
                with self.subTest(change=change),self.assertRaises(RuntimeError):inspect(backend,enumerate_ole)


class Owner:
    def __init__(self,data=b'{"sequence":42,"formats":[2,8,17]}',code=0):
        self.stdout=io.BytesIO(data);self.code=code;self.closed=False
        self.running=False;self.kill_fails=False;self.close_fails=False;self.killed=False
    def wait(self,timeout):
        if self.running:raise subprocess.TimeoutExpired('fixture',timeout)
        return self.code
    def poll(self):return None if self.running else self.code
    def kill(self):
        if self.kill_fails:raise OSError('synthetic failure')
        self.killed=True;self.running=False
    def close(self):
        if self.close_fails:raise OSError('synthetic failure')
        self.closed=True


class ProbeOwnership(unittest.TestCase):
    def test_owned_success_and_malformed_payloads_are_closed(self):
        for data,code,status in ((b'{"sequence":42,"formats":[2,8,17]}',0,None),
                (b'{}',0,'clipboard_failed'),(b'x'*2049,0,'clipboard_failed'),
                (b'',3,'format_unsupported'),(b'',2,'clipboard_failed')):
            owner=Owner(data,code);options=[]
            probe=ClipboardFormatProbe(spawn=lambda *args,**kwargs:options.append(kwargs) or owner)
            if status:
                with self.subTest(status=status),self.assertRaises(ClipboardFailure) as failure:probe.read()
                self.assertEqual(failure.exception.status,status)
            else:self.assertEqual(probe.read(),(42,(2,8,17)))
            self.assertTrue(owner.closed);self.assertIsNone(probe._process)
            self.assertEqual(options[0]['memory_limit'],256*1024*1024)

    def test_timeout_kills_only_held_family_and_retains_failed_cleanup(self):
        owner=Owner();owner.running=True;owner.kill_fails=True
        probe=ClipboardFormatProbe(spawn=lambda *args,**kwargs:owner)
        with self.assertRaises(ClipboardFailure) as failure:probe.read()
        self.assertEqual(failure.exception.status,'clipboard_cleanup_failed')
        self.assertIs(probe._process,owner)
        with self.assertRaises(ClipboardFailure):probe.read()
        owner.kill_fails=False;probe.close()
        self.assertTrue(owner.killed and owner.closed);self.assertIsNone(probe._process)
        owner=Owner();owner.running=True
        probe=ClipboardFormatProbe(spawn=lambda *args,**kwargs:owner)
        with self.assertRaises(ClipboardFailure) as failure:probe.read()
        self.assertEqual(failure.exception.status,'clipboard_busy');self.assertTrue(owner.closed)

    def test_partial_creation_owner_is_retained_until_cleanup_retry(self):
        owner=Owner();owner.close_fails=True
        def spawn(*args,**kwargs):
            failure=RuntimeError('synthetic constructor failure');failure.owner=owner;raise failure
        probe=ClipboardFormatProbe(spawn=spawn)
        with self.assertRaises(ClipboardFailure):probe.read()
        self.assertIs(probe._process,owner)
        owner.close_fails=False;probe.close();self.assertTrue(owner.closed)

if __name__=='__main__':unittest.main()
