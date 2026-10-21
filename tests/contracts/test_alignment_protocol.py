"""Cancellation/admission/result identity at the public worker boundary."""
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import patch

from hugin.errors import HuginError
from hugin.protocol import write_control, read_frame
from hugin.workers.client import EnginePool, WorkerClient

ROOT = Path(__file__).resolve().parents[2]


class AlignmentProtocolTests(unittest.TestCase):
    def client(self):
        client = WorkerClient(ROOT,'stt',lambda event:self.events.append(event))
        client.ready = True
        self.events = []
        identity, future = client._begin('align',str(uuid.uuid4()),3)
        client.active.update(alignment_text='word',alignment_samples=24000)
        return client,identity,future

    def event(self, client, identity, **changes):
        value = dict(schema_version=1,type='alignment',engine='stt',**identity.fields(),
            status='aligned',words=[dict(start=0,end=4,start_sample=0,end_sample=2400)])
        value.update(changes)
        source = io.BytesIO()
        write_control(source,value);source.seek(0)
        client.process = SimpleNamespace(stdout=source)
        client._read_control_event()

    def test_extra_keys_stale_identity_and_duplicate_result_are_rejected(self):
        for changed in [dict(extra=True),dict(request_id=str(uuid.uuid4())),dict(generation=4)]:
            client,identity,_ = self.client()
            with self.subTest(changed=changed):
                with self.assertRaises(HuginError): self.event(client,identity,**changed)
                self.assertEqual(self.events,[])
        client,identity,_ = self.client()
        self.event(client,identity)
        with self.assertRaises(HuginError): self.event(client,identity)
        self.assertEqual(len(self.events),1)

    def test_cancelled_result_is_validated_but_not_published_and_source_is_released(self):
        client,identity,future = self.client()
        client.active['cancelled'] = True
        self.event(client,identity)
        self.assertEqual(self.events,[])
        self.assertNotIn('alignment_text',client.active)
        self.assertFalse(future.done())

    def test_success_terminal_cannot_replace_missing_alignment_result(self):
        client,identity,_ = self.client()
        source = io.BytesIO()
        write_control(source,dict(schema_version=1,type='terminal',engine='stt',**identity.fields(),
            cancelled=False,code=None,audio_bytes=0,elapsed_seconds=.1))
        source.seek(0);client.process=SimpleNamespace(stdout=source)
        with self.assertRaises(HuginError): client._read_control_event()

    def test_cancel_before_transfer_is_replayed_after_command_admission_and_pcm_drains(self):
        client=WorkerClient(ROOT,'stt',lambda event:None)
        client.ready=True;client.data_out=io.BytesIO()
        sent=[];threads=[]
        client._send=lambda kind,identity,**fields:sent.append(kind)
        class DeferredThread:
            def __init__(self,target,**kwargs): self.target=target;threads.append(self)
            def start(self): pass
            def is_alive(self): return False
        request=str(uuid.uuid4())
        with patch('hugin.workers.client.threading.Thread',DeferredThread):
            future=client.align(b'\0\0'*1000,'word',request,1)
            client.cancel(request,1)
            threads[0].target()
        self.assertEqual(sent,['cancel','align','cancel'])
        client.data_out.seek(0)
        self.assertEqual(len(read_frame(client.data_out).data),2000)
        self.assertFalse(future.done())

    def test_pool_delegates_alignment_only_to_existing_stt_owner(self):
        calls=[]
        pool=EnginePool(ROOT,lambda event:None)
        pool.workers['stt']=SimpleNamespace(align=lambda *args:calls.append(args))
        pool.align(b'\0\0','word','request',2,'English')
        self.assertEqual(calls,[(b'\0\0','word','request',2,'English')])


if __name__ == '__main__': unittest.main()
