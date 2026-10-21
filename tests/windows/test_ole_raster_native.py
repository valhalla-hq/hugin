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
        backend=NativeClipboard();owner=None;edit=None;latest=None
        with tempfile.TemporaryDirectory(prefix='hugin-ole-fixture-') as folder:
            control=Path(folder)
            try:
                # A user image or unsupported initial object is never replaced
                # merely to run this fixture. Ask for a disposable plain-text copy.
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
                    reads.append((identity,bool(handle),backend.kernel.GlobalSize(handle) if handle else 0,
                                  backend.sequence()==latest))
                    return handle
                backend.user.GetClipboardData=recorded_get_data
                try:image=backend.snapshot(MAX_SNAPSHOT_BYTES)
                except Exception as error:
                    trace=(control/'trace').read_text() if (control/'trace').exists() else 'no provider GetData calls'
                    raise AssertionError(f'synthetic materialization failed: {reads}; {trace}') from error
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

                # WM_PASTE targets only this fixture's own message-only Edit.
                # No foreground changes, SendInput, or user's application input.
                edit=backend.user.CreateWindowExW(0,'EDIT','',4,0,0,120,30,-3,None,None,None)
                self.assertTrue(edit)
                backend.user.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
                backend.user.SendMessageW.restype=C.c_ssize_t
                backend.user.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
                backend.user.GetWindowTextW.restype=C.c_int
                text='Hugin Rasterprobe Ä 😀'
                latest=backend.stage(((13,(text+'\0').encode('utf-16-le')),),image.sequence)
                backend.user.SendMessageW(edit,0x302,0,0)
                value=C.create_unicode_buffer(100);backend.user.GetWindowTextW(edit,value,len(value))
                self.assertEqual(value.value,text)
                latest=backend.replace(image.formats,latest)
                self.assertEqual(dict(backend.snapshot(MAX_SNAPSHOT_BYTES).formats),payload)
                (control/'read').write_text(str(latest),encoding='ascii')
                self.assertEqual(self.wait_file(control/'result',owner),ready['png_sha256'])
            finally:
                try:
                    # Never overwrite a later user copy, including test failures.
                    if latest is not None and backend.sequence()==latest:
                        backend.replace(original.formats,latest)
                finally:
                    if edit:backend.user.DestroyWindow(edit)
                    (control/'stop').write_text('stop',encoding='ascii')
                    if owner:
                        try:owner.wait(timeout=5)
                        finally:
                            if owner.poll() is None:owner.kill();owner.wait(timeout=5)
                            owner.close()
                    backend.close()


if __name__=='__main__':unittest.main()
