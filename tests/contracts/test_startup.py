"""Startup unwind uses fake owners; no native input registrations."""
from contextlib import ExitStack
from pathlib import Path
from types import ModuleType,SimpleNamespace as NS
import unittest
from unittest.mock import patch

from hugin import application


def module(name,**fields):
    value=ModuleType(name);value.__dict__.update(fields);return value


class StartupContracts(unittest.TestCase):
    def _failure_closes_io_before_instance_release(self,ui_failure=False):
        owners=[];guards=[];released=[];controllers=[];joined=[];commands=[]
        class Owner:
            def __init__(self,*args,**kwargs):self.closed=False;owners.append(self)
            def start(self):pass
            def stop(self):self.closed=True
            close=stop
            def post(self,*args):pass
            def request_stop(self):pass
            def run(self):raise RuntimeError('synthetic UI loop failure')
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
                self.owners=[kwargs[name] for name in ('inputs','signals','output','clipboard')]
                self.capture_executor=self.audio_executor=self.maintenance_executor=self.selection_executor=Executor()
            def finish_io(self):
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
                controllers[0].finish_io()
        fakes={
            'hugin.audio':module('hugin.audio',Microphone=lambda *args:NS(),PCMOutput=Owner),
            'hugin.ui':module('hugin.ui',HuginWindow=Owner),
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
            with self.assertRaises(RuntimeError):application.Application(settings,pilot=True).run()
        self.assertTrue(guards[0].closed)
        self.assertTrue(released and all(released),'all started owners must close before mutex release')
        if ui_failure:
            self.assertIn('quit',commands)
            self.assertTrue(joined)

    def test_owner_thread_start_failure_closes_io_before_instance_release(self):
        self._failure_closes_io_before_instance_release()

    def test_ui_loop_failure_joins_live_owner_before_instance_release(self):
        self._failure_closes_io_before_instance_release(ui_failure=True)


class WindowCleanupContracts(unittest.TestCase):
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
