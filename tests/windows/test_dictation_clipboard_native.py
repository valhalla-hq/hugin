"""Opt-in publication/persistence proof; paste only into our hidden Edit."""
import ctypes as C
from ctypes import wintypes as W
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from hugin.windows.clipboard import ClipboardFailure,ClipboardService,NativeClipboard,MAX_SNAPSHOT_BYTES


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_NATIVE_CLIPBOARD')=='1',
                     'explicit disposable text clipboard probe required')
class DictationClipboardNative(unittest.TestCase):
    def test_unknown_original_becomes_persistent_text_and_pastes_into_owned_edit(self):
        writer=NativeClipboard();reader=NativeClipboard();latest=None;edit=None;parent=None
        replace=writer.replace
        def tracked_replace(*args,**kwargs):
            nonlocal latest
            try:latest=replace(*args,**kwargs)
            except ClipboardFailure as failure:
                if failure.owned_sequence is not None:latest=failure.owned_sequence
                raise
            return latest
        writer.replace=tracked_replace
        def snapshot_at(sequence):
            opened=reader._opened
            @contextmanager
            def guarded_open(**kwargs):
                with opened(**kwargs):
                    if reader.sequence()!=sequence:raise ClipboardFailure('clipboard_changed')
                    yield
            with patch.object(reader,'_opened',guarded_open):return reader.snapshot(MAX_SNAPSHOT_BYTES)
        try:
            with reader._opened():
                text_formats={1,7,13,16,*(reader.registered[name] for name in
                    ('HTML Format','Rich Text Format','Chromium internal source RFH token','Chromium internal source URL'))}
                self.assertTrue(set(reader._format_ids())<=text_formats,
                    'initial clipboard must be disposable text with supported formatting')
                initial=reader.sequence()
            original=snapshot_at(initial)
            unknown=writer.user.RegisterClipboardFormatW('Hugin.Test.UnsupportedOriginal.v1')
            latest=writer.replace(((unknown,b'synthetic unknown format'),),original.sequence)
            # Exercise the real service and producer without an eligible target.
            # There is no SendInput or foreground manipulation in this fixture.
            text='Hugin Zwischenablage Ä 😀'
            result=ClipboardService(backend=writer).deliver(text,None,lambda:True)
            self.assertEqual((result.status,result.copied,result.submitted),('target_unverifiable',True,False))
            published=snapshot_at(latest)
            self.assertEqual(published.sequence,latest)
            payload=dict(published.formats)
            self.assertEqual(payload[13].decode('utf-16-le').rstrip('\0'),text)
            self.assertEqual(payload[reader.registered['ExcludeClipboardContentFromMonitorProcessing']],b'\0'*4)
            self.assertEqual(len(payload[reader.tx_format]),32)

            rich_edit=C.WinDLL('Msftedit.dll')
            parent=reader.user.CreateWindowExW(0,'STATIC','',0,0,0,120,30,None,None,None,None)
            self.assertTrue(parent)
            edit=reader.user.CreateWindowExW(0,'RICHEDIT50W','',0x40000004,0,0,120,30,parent,None,None,None)
            self.assertTrue(edit)
            reader.user.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
            reader.user.SendMessageW.restype=C.c_ssize_t
            reader.user.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
            reader.user.GetWindowTextW.restype=C.c_int
            reader.user.SetWindowTextW.argtypes=[W.HWND,W.LPCWSTR]
            reader.user.SetWindowTextW.restype=W.BOOL
            self.assertTrue(reader.user.SetWindowTextW(edit,'Synthetic selection'))
            value=C.create_unicode_buffer(100)
            reader.user.GetWindowTextW(edit,value,len(value))
            self.assertEqual(value.value,'Synthetic selection')
            reader.user.SendMessageW(edit,0xb1,0,-1)
            self.assertEqual(reader.sequence(),latest,'clipboard changed before fixture paste')
            reader.user.SendMessageW(edit,0x302,0,0)
            self.assertEqual(reader.sequence(),latest,'clipboard changed during fixture paste')
            value=C.create_unicode_buffer(100)
            reader.user.GetWindowTextW(edit,value,len(value))
            self.assertEqual(value.value,text)
            self.assertEqual(reader.sequence(),latest)
            writer.close()
            persisted=snapshot_at(latest)
            self.assertTrue(persisted.formats==published.formats,'rendered clipboard did not survive owner close')
        finally:
            try:
                # A newer user's copy always wins, even when the test fails.
                if latest is not None and reader.sequence()==latest:
                    restored=reader.replace(original.formats,latest)
                    self.assertTrue(snapshot_at(restored).formats==original.formats,'original clipboard restoration differs')
            finally:
                if edit:reader.user.DestroyWindow(edit)
                if parent:reader.user.DestroyWindow(parent)
                try:writer.close()
                finally:reader.close()


if __name__=='__main__':unittest.main()
