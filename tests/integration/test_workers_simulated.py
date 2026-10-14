"""Protocol/process simulations only; these do not verify any model provider."""
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid

from hugin.workers import WorkerClient
from hugin.errors import HuginError

ROOT = Path(__file__).resolve().parents[2]
FAKE = r'''
import argparse, os, sys, time, threading
from pathlib import Path
from hugin.config import load_settings
from hugin.workers.server import WorkerServer
class SimulatedEngine:
    device = 'cpu'
    def __init__(self, settings, device):
        assert not any(t.name == 'hugin-control-reader' for t in threading.enumerate())
        print('UNIQUE_PRIVATE_EXCEPTION_AND_CONTENT', file=sys.stderr, flush=True)
    def transcribe(self, pcm, cancelled):
        if pcm[:2] == b'\x01\x00':
            for _ in range(100):
                if cancelled(): return ''
                time.sleep(.005)
        return 'Grüße. ' * 20000
    def synthesize(self, text, voice, language, cancelled):
        try:
            for _ in range(100):
                if cancelled(): break
                yield b'\x00\x00' * 6000
        finally:
            time.sleep(.03)  # Simulated generator close barrier.
    def synchronize(self): time.sleep(.01)
    def offload(self): pass
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


if __name__=='__main__':
    unittest.main()
