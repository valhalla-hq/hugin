"""Owned hidden Tk widgets only; no foreground or input manipulation."""
from dataclasses import replace
import os
import unittest
from unittest.mock import patch

from hugin.ui import HuginWindow,View


@unittest.skipUnless(os.name=='nt' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
                     'explicit owned hidden Tk fixture required')
class WordHighlightingNative(unittest.TestCase):
    def setUp(self):
        window=HuginWindow(lambda *_:None,with_tray=False)
        self.addCleanup(window.stop)
        self.root=window.root;self.panel=window.reading_panel
        # Retain the real non-activation styles on both owned wrappers; replace
        # only placement/show so these fixtures remain fully withdrawn.
        from hugin.windows.reading_panel import PanelPlacement
        protection=PanelPlacement(self.panel.window)
        self.addCleanup(protection.close)
        self.panel._placement=type('HiddenPlacement',(),{
            'work_area':lambda *args:(0,0,1280,800),'show':lambda *args,**kwargs:None,
            'close':lambda *args:None})()
        self.view=View(reading_job='first',reading_index=1,reading_total=2,
            reading_text='😀 Alpha\nNoch 😀 Bravo Ende.',reading_marking='aligned',reading_word=(2,7),
            activity='playing')

    def marked(self):
        ranges=self.panel.text.tag_ranges('reading_word')
        return self.panel.text.get(*ranges) if ranges else ''

    def test_astral_original_offsets_and_follow_only_when_word_changes(self):
        panel=self.panel
        with patch.object(panel.text,'see',wraps=panel.text.see) as see, \
                patch.object(panel,'_set_text',wraps=panel._set_text) as rebuild:
            panel.render(self.view,True)
            self.assertEqual(self.marked(),'Alpha')
            panel.render(replace(self.view,reading_paused=True),True)
            self.assertEqual(self.marked(),'Alpha');self.assertEqual(see.call_count,1)
            start=self.view.reading_text.index('Bravo')
            panel.render(replace(self.view,reading_word=(start,start+5)),True)
            self.assertEqual(self.marked(),'Bravo');self.assertEqual(see.call_count,2)
            self.assertEqual(rebuild.call_count,1)
            self.assertEqual(panel.text.get('1.0','end-1c'),self.view.reading_text)

    def test_hide_reopen_same_text_new_job_and_section_remove_stale_word(self):
        panel=self.panel;panel.render(self.view,True)
        panel.render(self.view,False);self.assertEqual(self.marked(),'')
        self.assertEqual(panel.text.get('1.0','end-1c'),'')
        with patch.object(panel,'_set_text',wraps=panel._set_text) as rebuild:
            panel.render(replace(self.view,reading_word=(8,12)),False)
            self.assertEqual(rebuild.call_count,0,'hidden progress must not rebuild empty text')
        panel.render(self.view,True);self.assertEqual(self.marked(),'Alpha')
        panel.render(replace(self.view,reading_job='new',reading_word=None),True)
        self.assertEqual(self.marked(),'')
        panel.render(self.view,True)
        panel.render(replace(self.view,reading_index=2,reading_word=None),True)
        self.assertEqual(self.marked(),'')
        panel.render(View(),True);self.assertEqual(self.marked(),'')

    def test_current_word_keeps_native_glyph_advances_at_each_panel_scale(self):
        from tkinter.font import Font
        panel=self.panel
        view=replace(self.view,reading_text='Das aktuelle Wort bleibt stehen.',reading_word=(4,12))
        panel.render(view,True)
        for work in ((0,0,1280,800),(0,0,450,300)):
            with self.subTest(work=work):
                panel._fit(work)
                normal=Font(root=self.root,font=panel.text.cget('font'))
                active=Font(root=self.root,font=panel.text.tag_cget('reading_word','font') or
                            panel.text.cget('font'))
                word=self.marked()
                self.assertEqual(word,'aktuelle')
                self.assertEqual([active.measure(word[:index]) for index in range(1,len(word)+1)],
                                 [normal.measure(word[:index]) for index in range(1,len(word)+1)],
                                 'marking must not move following glyphs or change wrapping')
                self.assertEqual(active.metrics('linespace'),normal.metrics('linespace'))

    def test_preparing_unavailable_and_invalid_spans_never_invent_mark(self):
        panel=self.panel
        panel.render(replace(self.view,reading_marking='preparing',reading_word=None),True)
        self.assertIn('Wörter werden zugeordnet',panel.scene.itemcget(panel._heading,'text'))
        for marking,span in (('device_position_unavailable',None),('aligned',(-1,5)),
                             ('aligned',(True,7)),('aligned',(2,999))):
            panel.render(replace(self.view,reading_marking=marking,reading_word=span),True)
            self.assertEqual(self.marked(),'')
            self.assertIn('Wortmarkierung nicht verfügbar',panel.scene.itemcget(panel._heading,'text'))

    def test_word_only_view_updates_panel_without_reconfiguring_main_controls(self):
        window=HuginWindow(lambda *_:None,with_tray=False)
        self.addCleanup(window.stop)
        window.reading_panel._placement=self.panel._placement
        window.render(self.view)
        start=self.view.reading_text.index('Bravo')
        with patch.object(window.copy,'configure',wraps=window.copy.configure) as controls:
            window.render(replace(self.view,reading_word=(start,start+5)))
            self.assertEqual(controls.call_count,0)
        ranges=window.reading_panel.text.tag_ranges('reading_word')
        self.assertEqual(window.reading_panel.text.get(*ranges),'Bravo')

    def test_follow_moves_text_view_without_opening_or_activating_window(self):
        import ctypes as ct
        user=ct.WinDLL('user32');user.GetForegroundWindow.restype=ct.c_void_p
        user.GetAncestor.argtypes=[ct.c_void_p,ct.c_uint];user.GetAncestor.restype=ct.c_void_p
        text='\n'.join(f'Zeile {number} Wort' for number in range(80))
        view=replace(self.view,reading_text=text,reading_word=(0,5))
        self.panel.render(view,True);self.root.update_idletasks()
        before=self.panel.text.yview()[0]
        start=text.rindex('Wort')
        self.panel.render(replace(view,reading_word=(start,start+4)),True)
        self.root.update_idletasks()
        self.assertGreater(self.panel.text.yview()[0],before)
        self.assertEqual(self.marked(),'Wort')
        self.assertEqual(self.panel.window.state(),'withdrawn')
        # Human foreground changes elsewhere are allowed; neither owned hidden
        # wrapper may activate as a consequence of following the word.
        self.assertNotIn(user.GetForegroundWindow(),{
            user.GetAncestor(self.root.winfo_id(),2),
            user.GetAncestor(self.panel.window.winfo_id(),2)})

