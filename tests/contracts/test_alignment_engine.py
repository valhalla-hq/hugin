"""Exercise the real adapter with simulated inference/DSP boundaries only."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from hugin.word_timing import WordTiming
from hugin.workers.engines import WhisperEngine


class Array:
    def __init__(self, samples): self.samples = samples
    def __len__(self): return self.samples
    def reshape(self, *shape): return self
    def to_ndarray(self): return self


class Features:
    def __init__(self, frames): self.shape=(128,frames)
    def __getitem__(self, indices): return Features(min(self.shape[1],indices[1].stop))


class AlignmentEngineTests(unittest.TestCase):
    def fixture(self, *, tokens=1, decoded='word', records=None):
        self.events = []
        class Tokenizer:
            sot_sequence = [100,101,102]
            def __init__(inner, hf, multilingual, task, language):
                self.events.append(('tokenizer',task,language))
            def encode(inner, text): return list(range(tokens))
            def decode(inner, encoded): return decoded
        def from_array(array, **kwargs):
            self.events.append(('frame',len(array),kwargs))
            return SimpleNamespace(sample_rate=None, samples=len(array))
        class Resampler:
            def __init__(inner, **kwargs): self.events.append(('resampler',kwargs))
            def resample(inner, frame):
                if frame is None: return []
                self.events.append(('resample',frame.sample_rate))
                return [Array(frame.samples * 2 // 3)]
        def features(array):
            self.events.append(('features',len(array)))
            return Features(len(array)//160+1)
        model = SimpleNamespace(hf_tokenizer=object(), model=SimpleNamespace(is_multilingual=True),
            feature_extractor=features, encode=Mock(return_value=object()),
            find_alignment=Mock(return_value=records if records is not None else [[
                dict(word='word',tokens=list(range(tokens)),start=0,end=.5)]]))
        engine = WhisperEngine.__new__(WhisperEngine)
        engine._load = Mock()
        engine.model = model
        engine.np = SimpleNamespace(frombuffer=lambda pcm,**kwargs:Array(len(pcm)//2),
            concatenate=lambda arrays:Array(sum(len(a) for a in arrays)))
        self.modules = {'faster_whisper':SimpleNamespace(),
            'faster_whisper.tokenizer':SimpleNamespace(Tokenizer=Tokenizer),
            'av':SimpleNamespace(AudioFrame=SimpleNamespace(from_ndarray=from_array),
                AudioResampler=Resampler)}
        return engine

    def align(self, engine, pcm=b'\0\0'*24000, text='word', cancelled=lambda:False):
        with patch.dict(sys.modules,self.modules):
            return engine.align(pcm,text,'German',cancelled)

    def test_actual_adapter_passes_known_text_as_batch_and_unpadded_frames(self):
        engine = self.fixture()
        result = self.align(engine)
        self.assertEqual(result.words,(WordTiming(0,4,0,12000),))
        args = engine.model.find_alignment.call_args.args
        self.assertEqual(args[1],[[0]])
        self.assertEqual(args[3],100)
        self.assertEqual(engine.model.encode.call_args.args[0].shape,(128,101),
            'short sections must not pay for a padded 30-second encoder window')
        self.assertIn(('features',16000),self.events)
        self.assertIn(('resample',24000),self.events)
        self.assertIn(('resampler',dict(format='fltp',layout='mono',rate=16000)),self.events)

    def test_duration_rejection_does_not_load_model_or_truncate(self):
        engine = self.fixture()
        self.assertEqual(self.align(engine,b'\0\0'*720001).status,'unavailable_duration')
        engine._load.assert_not_called()
        self.assertEqual(self.events,[])

    def test_decoder_budget_includes_sot_language_task_no_timestamps_and_eot(self):
        for tokens,status in [(443,'aligned'),(444,'unavailable_tokens')]:
            with self.subTest(tokens=tokens):
                engine = self.fixture(tokens=tokens)
                self.assertEqual(self.align(engine).status,status)
                self.assertEqual(engine.model.encode.called,status=='aligned')

    def test_source_roundtrip_mismatch_never_aligns_other_characters(self):
        engine = self.fixture(decoded='rewritten')
        self.assertEqual(self.align(engine).status,'unavailable_text')
        engine.model.encode.assert_not_called()

    def test_unspoken_outer_whitespace_does_not_consume_alignment_but_offsets_stay_original(self):
        engine=self.fixture()
        result=self.align(engine,text=' \n word\t ')
        self.assertEqual(result.words,(WordTiming(3,7,0,12000),))

    def test_cancel_before_load_and_after_encoder_never_enters_next_model_step(self):
        engine = self.fixture()
        self.assertEqual(self.align(engine,cancelled=lambda:True).status,'unavailable_cancelled')
        engine._load.assert_not_called()
        cancelled = [False]
        def encoded(features): cancelled[0]=True;return object()
        engine.model.encode.side_effect=encoded
        self.assertEqual(self.align(engine,cancelled=lambda:cancelled[0]).status,'unavailable_cancelled')
        engine.model.find_alignment.assert_not_called()

    def test_tiny_audio_and_bad_paths_are_rejected_without_estimates(self):
        engine = self.fixture()
        self.assertEqual(self.align(engine,b'\0\0'*240).status,'rejected_path')
        engine.model.encode.assert_not_called()
        for records in [[],[[]],[[dict(word='word',tokens=[0],start=0,end=0)]]]:
            engine = self.fixture(records=records)
            self.assertEqual(self.align(engine).status,'rejected_path')

    def test_model_failure_uses_existing_hard_failure_path(self):
        engine = self.fixture()
        engine.model.find_alignment.side_effect=RuntimeError('synthetic model fault')
        with self.assertRaises(RuntimeError): self.align(engine)


if __name__ == '__main__': unittest.main()
