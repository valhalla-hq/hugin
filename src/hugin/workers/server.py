"""Engine-side command owner. Cancel/credit input never waits on data output."""
from __future__ import annotations
import argparse
import hashlib
import logging
import os
from pathlib import Path
import queue
import sys
import threading
import time

from hugin.config import load_settings
from hugin.errors import HuginError
from hugin.protocol import (Identity, Frame, read_control, write_control,
    read_frame, write_frame, invalid, validate_digest)

ZERO = '00000000-0000-0000-0000-000000000000'


class WorkerServer:
    def __init__(self, settings, engine, instance, control_in, control_out,
                 data_in, data_out, factory):
        self.settings, self.engine, self.instance = settings, engine, instance
        self.control_in, self.control_out = control_in, control_out
        self.data_in, self.data_out, self.factory = data_in, data_out, factory
        self.commands = queue.Queue(maxsize=1)
        self.condition = threading.Condition()
        self.output_lock = threading.Lock()
        self.data_lock = threading.Lock()
        self.active = None
        self.cancelled = False
        self.credit = False
        self.stopping = False
        self._audio_writer = None

    def send(self, kind, identity, **fields):
        with self.output_lock:
            write_control(self.control_out, dict(schema_version=1, type=kind,
                engine=self.engine, **identity.fields(), **fields), self.settings.limits['control_bytes'])

    def _read_command(self):
        command = read_control(self.control_in, self.settings.limits['control_bytes'])
        identity = Identity.from_message(command)
        if (type(command.get('schema_version')) is not int or command.get('schema_version') != 1
                or command.get('engine') != self.engine or identity.engine_instance != self.instance):
            raise invalid()
        kind = command.get('type')
        base = {'schema_version','type','engine','engine_instance','request_id','generation'}
        extra = {'initialize': {'device'}, 'transcribe': {'length','sha256'},
                 'synthesize': {'text','voice','language'}, 'cancel': set(),
                 'credit': set(), 'shutdown': set(), 'offload': set()}
        if not isinstance(kind,str) or kind not in extra or set(command) != base | extra[kind]:
            raise invalid()
        return command, identity

    def _queue_command(self):
        # A reader owns a command only until transfer into the bounded queue.
        # Its next blocking read must not retain the previous text dictionary.
        command, identity = self._read_command()
        transferred = False
        try:
            kind = command.get('type')
            with self.condition:
                if kind == 'shutdown':
                    self.stopping = self.cancelled = True
                    self.condition.notify_all()
                    if self.active is None:
                        self.commands.put_nowait((command, identity))
                        transferred = True
                    return False
                if kind in ('cancel','credit'):
                    if identity == self.active:
                        if kind == 'cancel':
                            self.cancelled = True
                        else:
                            if self.credit:
                                raise invalid()
                            self.credit = True
                        self.condition.notify_all()
                else:
                    if self.active is not None:raise invalid()
                    self.active = identity
                    self.cancelled = self.credit = False
                    self.commands.put_nowait((command, identity))
                    transferred = True
            return True
        finally:
            if not transferred:
                command.clear()

    def _read_commands(self):
        try:
            while self._queue_command():
                pass
        except EOFError:
            # The parent vanished; its private job owns the process family.
            os._exit(0)
        except (HuginError, OSError, queue.Full, TypeError, ValueError):
            try:
                self.send('fault', self.active or Identity(self.instance, ZERO, 0),
                          code='protocol_invalid', phase='worker_protocol', retry='restart')
            finally:
                os._exit(2)

    def is_cancelled(self):
        with self.condition:
            return self.cancelled or self.stopping

    def _wait_credit(self, abort=None):
        with self.condition:
            while not self.credit and not self.cancelled and not self.stopping and not (abort and abort.is_set()):
                self.condition.wait()
            if self.cancelled or self.stopping or (abort and abort.is_set()):
                return False
            self.credit = False
            return True

    def _pcm(self, command, identity):
        length = command['length']
        if type(length) is not int or not 0 < length <= self.settings.limits['capture_bytes'] or length % 2:
            raise invalid()
        digest = validate_digest(command['sha256'])
        draft = bytearray()
        # Input keeps draining after cancellation, bounded by the declared capture.
        while len(draft) < length:
            self._append_pcm(draft,length,identity)
        if hashlib.sha256(draft).hexdigest() != digest:
            raise invalid()
        return draft

    def _append_pcm(self,draft,length,identity):
        frame = read_frame(self.data_in)
        if (frame.kind != 'pcm' or frame.identity != identity
                or frame.offset != len(draft) or len(draft) + len(frame.data) > length):
            raise invalid()
        draft.extend(frame.data)  # The frame scope ends before the next read.

    def _write_audio_chunk(self, pcm, identity, packet, outcome):
        # Only this writer owns the framing stream. Its chunk scope ends before
        # the next blocking queue wait, including cancellation and failures.
        for index in range(0, len(pcm), packet):
            if not self._wait_credit(outcome['abort']):
                return
            with self.data_lock:
                part = pcm[index:index+packet]
                write_frame(self.data_out, Frame('pcm', identity,
                    outcome['audio_bytes'], part))
                outcome['audio_bytes'] += len(part)

    def _synthesize(self, backend, text, voice, language, identity):
        """One queued provider chunk; generation stays on the engine owner.

        The writer's current chunk, one queue slot and one produced chunk
        waiting for that slot retain at most 3 * 1,440,000 PCM bytes. Existing
        frame/client/player credit bounds are unchanged. No inference runs on
        the writer, and only its confirmed exit permits a normal terminal.
        """
        pending = None
        producer_done = False
        outcome = dict(audio_bytes=0, fault=None, writer_failed=False,
                       abort=threading.Event())
        packet = min(self.settings.limits['frame_bytes'],
                     self.settings.limits['audio_buffer_ms'] * 24, 6000)
        packet -= packet % 2

        def write():
            nonlocal pending
            try:
                while True:
                    with self.condition:
                        while pending is None and not producer_done and not self.cancelled and not self.stopping and not outcome['abort'].is_set():
                            self.condition.wait()
                        if self.cancelled or self.stopping or outcome['abort'].is_set():
                            pending = None
                            return
                        if pending is None:
                            return
                        pcm, pending = pending, None
                        self.condition.notify_all()
                    try:
                        self._write_audio_chunk(pcm, identity, packet, outcome)
                    finally:
                        del pcm
            except Exception:
                with self.condition:
                    outcome['fault'] = outcome['fault'] or 'worker_failed'
                    outcome['writer_failed'] = True
                    outcome['abort'].set()
            finally:
                with self.condition:
                    pending = None
                    self.condition.notify_all()

        stream = backend.synthesize(text, voice, language,
            lambda:self.is_cancelled() or outcome['abort'].is_set())
        writer = None
        started = False
        terminal_safe = True
        try:
            writer = threading.Thread(target=write, daemon=True, name='hugin-audio-writer')
            self._audio_writer = writer
            writer.start()
            started = True
            for pcm in stream:
                if not isinstance(pcm, bytes) or len(pcm) % 2 or len(pcm) > 1440000:
                    raise invalid()
                with self.condition:
                    while pending is not None and outcome['fault'] is None and not self.cancelled and not self.stopping:
                        self.condition.wait()
                    if outcome['fault'] is not None or self.cancelled or self.stopping:
                        break
                    pending = pcm
                    self.condition.notify_all()
                del pcm  # The queue owns this chunk before next(generator).
        except Exception as error:
            with self.condition:
                outcome['fault'] = outcome['fault'] or (
                    error.code if isinstance(error, HuginError) else 'worker_failed')
                outcome['abort'].set()
                self.condition.notify_all()
        finally:
            # Close the generator on its original GPU owner, even if the writer
            # fails or cancellation wakes a producer blocked at the queue slot.
            try:
                stream.close()
            except Exception:
                with self.condition:
                    outcome['fault'] = outcome['fault'] or 'worker_failed'
                    outcome['abort'].set()
                terminal_safe = False
            with self.condition:
                producer_done = True
                self.condition.notify_all()
            if started:
                # Normal playback credit belongs to the local sink, which may
                # be paused. Initialization's readiness timer is not its owner.
                # Cancel/fault still impose the existing bounded cleanup wait.
                while writer.is_alive() and not self.is_cancelled() and not outcome['abort'].is_set():
                    writer.join(.05)
                writer.join(self.settings.limits['cancel_seconds'])
                if writer.is_alive():
                    # Keep the held writer reachable. Family exit, rather than
                    # a terminal, is the remaining cleanup proof.
                    outcome['fault'] = outcome['fault'] or 'worker_failed'
                    terminal_safe = False
                else:
                    self._audio_writer = None
            else:
                self._audio_writer = None
            if outcome['writer_failed']:
                terminal_safe = False  # A partial frame requires EOF/restart.
            with self.condition:
                pending = None
        return outcome['fault'], outcome['audio_bytes'], terminal_safe

    def _operate(self,backend,command,identity):
        # All inference text/PCM/stream locals belong to this one operation.
        # Return only technical terminal facts before synchronizing/publishing.
        kind = command['type']
        code = None
        terminal_safe = True
        audio_bytes = 0
        try:
            if kind == 'offload':
                backend.offload()
            elif kind == 'transcribe' and self.engine == 'stt':
                pcm = self._pcm(command, identity)
                try:
                    text = backend.transcribe(pcm, self.is_cancelled)
                finally:
                    pcm.clear()
                raw = text.encode('utf-8')
                if len(raw) > self.settings.limits['transcript_bytes']:
                    raise HuginError('resource_limit', 'transcribe')
                if not self.is_cancelled():
                    digest = hashlib.sha256(raw).hexdigest()
                    self.send('result_begin', identity, length=len(raw), sha256=digest)
                    with self.data_lock:
                        for offset in range(0, len(raw), self.settings.limits['frame_bytes']):
                            write_frame(self.data_out, Frame('text', identity, offset,
                                raw[offset:offset+self.settings.limits['frame_bytes']]))
                    self.send('result_end', identity, length=len(raw), sha256=digest)
            elif kind == 'synthesize' and self.engine == 'tts':
                text, voice, language = command['text'], command['voice'], command['language']
                if (not isinstance(text, str) or not text.strip() or len(text) > 600
                        or not isinstance(voice, str) or voice not in self.settings.voices or language not in ('German','English')):
                    raise invalid()
                code,audio_bytes,terminal_safe = self._synthesize(
                    backend,text,voice,language,identity)
            else:
                raise invalid()
        except Exception as exc:
            code = exc.code if isinstance(exc, HuginError) else 'worker_failed'
            if kind == 'initialize':
                terminal_safe = False
        finally:
            command.clear()  # Queue transfer ends here, including every failure.
        if code:
            self.send('fault', identity, code=code, phase=kind, retry='later')
        return code,audio_bytes,terminal_safe

    def run(self):
        # Native DLL initialization must finish on this thread before any
        # blocking command-reader thread starts (reproduced Windows CPU hang).
        # Init cancellation uses the parent's held-job startup watchdog.
        started = time.perf_counter()
        identity = Identity(self.instance,ZERO,0)
        try:
            command, identity = self._read_command()
            if command['type'] != 'initialize' or command['device'] not in (None,'cpu','cuda'):
                raise invalid()
            backend = self.factory(self.settings,command['device'])
            command.clear()
            del command
            backend.synchronize()
            self.send('ready',identity,device=backend.device,
                      sample_rate=16000 if self.engine == 'stt' else 24000)
            self.send('terminal',identity,cancelled=False,code=None,audio_bytes=0,
                      elapsed_seconds=time.perf_counter()-started)
        except Exception as exc:
            self.send('fault',identity,code=exc.code if isinstance(exc,HuginError) else 'worker_failed',
                      phase='initialize',retry='restart')
            return  # An incomplete initialization never asserts a GPU terminal.
        threading.Thread(target=self._read_commands, daemon=True,
                         name='hugin-control-reader').start()
        while True:
            command, identity = self.commands.get()
            kind = command['type']
            if kind == 'shutdown':
                command.clear()
                return
            started = time.perf_counter()
            code,audio_bytes,terminal_safe = self._operate(backend,command,identity)
            del command  # No payload-bearing local crosses the idle Queue.get.
            # Terminal acknowledges actual stream closure AND GPU completion.
            if terminal_safe:
                try:
                    backend.synchronize()
                except Exception:
                    terminal_safe = False
                    self.send('fault', identity, code='worker_failed',
                              phase='gpu_synchronize', retry='restart')
            if not terminal_safe:
                return  # EOF/observed own-family exit is the only release proof.
            with self.condition:
                cancelled = self.cancelled or self.stopping
                self.active = None
            self.send('terminal', identity, cancelled=cancelled, code=code,
                      audio_bytes=audio_bytes, elapsed_seconds=time.perf_counter()-started)
            if self.stopping:
                return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--engine', choices=('stt','tts'), required=True)
    parser.add_argument('--instance', required=True)
    parser.add_argument('--data-input', type=int, required=True)
    parser.add_argument('--data-output', type=int, required=True)
    args = parser.parse_args()
    control_out = sys.stdout.buffer
    sys.stdout = sys.stderr
    logging.disable(logging.CRITICAL)
    for name in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','DO_NOT_TRACK'):
        os.environ[name] = '1'
    if os.name == 'nt':
        import msvcrt
        data_in = msvcrt.open_osfhandle(args.data_input, os.O_RDONLY | os.O_BINARY)
        data_out = msvcrt.open_osfhandle(args.data_output, os.O_WRONLY | os.O_BINARY)
    else:
        data_in, data_out = args.data_input, args.data_output
    from .engines import WhisperEngine, QwenEngine
    settings = load_settings(args.root)
    try:
        return WorkerServer(settings, args.engine, args.instance, sys.stdin.buffer,
            control_out, os.fdopen(data_in,'rb',buffering=0),
            os.fdopen(data_out,'wb',buffering=0),
            WhisperEngine if args.engine == 'stt' else QwenEngine).run()
    except Exception:
        return 2  # Never print a native exception or content-bearing traceback.


if __name__ == '__main__':
    raise SystemExit(main())
