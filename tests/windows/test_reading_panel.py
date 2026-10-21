"""Own synthetic windows and silent native PCM only; no clipboard or hooks."""
import ctypes as ct
import os
import sys
import time
import unittest
from unittest.mock import patch
from dataclasses import replace

from hugin.ui import HuginWindow,View
from hugin.audio import PCMOutput
from hugin.reading_ui import panel_geometry


@unittest.skipUnless(sys.platform=='win32' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
                     'Explicit isolated native test required')
class ReadingPanelNative(unittest.TestCase):
    def test_failed_region_transfer_and_delete_keep_owner_until_window_cleanup(self):
        from hugin.windows.reading_panel import PanelPlacement
        window=HuginWindow(lambda *args:None,with_tray=False)
        self.addCleanup(window.stop)
        placement=PanelPlacement(window.reading_panel.window)
        window.reading_panel._placement=placement
        with patch.object(placement.api,'SetWindowRgn',return_value=0), \
                patch.object(placement.gdi,'DeleteObject',return_value=0):
            window.render(View(reading_job='region-fixture',reading_text='Synthetisch'))
            self.assertIsNotNone(placement._region)
            self.assertFalse(window.reading_panel._shown)
            self.assertEqual(str(window.read_stop['state']),'normal')
            with self.assertRaises(OSError):window.stop()
            self.assertFalse(window._closed)
            self.assertIsNotNone(placement._region)
        window.stop()
        self.assertIsNone(placement._region)
        self.assertTrue(window._closed)

    def test_header_drag_remembers_position_and_rounded_window_without_audio_actions(self):
        calls=[]
        window=HuginWindow(lambda *args:calls.append(args),with_tray=False)
        self.addCleanup(window.stop)
        window.show();window.root.update()
        view=View(reading_job='moving-fixture',reading_text='Nur synthetischer Text.',
                  reading_index=1,reading_total=2)
        window.render(view);window.root.update()
        panel=window.reading_panel
        user=panel._placement.api
        user.SetForegroundWindow.argtypes=[ct.c_void_p];user.SetForegroundWindow.restype=ct.c_int
        owned=user.GetAncestor(window.root.winfo_id(),2)
        self.assertTrue(user.SetForegroundWindow(owned))
        foreground=user.GetForegroundWindow()
        self.assertEqual(foreground,owned)
        x,y=panel.window.winfo_x(),panel.window.winfo_y()
        work=panel._placement.work_area()
        target=(work[0]+40,work[1]+60)
        panel.scene.event_generate('<ButtonPress-1>',x=25,y=20,rootx=x+25,rooty=y+20)
        panel.scene.event_generate('<B1-Motion>',x=25,y=20,rootx=target[0]+25,rooty=target[1]+20)
        panel.scene.event_generate('<ButtonRelease-1>',x=25,y=20,rootx=target[0]+25,rooty=target[1]+20)
        window.root.update()
        self.assertEqual((panel.window.winfo_x(),panel.window.winfo_y()),target)
        self.assertEqual(user.GetForegroundWindow(),foreground)
        # Native region excludes the square corner, but contains the text center.
        gdi=ct.WinDLL('gdi32')
        gdi.CreateRectRgn.argtypes=[ct.c_int]*4;gdi.CreateRectRgn.restype=ct.c_void_p
        gdi.DeleteObject.argtypes=[ct.c_void_p];gdi.DeleteObject.restype=ct.c_int
        gdi.PtInRegion.argtypes=[ct.c_void_p,ct.c_int,ct.c_int];gdi.PtInRegion.restype=ct.c_int
        user.GetWindowRgn.argtypes=[ct.c_void_p,ct.c_void_p];user.GetWindowRgn.restype=ct.c_int
        region=gdi.CreateRectRgn(0,0,0,0)
        try:
            self.assertTrue(user.GetWindowRgn(panel._placement.hwnd,region))
            self.assertFalse(gdi.PtInRegion(region,0,0))
            self.assertTrue(gdi.PtInRegion(region,100,100))
        finally:gdi.DeleteObject(region)
        panel.hide.invoke();window.render(View())
        window.render(replace(view,reading_job='next-fixture',reading_text='Neuer Abschnitt.'))
        with patch.object(panel._placement,'work_area',wraps=panel._placement.work_area) as area:
            window.reading_toggle.invoke();window.root.update()
        self.assertIsNotNone(area.call_args.args[0],'remembered rectangle selects the monitor')
        self.assertEqual((panel.window.winfo_x(),panel.window.winfo_y()),target)
        self.assertEqual(panel.text.get('1.0','end-1c'),'Neuer Abschnitt.')
        self.assertEqual(calls,[])
        self.assertEqual(user.GetForegroundWindow(),foreground)
        # Failure during an optional move cannot disable speech/main controls.
        with patch.object(panel._placement,'move',side_effect=OSError('synthetic')):
            panel.scene.event_generate('<ButtonPress-1>',x=25,y=20,rootx=target[0]+25,rooty=target[1]+20)
            panel.scene.event_generate('<B1-Motion>',x=25,y=20,rootx=target[0]+50,rooty=target[1]+20)
        self.assertFalse(panel._shown)
        self.assertIsNone(panel._drag)
        self.assertEqual(panel.text.get('1.0','end-1c'),'')
        self.assertEqual(str(window.read_pause['state']),'normal')
        self.assertIsNone(window.failure)

    def test_optional_panel_show_failure_keeps_main_controls_and_reading_available(self):
        window=HuginWindow(lambda *args:None,with_tray=False)
        self.addCleanup(window.stop)
        with patch('hugin.windows.reading_panel.PanelPlacement.show',side_effect=OSError('synthetic')):
            window.render(View(reading_job='fixture',reading_text='Synthetisch',reading_index=1,reading_total=1))
        self.assertIsNone(window.failure)
        self.assertFalse(window.reading_panel_enabled)
        self.assertFalse(window.reading_panel._shown)
        self.assertEqual(window.reading_panel.text.get('1.0','end-1c'),'')
        self.assertEqual(str(window.read_pause['state']),'normal')
        self.assertEqual(str(window.reading_toggle['state']),'disabled')

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
        # Synthetic small work area after a larger/high-DPI main display.
        panel.scale=4
        panel._placement.show(*panel._fit((0,0,680,480)));window.root.update()
        for control in panel.buttons:
            self.assertLessEqual(control.winfo_rootx()+control.winfo_width(),panel.window.winfo_rootx()+panel.window.winfo_width())
            self.assertLessEqual(control.winfo_rooty()+control.winfo_height(),panel.window.winfo_rooty()+panel.window.winfo_height())
        panel.hide.invoke();window.root.update()
        self.assertFalse(panel._shown);self.assertEqual(panel.text.get('1.0','end-1c'),'')
        self.assertEqual(window.reading_toggle.winfo_class(),'Button')
        self.assertEqual(window.reading_toggle.cget('text'),'Mitleseleiste einblenden')
        self.assertEqual(len(calls),1,'hide is presentation only')
        window.read_pause.invoke();self.assertEqual(calls[-1],('read_pause','synthetic-job'))
        window.reading_toggle.invoke();window.root.update()
        self.assertTrue(panel._shown);self.assertEqual(user.GetForegroundWindow(),before)
        self.assertEqual(window.reading_toggle.cget('text'),'Mitleseleiste ausblenden')
        self.assertEqual(panel.pause.cget('text'),'Fortsetzen')
        window.reading_toggle.invoke();window.root.update()
        self.assertFalse(panel._shown)
        window.render(View());window.root.update()
        self.assertFalse(panel._shown);self.assertEqual(panel.text.get('1.0','end-1c'),'')
        self.assertEqual(panel._job,'');self.assertIsNone(panel._view)
        next_view=replace(view,reading_job='next-synthetic-job',reading_text='Ein neuer Abschnitt.')
        window.render(next_view);window.root.update()
        self.assertFalse(panel._shown,'hidden preference survives a new reading job')
        self.assertEqual(panel.text.get('1.0','end-1c'),'')
        window.reading_toggle.invoke();window.root.update()
        self.assertTrue(panel._shown);self.assertEqual(user.GetForegroundWindow(),before)
        self.assertEqual(panel.text.get('1.0','end-1c'),next_view.reading_text)
        panel.pause.invoke();self.assertEqual(calls[-1],('read_pause','next-synthetic-job'))

    def test_panel_can_show_while_main_is_hidden_without_activating_it(self):
        import tkinter as tk
        window=HuginWindow(lambda *args:None,with_tray=False)
        self.addCleanup(window.stop)
        fixture=tk.Toplevel(window.root);fixture.title('Owned focus fixture')
        fixture.geometry('320x120+40+40');fixture.update()
        user=ct.WinDLL('user32')
        user.GetAncestor.argtypes=[ct.c_void_p,ct.c_uint];user.GetAncestor.restype=ct.c_void_p
        user.SetForegroundWindow.argtypes=[ct.c_void_p];user.SetForegroundWindow.restype=ct.c_int
        user.GetForegroundWindow.argtypes=[];user.GetForegroundWindow.restype=ct.c_void_p
        owned=user.GetAncestor(fixture.winfo_id(),2)
        self.assertTrue(user.SetForegroundWindow(owned))
        window.render(View(reading_job='fixture',reading_total=2))
        window.root.update()
        self.assertEqual(window.root.state(),'withdrawn')
        self.assertTrue(window.reading_panel._shown)
        self.assertEqual(user.GetForegroundWindow(),owned)
        self.assertEqual(str(window.reading_panel.pause['state']),'disabled')

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
    def test_remembered_negative_position_and_removed_monitor_are_clamped(self):
        self.assertEqual(panel_geometry((-1920,-100,0,980),1,(-1800,40))[:2],(-1800,40))
        x,y,w,h=panel_geometry((0,0,1280,680),2,(-1800,4000))
        self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
        self.assertLessEqual(x+w,1280);self.assertLessEqual(y+h,680)

    def test_negative_monitor_and_high_dpi_fit_actual_work_area(self):
        for work in ((0,0,1920,1040),(-1920,0,0,1040),(0,-1080,1920,-40),(0,0,1280,680)):
            for scale in (1,1.5,2,4):
                x,y,w,h=panel_geometry(work,scale)
                self.assertGreaterEqual(x,work[0]);self.assertGreaterEqual(y,work[1])
                self.assertLessEqual(x+w,work[2]);self.assertLessEqual(y+h,work[3])
