"""Three original bounded PCM signals; no assets, models or system sound service."""
from __future__ import annotations

import math
import struct
import threading
import time

from .audio import PCMOutput
from .errors import HuginError


def _pulse(frequency, milliseconds):
    count = 24000*milliseconds//1000
    fade = min(144,count//2)
    samples=[]
    for index in range(count):
        edge=min(index,count-1-index,fade)/fade
        envelope=math.sin(edge*math.pi/2)**2
        samples.append(round(7500*envelope*math.sin(2*math.pi*frequency*index/24000)))
    return struct.pack('<'+'h'*count,*samples)


_START = _pulse(420,35)+bytes(24000*2*45//1000)+_pulse(420,35)
_END = _pulse(1000,65)+bytes(24000*2*25//1000)+_pulse(1600,90)
_COMPLETE = (_pulse(660,40)+bytes(24000*2*15//1000)+_pulse(880,40)
    +bytes(24000*2*15//1000)+_pulse(1320,70))
_SIGNALS = {'start':_START,'end':_END,'complete':_COMPLETE}


class DictationCues:
    """One dictation writer; stop reaches it directly, outside capture FIFO.

    25ms is a bounded provisional acoustic tail, not an echo-free claim.
    Native hearing/loopback acceptance remains separate from these contracts.
    """
    tail_seconds = .025

    def __init__(self, *, output=None, clock=time.monotonic):
        self.output=output if output is not None else PCMOutput(buffer_ms=100)
        self._clock=clock
        self._lock=threading.Lock()
        self._active=None
        self._cancel=None
        self._cleanup_pending=False
        self._closed=False

    @property
    def closed(self):
        with self._lock:return self._closed

    @property
    def cleanup_pending(self):
        with self._lock:return self._cleanup_pending

    def play(self, kind, job, cancelled):
        if kind not in _SIGNALS:
            raise HuginError('protocol_invalid','capture_cue')
        with self._lock:
            if self._closed or self._cleanup_pending or self._active is not None:
                raise HuginError('audio_failed','capture_cue_owner')
            if cancelled():return False
            local_cancel=threading.Event()
            self._active,self._cancel=job,local_cancel
        deadline=self._clock()+.5
        def interrupted():return local_cancel.is_set() or cancelled() or self._clock()>=deadline
        def completed_or_cancelled(completed):
            if local_cancel.is_set() or cancelled():return False
            if not completed or self._clock()>=deadline:
                raise HuginError('audio_failed','capture_cue_timeout')
            return True
        try:
            if interrupted():return completed_or_cancelled(False)
            identity=(job,kind)
            self.output.start(identity)
            completed=(self.output.write(_SIGNALS[kind],identity,interrupted)
                and self.output.drain(identity,interrupted))
            return completed_or_cancelled(completed)
        finally:
            try:self.stop(job)
            finally:
                with self._lock:self._active,self._cancel=None,None

    def stop(self, job=None):
        # Serialize identity, native reset and its fact together. This lock is
        # never held by write/drain, so cancel does not queue behind playback.
        with self._lock:
            if job is not None and self._active != job:return
            if self._cancel is not None:self._cancel.set()
            try:self.output.stop()
            except Exception:
                self._cleanup_pending=True
                raise HuginError('audio_failed','capture_cue_cleanup') from None
            else:
                self._cleanup_pending=False

    def close(self):
        if self.closed:return
        self.stop()
        try:self.output.close()
        except Exception:
            with self._lock:self._cleanup_pending=True
            raise HuginError('audio_failed','capture_cue_cleanup') from None
        with self._lock:self._closed=True;self._cleanup_pending=False
