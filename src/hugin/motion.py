"""Presentation-only motion clock; receives facts, never performs app actions."""
from __future__ import annotations

import math


class Motion:
    def __init__(self):
        self.activity='preparing'
        self.level=0.0
        self._receipt=0
        self._start=0.0
        self._until=0.0

    def update(self, view, now):
        self.activity='error' if view.error else view.activity
        level=view.audio_level
        self.level=(max(0.0,min(1.0,float(level)))
                    if type(level) in (int,float) and math.isfinite(level)
                    and self.activity=='recording' else 0.0)
        if view.completion_id > self._receipt:
            self._receipt=view.completion_id
            self._start=now
            self._until=view.completion_until
        if self.activity!='idle' or view.completion_until<=now:
            self._until=0.0

    def phase(self, now):
        return 'complete' if now < self._until and self.activity=='idle' else self.activity

    def progress(self, now):
        duration=self._until-self._start
        return min(1.0,max(0.0,(now-self._start)/duration)) if duration>0 else 1.0
