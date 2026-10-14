"""Probe orchestration with simulated clients; establishes no CUDA/provider coverage."""
from concurrent.futures import Future
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import wave

from hugin.errors import HuginError

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('probe_gpu', ROOT / 'tools/probe_gpu.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
EXPECTED = ' '.join(['synthetic'] * 17)


def completed(value):
    future = Future(); future.set_result(value); return future


class SimulatedWorker:
    def __init__(self, factory, engine, callback):
        self.factory, self.engine, self.callback = factory, engine, callback
        self.engine_instance = str(len(factory.workers))
        self.closed = self.cancelled = False
        self.device = factory.device
        self.process = NS(metrics=self.metrics)
        factory.workers.append(self)
    def metrics(self):
        if not self.closed: raise AssertionError('metrics must include confirmed cleanup')
        return dict(cpu_seconds=3.25, peak_job_commit_bytes=1000)
    def start(self, *, device):
        self.factory.actions.append((self.engine, 'start', device))
        return completed(dict(device=self.device))
    def event(self, kind, request, generation, **fields):
        self.callback(dict(type=kind, engine=self.engine, engine_instance=self.engine_instance,
            request_id=request, generation=generation, **fields))
    def transcribe(self, pcm, request, generation):
        self.factory.actions.append((self.engine, 'transcribe'))
        self.event('result', request, generation, text=self.factory.transcript)
        return completed(dict(code=None, cancelled=False, audio_bytes=0))
    def offload(self):
        self.factory.actions.append((self.engine, 'offload'))
        return completed(dict(code=None, cancelled=False))
    def synthesize(self, text, voice, request, generation, language):
        self.factory.actions.append((self.engine, 'synthesize', voice, text, language))
        self.cancelled = False
        offset = 0
        for _ in range(self.factory.audio_chunks):
            pcm = b'\x01\x00' * 3000
            self.event('audio', request, generation, pcm=pcm, sample_rate=24000, offset=offset)
            offset += len(pcm)
            if self.cancelled: break
        return completed(dict(code=None, cancelled=self.cancelled and self.factory.confirm_cancel,
            audio_bytes=offset))
    def cancel(self, request, generation):
        self.factory.actions.append((self.engine, 'cancel'))
        self.cancelled = True
        return True
    def cancel_active(self): self.cancelled = True
    def close(self):
        self.factory.actions.append((self.engine, 'close'))
        if self.factory.fail_close:
            raise HuginError('worker_timeout', 'worker_exit')
        self.closed = True


class Factory:
    device = 'cuda'; transcript = EXPECTED; audio_chunks = 2
    fail_close = False; confirm_cancel = True
    def __init__(self): self.workers = []; self.actions = []
    def __call__(self, root, engine, callback): return SimulatedWorker(self, engine, callback)


class GPUProbeContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / '.runtime').mkdir()
        self.settings = NS(root=self.root, limits=dict(ready_seconds=1, cancel_seconds=1, exit_seconds=1))
        self.patches = [patch.object(probe, 'load_settings', return_value=self.settings),
            patch.object(probe, 'verify_voice_assets'),
            patch.object(probe, '_reference', return_value=(b'\0\0' * 8, EXPECTED))]
        for item in self.patches: item.start()
        self.factory = Factory()
    def tearDown(self):
        for worker in self.factory.workers:
            worker.factory.fail_close = False
            worker.close(); probe._HELD_CLIENTS.discard(worker)
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()
    def run_probe(self, **kwargs):
        return probe.probe(self.root, run=True, client_factory=self.factory, **kwargs)

    def test_default_plan_never_starts_workers_verifies_audio_or_creates_outputs(self):
        with patch.object(probe, '_reference', side_effect=AssertionError('must not read audio')), \
                patch.object(probe, 'verify_voice_assets', side_effect=AssertionError('must not verify on plan')):
            result = probe.probe(self.root, samples=True, client_factory=self.factory)
        self.assertEqual(result['status'], 'planned')
        self.assertFalse(result['starts_workers']); self.assertFalse(result['writes_samples'])
        self.assertEqual(self.factory.workers, [])
        self.assertFalse((self.root / '.runtime/pilot-audio').exists())

    def test_serial_slots_confirm_exit_before_reload_and_tts_and_read_held_family_metrics_after_cleanup(self):
        result = self.run_probe()
        self.assertEqual(result['status'], 'passed'); self.assertTrue(result['cleanup_confirmed'])
        self.assertEqual([row['engine'] for row in result['workers']], ['stt', 'stt', 'tts'])
        actions = [(action[0], action[1]) for action in self.factory.actions]
        self.assertEqual(actions[:9], [('stt', 'start'), ('stt', 'transcribe'), ('stt', 'transcribe'),
            ('stt', 'offload'), ('stt', 'close'), ('stt', 'start'), ('stt', 'transcribe'),
            ('stt', 'close'), ('tts', 'start')])
        self.assertTrue(all(row['closed'] and row['family_cpu_seconds'] == 3.25
            and row['family_peak_job_commit_bytes'] == 1000 for row in result['workers']))
        speech = [action for action in self.factory.actions if action[1] == 'synthesize']
        self.assertEqual({action[3] for action in speech}, {probe.SYNTHETIC_TEXT})
        self.assertEqual({action[4] for action in speech}, {'German'})
        self.assertNotIn(EXPECTED, json.dumps(result))
        self.assertIn('same-process STT reload device', result['unmeasured'])

    def test_cpu_fallback_fails_and_cannot_enter_tts_slot(self):
        self.factory.device = 'cpu'
        result = self.run_probe()
        self.assertEqual(result['error'], dict(code='worker_failed', phase='stt_cpu_fallback'))
        self.assertTrue(result['cleanup_confirmed'])
        self.assertEqual(len(self.factory.workers), 1)

    def test_unconfirmed_cleanup_retains_owner_and_blocks_next_gpu_slot(self):
        self.factory.fail_close = True
        result = self.run_probe()
        self.assertEqual(result['status'], 'failed'); self.assertFalse(result['cleanup_confirmed'])
        self.assertFalse(result['workers'][0]['closed'])
        self.assertEqual(len(self.factory.workers), 1)
        self.assertIn(self.factory.workers[0], probe._HELD_CLIENTS)
        retried = self.run_probe()
        self.assertEqual(retried['error'], dict(code='worker_timeout', phase='pilot_cleanup_pending'))
        self.assertFalse(retried['cleanup_confirmed'])
        self.assertEqual(len(self.factory.workers), 1)

    def test_transcript_mismatch_reports_only_counts_and_failure_phase(self):
        self.factory.transcript = 'PRIVATE_SYNTHETIC_MISMATCH'
        result = self.run_probe()
        self.assertEqual(result['error']['phase'], 'stt_transcript_mismatch')
        self.assertFalse(result['operations'][0]['normalized_exact_match'])
        self.assertNotIn(self.factory.transcript, json.dumps(result))
        self.assertEqual(len(self.factory.workers), 1)

    def test_pcm_limit_cancels_without_retaining_or_writing_more_than_thirty_seconds(self):
        self.factory.audio_chunks = 241
        result = self.run_probe(samples=True)
        self.assertEqual(result['error'], dict(code='resource_limit', phase='pilot_audio'))
        self.assertTrue(result['cleanup_confirmed'])
        self.assertEqual(list((self.root / '.runtime/pilot-audio').rglob('*.wav')), [])

    def test_samples_are_exclusive_pcm16_24khz_and_cancel_sample_is_not_saved(self):
        result = self.run_probe(samples=True)
        files = list((self.root / '.runtime/pilot-audio').rglob('*.wav'))
        self.assertEqual(sorted(path.name for path in files), ['freya.wav', 'tyr.wav'])
        for path in files:
            with wave.open(str(path), 'rb') as source:
                self.assertEqual((source.getnchannels(), source.getsampwidth(), source.getframerate()), (1, 2, 24000))
                self.assertEqual(source.getnframes(), 6000)
        cancel = result['operations'][-1]
        self.assertTrue(cancel['terminal_cancelled']); self.assertTrue(cancel['cancel_accepted'])
        self.assertEqual(cancel['audio_chunks'], 1)
        with self.assertRaises(FileExistsError): probe._write_sample(files[0].parent, files[0].stem, b'\0\0')
        self.assertEqual(files[0].stat().st_size, 12044)

    def test_cancel_request_without_cancelled_terminal_is_not_a_pass(self):
        self.factory.confirm_cancel = False
        result = self.run_probe()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error']['phase'], 'tts_terminal')
        self.assertTrue(result['cleanup_confirmed'])

    def test_raw_exception_payload_is_not_reported(self):
        with patch.object(probe, '_reference', side_effect=RuntimeError('PRIVATE_RAW_PAYLOAD')):
            result = self.run_probe()
        self.assertNotIn('PRIVATE_RAW_PAYLOAD', json.dumps(result))
        self.assertEqual(result['error'], dict(code='worker_failed', phase='pilot_setup'))

    def test_initialize_and_cancel_future_waits_use_the_configured_distinct_deadlines(self):
        observed = []
        class DeadlineFuture:
            def add_done_callback(self, callback): pass
            def result(self, timeout):
                observed.append(timeout)
                raise TimeoutError('PRIVATE_TIMEOUT_PAYLOAD')
        self.settings.limits.update(ready_seconds=7, cancel_seconds=2)
        with patch.object(SimulatedWorker, 'start', return_value=DeadlineFuture()):
            result = self.run_probe()
        self.assertEqual(result['error'], dict(code='worker_timeout', phase='stt_ready'))
        self.assertEqual(observed, [7]); observed.clear()
        synthesize = SimulatedWorker.synthesize
        def incomplete_cancel(worker, *args):
            result = synthesize(worker, *args)
            return DeadlineFuture() if worker.cancelled else result
        with patch.object(SimulatedWorker, 'synthesize', incomplete_cancel):
            result = self.run_probe()
        self.assertEqual(result['error'], dict(code='worker_timeout', phase='tts_cancel'))
        self.assertEqual(observed, [2])
        self.assertNotIn('PRIVATE_TIMEOUT_PAYLOAD', json.dumps(result))

    def test_initialization_fault_phase_survives_later_generic_worker_exit(self):
        def fail(worker, *, device):
            worker.callback(dict(type='fault', engine_instance=worker.engine_instance,
                code='worker_failed', phase='gpu_synchronize'))
            future = Future(); future.set_exception(HuginError('worker_failed', 'worker_exit'))
            return future
        with patch.object(SimulatedWorker, 'start', fail): result = self.run_probe()
        self.assertEqual(result['error'], dict(code='worker_failed', phase='gpu_synchronize'))
        self.assertTrue(result['cleanup_confirmed'])

    def test_sample_directory_rejects_redirects_without_touching_foreign_files(self):
        target = self.root / 'foreign'; target.mkdir()
        sentinel = target / 'sentinel'; sentinel.write_bytes(b'preserve')
        link = self.root / '.runtime/pilot-audio'
        try: link.symlink_to(target, target_is_directory=True)
        except OSError:
            if os.name != 'nt': raise
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)],
                check=True, capture_output=True)
        result = self.run_probe(samples=True)
        self.assertEqual(result['error'], dict(code='config_invalid', phase='pilot_audio_path'))
        self.assertEqual(sentinel.read_bytes(), b'preserve')
        self.assertEqual(list(target.iterdir()), [sentinel])
        self.assertEqual(self.factory.workers, [])

    def test_cli_remains_descriptive_without_run(self):
        with patch('sys.stdout', new_callable=io.StringIO) as stdout:
            code = probe.main(['--root', str(self.root), '--samples'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())['status'], 'planned')
        self.assertEqual(self.factory.workers, [])


if __name__ == '__main__': unittest.main()
