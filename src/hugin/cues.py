"""Pinned local Whispering cues; no decoder or network in normal playback."""
from __future__ import annotations

import hashlib
import threading
import time

from .audio import PCMOutput,MAX_PCM_WRITE_BYTES
from .errors import HuginError


ASSET_DIRECTORY = '.runtime/cues/whispering-v7.11.0'
CUE_FILES = {
    'start': (16312,'005da1ff41ce6bd97c932da46b7d9408b3e56dd2f55dc4c4ff41581f5f04a6ca'),
    'end': (24000,'590e77778d799601bb9fd102b58d45a1763448d5b2a9e04655acb9eff8dcfdfa'),
    'complete': (64618,'9807f70fcfaf45886621fb82607cd23ef5e75f925d8eb74b7d6fc11b8461f7ce'),
}


def load_cue_signals(root):
    """Read each fixed asset once, bounded before hashing or retaining bytes."""
    signals={}
    try:
        for kind,(size,digest) in CUE_FILES.items():
            with (root/ASSET_DIRECTORY/(kind+'.pcm')).open('rb') as source:
                pcm=source.read(size+1)
            if len(pcm)!=size or hashlib.sha256(pcm).hexdigest()!=digest:
                raise ValueError
            signals[kind]=pcm
    except (OSError,ValueError):
        raise HuginError('audio_failed','cue_asset') from None
    return signals


class DictationCues:
    """One dictation writer; stop reaches it directly, outside capture FIFO.

    25ms is a bounded provisional acoustic tail, not an echo-free claim.
    Native hearing/loopback acceptance remains separate from these contracts.
    """
    tail_seconds = .025

    def __init__(self, signals, *, output=None, clock=time.monotonic):
        if (set(signals)!=set(CUE_FILES) or any(type(pcm) is not bytes or not pcm
                or len(pcm)%2 or len(pcm)>MAX_PCM_WRITE_BYTES for pcm in signals.values())):
            raise HuginError('audio_failed','cue_format')
        self._signals=dict(signals)
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
        if kind not in self._signals:
            raise HuginError('protocol_invalid','capture_cue')
        with self._lock:
            if self._closed or self._cleanup_pending or self._active is not None:
                raise HuginError('audio_failed','capture_cue_owner')
            if cancelled():return False
            local_cancel=threading.Event()
            self._active,self._cancel=job,local_cancel
        pcm=self._signals[kind]
        deadline=self._clock()+len(pcm)/48000+.5
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
            completed=(self.output.write(pcm,identity,interrupted)
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
