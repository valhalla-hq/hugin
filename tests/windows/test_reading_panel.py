"""Own synthetic windows and silent native PCM only; no clipboard or hooks."""
import ctypes as ct
import os
import sys
import time
import unittest
from dataclasses import replace

from hugin.ui import HuginWindow,View
from hugin.audio import PCMOutput
from hugin.reading_ui import panel_geometry


@unittest.skipUnless(sys.platform=='win32' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
                     'Explicit isolated native test required')
class ReadingPanelNative(unittest.TestCase):
    def test_panel_show_update_hide_preserve_owned_foreground_and_clear_text(self):
        calls=[]
        window=HuginWindow(lambda *args:calls.append(args),with_tray=False)
        self.addCleanup(window.stop)
        window.show();window.root.update()
        user=ct.WinDLL('user32')
        user.GetAncestor.argtypes=[ct.c_void_p,ct.c_uint];user.GetAncestor.restype=ct.c_void_p
        user.SetForegroundWindow.argtypes=[ct.c_void_p];user.SetForegroundWindow.restype=ct.c_int
        user.GetForegroundWindow.argtypes=[];user.GetForegroundWindow.restype=ct.c_void_p
        owned=user.GetAncestor(window.root.winfo_id(),2)
        self.assertTrue(user.SetForegroundWindow(owned))
        before=user.GetForegroundWindow();self.assertEqual(before,owned)
        view=View(status='Vorlesen läuft',activity='playing',active_action='reading',
            reading_job='synthetic-job',reading_text='Ein synthetischer Abschnitt zum Mitlesen. '*8,
            reading_index=1,reading_total=3)
        window.render(view);window.root.update()
        panel=window.reading_panel
        self.assertTrue(panel._shown)
        self.assertEqual(user.GetForegroundWindow(),before)
        self.assertEqual(panel.text.get('1.0','end-1c'),view.reading_text)
        panel.pause.invoke();self.assertEqual(calls[-1],('read_pause','synthetic-job'))
        window.render(replace(view,reading_paused=True));window.root.update()
        self.assertEqual(panel.pause.cget('text'),'Fortsetzen')
        self.assertEqual(window.read_pause.cget('text'),'Fortsetzen')
        self.assertEqual(user.GetForegroundWindow(),before)
        for control in panel.buttons:
            self.assertLessEqual(control.winfo_rootx()+control.winfo_width(),panel.window.winfo_rootx()+panel.window.winfo_width())
            self.assertLessEqual(control.winfo_rooty()+control.winfo_height(),panel.window.winfo_rooty()+panel.window.winfo_height())
        panel.hide.invoke();window.root.update()
        self.assertFalse(panel._shown);self.assertEqual(panel.text.get('1.0','end-1c'),'')
        self.assertEqual(len(calls),1,'hide is presentation only')
        window.read_pause.invoke();self.assertEqual(calls[-1],('read_pause','synthetic-job'))
        window.reading_panel_enabled.set(True);window._reading_visibility();window.root.update()
        self.assertTrue(panel._shown);self.assertEqual(user.GetForegroundWindow(),before)
        window.render(View());window.root.update()
        self.assertFalse(panel._shown);self.assertEqual(panel.text.get('1.0','end-1c'),'')
        self.assertEqual(panel._job,'');self.assertIsNone(panel._view)

    def test_native_silent_pause_preserves_queue_then_resumes(self):
        output=PCMOutput(buffer_ms=250)
        self.addCleanup(output.close)
        output.start('synthetic-silence')
        self.assertTrue(output.write(b'\0'*12000,'synthetic-silence'))
        self.assertTrue(output.pause('synthetic-silence',True))
        output._player.collect();held=output._player.queued_bytes
        self.assertGreater(held,0)
        time.sleep(.18);output._player.collect()
        self.assertEqual(output._player.queued_bytes,held)
        self.assertTrue(output.pause('synthetic-silence',False))
        deadline=time.monotonic()+2
        self.assertTrue(output.drain('synthetic-silence',lambda:time.monotonic()>deadline))


class ReadingGeometry(unittest.TestCase):
    def test_negative_monitor_and_high_dpi_fit_actual_work_area(self):
        for work in ((0,0,1920,1040),(-1920,0,0,1040),(0,-1080,1920,-40),(0,0,1280,680)):
            for scale in (1,1.5,2,4):
                x,y,w,h=panel_geometry(work,scale)
                self.assertGreaterEqual(x,work[0]);self.assertGreaterEqual(y,work[1])
                self.assertLessEqual(x+w,work[2]);self.assertLessEqual(y+h,work[3])
