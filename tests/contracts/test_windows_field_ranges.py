"""UIA field ownership is independent of structural endpoint ordering.

Chromium 155.0.8059.40 AXPosition::SlowCompareTo compares text offset,
then upstream/downstream affinity. Atomic fields hide their child anchors
from GetEnclosingElement. Model those public facts separately, not as an
invalid numeric offset that Python slicing silently clamps.
"""
from dataclasses import dataclass
from types import SimpleNamespace as NS
import unittest

from hugin.windows.selection_probe import read_uia_target, _target_proof, confirm_uia_target
from test_windows_target import Automation, Element, Uia, BASE, Ranges


@dataclass(frozen=True, order=True)
class Position:
    offset: int
    affinity: int = 0


class FieldRange:
    def __init__(self, model, start, end):
        self.model, self.start, self.end = model, start, end

    def Clone(self):
        return FieldRange(self.model, self.start, self.end)

    def CompareEndpoints(self, endpoint, other, other_endpoint):
        left = (self.start, self.end)[endpoint]
        right = (other.start, other.end)[other_endpoint]
        return (left > right) - (left < right)

    def GetEnclosingElement(self):
        return self.model.enclosure(self)

    def GetChildren(self):
        return NS(Length=0)

    def MoveEndpointByRange(self, endpoint, other, other_endpoint):
        value = (other.start, other.end)[other_endpoint]
        if endpoint == 0:
            self.start, self.end = value, max(self.end, value)
        else:
            self.end, self.start = value, min(self.start, value)

    def GetText(self, limit):
        assert 0 < limit <= 262145
        data = self.model.text.encode('utf-16-le')
        assert 0 <= self.start.offset <= self.end.offset <= len(data) // 2
        text = data[2*self.start.offset:2*self.end.offset].decode('utf-16-le')[:limit]
        self.model.after_read()
        return text

    def Select(self):
        raise AssertionError('a field proof must not modify the selection')


class FieldPattern:
    SupportedTextSelection = 1

    def __init__(self, owner, text, start, end):
        self.owner, self.text = owner, text
        self.start, self.end = start, end
        self.enclosure = lambda _: self.owner
        self.after_read = lambda: None

    def QueryInterface(self, *_):
        return self

    @property
    def DocumentRange(self):
        return FieldRange(self, Position(0), Position(len(self.text.encode('utf-16-le')) // 2))

    def GetSelection(self):
        return Ranges(FieldRange(self, self.start, self.end))


def field(start, end, text='Anfang alte Wörter Ende'):
    automation = Automation()
    automation.focus.pattern = FieldPattern(automation.focus, text, start, end)
    return automation


class FieldRangeContracts(unittest.TestCase):
    def read(self, automation):
        return read_uia_target(automation, Uia, BASE, lambda: BASE, lambda: False)

    def proof(self, automation):
        return _target_proof(automation, Uia, BASE, lambda: BASE, lambda: False)

    def confirm(self, automation, proof):
        return confirm_uia_target(automation, Uia, BASE, lambda: BASE, proof)

    def test_cursor_partial_and_full_selection_with_hidden_child_end_affinity(self):
        for start, end in ((0, 0), (7, 7), (23, 23), (7, 18), (7, 23), (0, 23)):
            with self.subTest(start=start, end=end):
                automation = field(Position(start, int(start == 23)), Position(end, int(end == 23)))
                result = self.read(automation)
                self.assertEqual(result.status, 'target_captured')
                self.assertEqual(result.identity.selection, (start, end))
                self.assertEqual(result.identity.start_id, automation.focus.GetRuntimeId())
                self.assertEqual(result.identity.end_id, automation.focus.GetRuntimeId())
                self.assertEqual(result.identity.end_relation, 1 if end == 23 else -1)
                self.assertEqual(self.confirm(automation, self.proof(automation)).status, 'target_captured')

    def test_visible_and_hidden_child_enclosures_use_the_same_range_semantics(self):
        for visible in (False, True):
            automation = field(Position(7), Position(23, 1))
            child = Element(77, automation.focus)
            if visible:
                automation.focus.pattern.enclosure = lambda _: child
            result = self.read(automation)
            self.assertEqual(result.status, 'target_captured')
            self.assertEqual(result.identity.selection, (7, 23))
            self.assertEqual(result.identity.end_relation, 1)

    def test_unicode_offsets_are_utf16_and_affinity_is_not_an_extra_character(self):
        automation = field(Position(1), Position(6, 1), 'A😀e\u0301Z')
        result = self.read(automation)
        self.assertEqual(result.status, 'target_captured')
        self.assertEqual(result.identity.selection, (1, 6))
        self.assertEqual(result.identity.end_relation, 1)

    def test_same_text_length_does_not_authorize_a_foreign_or_unknown_enclosure(self):
        for kind in ('sibling', 'root', 'unknown'):
            automation = field(Position(23, 1), Position(23, 1))
            other = Element(88, automation.root) if kind == 'sibling' else automation.root if kind == 'root' else None
            automation.focus.pattern.enclosure = lambda text_range: (
                other if text_range.start == text_range.end else automation.focus)
            self.assertEqual(self.read(automation).status, 'target_unverifiable', kind)

    def test_changed_start_end_affinity_or_field_rejects_confirmation(self):
        for kind in ('start', 'end', 'affinity', 'field'):
            automation = field(Position(7), Position(23, 1))
            proof = self.proof(automation)
            if kind == 'start':
                automation.focus.pattern.start = Position(8)
            elif kind == 'end':
                automation.focus.pattern.end = Position(22)
            elif kind == 'affinity':
                automation.focus.pattern.end = Position(23)
            else:
                automation.focus = Element(99, automation.root)
            self.assertEqual(self.confirm(automation, proof).status, 'target_changed', kind)

    def test_invisible_noncollapsed_affinity_span_remains_unverifiable(self):
        automation = field(Position(23), Position(23, 1))
        self.assertEqual(self.read(automation).status, 'target_unverifiable')

    def test_change_after_last_text_read_is_rejected(self):
        automation = field(Position(7), Position(23, 1))
        proof = self.proof(automation)
        reads = 0
        def change():
            nonlocal reads
            reads += 1
            if reads == 4:
                automation.focus.pattern.end = Position(23)
        automation.focus.pattern.after_read = change
        self.assertEqual(self.confirm(automation, proof).status, 'target_changed')


if __name__ == '__main__':
    unittest.main()
