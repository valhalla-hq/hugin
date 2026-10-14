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
import re
import shutil
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from hugin.config import load_settings
from hugin.workers.assets import load_file_lock,verify_records


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()


def validate_copy(source,target,records):
    verify_records(source,records,exact=False)
    expected={item['file'] for item in records}
    if target.exists():
        existing={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
        if existing - expected:
            raise ValueError('destination_unlocked_files')
    for item in records:
        destination=(target/item['file']).resolve()
        if not destination.is_relative_to(target.resolve()):
            raise ValueError('destination_outside_root')
        if destination.exists():
            if destination.stat().st_size != item['size'] or digest(destination) != item['sha256']:
                raise ValueError('destination_integrity_conflict')


def copy_locked(source, target, lock, *, records=None):
    records=records or load_file_lock(lock)
    validate_copy(source,target,records)
    for item in records:
        origin=(source/item['file']).resolve()
        destination=(target/item['file']).resolve()
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent,delete=False,suffix='.partial') as temporary:
            partial=Path(temporary.name)
        try:
            shutil.copyfile(origin,partial)
            if partial.stat().st_size != item['size'] or digest(partial) != item['sha256']:
                raise ValueError('copied_integrity_conflict')
            try:
                os.link(partial,destination)  # Atomic create; never replace a concurrent file.
            except FileExistsError:
                if destination.stat().st_size != item['size'] or digest(destination) != item['sha256']:
                    raise ValueError('destination_integrity_conflict')
        finally:
            partial.unlink(missing_ok=True)
    verify_records(target,records)


def package_pins(root,engine):
    pins={}
    for line in (root/'locks'/f'{engine}.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9.!+_-]+)',line)
        if match:
            name,version=match.groups()
        elif line == (root/'locks/faster-qwen.txt').read_text(encoding='utf-8').strip():
            name='faster-qwen3-tts'
            version=json.loads((root/'locks/engines-provenance.json').read_text(encoding='utf-8'))['tts']['faster_qwen_version']
        else:
            raise ValueError('unlocked_package_requirement')
        name=re.sub(r'[-_.]+','-',name).lower()
        if name in pins:
            raise ValueError('duplicate_package_requirement')
        pins[name]=version
    if not pins:
        raise ValueError('empty_package_lock')
    return pins


def _installed_versions(executable,pins):
    script='''import importlib.metadata as m,json,sys
versions={}
for name in json.loads(sys.argv[1]):
    try: versions[name]=m.version(name)
    except m.PackageNotFoundError: versions[name]=None
print(json.dumps(versions))
'''
    result=subprocess.run([str(executable),'-c',script,json.dumps(list(pins))],
        check=True,capture_output=True,text=True)
    versions=json.loads(result.stdout)
    if not isinstance(versions,dict) or set(versions) != set(pins):
        raise ValueError('package_metadata_invalid')
    return versions


def _environment_spec(root,engine):
    root=Path(root).resolve()
    if engine not in ('stt','tts'):
        raise ValueError('unknown_engine')
    runtime=(root/'.runtime'/engine).resolve()
    if not runtime.is_relative_to(root/'.runtime'):
        raise ValueError('environment_outside_runtime')
    pins=package_pins(root,engine)
    expected_owner={'schema_version':1,'engine':engine,'runtime':str(runtime),
                    'python':'3.12.10','pins':pins}
    marker=runtime/'hugin-environment.json'
    if runtime.exists():
        if not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')) != expected_owner:
            raise ValueError('environment_ownership_or_lock_conflict')
    executable=runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    return runtime,executable,pins,expected_owner,marker


def validate_environment(root,engine):
    _,executable,pins,_,_=_environment_spec(root,engine)
    if executable.exists():
        installed=_installed_versions(executable,pins)
        if any(version is not None and version != pins[name] for name,version in installed.items()):
            raise ValueError('existing_package_version_conflict')


def prepare_environment(engine, *, root=ROOT):
    root=Path(root).resolve()
    runtime,executable,pins,expected_owner,marker=_environment_spec(root,engine)
    if not runtime.exists():
        runtime.mkdir(parents=True)
        marker.write_text(json.dumps(expected_owner,indent=2)+'\n',encoding='utf-8')
    if not executable.exists():
        venv.EnvBuilder(with_pip=True).create(runtime)
    installed=_installed_versions(executable,pins)
    if any(version is not None and version != pins[name] for name,version in installed.items()):
        raise ValueError('existing_package_version_conflict')
    # Every resolved dependency is pinned; no unrelated interpreter or tool upgrade.
    command=[str(executable),'-m','pip','install','--disable-pip-version-check',
             '--no-deps','-r',str(root/'locks'/f'{engine}.txt')]
    if engine=='tts':
        command.extend(['--extra-index-url','https://download.pytorch.org/whl/cu128'])
    if any(version is None for version in installed.values()):
        subprocess.run(command,check=True)
        if _installed_versions(executable,pins) != pins:
            raise ValueError('installed_package_version_conflict')
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
