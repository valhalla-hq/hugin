import os
import unittest
import weakref

from hugin.ui import HuginWindow,View


@unittest.skipUnless(os.environ.get('HUGIN_INTERACTIVE_TESTS')=='1','Explicit isolated UI test required')
class NativeWindowContract(unittest.TestCase):
    def setUp(self):
        self.window = HuginWindow(lambda kind,value:None,with_tray=False)

    def tearDown(self):
        # Tk's shared event queue can outlive a destroyed test root. Cancel
        # this fixture's callbacks before the next isolated root is created.
        for timer in self.window.root.tk.splitlist(self.window.root.tk.call('after','info')):
            self.window.root.after_cancel(timer)
        self.window.stop()

    def test_status_updates_do_not_map_window_or_steal_focus(self):
        self.window.render(View(status='Aufnahme',text='Synthetischer Prüftext.',voice='tyr'))
        self.window.root.update_idletasks()
        self.assertEqual(self.window.root.state(),'withdrawn')
        self.assertEqual(self.window.voice.current(),1)
        self.assertEqual(self.window.text.get('1.0','end-1c'),'Synthetischer Prüftext.')

    def test_expired_result_is_removed_from_visible_widget(self):
        self.window.render(View(text='Einmaliger synthetischer Inhalt'))
        self.window.render(View(text=''))
        self.assertEqual(self.window.text.get('1.0','end-1c'),'')
        self.assertEqual(str(self.window.copy['state']),'disabled')

    def test_stop_releases_displayed_and_pending_python_text(self):
        class Marker(str):pass
        shown=Marker('Synthetischer angezeigter Inhalt')
        pending=Marker('Synthetischer wartender Inhalt')
        shown_ref,pending_ref=weakref.ref(shown),weakref.ref(pending)
        self.window.render(View(text=shown));self.window.post(View(text=pending))
        del shown,pending
        self.window.stop()
        self.assertIsNone(shown_ref())
        self.assertIsNone(pending_ref())
