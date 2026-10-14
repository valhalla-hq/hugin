"""Own synthetic Tk windows only; no input hooks, clipboard, audio or engines."""
import os
import sys
import tkinter as tk
from tkinter import font,ttk
import unittest
from unittest.mock import patch

from hugin.branding import BACKGROUND,FIELD,TEXT,ACCENT,ACTIVITY_COLORS,hugin_icon
from hugin.ui import HuginWindow,View,tray_image


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


@unittest.skipUnless(sys.platform=='win32' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
                     'Explicit isolated native UI test required')
class NativeVisualContract(unittest.TestCase):
    def make_window(self,scale=1):
        original=tk.Tk
        def scaled_root(*args,**kwargs):
            root=original(*args,**kwargs)
            root.tk.call('tk','scaling',96*scale/72)
            fpixels=root.winfo_fpixels
            root.winfo_fpixels=lambda value:96*scale if value=='1i' else fpixels(value)
            root.winfo_screenheight=lambda:1080
            return root
        with patch('hugin.ui.tk.Tk',scaled_root):
            window=HuginWindow(lambda *args:None,with_tray=False)
        self.addCleanup(self.close_window,window)
        return window

    def close_window(self,window):
        for timer in window.root.tk.splitlist(window.root.tk.call('after','info')):
            window.root.after_cancel(timer)
        window.stop()

    def assert_visible_controls(self,window):
        window.root.update()
        for widget in descendants(window.root):
            if not widget.winfo_ismapped():continue
            if widget.winfo_class() not in ('TButton','TCombobox','TLabel','Label','Text'):continue
            with self.subTest(widget=str(widget)):
                parent=widget.master
                while parent is not None:
                    self.assertGreaterEqual(widget.winfo_rootx(),parent.winfo_rootx())
                    self.assertGreaterEqual(widget.winfo_rooty(),parent.winfo_rooty())
                    self.assertLessEqual(widget.winfo_rootx()+widget.winfo_width(),parent.winfo_rootx()+parent.winfo_width())
                    self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),parent.winfo_rooty()+parent.winfo_height())
                    parent=parent.master
        line_height=font.Font(root=window.root,font=window.text.cget('font')).metrics('linespace')
        self.assertGreaterEqual(window.text.winfo_height(),line_height+2*int(window.text.cget('pady'))+2)

    def test_three_dpi_scales_keep_text_and_actions_inside_their_cards(self):
        for scale in (1,1.5,2):
            with self.subTest(scale=scale):
                window=self.make_window(scale)
                window.render(View(status='Bereit',detail='Synthetische Ansicht · alles lokal',
                    text='Dieser Text ist ausschließlich eine Darstellungsprobe.',
                    components='Whisper · bereit    Qwen · bereit',
                    error='Synthetischer Diagnosehinweis: Der Prüfadapter meldet eine begrenzte Störung. Bitte erneut versuchen.',
                    dictation_shortcut='Strg+Alt+D · erneut: fertig',
                    reading_shortcut='Text markieren · Strg+Alt+V · erneut: Stopp'))
                window.show()
                self.assert_visible_controls(window)
                width,height=window.root.minsize()
                window.root.geometry(f'{width}x{height}')
                self.assert_visible_controls(window)
                self.close_window(window)

    def test_popup_and_disabled_text_keep_dark_readable_colors(self):
        window=self.make_window()
        window.render(View(text='Synthetische Textauswahl'))
        style=ttk.Style(window.root)
        self.assertEqual(style.theme_use(),'clam')
        self.assertEqual(window.root.cget('background'),BACKGROUND)
        self.assertEqual(style.lookup('TCombobox','fieldbackground',('readonly',)),FIELD)
        popup=window.root.tk.call('ttk::combobox::PopdownWindow',str(window.voice))
        listbox=str(popup)+'.f.l'
        for option,expected in (('-background',FIELD),('-foreground',TEXT),
                                ('-selectbackground',ACCENT),('-selectforeground',TEXT)):
            self.assertEqual(window.root.tk.call(listbox,'cget',option),expected)
        self.assertEqual(str(window.text.cget('state')),'disabled')
        self.assertEqual(window.text.cget('background'),FIELD)
        self.assertEqual(window.text.cget('foreground'),TEXT)
        self.assertEqual(window.text.cget('selectforeground'),TEXT)
        self.assertNotEqual(window.text.cget('selectbackground'),FIELD)
        self.assertNotEqual(window.text.cget('inactiveselectbackground'),FIELD)

    def test_existing_actions_and_controller_mode_remain_unchanged(self):
        window=self.make_window();actions=[]
        window.on_action=lambda *args:actions.append(args)
        window.render(View(status='Aufnahme',mode='CPU · Lokal',voice='tyr',
            text='Synthetischer Inhalt',activity='recording'))
        self.assertEqual(window.mode.cget('text'),'CPU · Lokal')
        self.assertEqual(window.status.cget('text'),'Aufnahme')
        self.assertEqual(window.voice.current(),1)
        self.assertEqual(window.text.get('1.0','end-1c'),'Synthetischer Inhalt')
        window.copy.invoke();window.clear.invoke()
        next(widget for widget in descendants(window.root)
             if widget.winfo_class()=='TButton' and widget.cget('text')=='Diagnose kopieren').invoke()
        window.voice.current(0);window.voice.event_generate('<<ComboboxSelected>>')
        self.assertEqual(actions,[('copy',None),('clear',None),('diagnose',None),('voice','freya')])
        window.render(View())
        self.assertEqual(str(window.copy.cget('state')),'disabled')
        self.assertEqual(str(window.clear.cget('state')),'disabled')
        self.assertEqual(window.root.state(),'withdrawn')

    def test_small_icons_share_raven_with_distinct_status_jewels(self):
        from PIL import ImageChops
        for size in (16,32,64,128):
            with self.subTest(size=size):
                icons=[hugin_icon(size,color) for color in ACTIVITY_COLORS.values()]
                self.assertTrue(all(icon.size==(size,size) and icon.mode=='RGBA' for icon in icons))
                self.assertEqual(len({icon.tobytes() for icon in icons}),len(ACTIVITY_COLORS))
                for icon in icons[1:]:
                    bounds=ImageChops.difference(icons[0],icon).convert('RGB').getbbox()
                    self.assertIsNotNone(bounds)
                    # LANCZOS can spread the tiny jewel by a few edge pixels.
                    self.assertGreaterEqual(bounds[0],size*.5)
                    self.assertGreaterEqual(bounds[1],size*.5)
                self.assertLessEqual(icons[0].getpixel((0,0))[3],2)
        self.assertEqual(tray_image().tobytes(),hugin_icon(64).tobytes())


if __name__=='__main__':unittest.main()
