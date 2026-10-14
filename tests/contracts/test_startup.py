"""Startup unwind uses fake owners; no native input registrations."""
from contextlib import ExitStack
from pathlib import Path
from types import ModuleType,SimpleNamespace as NS
import unittest
from unittest.mock import patch

from hugin import application
from hugin.errors import HuginError


def module(name,**fields):
    value=ModuleType(name);value.__dict__.update(fields);return value


class StartupContracts(unittest.TestCase):
    def _failure_closes_io_before_instance_release(self,ui_failure=False,join_failure=False,cleanup_failure=False,window_failure=False,window_start_failure=False):
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
                if window_start_failure:
                    error=HuginError('interface_failed','window_start');error.owner=self
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
                self.owners=[kwargs[name] for name in ('inputs','signals','output','clipboard')]
                self.capture_executor=self.audio_executor=self.maintenance_executor=self.selection_executor=Executor()
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
        fakes={
            'hugin.audio':module('hugin.audio',Microphone=lambda *args:NS(),PCMOutput=Owner),
            'hugin.ui':module('hugin.ui',HuginWindow=Window),
            'hugin.windows.input':module('hugin.windows.input',WindowsInputs=Owner),
            'hugin.windows.instance':module('hugin.windows.instance',InstanceGuard=Guard),
            'hugin.windows.clipboard':module('hugin.windows.clipboard',ClipboardService=Owner),
            'hugin.windows.signals':module('hugin.windows.signals',WindowsSignals=Owner),
            'hugin.workers':module('hugin.workers',EnginePool=lambda *args:NS(workers={})),
            'hugin.targets':module('hugin.targets',load_target_approvals=lambda root:NS(delivery=(),capture_fallback=())),
        }
        settings=NS(root=Path(__file__).resolve().parents[2],
            limits={'clipboard_bytes':1,'capture_bytes':2,'audio_buffer_ms':250})
        with ExitStack() as patches:
            patches.enter_context(patch.dict('sys.modules',fakes))
            patches.enter_context(patch.object(application,'Controller',Controller))
            patches.enter_context(patch.object(application.threading,'Thread',FailedThread))
            app=application.Application(settings,pilot=True)
            with self.assertRaises((RuntimeError,HuginError)):app.run()
        if join_failure or cleanup_failure or window_failure:
            self.assertFalse(guards[0].closed,'unconfirmed cleanup must retain the instance owner')
            self.assertIs(app._startup_owners[0],guards[0])
        else:
            self.assertTrue(guards[0].closed)
            if window_start_failure:
                self.assertTrue(next(owner for owner in owners if isinstance(owner,Window)).closed)
            else:
                self.assertTrue(released and all(released),'all started owners must close before mutex release')
        if ui_failure:
            self.assertIn('quit',commands)
            self.assertTrue(joined)

    def test_owner_thread_start_failure_closes_io_before_instance_release(self):
        self._failure_closes_io_before_instance_release()

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


class WindowCleanupContracts(unittest.TestCase):
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
        window.root=Root();window._tray=NS(stop=lambda:calls.append('tray'))
        window._alive=True;window._closed=False
        window.stop();window.stop()
        self.assertEqual(calls,['tray','root'])
