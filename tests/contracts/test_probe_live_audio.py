"""Probe plan/source/lifetime guards; no CUDA, native output or user I/O."""
from contextlib import redirect_stdout
import importlib.util
from concurrent.futures import Future
import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from hugin.errors import HuginError

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('probe_live_audio', ROOT/'tools/probe_live_audio.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class LiveAudioProbeContracts(unittest.TestCase):
    def test_default_plan_uses_explicit_runtime_and_has_no_write_or_worker_effect(self):
        with patch.object(probe, '_run_directory', side_effect=AssertionError('no writes')), \
             patch.object(probe, '_head', return_value='synthetic-fixed-head'):
            report = probe.probe(ROOT, cancel=True)
        self.assertEqual(report['status'], 'planned')
        self.assertEqual(report['runtime_root'], str(ROOT.resolve()))
        self.assertEqual(report['source_root'], str(ROOT.resolve()))
        self.assertFalse(report['starts_workers'])
        self.assertFalse(report['plays_synthetic_audio'])
        self.assertFalse(report['writes_technical_trace'])
        self.assertEqual(report['budgets']['provider_retained_pcm_bytes'], 4320000)
        self.assertEqual(report['budgets']['client_packet_bytes'], 6000)
        self.assertEqual(report['budgets']['native_buffer_ms'], 125)

    def test_spawn_binds_new_source_and_preserves_runtime_interpreter_root_and_handles(self):
        runtime = Path('stable-runtime')
        source = Path('new-source')
        command = [str(runtime/'python.exe'), '-m', 'hugin.workers.server',
            '--root', str(runtime), '--engine', 'tts', '--data-input', '44', '--data-output', '55']
        environment = {'PYTHONPATH':'old-source', 'HF_HUB_OFFLINE':'1'}
        handles = object()
        observed = []
        def owned(args, **kwargs):observed.append((args, kwargs));return 'held-job-owner'
        owner = probe._spawn_from_source(command, source=source, trace=Path('trace'),
            owned_process=owned, env=environment, startupinfo=handles, cwd=str(runtime))
        self.assertEqual(owner, 'held-job-owner')
        args, kwargs = observed[0]
        self.assertEqual(args[0], command[0])
        self.assertEqual(args[1], str(source/'tools/probe_live_audio.py'))
        self.assertEqual(args[4:], command[3:])
        self.assertEqual(kwargs['env']['PYTHONPATH'], str(source/'src'))
        self.assertEqual(kwargs['env']['HF_HUB_OFFLINE'], '1')
        self.assertEqual(environment['PYTHONPATH'], 'old-source')
        self.assertIs(kwargs['startupinfo'], handles)
        self.assertEqual(kwargs['cwd'], str(runtime))
        with self.assertRaises(HuginError):
            probe._spawn_from_source(['foreign', '-m', 'foreign.module'], source=source,
                trace=Path('trace'), owned_process=owned, env=environment)
        self.assertEqual(len(observed), 1)

    def test_cli_failure_contains_only_typed_code_and_phase(self):
        output = io.StringIO()
        for failure in (RuntimeError('PRIVATE_EXCEPTION_AND_TEXT'), HuginError('audio_failed', 'synthetic_audio')):
            output.seek(0);output.truncate()
            with patch.object(probe, 'probe', side_effect=failure), redirect_stdout(output):
                self.assertEqual(probe.main(['--root', str(ROOT), '--run']), 1)
            report = json.loads(output.getvalue())
            self.assertEqual(set(report), {'status', 'error'})
            self.assertEqual(set(report['error']), {'code', 'phase'})
            self.assertNotIn('PRIVATE', output.getvalue())

    def test_run_directories_are_additive_and_child_rejects_foreign_trace_before_engine_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root/'.runtime').mkdir()
            first = probe._run_directory(root)
            second = probe._run_directory(root)
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, root/'.runtime/live-audio-probe')
            self.assertEqual(list(first.iterdir()), [])
            with self.assertRaises(HuginError) as failure:
                probe._worker(root/'foreign.json', ['--root', str(root),'--engine','tts'])
            self.assertEqual(failure.exception.code, 'config_invalid')

    def test_executor_close_cannot_claim_exit_while_owned_task_is_blocked(self):
        entered, release = threading.Event(), threading.Event()
        executor = probe._Executor(1)
        def held():entered.set();release.wait(1)
        executor.submit(held)
        try:
            self.assertTrue(entered.wait(1))
            self.assertFalse(executor.close_bounded(time.monotonic()+.01))
        finally:release.set()
        self.assertTrue(executor.close_bounded(time.monotonic()+1))

    def test_worker_metrics_are_bounded_numeric_facts_not_untrusted_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'worker.json'
            operation = dict(chunks=[dict(ready_clock=1.0, compute_ms=2.0, bytes=4)],
                pcm_bytes=4, sha256='a'*64)
            path.write_text(json.dumps(dict(schema_version=1, operations=[operation])), encoding='utf-8')
            self.assertEqual(probe._read_worker_trace(path), [operation])
            operation['chunks'][0]['compute_ms'] = 'PRIVATE_EXCEPTION_AND_TEXT'
            path.write_text(json.dumps(dict(schema_version=1, operations=[operation])), encoding='utf-8')
            with self.assertRaises(HuginError):probe._read_worker_trace(path)
            path.write_bytes(b' '*262145)
            with self.assertRaises(HuginError) as failure:probe._read_worker_trace(path)
            self.assertEqual(failure.exception.code, 'resource_limit')

    def test_real_controller_probe_flow_with_simulated_pool_and_output(self):
        """Real controller/executors; simulated model/process/driver only."""
        from hugin import audio, workers
        for underflow in (False, True):
            with self.subTest(underflow=underflow), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary).resolve()
                provider = []
                class Device:
                    def __init__(self, rate):
                        self.queued_bytes = 0;self.headers = [];self.handle = object()
                    def collect(self, force=False):
                        if force or self.operation['draining'] or underflow:
                            self.headers.clear();self.queued_bytes = 0
                        elif len(self.headers) > 1:self.queued_bytes -= self.headers.pop(0)
                    def submit(self, pcm):self.headers.append(len(pcm));self.queued_bytes += len(pcm)
                    def reset(self):self.headers.clear();self.queued_bytes = 0
                    def close(self):self.reset();self.handle = None
                class Worker:
                    engine = 'tts';device = 'cuda';closed = False;failed = False
                    def __init__(self,engine):
                        self.engine=engine
                        self.engine_instance = str(uuid.uuid4())
                        self.cancelled = threading.Event();self.thread = None
                        self.process = SimpleNamespace(poll=lambda:0 if self.closed else None,
                            metrics=lambda:dict(cpu_seconds=.01, peak_job_commit_bytes=123456))
                    def close(self):
                        self.cancelled.set()
                        if self.thread is not None:self.thread.join(1)
                        if self.thread is not None and self.thread.is_alive():raise HuginError('worker_timeout', 'synthetic_cleanup')
                        self.closed = True
                        if self.engine=='tts':
                            (directory/'worker.json').write_text(json.dumps({'schema_version':1, 'operations':provider}), encoding='utf-8')
                class Pool:
                    def __init__(self, root, callback, **kwargs):self.callback = callback;self.workers = {}
                    def start(self, engine, **kwargs):
                        worker = Worker(engine);self.workers[engine] = worker
                        future = Future();future.set_result(dict(device='cuda', engine_instance=worker.engine_instance))
                        return future
                    def synthesize(self, text, voice, request_id, generation, language):
                        assert text == probe.TEXT
                        worker = self.workers['tts'];worker.cancelled.clear()
                        future = Future()
                        def produce():
                            digest = hashlib.sha256();count = 0
                            for index in range(3):
                                pcm = bytes([index+1, 0])*3000
                                if worker.cancelled.is_set():break
                                digest.update(pcm)
                                self.callback(dict(type='audio', engine='tts', engine_instance=worker.engine_instance,
                                    request_id=request_id, generation=generation, pcm=pcm, sample_rate=24000, offset=count))
                                count += len(pcm)
                            provider.append(dict(chunks=[], pcm_bytes=count, sha256=digest.hexdigest()))
                            terminal = dict(type='terminal', engine='tts', engine_instance=worker.engine_instance,
                                request_id=request_id, generation=generation, cancelled=worker.cancelled.is_set(),
                                code=None, audio_bytes=count)
                            future.set_result(terminal)
                            self.callback(terminal)
                        worker.thread = threading.Thread(target=produce)
                        worker.thread.start()
                        return future
                    def align(self,pcm,text,request_id,generation,language):
                        from hugin.word_timing import AlignmentResult
                        worker=self.workers['stt']
                        self.callback(dict(type='alignment',engine='stt',engine_instance=worker.engine_instance,
                            request_id=request_id,generation=generation,result=AlignmentResult('rejected_path',())))
                        future=Future();future.set_result(dict(code=None,cancelled=False));return future
                    def cancel(self, *args):self.workers['tts'].cancelled.set();return True
                with patch.object(probe, '_run_directory', return_value=directory), \
                     patch.object(probe, '_head', return_value='synthetic-head'), \
                     patch.object(audio, '_WaveOut', Device), patch.object(workers, 'EnginePool', Pool):
                    report = probe.probe(ROOT, run=True, cancel=True)
                self.assertEqual(report['status'], 'failed' if underflow else 'passed', report.get('error'))
                self.assertTrue(report['cleanup_confirmed'], report.get('cleanup_error'))
                self.assertEqual(len(report['operations']), 3)
                self.assertEqual([item['voice'] for item in report['operations']], ['freya', 'tyr', 'tyr'])
                self.assertTrue(report['operations'][-1]['playback_cancelled'])
                self.assertFalse(report['operations'][-1]['terminal']['cancelled'])
                self.assertTrue(all(item['provider_pcm_exact'] for item in report['operations'][:2]))
                self.assertTrue(all(item['peak_queued_bytes'] <= 6000 for item in report['operations']))
                self.assertFalse(probe._HELD)
                if underflow:self.assertEqual(report['error'], dict(code='audio_failed', phase='live_probe_underflow'))


if __name__ == '__main__':unittest.main()
