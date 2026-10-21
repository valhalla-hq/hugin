"""Opt-in synthetic OLE image -> staged text -> exact image/policy restoration."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

from hugin.windows.clipboard import NativeClipboard,MAX_SNAPSHOT_BYTES
from hugin.windows.process import OwnedProcess


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_NATIVE_CLIPBOARD')=='1',
                     'explicit synthetic clipboard probe required')
class NativeOleRaster(unittest.TestCase):
    def wait_file(self,path,owner,timeout=12):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            if path.is_file() and path.stat().st_size:return path.read_text(encoding='utf-8-sig')
            if owner.poll() is not None:
                self.fail('fixture exited: '+owner.stderr.read(4096).decode('utf-8',errors='replace'))
            time.sleep(.02)
        self.fail('synthetic fixture timed out')

    def test_ole_bitmap_stream_and_policies_survive_staging_and_real_edit_paste(self):
        backend=NativeClipboard();owner=None;edit=None;parent=None;latest=None
        with tempfile.TemporaryDirectory(prefix='hugin-ole-fixture-') as folder:
            control=Path(folder)
            try:
                with backend._opened():
                    if not set(backend._format_ids())<={1,7,13,16}:
                        self.fail('initial clipboard must contain only disposable plain text')
                original=backend.snapshot(MAX_SNAPSHOT_BYTES)
                self.assertTrue({identity for identity,_ in original.formats}<={1,7,13,16},
                                'initial snapshot must contain only disposable plain text')
                fixture=Path(__file__).with_name('_ole_raster_fixture.ps1')
                powershell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
                owner=OwnedProcess([str(powershell),'-NoProfile','-NonInteractive','-STA','-File',
                    str(fixture),'-ControlDirectory',str(control),'-ExpectedSequence',str(original.sequence)],stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,memory_limit=512*1024*1024)
                ready=json.loads(self.wait_file(control/'ready',owner));latest=ready['sequence']
                reads=[];get_data=backend.user.GetClipboardData
                def recorded_get_data(identity):
                    handle=get_data(identity)
                    error=C.get_last_error()
                    reads.append((identity,bool(handle),backend.kernel.GlobalSize(handle) if handle else 0,
                                  backend.sequence()==latest,error))
                    return handle
                backend.user.GetClipboardData=recorded_get_data
                try:image=backend.snapshot(MAX_SNAPSHOT_BYTES)
                except Exception as error:
                    trace=(control/'trace').read_text() if (control/'trace').exists() else 'no provider GetData calls'
                    code=owner.poll()
                    stderr=owner.stderr.read(4096).decode('utf-8',errors='replace') if code is not None else ''
                    raise AssertionError(f'synthetic materialization failed: {reads}; provider_exit={code}; {trace}; {stderr}') from error
                finally:backend.user.GetClipboardData=get_data
                self.assertEqual(image.sequence,latest,'clipboard changed after fixture publication')
                payload=dict(image.formats);png=backend.registered['PNG']
                self.assertEqual(hashlib.sha256(payload[png]).hexdigest(),ready['png_sha256'])
                for name,expected in (('CanUploadToCloudClipboard',b'\0'*4),
                                      ('CanIncludeInClipboardHistory',b'\1\0\0\0')):
                    self.assertEqual(payload[backend.registered[name]][:4],expected)
                self.assertTrue({8,17}<=payload.keys())
                self.assertFalse({2,backend.registered['DataObject'],backend.registered['Ole Private Data']}&payload.keys())
                self.assertEqual(dict(backend.snapshot(MAX_SNAPSHOT_BYTES).formats),payload)

                # WM_PASTE targets only this fixture's own hidden RichEdit child.
                # No foreground changes, SendInput, or user's application input.
                rich_edit=C.WinDLL('Msftedit.dll')
                parent=backend.user.CreateWindowExW(0,'STATIC','',0,0,0,120,30,None,None,None,None)
                self.assertTrue(parent)
                edit=backend.user.CreateWindowExW(0,'RICHEDIT50W','',0x40000004,0,0,120,30,parent,None,None,None)
                self.assertTrue(edit)
                backend.user.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
                backend.user.SendMessageW.restype=C.c_ssize_t
                backend.user.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
                backend.user.GetWindowTextW.restype=C.c_int
                backend.user.SetWindowTextW.argtypes=[W.HWND,W.LPCWSTR]
                backend.user.SetWindowTextW.restype=W.BOOL
                self.assertTrue(backend.user.SetWindowTextW(edit,'Synthetic selection'))
                value=C.create_unicode_buffer(100);backend.user.GetWindowTextW(edit,value,len(value))
                self.assertEqual(value.value,'Synthetic selection')
                backend.user.SendMessageW(edit,0xb1,0,-1)
                text='Hugin Rasterprobe Ä 😀'
                latest=backend.stage(((13,(text+'\0').encode('utf-16-le')),),image.sequence)
                with backend._opened():
                    h=get_data(13);self.assertTrue(h)
                    self.assertEqual(backend._read_handle(h,backend.kernel.GlobalSize(h)).decode('utf-16-le').rstrip('\0'),text)
                backend.user.SendMessageW(edit,0x302,0,0)
                value=C.create_unicode_buffer(100);backend.user.GetWindowTextW(edit,value,len(value))
                self.assertEqual(value.value,text)
                latest=backend.replace(image.formats,latest)
                self.assertEqual(dict(backend.snapshot(MAX_SNAPSHOT_BYTES).formats),payload)
                (control/'read').write_text(str(latest),encoding='ascii')
                self.assertEqual(self.wait_file(control/'result',owner),ready['png_sha256'])
            finally:
                try:
                    # Delayed rendering may change the sequence. Only the live
                    # provider's exact OleIsCurrentClipboard proof can renew
                    # cleanup authority; a captured foreign snapshot cannot.
                    if latest is not None and backend.sequence()!=latest and owner and owner.poll() is None:
                        (control/'ownership').write_text('prove',encoding='ascii')
                        owned=int(self.wait_file(control/'owned',owner,timeout=2))
                        if owned:latest=owned
                    # Never overwrite a later user copy, including test failures.
                    if latest is not None and backend.sequence()==latest:
                        restored=backend.replace(original.formats,latest)
                        final=backend.snapshot(MAX_SNAPSHOT_BYTES)
                        self.assertEqual(final.sequence,restored)
                        self.assertEqual(final.formats,original.formats)
                finally:
                    try:
                        if edit:backend.user.DestroyWindow(edit)
                        if parent:backend.user.DestroyWindow(parent)
                        (control/'stop').write_text('stop',encoding='ascii')
                        if owner:
                            try:owner.wait(timeout=5)
                            finally:
                                if owner.poll() is None:owner.kill();owner.wait(timeout=5)
                                owner.close()
                    finally:backend.close()


if __name__=='__main__':unittest.main()
