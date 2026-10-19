"""Startup unwind uses fake owners; no native input registrations."""
from contextlib import ExitStack
from pathlib import Path
import queue
import threading
import gc
import weakref
from types import ModuleType,SimpleNamespace as NS
import unittest
from unittest.mock import patch

from hugin import application
from hugin.errors import HuginError


def module(name,**fields):
    value=ModuleType(name);value.__dict__.update(fields);return value


class StartupContracts(unittest.TestCase):
    def _failure_closes_io_before_instance_release(self,ui_failure=False,join_failure=False,cleanup_failure=False,window_failure=False,window_start_failure=False,window_interrupt=False,cue_failure=False):
        owners=[];guards=[];released=[];controllers=[];joined=[];commands=[]
        class Owner:
            def __init__(self,*args,**kwargs):self.closed=False;owners.append(self)
            def start(self):pass
            def stop(self):self.closed=True
            close=stop
            def post(self,*args):pass
            def request_stop(self):pass
            def run(self):raise RuntimeError('synthetic UI loop failure')
        class Window(Owner):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                if window_start_failure or window_interrupt:
                    error=KeyboardInterrupt() if window_interrupt else HuginError('interface_failed','window_start')
                    error.owner=self
                    raise error
            def stop(self):
                if window_failure: raise RuntimeError('synthetic window cleanup failure')
                super().stop()
        class Guard(Owner):
            def __init__(self):super().__init__();guards.append(self)
            def acquire(self):return True
            def close(self):
                released.extend(owner.closed for owner in owners if owner is not self)
                super().close()
        class Executor:
            def shutdown(self,**kwargs):pass
        class Controller:
            def __init__(self,settings,**kwargs):
                controllers.append(self)
                self._closed=False
                self.owners=[kwargs[name] for name in ('inputs','signals','output','clipboard','cues')]
                self.capture_executor=self.audio_executor=self.maintenance_executor=self.selection_executor=self.delivery_executor=Executor()
            def finish_io(self):
                if cleanup_failure: return False
                for owner in self.owners:owner.close()
                return True
            def run(self,*args):pass
            def command(self,kind,*args):commands.append(kind)
        class FailedThread:
            def __init__(self,*args,**kwargs):pass
            def start(self):
                if not ui_failure: raise RuntimeError('synthetic start failure')
            def join(self):
                joined.append(True)
                if join_failure: raise RuntimeError('synthetic interrupted join')
                controllers[0]._closed=controllers[0].finish_io()
        def cue_signals(root):
            if cue_failure:raise HuginError('audio_failed','cue_asset')
            return {}
        fakes={
            'hugin.audio':module('hugin.audio',Microphone=lambda *args:NS(),PCMOutput=Owner),
            'hugin.cues':module('hugin.cues',DictationCues=Owner,load_cue_signals=cue_signals),
            'hugin.ui':module('hugin.ui',HuginWindow=Window),
            'hugin.windows.input':module('hugin.windows.input',WindowsInputs=Owner),
            'hugin.windows.instance':module('hugin.windows.instance',InstanceGuard=Guard),
            'hugin.windows.clipboard':module('hugin.windows.clipboard',ClipboardService=Owner),
            'hugin.windows.signals':module('hugin.windows.signals',WindowsSignals=Owner),
            'hugin.workers':module('hugin.workers',EnginePool=lambda *args:NS(workers={})),
            'hugin.targets':module('hugin.targets',load_target_approvals=lambda root:NS(delivery=(),capture_fallback=(),verified_edit=None)),
        }
        settings=NS(root=Path(__file__).resolve().parents[2],
            limits={'clipboard_bytes':1,'capture_bytes':2,'audio_buffer_ms':250})
        with ExitStack() as patches:
            patches.enter_context(patch.dict('sys.modules',fakes))
            patches.enter_context(patch.object(application,'Controller',Controller))
            patches.enter_context(patch.object(application.threading,'Thread',FailedThread))
            app=application.Application(settings,pilot=True)
            with self.assertRaises((RuntimeError,HuginError,KeyboardInterrupt)):app.run()
        if join_failure or cleanup_failure or window_failure:
            self.assertFalse(guards[0].closed,'unconfirmed cleanup must retain the instance owner')
            self.assertIs(app._startup_owners[0],guards[0])
        else:
            self.assertTrue(guards[0].closed)
            if cue_failure:
                self.assertEqual(owners,guards,'asset failure must precede native owner construction')
            elif window_start_failure or window_interrupt:
                self.assertTrue(next(owner for owner in owners if isinstance(owner,Window)).closed)
            else:
                self.assertTrue(released and all(released),'all started owners must close before mutex release')
        if ui_failure:
            self.assertIn('quit',commands)
            self.assertTrue(joined)

    def test_owner_thread_start_failure_closes_io_before_instance_release(self):
        self._failure_closes_io_before_instance_release()

    def test_missing_cue_assets_release_guard_before_native_io_is_constructed(self):
        self._failure_closes_io_before_instance_release(cue_failure=True)

    def test_ui_loop_failure_joins_live_owner_before_instance_release(self):
        self._failure_closes_io_before_instance_release(ui_failure=True)

    def test_interrupted_join_retains_instance_and_live_controller(self):
        self._failure_closes_io_before_instance_release(ui_failure=True,join_failure=True)

    def test_failed_startup_cleanup_retains_instance_and_native_owners(self):
        self._failure_closes_io_before_instance_release(cleanup_failure=True)

    def test_failed_window_close_retains_instance_and_window_owner(self):
        self._failure_closes_io_before_instance_release(ui_failure=True,window_failure=True)

    def test_partial_window_start_retains_owner_for_startup_cleanup(self):
        self._failure_closes_io_before_instance_release(window_start_failure=True)

    def test_interrupted_partial_window_start_keeps_owner_for_cleanup(self):
        self._failure_closes_io_before_instance_release(window_interrupt=True)


class WindowCleanupContracts(unittest.TestCase):
    def test_interrupted_constructor_closes_partial_root_and_preserves_interrupt(self):
        from hugin import ui
        class Root:
            closed=False
            def withdraw(self):raise KeyboardInterrupt()
            def destroy(self):self.closed=True
        root=Root()
        with patch.object(ui.tk,'Tk',return_value=root),patch.object(ui.sys,'platform','fixture'):
            with self.assertRaises(KeyboardInterrupt) as failure:ui.HuginWindow(lambda *args:None,with_tray=False)
        self.assertTrue(root.closed)
        self.assertIs(failure.exception.owner.root,root)

    def test_native_tray_failure_requests_owned_shutdown_once(self):
        from hugin.ui import HuginWindow
        window=HuginWindow.__new__(HuginWindow);calls=[]
        window._alive=True;window._tray=NS(error=HuginError('input_failed','tray_loop'))
        window.failure=None;window._commands=queue.Queue();window._updates=queue.Queue()
        window._stop_requested=threading.Event()
        window.root=NS(after=lambda *args:None);window.on_action=lambda *args:calls.append(args)
        window._pump();window._pump()
        self.assertEqual(calls,[('quit',None)])
        self.assertEqual(window.failure.code,'interface_failed')

    def test_window_constructor_failure_preserves_and_closes_partial_root(self):
        from hugin import ui
        class Root:
            closed=False
            def withdraw(self):raise RuntimeError('synthetic window setup failure')
            def destroy(self):self.closed=True
        root=Root()
        with patch.object(ui.tk,'Tk',return_value=root),patch.object(ui.sys,'platform','fixture'):
            with self.assertRaises(HuginError) as failure:ui.HuginWindow(lambda *args:None,with_tray=False)
        self.assertIs(failure.exception.owner.root,root)
        self.assertTrue(root.closed)

    def test_confirmed_window_close_is_idempotent(self):
        from hugin.ui import HuginWindow
        calls=[]
        class Root:
            def destroy(self):
                if 'root' in calls: raise RuntimeError('already destroyed')
                calls.append('root')
        window=HuginWindow.__new__(HuginWindow)
        window.root=Root();window._tray=NS(close=lambda:calls.append('tray'),closed=True)
        window._alive=True;window._closed=False
        window.stop();window.stop()
        self.assertEqual(calls,['tray','root'])


class WindowPumpContracts(unittest.TestCase):
    def setUp(self):
        from hugin.ui import HuginWindow
        self.calls=[]
        class Root:
            destroyed=False
            def destroy(self):self.destroyed=True
            def quit(self):pass
            def after(self,*args):self.scheduled=True
            def deiconify(self):pass
            def lift(self):pass
        class Tray:
            closed=False;error=None;fail_once=False
            def close(self):
                if self.fail_once:
                    self.fail_once=False
                    raise HuginError('input_failed','synthetic_tray_close')
                self.closed=True
        self.window=HuginWindow.__new__(HuginWindow)
        self.window.root=Root();self.window._tray=Tray()
        self.window._alive=True;self.window._closed=False;self.window.failure=None
        self.window._commands=queue.Queue(maxsize=32);self.window._updates=queue.Queue(maxsize=2)
        self.window._stop_requested=threading.Event()
        self.window.on_action=lambda *args:self.calls.append(args)

    def test_full_open_queue_cannot_discard_confirmed_controller_stop(self):
        for _ in range(32):self.window._command('show')
        self.window.request_stop();self.window._pump()
        self.assertTrue(self.window.root.destroyed)

    def test_transient_tray_close_failure_retains_live_pump_and_owner_for_retry(self):
        self.window._tray.fail_once=True
        self.window.request_stop();self.window._pump()
        self.assertFalse(self.window.root.destroyed)
        self.assertIsNotNone(self.window.failure)
        self.window.request_stop();self.window._pump()
        self.assertTrue(self.window.root.destroyed)

    def test_view_update_failure_requests_quit_and_keeps_stop_path_live(self):
        def fail(view):raise HuginError('input_failed','synthetic_icon_update')
        self.window.render=fail
        self.window._updates.put(object())
        self.window._pump()
        self.assertEqual(self.calls,[('quit',None)])
        self.assertEqual(self.window.failure.code,'interface_failed')
        self.assertTrue(self.window.root.scheduled)
        self.window.request_stop();self.window._pump()
        self.assertTrue(self.window.root.destroyed)

    def test_saved_interrupt_releases_view_traceback_and_context(self):
        from hugin.ui import View
        def fail(view):
            try:raise ValueError('synthetic inner failure')
            except ValueError:raise KeyboardInterrupt() from RuntimeError('synthetic cause')
        self.window.render=fail
        view=View(text='Synthetischer vertraulicher Marker')
        reference=weakref.ref(view)
        self.window._updates.put(view);del view
        self.window._pump();self.window.stop();gc.collect()
        self.assertIsInstance(self.window.failure,KeyboardInterrupt)
        self.assertIsNone(reference())
        self.assertIsNone(self.window.failure.__context__)
        self.assertIsNone(self.window.failure.__cause__)
