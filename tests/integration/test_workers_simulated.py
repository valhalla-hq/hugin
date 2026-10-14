"""Protocol/process simulations only; these do not verify any model provider."""
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
import weakref
from unittest.mock import patch

from hugin.workers import WorkerClient
from hugin.errors import HuginError
from hugin.protocol import read_frame

ROOT = Path(__file__).resolve().parents[2]
FAKE = r'''
import argparse, gc, os, sys, time, threading, weakref
from pathlib import Path
from hugin.config import load_settings
from hugin.workers.server import WorkerServer
import hugin.workers.server as server_module
class TrackedTranscript(str): pass
synthesis_refs = []
original_read_control = server_module.read_control
def tracked_control(*args, **kwargs):
    command = original_read_control(*args, **kwargs)
    if command.get('type') == 'synthesize':
        command['text'] = TrackedTranscript(command['text'])
        synthesis_refs.append(weakref.ref(command['text']))
    return command
server_module.read_control = tracked_control
class SimulatedEngine:
    device = 'cpu'
    def __init__(self, settings, device):
        assert not any(t.name == 'hugin-control-reader' for t in threading.enumerate())
        print('UNIQUE_PRIVATE_EXCEPTION_AND_CONTENT', file=sys.stderr, flush=True)
        self.transcript_ref = None
    def transcribe(self, pcm, cancelled):
        if pcm[:2] == b'\x01\x00':
            for _ in range(100):
                if cancelled(): return ''
                time.sleep(.005)
        text = TrackedTranscript('Grüße. ' * 20000)
        self.transcript_ref = weakref.ref(text)
        return text
    def synthesize(self, text, voice, language, cancelled):
        try:
            count = 1 if text in ('Terminal race','Next chunk') else 100
            frames = 3000 if count == 1 else 6000
            for _ in range(count):
                if cancelled(): break
                yield b'\x00\x00' * frames
        finally:
            time.sleep(.03)  # Simulated generator close barrier.
    def synchronize(self):
        gc.collect()
        if any(reference() is not None for reference in synthesis_refs):
            raise AssertionError('completed synthesis text still referenced in worker')
        time.sleep(.01)
    def offload(self):
        gc.collect()
        if self.transcript_ref is not None and self.transcript_ref() is not None:
            raise AssertionError('completed transcript still referenced in worker')
p=argparse.ArgumentParser()
p.add_argument('--root', type=Path)
p.add_argument('--engine')
p.add_argument('--instance')
p.add_argument('--data-input',type=int)
p.add_argument('--data-output',type=int)
a=p.parse_args()
out=sys.stdout.buffer
sys.stdout=sys.stderr
if os.name == 'nt':
    import msvcrt
    di=msvcrt.open_osfhandle(a.data_input,os.O_RDONLY|os.O_BINARY)
    do=msvcrt.open_osfhandle(a.data_output,os.O_WRONLY|os.O_BINARY)
else: di,do=a.data_input,a.data_output
WorkerServer(load_settings(a.root),a.engine,a.instance,sys.stdin.buffer,out,
    os.fdopen(di,'rb',buffering=0),os.fdopen(do,'wb',buffering=0),SimulatedEngine).run()
'''


class SimulatedWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.script = Path(self.temp.name) / 'simulated.py'
        self.script.write_text(FAKE,encoding='utf-8')
        self.clients = []
        self.events = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        self.temp.cleanup()

    def client(self,engine,callback=None):
        client=WorkerClient(ROOT,engine,callback or self.events.append,
            spawn=subprocess.Popen,command=[sys._base_executable,str(self.script)])
        self.clients.append(client)
        ready=client.start(device='cpu').result(timeout=10)
        self.assertEqual(ready['type'],'ready')
        return client

    def test_large_transcript_atomic_and_stderr_discarded(self):
        client=self.client('stt')
        request=str(uuid.uuid4())
        terminal=client.transcribe(b'\x00\x00'*16000,request,1).result(timeout=10)
        self.assertFalse(terminal['cancelled'])
        results=[e for e in self.events if e['type']=='result']
        self.assertEqual(len(results),1)
        self.assertGreater(len(results[0]['text'].encode()),65536)
        self.assertEqual(results[0]['request_id'],request)
        self.assertNotIn('UNIQUE_PRIVATE_EXCEPTION_AND_CONTENT',repr(self.events))
        self.assertEqual(client.offload().result(timeout=5)['type'],'terminal')

    def test_completed_provider_transcript_is_released_before_next_offload(self):
        client=self.client('stt')
        terminal=client.transcribe(b'\x00\x00'*16000,str(uuid.uuid4()),1).result(timeout=10)
        self.assertIsNone(terminal['code'])
        result=next(event for event in self.events if event['type']=='result')
        self.assertIs(type(result['text']),str,'client result is a separate UTF-8 decode')
        # The simulated provider holds only a weak reference to its str subclass.
        # offload runs after terminal and fails if server idle locals retain it.
        offloaded=client.offload().result(timeout=5)
        self.assertIsNone(offloaded['code'])
        self.assertFalse(any(event['type']=='fault' for event in self.events))

    def test_synthesis_text_is_released_before_terminal(self):
        client=self.client('tts')
        terminal=client.synthesize('Terminal race','freya',str(uuid.uuid4()),1).result(timeout=10)
        self.assertIsNone(terminal['code'])
        self.assertEqual(len([event for event in self.events if event['type']=='audio']),1)
        self.assertFalse(any(event['type']=='fault' for event in self.events))

    def test_processed_text_and_pcm_frames_are_released_before_idle_read(self):
        for engine in ('stt','tts'):
            with self.subTest(engine=engine):
                references=[];next_read=threading.Event();received=0
                expected=len(('Grüße. '*20000).encode()) if engine=='stt' else 6000
                def observed_read(source):
                    nonlocal received
                    if received==expected:next_read.set()
                    frame=read_frame(source)
                    received+=len(frame.data)
                    references.append(weakref.ref(frame))
                    return frame
                with patch('hugin.workers.client.read_frame',observed_read):
                    client=self.client(engine)
                    request=str(uuid.uuid4())
                    future=(client.transcribe(b'\x00\x00'*16000,request,1) if engine=='stt'
                        else client.synthesize('Terminal race','freya',request,1))
                    self.assertIsNone(future.result(timeout=10)['code'])
                    self.assertTrue(next_read.wait(2),'reader must be waiting for its next frame')
                    self.assertTrue(references)
                    self.assertTrue(all(reference() is None for reference in references),
                        'reader retains a completed frame while idle')
                    client.close()

    def test_cancel_during_audio_backpressure_reaches_terminal(self):
        entered, release=threading.Event(),threading.Event()
        def callback(event):
            self.events.append(event)
            if event['type']=='audio':
                entered.set()
                release.wait(timeout=5)
        client=self.client('tts',callback)
        request=str(uuid.uuid4())
        future=client.synthesize('Synthetischer Test.','freya',request,7)
        self.assertTrue(entered.wait(timeout=5))
        started=time.perf_counter()
        self.assertTrue(client.cancel(request,7))
        terminal=future.result(timeout=2)
        self.assertTrue(terminal['cancelled'])
        self.assertLess(time.perf_counter()-started,1)
        self.assertEqual(len([e for e in self.events if e['type']=='audio']),1)
        release.set()

    def test_cancel_does_not_publish_transcript_or_touch_sentinel(self):
        sentinel=subprocess.Popen([sys._base_executable,'-c','import time;time.sleep(8)'])
        try:
            client=self.client('stt')
            request=str(uuid.uuid4())
            future=client.transcribe(b'\x01\x00'*16000,request,3)
            client.cancel(request,3)
            self.assertTrue(future.result(timeout=5)['cancelled'])
            self.assertFalse(any(e['type']=='result' for e in self.events))
            client.close()
            self.assertIsNone(sentinel.poll())
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=5)

    def test_wrong_identity_cannot_cancel_current_job(self):
        client=self.client('stt')
        request=str(uuid.uuid4())
        future=client.transcribe(b'\x01\x00'*16000,request,3)
        self.assertFalse(client.cancel(str(uuid.uuid4()),3))
        self.assertFalse(future.result(timeout=5)['cancelled'])

    def test_success_terminal_waits_for_last_audio_callback_to_return(self):
        entered,release,finished=threading.Event(),threading.Event(),threading.Event()
        def callback(event):
            self.events.append(event)
            if event['type']=='audio':
                entered.set()
                release.wait(timeout=5)
                finished.set()
        client=self.client('tts',callback)
        future=client.synthesize('Terminal race','freya',str(uuid.uuid4()),1)
        try:
            self.assertTrue(entered.wait(timeout=5))
            with self.assertRaises(TimeoutError):
                future.result(timeout=.2)
            self.assertFalse(finished.is_set())
        finally:
            release.set()
        self.assertFalse(future.result(timeout=5)['cancelled'])
        self.assertTrue(finished.is_set())

    def test_next_chunk_cannot_start_until_previous_callback_completed(self):
        entered,release=threading.Event(),threading.Event()
        first,second=str(uuid.uuid4()),str(uuid.uuid4())
        next_futures=[]
        completed=[]
        def callback(event):
            self.events.append(event)
            if event['type']=='audio':
                if event['request_id']==first:
                    entered.set();release.wait(timeout=5)
                completed.append(event['request_id'])
        client=self.client('tts',callback)
        future=client.synthesize('Terminal race','freya',first,4)
        def next_chunk(done):
            next_futures.append(client.synthesize('Next chunk','freya',second,4))
        future.add_done_callback(next_chunk)
        try:
            self.assertTrue(entered.wait(timeout=5))
            with self.assertRaises(TimeoutError):future.result(timeout=.2)
            self.assertEqual(next_futures,[])
        finally:release.set()
        future.result(timeout=5)
        deadline=time.monotonic()+5
        while not next_futures and time.monotonic()<deadline:time.sleep(.005)
        self.assertEqual(len(next_futures),1)
        self.assertFalse(next_futures[0].result(timeout=5)['cancelled'])
        self.assertEqual(completed,[first,second])

    def test_cancelled_callback_does_not_acknowledge_following_request(self):
        entered,release=threading.Event(),threading.Event()
        first,second=str(uuid.uuid4()),str(uuid.uuid4())
        def callback(event):
            self.events.append(event)
            if event['type']=='audio' and event['request_id']==first:
                entered.set();release.wait(timeout=5)
        client=self.client('tts',callback)
        future=client.synthesize('Terminal race','freya',first,2)
        try:
            self.assertTrue(entered.wait(timeout=5))
            client.cancel(first,2)
            self.assertTrue(future.result(timeout=2)['cancelled'])
            following=client.synthesize('Next chunk','tyr',second,3)
        finally:release.set()
        self.assertFalse(following.result(timeout=5)['cancelled'])
        self.assertEqual([e['request_id'] for e in self.events if e['type']=='audio'],[first,second])

    def test_failed_creation_retains_cleanup_owner_and_retryable_close(self):
        class UnfinishedOwner:
            stdin = stdout = stderr = None
            waits = 0
            killed = False
            released = False
            def wait(self, timeout):
                self.waits += 1
                if self.waits < 3:
                    raise subprocess.TimeoutExpired('simulated', timeout)
                return 0
            def kill(self): self.killed = True
            def close(self): self.released = True
        owner = UnfinishedOwner()
        def failed_spawn(*args,**kwargs):
            error = HuginError('worker_failed','process_cleanup')
            error.owner = owner
            raise error
        client = WorkerClient(ROOT,'stt',self.events.append,spawn=failed_spawn)
        with self.assertRaises(HuginError):
            client.start(device='cpu')
        self.assertIs(client.process,owner)
        with self.assertRaises(HuginError):
            client.close()
        self.assertIs(client.process,owner)
        self.assertFalse(owner.released)
        client.close()
        self.assertTrue(owner.released)

    def test_failed_native_kill_does_not_become_closed_on_retry(self):
        class Owner:
            stdin=stdout=stderr=None
            released=False
            alive=True
            kills=0
            def wait(self,timeout):
                if self.alive: raise subprocess.TimeoutExpired('synthetic',timeout)
                return 0
            def kill(self):
                self.kills+=1
                if self.kills==1: raise HuginError('worker_failed','job_terminate')
                self.alive=False
            def close(self): self.released=True
        owner=Owner();client=WorkerClient(ROOT,'stt',lambda event:None)
        client.process=owner
        with self.assertRaises(HuginError): client.close()
        self.assertFalse(client.closed)
        self.assertTrue(owner.alive)
        client.close()
        self.assertTrue(client.closed)
        self.assertFalse(owner.alive)
        self.assertTrue(owner.released)


if __name__=='__main__':
    unittest.main()
