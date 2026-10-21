"""Owned native windows only; no hooks, clipboard, audio or engines."""
import ctypes as ct
import os
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

from hugin.ui import HuginWindow,View


@unittest.skipUnless(sys.platform=='win32' and os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1',
                     'Explicit owned native UI test required')
class NativePanelActions(unittest.TestCase):
    def make_window(self,calls):
        window=HuginWindow(lambda *args:calls.append(args),with_tray=False)
        self.addCleanup(window.stop)
        window.render(View(activity='idle',panel_token=(0,'IDLE'),
            dictation_control='start',reading_control='start'))
        window.show();window.root.update()
        return window

    def test_button_mouse_activation_is_suppressed_but_normal_controls_keep_activation(self):
        calls=[];window=self.make_window(calls)
        user=ct.WinDLL('user32')
        user.SendMessageW.argtypes=[ct.c_void_p,ct.c_uint,ct.c_size_t,ct.c_ssize_t]
        user.SendMessageW.restype=ct.c_ssize_t
        user.GetAncestor.argtypes=[ct.c_void_p,ct.c_uint];user.GetAncestor.restype=ct.c_void_p
        top=user.GetAncestor(window.root.winfo_id(),2)
        for button in (window.dictation_button,window.read_action):
            self.assertEqual(user.SendMessageW(button.winfo_id(),0x21,top,0x2010001),3)
        self.assertNotEqual(user.SendMessageW(window.copy.winfo_id(),0x21,top,0x2010001),3)
        window.dictation_button.invoke()
        self.assertEqual(calls,[('panel_dictation',(0,'IDLE'))])
        # An activating click into Hugin must never cause a remembered-target read.
        with patch.object(window._action_focus,'external_target',return_value=False):
            window.read_action.invoke()
        self.assertEqual(len(calls),1)
        self.assertIn('markieren',window.scene.itemcget(window._labels['detail'],'text'))

    def test_finish_without_external_focus_still_stops_recording(self):
        calls=[];window=self.make_window(calls)
        window.render(View(activity='recording',active_action='dictation',
            panel_token=(1,'RECORDING'),dictation_control='finish'))
        with patch.object(window._action_focus,'external_target',return_value=False):
            window.dictation_button.invoke()
        self.assertEqual(calls,[('panel_dictation',(1,'RECORDING'))])
        self.assertEqual(window.dictation_button.cget('text'),'Fertig & einfügen')
        calls.clear()
        with patch.object(window._action_focus,'external_target',return_value=True):
            window.dictation_button.invoke()
        self.assertEqual(calls,[('panel_dictation',(1,'RECORDING'))])

    def test_failed_native_detach_retains_owner_for_stop_retry(self):
        window=self.make_window([]);owner=window._action_focus
        before=set(owner.handles)
        with patch.object(owner.api,'RemoveWindowSubclass',return_value=0):
            with self.assertRaises(OSError):window.stop()
        self.assertEqual(owner.handles,before)
        self.assertFalse(window._closed)
        window.stop()
        self.assertFalse(owner.handles)

    def test_top_level_protection_survives_show_and_ordinary_click_activates_hugin(self):
        window=self.make_window([]);owner=window._action_focus;user=owner.user
        top=owner._top
        self.assertEqual(top,user.GetAncestor(window.root.winfo_id(),2))
        mask=0x08000000|0x00040000
        self.assertEqual(user.GetWindowLongPtrW(top,-20)&mask,mask)
        window.hide();window.show();window.root.update()
        self.assertEqual(user.GetWindowLongPtrW(top,-20)&mask,mask)
        fixture=tk.Toplevel(window.root);entry=tk.Entry(fixture);entry.pack()
        fixture.update();source=user.GetAncestor(fixture.winfo_id(),2)
        self.assertTrue(user.SetForegroundWindow(source));entry.focus_force();window.root.update()
        self.assertEqual(user.GetForegroundWindow(),source)
        user.SendMessageW.argtypes=[ct.c_void_p,ct.c_uint,ct.c_size_t,ct.c_ssize_t]
        user.SendMessageW.restype=ct.c_ssize_t
        # A normal child forwards mouse activation to our wrapper. Only Hugin
        # itself is activated; action buttons never reach this branch.
        user.SendMessageW(window.copy.winfo_id(),0x21,top,0x2010001)
        window.root.update()
        self.assertEqual(user.GetForegroundWindow(),top)

    def test_style_cleanup_failure_retains_native_owner_until_retry(self):
        window=self.make_window([]);owner=window._action_focus;top=owner._top
        with patch.object(owner,'_set_style',side_effect=OSError('style denied')):
            with self.assertRaises(OSError):window.stop()
        self.assertIn(top,owner.handles)
        self.assertEqual(owner._top,top)
        self.assertTrue(owner._added_style)
        self.assertFalse(window._closed)
        window.stop();self.assertFalse(owner.handles)

    def test_detach_restores_only_owned_style_bits_and_keyboard_button_still_invokes(self):
        calls=[];window=self.make_window(calls);owner=window._action_focus;top=owner._top
        style=owner._style(top);added=owner._added_style
        owner._set_style(top,style|0x10)  # Unrelated own-window accept-files bit.
        window.dictation_button.focus_force();window.root.update()
        window.dictation_button.event_generate('<Return>');window.root.update()
        self.assertEqual(calls,[('panel_dictation',(0,'IDLE'))])
        owner.close()
        self.assertEqual(owner._style(top),(style|0x10)&~added)
        self.assertFalse(owner.handles)

    def test_native_message_and_tk_click_bindings_keep_owned_selection_and_foreground(self):
        calls=[];window=self.make_window(calls)
        fixture=tk.Toplevel(window.root);fixture.title('Owned action source fixture')
        entry=tk.Entry(fixture);entry.pack();entry.insert(0,'synthetic selected words')
        fixture.update();entry.focus_force();entry.selection_range(0,9);window.root.update()
        user=window._action_focus.user
        user.GetAncestor.argtypes=[ct.c_void_p,ct.c_uint];user.GetAncestor.restype=ct.c_void_p
        user.SendMessageW.argtypes=[ct.c_void_p,ct.c_uint,ct.c_size_t,ct.c_ssize_t]
        user.SendMessageW.restype=ct.c_ssize_t
        self.assertTrue(user.SetForegroundWindow(user.GetAncestor(fixture.winfo_id(),2)))
        entry.focus_force();window.root.update()
        before=user.GetForegroundWindow()
        self.assertEqual(before,user.GetAncestor(fixture.winfo_id(),2))
        # Same-process synthetic source: bypass only the UX process filter.
        # Native activation decision and shipped Tk mouse bindings are real.
        with patch.object(window._action_focus,'external_target',return_value=True):
            button=window.read_action
            self.assertEqual(user.SendMessageW(button.winfo_id(),0x21,
                user.GetAncestor(window.root.winfo_id(),2),0x2010001),3)
            for event in ('<Enter>','<ButtonPress-1>','<ButtonRelease-1>'):
                button.event_generate(event,x=10,y=10)
                window.root.update()
        self.assertEqual(calls,[('panel_read',(0,'IDLE'))])
        self.assertEqual(user.GetForegroundWindow(),before)
        self.assertEqual(window.root.focus_get(),entry)
        self.assertEqual((entry.index('sel.first'),entry.index('sel.last')),(0,9))

    def test_destroyed_button_drops_native_registration_before_handle_reuse(self):
        window=self.make_window([]);owner=window._action_focus
        hwnd=window.dictation_button.winfo_id()
        self.assertIn(hwnd,owner.handles)
        window.dictation_button.destroy()
        self.assertNotIn(hwnd,owner.handles)

    def test_held_click_cannot_finish_recording_started_by_a_hotkey(self):
        calls=[];window=self.make_window(calls);button=window.dictation_button
        for event in ('<Enter>','<ButtonPress-1>'):
            button.event_generate(event,x=10,y=10)
        # Modifiers can arrive at an already keyboard-focused button while the
        # mouse is held. They must not erase the original mouse intent.
        button.focus_force();window.root.update()
        button.event_generate('<KeyPress-Control_L>');window.root.update()
        self.assertEqual(window._panel_intents['dictation'],(0,'IDLE'))
        window.render(View(activity='recording',active_action='dictation',
            panel_token=(1,'RECORDING'),dictation_control='finish'))
        window.root.update()
        with patch.object(window._action_focus,'external_target',return_value=True):
            button.event_generate('<ButtonRelease-1>',x=10,y=10);window.root.update()
        self.assertFalse(calls)
        self.assertFalse(window._panel_intents)
        # A fresh complete click still performs the current action.
        with patch.object(window._action_focus,'external_target',return_value=True):
            for event in ('<Enter>','<ButtonPress-1>','<ButtonRelease-1>'):
                button.event_generate(event,x=10,y=10);window.root.update()
        self.assertEqual(calls,[('panel_dictation',(1,'RECORDING'))])

    def test_held_read_stop_cannot_restart_naturally_finished_reading(self):
        calls=[];window=self.make_window(calls);button=window.read_action
        window.render(View(panel_token=(1,'TTS_PLAYING'),reading_control='stop'))
        window.root.update()
        for event in ('<Enter>','<ButtonPress-1>'):
            button.event_generate(event,x=10,y=10)
        window.render(View(panel_token=(1,'IDLE'),reading_control='start'))
        window.root.update()
        with patch.object(window._action_focus,'external_target',return_value=True):
            button.event_generate('<ButtonRelease-1>',x=10,y=10);window.root.update()
        self.assertFalse(calls)
        self.assertFalse(window._panel_intents)
