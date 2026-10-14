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

    def _read_commands(self):
        try:
            while True:
                command, identity = self._read_command()
                kind = command.get('type')
                with self.condition:
                    if kind == 'shutdown':
                        self.stopping = self.cancelled = True
                        self.condition.notify_all()
                        if self.active is None:
                            self.commands.put_nowait((command, identity))
                        return
                    if kind in ('cancel','credit'):
                        if identity == self.active:
                            if kind == 'cancel':
                                self.cancelled = True
                            else:
                                if self.credit:
                                    raise invalid()
                                self.credit = True
                            self.condition.notify_all()
                        continue
                    if self.active is not None:
                        raise invalid()
                    self.active = identity
                    self.cancelled = self.credit = False
                    self.commands.put_nowait((command, identity))
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

    def _wait_credit(self):
        with self.condition:
            while not self.credit and not self.cancelled and not self.stopping:
                self.condition.wait()
            if self.cancelled or self.stopping:
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
            frame = read_frame(self.data_in)
            if (frame.kind != 'pcm' or frame.identity != identity
                    or frame.offset != len(draft) or len(draft) + len(frame.data) > length):
                raise invalid()
            draft.extend(frame.data)
        if hashlib.sha256(draft).hexdigest() != digest:
            raise invalid()
        return draft

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
                return
            started = time.perf_counter()
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
                    stream = backend.synthesize(text, voice, language, self.is_cancelled)
                    packet = min(self.settings.limits['frame_bytes'],
                                 self.settings.limits['audio_buffer_ms'] * 24, 6000)
                    packet -= packet % 2
                    try:
                        for pcm in stream:
                            if not isinstance(pcm, bytes) or len(pcm) % 2 or len(pcm) > 1440000:
                                raise invalid()
                            for index in range(0, len(pcm), packet):
                                if not self._wait_credit():
                                    break
                                with self.data_lock:
                                    part = pcm[index:index+packet]
                                    write_frame(self.data_out, Frame('pcm', identity, audio_bytes, part))
                                    audio_bytes += len(part)
                            if self.is_cancelled():
                                break
                    finally:
                        stream.close()
                else:
                    raise invalid()
            except Exception as exc:
                code = exc.code if isinstance(exc, HuginError) else 'worker_failed'
                self.send('fault', identity, code=code, phase=kind, retry='later')
                if kind == 'initialize':
                    terminal_safe = False
            finally:
                # Terminal acknowledges actual stream closure AND GPU completion.
                if backend is not None and terminal_safe:
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
