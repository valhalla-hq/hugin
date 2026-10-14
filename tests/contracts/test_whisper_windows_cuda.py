"""Legacy CUDA basename lookup must see Hugin's verified, held libraries."""
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
from unittest.mock import patch

from hugin.workers.engines import WhisperEngine


class Array:
    def astype(self,_):return self
    def __itruediv__(self,_):return self


class WhisperWindowsCuda(unittest.TestCase):
    def engine(self,device):
        loaded={};verified=[];directory_handles=[]
        root=Path('/hugin-fixture').absolute()
        settings=NS(root=root,paths={'stt_model':root/'model'},
            stt={'device':device,'compute_type':'int8_float16','cpu_threads':6},
            limits={'transcript_bytes':262144})
        # ctypes function objects permit the restype assignment.
        def sync():return 0
        def load(name):
            path=Path(name)
            self.assertIn(root/'.runtime/cuda',verified)
            self.assertEqual(path.parent,root/'.runtime/cuda')
            library=NS(cudaDeviceSynchronize=sync)
            loaded[path.name]=library
            return library
        def add_directory(path):
            token=object();directory_handles.append(token);return token
        class Model:
            def __init__(self,*args,**kwargs):
                self.device=kwargs['device'];self.model=NS(model_is_loaded=True)
            def transcribe(self,*args,**kwargs):
                # Like CT2 LoadLibraryA, this lookup doesn't use Python's
                # AddDllDirectory flags. Only an explicitly loaded DLL works.
                if self.device=='cuda' and not {'cublasLt64_12.dll','cublas64_12.dll'}<=loaded.keys():
                    raise RuntimeError('legacy cuBLAS lookup failed')
                def segments():yield NS(text='Synthetischer Test')
                return segments(),None
        modules={'numpy':NS(frombuffer=lambda *args,**kwargs:Array(),float32=object()),
                 'faster_whisper':NS(WhisperModel=Model)}
        with patch('hugin.workers.engines.os',NS(name='nt',add_dll_directory=add_directory)), \
             patch('hugin.workers.engines.verify_files',lambda path,lock:verified.append(path)), \
             patch('hugin.workers.engines.ctypes.WinDLL',load,create=True), \
             patch.dict(sys.modules,modules):
            engine=WhisperEngine(settings,device)
            self.assertEqual(engine.transcribe(b'\0\0',lambda:False),'Synthetischer Test')
            engine.synchronize()
        return engine,loaded,directory_handles

    def test_gpu_transcription_resolves_held_verified_legacy_libraries(self):
        engine,loaded,directories=self.engine('cuda')
        self.assertEqual(engine.device,'cuda')
        self.assertTrue(directories)
        # Keep the library objects alive for the native model's lifetime.
        retained=list(vars(engine).values())
        self.assertTrue(any(isinstance(value,list) and loaded['cublas64_12.dll'] in value for value in retained))

    def test_cpu_does_not_load_cuda_libraries(self):
        engine,loaded,directories=self.engine('cpu')
        self.assertEqual(engine.device,'cpu')
        self.assertEqual(loaded,{})
        self.assertEqual(directories,[])


if __name__=='__main__':unittest.main()
