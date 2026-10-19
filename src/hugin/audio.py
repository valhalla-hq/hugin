"""Owned PCM capture/output. waveOut ABI adapted from PipPal (notices/PipPal-MIT.md)."""
from __future__ import annotations

import ctypes as ct
from ctypes import wintypes as wt
from dataclasses import dataclass,field
import math
import struct
import threading
import time

from .errors import HuginError

MAX_PCM_WRITE_BYTES = 65536


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


@dataclass
class _InputGate:
    required: bool
    cutoff: float | None = None
    cancelled: bool = False
    fault: HuginError | None = None
    _level: float = 0.0
    _level_at: float | None = None
    _meter_open: bool = True
    _meter_lock: threading.Lock = field(default_factory=threading.Lock,repr=False)

    def measure(self,data,now):
        # Exactly the latest <=32ms of accepted mono PCM16, with fixed callback
        # work and no retained samples, queue or UI callback.
        window=memoryview(data)[-1024:]
        count=len(window)//2
        squares=sum(sample*sample for (sample,) in struct.iter_unpack('<h',window))
        level=math.sqrt(squares/count)/32768 if count else 0.0
        with self._meter_lock:
            if self._meter_open and not self.cancelled:
                self._level,self._level_at=level,now

    def close_meter(self,*,cancel=False):
        with self._meter_lock:
            if cancel:self.cancelled=True
            self._meter_open=False
            self._level,self._level_at=0.0,None

    def level(self,now):
        with self._meter_lock:
            if (not self._meter_open or self.cancelled or self._level_at is None
                    or not 0<=now-self._level_at<=.25):
                return 0.0
            return self._level


def _windows_capture_options(sd):
    """Bind the native WASAPI default once; MME does not supply ADC clocks."""
    apis=sd.query_hostapis()
    if not isinstance(apis,(tuple,list)):
        raise HuginError('microphone_failed','capture_device')
    matches=[(index,api) for index,api in enumerate(apis)
        if isinstance(api,dict) and api.get('name')=='Windows WASAPI']
    if len(matches)!=1:
        raise HuginError('microphone_failed','capture_device')
    host,api=matches[0];device=api.get('default_input_device')
    if type(device) is not int or not 0<=device<1<<31:
        raise HuginError('microphone_failed','capture_device')
    info=sd.query_devices(device)
    if (not isinstance(info,dict) or type(info.get('hostapi')) is not int or info['hostapi']!=host
            or type(info.get('max_input_channels')) is not int or info['max_input_channels']<1):
        raise HuginError('microphone_failed','capture_device')
    return dict(device=device,extra_settings=sd.WasapiSettings(auto_convert=True))


class Microphone:
    def __init__(self, limit: int, stream_factory=None, *, clock=time.monotonic):
        self.limit = limit
        self._factory = stream_factory
        self._stream = None
        self._buffer = None
        self._gate = None
        self._clock = clock

    def start(self, *, armed=True):
        if type(armed) is not bool:
            raise HuginError('config_invalid','capture_gate')
        if self._stream is not None:
            raise HuginError('microphone_failed','capture_start')
        import sounddevice as sd
        buffer = RecordingBuffer(self.limit)
        gate = _InputGate(required=not armed)
        self._buffer,self._gate = buffer,gate

        def callback(data, frames, timing, status):
            if gate.cancelled:
                return
            if status:
                gate.fault = HuginError('microphone_failed','capture_callback')
                gate.close_meter()
                raise sd.CallbackAbort
            if gate.required:
                adc = getattr(timing,'inputBufferAdcTime',None)
                if type(adc) not in (int,float) or adc==0 or not math.isfinite(adc):
                    gate.fault = HuginError('microphone_failed','capture_clock')
                    gate.close_meter()
                    raise sd.CallbackAbort
                # A callback delivered after arming may contain old ADC data.
                # Drop the whole block when it starts before the cutoff,
                # including blocks that overlap it. No callback waits or I/O.
                if gate.cutoff is None or adc < gate.cutoff:
                    return
            if not buffer.append(data):
                gate.close_meter()
                raise sd.CallbackAbort
            gate.measure(data,self._clock())

        try:
            options={}
            if self._factory is None:
                options=_windows_capture_options(sd)
                sd.check_input_settings(channels=1,dtype='int16',samplerate=16000,**options)
            factory = self._factory or sd.RawInputStream
            stream = factory(samplerate=16000,channels=1,dtype='int16',callback=callback,**options)
            self._stream = stream
            stream.start()
            if gate.fault or buffer.fault:
                raise HuginError('microphone_failed','capture_start')
        except Exception:
            self.cancel()
            raise HuginError('microphone_failed','capture_start') from None

    @property
    def device_time(self):
        if self._stream is None:
            raise HuginError('microphone_failed','capture_clock')
        value = self._stream.time
        if type(value) not in (int,float) or not math.isfinite(value):
            raise HuginError('microphone_failed','capture_clock')
        return float(value)

    def arm_after(self, device_time):
        if (self._stream is None or self._gate is None or self._gate.cancelled
                or not self._gate.required or self.fault is not None
                or type(device_time) not in (int,float) or not math.isfinite(device_time)):
            raise HuginError('microphone_failed','capture_gate')
        self._gate.cutoff = float(device_time)

    def stop(self) -> bytes:
        if self._stream is None or self._buffer is None:
            raise HuginError('microphone_failed','capture_stop')
        self._gate.close_meter()
        try:
            self._stream.stop(ignore_errors=False)
            self._stream.close(ignore_errors=False)
        except Exception:
            raise HuginError('microphone_failed','capture_stop') from None
        self._stream = None
        self._gate.close_meter(cancel=True)
        if self._gate.fault:
            raise self._gate.fault
        return self._buffer.finish()

    def cancel(self):
        if self._gate is not None:
            self._gate.close_meter(cancel=True)
        if self._buffer is not None:
            self._buffer.cancel()
        if self._stream is not None:
            try:
                self._stream.abort(ignore_errors=False)
                self._stream.close(ignore_errors=False)
            except Exception:
                raise HuginError('microphone_failed','capture_close') from None
            self._stream = None

    @property
    def audio_level(self):
        gate=self._gate
        if self._stream is None or gate is None or self.fault is not None:
            return 0.0
        return gate.level(self._clock())

    @property
    def fault(self):
        return (self._gate.fault if self._gate else None) or (self._buffer.fault if self._buffer else None)

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
        # Keep a second native header queued while reclaiming/refilling the
        # first. One full-capacity header forces every refill past queue empty.
        self._block_bytes = max(2, (self.capacity//2)//2*2)
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
        if not isinstance(pcm,bytes) or len(pcm)>MAX_PCM_WRITE_BYTES or len(pcm)%2:
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
                count = min(len(pcm)-offset,self._block_bytes,max(0,available))//2*2
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
