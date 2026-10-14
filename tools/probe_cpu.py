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
    def __init__(self): self.count=0;self.text=None
    def capture_target(self): return NS(target='synthetic-memory-target')
    def deliver(self,text,target,still_current,*,authorize):
        accepted=still_current() and authorize('synthetic-memory-transaction')
        if accepted: self.count+=1;self.text=text
        return NS(submitted=accepted,restored=True)
    def close(self): self.text=None


class Output:
    def stop(self): pass
    def close(self): pass


class CPUOnlyPool(EnginePool):
    def start(self,engine,*,device=None):
        if engine!='stt': raise RuntimeError('cpu_probe_only')
        return super().start(engine,device='cpu')


def normalize(text): return ' '.join(re.findall(r'\w+',text.casefold()))


def probe(root):
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
    finished=threading.Event();delivered=threading.Event()
    clipboard=Clipboard();controller=None
    def publish(view):
        if view.text: delivered.set()
    def event(value): controller.worker_event(value)
    pool=CPUOnlyPool(root,event)
    controller=Controller(settings,inputs=Inputs(),microphone=Capture(pcm),output=Output(),
        clipboard=clipboard,pool=pool,publish=publish)
    thread=threading.Thread(target=controller.run,args=(finished.set,),name='hugin-cpu-probe')
    thread.start();started=time.perf_counter()
    try:
        controller.command('dictation')
        # The capture executor is real, while its PCM source is the approved WAV.
        deadline=time.monotonic()+5
        while not controller.microphone.owned and time.monotonic()<deadline: time.sleep(.01)
        if not controller.microphone.owned: raise TimeoutError('capture_start')
        controller.command('dictation')
        if not delivered.wait(60): raise TimeoutError('transcript')
        # Publish occurs after StageDelivery returns on the serial owner.
        deadline=time.monotonic()+5
        while clipboard.count!=1 and time.monotonic()<deadline: time.sleep(.01)
        actual=normalize(clipboard.text or '')
        result={'schema_version':1,'scenario':'controller-own-cpu-whisper',
            'elapsed_seconds':round(time.perf_counter()-started,3),
            'reference_words':len(expected.split()),'transcript_words':len(actual.split()),
            'normalized_exact_match':actual==expected,'deliveries':clipboard.count,
            'device':controller._devices.get('stt'),'content_persisted':False,
            'physical_inputs':False,'native_clipboard':False,'gpu_loaded':False}
        if actual!=expected or clipboard.count!=1: raise ValueError('transcript_mismatch')
    finally:
        controller.command('quit')
        thread.join(12)
        if thread.is_alive(): raise TimeoutError('controller_cleanup')
    result['owned_workers_remaining']=len(pool.workers)
    result['microphone_owned']=controller.microphone.owned
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    try: print(json.dumps(probe(args.root.resolve()),indent=2));return 0
    except Exception:
        print(json.dumps({'scenario':'controller-own-cpu-whisper','error':'probe_failed'}));return 1


if __name__=='__main__': raise SystemExit(main())
