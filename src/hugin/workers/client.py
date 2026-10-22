"""Nonblocking job submission with bounded private IPC and held process ownership.

Callbacks execute on reader threads. An audio callback may wait for the bounded
player to accept PCM; cancel uses a separate control writer and remains live.
"""
from __future__ import annotations
from concurrent.futures import Future
import hashlib
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid

from hugin.config import load_settings
from hugin.errors import HuginError
from hugin.word_timing import MAX_SECTION_PCM_BYTES, MAX_TEXT, parse_alignment
from hugin.protocol import (Identity, Frame, TranscriptReceiver, read_control,
    write_control, read_frame, write_frame, invalid)


class WorkerClient:
    def __init__(self, root: Path, engine: str, callback, *, spawn=None,
                 command=None):
        if engine not in ('stt','tts'):
            raise invalid()
        self.settings = load_settings(Path(root))
        self.engine, self.callback, self.spawn = engine, callback, spawn
        self.command = command
        self.engine_instance = str(uuid.uuid4())
        self.process = None
        self.data_in = self.data_out = None
        self.condition = threading.Condition()
        self.control_lock = threading.Lock()
        self.data_lock = threading.Lock()
        self.active = None
        self.closed = False
        self._closing = False
        self._close_lock = threading.Lock()
        self.failed = False
        self.ready = False
        self.device = None
        self._threads = []

    def _emit(self, event):
        with self.condition:
            if self.closed or self._closing: return
        try:
            self.callback(event)
        except Exception:
            # Caller exceptions are not protocol/log payloads.
            self.cancel_active()

    def _send(self, kind, identity, **fields):
        with self.control_lock:
            if self.process is None or self.process.stdin is None:
                raise HuginError('worker_failed', 'worker_control')
            try:
                write_control(self.process.stdin, dict(schema_version=1, type=kind,
                    engine=self.engine, **identity.fields(), **fields), self.settings.limits['control_bytes'])
            except (OSError,ValueError):
                raise HuginError('worker_failed','worker_control') from None

    def _begin(self, kind, request_id, generation):
        identity = Identity(self.engine_instance, request_id, generation)
        with self.condition:
            if self.closed or self._closing or self.failed or self.active is not None:
                raise HuginError('worker_failed', 'worker_busy')
            future = Future()
            self.active = dict(identity=identity, kind=kind, future=future,
                cancelled=False, receiver=None, received=0, ready_event=None,
                accepted_audio=0, result_ended=False)
            return identity, future

    def start(self, *, device=None):
        if device not in (None,'cpu','cuda') or self.process is not None:
            raise HuginError('worker_failed', 'worker_start')
        incoming_read, incoming_write = os.pipe()
        outgoing_read, outgoing_write = os.pipe()
        startupinfo = None
        kwargs = dict(stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      cwd=str(self.settings.root), close_fds=True)
        command = self.command or [str(self.settings.root / '.runtime' / self.engine /
            ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')),
            '-m', 'hugin.workers.server']
        child_input, child_output = incoming_read, outgoing_write
        try:
            if os.name == 'nt':
                import msvcrt
                child_input = msvcrt.get_osfhandle(incoming_read)
                child_output = msvcrt.get_osfhandle(outgoing_write)
                os.set_handle_inheritable(child_input, True)
                os.set_handle_inheritable(child_output, True)
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.lpAttributeList = {'handle_list': [child_input, child_output]}
                kwargs.update(startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
                if self.spawn is None:
                    # Imported lazily; pure protocol/engine tests need no Win32 module.
                    from hugin.windows.process import OwnedProcess
                    self.spawn = OwnedProcess
            else:
                kwargs['pass_fds'] = (incoming_read, outgoing_write)
                if self.spawn is None:
                    self.spawn = subprocess.Popen
            # Child uses only its own source/runtime paths. No old-stack PATH entry.
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.settings.root / 'src')
            for name in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','DO_NOT_TRACK'):
                env[name] = '1'
            kwargs['env'] = env
            args = [*command, '--root', str(self.settings.root), '--engine', self.engine,
                '--instance', self.engine_instance, '--data-input', str(child_input),
                '--data-output', str(child_output)]
            self.process = self.spawn(args, **kwargs)
        except Exception as error:
            if getattr(error, 'owner', None) is not None:
                self.process = error.owner
                self.failed = True
            for descriptor in (incoming_write, outgoing_read):
                os.close(descriptor)
            failure = HuginError('worker_failed', 'worker_start')
            if self.process is not None:
                failure.owner = self.process
            raise failure from None
        finally:
            os.close(incoming_read)
            os.close(outgoing_write)
        self.data_in = os.fdopen(outgoing_read, 'rb', buffering=0)
        self.data_out = os.fdopen(incoming_write, 'wb', buffering=0)
        identity, future = self._begin('initialize', str(uuid.uuid4()), 0)
        for target in (self._control_reader, self._data_reader, self._stderr_reader):
            thread = threading.Thread(target=target, daemon=True)
            self._threads.append(thread)
            try: thread.start()
            except Exception:
                self._threads.remove(thread)
                raise HuginError('worker_failed','worker_readers') from None
        self._send('initialize', identity, device=device)
        return future

    def transcribe(self, pcm: bytes, request_id: str, generation: int):
        # Admission and transfer ownership must precede any concurrent close.
        with self._close_lock:
            return self._transcribe(pcm,request_id,generation)

    def _transcribe(self, pcm, request_id, generation):
        if self.engine != 'stt' or not self.ready or not isinstance(pcm, bytes):
            raise HuginError('worker_failed', 'transcribe')
        if not pcm or len(pcm) % 2 or len(pcm) > self.settings.limits['capture_bytes']:
            raise HuginError('resource_limit', 'transcribe')
        identity, future = self._begin('transcribe', request_id, generation)
        return self._transfer_pcm(pcm, identity, future, 'transcribe')

    def align(self, pcm24: bytes, text: str, request_id: str, generation: int,
              language=None):
        with self._close_lock:
            language = language or self.settings.language
            if (self.engine != 'stt' or not self.ready or not isinstance(pcm24, bytes)
                    or not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT
                    or language not in ('German','English')):
                raise HuginError('protocol_invalid', 'align')
            if (not pcm24 or len(pcm24) % 2
                    or len(pcm24) > min(MAX_SECTION_PCM_BYTES, self.settings.limits['capture_bytes'])):
                raise HuginError('resource_limit', 'align')
            identity, future = self._begin('align', request_id, generation)
            with self.condition:
                self.active.update(alignment_text=text, alignment_samples=len(pcm24)//2)
            return self._transfer_pcm(pcm24, identity, future, 'align', text=text, language=language)

    def _transfer_pcm(self, pcm, identity, future, kind, **fields):
        # Hashing/copying and pipe writes stay off the caller's input/UI thread.
        def transfer():
            try:
                self._send(kind, identity, length=len(pcm), sha256=hashlib.sha256(pcm).hexdigest(), **fields)
                with self.condition:
                    cancelled = self.active is not None and self.active['cancelled']
                if cancelled:
                    self._send('cancel', identity)
                with self.data_lock:
                    for offset in range(0, len(pcm), self.settings.limits['frame_bytes']):
                        write_frame(self.data_out, Frame('pcm', identity, offset,
                            pcm[offset:offset+self.settings.limits['frame_bytes']]))
            except Exception:
                self._fail('worker_failed', 'worker_input')
        thread=threading.Thread(target=transfer,name='hugin-pcm-transfer',daemon=True)
        self._threads=[item for item in self._threads if item.is_alive()]
        self._threads.append(thread)
        try: thread.start()
        except Exception:
            self._threads.remove(thread)
            self._fail('worker_failed','worker_input')
        return future

    def synthesize(self, text: str, voice: str, request_id: str, generation: int,
                   language=None):
        language = language or self.settings.language
        if (self.engine != 'tts' or not self.ready or not isinstance(text, str)
                or not text.strip() or len(text) > 600 or not isinstance(voice, str) or voice not in self.settings.voices
                or language not in ('German','English')):
            raise HuginError('protocol_invalid', 'synthesize')
        identity, future = self._begin('synthesize', request_id, generation)
        self._send('synthesize', identity, text=text, voice=voice, language=language)
        self._send('credit', identity)
        return future

    def offload(self):
        if self.engine != 'stt' or not self.ready:
            raise HuginError('unsupported', 'offload')
        identity, future = self._begin('offload', str(uuid.uuid4()), 0)
        self._send('offload', identity)
        return future

    def cancel(self, request_id: str, generation: int):
        identity = Identity(self.engine_instance, request_id, generation)
        with self.condition:
            if self.active is None or identity != self.active['identity']:
                return False
            self.active['cancelled'] = True
            if self.active['receiver'] is not None:
                self.active['receiver'].cancel()
            self.condition.notify_all()
        self._send('cancel', identity)
        return True

    def cancel_active(self):
        with self.condition:
            identity = self.active['identity'] if self.active else None
        if identity is not None:
            try:
                self.cancel(identity.request_id, identity.generation)
            except (HuginError, OSError):
                pass

    def _fail(self, code, phase):
        with self.condition:
            if self.failed or self.closed or self._closing:
                return
            self.failed = True
            self.ready = False
            active = self.active
            if active and active['receiver'] is not None:
                active['receiver'].cancel()
            self.condition.notify_all()
        event = dict(type='fault', engine=self.engine, engine_instance=self.engine_instance,
                     code=code, phase=phase, retry='restart')
        if active:
            event.update(active['identity'].fields())
            if not active['future'].done():
                active['future'].set_exception(HuginError(code, phase))
        self._emit(event)

    def _control_reader(self):
        try:
            while True:
                self._read_control_event()
        except EOFError:
            self._fail('worker_failed', 'worker_exit')
        except (HuginError, OSError, ValueError):
            self._fail('protocol_invalid', 'worker_control')

    def _read_control_event(self):
        event = read_control(self.process.stdout, self.settings.limits['control_bytes'])
        identity = Identity.from_message(event)
        base = {'schema_version','type','engine','engine_instance','request_id','generation'}
        extra = {'ready': {'device','sample_rate'}, 'result_begin': {'length','sha256'},
            'result_end': {'length','sha256'}, 'terminal': {'cancelled','code','audio_bytes','elapsed_seconds'},
            'fault': {'code','phase','retry'}, 'alignment': {'status','words'}}
        kind = event.get('type')
        if (type(event.get('schema_version')) is not int or event.get('schema_version') != 1 or event.get('engine') != self.engine
                or identity.engine_instance != self.engine_instance or not isinstance(kind,str) or kind not in extra
                or set(event) != base | extra[kind]):
            raise invalid()
        publish = None
        with self.condition:
            active = self.active
            if active is None or identity != active['identity']:
                raise invalid()
            if kind == 'ready':
                if (active['kind'] != 'initialize' or active['ready_event'] is not None
                        or event['device'] not in ('cpu','cuda')
                        or type(event['sample_rate']) is not int
                        or event['sample_rate'] != (16000 if self.engine == 'stt' else 24000)):
                    raise invalid()
                active['ready_event'] = event
            elif kind == 'result_begin':
                if active['kind'] != 'transcribe' or active['receiver'] is not None:
                    raise invalid()
                active['receiver'] = TranscriptReceiver(identity, event['length'],
                    event['sha256'], self.settings.limits['transcript_bytes'])
                self.condition.notify_all()
            elif kind == 'result_end':
                receiver = active['receiver']
                if receiver is None or active['result_ended']:
                    raise invalid()
                self.condition.wait_for(lambda: self.failed or
                    active['received'] == receiver.length,
                    timeout=self.settings.limits['ready_seconds'])
                if self.failed or active['received'] != receiver.length:
                    raise invalid()
                if not active['cancelled']:
                    publish = dict(type='result', engine=self.engine,
                                   **identity.fields(), text=receiver.finish(event['length'],event['sha256']))
                active['result_ended'] = True
            elif kind == 'alignment':
                if active['kind'] != 'align' or active['result_ended']:
                    raise invalid()
                result = parse_alignment(dict(status=event['status'], words=event['words']),
                    active.pop('alignment_text'), active.pop('alignment_samples'))
                active['result_ended'] = True
                if not active['cancelled']:
                    publish = dict(type='alignment', engine=self.engine,
                        **identity.fields(), result=result)
            elif kind == 'terminal':
                if (type(event['cancelled']) is not bool or type(event['audio_bytes']) is not int
                        or event['audio_bytes'] < 0 or event['audio_bytes'] % 2
                        or type(event['elapsed_seconds']) not in (int,float)
                        or event['elapsed_seconds'] < 0
                        or event['code'] not in (None,'worker_failed','resource_limit','protocol_invalid','unsupported','asset_integrity')):
                    raise invalid()
                if active['kind'] == 'synthesize':
                    # Even cancellation must drain the declared framed
                    # bytes before this request's identity is retired.
                    # Receipt advances before callbacks, so this never
                    # waits behind the current blocked audio callback.
                    self.condition.wait_for(lambda: self.failed or
                        active['received'] == event['audio_bytes'],
                        timeout=self.settings.limits['ready_seconds'])
                    if self.failed or active['received'] != event['audio_bytes']:
                        raise invalid()
                if not event['cancelled'] and not active['cancelled']:
                    if active['kind'] in ('transcribe','align') and event['code'] is None and not active['result_ended']:
                        raise invalid()
                    if active['kind'] == 'synthesize':
                        # This is our local audio callback, not remote transport
                        # readiness. Pause may hold it indefinitely; cancel and
                        # failure wake it independently of playback credit.
                        self.condition.wait_for(lambda: self.failed or active['cancelled'] or
                            active['accepted_audio'] == event['audio_bytes'])
                        if self.failed or (not active['cancelled'] and active['accepted_audio'] != event['audio_bytes']):
                            raise invalid()
                if active['receiver'] is not None:
                    active['receiver'].cancel()
                self.active = None
                self.condition.notify_all()
                if active['kind'] == 'initialize':
                    ready = active['ready_event']
                    if ready is None or event['cancelled'] or event['code']:
                        active['future'].set_exception(HuginError('worker_failed','initialize'))
                    else:
                        self.ready, self.device = True, ready['device']
                        active['future'].set_result(ready)
                        publish = ready
                else:
                    active['future'].set_result(event)
                    publish = event
            else:
                if (event['code'] not in ('worker_failed','resource_limit','protocol_invalid','unsupported','asset_integrity')
                        or event['phase'] not in ('worker_protocol','initialize','transcribe','align','synthesize','offload','gpu_synchronize')
                        or event['retry'] not in ('later','restart')):
                    raise invalid()
                publish = event
        if publish is not None:
            self._emit(publish)

    def _data_reader(self):
        try:
            while True:
                self._read_data_frame()
        except EOFError:
            self._fail('worker_failed','worker_exit')
        except (HuginError, OSError, ValueError):
            self._fail('protocol_invalid','worker_data')

    def _read_data_frame(self):
        frame = read_frame(self.data_in)
        with self.condition:
            active = self.active
            if active is None or frame.identity != active['identity'] or frame.offset != active['received']:
                raise invalid()
            if frame.kind == 'text':
                self.condition.wait_for(lambda: self.failed or active['receiver'] is not None,
                    timeout=self.settings.limits['ready_seconds'])
                receiver = active['receiver']
                if receiver is None or active['received'] + len(frame.data) > receiver.length:
                    raise invalid()
                if not active['cancelled']:
                    receiver.add(frame)
            elif (active['kind'] != 'synthesize' or len(frame.data) >
                    min(self.settings.limits['audio_buffer_ms'] * 24, 6000)):
                raise invalid()
            active['received'] += len(frame.data)
            cancelled = active['cancelled']
            self.condition.notify_all()
        if frame.kind == 'pcm' and not cancelled:
            self._emit(dict(type='audio',engine=self.engine,**frame.identity.fields(),
                            pcm=frame.data,sample_rate=24000,offset=frame.offset))
            with self.condition:
                still_current = self.active is active and not active['cancelled']
                if still_current:
                    # Receipt proves framing, not publication. A normal
                    # terminal must not overtake this callback (and let
                    # the coordinator retire its last PCM as stale).
                    active['accepted_audio'] += len(frame.data)
                    self.condition.notify_all()
            if still_current:
                self._send('credit', frame.identity)

    def _stderr_reader(self):
        # Drain in bounded chunks, discard every byte. Native output can contain
        # user content; neither exception names nor raw lines are diagnostics.
        try:
            while self.process.stderr.read(4096):
                pass
        except (OSError, ValueError):
            pass

    def close(self):
        with self._close_lock:
            if self.closed or self.process is None:
                self.closed = True
                return
            self._close_owned()

    def _close_owned(self):
        self.cancel_active()
        with self.condition:
            # Stop admission/publication now; closed is only a completed
            # cleanup fact, never an intent to terminate a held native family.
            self._closing = True
            self.ready = False
            identity = self.active['identity'] if self.active else Identity(
                self.engine_instance, str(uuid.uuid4()), 0)
        try:
            self._send('shutdown', identity)
        except (HuginError, OSError, ValueError):
            pass
        # A failed creation may own handles without ever owning a process.
        # Only its owner can prove that fact; unknown adapters still wait.
        if getattr(self.process,'process_created',None) is not False:
            try:
                self.process.wait(timeout=self.settings.limits['cancel_seconds'])
            except subprocess.TimeoutExpired:
                self.process.kill()  # Held own-process Job Object, never a PID lookup.
                try:
                    self.process.wait(timeout=self.settings.limits['exit_seconds'])
                except subprocess.TimeoutExpired:
                    self.failed = True
                    raise HuginError('worker_timeout','worker_exit') from None
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr,self.data_in,self.data_out):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass
        deadline=time.monotonic()+1
        for thread in self._threads:
            if thread is not threading.current_thread(): thread.join(max(0,deadline-time.monotonic()))
        if any(thread is not threading.current_thread() and thread.is_alive() for thread in self._threads):
            raise HuginError('worker_timeout','worker_threads')
        if hasattr(self.process, 'close'):
            self.process.close()
        with self.condition:
            self.closed = True
            if self.active and not self.active['future'].done():
                self.active['future'].set_exception(HuginError('worker_failed','worker_closed'))
            self.active = None
            self.condition.notify_all()


class EnginePool:
    """Registry only. The controller serializes start/offload/inference itself."""
    def __init__(self, root: Path, callback, *, spawn=None):
        self.root, self.callback, self.spawn = Path(root), callback, spawn
        self.workers = {}

    def start(self, engine, *, device=None):
        if engine in self.workers:
            raise HuginError('worker_failed','worker_start')
        worker = WorkerClient(self.root,engine,self.callback,spawn=self.spawn)
        self.workers[engine] = worker
        return worker.start(device=device)

    def transcribe(self, pcm, request_id, generation):
        return self.workers['stt'].transcribe(pcm,request_id,generation)

    def align(self, pcm24, text, request_id, generation, language=None):
        return self.workers['stt'].align(pcm24,text,request_id,generation,language)

    def synthesize(self, text, voice, request_id, generation, language=None):
        return self.workers['tts'].synthesize(text,voice,request_id,generation,language)

    def cancel(self, engine, request_id, generation):
        return self.workers[engine].cancel(request_id,generation)

    def offload(self, engine='stt'):
        return self.workers[engine].offload()

    def close(self):
        errors = []
        for worker in self.workers.values():
            try:
                worker.close()
            except HuginError as error:
                errors.append(error)
        if errors:
            raise errors[0]
