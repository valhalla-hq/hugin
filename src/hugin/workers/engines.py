"""Native implementations preserving the verified old-stack model parameters."""
import ctypes
import os

from hugin.config import verify_voice_assets
from hugin.errors import HuginError
from .assets import verify_files


class WhisperEngine:
    def __init__(self, settings, device=None):
        self.settings = settings
        self.device = device or settings.stt['device']
        verify_files(settings.paths['stt_model'], settings.root / 'locks/stt-model.json')
        self._dll_handles = []
        self._cuda_libraries = []
        self._cudart = None
        if self.device == 'cuda':
            directory = settings.root / '.runtime/cuda'
            verify_files(directory, settings.root / 'locks/cuda.json')
            if os.name == 'nt':
                self._dll_handles.append(os.add_dll_directory(str(directory)))
                self._cudart = ctypes.WinDLL(str(directory / 'cudart64_12.dll'))
                self._cudart.cudaDeviceSynchronize.restype = ctypes.c_int
                # CT2 4.8.2 resolves cuBLAS by legacy LoadLibraryA basename.
                # AddDllDirectory alone doesn't cover that search. Preload
                # verified absolute paths and retain them with this engine.
                self._cuda_libraries = [ctypes.WinDLL(str(directory / name))
                    for name in ('cublasLt64_12.dll','cublas64_12.dll')]
        import numpy as np
        from faster_whisper import WhisperModel
        self.np = np
        self._factory = WhisperModel
        self.model = None
        self._load()

    def _load(self):
        try:
            if self.model is None:
                self.model = self._factory(str(self.settings.paths['stt_model']),
                    device=self.device,
                    compute_type=self.settings.stt['compute_type'] if self.device == 'cuda' else 'int8',
                    cpu_threads=self.settings.stt['cpu_threads'], num_workers=1,
                    local_files_only=True)
            elif not self.model.model.model_is_loaded:
                self.model.model.load_model()
        except RuntimeError:
            if self.device != 'cuda':
                raise
            # Preserve the old stack's explicit local CPU fallback on load failure.
            self.model = None
            self.device = 'cpu'
            self._load()

    def transcribe(self, pcm, cancelled):
        self._load()
        if cancelled():
            return ''
        audio = self.np.frombuffer(pcm, dtype='<i2').astype(self.np.float32)
        audio /= 32768.0
        segments, _info = self.model.transcribe(audio, language=None,
            task='transcribe', beam_size=5, temperature=0.0, initial_prompt=None,
            condition_on_previous_text=False, vad_filter=True,
            vad_parameters={'min_silence_duration_ms': 500})
        parts = []
        size = 0
        try:
            for segment in segments:
                if cancelled():
                    break
                text = segment.text.strip()
                size += len(text.encode('utf-8')) + (1 if parts else 0)
                if size > self.settings.limits['transcript_bytes']:
                    raise HuginError('resource_limit', 'transcribe')
                parts.append(text)
        finally:
            segments.close()
            del audio
        return ' '.join(parts).strip()

    def synchronize(self):
        if self._cudart is not None:
            # A CUDA load attempt may have fallen back to CPU. Still observe
            # completion of any earlier native device work before terminal.
            if self._cudart.cudaDeviceSynchronize() != 0:
                raise HuginError('worker_failed', 'gpu_synchronize')
        elif self.device == 'cuda':
            raise HuginError('worker_failed', 'gpu_synchronize')

    def offload(self):
        self.synchronize()
        self.model.model.unload_model(to_cpu=True)


class QwenEngine:
    def __init__(self, settings, device=None):
        if device not in (None, 'cuda'):
            raise HuginError('unsupported', 'tts_initialize')
        self.device = 'cuda'
        self.settings = settings
        verify_files(settings.paths['tts_model'], settings.root / 'locks/tts-model.json')
        verify_voice_assets(settings)
        import numpy as np
        import torch
        from faster_qwen3_tts import FasterQwen3TTS
        self.np, self.torch = np, torch
        torch.set_num_threads(4)
        self.references = {key: voice.reference_text.read_text(encoding='utf-8')
                           for key, voice in settings.voices.items()}
        self.model = FasterQwen3TTS.from_pretrained(str(settings.paths['tts_model']),
            max_seq_len=1024, dtype=torch.bfloat16, attn_implementation='sdpa',
            local_files_only=True)
        self.model.warmup(prefill_len=128)
        with torch.inference_mode():
            for voice in settings.voices:
                stream = self._generate('Bereit.', voice, 'German')
                try:
                    for _ in stream:
                        pass
                finally:
                    stream.close()
        self.synchronize()

    def _generate(self, text, voice, language):
        self.torch.manual_seed(42)
        self.torch.cuda.manual_seed_all(42)
        return self.model.generate_voice_clone_streaming(text=text, language=language,
            ref_audio=str(self.settings.voices[voice].reference), ref_text=self.references[voice],
            xvec_only=False, chunk_size=8, max_new_tokens=640)

    def synthesize(self, text, voice, language, cancelled):
        with self.torch.inference_mode():
            stream = self._generate(text, voice, language)
            try:
                for audio, sample_rate, _timing in stream:
                    if cancelled():
                        break
                    if int(sample_rate) != 24000:
                        raise HuginError('protocol_invalid', 'tts_audio')
                    values = self.np.asarray(audio).reshape(-1)
                    # Bound representation expansion before conversion to PCM.
                    if values.size > 24000 * 30 or not self.np.isfinite(values).all():
                        raise HuginError('resource_limit', 'tts_audio')
                    if values.size:
                        yield (self.np.clip(values, -1, 1) * 32767).astype('<i2').tobytes()
            finally:
                stream.close()

    def synchronize(self):
        self.torch.cuda.synchronize()

    def offload(self):
        raise HuginError('unsupported', 'tts_offload')
