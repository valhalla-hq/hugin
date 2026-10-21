"""Public worker IPC with a simulated provider; no model/GPU/audio execution."""
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid

from hugin.errors import HuginError
from hugin.word_timing import AlignmentResult, WordTiming
from hugin.workers import WorkerClient

ROOT = Path(__file__).resolve().parents[2]
FAKE = r'''
import argparse, os, sys, time, weakref
from pathlib import Path
from hugin.config import load_settings
from hugin.word_timing import AlignmentResult, WordTiming, lexeme_spans
from hugin.workers.server import WorkerServer
import hugin.workers.server as server_module
class TrackedText(str): pass
references = []
read_control = server_module.read_control
def tracked_control(*args, **kwargs):
    command = read_control(*args, **kwargs)
    if command['type'] == 'align':
        command['text'] = TrackedText(command['text'])
        references.append(weakref.ref(command['text']))
    return command
server_module.read_control = tracked_control
class Engine:
    device = 'cpu'
    pending = False
    def __init__(self, settings, device): pass
    def align(self, pcm, text, language, cancelled):
        if len(pcm) > 1440000:
            return AlignmentResult('unavailable_duration', ())
        if pcm[:2] == b'\x01\x00':
            while not cancelled(): time.sleep(.005)
            return AlignmentResult('unavailable_cancelled', ())
        self.pending = True
        self.fail_sync = text == 'syncfail'
        if text == 'blocked': time.sleep(5)
        if text == 'invalid':
            return AlignmentResult('aligned', (WordTiming(0,7,0,len(pcm)),))
        spans = lexeme_spans(text)
        return AlignmentResult('aligned', tuple(WordTiming(a,b,i*2400,(i+1)*2400)
            for i,(a,b) in enumerate(spans)))
    def synchronize(self):
        if self.pending:
            self.pending = False
            if any(reference() is not None for reference in references):
                raise AssertionError('alignment source retained across terminal')
            if self.fail_sync: raise RuntimeError('synthetic synchronization failure')
            time.sleep(.2)
    def offload(self): pass
p=argparse.ArgumentParser()
p.add_argument('--root',type=Path);p.add_argument('--engine');p.add_argument('--instance')
p.add_argument('--data-input',type=int);p.add_argument('--data-output',type=int)
a=p.parse_args();out=sys.stdout.buffer;sys.stdout=sys.stderr
if os.name == 'nt':
    import msvcrt
    di=msvcrt.open_osfhandle(a.data_input,os.O_RDONLY|os.O_BINARY)
    do=msvcrt.open_osfhandle(a.data_output,os.O_WRONLY|os.O_BINARY)
else:di,do=a.data_input,a.data_output
WorkerServer(load_settings(a.root),a.engine,a.instance,sys.stdin.buffer,out,
    os.fdopen(di,'rb',buffering=0),os.fdopen(do,'wb',buffering=0),Engine).run()
'''


class WorkerAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        script = Path(self.directory.name) / 'alignment_fixture.py'
        script.write_text(FAKE, encoding='utf-8')
        self.events = []
        self.aligned = threading.Event()
        def callback(event):
            self.events.append(event)
            if event['type'] == 'alignment': self.aligned.set()
        self.client = WorkerClient(ROOT, 'stt', callback, spawn=subprocess.Popen,
            command=[sys._base_executable, str(script)])
        self.addCleanup(self.client.close)
        # This child contains synthetic literals only. Capture a bounded fixture
        # traceback for startup diagnosis; real WorkerClient stderr is discarded.
        diagnostic = bytearray()
        def fixture_stderr():
            try:
                while data := self.client.process.stderr.read(4096):
                    diagnostic.extend(data[:max(0,4096-len(diagnostic))])
            except (OSError,ValueError): pass
        self.client._stderr_reader = fixture_stderr
        try:
            self.client.start(device='cpu').result(timeout=5)
        except HuginError:
            self.client.close()
            self.fail('synthetic worker startup: ' + diagnostic.decode('utf-8','replace'))

    def test_typed_original_offsets_arrive_before_synchronized_terminal(self):
        request = str(uuid.uuid4())
        future = self.client.align(b'\0\0' * 24000, 'Grüße Grüße!', request, 4)
        self.assertTrue(self.aligned.wait(3))
        self.assertFalse(future.done(), 'alignment is not GPU completion')
        event = next(e for e in self.events if e['type'] == 'alignment')
        self.assertEqual(event['request_id'], request)
        self.assertEqual(event['result'], AlignmentResult('aligned', (
            WordTiming(0,5,0,2400), WordTiming(6,12,2400,4800))))
        self.assertIsNone(future.result(timeout=3)['code'])

    def test_cancel_drops_alignment_and_cannot_cancel_new_identity(self):
        request = str(uuid.uuid4())
        future = self.client.align(b'\1\0' * 24000, 'Word.', request, 2)
        self.assertFalse(self.client.cancel(str(uuid.uuid4()),2))
        self.assertTrue(self.client.cancel(request,2))
        self.assertTrue(future.result(timeout=3)['cancelled'])
        self.assertFalse(self.aligned.is_set())
        following = self.client.align(b'\0\0' * 24000, 'Next.', str(uuid.uuid4()),3)
        self.assertFalse(self.client.cancel(request,2))
        self.assertIsNone(following.result(timeout=3)['code'])
        self.assertEqual(len([e for e in self.events if e['type']=='alignment']),1)

    def test_invalid_provider_intervals_fail_at_receiving_boundary(self):
        future = self.client.align(b'\0\0' * 24000, 'invalid', str(uuid.uuid4()),1)
        with self.assertRaises(HuginError): future.result(timeout=3)
        self.assertFalse(self.aligned.is_set())

    def test_admission_bounds_and_next_request_after_rejection(self):
        for pcm,text in [(b'\0', 'word'), (b'\0\0' * 1440001,'word'),
                         (b'\0\0', 'w'*601), (b'\0\0','')]:
            with self.assertRaises(HuginError):
                self.client.align(pcm,text,str(uuid.uuid4()),1)
        self.assertIsNone(self.client.align(b'\0\0'*24000,'Word',str(uuid.uuid4()),2)
            .result(timeout=3)['code'])

    def test_synchronization_failure_cannot_publish_success_terminal(self):
        future = self.client.align(b'\0\0'*24000,'syncfail',str(uuid.uuid4()),1)
        with self.assertRaises(HuginError): future.result(timeout=3)
        self.assertFalse(any(e['type']=='terminal' and e.get('generation')==1 for e in self.events))

    def test_technical_rejection_is_typed_successful_operation_without_invented_words(self):
        future=self.client.align(b'\0\0'*744000,'Word.',str(uuid.uuid4()),1)
        self.assertIsNone(future.result(timeout=3)['code'])
        result=next(e['result'] for e in self.events if e['type']=='alignment')
        self.assertEqual(result,AlignmentResult('unavailable_duration',()))

    def test_stuck_alignment_cleanup_reaps_its_process_before_closed(self):
        from dataclasses import replace
        self.client.settings = replace(self.client.settings, limits={
            **self.client.settings.limits,'cancel_seconds':.05,'exit_seconds':1})
        future = self.client.align(b'\0\0'*24000,'blocked',str(uuid.uuid4()),1)
        self.client.close()
        self.assertTrue(self.client.closed)
        self.assertIsNotNone(self.client.process.poll())
        with self.assertRaises(HuginError): future.result(timeout=1)


if __name__ == '__main__': unittest.main()
