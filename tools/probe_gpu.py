"""Explicit serial CUDA pilot using only Hugin's owned workers and synthetic audio.

Default: describe the plan without starting workers or writing samples. --run
loads GPU models; the operator must first arrange the authorized Altstack pause.
No microphone, playback, clipboard, input hooks, installation or process lookup.
"""
from __future__ import annotations

import argparse
from concurrent.futures import TimeoutError
import json
from pathlib import Path
import re
import sys
import threading
import time
import uuid
import wave
import warnings

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / 'src'))
from hugin.config import load_settings, verify_voice_assets
from hugin.errors import HuginError
from hugin.workers import WorkerClient

SYNTHETIC_TEXT = 'Dies ist eine kurze synthetische Sprachprobe für Hugin. Freya und Tyr lesen denselben deutschen Text.'
MAX_PCM = 30 * 24000 * 2
_HELD_CLIENTS = set()  # Failed cleanup keeps the same own-family owner reachable.


def normalize(text):
    return ' '.join(re.findall(r'\w+', text.casefold()))


def _reference(settings):
    voice = settings.voices['tyr']
    expected = normalize(voice.reference_text.read_text(encoding='utf-8'))
    if len(expected.split()) != 17:
        raise HuginError('asset_integrity', 'pilot_reference')
    with wave.open(str(voice.reference), 'rb') as source:
        rate, frames = source.getframerate(), source.getnframes()
        if (source.getnchannels() != 1 or source.getsampwidth() != 2
                or not 0 < rate <= 192000 or not 0 < frames <= rate * 30):
            raise HuginError('asset_integrity', 'pilot_reference')
        pcm = source.readframes(frames)
        if len(pcm) != frames * 2:
            raise HuginError('asset_integrity', 'pilot_reference')
    if rate != 16000:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            import audioop
        pcm, _ = audioop.ratecv(pcm, 2, 1, rate, 16000, None)
    if not pcm or len(pcm) > min(settings.limits['capture_bytes'], 30 * 16000 * 2):
        raise HuginError('resource_limit', 'pilot_reference')
    return pcm, expected


def _sample_directory(root):
    # Resolve the selected checkout once; reject redirects below that boundary.
    runtime = root / '.runtime'
    directory = runtime / 'pilot-audio'
    if not runtime.is_dir() or runtime.resolve() != runtime:
        raise HuginError('config_invalid', 'pilot_audio_path')
    if directory.resolve() != directory:
        raise HuginError('config_invalid', 'pilot_audio_path')
    directory.mkdir(exist_ok=True)
    run = directory / str(uuid.uuid4())
    run.mkdir()  # Never reuse or overwrite a previous run, even our own.
    return run


def _write_sample(directory, voice, pcm):
    path = directory / (voice + '.wav')
    with path.open('xb') as stream, wave.open(stream, 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(pcm)
    return path


class _Events:
    def __init__(self, expected, samples):
        self.expected, self.samples = expected, samples
        self.worker = self.current = None
        self.failure = None

    def begin(self, name, *, cancel=False):
        operation = dict(name=name, request_id=str(uuid.uuid4()), generation=1,
            started=time.perf_counter(), audio_bytes=0, audio_chunks=0,
            first_chunk_seconds=None, result_count=0, transcript_words=0,
            normalized_exact_match=False, pcm=bytearray(), error=None,
            cancel=cancel, cancel_accepted=False, cancel_started=None,
            first_done=threading.Event(), wake=threading.Event())
        self.current = operation
        return operation

    def __call__(self, event):
        operation = self.current
        if event.get('engine_instance') == self.worker.engine_instance and event['type'] == 'fault':
            self.failure = HuginError(event['code'], event['phase'])
        if operation is None or any(event.get(key) != value for key, value in (
                ('engine_instance', self.worker.engine_instance),
                ('request_id', operation['request_id']), ('generation', operation['generation']))):
            return
        try:
            if event['type'] == 'fault':
                operation['error'] = self.failure
                operation['wake'].set()
            elif event['type'] == 'result':
                actual = normalize(event['text'])
                operation['result_count'] += 1
                operation['transcript_words'] = len(actual.split())
                operation['normalized_exact_match'] = actual == self.expected
            elif event['type'] == 'audio':
                pcm = event['pcm']
                if (event['sample_rate'] != 24000 or not pcm or len(pcm) % 2
                        or len(pcm) > 6000 or event['offset'] != operation['audio_bytes']):
                    raise HuginError('protocol_invalid', 'pilot_audio')
                if operation['audio_bytes'] + len(pcm) > MAX_PCM:
                    raise HuginError('resource_limit', 'pilot_audio')
                operation['audio_bytes'] += len(pcm)
                operation['audio_chunks'] += 1
                if operation['first_chunk_seconds'] is None:
                    operation['first_chunk_seconds'] = time.perf_counter() - operation['started']
                if self.samples and not operation['cancel']:
                    operation['pcm'].extend(pcm)
                if operation['cancel'] and operation['audio_chunks'] == 1:
                    operation['cancel_started'] = time.perf_counter()
                    operation['cancel_accepted'] = self.worker.cancel(
                        operation['request_id'], operation['generation'])
                    operation['first_done'].set()
                    operation['wake'].set()
        except Exception as error:
            operation['error'] = error if isinstance(error, HuginError) else HuginError('worker_failed', 'pilot_callback')
            self.worker.cancel_active()
            operation['wake'].set()


def probe(root, *, run=False, samples=False, client_factory=None):
    """Return content-free facts. Injected clients test orchestration, not CUDA."""
    root = Path(root).resolve()
    settings = load_settings(root)
    report = dict(schema_version=1, scenario='serial-own-cuda-synthetic',
        status='planned', starts_workers=bool(run), writes_samples=bool(run and samples),
        steps=['stt_cuda_cold', 'stt_cuda_warm', 'stt_offload', 'stt_close',
            'stt_new_worker_cuda_reload', 'stt_close', 'tts_cuda_init',
            'tts_freya', 'tts_tyr', 'tts_cancel_after_first_chunk', 'tts_close'],
        deadlines_seconds={key: settings.limits[key] for key in ('ready_seconds', 'cancel_seconds', 'exit_seconds')},
        reload_scope='new_worker_after_offload_and_confirmed_family_exit',
        cold_scope='new worker/model; OS file cache uncontrolled',
        unmeasured=['same-process STT reload device', 'physical working-set RAM peak', 'GPU peak memory',
            'p50/p95', 'listening quality', 'physical target matrix', 'Altstack comparison', 'agent tokens'])
    if not run:
        return report
    started, cpu_started = time.perf_counter(), time.process_time()
    workers, operations = [], []
    report.update(status='failed', cleanup_confirmed=False, workers=[], operations=operations)
    phase = 'pilot_setup'

    def wait(future, seconds, label):
        try:
            return future.result(timeout=seconds)
        except TimeoutError:
            raise HuginError('worker_timeout', label) from None

    def open_worker(engine):
        events = _Events(expected, samples)
        worker = client_factory(root, engine, events)
        events.worker = worker
        facts = dict(engine=engine, device=None, closed=False)
        workers.append((worker, facts))
        report['workers'].append(facts)
        _HELD_CLIENTS.add(worker)
        before = time.perf_counter()
        try:
            ready = wait(worker.start(device='cuda'), settings.limits['ready_seconds'], engine + '_ready')
        except HuginError:
            if events.failure: raise events.failure
            raise
        facts.update(device=ready['device'], initialization_seconds=round(time.perf_counter()-before, 6))
        if ready['device'] != 'cuda' or worker.device != 'cuda':
            raise HuginError('worker_failed', engine + '_cpu_fallback')
        return worker, events

    def close_worker(worker, facts):
        try:
            worker.close()
        finally:
            facts['closed'] = worker.closed
        if not worker.closed:
            raise HuginError('worker_timeout', 'pilot_cleanup_unconfirmed')
        _HELD_CLIENTS.discard(worker)
        metrics = worker.process.metrics() if worker.process is not None else None
        facts['family_cpu_seconds'] = None if metrics is None else round(metrics['cpu_seconds'], 6)
        facts['family_peak_job_commit_bytes'] = None if metrics is None else metrics['peak_job_commit_bytes']

    def operation(worker, events, name, *, voice=None, cancel=False):
        active = events.begin(name, cancel=cancel)
        try:
            if voice is None:
                future = worker.transcribe(pcm, active['request_id'], active['generation'])
            else:
                future = worker.synthesize(SYNTHETIC_TEXT, voice, active['request_id'], active['generation'], 'German')
            if cancel:
                future.add_done_callback(lambda _: active['wake'].set())
                if not active['wake'].wait(settings.limits['ready_seconds']):
                    raise HuginError('worker_timeout', 'tts_first_chunk')
                if active['error']: raise active['error']
                if not active['first_done'].is_set():
                    wait(future, 0, 'tts_cancel')
                    raise HuginError('worker_failed', 'tts_cancel_no_audio')
            try:
                terminal = wait(future, settings.limits['cancel_seconds'] if cancel else settings.limits['ready_seconds'], name)
            except HuginError:
                if active['error']: raise active['error']
                raise
            if active['error']: raise active['error']
            facts = dict(name=name, elapsed_seconds=round(time.perf_counter()-active['started'], 6),
                terminal_cancelled=terminal['cancelled'], terminal_audio_bytes=terminal['audio_bytes'])
            operations.append(facts)
            if terminal['code']: raise HuginError(terminal['code'], name)
            if voice is None:
                facts.update(reference_words=17, transcript_words=active['transcript_words'],
                    normalized_exact_match=active['normalized_exact_match'])
                if terminal['cancelled'] or active['result_count'] != 1 or not active['normalized_exact_match']:
                    raise HuginError('worker_failed', 'stt_transcript_mismatch')
            else:
                facts.update(voice=voice, sample_rate=24000, pcm_bytes=active['audio_bytes'],
                    audio_chunks=active['audio_chunks'], first_chunk_seconds=active['first_chunk_seconds'])
                if not active['audio_bytes'] or terminal['cancelled'] != cancel:
                    raise HuginError('worker_failed', 'tts_terminal')
                if cancel:
                    facts.update(cancel_accepted=active['cancel_accepted'],
                        cancel_to_terminal_seconds=round(time.perf_counter()-active['cancel_started'], 6))
                    if not active['cancel_accepted']: raise HuginError('worker_failed', 'tts_cancel')
                elif terminal['audio_bytes'] != active['audio_bytes']:
                    raise HuginError('protocol_invalid', 'pilot_audio')
                elif samples:
                    path = _write_sample(sample_directory, voice, active['pcm'])
                    facts['sample'] = path.relative_to(root).as_posix()
        finally:
            events.current = None
            active['pcm'].clear()

    try:
        if any(not worker.closed for worker in _HELD_CLIENTS):
            raise HuginError('worker_timeout', 'pilot_cleanup_pending')
        if client_factory is None:
            if sys.platform != 'win32': raise HuginError('unsupported', 'pilot_platform')
            from hugin.windows.process import OwnedProcess
            client_factory = lambda root, engine, callback: WorkerClient(root, engine, callback, spawn=OwnedProcess)
        verify_voice_assets(settings)
        pcm, expected = _reference(settings)
        sample_directory = _sample_directory(root) if samples else None
        phase = 'stt_pilot'
        stt, events = open_worker('stt')
        operation(stt, events, 'stt_cold')
        operation(stt, events, 'stt_warm')
        before = time.perf_counter()
        terminal = wait(stt.offload(), settings.limits['ready_seconds'], 'stt_offload')
        if terminal['code'] or terminal['cancelled']: raise HuginError(terminal['code'] or 'worker_failed', 'stt_offload')
        operations.append(dict(name='stt_offload', elapsed_seconds=round(time.perf_counter()-before, 6)))
        close_worker(*workers[-1])
        stt, events = open_worker('stt')
        operation(stt, events, 'stt_reloaded')
        close_worker(*workers[-1])
        phase = 'tts_pilot'
        tts, events = open_worker('tts')
        for voice in ('freya', 'tyr'): operation(tts, events, 'tts_' + voice, voice=voice)
        operation(tts, events, 'tts_cancel', voice='tyr', cancel=True)
        close_worker(*workers[-1])
        report['status'] = 'passed'
    except (Exception, KeyboardInterrupt) as error:
        report['error'] = dict(code=error.code, phase=error.phase) if isinstance(error, HuginError) else dict(
            code='worker_failed', phase='pilot_interrupted' if isinstance(error, KeyboardInterrupt) else phase)
    finally:
        for worker, facts in workers:
            if not worker.closed:
                try: close_worker(worker, facts)
                except (Exception, KeyboardInterrupt) as error:
                    report['status'] = 'failed'
                    report.setdefault('cleanup_errors', []).append(dict(
                        code=error.code if isinstance(error, HuginError) else 'worker_failed',
                        phase=error.phase if isinstance(error, HuginError) else 'pilot_cleanup'))
        report.update(cleanup_confirmed=all(facts['closed'] for _, facts in workers)
                and not any(not worker.closed for worker in _HELD_CLIENTS),
            elapsed_seconds=round(time.perf_counter()-started, 6),
            probe_cpu_seconds=round(time.process_time()-cpu_started, 6))
        metrics = report['workers']
        if any(facts.get('family_cpu_seconds') is None for facts in metrics):
            report['unmeasured'].append('one or more worker-family CPU/peak-job-commit metrics')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('C:/Users/brian/Hugin'))
    parser.add_argument('--run', action='store_true', help='Explicitly load CUDA models and run the serial synthetic pilot.')
    parser.add_argument('--samples', action='store_true', help='With --run, save new bounded synthetic 24 kHz PCM16 WAVs below .runtime/pilot-audio.')
    args = parser.parse_args(argv)
    try:
        report = probe(args.root, run=args.run, samples=args.samples)
    except Exception as error:
        report = dict(status='failed', error=dict(code=error.code, phase=error.phase)
            if isinstance(error, HuginError) else dict(code='worker_failed', phase='pilot_configuration'))
    print(json.dumps(report, indent=2))
    return int(report['status'] == 'failed')


if __name__ == '__main__':
    raise SystemExit(main())
