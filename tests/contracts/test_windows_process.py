import subprocess
import unittest

from hugin.errors import HuginError
from hugin.windows.process import OwnedProcess
from hugin.windows.instance import InstanceGuard


class FakeProcess:
    def __init__(self):
        self.events = []
        self.active = 1
        self.exit_code = None
        self.attach_fails = False
        self.closed = []

    def create_job(self, memory_limit=None):
        self.events.append('job')
        self.memory_limit = memory_limit
        return 100

    def create_suspended(self, command, stdio, extra_handles, cwd, env, flags):
        self.events.append(('suspended', command, extra_handles))
        return 101, 102, 42

    def assign(self, job, process):
        self.events.append('assign')
        if self.attach_fails:
            raise HuginError('worker_failed', 'job_assignment')

    def resume(self, thread):
        self.events.append('resume')

    def exit_status(self, process):
        return self.exit_code

    def active_processes(self, job):
        return self.active

    def terminate_job(self, job):
        self.events.append(('terminate_job', job))
        self.active = 0
        self.exit_code = 1

    def terminate_process(self, process):
        self.events.append(('terminate_process', process))
        self.active = 0
        self.exit_code = 1

    def close_handle(self, handle):
        self.closed.append(handle)

    def stdio_handle(self, descriptor):
        return descriptor


class WindowsProcessContracts(unittest.TestCase):
    def test_job_metrics_are_retained_before_owned_handle_close(self):
        backend=FakeProcess()
        expected={'cpu_seconds':2.5,'peak_job_commit_bytes':4096}
        backend.metrics=lambda job: dict(expected)
        process=OwnedProcess(['python','worker'],backend=backend)
        process.kill();process.wait(.1);process.close()
        backend.metrics=lambda job: self.fail('must not query a closed job handle')
        self.assertEqual(process.metrics(),expected)

    def test_process_cannot_run_before_job_assignment(self):
        backend = FakeProcess()
        process = OwnedProcess(['python', 'worker'], backend=backend)
        self.assertEqual(backend.events[:4], ['job', ('suspended', ['python', 'worker'], []), 'assign', 'resume'])
        self.assertIn(102, backend.closed)
        process.terminate()
        self.assertEqual(process.wait(0.01), 1)
        process.close()
        self.assertIn(('terminate_job', 100), backend.events)
        self.assertIn(100, backend.closed)

    def test_redirector_exit_does_not_claim_family_terminal(self):
        backend = FakeProcess()
        process = OwnedProcess(['python', 'worker'], backend=backend)
        backend.exit_code = 0
        self.assertIsNone(process.poll())
        with self.assertRaises(subprocess.TimeoutExpired):
            process.wait(0.001)
        with self.assertRaises(HuginError):
            process.close()
        self.assertNotIn(100, backend.closed)
        process.kill()
        process.close()

    def test_assignment_failure_never_resumes_and_reaps_only_created_process(self):
        backend = FakeProcess()
        backend.attach_fails = True
        with self.assertRaises(HuginError):
            OwnedProcess(['python', 'worker'], backend=backend)
        self.assertNotIn('resume', backend.events)
        self.assertIn(('terminate_process', 101), backend.events)
        self.assertEqual(set(backend.closed), {100, 101, 102})

    def test_foreign_inherited_handles_are_only_forwarded_explicitly(self):
        backend = FakeProcess()
        class Startup:
            lpAttributeList = {'handle_list': [500, 501]}
        process = OwnedProcess(['python', 'worker'], startupinfo=Startup(), backend=backend)
        self.assertEqual(backend.events[1][2], [500, 501])
        process.kill()
        process.close()
        self.assertNotIn(500, backend.closed)

    def test_failed_cleanup_returns_owner_and_keeps_handles(self):
        backend = FakeProcess()
        backend.attach_fails = True
        terminate = backend.terminate_process
        def blocked(_):
            raise HuginError('worker_failed', 'process_terminate')
        backend.terminate_process = blocked
        with self.assertRaises(HuginError) as failure:
            OwnedProcess(['python', 'worker'], backend=backend)
        owner = failure.exception.owner
        self.assertEqual(backend.closed, [])
        backend.terminate_process = terminate
        owner.kill()
        owner.wait(0.01)
        owner.close()
        self.assertEqual(set(backend.closed), {100, 101, 102})

    def test_probe_memory_limit_is_applied_before_process_creation(self):
        backend = FakeProcess()
        process = OwnedProcess(['python', 'worker'], backend=backend, memory_limit=256 * 1024 * 1024)
        self.assertEqual(backend.memory_limit, 256 * 1024 * 1024)
        process.kill()
        process.close()


class FakeMutex:
    def __init__(self):
        self.owned = False
        self.name = None

    def acquire(self, name):
        self.name = name
        if self.owned:
            return 100, False
        self.owned = True
        return 100, True

    def release(self, handle, acquired):
        if acquired:
            self.owned = False


class InstanceContracts(unittest.TestCase):
    def test_second_instance_does_not_claim_ownership(self):
        backend = FakeMutex()
        first, second = InstanceGuard(user_sid='S-1-5-21-123', backend=backend), InstanceGuard(user_sid='S-1-5-21-123', backend=backend)
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        second.close()
        self.assertTrue(backend.owned)
        first.close()
        self.assertFalse(backend.owned)
        self.assertTrue(backend.name.startswith('Local\\Hugin.v1.'))

    def test_distinct_user_ids_use_distinct_names(self):
        one, two = FakeMutex(), FakeMutex()
        first, second = InstanceGuard(user_sid='S-1-5-21-1', backend=one), InstanceGuard(user_sid='S-1-5-21-2', backend=two)
        first.acquire()
        second.acquire()
        self.assertNotEqual(one.name, two.name)
        first.close()
        second.close()
