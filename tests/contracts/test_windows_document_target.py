"""Document fields prove range editability without a ValuePattern or text value."""
from unittest.mock import patch
import unittest

from hugin.windows.selection_probe import read_uia_target, _target_proof, confirm_uia_target
from test_windows_target import Automation, BASE, Element, Range, Uia as EditUia


class Uia(EditUia):
    UIA_DocumentControlTypeId = 50030
    UIA_IsReadOnlyAttributeId = 40015


def document(start=7, width=0):
    automation = Automation()
    focus = automation.focus
    focus.CurrentControlType = Uia.UIA_DocumentControlTypeId
    focus.pattern.position, focus.pattern.width = start, width
    focus.pattern.owner = Element(77, focus)
    focus.GetCurrentPropertyValue = lambda identity: identity == Uia.UIA_IsTextPatternAvailablePropertyId
    original = focus.GetCurrentPattern
    def pattern(identity):
        if identity == Uia.UIA_ValuePatternId:
            raise AssertionError('a Document must not require ValuePattern')
        return original(identity)
    focus.GetCurrentPattern = pattern
    return automation


class DocumentTargetContracts(unittest.TestCase):
    def read(self, automation):
        return read_uia_target(automation, Uia, BASE, lambda: BASE, lambda: False)

    def proof(self, automation):
        return _target_proof(automation, Uia, BASE, lambda: BASE, lambda: False)

    def confirm(self, automation, proof):
        return confirm_uia_target(automation, Uia, BASE, lambda: BASE, proof)

    def test_document_without_value_pattern_proves_cursor_partial_and_full_selection(self):
        with patch.object(Range, 'GetAttributeValue', return_value=False, create=True):
            for start, width in ((0, 0), (7, 0), (100, 0), (7, 11), (0, 100)):
                with self.subTest(start=start, width=width):
                    automation = document(start, width)
                    result = self.read(automation)
                    self.assertEqual(result.status, 'target_captured')
                    self.assertEqual(result.identity.selection, (start, start + width))
                    self.assertEqual(self.confirm(automation, self.proof(automation)).status, 'target_captured')

    def test_document_and_selection_both_require_explicit_false_readonly(self):
        for scope in ('document', 'selection'):
            for value in (True, None, object(), 0, 1, 'false'):
                with self.subTest(scope=scope, value=value):
                    automation = document(7, 3)
                    def attribute(span, identity):
                        self.assertEqual(identity, Uia.UIA_IsReadOnlyAttributeId)
                        is_document = (span.start, span.end) == (900, 1000)
                        return value if (scope == 'document') == is_document else False
                    with patch.object(Range, 'GetAttributeValue', attribute, create=True):
                        self.assertEqual(self.read(automation).status, 'target_unverifiable')

    def test_document_protection_or_range_changes_after_last_read_reject_confirmation(self):
        original = Range.GetText
        for mutation in ('readonly', 'selection', 'focus', 'disabled', 'embedded'):
            automation = document(7, 3)
            readonly = False
            calls = 0
            def attribute(span, identity):
                is_document = (span.start, span.end) == (900, 1000)
                return False if is_document else readonly
            def text(span, limit):
                nonlocal calls, readonly
                value = original(span, limit)
                calls += 1
                if calls == 4:
                    if mutation == 'readonly': readonly = True
                    elif mutation == 'selection': automation.focus.pattern.width = 4
                    elif mutation == 'focus': automation.focus = Element(99, automation.root)
                    elif mutation == 'disabled': automation.focus.CurrentIsEnabled = False
                    else: automation.focus.pattern.embedded = (8,)
                return value
            with patch.object(Range, 'GetAttributeValue', attribute, create=True):
                proof = self.proof(automation)
                with patch.object(Range, 'GetText', text):
                    result = self.confirm(automation, proof)
                self.assertEqual(result.status, 'target_changed' if mutation in ('selection', 'focus') else 'target_unverifiable', mutation)

    def test_document_foreign_enclosure_and_embedded_object_remain_rejected(self):
        for mutation in ('foreign', 'embedded', 'password', 'unsupported_type'):
            automation = document()
            if mutation == 'foreign': automation.focus.pattern.owner = automation.root
            elif mutation == 'embedded': automation.focus.pattern.embedded = (2,)
            elif mutation == 'password': automation.focus.CurrentIsPassword = True
            else: automation.focus.CurrentControlType = 50026
            with patch.object(Range, 'GetAttributeValue', return_value=False, create=True):
                self.assertEqual(self.read(automation).status, 'target_unverifiable', mutation)

    def test_document_provider_exception_remains_a_probe_failure(self):
        with patch.object(Range, 'GetAttributeValue', side_effect=RuntimeError('synthetic provider failure'), create=True):
            self.assertEqual(self.read(document()).status, 'target_probe_failed')

    def test_document_unicode_uses_the_same_utf16_identity(self):
        automation = document(1, 3)
        automation.focus.pattern.text = 'A😀e\u0301Z'
        with patch.object(Range, 'GetAttributeValue', return_value=False, create=True):
            result = self.read(automation)
            self.assertEqual(result.status, 'target_captured')
            self.assertEqual(result.identity.selection, (1, 5))


if __name__ == '__main__':
    unittest.main()
