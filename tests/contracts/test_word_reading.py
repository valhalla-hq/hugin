"""Public reading lifecycle: prepare one section, align it, then play it."""
import unittest
from hugin import coordinator as c
from hugin.word_timing import AlignmentResult,WordTiming,MAX_SECTION_PCM_BYTES


def begin(core,text='Hallo Welt.'):
    core.dispatch(c.ReadToggle());job=core.snapshot().job
    core.dispatch(c.SelectionReady(job,text));operation=core.snapshot().gpu_slot
    core.dispatch(c.EngineReady(operation));core.dispatch(c.EngineTerminal(operation))
    return job,core.snapshot().gpu_slot


def prepared(core,synthesis,pcm=b'\0\0',result=None,effects=None):
    """Drive the public worker events, retaining every native terminal barrier."""
    core.dispatch(c.EngineAudio(synthesis,pcm))
    core.dispatch(c.EngineTerminal(synthesis))
    operation=core.snapshot().gpu_slot
    if operation.action==c.Action.INITIALIZE:
        core.dispatch(c.EngineReady(operation));core.dispatch(c.EngineTerminal(operation))
        operation=core.snapshot().gpu_slot
    assert operation.action==c.Action.ALIGN
    core.dispatch(c.EngineAlignment(operation,result or AlignmentResult('rejected_path',())))
    completed=core.dispatch(c.EngineTerminal(operation))
    if effects is not None:effects.extend(completed)
    return next(e for e in completed if isinstance(e,c.PlayAudio))


class WordReadingContracts(unittest.TestCase):
    def test_one_next_section_prepares_during_playback_without_early_display_or_extra_prefetch(self):
        core=c.Coordinator(instance_id='prefetch-word')
        job,synthesis=begin(core,'Ein kurzer Satz. '*70)
        first=prepared(core,synthesis)
        core.dispatch(c.SectionStarted(job,first.section))
        following=core.snapshot().gpu_slot
        self.assertIsNotNone(following,'next section should prepare while current audio plays')
        self.assertEqual(following.action,c.Action.SYNTHESIZE)
        core.dispatch(c.EngineAudio(following,b'\0\0'))
        core.dispatch(c.EngineTerminal(following))
        alignment=core.snapshot().gpu_slot
        core.dispatch(c.EngineAlignment(alignment,AlignmentResult('rejected_path',())))
        effects=core.dispatch(c.EngineTerminal(alignment))
        self.assertFalse(any(isinstance(e,(c.PlayAudio,c.BeginEngine)) for e in effects))
        self.assertEqual(core.snapshot().reading_section,first.section)
        self.assertIsNone(core.snapshot().gpu_slot)
        effects=core.dispatch(c.AudioFinished(job,first.sequence))
        second,=[e for e in effects if isinstance(e,c.PlayAudio)]
        self.assertEqual(second.section.index,2)
        self.assertEqual(core.snapshot().gpu_slot.action,c.Action.SYNTHESIZE)

    def test_audio_cannot_play_until_synthesis_terminal_and_alignment_terminal(self):
        core=c.Coordinator(instance_id='word-fixture')
        job,synthesis=begin(core)
        effects=core.dispatch(c.EngineAudio(synthesis,b'\0\0'*12000))
        self.assertFalse(any(isinstance(e,c.PlayAudio) for e in effects),
                         'unprepared speech must not escape before its word times')
        self.assertEqual(core.snapshot().gpu_slot,synthesis)
        effects=core.dispatch(c.EngineTerminal(synthesis))
        initialize=core.snapshot().gpu_slot
        self.assertEqual(initialize.engine,c.Engine.STT)
        self.assertEqual(initialize.action,c.Action.INITIALIZE)
        core.dispatch(c.EngineReady(initialize));core.dispatch(c.EngineTerminal(initialize))
        alignment=core.snapshot().gpu_slot
        self.assertEqual(alignment.action,c.Action.ALIGN)
        from hugin.word_timing import AlignmentResult,WordTiming
        result=AlignmentResult('aligned',(WordTiming(0,5,0,6000),WordTiming(6,11,6000,12000)))
        effects=core.dispatch(c.EngineAlignment(alignment,result))
        self.assertFalse(any(isinstance(e,c.PlayAudio) for e in effects))
        self.assertEqual(core.snapshot().gpu_slot,alignment)
        effects=core.dispatch(c.EngineTerminal(alignment))
        play,= [e for e in effects if isinstance(e,c.PlayAudio)]
        self.assertEqual(play.job,job)
        self.assertEqual(play.pcm,b'\0\0'*12000)
        self.assertEqual(play.section.words,result.words)
        self.assertIsNone(core.snapshot().gpu_slot)
        core.dispatch(c.SectionStarted(job,play.section))
        core.dispatch(c.WordProgress(job,1,(6,11)))
        self.assertEqual(core.snapshot().reading_word,(6,11))
        core.dispatch(c.AudioFinished(job,play.sequence))
        self.assertEqual(core.snapshot().state,c.State.IDLE)
        self.assertIsNone(core.snapshot().reading_word)

    def test_cancel_alignment_retains_gpu_owner_until_terminal_and_discards_words(self):
        core=c.Coordinator(instance_id='cancel-word')
        job,synthesis=begin(core)
        core.dispatch(c.EngineAudio(synthesis,b'\0\0'*12000))
        core.dispatch(c.EngineTerminal(synthesis))
        init=core.snapshot().gpu_slot
        core.dispatch(c.EngineReady(init));core.dispatch(c.EngineTerminal(init))
        alignment=core.snapshot().gpu_slot
        core.dispatch(c.DictationToggle());core.dispatch(c.AudioReset(job))
        new=core.snapshot().job
        self.assertEqual(new.kind,c.JobKind.DICTATION)
        self.assertEqual(core.snapshot().gpu_slot,alignment)
        core.dispatch(c.RecordingStarted(new));core.dispatch(c.DictationToggle())
        core.dispatch(c.RecordingStopped(new,b'\0\0'*160))
        self.assertEqual(core.snapshot().gpu_slot,alignment)
        core.dispatch(c.EngineAlignment(alignment,AlignmentResult('rejected_path',())))
        effects=core.dispatch(c.EngineTerminal(alignment))
        self.assertFalse(any(isinstance(e,c.PlayAudio) for e in effects))
        self.assertEqual(core.snapshot().gpu_slot.action,c.Action.TRANSCRIBE)
        self.assertIsNone(core.snapshot().reading_word)

    def test_paused_word_cannot_advance_and_unavailable_position_clears_it(self):
        core=c.Coordinator(instance_id='pause-word')
        job,synthesis=begin(core)
        result=AlignmentResult('aligned',(WordTiming(0,5,0,6000),WordTiming(6,11,6000,12000)))
        play=prepared(core,synthesis,b'\0\0'*12000,result)
        core.dispatch(c.SectionStarted(job,play.section))
        core.dispatch(c.WordProgress(job,1,(0,5)))
        core.dispatch(c.PauseReading(job.request_id))
        core.dispatch(c.WordProgress(job,1,(6,11)))
        self.assertEqual(core.snapshot().reading_word,(0,5))
        core.dispatch(c.PauseReading(job.request_id))
        core.dispatch(c.WordProgress(job,2,(6,11)))
        self.assertEqual(core.snapshot().reading_word,(0,5))
        core.dispatch(c.WordProgress(job,1,None,False))
        self.assertIsNone(core.snapshot().reading_word)
        self.assertEqual(core.snapshot().reading_marking,'unavailable_position')
        core.dispatch(c.Cancel());core.dispatch(c.WordProgress(job,1,(6,11)))
        self.assertIsNone(core.snapshot().reading_word)

    def test_unavailable_alignment_preserves_complete_audio_and_reports_section_only(self):
        core=c.Coordinator(instance_id='unavailable-word')
        job,synthesis=begin(core)
        pcm=b'\1\0'*12000
        play=prepared(core,synthesis,pcm,AlignmentResult('unavailable_duration',()))
        self.assertEqual(play.pcm,pcm)
        core.dispatch(c.SectionStarted(job,play.section))
        self.assertEqual(core.snapshot().reading_marking,'unavailable_duration')
        self.assertIsNone(core.snapshot().reading_word)

    def test_section_audio_limit_cancels_producer_without_early_playback(self):
        core=c.Coordinator(instance_id='bounded-word')
        job,synthesis=begin(core)
        produced=0
        while produced<=MAX_SECTION_PCM_BYTES:
            effects=core.dispatch(c.EngineAudio(synthesis,b'\0\0'*32000))
            self.assertFalse(any(isinstance(e,c.PlayAudio) for e in effects))
            produced+=64000
        self.assertEqual(core.snapshot().error.code,'resource_limit')
        self.assertEqual(core.snapshot().gpu_slot,synthesis)
        core.dispatch(c.AudioReset(job));core.dispatch(c.EngineTerminal(synthesis))
        self.assertIsNone(core.snapshot().gpu_slot)
