"""Real own CPU-Whisper through the controller, with RAM-only synthetic I/O.

No physical recording, input injection, clipboard mutation or GPU model load.
This complements device probes; it does not establish the native target matrix.
"""
from pathlib import Path
import argparse
import json
import re
import sys
import threading
import time
from types import SimpleNamespace as NS
import wave
import warnings

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from hugin.application import Controller
from hugin.config import load_settings,verify_voice_assets
from hugin.workers import EnginePool


class Inputs:
    running=True
    closed=False
    error=None
    def set_cancel_active(self,active): pass
    def stop(self): self.running=False; self.closed=True


class Capture:
    owned=False
    fault=None
    def __init__(self,pcm): self.pcm=pcm
    def start(self): self.owned=True
    def stop(self): self.owned=False;return self.pcm
    def cancel(self): self.owned=False;self.pcm=b''


class Clipboard:
    def __init__(self): self.count=0;self.text=None;self.delivered=threading.Event()
    def capture_target(self): return NS(target='synthetic-memory-target')
    def deliver(self,text,target,still_current,*,authorize):
        accepted=still_current() and authorize('synthetic-memory-transaction')
        if accepted:
            self.count+=1;self.text=text;self.delivered.set()
        return NS(submitted=accepted,restored=True)
    def close(self): self.text=None


class Output:
    def stop(self): pass
    def close(self): pass


class CPUOnlyPool(EnginePool):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.instances=[]
    def start(self,engine,*,device=None):
        if engine!='stt': raise RuntimeError('cpu_probe_only')
        future=super().start(engine,device='cpu')
        self.instances.append(self.workers[engine]);return future


def normalize(text): return ' '.join(re.findall(r'\w+',text.casefold()))


def probe(root,repeats=1):
    if type(repeats) is not int or not 1<=repeats<=5: raise ValueError('repeat_limit')
    settings=load_settings(root);verify_voice_assets(settings)
    voice=settings.voices['tyr']
    with wave.open(str(voice.reference),'rb') as source:
        if source.getnchannels()!=1 or source.getsampwidth()!=2: raise ValueError('reference_format')
        pcm=source.readframes(source.getnframes());rate=source.getframerate()
    if rate!=16000:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',DeprecationWarning)
            import audioop
        pcm,_=audioop.ratecv(pcm,2,1,rate,16000,None)
    expected=normalize(voice.reference_text.read_text(encoding='utf-8'))
    finished=threading.Event()
    clipboard=Clipboard();controller=None
    def publish(view):
        pass
    def event(value): controller.worker_event(value)
    pool=CPUOnlyPool(root,event)
    controller=Controller(settings,inputs=Inputs(),microphone=Capture(pcm),output=Output(),
        clipboard=clipboard,pool=pool,publish=publish)
    thread=threading.Thread(target=controller.run,args=(finished.set,),name='hugin-cpu-probe')
    cpu_started=time.process_time()
    thread.start();started=time.perf_counter();runs=[]
    try:
        for index in range(repeats):
            run_started=time.perf_counter();clipboard.delivered.clear()
            controller.command('dictation')
            # Real capture executor, approved synthetic PCM source, no device.
            deadline=time.monotonic()+5
            while not controller.microphone.owned and time.monotonic()<deadline: time.sleep(.01)
            if not controller.microphone.owned: raise TimeoutError('capture_start')
            controller.command('dictation')
            if not clipboard.delivered.wait(60): raise TimeoutError('transcript')
            actual=normalize(clipboard.text or '')
            if actual!=expected or clipboard.count!=index+1: raise ValueError('transcript_mismatch')
            runs.append({'engine_state':'new_worker' if index==0 else 'resident_model',
                'elapsed_seconds':round(time.perf_counter()-run_started,3),
                'reference_words':len(expected.split()),'transcript_words':len(actual.split()),
                'normalized_exact_match':actual==expected})
        result={'schema_version':1,'scenario':'controller-own-cpu-whisper',
            'elapsed_seconds':round(time.perf_counter()-started,3),
            'runs':runs,'deliveries':clipboard.count,
            'device':controller._devices.get('stt'),'content_persisted':False,
            'physical_inputs':False,'native_clipboard':False,'gpu_loaded':False}
    finally:
        controller.command('quit')
        thread.join(12)
        if thread.is_alive(): raise TimeoutError('controller_cleanup')
    result['owned_workers_remaining']=len(pool.workers)
    result['microphone_owned']=controller.microphone.owned
    result['controller_cpu_seconds']=round(time.process_time()-cpu_started,3)
    metrics=pool.instances[0].process.metrics() if len(pool.instances)==1 else None
    result['worker_family_cpu_seconds']=None if metrics is None else round(metrics['cpu_seconds'],3)
    result['worker_family_peak_commit_bytes']=None if metrics is None else metrics['peak_job_commit_bytes']
    result['unmeasured']=['physical working-set RAM peak','agent tokens','GPU tasks','baseline comparison','p50/p95']
    result['cold_scope']='new worker/model; OS file cache uncontrolled'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--repeat',type=int,default=1)
    args=parser.parse_args()
    try: print(json.dumps(probe(args.root.resolve(),args.repeat),indent=2));return 0
    except Exception:
        print(json.dumps({'scenario':'controller-own-cpu-whisper','error':'probe_failed'}));return 1


if __name__=='__main__': raise SystemExit(main())
