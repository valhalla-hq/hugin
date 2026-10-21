"""Deterministic engine/transport simulations; no GPU or native audio claim."""
import io
import threading
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from hugin.audio import PCMOutput
from hugin.protocol import Identity, read_frame
from hugin.workers.server import WorkerServer
from test_audio import FIFO


class StreamContracts(unittest.TestCase):
    def test_completed_provider_can_wait_for_paused_credit_beyond_ready_timeout(self):
        server,identity=self.server()
        server.settings.limits['ready_seconds']=.02
        waiting=threading.Event();release=threading.Event();result=[]
        class Engine:
            def synthesize(self,*args):yield b'\0\0'
        def credit(abort=None):
            waiting.set();return release.wait(1)
        server._wait_credit=credit
        owner=threading.Thread(target=lambda:result.append(server._operate(Engine(),self.command(),identity)))
        owner.start()
        try:
            self.assertTrue(waiting.wait(1));time.sleep(.08)
            self.assertTrue(owner.is_alive(),'paused credit is not failed initialization')
            self.assertEqual(result,[])
        finally:
            release.set();owner.join(1)
        self.assertEqual(result,[(None,2,True)])

    def server(self, output=None):
        settings = SimpleNamespace(limits=dict(frame_bytes=65536,
            audio_buffer_ms=250, control_bytes=65536, ready_seconds=2,
            cancel_seconds=1, exit_seconds=1), voices={'freya':None,'tyr':None})
        identity = Identity(str(uuid.uuid4()), str(uuid.uuid4()), 1)
        server = WorkerServer(settings, 'tts', identity.engine_instance,
            io.BytesIO(), io.BytesIO(), io.BytesIO(), output or io.BytesIO(), None)
        server.active = identity
        return server, identity

    def command(self, voice='freya'):
        return dict(type='synthesize', text='Synthetic stream fixture.',
                    voice=voice, language='German')

    def test_next_provider_chunk_can_compute_while_first_writer_waits_for_credit(self):
        server, identity = self.server()
        second_started = threading.Event()
        owner = threading.get_ident()
        owners = []
        class Engine:
            def synthesize(self, text, voice, language, cancelled):
                owners.append(threading.get_ident())
                yield b'\1\0' * 16000
                second_started.set()
                owners.append(threading.get_ident())
                yield b'\2\0' * 16000
        def credit(abort=None):
            if not second_started.wait(.5):
                raise RuntimeError('next generation is blocked behind playback credit')
            return True
        server._wait_credit = credit
        code, length, terminal_safe = server._operate(Engine(), self.command(), identity)
        self.assertIsNone(code, 'playback credit must not stall the next generation')
        self.assertTrue(terminal_safe)
        self.assertEqual(length, 64000)
        self.assertEqual(owners, [owner, owner], 'GPU generation keeps its existing owner')

    def test_provider_failure_releases_writer_waiting_for_credit(self):
        server, identity = self.server()
        server.settings.limits['ready_seconds'] = .03
        closed = threading.Event()
        class Engine:
            def synthesize(self, text, voice, language, cancelled):
                try:
                    yield b'\1\0' * 16000
                    raise RuntimeError('synthetic provider failure')
                finally:
                    closed.set()
        try:
            code, length, terminal_safe = server._operate(Engine(), self.command(), identity)
            self.assertEqual(code, 'worker_failed')
            self.assertEqual(length, 0)
            self.assertTrue(closed.is_set())
            self.assertIsNone(server._audio_writer, 'failed producer must wake the credit wait')
            self.assertTrue(terminal_safe)
        finally:
            with server.condition:
                server.cancelled = True
                server.condition.notify_all()
            if server._audio_writer is not None:
                server._audio_writer.join(1)

    def test_delayed_provider_and_credit_fifo_preserve_both_voices_without_gaps(self):
        """Cooperative logical clocks model compute parallel to credited output.

        Each 667ms provider chunk needs 250/350ms of serial computation. The
        writer yields scheduling to the producer at each chunk boundary;
        future PCM cannot be played before that chunk's logical ready time.
        No wall-clock scheduling or native devices determine the assertion.
        """
        for voice in ('freya', 'tyr'):
            for compute_ms in (250, 350):
                with self.subTest(voice=voice, compute_ms=compute_ms):
                    clock = [0]
                    device = FIFO(24000, clock)
                    output = PCMOutput(buffer_ms=125, factory=lambda rate:device)
                    output.start(voice)
                    chunks = [bytes([index, 0])*16000 for index in range(1, 7)]
                    generated = [threading.Event() for _ in range(7)]
                    ready = [0]*7
                    class Engine:
                        def synthesize(self, text, selected, language, cancelled):
                            compute_tail = 0
                            for index, pcm in enumerate(chunks, 1):
                                compute_tail = max(clock[0], compute_tail)+compute_ms*24
                                ready[index] = compute_tail
                                generated[index].set()
                                yield pcm
                    class Pipe:
                        def __init__(self):
                            self.buffer = io.BytesIO()
                            self.pending = None
                            self.seen = set()
                            self.frames = 0
                        def write(self, data):return self.buffer.write(data)
                        def flush(self):
                            assert self.pending is None
                            frame = read_frame(io.BytesIO(self.buffer.getvalue()))
                            self.buffer = io.BytesIO()
                            index = frame.data[0]
                            if index not in self.seen:
                                if index < len(chunks):
                                    assert generated[index+1].wait(.5), 'compute must progress while transport is busy'
                                clock[0] = max(clock[0], ready[index])
                                self.seen.add(index)
                            self.pending = frame
                            self.frames += 1
                        def accept(self):
                            if self.pending is not None:
                                frame, self.pending = self.pending, None
                                assert output.write(frame.data, voice)
                    pipe = Pipe()
                    server, identity = self.server(pipe)
                    def credit(abort=None):pipe.accept();return True
                    server._wait_credit = credit
                    def advance(seconds):clock[0] += round(seconds*24000)
                    try:
                        with patch('hugin.audio.time.sleep', advance):
                            code, length, safe = server._operate(Engine(), self.command(voice), identity)
                            pipe.accept()
                            self.assertTrue(output.drain(voice))
                        self.assertIsNone(code)
                        self.assertTrue(safe)
                        self.assertEqual(length, 192000)
                        self.assertEqual(pipe.frames, 36)
                        self.assertEqual(b''.join(device.writes), b''.join(chunks))
                        self.assertLessEqual(device.peak, 6000)
                        self.assertEqual(device.gaps, [])
                    finally:output.close()

    def test_cancel_wakes_full_lookahead_and_keeps_exactly_three_provider_chunks(self):
        server, identity = self.server()
        third = threading.Event()
        closed = threading.Event()
        produced = []
        class Engine:
            def synthesize(self, text, voice, language, cancelled):
                try:
                    for index in range(10):
                        produced.append(index)
                        if index == 2:third.set()
                        yield bytes([index, 0])*720000
                finally:closed.set()
        result = []
        operation = threading.Thread(target=lambda:result.append(server._operate(Engine(), self.command(), identity)))
        operation.start()
        try:
            self.assertTrue(third.wait(1))
            self.assertEqual(produced, [0, 1, 2])
            with server.condition:
                server.cancelled = True
                server.condition.notify_all()
            operation.join(1)
            self.assertFalse(operation.is_alive())
            self.assertTrue(closed.is_set())
            self.assertIsNone(server._audio_writer)
            self.assertEqual(result, [(None, 0, True)])
        finally:
            with server.condition:
                server.cancelled = True
                server.condition.notify_all()
            operation.join(1)

    def test_writer_failure_wakes_blocked_producer_and_requires_family_exit(self):
        third = threading.Event()
        closed = threading.Event()
        class BrokenPipe:
            def write(self, data):
                assert third.wait(1)
                raise OSError('synthetic pipe failure')
        server, identity = self.server(BrokenPipe())
        server.credit = True
        class Engine:
            def synthesize(self, text, voice, language, cancelled):
                try:
                    for index in range(10):
                        if index == 2:third.set()
                        yield b'\0\0'*16000
                finally:closed.set()
        code, length, safe = server._operate(Engine(), self.command(), identity)
        self.assertEqual((code, length, safe), ('worker_failed', 0, False))
        self.assertTrue(closed.is_set())
        self.assertIsNone(server._audio_writer)

    def test_writer_construction_and_start_failure_close_generator_on_owner(self):
        for failure in ('construct', 'start'):
            with self.subTest(failure=failure):
                server, identity = self.server()
                closed = []
                owner = threading.get_ident()
                class Stream:
                    def close(self):closed.append(threading.get_ident())
                class Engine:
                    def synthesize(self, *args):return Stream()
                class FailedThread:
                    def __init__(self, **kwargs):
                        if failure == 'construct':raise RuntimeError('synthetic constructor failure')
                    def start(self):raise RuntimeError('synthetic start failure')
                with patch('hugin.workers.server.threading.Thread', FailedThread):
                    result = server._operate(Engine(), self.command(), identity)
                self.assertEqual(result, ('worker_failed', 0, True))
                self.assertEqual(closed, [owner])
                self.assertIsNone(server._audio_writer)

    def test_terminal_waits_for_generator_close_writer_exit_and_gpu_sync(self):
        close_entered, close_release, closed = (threading.Event() for _ in range(3))
        write_entered, write_release = threading.Event(), threading.Event()
        class Pipe(io.BytesIO):
            def write(self, data):
                write_entered.set()
                if not write_release.wait(2):raise OSError('synthetic held write')
                return super().write(data)
        server, identity = self.server(Pipe())
        server._wait_credit = lambda abort=None:True
        events, synchronized = [], []
        class Engine:
            device = 'cuda'  # Simulation only; no provider is imported.
            def synthesize(self, *args):
                try:yield b'\1\0'*16000
                finally:
                    close_entered.set()
                    if not close_release.wait(2):raise RuntimeError('synthetic held close')
                    closed.set()
            def synchronize(self):
                if synchronized:
                    assert closed.is_set()
                    assert server._audio_writer is None
                synchronized.append(threading.get_ident())
        initialization = Identity(identity.engine_instance, str(uuid.uuid4()), 0)
        server._read_command = lambda:(dict(type='initialize', device='cuda'), initialization)
        server._read_commands = lambda:server.commands.put((self.command(), identity))
        server.factory = lambda settings, device:Engine()
        def send(kind, current, **facts):
            events.append((kind, current, facts))
            if kind == 'terminal' and current == identity:server.stopping = True
        server.send = send
        operation = threading.Thread(target=server.run)
        operation.start()
        try:
            self.assertTrue(close_entered.wait(1))
            self.assertTrue(write_entered.wait(1))
            self.assertEqual(len(synchronized), 1)
            self.assertFalse(any(kind == 'terminal' and current == identity for kind,current,_ in events))
            close_release.set()
            self.assertTrue(closed.wait(1))
            self.assertEqual(len(synchronized), 1, 'GPU completion cannot overtake a held writer')
        finally:
            close_release.set();write_release.set();operation.join(2)
        self.assertFalse(operation.is_alive())
        self.assertEqual(len(synchronized), 2)
        terminals = [facts for kind,current,facts in events if kind == 'terminal' and current == identity]
        self.assertEqual(len(terminals), 1)
        self.assertEqual(terminals[0]['audio_bytes'], 32000)
        self.assertIsNone(terminals[0]['code'])

    def test_failed_generator_close_or_gpu_sync_never_publishes_terminal(self):
        for failure in ('close', 'sync'):
            with self.subTest(failure=failure):
                server, identity = self.server()
                server._wait_credit = lambda abort=None:True
                events, synchronized = [], []
                class Stream:
                    def __iter__(self):return iter((b'\1\0'*160,))
                    def close(self):
                        if failure == 'close':raise RuntimeError('synthetic close failure')
                class Engine:
                    device = 'cpu'
                    def synthesize(self, *args):return Stream()
                    def synchronize(self):
                        synchronized.append(True)
                        if len(synchronized) == 2:raise RuntimeError('synthetic synchronization failure')
                initialization = Identity(identity.engine_instance, str(uuid.uuid4()), 0)
                server._read_command = lambda:(dict(type='initialize', device='cpu'), initialization)
                server._read_commands = lambda:server.commands.put((self.command(), identity))
                server.factory = lambda settings, device:Engine()
                server.send = lambda kind,current,**facts:events.append((kind,current,facts))
                server.run()
                self.assertFalse(any(kind == 'terminal' and current == identity for kind,current,_ in events))
                self.assertTrue(any(kind == 'fault' and current == identity for kind,current,_ in events))
                self.assertEqual(len(synchronized), 1 if failure == 'close' else 2)
                self.assertIsNone(server._audio_writer)

    def test_cancel_cannot_claim_cleanup_while_pipe_writer_is_still_owned(self):
        entered, release, closed = (threading.Event() for _ in range(3))
        class HeldPipe(io.BytesIO):
            def write(self, data):
                entered.set()
                if not release.wait(2):raise OSError('synthetic held pipe')
                return super().write(data)
        server, identity = self.server(HeldPipe())
        server.settings.limits['cancel_seconds'] = .03
        server.credit = True
        class Engine:
            def synthesize(self, *args):
                try:
                    for _ in range(10):yield b'\1\0'*16000
                finally:closed.set()
        result = []
        operation = threading.Thread(target=lambda:result.append(server._operate(Engine(), self.command(), identity)))
        operation.start()
        try:
            self.assertTrue(entered.wait(1))
            with server.condition:
                server.cancelled = True
                server.condition.notify_all()
            operation.join(1)
            self.assertFalse(operation.is_alive())
            self.assertTrue(closed.is_set())
            self.assertEqual(result, [('worker_failed', 0, False)])
            self.assertIsNotNone(server._audio_writer)
            self.assertTrue(server._audio_writer.is_alive())
        finally:
            release.set();operation.join(1)
            if server._audio_writer is not None:server._audio_writer.join(1)
        self.assertFalse(server._audio_writer.is_alive())


if __name__ == '__main__':
    unittest.main()
