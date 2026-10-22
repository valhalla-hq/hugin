"""Explicit offline synthetic codec-batch screen. No playback or personal input.

Uses production worker IPC and alignment, with a probe-only Qwen batching override.
Initialization is separate from counterbalanced warm runs. PCM remains in RAM.
"""
from pathlib import Path
import argparse
import json
import sys
import threading
import time
import uuid

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / 'src'))
from hugin.coordinator import Coordinator
from hugin.windows.instance import InstanceGuard
from hugin.workers.client import WorkerClient
from hugin.word_timing import MAX_SECTION_PCM_BYTES, lexeme_spans
from probe_reading_start import PARAGRAPH, LONG_SENTENCE, comparison_cases

_HELD = []


def cases(*, cancellation_only=False):
    rows = []
    for name, text in (('paragraph', PARAGRAPH), ('long_sentence', LONG_SENTENCE)):
        section = Coordinator._split_selection(text)[0]
        for voice in ('freya', 'tyr'):
            for repeat, order in enumerate(((8, 16, 24), (24, 8, 16), (16, 24, 8))):
                for batch in order:
                    rows.append(dict(fixture=name, text=section, voice=voice,
                                     repeat=repeat, batch=batch, cancel=False))
    for after_packet in (False, True):
        for voice in ('freya', 'tyr'):
            for batch in (8, 16, 24):
                rows.append(dict(fixture='cancel', text=PARAGRAPH[:240], voice=voice,
                                 repeat=0, batch=batch, cancel=True, after_packet=after_packet))
    return [row for row in rows if row['cancel']] if cancellation_only else rows


def native_worker_main(*, recheck=False):
    plan = [dict(text=part, voice=voice, batch=8 if policy == 'baseline' else None)
            for _, voice, policy, text in comparison_cases(recheck=recheck)
            for part in Coordinator._split_selection(text)]
    return worker_main(plan)


def worker_main(plan=None, *, cancellation_only=False):
    from hugin.workers import engines, server
    base = engines.QwenEngine

    class ProbeQwen(base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._cases = iter(cases(cancellation_only=cancellation_only) if plan is None else plan)
            self._batch = 8
            original = self.model.generate_voice_clone_streaming

            def generate(**fields):
                if self._batch is not None:
                    fields['chunk_size'] = self._batch
                return original(**fields)
            self.model.generate_voice_clone_streaming = generate

        def synthesize(self, text, voice, language, cancelled):
            case = next(self._cases)
            if text != case['text'] or voice != case['voice']:
                raise RuntimeError('probe_case_mismatch')
            self._batch = case['batch']
            yield from super().synthesize(text, voice, language, cancelled)

    engines.QwenEngine = ProbeQwen
    return server.main()


class Session:
    def __init__(self, guard):
        self.guard, self.workers = guard, []

    def cleanup(self):
        complete = True
        for worker in self.workers:
            try:
                worker.close()
                complete = worker.closed and complete
            except (Exception, KeyboardInterrupt):
                complete = False
        if complete:
            try:
                self.guard.close()
            except (Exception, KeyboardInterrupt):
                return False
        return complete


def retry_cleanup():
    for owner in list(_HELD):
        if owner.cleanup():
            _HELD.remove(owner)
    return not _HELD


class Observation:
    """One request pair owns its callbacks, even across a cancellation terminal."""
    def __init__(self, tts_request, stt_request):
        self.requests = {'tts': tts_request, 'stt': stt_request}
        self.lock = threading.Lock()
        self.pcm, self.alignments, self.faults = bytearray(), [], []
        self.first_audio = None
        self.first_packet = threading.Event()
        self.closed = False

    def receive(self, event):
        if (event.get('request_id') != self.requests.get(event.get('engine'))
                or event.get('generation') != 1):
            return
        with self.lock:
            if self.closed:
                return
            if event['type'] == 'audio':
                if len(self.pcm) + len(event['pcm']) > MAX_SECTION_PCM_BYTES:
                    self.faults.append('audio_bound')
                    raise RuntimeError('audio_bound')
                if self.first_audio is None:
                    self.first_audio = time.perf_counter()
                self.pcm.extend(event['pcm'])
                self.first_packet.set()
            elif event['type'] == 'alignment':
                self.alignments.append(event['result'])
            elif event['type'] == 'fault':
                self.faults.append(event['code'])

    def snapshot(self, *, close=False):
        with self.lock:
            self.closed = self.closed or close
            return dict(pcm=bytes(self.pcm), alignments=list(self.alignments),
                        faults=list(self.faults), first_audio=self.first_audio)


def run(root, *, cancellation_only=False):
    if _HELD:
        raise RuntimeError('probe_cleanup_pending')
    guard = InstanceGuard()
    if not guard.acquire():
        guard.close()
        raise RuntimeError('Hugin must quit normally before the exclusive probe')
    owner = Session(guard)
    _HELD.append(owner)
    rows = []
    started, cpu = time.perf_counter(), time.process_time()
    observation = None

    def receive(event):
        current = observation
        if current is not None:
            current.receive(event)

    def checked(future, *, timeout=60, cancelled=False):
        result = future.result(timeout=timeout)
        if ((observation is not None and observation.snapshot()['faults'])
                or result.get('code') or result.get('cancelled', False) != cancelled):
            raise RuntimeError('probe_worker_failure')
        return result

    def metrics():
        return {w.engine: w.process.metrics() for w in owner.workers}

    try:
        init = {}
        for engine in ('tts', 'stt'):
            bootstrap = ('import sys;sys.path.insert(0,' + repr(str(SOURCE / 'tools')) +
                         ');from probe_tts_batch import worker_main;raise SystemExit(worker_main(cancellation_only=' +
                         repr(cancellation_only) + '))')
            worker = WorkerClient(root, engine, receive, command=[
                str(root / '.runtime' / engine / 'Scripts/python.exe'), '-c', bootstrap])
            owner.workers.append(worker)
            begin = time.perf_counter()
            checked(worker.start(device='cuda'))
            init[engine] = round(time.perf_counter() - begin, 3)
            if worker.device != 'cuda':
                raise RuntimeError('probe_cpu_fallback')
        tts, stt = owner.workers
        for case in cases(cancellation_only=cancellation_only):
            request, alignment_request = str(uuid.uuid4()), str(uuid.uuid4())
            observation = Observation(request, alignment_request)
            before = metrics()
            begin = time.perf_counter()
            future = tts.synthesize(case['text'], case['voice'], request, 1, 'German')
            cancel_started = None
            if case['cancel']:
                if case['after_packet']:
                    if not observation.first_packet.wait(2):
                        raise TimeoutError('probe_first_packet')
                    time.sleep(.01)  # Producer may already be preparing the next batch.
                else:
                    time.sleep(.15)
                cancel_started = time.perf_counter()
                if not tts.cancel(request, 1):
                    raise RuntimeError('probe_cancel_not_active')
            checked(future, timeout=2 if case['cancel'] else 60, cancelled=case['cancel'])
            generated = time.perf_counter()
            if not case['cancel']:
                checked(stt.align(observation.snapshot()['pcm'], case['text'], alignment_request, 1, 'German'))
                if len(observation.snapshot()['alignments']) != 1:
                    raise RuntimeError('probe_missing_alignment')
            completed, after = time.perf_counter(), metrics()
            captured = observation.snapshot(close=True)
            pcm, alignments, first_audio = captured['pcm'], captured['alignments'], captured['first_audio']
            row = {key: value for key, value in case.items() if key != 'text'}
            row.update(chars=len(case['text']), words_expected=len(lexeme_spans(case['text'])),
                tts_seconds=round(generated - begin, 4),
                preparation_seconds=round(completed - begin, 4),
                first_packet_seconds=round(first_audio - begin, 4) if first_audio else None,
                audio_seconds=round(len(pcm) / 48000, 4),
                alignment=alignments[0].status if alignments else None,
                aligned_words=len(alignments[0].words) if alignments else 0,
                cancel_seconds=round(generated - cancel_started, 4) if cancel_started else None,
                worker_cpu_seconds={key:round(value['cpu_seconds']-before[key]['cpu_seconds'], 4)
                                    for key,value in after.items()},
                worker_peak_commit_bytes={key:value['peak_job_commit_bytes'] for key,value in after.items()})
            rows.append(row)
            print(json.dumps(row), flush=True)
            del pcm, alignments, captured
        observation = None
    finally:
        if not owner.cleanup():
            raise RuntimeError('probe_cleanup_pending')
        _HELD.remove(owner)
    return dict(rows=rows, initialization_seconds=init,
        elapsed_seconds=round(time.perf_counter()-started, 3),
        controller_cpu_seconds=round(time.process_time()-cpu, 3),
        workers_closed=all(w.closed for w in owner.workers),
        note='Warm preparation is worker TTS plus actual-audio alignment; no playback or UI. '
             'Initialization measured separately; OS cache uncontrolled. Peak commit is '
             'cumulative per worker family, not working set, simultaneous total or GPU VRAM.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--cancellation-only', action='store_true')
    args = parser.parse_args()
    if not args.run:
        print('Plan: exclusive synthetic 8/16/24 codec batches, both voices, real alignment; no audio playback.')
        return 0
    report = run(args.root.resolve(), cancellation_only=args.cancellation_only)
    target = SOURCE / '.runtime' / ('tts-batch-cancel.json' if args.cancellation_only else 'tts-batch-screen.json')
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(report=str(target), workers_closed=report['workers_closed'])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
