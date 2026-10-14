"""Owned PCM capture/output. waveOut ABI adapted from PipPal (notices/PipPal-MIT.md)."""
from __future__ import annotations

import ctypes as ct
from ctypes import wintypes as wt
import threading
import time

from .errors import HuginError


class RecordingBuffer:
    def __init__(self, limit: int):
        if type(limit) is not int or limit <= 0 or limit % 2:
            raise HuginError('config_invalid','capture')
        self.limit = limit
        self._data = bytearray()
        self._fault = None
        self._cancelled = False
        self._lock = threading.Lock()

    def append(self, data) -> bool:
        with self._lock:
            if self._cancelled or self._fault:
                return False
            length = len(data)
            if length % 2:
                raise HuginError('protocol_invalid','capture')
            if length > self.limit-len(self._data):
                self._fault = HuginError('capture_limit','capture')
                return False
            self._data.extend(data)
            return True

    def cancel(self):
        with self._lock:
            self._cancelled = True
            self._data.clear()

    def finish(self) -> bytes:
        with self._lock:
            if self._fault:
                raise self._fault
            result = bytes(self._data)
            self._data.clear()
            return result

    @property
    def fault(self):
        with self._lock:
            return self._fault


class Microphone:
    def __init__(self, limit: int, stream_factory=None):
        self.limit = limit
        self._factory = stream_factory
        self._stream = None
        self._buffer = None
        self._callback_fault = None

    def start(self):
        if self._stream is not None:
            raise HuginError('microphone_failed','capture_start')
        import sounddevice as sd
        self._buffer = RecordingBuffer(self.limit)
        self._callback_fault = None

        def callback(data, frames, timing, status):
            if status:
                self._callback_fault = HuginError('microphone_failed','capture_callback')
                raise sd.CallbackAbort
            if not self._buffer.append(data):
                raise sd.CallbackAbort

        try:
            if self._factory is None:
                sd.check_input_settings(channels=1,dtype='int16',samplerate=16000)
            factory = self._factory or sd.RawInputStream
            stream = factory(samplerate=16000,channels=1,dtype='int16',callback=callback)
            self._stream = stream
            stream.start()
        except Exception:
            self.cancel()
            raise HuginError('microphone_failed','capture_start') from None

    def stop(self) -> bytes:
        if self._stream is None or self._buffer is None:
            raise HuginError('microphone_failed','capture_stop')
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            raise HuginError('microphone_failed','capture_stop') from None
        self._stream = None
        if self._callback_fault:
            raise self._callback_fault
        return self._buffer.finish()

    def cancel(self):
        if self._buffer is not None:
            self._buffer.cancel()
        if self._stream is not None:
            try:
                self._stream.abort()
                self._stream.close()
            except Exception:
                raise HuginError('microphone_failed','capture_close') from None
            self._stream = None

    @property
    def fault(self):
        return self._callback_fault or (self._buffer.fault if self._buffer else None)

    @property
    def owned(self):
        return self._stream is not None


class _Format(ct.Structure):
    _pack_ = 2
    _fields_ = [('tag',wt.WORD),('channels',wt.WORD),('rate',wt.DWORD),
        ('bytes_per_second',wt.DWORD),('alignment',wt.WORD),('bits',wt.WORD),('extra',wt.WORD)]


class _Header(ct.Structure):
    pass


_Header._fields_ = [('data',ct.c_void_p),('length',wt.DWORD),('recorded',wt.DWORD),
    ('user',ct.c_size_t),('flags',wt.DWORD),('loops',wt.DWORD),
    ('next',ct.POINTER(_Header)),('reserved',ct.c_size_t)]


class _WaveOut:
    def __init__(self, rate):
        self.api = ct.WinDLL('winmm',use_last_error=True)
        self.api.waveOutOpen.argtypes = [ct.POINTER(ct.c_void_p),wt.UINT,ct.POINTER(_Format),
            ct.c_size_t,ct.c_size_t,wt.DWORD]
        self.api.waveOutOpen.restype = wt.UINT
        for name in ('waveOutPrepareHeader','waveOutUnprepareHeader','waveOutWrite'):
            fn = getattr(self.api,name)
            fn.argtypes = [ct.c_void_p,ct.POINTER(_Header),wt.UINT]
            fn.restype = wt.UINT
        for name in ('waveOutReset','waveOutClose'):
            fn = getattr(self.api,name);fn.argtypes=[ct.c_void_p];fn.restype=wt.UINT
        self.handle = ct.c_void_p()
        self.buffers = []
        self.queued_bytes = 0
        fmt = _Format(1,1,rate,rate*2,2,16,0)
        self._check(self.api.waveOutOpen(ct.byref(self.handle),0xFFFFFFFF,ct.byref(fmt),0,0,0))

    @staticmethod
    def _check(code):
        if code:
            raise HuginError('audio_failed','playback')

    def collect(self, force=False):
        keep = []
        for index,(header,data) in enumerate(self.buffers):
            if header.flags & 1 or (force and not header.flags & 16):
                try:
                    self._check(self.api.waveOutUnprepareHeader(self.handle,ct.byref(header),ct.sizeof(header)))
                except HuginError:
                    keep.append((header,data))
                    keep.extend(self.buffers[index+1:])
                    self.buffers = keep
                    raise
                self.queued_bytes -= header.length
            else:
                keep.append((header,data))
        self.buffers = keep

    def submit(self, pcm):
        data = ct.create_string_buffer(pcm)
        header = _Header(data=ct.cast(data,ct.c_void_p),length=len(pcm))
        self._check(self.api.waveOutPrepareHeader(self.handle,ct.byref(header),ct.sizeof(header)))
        self.buffers.append((header,data))
        self.queued_bytes += len(pcm)
        self._check(self.api.waveOutWrite(self.handle,ct.byref(header),ct.sizeof(header)))

    def reset(self):
        self._check(self.api.waveOutReset(self.handle))
        # Keep ownership until every returned header has been unprepared.
        self.collect(force=True)
        if self.buffers:
            raise HuginError('audio_failed','playback_reset')

    def close(self):
        self.reset()
        self._check(self.api.waveOutClose(self.handle))
        self.handle = None


class PCMOutput:
    """Blocking write is only for an audio worker; stop never waits behind backpressure."""
    def __init__(self, rate=24000, buffer_ms=250, factory=None):
        if rate != 24000 or type(buffer_ms) is not int or not 0 < buffer_ms <= 250:
            raise HuginError('config_invalid','playback')
        self.rate = rate
        self.capacity = (rate*2*buffer_ms//1000)//2*2
        self._factory = factory or _WaveOut
        self._player = None
        self._job = None
        self._lock = threading.RLock()

    def start(self, job):
        with self._lock:
            self.stop()
            if self._player is not None:
                self._player.close()
                self._player = None
            self._player = self._factory(self.rate)
            self._job = job

    def write(self, pcm: bytes, job, cancelled=lambda:False) -> bool:
        if not isinstance(pcm,bytes) or len(pcm)>65536 or len(pcm)%2:
            raise HuginError('protocol_invalid','playback')
        offset = 0
        while offset < len(pcm):
            if cancelled():
                return False
            with self._lock:
                if self._job != job or self._player is None:
                    return False
                self._player.collect()
                available = self.capacity-self._player.queued_bytes
                count = min(len(pcm)-offset,max(0,available))//2*2
                if count:
                    self._player.submit(pcm[offset:offset+count])
                    offset += count
                    continue
            time.sleep(.005)
        return True

    def drain(self, job, cancelled=lambda:False) -> bool:
        while not cancelled():
            with self._lock:
                if self._job != job or self._player is None:
                    return False
                self._player.collect()
                if not self._player.queued_bytes:
                    return True
            time.sleep(.005)
        return False

    def stop(self):
        with self._lock:
            self._job = None
            if self._player is not None:
                self._player.reset()

    def close(self):
        with self._lock:
            self.stop()
            if self._player is not None:
                self._player.close()
                self._player = None
