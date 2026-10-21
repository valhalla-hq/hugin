"""Explicit synthetic model -> private IPC -> Controller -> PCMOutput probe.

Default is read-only. --run loads CUDA and plays synthetic Freya/Tyr speech;
the operator must arrange the exclusive pilot pause first. No input hooks,
microphone, clipboard, preference changes, installations or foreign cleanup.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import uuid

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE/'src'))
from hugin.errors import HuginError

TEXT = 'Dies ist eine kurze synthetische Sprachprobe für Hugin. Freya und Tyr lesen denselben deutschen Text.'
MAX_PCM = 30*24000*2
_HELD = []  # A failed cleanup retains its own controller/process owners.


def _failure(error, phase):
    return dict(code=error.code, phase=error.phase) if isinstance(error, HuginError) else dict(code='worker_failed', phase=phase)


def _head(root):
    try:
        return subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):return None


def _run_directory(root):
    runtime = root/'.runtime'
    parent = runtime/'live-audio-probe'
    if not runtime.is_dir() or runtime.resolve() != runtime or parent.resolve() != parent:
        raise HuginError('config_invalid', 'live_probe_path')
    parent.mkdir(exist_ok=True)
    run = parent/str(uuid.uuid4())
    run.mkdir()
    return run


def _read_worker_trace(path):
    with path.open('rb') as source:raw = source.read(262145)
    if len(raw) > 262144:raise HuginError('resource_limit', 'live_probe_metrics')
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {'schema_version', 'operations'} or type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise HuginError('protocol_invalid', 'live_probe_metrics')
    operations = value['operations']
    if not isinstance(operations, list) or len(operations) > 3:
        raise HuginError('protocol_invalid', 'live_probe_metrics')
    for operation in operations:
        if not isinstance(operation, dict) or set(operation) != {'chunks', 'pcm_bytes', 'sha256'}:
            raise HuginError('protocol_invalid', 'live_probe_metrics')
        digest, count, chunks = operation['sha256'], operation['pcm_bytes'], operation['chunks']
        if (not isinstance(digest, str) or len(digest) != 64 or any(char not in '0123456789abcdef' for char in digest)
                or type(count) is not int or not 0 <= count <= 128*MAX_PCM
                or not isinstance(chunks, list) or len(chunks) > 128):
            raise HuginError('protocol_invalid', 'live_probe_metrics')
        for chunk in chunks:
            if (not isinstance(chunk, dict) or set(chunk) != {'ready_clock', 'compute_ms', 'bytes'}
                    or type(chunk['bytes']) is not int or not 0 <= chunk['bytes'] <= MAX_PCM
                    or any(type(chunk[key]) not in (int, float) or not math.isfinite(chunk[key]) or chunk[key] < 0
                        for key in ('ready_clock', 'compute_ms'))):
                raise HuginError('protocol_invalid', 'live_probe_metrics')
    return operations


def _spawn_from_source(command, *, source, trace, owned_process, **kwargs):
    """Runtime interpreter/assets stay selected; worker source is this checkout."""
    if command[1:3] != ['-m', 'hugin.workers.server']:
        raise HuginError('config_invalid', 'live_probe_launcher')
    env = dict(kwargs['env'])
    env['PYTHONPATH'] = str(source/'src')
    kwargs['env'] = env
    return owned_process([command[0], str(source/'tools/probe_live_audio.py'),
        '--_worker-trace', str(trace), *command[3:]], **kwargs)


def _worker(trace, remaining):
    """Probe-only provider timings; no text/PCM/exception payload is persisted."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--root', type=Path, required=True)
    args, _ = parser.parse_known_args(remaining)
    root, trace = args.root.resolve(), trace.resolve()
    if (trace.name != 'worker.json' or trace.parent.parent != root/'.runtime/live-audio-probe'
            or str(uuid.UUID(trace.parent.name)) != trace.parent.name):
        raise HuginError('config_invalid', 'live_probe_path')
    from hugin.workers import engines, server
    base = engines.QwenEngine
    facts = []
    class ObservedEngine(base):
        def synthesize(self, *args):
            operation = dict(chunks=[], pcm_bytes=0, sha256=None)
            facts.append(operation)
            digest = hashlib.sha256()
            stream = super().synthesize(*args)
            try:
                while True:
                    before = time.perf_counter()
                    try:pcm = next(stream)
                    except StopIteration:break
                    ready = time.perf_counter()
                    if len(operation['chunks']) >= 128:
                        raise HuginError('resource_limit', 'live_probe_trace')
                    operation['chunks'].append(dict(ready_clock=ready,
                        compute_ms=(ready-before)*1000, bytes=len(pcm)))
                    operation['pcm_bytes'] += len(pcm)
                    digest.update(pcm)
                    yield pcm
                    del pcm
            finally:
                stream.close()
                operation['sha256'] = digest.hexdigest()
    engines.QwenEngine = ObservedEngine
    sys.argv = [sys.argv[0], *remaining]
    try:return server.main()
    finally:
        with trace.open('x', encoding='utf-8') as output:
            json.dump(dict(schema_version=1, operations=facts), output)


class _Executor(ThreadPoolExecutor):
    def __init__(self, count):
        super().__init__(count, thread_name_prefix='hugin-live-probe')
        self.submitted = []
    def submit(self, *args, **kwargs):
        future = super().submit(*args, **kwargs)
        self.submitted.append(future)
        return future
    def close_bounded(self, deadline):
        self.shutdown(wait=False, cancel_futures=True)
        _, pending = wait(self.submitted, timeout=max(0, deadline-time.monotonic()))
        # All tasks are owned by these executors. Their threads also need an
        # observed exit, rather than Future.done alone, before success.
        for thread in self._threads:
            thread.join(max(0, deadline-time.monotonic()))
        return not pending and not any(thread.is_alive() for thread in self._threads)


def probe(root, *, run=False, cancel=False):
    root = Path(root).resolve()
    from hugin.config import load_settings
    settings = load_settings(root)
    report = dict(schema_version=1, status='planned', source_root=str(SOURCE),
        source_head=_head(SOURCE), runtime_root=str(root), runtime_head=_head(root),
        starts_workers=bool(run), plays_synthetic_audio=bool(run), writes_technical_trace=bool(run),
        voices=['freya', 'tyr'], cancel_after_first_accepted_packet=cancel,
        budgets=dict(provider_retained_pcm_bytes=3*MAX_PCM,
            client_packet_bytes=min(6000, settings.limits['audio_buffer_ms']*24),
            native_buffer_ms=max(1, settings.limits['audio_buffer_ms']//2)),
        unmeasured=['physical working-set RAM', 'GPU peak memory', 'p95',
            'audible quality', 'physical target matrix', 'agent tokens'])
    if not run:return report
    if sys.platform != 'win32':raise HuginError('unsupported', 'live_probe_platform')
    if _HELD:raise HuginError('worker_timeout', 'live_probe_cleanup_pending')
    from hugin.application import Controller
    from hugin import coordinator as c
    from hugin.audio import PCMOutput, _WaveOut
    from hugin.workers import EnginePool
    from hugin.windows.process import OwnedProcess
    directory = _run_directory(root)
    trace_path = directory/'worker.json'
    report.update(status='failed', cleanup_confirmed=False, operations=[])
    started, cpu_started = time.perf_counter(), time.process_time()
    current, workers, executors = None, [], []
    controller = None
    trace_lock = threading.Lock()

    def append(operation, kind, **facts):
        with trace_lock:
            if len(operation['trace']) >= 4096:raise HuginError('resource_limit', 'live_probe_trace')
            operation['trace'].append(dict(kind=kind, clock=time.perf_counter(), **facts))

    class Player(_WaveOut):
        def __init__(self, rate):
            super().__init__(rate)
            self.operation = current
            self.tail = None
        def collect(self, force=False):
            before = self.queued_bytes
            super().collect(force)
            if not force and before and not self.queued_bytes and not self.operation['draining']:
                self.operation['empty_refills'] += 1
                append(self.operation, 'queue_empty', estimated_gap_ms=None if self.tail is None
                    else max(0, (time.perf_counter()-self.tail)*1000))
        def submit(self, pcm):
            before = self.queued_bytes
            super().submit(pcm)
            now = time.perf_counter()
            self.tail = max(now, self.tail or now)+len(pcm)/48000
            self.operation['native_bytes'] += len(pcm)
            self.operation['native_hash'].update(pcm)
            self.operation['peak_queued_bytes'] = max(self.operation['peak_queued_bytes'], self.queued_bytes)
            append(self.operation, 'native_submit', bytes=len(pcm), queued_before=before, queued_after=self.queued_bytes)

    class Output(PCMOutput):
        closed = False
        def write(self, pcm, job, cancelled=lambda:False, *, started=None):
            accepted = super().write(pcm, job, cancelled,started=started)
            if accepted and current['cancel'] and current['cancel_started'] is None:
                current['cancel_started'] = time.monotonic()
                controller.command('cancel')
            return accepted
        def drain(self, *args):
            current['draining'] = True
            return super().drain(*args)
        def close(self):
            super().close()
            self.closed = True

    class Inputs:
        running = True
        error = None
        def set_cancel_active(self, enabled):pass
        def stop(self):self.running = False
    class Microphone:
        owned = False
        fault = None
        def start(self):raise HuginError('unsupported', 'live_probe_microphone')
        def stop(self):raise HuginError('unsupported', 'live_probe_microphone')
        def cancel(self):pass
    class Selection:
        def capture_selection(self, cancelled):return SimpleNamespace(status='captured', text=TEXT)
        def close(self):pass
    class ProbeController(Controller):
        def _voice(self):return 'freya'
        def _effect(self, effect, audio_ack=None):
            if isinstance(effect, c.PersistVoice):return False  # In-memory probe choice only.
            return super()._effect(effect, audio_ack)
    class Pool(EnginePool):
        def start(self, engine, **kwargs):
            try:return super().start(engine, **kwargs)
            finally:
                if engine in self.workers:workers.append(self.workers[engine])

    def callback(event):
        operation = current
        if operation is None:return
        kind = event['type']
        if kind == 'audio':
            operation['in_callback'] += 1
            before = time.perf_counter()
            try:
                if operation['pcm_bytes']+len(event['pcm']) > MAX_PCM:
                    raise HuginError('resource_limit', 'live_probe_audio')
                operation['pcm_bytes'] += len(event['pcm'])
                operation['callback_hash'].update(event['pcm'])
                append(operation, 'ipc_arrival', bytes=len(event['pcm']), offset=event['offset'])
                controller.worker_event(event)
                append(operation, 'callback_ack', wait_ms=(time.perf_counter()-before)*1000)
            except Exception as error:
                operation['error'] = _failure(error, 'live_probe_callback')
                controller.command('cancel')
            finally:operation['in_callback'] -= 1
        else:
            if kind == 'fault':operation['error'] = dict(code=event['code'], phase=event['phase'])
            if kind == 'terminal':
                operation['terminal'] = dict(cancelled=event['cancelled'], code=event['code'],
                    audio_bytes=event['audio_bytes'], clock=time.perf_counter())
            controller.worker_event(event)

    def pump_until(predicate, deadline, phase):
        while not predicate():
            if time.monotonic() >= deadline:raise HuginError('worker_timeout', phase)
            controller.pump_once(.005)
            controller.tick()
            if controller._runtime_error:raise controller._runtime_error
            if controller.core.snapshot().error:
                raise HuginError(controller.core.snapshot().error.code, phase)

    try:
        spawn = lambda command,**kwargs:_spawn_from_source(command, source=SOURCE,
            trace=trace_path, owned_process=OwnedProcess, **kwargs)
        pool = Pool(root, callback, spawn=spawn)
        output = Output(buffer_ms=max(1, settings.limits['audio_buffer_ms']//2), factory=Player)
        executors = [_Executor(count) for count in (1,1,2,1,1)]
        controller = ProbeController(settings, inputs=Inputs(), microphone=Microphone(),
            output=output, clipboard=Selection(), pool=pool, publish=lambda view:None,
            **dict(zip(('capture_executor','audio_executor','maintenance_executor',
                'selection_executor','delivery_executor'), executors)))
        _HELD.append(controller)
        scenarios = [('freya', False), ('tyr', False)]+([('tyr', True)] if cancel else [])
        for voice, cancelling in scenarios:
            controller.command('voice', voice)
            while controller.pump_once():pass
            current = dict(voice=voice, cancel=cancelling, cancel_started=None,
                trace=[], pcm_bytes=0, native_bytes=0, peak_queued_bytes=0, empty_refills=0,
                terminal=None, error=None, draining=False, in_callback=0,
                callback_hash=hashlib.sha256(), native_hash=hashlib.sha256())
            before = time.perf_counter()
            controller.command('read')
            deadline = time.monotonic()+settings.limits['ready_seconds']
            def finished():
                if current['cancel_started'] is not None:
                    if time.monotonic() > current['cancel_started']+settings.limits['cancel_seconds']:
                        raise HuginError('worker_timeout', 'live_probe_cancel')
                snapshot = controller.core.snapshot()
                return current['terminal'] is not None and current['in_callback'] == 0 and snapshot.job is None and not snapshot.cancelling_job and snapshot.gpu_slot is None
            pump_until(finished, deadline, 'live_probe_operation')
            if current['error']:raise HuginError(current['error']['code'], current['error']['phase'])
            if current['terminal']['code'] or current['terminal']['cancelled'] != cancelling:
                raise HuginError('worker_failed', 'live_probe_terminal')
            if not current['native_bytes']:raise HuginError('audio_failed', 'live_probe_no_audio')
            if not cancelling and (current['pcm_bytes'] != current['native_bytes'] or current['callback_hash'].digest() != current['native_hash'].digest()):
                raise HuginError('protocol_invalid', 'live_probe_pcm')
            current['elapsed_seconds'] = time.perf_counter()-before
            current['callback_sha256'] = current.pop('callback_hash').hexdigest()
            current['native_sha256'] = current.pop('native_hash').hexdigest()
            report['operations'].append(current)
            current = None
        if any(worker.device != 'cuda' for worker in workers):
            raise HuginError('worker_failed', 'live_probe_cpu_fallback')
        if any(operation['empty_refills'] for operation in report['operations'] if not operation['cancel']):
            raise HuginError('audio_failed', 'live_probe_underflow')
        report['status'] = 'passed'
    except (Exception, KeyboardInterrupt) as error:
        report['error'] = _failure(error, 'live_probe_interrupted' if isinstance(error, KeyboardInterrupt) else 'live_probe')
    finally:
        cleanup_deadline = time.monotonic()+settings.limits['cancel_seconds']+settings.limits['exit_seconds']+2
        io_closed = False
        if controller is not None:
            try:
                controller.command('quit')
                while not controller.shutdown_ready() and time.monotonic() < cleanup_deadline:
                    controller.pump_once(.005);controller.tick()
                io_closed = controller.shutdown_ready() and controller.finish_io()
            except (Exception, KeyboardInterrupt) as error:
                report['cleanup_error'] = _failure(error, 'live_probe_cleanup')
        executors_closed = all([executor.close_bounded(cleanup_deadline) for executor in executors])
        report['cleanup_confirmed'] = io_closed and executors_closed and all(worker.closed for worker in workers)
        if report['cleanup_confirmed']:
            _HELD.remove(controller)
        else:
            report['status'] = 'failed'
            report.setdefault('cleanup_error', dict(code='worker_timeout', phase='live_probe_cleanup_unconfirmed'))
        report['workers'] = []
        for worker in workers:
            facts = dict(engine=worker.engine, device=worker.device, closed=worker.closed, metrics=None)
            try:
                if worker.closed and worker.process is not None:facts['metrics'] = worker.process.metrics()
            except Exception as error:
                report['status'] = 'failed'
                report['metrics_error'] = _failure(error, 'live_probe_family_metrics')
            report['workers'].append(facts)
        report['elapsed_seconds'] = time.perf_counter()-started
        report['controller_cpu_seconds'] = time.process_time()-cpu_started
    if report['cleanup_confirmed']:
        try:
            report['worker_operations'] = _read_worker_trace(trace_path)
            for operation, provider in zip(report['operations'], report['worker_operations'], strict=True):
                operation['provider_pcm_exact'] = (operation['callback_sha256'] == provider['sha256']
                    and operation['pcm_bytes'] == provider['pcm_bytes']) if not operation['cancel'] else None
                if operation['provider_pcm_exact'] is False:raise HuginError('protocol_invalid', 'live_probe_provider_pcm')
        except Exception as error:
            report['status'] = 'failed'
            report['metrics_error'] = _failure(error, 'live_probe_metrics')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Existing stable Hugin runtime checkout; source comes from this tool checkout.')
    parser.add_argument('--run', action='store_true', help='Explicitly load CUDA and play both synthetic voices after arranging the exclusive pause.')
    parser.add_argument('--cancel', action='store_true', help='After both normal voices, cancel a third synthetic Tyr operation after its first accepted packet.')
    args = parser.parse_args(argv)
    try:report = probe(args.root, run=args.run, cancel=args.cancel)
    except (Exception, KeyboardInterrupt) as error:
        report = dict(status='failed', error=_failure(error, 'live_probe_setup'))
    print(json.dumps(report, indent=2))
    return int(report['status'] == 'failed')


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--_worker-trace':
        raise SystemExit(_worker(Path(sys.argv[2]), sys.argv[3:]))
    raise SystemExit(main())
