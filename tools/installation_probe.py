"""Technical installed-artifact check; no microphone, clipboard or audible output."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import threading
import time

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from hugin.config import load_settings,verify_voice_assets
from hugin.cues import load_cue_signals
from hugin.targets import load_target_approvals
from production_package import load_release,verify_release

_HELD=[]  # Failed cleanup retains process/native ownership in this probe session.

PROFILE_CODE='''
import sys,os,json,re
from pathlib import Path
from importlib import metadata
root=Path(sys.argv[1]).resolve();profile=sys.argv[2]
assert sys.flags.isolated and not any(not Path(p).resolve().is_relative_to(root) for p in sys.path)
cuda=os.add_dll_directory(str(root/'.runtime/cuda'))
report_stream=sys.stdout;sys.stdout=sys.stderr
if profile=='controller':
    import tkinter,PIL,sounddevice,comtypes,pystray
    assert tkinter.Tcl().eval('info patchlevel')=='8.6.15'
    from hugin.windows.selection_probe import _load_comtypes,_system_typelib
    _,client=_load_comtypes();client.GetModule(_system_typelib())
    assert client.gen_dir is None
elif profile=='stt':
    import faster_whisper,ctranslate2,numpy,av
else:
    import torch,torchaudio,transformers,qwen_tts,faster_qwen3_tts
versions={}
for dist in metadata.distributions():
    name=re.sub(r'[-_.]+','-',dist.metadata['Name'].lower())
    assert name not in versions
    versions[name]=dist.version
sys.stdout=report_stream
print(json.dumps(dict(prefix=sys.prefix,isolated=bool(sys.flags.isolated),versions=versions)))
'''


def private_profile(root,profile,expected):
    from hugin.windows.process import OwnedProcess
    executable=root/'.runtime'/profile/'Scripts/python.exe'
    try:
        owner=OwnedProcess([str(executable),'-B','-c',PROFILE_CODE,str(root),profile],
            stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,cwd=str(root),
            env={**os.environ,'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','DO_NOT_TRACK':'1'})
    except Exception as error:
        partial=getattr(error,'owner',None)
        if partial is not None:
            _HELD.append(partial)
            if getattr(partial,'process_created',None) is False or partial.poll() is not None:
                try:partial.close();_HELD.remove(partial)
                except Exception:pass
        raise
    _HELD.append(owner);captured=[];read_errors=[]
    def read_report():
        try:
            parts=[];size=0
            while True:
                piece=owner.stdout.read(65537-size)
                if not piece:break
                parts.append(piece);size+=len(piece)
                if size>65536:raise ValueError('private_profile_capacity')
            captured.append(b''.join(parts))
        except Exception as error:read_errors.append(error)
    reader=threading.Thread(target=read_report,daemon=True)
    reader.start()
    try:
        deadline=time.monotonic()+90
        while owner.poll() is None:
            if read_errors or time.monotonic()>=deadline:
                owner.kill();owner.wait(timeout=5)
                raise RuntimeError('private_profile_read_failed' if read_errors else 'private_profile_timeout')
            time.sleep(.01)
        code=owner.wait(timeout=0)
        reader.join(3)
        if reader.is_alive() or read_errors or not captured or code!=0:
            raise RuntimeError('private_profile_failed_'+profile)
        facts=json.loads(captured[0])
        if facts['versions']!=expected:raise RuntimeError('installed_package_versions_differ_'+profile)
        return dict(profile=profile,isolated=facts['isolated'],packages=len(expected),metrics=owner.metrics())
    finally:
        if owner.poll() is not None:
            owner.close();_HELD.remove(owner)


def check_inputs(root):
    from hugin.activation import require_activation
    from hugin.bindings import BINDINGS,PROFILE
    from hugin.windows.input import WindowsInputs
    from hugin.windows.instance import InstanceGuard
    settings=load_settings(root);require_activation(settings.paths['state'])
    guard=InstanceGuard();inputs=None
    if not guard.acquire():guard.close();raise RuntimeError('quit_hugin_before_input_probe')
    try:
        inputs=WindowsInputs(lambda action:None)
        inputs.start();inputs.set_cancel_active(True)
        keys=inputs._backend.keys.copy();hook=bool(inputs._backend.hook)
        inputs.set_cancel_active(False);inputs.stop()
        if keys!={1,2,3} or not hook or not inputs.closed:raise RuntimeError('input_profile_not_registered')
        return dict(profile=PROFILE,registered=True,closed=True,
            bindings=[dict(action=b.action,shortcut=b.shortcut,mouse=b.mouse) for b in BINDINGS],
            physical_clicks_tested=False)
    finally:
        try:
            if inputs is not None and not inputs.closed:inputs.stop()
        finally:
            if inputs is None or inputs.closed:
                try:guard.close()
                except Exception:_HELD.append(guard);raise
            else:_HELD.append((guard,inputs))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--inputs',action='store_true')
    args=parser.parse_args();root=args.root.resolve()
    report=args.report or root/'.runtime/installation-probe.json'
    started=time.perf_counter();cpu=time.process_time()
    facts=dict(schema_version=1,app='Hugin',success=False,microphone=False,clipboard=False,audible_speech=False)
    try:
        manifest=verify_release(root);verify_voice_assets(load_settings(root));load_cue_signals(root)
        load_target_approvals(root)
        facts.update(version=manifest['version'],source_commit=manifest['source_commit'],
            profiles=[private_profile(root,p,manifest['package_profiles'][p]) for p in ('controller','stt','tts')])
        if args.inputs:facts['inputs']=check_inputs(root)
        facts['success']=True
    except Exception as error:
        facts['error']=type(error).__name__+':'+str(error)[:160]
    facts.update(elapsed_seconds=round(time.perf_counter()-started,3),cpu_seconds=round(time.process_time()-cpu,3),
                 cleanup_pending=bool(_HELD))
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(facts,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(facts))
    return int(not facts['success'] or facts['cleanup_pending'])


if __name__=='__main__':raise SystemExit(main())
