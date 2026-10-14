"""Plan/apply Hugin-owned model, CUDA, and new isolated engine environments.

No model download, no old-environment modification, no GPU initialization.
Existing divergent destination files fail closed rather than being overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from hugin.config import load_settings
from hugin.workers.assets import verify_files


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()


def copy_locked(source, target, lock):
    verify_files(source,lock,exact=False)
    records=json.loads(lock.read_text(encoding='utf-8'))['files']
    for item in records:
        origin=(source/item['file']).resolve()
        destination=(target/item['file']).resolve()
        if not destination.is_relative_to(target.resolve()):
            raise ValueError('destination_outside_root')
        if destination.exists():
            if destination.stat().st_size != item['size'] or digest(destination) != item['sha256']:
                raise ValueError('destination_integrity_conflict')
            continue
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent,delete=False,suffix='.partial') as temporary:
            partial=Path(temporary.name)
        try:
            shutil.copyfile(origin,partial)
            if partial.stat().st_size != item['size'] or digest(partial) != item['sha256']:
                raise ValueError('copied_integrity_conflict')
            os.replace(partial,destination)
        finally:
            partial.unlink(missing_ok=True)
    verify_files(target,lock)


def prepare_environment(engine):
    runtime=ROOT/'.runtime'/engine
    executable=runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not executable.exists():
        if runtime.exists():
            raise ValueError('existing_incomplete_environment')
        venv.EnvBuilder(with_pip=True).create(runtime)
    # Every resolved dependency is pinned; no unrelated interpreter or tool upgrade.
    command=[str(executable),'-m','pip','install','--disable-pip-version-check',
             '--no-deps','-r',str(ROOT/'locks'/f'{engine}.txt')]
    if engine=='tts':
        command.extend(['--extra-index-url','https://download.pytorch.org/whl/cu128'])
    subprocess.run(command,check=True)
    subprocess.run([str(executable),'-m','pip','check'],check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stt-source',type=Path)
    parser.add_argument('--tts-source',type=Path)
    parser.add_argument('--cuda-source',type=Path)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--install',choices=('stt','tts','all'))
    args=parser.parse_args()
    settings=load_settings(ROOT)
    copies=[]
    for name,source in (('stt',args.stt_source),('tts',args.tts_source),('cuda',args.cuda_source)):
        if source is not None:
            target=settings.paths[name+'_model'] if name!='cuda' else ROOT/'.runtime/cuda'
            lock=ROOT/'locks'/('cuda.json' if name=='cuda' else name+'-model.json')
            copies.append((source.resolve(),target,lock))
    plan={'schema_version':1,'mode':'apply' if args.apply else 'plan',
          'copies':[{'source':str(s),'destination':str(t),'lock':str(l)} for s,t,l in copies],
          'new_environments':[] if not args.install else
              [str(ROOT/'.runtime'/e) for e in (('stt','tts') if args.install=='all' else (args.install,))],
          'gpu_load':False,'model_download':False}
    print(json.dumps(plan,indent=2))
    if not args.apply:
        return 0
    if sys.version_info[:3]!=(3,12,10):
        raise ValueError('python_version_mismatch')
    for source,target,lock in copies:
        copy_locked(source,target,lock)
    if args.install:
        for engine in (('stt','tts') if args.install=='all' else (args.install,)):
            prepare_environment(engine)
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('Engine preparation failed: '+type(error).__name__,file=sys.stderr)
        raise SystemExit(2)
