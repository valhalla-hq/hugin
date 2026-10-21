"""Observable reducer contracts; these tests never open devices or workers."""
from dataclasses import replace
import unittest

from hugin.coordinator import (
    Action, AudioFinished, AudioReset, BeginEngine, Busy, Cancel, CancelDelivery,
    CancelEngine, CaptureSelection, Coordinator, CopyResult, CopyText, DeleteResult,
    DeliverText, DeliveryCommit, DeliveryFinished, DictationToggle, Engine,
    EngineAudio, EngineExited, EngineFault, EngineReady, EngineResult,
    EngineTerminal, JobKind, Limits, PersistVoice, PlayAudio, ReadToggle,
    RecordingStarted, RecordingStopped, ResetAudio, RetryCleanup, SelectionReady, SetEscape,
    Shutdown, StageDelivery, StartRecording, State, StopRecording, Tick,
    VoiceSelected,
)
from hugin.errors import HuginError
from test_word_reading import prepared


class CoordinatorContracts(unittest.TestCase):
    def setUp(self):
        self.core = Coordinator(instance_id='synthetic-run', now=10)

    def effects(self, event, effect_type):
        return [item for item in self.core.dispatch(event) if isinstance(item, effect_type)]

    def record(self):
        start, = self.effects(DictationToggle(), StartRecording)
        self.core.dispatch(RecordingStarted(start.job))
        return start.job

    def stop(self, job):
        self.core.dispatch(DictationToggle())
        return self.effects(RecordingStopped(job, b'\x00\x00' * 4, 'synthetic-target'), BeginEngine)

    def initialized(self, operation):
        self.core.dispatch(EngineReady(operation))
        begin, = self.effects(EngineTerminal(operation), BeginEngine)
        return begin.operation

    def transcription(self, text='Synthetic dictation'):
        job = self.record()
        begin, = self.stop(job)
        operation = self.initialized(begin.operation) if begin.operation.action == Action.INITIALIZE else begin.operation
        stage, = self.effects(EngineResult(operation, text), StageDelivery)
        return job, operation, stage

    def reading(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        begin, = self.effects(SelectionReady(capture.job, 'Synthetic selection'), BeginEngine)
        operation = self.initialized(begin.operation) if begin.operation.action == Action.INITIALIZE else begin.operation
        return capture.job, operation

    def finish_delivery(self, job, operation):
        self.core.dispatch(DeliveryCommit(job, 'own-transaction', True))
        self.core.dispatch(DeliveryFinished(job))
        self.core.dispatch(EngineTerminal(operation))

    def test_recording_does_not_wait_for_engine_readiness(self):
        effects = self.core.dispatch(DictationToggle())
        self.assertEqual(effects[0], SetEscape(True))
        start, = [item for item in effects if isinstance(item, StartRecording)]
        self.assertEqual(self.core.snapshot().state, State.STARTING)
        self.assertIsNone(self.core.snapshot().gpu_slot)
        self.assertEqual(start.job.kind, JobKind.DICTATION)
        self.assertTrue(self.core.snapshot().escape_reserved)
        self.core.dispatch(RecordingStarted(start.job))
        self.assertEqual(self.core.snapshot().state, State.RECORDING)

    def test_failed_microphone_start_does_not_claim_recording(self):
        start, = self.effects(DictationToggle(), StartRecording)
        self.core.dispatch(RecordingStarted(start.job, HuginError('microphone_failed')))
        self.assertEqual(self.core.snapshot().state, State.ERROR)
        self.assertIsNone(self.core.snapshot().job)
        self.assertFalse(self.core.snapshot().escape_reserved)

    def test_stop_initializes_then_transcribes_and_waits_for_terminal(self):
        job = self.record()
        begin, = self.stop(job)
        self.assertEqual(begin.operation.action, Action.INITIALIZE)
        self.assertEqual(begin.operation.engine, Engine.STT)
        self.assertEqual(self.core.dispatch(EngineReady(begin.operation)), ())
        self.assertEqual(self.core.snapshot().gpu_slot, begin.operation)
        operation = self.initialized(begin.operation)
        self.assertEqual(operation.action, Action.TRANSCRIBE)
        self.assertEqual(operation.job, job)

    def test_direct_toggles_are_busy_during_dictation_processing(self):
        job = self.record()
        self.assertEqual(len(self.effects(ReadToggle(), Busy)), 1)
        self.stop(job)
        self.assertEqual(len(self.effects(DictationToggle(), Busy)), 1)
        self.assertEqual(len(self.effects(ReadToggle(), Busy)), 1)
        self.assertEqual(self.core.snapshot().job, job)

    def test_read_toggle_cancels_selection_before_any_audio(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        reset, = self.effects(ReadToggle(), ResetAudio)
        self.assertEqual(reset.job, capture.job)
        self.assertEqual(self.core.dispatch(SelectionReady(capture.job, 'Late text')), ())
        self.core.dispatch(AudioReset(capture.job))
        self.assertEqual(self.core.snapshot().state, State.IDLE)

    def test_dictation_preempts_tts_only_after_audio_reset(self):
        old_job, operation = self.reading()
        effects = self.core.dispatch(DictationToggle())
        self.assertTrue(any(isinstance(item, CancelEngine) for item in effects))
        self.assertFalse(any(isinstance(item, StartRecording) for item in effects))
        start, = self.effects(AudioReset(old_job), StartRecording)
        self.assertGreater(start.job.generation, old_job.generation)
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.assertEqual(self.core.snapshot().retired_operations, (operation,))
        self.assertEqual(self.core.dispatch(EngineAudio(operation, b'\x00\x00')), ())

    def test_rear_stop_then_front_starts_recording_while_gpu_cancel_runs(self):
        old_job, operation = self.reading()
        self.core.dispatch(ReadToggle())
        self.core.dispatch(AudioReset(old_job))
        start, = self.effects(DictationToggle(), StartRecording)
        self.assertEqual(self.core.snapshot().state, State.STARTING)
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.core.dispatch(RecordingStarted(start.job))
        self.assertEqual(self.stop(start.job), [])
        next_begin, = self.effects(EngineTerminal(operation), BeginEngine)
        self.assertEqual(next_begin.operation.engine, Engine.STT)
        self.assertEqual(self.core.snapshot().job, start.job)
        self.assertEqual(self.core.dispatch(EngineTerminal(operation)), ())
        self.assertEqual(self.core.snapshot().gpu_slot, next_begin.operation)

    def test_front_during_pending_rear_cancel_queues_until_reset(self):
        old_job, _ = self.reading()
        self.core.dispatch(ReadToggle())
        self.assertEqual(self.effects(DictationToggle(), StartRecording), [])
        start, = self.effects(AudioReset(old_job), StartRecording)
        self.assertEqual(start.job.kind, JobKind.DICTATION)

    def test_audio_reset_failure_never_opens_microphone(self):
        old_job, _ = self.reading()
        self.core.dispatch(DictationToggle())
        self.assertEqual(self.effects(AudioReset(old_job, False), StartRecording), [])
        self.assertEqual(self.core.snapshot().state, State.ERROR)
        self.assertEqual(self.core.snapshot().error.code, 'audio_failed')
        self.assertEqual(self.effects(DictationToggle(), StartRecording), [])

    def test_cancel_during_initialization_keeps_slot_until_real_terminal(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        begin, = self.effects(SelectionReady(capture.job, 'Selection'), BeginEngine)
        self.core.dispatch(DictationToggle())
        start, = self.effects(AudioReset(capture.job), StartRecording)
        self.core.dispatch(RecordingStarted(start.job))
        self.assertEqual(self.stop(start.job), [])
        self.core.dispatch(EngineReady(begin.operation))
        self.assertEqual(self.core.snapshot().gpu_slot, begin.operation)
        next_begin, = self.effects(EngineTerminal(begin.operation), BeginEngine)
        self.assertEqual(next_begin.operation.engine, Engine.STT)

    def test_escape_before_delivery_commit_suppresses_all_insertions(self):
        job, operation, _ = self.transcription()
        self.assertEqual(len(self.effects(Cancel(), CancelDelivery)), 1)
        self.assertEqual(self.effects(DeliveryCommit(job, 'own-transaction', True), DeliverText), [])
        self.assertEqual(self.core.snapshot().result.text, 'Synthetic dictation')
        self.core.dispatch(DeliveryFinished(job))
        self.core.dispatch(EngineTerminal(operation))
        self.assertEqual(self.core.snapshot().state, State.IDLE)
        self.assertFalse(self.core.snapshot().escape_reserved)

    def test_delivery_commit_is_once_and_cancel_afterwards_never_undoes(self):
        job, operation, _ = self.transcription()
        delivered, = self.effects(DeliveryCommit(job, 'own-transaction', True), DeliverText)
        self.assertEqual(delivered.job, job)
        self.assertEqual(self.effects(DeliveryCommit(job, 'own-transaction', True), DeliverText), [])
        self.core.dispatch(Cancel())
        self.core.dispatch(DeliveryFinished(job))
        self.core.dispatch(EngineTerminal(operation))
        self.assertEqual(self.core.snapshot().result.text, 'Synthetic dictation')

    def test_invalid_target_commit_keeps_result_without_delivery(self):
        job, operation, _ = self.transcription()
        self.assertEqual(self.effects(DeliveryCommit(job, 'changed-transaction', False), DeliverText), [])
        self.assertEqual(self.core.snapshot().error.code, 'target_changed')
        self.assertEqual(self.core.snapshot().result.text, 'Synthetic dictation')
        self.core.dispatch(DeliveryFinished(job))
        self.core.dispatch(EngineTerminal(operation))

    def test_cancel_recording_waits_for_closed_capture_and_rejects_late_stop(self):
        job = self.record()
        stop, = self.effects(Cancel(), StopRecording)
        self.assertTrue(stop.discard)
        self.assertEqual(len(self.effects(DictationToggle(), Busy)), 1)
        self.assertEqual(self.effects(RecordingStopped(job, b'late', 'target'), BeginEngine), [])
        self.assertEqual(self.core.snapshot().state, State.IDLE)
        self.assertEqual(self.core.dispatch(RecordingStarted(job)), ())

    def test_stale_result_or_wrong_worker_identity_cannot_publish(self):
        job, operation, _ = self.transcription('Previous')
        self.finish_delivery(job, operation)
        current = self.record()
        self.assertEqual(self.core.dispatch(EngineResult(operation, 'Late secret')), ())
        forged = replace(operation, engine_instance='foreign-worker')
        self.assertEqual(self.core.dispatch(EngineTerminal(forged)), ())
        self.assertEqual(self.core.snapshot().job, current)
        self.assertEqual(self.core.snapshot().result.text, 'Previous')

    def test_result_slot_replaces_expires_copies_and_cancel_preserves(self):
        job, operation, _ = self.transcription('First')
        self.finish_delivery(job, operation)
        abandoned = self.record()
        self.core.dispatch(Cancel())
        self.core.dispatch(RecordingStopped(abandoned))
        self.assertEqual(self.core.snapshot().result.text, 'First')
        job, operation, _ = self.transcription('Second')
        self.finish_delivery(job, operation)
        copy, = self.effects(CopyResult(), CopyText)
        self.assertEqual(copy.text, 'Second')
        self.core.dispatch(Tick(309.999))
        self.assertIsNotNone(self.core.snapshot().result)
        self.core.dispatch(Tick(310))
        self.assertIsNone(self.core.snapshot().result)
        self.assertEqual(self.core.dispatch(CopyResult()), ())

    def test_delete_and_shutdown_release_result_slot(self):
        job, operation, _ = self.transcription()
        self.finish_delivery(job, operation)
        self.core.dispatch(DeleteResult())
        self.assertIsNone(self.core.snapshot().result)
        job, operation, _ = self.transcription()
        self.finish_delivery(job, operation)
        self.core.dispatch(Shutdown())
        self.assertEqual(self.core.snapshot().state, State.STOPPING)
        self.assertIsNone(self.core.snapshot().result)
        self.assertEqual(self.core.dispatch(DictationToggle()), ())

    def test_voice_change_cancels_tts_and_applies_only_to_next_job(self):
        job, operation = self.reading()
        effects = self.core.dispatch(VoiceSelected('tyr'))
        self.assertIn(PersistVoice('tyr'), effects)
        self.assertTrue(any(isinstance(item, ResetAudio) for item in effects))
        self.core.dispatch(AudioReset(job))
        self.core.dispatch(EngineTerminal(operation))
        capture, = self.effects(ReadToggle(), CaptureSelection)
        begin, = self.effects(SelectionReady(capture.job, 'Next'), BeginEngine)
        self.assertEqual(begin.voice, 'tyr')
        self.assertEqual(self.core.snapshot().voice, 'tyr')

    def test_voice_change_during_recording_leaves_job_intact(self):
        job = self.record()
        effects = self.core.dispatch(VoiceSelected('tyr'))
        self.assertEqual(effects, (PersistVoice('tyr'),))
        self.assertEqual(self.core.snapshot().job, job)
        self.assertEqual(self.core.snapshot().state, State.RECORDING)

    def test_unknown_voice_is_visible_without_fallback(self):
        self.core.dispatch(VoiceSelected('not-a-voice'))
        self.assertEqual(self.core.snapshot().voice, 'freya')
        self.assertEqual(self.core.snapshot().error.code, 'config_invalid')

    def test_empty_selection_never_schedules_engine(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        self.assertEqual(self.effects(SelectionReady(capture.job, ' \n'), BeginEngine), [])
        self.assertEqual(self.core.snapshot().error.code, 'selection_empty')

    def test_tts_waits_for_preparation_and_audio_drain(self):
        job, operation = self.reading()
        play = prepared(self.core, operation)
        self.assertEqual(play.job, job)
        self.assertIsNotNone(self.core.snapshot().job)
        self.core.dispatch(AudioFinished(job, play.sequence))
        self.assertEqual(self.core.snapshot().state, State.IDLE)

    def test_engine_fault_keeps_resource_owned_until_verified_exit(self):
        job, operation = self.reading()
        self.core.dispatch(EngineFault(operation, HuginError('worker_failed', 'raw private payload')))
        self.core.dispatch(AudioReset(job))
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.assertEqual(self.core.snapshot().error.phase, 'engine')
        self.core.dispatch(EngineExited(Engine.TTS, 'foreign-worker'))
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.core.dispatch(EngineExited(Engine.TTS, operation.engine_instance))
        self.assertIsNone(self.core.snapshot().gpu_slot)

    def test_transcript_limit_is_utf8_bytes_and_never_replaces_slot_on_error(self):
        self.core = Coordinator(instance_id='limited', limits=Limits(transcript_bytes=8))
        job = self.record()
        begin, = self.stop(job)
        operation = self.initialized(begin.operation)
        self.assertEqual(self.effects(EngineResult(operation, 'é' * 5), StageDelivery), [])
        self.assertIsNone(self.core.snapshot().result)
        self.assertEqual(self.core.snapshot().error.code, 'resource_limit')

    def test_out_of_phase_result_and_terminal_without_result_fail_closed(self):
        job = self.record()
        begin, = self.stop(job)
        self.assertEqual(self.effects(EngineResult(begin.operation, 'Too early'), StageDelivery), [])
        self.assertEqual(self.core.snapshot().error.code, 'protocol_invalid')

    def test_terminal_without_complete_transcript_never_stages_delivery(self):
        job = self.record()
        begin, = self.stop(job)
        operation = self.initialized(begin.operation)
        self.assertEqual(self.effects(EngineTerminal(operation), StageDelivery), [])
        self.assertEqual(self.core.snapshot().error.code, 'protocol_invalid')
        self.assertIsNone(self.core.snapshot().result)

    def test_cancel_transcribing_blocks_until_actual_terminal(self):
        job = self.record()
        begin, = self.stop(job)
        operation = self.initialized(begin.operation)
        self.core.dispatch(Cancel())
        self.assertEqual(len(self.effects(DictationToggle(), Busy)), 1)
        self.assertEqual(self.core.dispatch(EngineResult(operation, 'Late')), ())
        self.core.dispatch(EngineTerminal(operation))
        self.assertEqual(self.core.snapshot().state, State.IDLE)
        self.assertEqual(len(self.effects(DictationToggle(), StartRecording)), 1)

    def test_old_and_foreign_terminals_cannot_release_new_slot(self):
        old_job, old_operation = self.reading()
        self.core.dispatch(DictationToggle())
        # Native termination may precede audio reset; it cannot open the mic.
        self.assertEqual(self.effects(EngineTerminal(old_operation), StartRecording), [])
        start, = self.effects(AudioReset(old_job), StartRecording)
        self.core.dispatch(RecordingStarted(start.job))
        new_begin, = self.stop(start.job)
        self.assertEqual(self.core.dispatch(EngineTerminal(old_operation)), ())
        foreign = replace(new_begin.operation, engine_instance=old_operation.engine_instance)
        self.assertEqual(self.core.dispatch(EngineTerminal(foreign)), ())
        self.assertEqual(self.core.snapshot().gpu_slot, new_begin.operation)
        self.assertEqual(self.core.dispatch(AudioReset(old_job)), ())
        self.assertEqual(self.core.snapshot().job, start.job)

    def test_old_tts_fault_does_not_fail_new_recording(self):
        old_job, old_operation = self.reading()
        self.core.dispatch(DictationToggle())
        start, = self.effects(AudioReset(old_job), StartRecording)
        self.core.dispatch(RecordingStarted(start.job))
        self.core.dispatch(EngineFault(old_operation, HuginError('worker_failed')))
        self.assertEqual(self.core.snapshot().job, start.job)
        self.assertEqual(self.core.snapshot().state, State.RECORDING)
        self.assertIsNone(self.core.snapshot().error)
        self.assertEqual(self.stop(start.job), [])
        next_begin, = self.effects(EngineTerminal(old_operation), BeginEngine)
        self.assertEqual(next_begin.operation.engine, Engine.STT)

    def test_toggle_before_start_ack_is_ordered_as_stop(self):
        start, = self.effects(DictationToggle(), StartRecording)
        stop, = self.effects(DictationToggle(), StopRecording)
        self.assertEqual(start.job, stop.job)
        self.core.dispatch(RecordingStarted(start.job))
        self.assertEqual(self.core.snapshot().state, State.TRANSCRIBING)
        begin, = self.effects(RecordingStopped(start.job, b'\x00\x00'), BeginEngine)
        self.assertEqual(begin.operation.engine, Engine.STT)

    def test_engine_payload_and_failure_bounds_do_not_release_ownership(self):
        for pcm, code in ((b'x', 'protocol_invalid'), (b'\x00\x00' * 32769, 'resource_limit')):
            with self.subTest(code=code):
                self.setUp()
                _, operation = self.reading()
                self.assertEqual(self.effects(EngineAudio(operation, pcm), PlayAudio), [])
                self.assertEqual(self.core.snapshot().error.code, code)
                self.assertEqual(self.core.snapshot().gpu_slot, operation)

    def test_large_atomic_transcript_can_exceed_control_envelope(self):
        text = 'é' * (128 * 1024)
        job, operation, stage = self.transcription(text)
        self.assertEqual(stage.text, text)
        self.assertEqual(self.core.snapshot().result.text, text)
        self.finish_delivery(job, operation)

    def test_tts_chunks_keep_one_job_unique_requests_and_per_section_drain_barrier(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        text = ('Sentence with synthetic words. ' * 40) + ('x' * 450)
        init, = self.effects(SelectionReady(capture.job, text), BeginEngine)
        self.core.dispatch(EngineReady(init.operation))
        begin, = self.effects(EngineTerminal(init.operation), BeginEngine)
        chunks, request_ids = [], set()
        audio_sequence = 0
        while True:
            chunks.append(begin.payload)
            self.assertLessEqual(len(begin.payload), 240)
            self.assertTrue(begin.payload.strip())
            self.assertEqual(begin.operation.job, capture.job)
            self.assertEqual(begin.operation.engine_instance, init.operation.engine_instance)
            self.assertNotIn(begin.operation.request_id, request_ids)
            request_ids.add(begin.operation.request_id)
            play = prepared(self.core, begin.operation)
            audio_sequence += 1
            self.assertEqual(play.sequence, audio_sequence)
            self.assertIsNone(self.core.snapshot().gpu_slot)
            self.assertEqual(self.effects(AudioFinished(capture.job, audio_sequence-1), BeginEngine), [])
            effects = self.core.dispatch(AudioFinished(capture.job, audio_sequence))
            next_operations = [item for item in effects if isinstance(item, BeginEngine)]
            if not next_operations: break
            begin, = next_operations
            self.assertEqual(begin.operation.action, Action.SYNTHESIZE)
        self.assertEqual(''.join(chunks), text)
        self.assertGreater(len(chunks), 3)
        self.assertEqual(self.core.snapshot().state, State.IDLE)

    def test_cancel_chunked_tts_discards_all_unstarted_chunks(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        init, = self.effects(SelectionReady(capture.job, 'Long sentence. ' * 100), BeginEngine)
        operation = self.initialized(init.operation)
        self.core.dispatch(Cancel())
        self.core.dispatch(AudioReset(capture.job))
        self.assertEqual(self.effects(EngineTerminal(operation), BeginEngine), [])

    def test_duplicate_selection_cannot_start_second_stream_during_final_drain(self):
        job, operation = self.reading()
        self.core.dispatch(EngineTerminal(operation))
        self.assertEqual(self.effects(SelectionReady(job, 'Duplicate'), BeginEngine), [])

    def test_whitespace_spans_never_create_empty_tts_request(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        init, = self.effects(SelectionReady(capture.job, ' ' * 900 + 'Spoken.' + '\n' * 900), BeginEngine)
        self.core.dispatch(EngineReady(init.operation))
        begin, = self.effects(EngineTerminal(init.operation), BeginEngine)
        spoken = []
        while True:
            self.assertTrue(begin.payload.strip())
            self.assertLessEqual(len(begin.payload), 400)
            spoken.append(begin.payload.strip())
            following = self.effects(EngineTerminal(begin.operation), BeginEngine)
            if not following:
                break
            begin, = following
        self.assertEqual(''.join(spoken), 'Spoken.')

    def test_tts_selection_byte_limit_precedes_scheduling(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        self.assertEqual(self.effects(SelectionReady(capture.job, 'é' * 131073), BeginEngine), [])
        self.assertEqual(self.core.snapshot().error.code, 'resource_limit')

    def test_cancelled_init_without_ready_does_not_claim_model_is_ready(self):
        capture, = self.effects(ReadToggle(), CaptureSelection)
        init, = self.effects(SelectionReady(capture.job, 'First'), BeginEngine)
        self.core.dispatch(Cancel())
        self.core.dispatch(AudioReset(capture.job))
        self.core.dispatch(EngineTerminal(init.operation))
        next_capture, = self.effects(ReadToggle(), CaptureSelection)
        self.assertEqual(self.effects(SelectionReady(next_capture.job, 'Second'), BeginEngine), [])
        self.assertEqual(self.core.snapshot().error.code, 'worker_failed')

    def test_time_must_be_finite_and_monotonic(self):
        for value in (float('nan'), float('inf'), 9):
            with self.subTest(value=value), self.assertRaises(HuginError):
                self.core.dispatch(Tick(value))

    def idle_stt(self):
        job, operation, _ = self.transcription()
        self.finish_delivery(job, operation)
        return operation

    def idle_offload(self):
        self.idle_stt()
        begin, = self.effects(Tick(100), BeginEngine)
        self.assertEqual(begin.operation.action, Action.OFFLOAD)
        return begin.operation

    def test_idle_offload_is_explicit_once_and_has_no_user_generation(self):
        previous = self.idle_stt()
        generation = self.core.snapshot().generation
        self.assertEqual(self.effects(Tick(99.999), BeginEngine), [])
        begin, = self.effects(Tick(100), BeginEngine)
        self.assertEqual(begin.operation.action, Action.OFFLOAD)
        self.assertEqual(begin.operation.engine, Engine.STT)
        self.assertIsNone(begin.operation.job)
        self.assertIsNone(begin.payload)
        self.assertIsNone(begin.voice)
        self.assertEqual(begin.operation.engine_instance, previous.engine_instance)
        self.assertNotEqual(begin.operation.request_id, previous.request_id)
        self.assertEqual(self.core.snapshot().generation, generation)
        self.assertEqual(self.core.snapshot().state, State.IDLE)
        self.assertFalse(self.core.snapshot().escape_reserved)
        self.assertEqual(self.core.snapshot().retired_operations, ())
        self.assertEqual(self.core.snapshot().gpu_slot, begin.operation)
        self.assertEqual(self.effects(Tick(200), BeginEngine), [])
        self.core.dispatch(EngineTerminal(begin.operation))
        self.assertEqual(self.effects(Tick(1000), BeginEngine), [])
        stt = next(item for item in self.core.snapshot().components if item.engine == Engine.STT)
        self.assertTrue(stt.ready)

    def test_idle_offload_uses_configured_interval_and_validates_it(self):
        self.core = Coordinator(instance_id='configured', stt_idle_unload_seconds=5, now=10)
        self.idle_stt()
        self.assertEqual(self.effects(Tick(14.999), BeginEngine), [])
        begin, = self.effects(Tick(15), BeginEngine)
        self.assertEqual(begin.operation.action, Action.OFFLOAD)
        for value in (0, -1, True, 1.5, 3601):
            with self.subTest(value=value), self.assertRaises(HuginError):
                Coordinator(instance_id='invalid', stt_idle_unload_seconds=value)

    def test_idle_offload_never_overlaps_retired_stt_slot(self):
        job, operation, _ = self.transcription()
        self.core.dispatch(DeliveryCommit(job, 'own-transaction', True))
        self.core.dispatch(DeliveryFinished(job))
        self.assertEqual(self.core.snapshot().retired_operations, (operation,))
        self.assertEqual(self.effects(Tick(1000), BeginEngine), [])
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.core.dispatch(EngineTerminal(operation))
        self.assertEqual(self.effects(Tick(1089.999), BeginEngine), [])
        begin, = self.effects(Tick(1090), BeginEngine)
        self.assertEqual(begin.operation.action, Action.OFFLOAD)

    def test_idle_offload_waits_for_reading_drain_and_rearms_after_alignment(self):
        self.idle_stt()
        job, operation = self.reading()
        self.assertEqual(self.effects(Tick(100), BeginEngine), [])
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        play = prepared(self.core, operation)
        self.assertEqual(self.effects(Tick(190), BeginEngine), [])
        self.core.dispatch(AudioFinished(job, play.sequence))
        begin, = self.effects(Tick(191), BeginEngine)
        self.assertEqual(begin.operation.action, Action.OFFLOAD)

    def test_recording_starts_during_offload_but_transcribe_waits_for_terminal(self):
        offload = self.idle_offload()
        effects = self.core.dispatch(DictationToggle())
        start, = [item for item in effects if isinstance(item, StartRecording)]
        self.assertFalse(any(isinstance(item, CancelEngine) for item in effects))
        self.core.dispatch(RecordingStarted(start.job))
        self.assertEqual(self.stop(start.job), [])
        self.assertEqual(self.core.snapshot().gpu_slot, offload)
        begin, = self.effects(EngineTerminal(offload), BeginEngine)
        self.assertEqual(begin.operation.action, Action.TRANSCRIBE)
        self.assertEqual(begin.operation.job, start.job)
        self.assertEqual(begin.operation.engine_instance, offload.engine_instance)
        self.assertEqual(self.core.dispatch(EngineTerminal(offload)), ())
        self.assertEqual(self.core.snapshot().gpu_slot, begin.operation)

    def test_completed_transcription_rearms_idle_offload_from_its_own_terminal(self):
        offload = self.idle_offload()
        self.core.dispatch(EngineTerminal(offload))
        job, operation, _ = self.transcription('After reload')
        self.core.dispatch(Tick(200))
        self.finish_delivery(job, operation)
        self.assertEqual(self.effects(Tick(289.999), BeginEngine), [])
        begin, = self.effects(Tick(290), BeginEngine)
        self.assertEqual(begin.operation.action, Action.OFFLOAD)
        self.assertEqual(begin.operation.engine_instance, offload.engine_instance)
        self.assertNotEqual(begin.operation.request_id, offload.request_id)

    def test_offload_fault_retains_slot_until_matching_exit_and_waiter_reinitializes(self):
        offload = self.idle_offload()
        job = self.record()
        self.assertEqual(self.stop(job), [])
        self.core.dispatch(EngineFault(offload, HuginError('worker_failed', 'private payload')))
        self.assertEqual(self.core.snapshot().gpu_slot, offload)
        self.assertEqual(self.core.snapshot().job, job)
        self.assertEqual(self.core.snapshot().error.phase, 'offload')
        self.assertEqual(self.effects(Tick(1000), BeginEngine), [])
        self.core.dispatch(EngineExited(Engine.STT, 'foreign-worker'))
        self.assertEqual(self.core.snapshot().gpu_slot, offload)
        begin, = self.effects(EngineExited(Engine.STT, offload.engine_instance), BeginEngine)
        self.assertEqual(begin.operation.action, Action.INITIALIZE)
        self.assertNotEqual(begin.operation.engine_instance, offload.engine_instance)
        self.assertEqual(begin.operation.job, job)

    def test_offload_failed_terminal_blocks_automatic_retry(self):
        offload = self.idle_offload()
        self.core.dispatch(EngineTerminal(offload, False))
        self.assertIsNone(self.core.snapshot().gpu_slot)
        self.assertEqual(self.core.snapshot().error.code, 'worker_failed')
        self.assertEqual(self.core.snapshot().error.phase, 'offload')
        self.assertEqual(self.core.snapshot().state, State.ERROR)
        stt = next(item for item in self.core.snapshot().components if item.engine == Engine.STT)
        self.assertFalse(stt.ready)
        self.assertTrue(stt.blocked)
        self.assertEqual(self.effects(Tick(1000), BeginEngine), [])

    def test_offload_cannot_publish_payload_or_be_completed_by_unmatched_terminal(self):
        offload = self.idle_offload()
        self.assertEqual(self.core.dispatch(EngineAudio(offload, b'\x00\x00')), ())
        self.assertEqual(self.core.dispatch(EngineResult(offload, 'Not a transcript')), ())
        self.assertEqual(self.core.dispatch(EngineTerminal(replace(offload, request_id='foreign'))), ())
        self.assertEqual(self.core.snapshot().gpu_slot, offload)
        self.assertEqual(self.core.snapshot().result.text, 'Synthetic dictation')
        self.assertEqual(self.core.snapshot().state, State.IDLE)

    def test_cancel_waiting_dictation_does_not_cancel_maintenance_or_publish_late_work(self):
        offload = self.idle_offload()
        job = self.record()
        self.assertEqual(self.stop(job), [])
        self.assertEqual(self.effects(Cancel(), CancelEngine), [])
        self.assertIsNone(self.core.snapshot().job)
        self.assertEqual(self.core.snapshot().gpu_slot, offload)
        self.assertEqual(self.effects(EngineTerminal(offload), BeginEngine), [])
        self.assertEqual(self.core.snapshot().state, State.IDLE)

    def test_verified_offload_exit_without_user_job_does_not_invent_failure(self):
        offload = self.idle_offload()
        self.core.dispatch(EngineExited(Engine.STT, offload.engine_instance))
        self.assertIsNone(self.core.snapshot().gpu_slot)
        self.assertIsNone(self.core.snapshot().error)
        self.assertEqual(self.core.snapshot().state, State.IDLE)
        self.assertEqual(self.effects(Tick(1000), BeginEngine), [])

    def test_shutdown_keeps_offload_owned_until_confirmed_exit(self):
        offload = self.idle_offload()
        self.core.dispatch(Shutdown())
        self.assertEqual(self.core.snapshot().gpu_slot, offload)
        self.assertEqual(self.effects(Tick(1000), BeginEngine), [])
        self.core.dispatch(EngineExited(Engine.STT, offload.engine_instance))
        self.assertIsNone(self.core.snapshot().gpu_slot)
        self.assertEqual(self.core.snapshot().state, State.STOPPING)

    def test_explicit_cleanup_retry_reissues_only_held_audio_reset_during_shutdown(self):
        job, operation = self.reading()
        self.core.dispatch(Cancel())
        self.core.dispatch(AudioReset(job, False))
        self.core.dispatch(Shutdown())
        generation = self.core.snapshot().generation
        self.assertEqual(self.core.dispatch(RetryCleanup()), (ResetAudio(job),))
        self.assertEqual(self.core.snapshot().generation, generation)
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.assertEqual(self.core.snapshot().state, State.STOPPING)
        self.assertEqual(self.effects(AudioReset(job), StartRecording), [])
        self.assertIsNone(self.core.snapshot().cancelling_job)
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.core.dispatch(EngineTerminal(operation))
        self.assertEqual(self.core.dispatch(RetryCleanup()), ())

    def test_explicit_cleanup_retry_reissues_discard_capture_stop_until_ack(self):
        job = self.record()
        self.core.dispatch(Shutdown())
        generation = self.core.snapshot().generation
        self.assertEqual(self.core.dispatch(RetryCleanup()), (StopRecording(job, discard=True),))
        self.assertEqual(self.core.snapshot().generation, generation)
        self.assertEqual(self.core.snapshot().cancelling_job, job)
        self.core.dispatch(RecordingStopped(job))
        self.assertIsNone(self.core.snapshot().cancelling_job)
        self.assertEqual(self.core.dispatch(RetryCleanup()), ())
        self.assertEqual(self.core.snapshot().state, State.STOPPING)

    def test_cleanup_retry_never_repeats_delivery_and_preserves_finished_result(self):
        job, operation, _ = self.transcription('Preserved result')
        self.core.dispatch(DeliveryCommit(job, 'own-transaction', True))
        self.core.dispatch(Cancel())
        result = self.core.snapshot().result
        generation = self.core.snapshot().generation
        self.assertEqual(self.core.dispatch(RetryCleanup()), ())
        self.assertEqual(self.core.snapshot().generation, generation)
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.assertEqual(self.core.snapshot().cancelling_job, job)
        self.assertEqual(self.core.snapshot().result, result)
        self.core.dispatch(Shutdown())
        self.assertEqual(self.core.dispatch(RetryCleanup()), ())
        # Shutdown intentionally cleared the result; retry cannot recreate it.
        self.assertIsNone(self.core.snapshot().result)
        self.assertEqual(self.effects(DeliveryCommit(job, 'own-transaction', True), DeliverText), [])

    def test_cleanup_retry_does_not_release_cancelled_engine_without_terminal(self):
        job = self.record()
        begin, = self.stop(job)
        operation = self.initialized(begin.operation)
        self.core.dispatch(Cancel())
        generation = self.core.snapshot().generation
        self.assertEqual(self.core.dispatch(RetryCleanup()), ())
        self.assertEqual(self.core.snapshot().generation, generation)
        self.assertEqual(self.core.snapshot().gpu_slot, operation)
        self.assertEqual(self.core.snapshot().cancelling_job, job)

    def test_cleanup_retry_clears_pending_dictation_before_quit_cleanup_ack(self):
        old_job, operation = self.reading()
        self.core.dispatch(DictationToggle())
        self.assertEqual(self.core.dispatch(RetryCleanup()), (ResetAudio(old_job),))
        self.assertEqual(self.effects(AudioReset(old_job), StartRecording), [])
        self.assertIsNone(self.core.snapshot().job)
        self.assertEqual(self.core.snapshot().gpu_slot, operation)

    def test_cleanup_retry_while_idle_has_no_effect_or_new_generation(self):
        generation = self.core.snapshot().generation
        self.assertEqual(self.core.dispatch(RetryCleanup()), ())
        self.assertEqual(self.core.snapshot().generation, generation)
        self.assertEqual(self.core.snapshot().state, State.IDLE)


if __name__ == '__main__':
    unittest.main()
