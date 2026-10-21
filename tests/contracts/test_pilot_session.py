"""No automatic old-stack return from the owned test-session launcher."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

path=Path(__file__).resolve().parents[2]/'tools/pilot_session.py'
spec=importlib.util.spec_from_file_location('pilot_session',path)
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)


class Owner:
    pid=123
    def __init__(self,*args,**kwargs):self.calls=[]
    def wait(self,timeout=None):self.calls.append(('wait',timeout));return 0
    def close(self):self.calls.append('close')
    def kill(self):self.calls.append('kill')


class PilotSession(unittest.TestCase):
    def test_constructor_without_process_retries_its_held_handle_close(self):
        from test_windows_process import FakeProcess
        from hugin.windows.process import OwnedProcess
        backend=FakeProcess();closes=[];reports=[]
        def create(*args):raise OSError('no process created')
        def close(handle):
            closes.append(handle)
            if len(closes)==1:raise OSError('first handle close failed')
            backend.closed.append(handle)
        backend.create_suspended=create;backend.close_handle=close
        def factory(*args,**kwargs):return OwnedProcess(*args,**kwargs,backend=backend)
        # No process exists to wait for. A wait/sleep here is a lifecycle error.
        with patch.object(pilot.time,'sleep',side_effect=AssertionError('wait before partial close')):
            self.assertEqual(pilot.run_owned(['synthetic'],path.parent,
                lambda state,**facts:reports.append((state,facts)),factory=factory),2)
        self.assertEqual(closes,[100,100])
        self.assertEqual(backend.closed,[100])
        self.assertEqual(reports[-1][0],'session_failed')

    def test_exit_and_failure_never_dispatch_other_apps(self):
        for fail in (False,True):
            with self.subTest(fail=fail):
                owner=Owner();events=[]
                def factory(*args,**kwargs):
                    if fail:
                        error=RuntimeError('owned constructor cleanup');error.owner=owner
                        raise error
                    return owner
                with patch.object(pilot.os,'startfile',create=True) as start:
                    code=pilot.run_owned(['synthetic'],path.parent,lambda state,**facts:
                        events.append((state,facts)),factory=factory)
                start.assert_not_called()
                self.assertEqual(code,2 if fail else 0)
                self.assertEqual(owner.calls,(['close'] if fail else [('wait',None),'close']))
                self.assertEqual(events[-1][1]['started_shortcuts'],[])
                self.assertTrue(events[-1][1]['own_family_exited'])

    def test_failed_cleanup_retains_owner_until_successful_retry(self):
        owner=Owner();events=[];closes=0
        def close():
            nonlocal closes
            closes+=1
            if closes<=3:raise OSError('retry required')
        owner.close=close
        def factory(*args,**kwargs):
            error=RuntimeError();error.owner=owner;raise error
        with patch.object(pilot.time,'sleep'):
            self.assertEqual(pilot.run_owned(['synthetic'],path.parent,
                lambda state,**facts:events.append((state,facts)),factory=factory),2)
        self.assertEqual([item[0] for item in events],['own_cleanup_pending','session_failed'])
        self.assertEqual(closes,4)

    def test_active_failed_constructor_reaps_only_its_owned_process_before_close(self):
        from test_windows_process import FakeProcess
        from hugin.windows.process import OwnedProcess
        backend=FakeProcess();backend.attach_fails=True;attempts=0
        terminate=backend.terminate_process
        def retry(process):
            nonlocal attempts
            attempts+=1
            if attempts==1:raise OSError('first termination failed')
            terminate(process)
        backend.terminate_process=retry
        def factory(*args,**kwargs):return OwnedProcess(*args,**kwargs,backend=backend)
        self.assertEqual(pilot.run_owned(['synthetic'],path.parent,lambda *a,**k:None,
            factory=factory),2)
        self.assertEqual(attempts,2)
        self.assertNotIn('resume',backend.events)
        self.assertEqual(set(backend.closed),{100,101,102})

    def test_plan_requires_exact_clean_source_and_runtime(self):
        head='a'*40;runtime_head='b'*40
        with patch.object(pilot,'git',side_effect=[head,'',runtime_head,'','']):
            report=pilot.plan(path.parent,head,runtime_head)
            self.assertEqual(report['pilot_hotkeys'],['Alt+Y','Strg+Alt+V'])
        self.assertEqual(report['old_stack_return'],'disabled')
        for answers in ([head,'dirty'],[head,'','c'*40],[head,'',runtime_head,'dirty'],
                        [head,'',runtime_head,'','worker diff']):
            with self.subTest(answers=answers),patch.object(pilot,'git',side_effect=answers):
                with self.assertRaises(RuntimeError):pilot.plan(path.parent,head,runtime_head)
