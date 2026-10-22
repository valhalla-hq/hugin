"""Explicit synthetic old/new section-policy comparison; speech is never played.

Uses real workers, alignment and Controller/native playback with equal-length
silent PCM. No clipboard, microphone, hooks or preference writes. --run requires
Hugin to have quit normally; InstanceGuard enforces exclusivity. No text/audio
is included in the report. Section baselines are frozen from main 9ec85225
(original comparison) or 1c598db (--natural-sections).
"""
from collections import deque
from pathlib import Path
from types import SimpleNamespace as NS
import argparse
import json
import re
import sys
import time

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / 'src'))
from hugin import coordinator as c
from hugin.application import Controller
from hugin.audio import PCMOutput
from hugin.config import load_settings
from hugin.windows.instance import InstanceGuard
from hugin.workers.client import EnginePool, WorkerClient
from probe_live_audio import _Executor
from fixtures.reading_sections_46f1578 import split_reading_sections as review_baseline

_HELD = []  # Failed sessions retain the guard and every owner for cleanup retry.


class _ProbeSession:
    def __init__(self, guard):
        self.guard = guard
        self.controller = None
        self.executors = []
        self.workers = []
        self.io_closed = False

    def cleanup(self):
        if not self.io_closed:
            try:
                if self.controller is not None:
                    self.controller.command('quit')
                    deadline = time.monotonic() + 15
                    # A retry must process Quit even when worker shutdown was
                    # already ready: Quit also re-arms failed native I/O closes.
                    while True:
                        handled = self.controller.pump_once(.005)
                        self.controller.tick()
                        if not handled and self.controller.shutdown_ready():
                            break
                        if time.monotonic() >= deadline:
                            return False
                    if not self.controller.finish_io():
                        return False
                self.io_closed = True
            except (Exception, KeyboardInterrupt):
                return False  # Keep executors usable for the controller's retry.
        complete = all(worker.closed for worker in self.workers)
        for executor in self.executors:
            try:
                closed = executor.close_bounded(time.monotonic() + 3)
            except (Exception, KeyboardInterrupt):
                closed = False
            complete = closed and complete
        if complete:
            try:
                self.guard.close()
            except (Exception, KeyboardInterrupt):
                return False
        return complete


def retry_cleanup():
    """Call on the owning thread; failed owners remain available for another try."""
    for owner in list(_HELD):
        if owner.cleanup():
            _HELD.remove(owner)
    return not _HELD

PARAGRAPH = ('Guten Tag. Hugin markiert beim Vorlesen jedes gesprochene Wort. '
             'Wir machen eine kurze Pause, und lesen dann weiter. ') * 3
LONG_SENTENCE = ('Bei dieser Sprachprobe lesen Freya und Tyr einen längeren Satz, '
                 'während Hugin im Hintergrund den nächsten Abschnitt vorbereitet, '
                 'damit die Wiedergabe flüssig bleibt und jedes Wort passend zur '
                 'Stimme hervorgehoben wird, auch wenn der Text etwas länger ist '
                 'und mehrere Gedanken miteinander verbindet. ')

NATURAL_SENTENCES = ('Dieser kurze erste Satz soll vollständig zusammenbleiben. '
    'Auch dieser zweite Satz sollte in der Mitleseleiste als zusammengehöriger Gedanke erscheinen. '
    'Danach folgt ein weiterer Satz, der den Absatz für unsere Probe verlängert.')
NATURAL_CLAUSES = ('Wenn Hugin den Anfang des Textes vorbereitet, kann es an einer passenden Sprechpause schneiden, '
    'während es den nächsten Teil schon im Hintergrund vorbereitet, damit beim Vorlesen keine störenden Pausen entstehen. '
    'Dieser zusätzliche Satz hält den Test über dem bisherigen Restlimit.')
NATURAL_MIXED = ('Dr. Müller erklärt die Funktion und nennt z. B. den Preis von 12,50 Euro. '
    'Am 12. Oktober beginnt die nächste Leseprobe, und Freya sowie Tyr lesen einen weiteren Absatz vor. '
    'Danach folgt eine vollständige Aussage; sie bleibt beim Vorlesen gut verständlich. '
    'Zum Schluss prüfen wir die Wortmarkierung und beenden diese kurze Probe.')

SHORT_SENTENCES = ('Wir lesen diesen Satz gemeinsam. Der nächste Gedanke bleibt ganz. '
    'Auch kurze Sätze gehören dazu. Die Anzeige folgt unserer Stimme. '
    'Jeder Abschnitt endet sinnvoll. Wir lesen jetzt ruhig weiter. '
    'Zum Schluss endet diese Probe.')


def comparison_cases(*, recheck=False, natural_sections=False, review_fixes=False):
    if review_fixes:
        cases=[('cold','freya','baseline',SHORT_SENTENCES)]
        for voice in ('freya','tyr'):
            for name,text in (('short_sentences',SHORT_SENTENCES),('clauses',NATURAL_CLAUSES)):
                policies=('baseline','candidate') if voice=='freya' else ('candidate','baseline')
                cases.extend((name,voice,policy,text) for policy in policies)
        return cases
    if natural_sections:
        cases = [('cold', 'freya', 'baseline', NATURAL_SENTENCES)]
        for voice in ('freya', 'tyr'):
            for name, text in (('sentences', NATURAL_SENTENCES), ('clauses', NATURAL_CLAUSES),
                               ('mixed', NATURAL_MIXED)):
                policies = ('baseline', 'candidate') if name != 'clauses' else ('candidate', 'baseline')
                cases.extend((name, voice, policy, text) for policy in policies)
        return cases
    if recheck:
        opening = c.Coordinator._split_selection(PARAGRAPH)[0]
        cases = [('cold', 'freya', 'baseline', opening)]
        for repeat in range(3):
            policies = ('baseline', 'candidate') if repeat % 2 == 0 else ('candidate', 'baseline')
            cases.extend((f'opening_{repeat}', 'freya', policy, opening) for policy in policies)
        return cases
    cases = [('cold', 'freya', 'baseline', PARAGRAPH)]
    for voice in ('freya', 'tyr'):
        for name, text in (('paragraph', PARAGRAPH), ('long_sentence', LONG_SENTENCE)):
            policies = ('baseline', 'candidate') if name == 'paragraph' else ('candidate', 'baseline')
            cases.extend((name, voice, policy, text) for policy in policies)
    return cases


def baseline(text):
    chunks = deque()
    offset = 0
    while offset < len(text):
        end = min(offset + 240, len(text))
        window = text[offset:end]
        if end < len(text):
            sentence = list(re.finditer(r'[.!?]["\'”’\)\]]*\s+|\n+', window))
            whitespace = list(re.finditer(r'\s+', window)) if not sentence else []
            boundaries = sentence or whitespace
            if boundaries:
                end = offset + boundaries[-1].end()
        chunk = text[offset:end]
        if chunk.strip():
            chunks.append(chunk)
        offset = end
    return chunks


def natural_baseline(text):
    """Frozen accepted 120-character policy from main1c598db, not the older240."""
    chunks, offset, budget = deque(), 0, 120
    while offset < len(text):
        end = min(offset + budget, len(text))
        window = text[offset:end]
        if len(text) - offset <= min(240, budget + 40):
            end = len(text)
        elif end < len(text):
            sentence = [m for m in re.finditer(r'[.!?]["\'”’\)\]]*\s+|\n+', window)
                        if m.end() >= budget * 2 // 3]
            whitespace = list(re.finditer(r'\s+', window)) if not sentence else []
            if sentence:
                end = offset + sentence[0].end()
            elif whitespace:
                end = offset + whitespace[-1].end()
            else:
                hard_end = min(offset + 240, len(text))
                boundary = re.search(r'\s+', text[offset:hard_end])
                end = offset + boundary.end() if boundary else hard_end
        chunk = text[offset:end]
        if chunk.strip():
            chunks.append(chunk)
            budget = min(240, max(120, len(chunk) * 3 // 2))
        offset = end
    return chunks


class Inputs:
    running = True
    error = None
    def set_cancel_active(self, active): pass
    def stop(self): self.running = False


class Microphone:
    owned = False
    fault = None
    def cancel(self): pass


def run(root, *, codec_batches=False, recheck=False, natural_sections=False, review_fixes=False):
    if _HELD:
        raise RuntimeError('probe_cleanup_pending')
    guard = InstanceGuard()
    if not guard.acquire():
        guard.close()
        raise RuntimeError('Hugin must quit normally before the exclusive probe')
    owner = _ProbeSession(guard)
    _HELD.append(owner)
    controller = None
    instances, executors, runs = [], [], []
    owner.workers = instances
    current, sections, alignment = {}, [], []
    marks = set()
    started, cpu = time.perf_counter(), time.process_time()

    class Pool(EnginePool):
        def start(self, engine, **kwargs):
            bootstrap = ('import sys;sys.path.insert(0,' + repr(str(SOURCE / 'src')) +
                ');from hugin.workers.server import main;raise SystemExit(main())')
            if codec_batches:
                bootstrap = ('import sys;sys.path.insert(0,' + repr(str(SOURCE / 'tools')) +
                    ');from probe_tts_batch import native_worker_main;raise SystemExit(native_worker_main(recheck=' +
                    repr(recheck) + '))')
            worker = WorkerClient(root, engine, self.callback, command=[
                str(root / '.runtime' / engine / 'Scripts/python.exe'), '-c', bootstrap])
            self.workers[engine] = worker
            instances.append(worker)
            return worker.start(**kwargs)

    class Output(PCMOutput):
        def write(self, pcm, job, cancelled, *, started=None, progress=None):
            def observed():
                sections.append(dict(start=time.perf_counter()))
                started()
            return super().write(b'\0' * len(pcm), job, cancelled,
                started=observed if started else None, progress=progress)

        def drain(self, *args, **kwargs):
            result = super().drain(*args, **kwargs)
            if result:
                sections[-1]['end'] = time.perf_counter()
            return result

    class Selection:
        def capture_selection(self, cancelled):
            return NS(status='captured', text=current['text'])
        def close(self): pass

    class ProbeController(Controller):
        def _voice(self): return current.get('voice', 'freya')
        def _effect(self, effect, audio_ack=None):
            if isinstance(effect, c.PersistVoice):
                return False
            if isinstance(effect, c.PlayAudio):
                alignment.append(dict(chars=len(effect.section.text),
                    audio_seconds=len(effect.pcm) / 48000,
                    status=effect.section.marking, words=len(effect.section.words),
                    head_samples=effect.section.words[0].start_sample if effect.section.words else None,
                    tail_samples=len(effect.pcm)//2-effect.section.words[-1].end_sample
                        if effect.section.words else None))
            return super()._effect(effect, audio_ack)

    def publish(view):
        if view.reading_word:
            marks.add((view.reading_index, view.reading_word))
        # The run loop checks errors; publication must remain usable for cleanup
        # after a native close failure has left the controller's error visible.

    def metrics():
        return {w.engine: w.process.metrics() for w in instances if w.process is not None}

    try:
        pool = Pool(root, lambda event: controller.worker_event(event))
        executors = [_Executor(n) for n in (1, 1, 2, 1, 1)]
        owner.executors = executors
        controller = ProbeController(load_settings(root), inputs=Inputs(), microphone=Microphone(),
            clipboard=Selection(), output=Output(), pool=pool, publish=publish,
            **dict(zip(('capture_executor', 'audio_executor', 'maintenance_executor',
                        'selection_executor', 'delivery_executor'), executors)))
        owner.controller = controller
        candidate = c.Coordinator._split_selection
        reference = review_baseline if review_fixes else natural_baseline if natural_sections else baseline
        for name, voice, policy, text in comparison_cases(recheck=recheck,
                natural_sections=natural_sections,review_fixes=review_fixes):
            current.update(text=text, voice=voice)
            controller.core._split_selection = reference if policy == 'baseline' and not codec_batches else candidate
            sections.clear(); alignment.clear(); marks.clear()
            before, begin = metrics(), time.perf_counter()
            print(json.dumps(dict(stage='begin', case=name, voice=voice, policy=policy)), flush=True)
            controller.command('voice', voice); controller.pump_once()
            controller.command('read'); controller.pump_once()
            deadline = time.monotonic() + 120
            while controller.core.snapshot().job is not None or controller.core.snapshot().gpu_slot is not None:
                controller.pump_once(.005); controller.tick()
                if controller._runtime_error or controller.core.snapshot().error:
                    raise RuntimeError('probe_controller_error')
                if time.monotonic() > deadline:
                    raise TimeoutError('reading_start_probe')
            after = metrics()
            row = dict(case=name, voice=voice, policy=policy, sections=len(sections),
                first_play_seconds=round(sections[0]['start']-begin, 3),
                elapsed_seconds=round(time.perf_counter()-begin, 3),
                gaps_ms=[round((b['start']-a['end'])*1000, 2) for a,b in zip(sections, sections[1:])],
                audio_seconds=[round(s['audio_seconds'], 3) for s in alignment],
                alignment=list(alignment), marked_words=len(marks),
                worker_cpu_seconds={engine: round(value['cpu_seconds']-
                    before.get(engine, {}).get('cpu_seconds', 0), 3) for engine,value in after.items()},
                worker_peak_commit_bytes={engine:value['peak_job_commit_bytes'] for engine,value in after.items()})
            runs.append(row)
            print(json.dumps(dict(stage='result', **row)), flush=True)
        if any(worker.device != 'cuda' for worker in instances):
            raise RuntimeError('probe_cpu_fallback')
    finally:
        if not owner.cleanup():
            raise RuntimeError('probe_cleanup_pending')
        _HELD.remove(owner)
    return dict(runs=runs, workers_closed=all(w.closed for w in instances),
        devices={worker.engine:worker.device for worker in instances},
        elapsed_seconds=round(time.perf_counter()-started, 3),
        controller_cpu_seconds=round(time.process_time()-cpu, 3),
        audible_speech=False, native_clock=True, content_persisted=False,
        comparison=('review_fixes_vs_46f1578' if review_fixes else
                    'natural_sections_vs_1c598db' if natural_sections else
                    'codec_batch_8_vs_production' if codec_batches else 'section_policy'),
        note='Cold includes model initialization; warm cases share workers. OS cache uncontrolled. '
             'Peak commit is cumulative per worker family, not GPU VRAM or total process-family peak.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--codec-batches', action='store_true',
                        help='Compare codec batch 8 with production, using current sections for both.')
    modes.add_argument('--codec-recheck', action='store_true',
                        help='Repeat the Freya opening three times with both codec variants.')
    modes.add_argument('--natural-sections', action='store_true',
                       help='Compare natural sentence/clause sections with accepted main1c598db.')
    modes.add_argument('--review-fixes', action='store_true',
                       help='Compare short-sentence fixes with frozen accepted main46f1578.')
    args = parser.parse_args()
    if not args.run:
        print('Plan: exclusive synthetic Freya/Tyr baseline/candidate, real alignment and silent native playback.')
        return 0
    report = run(args.root.resolve(), codec_batches=args.codec_batches or args.codec_recheck,
                 recheck=args.codec_recheck, natural_sections=args.natural_sections,
                 review_fixes=args.review_fixes)
    name = ('review-fixes-native.json' if args.review_fixes else
            'natural-sections-native.json' if args.natural_sections else
            'codec-batch-recheck.json' if args.codec_recheck else
            'codec-batch-native.json' if args.codec_batches else 'reading-start-measure.json')
    target = SOURCE / '.runtime' / name
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(report=str(target), workers_closed=report['workers_closed'])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
