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
            if widget.winfo_class() not in ('TButton','Button','Checkbutton','TCombobox','TLabel','Label','Text'):continue
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
        for name in ('dictation','reading'):
            card=window.scene.bbox(window._items[name])
            for suffix in ('_title','_key'):
                bounds=window.scene.bbox(window._labels[name+suffix])
                self.assertGreaterEqual(bounds[0],card[0])
                self.assertGreaterEqual(bounds[1],card[1])
                self.assertLessEqual(bounds[2],card[2])
                self.assertLessEqual(bounds[3],card[3])

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

    def test_voice_controls_and_disabled_text_keep_dark_readable_colors(self):
        window=self.make_window()
        window.render(View(text='Synthetische Textauswahl'))
        style=ttk.Style(window.root)
        self.assertEqual(style.theme_use(),'clam')
        self.assertEqual(window.root.cget('background'),BACKGROUND)
        for button in window.voice_buttons.values():
            self.assertEqual(button.cget('foreground'),TEXT)
            self.assertTrue(button.cget('takefocus'))
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
        self.assertEqual(window.scene.itemcget(window._labels['mode'],'text'),'CPU · Lokal')
        self.assertEqual(window.scene.itemcget(window._labels['status'],'text'),'Aufnahme')
        self.assertTrue(window.voice_buttons['tyr']._selected)
        self.assertEqual(window.text.get('1.0','end-1c'),'Synthetischer Inhalt')
        window.copy.invoke();window.clear.invoke()
        window.diagnose.invoke()
        window.voice_buttons['freya'].invoke()
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

    def test_mode_tiles_switch_without_layout_or_growing_images(self):
        window=self.make_window();window.show();window.root.update()
        def images():
            return tuple(window.scene.itemcget(window._items[name],'image')
                         for name in ('dictation','reading'))
        window.render(View(activity='idle'))
        idle=images();count=len(window.root.tk.call('image','names'))
        for _ in range(3):
            window.render(View(activity='recording',active_action='dictation'))
            recording=images()
            self.assertNotEqual(recording[0],idle[0])
            self.assertEqual(recording[1],idle[1])
            window.render(View(activity='playing',active_action='reading'))
            reading=images()
            self.assertEqual(reading[0],idle[0])
            self.assertNotEqual(reading[1],idle[1])
            window.render(View(activity='idle'))
            self.assertEqual(images(),idle)
        self.assertEqual(len(window.root.tk.call('image','names')),count)

    def test_voice_button_corners_match_parent_even_during_hover_and_focus(self):
        from PIL import ImageTk
        for scale in (1,1.5,2):
            window=self.make_window(scale);window.show();window.root.update()
            parent=ImageTk.getimage(window._images['voices'])
            card=window.scene.coords(window._items['voices'])
            for name,button in window.voice_buttons.items():
                at=window.scene.coords(window._windows[name])
                offset=(round(at[0]-card[0]),round(at[1]-card[1]))
                for focused in (False,True):
                    button._focus_changed(focused)
                    button._pointer(hover=True);button.step(immediate=True)
                    frame=ImageTk.getimage(button._shown_image)
                    for x,y in ((0,0),(frame.width-1,0),(0,frame.height-1),
                                (frame.width-1,frame.height-1)):
                        self.assertEqual(frame.getpixel((x,y)),parent.getpixel((offset[0]+x,offset[1]+y)))
                self.assertEqual(int(button.cget('highlightthickness')),0)
            self.close_window(window)


if __name__=='__main__':unittest.main()
