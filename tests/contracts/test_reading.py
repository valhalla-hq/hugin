"""Reading ownership and pause guards; synthetic content/devices only."""
import threading
import time
import unittest

from hugin import coordinator as c
from hugin.audio import PCMOutput
from test_audio import Device
from test_word_reading import prepared


def ready_reading(core, text='Erster Abschnitt. ' * 45):
    core.dispatch(c.ReadToggle())
    job=core.snapshot().job
    core.dispatch(c.SelectionReady(job,text))
    init=core.snapshot().gpu_slot
    core.dispatch(c.EngineReady(init));core.dispatch(c.EngineTerminal(init))
    return job,core.snapshot().gpu_slot


class ReadingOwnership(unittest.TestCase):
    def test_prepared_text_does_not_advance_played_section_and_cancel_forgets(self):
        core=c.Coordinator(instance_id='fixture')
        job,op=ready_reading(core)
        self.assertIsNone(core.snapshot().reading_section)
        first=prepared(core,op)
        self.assertIsNone(core.snapshot().reading_section)
        core.dispatch(c.SectionStarted(job,first.section))
        self.assertEqual(core.snapshot().reading_section.index,1)
        core.dispatch(c.AudioFinished(job,first.sequence))
        second=prepared(core,core.snapshot().gpu_slot)
        self.assertEqual(core.snapshot().reading_section,first.section)
        core.dispatch(c.SectionStarted(job,second.section))
        self.assertEqual(core.snapshot().reading_section.index,2)
        core.dispatch(c.Cancel())
        self.assertIsNone(core.snapshot().reading_section)
        core.dispatch(c.SectionStarted(job,first.section))
        self.assertIsNone(core.snapshot().reading_section)

    def test_pause_is_job_bound_and_blocks_next_section_until_resume(self):
        core=c.Coordinator(instance_id='fixture')
        job,op=ready_reading(core)
        self.assertEqual(core.dispatch(c.PauseReading(job.request_id)),())
        effect=prepared(core,op)
        core.dispatch(c.SectionStarted(job,effect.section))
        self.assertEqual(core.dispatch(c.PauseReading('stale')),())
        self.assertFalse(core.snapshot().reading_paused)
        effects=core.dispatch(c.PauseReading(job.request_id))
        self.assertTrue(core.snapshot().reading_paused)
        self.assertTrue(any(isinstance(e,c.PauseAudio) and e.paused for e in effects))
        core.dispatch(c.AudioFinished(job,effect.sequence))
        self.assertIsNone(core.snapshot().gpu_slot)
        effects=core.dispatch(c.PauseReading(job.request_id))
        self.assertFalse(core.snapshot().reading_paused)
        self.assertTrue(any(isinstance(e,c.BeginEngine) for e in effects))
        core.dispatch(c.DictationToggle())
        self.assertIsNone(core.snapshot().reading_section)
        self.assertFalse(core.snapshot().reading_paused)


class PauseDevice(Device):
    def __init__(self,rate):
        super().__init__(rate);self.paused=False;self.release=False
    def pause(self,paused):self.paused=paused
    def collect(self):
        if self.release and not self.paused:self.queued_bytes=0


class ReadingOutput(unittest.TestCase):
    def test_pause_preserves_pcm_and_cancel_unblocks_without_waiting_for_writer(self):
        device=PauseDevice(24000)
        output=PCMOutput(factory=lambda rate:device,buffer_ms=125)
        self.addCleanup(output.close)
        output.start('one')
        self.assertTrue(output.write(b'\1\0'*100,'one'))
        self.assertFalse(output.pause('stale',True))
        self.assertTrue(output.pause('one',True))
        before=list(device.writes)
        result=[]
        writer=threading.Thread(target=lambda:result.append(output.write(b'\2\0'*8000,'one')))
        writer.start()
        time.sleep(.03)
        self.assertEqual(device.writes,before)
        self.assertTrue(writer.is_alive())
        device.release=True
        self.assertTrue(output.pause('one',False))
        writer.join(1)
        self.assertFalse(writer.is_alive())
        self.assertEqual(result,[True])
        self.assertEqual(b''.join(device.writes),b'\1\0'*100+b'\2\0'*8000)
        output.pause('one',True)
        blocked=threading.Thread(target=lambda:result.append(output.write(b'\3\0','one')))
        blocked.start();time.sleep(.01);output.stop();blocked.join(1)
        self.assertFalse(blocked.is_alive());self.assertEqual(result,[True,False])
        self.assertNotIn(b'\3\0',device.writes)
