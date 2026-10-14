"""Plan/apply Hugin-owned model, CUDA, and new isolated engine environments.

No model download, no old-environment modification, no GPU initialization.
Existing divergent destination files fail closed rather than being overwritten.
"""
from __future__ import annotations
import argparse
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
from hugin.workers.assets import load_file_lock,verify_records
from runtime_packages import (BUILD_TOOLS, PROFILES, PYTHON, SOURCE_DATE_EPOCH,
    assemble_manifest, digest, faster_qwen_source, inspect_wheels, load_wheel_lock,
    package_origin, package_pins, validate_wheelhouse, wheel_metadata, write_requirements)


def validate_copy(source,target,records,*,allow_extra=False):
    verify_records(source,records,exact=False)
    validate_destination(target,records,allow_extra=allow_extra)


def validate_destination(target,records,*,allow_extra=False):
    expected={item['file'] for item in records}
    if target.exists():
        existing={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
        if existing - expected and not allow_extra:
            raise ValueError('destination_unlocked_files')
    for item in records:
        destination=(target/item['file']).resolve()
        if not destination.is_relative_to(target.resolve()):
            raise ValueError('destination_outside_root')
        if destination.exists():
            if destination.stat().st_size != item['size'] or digest(destination) != item['sha256']:
                raise ValueError('destination_integrity_conflict')


def copy_locked(source, target, lock, *, records=None,allow_extra=False):
    records=records or load_file_lock(lock)
    validate_copy(source,target,records,allow_extra=allow_extra)
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
    verify_records(target,records,exact=not allow_extra)


def _installed_versions(executable,pins):
    script='''import importlib.metadata as m,json,sys
versions={}
for name in json.loads(sys.argv[1]):
    try: versions[name]=m.version(name)
    except m.PackageNotFoundError: versions[name]=None
print(json.dumps(versions))
'''
    result=subprocess.run([str(executable),'-I','-c',script,json.dumps(list(pins))],
        check=True,capture_output=True,text=True)
    versions=json.loads(result.stdout)
    if not isinstance(versions,dict) or set(versions) != set(pins):
        raise ValueError('package_metadata_invalid')
    return versions


def _installation_paths(executable):
    # Ask the installing pip for its own scheme; sysconfig's base stdlib and
    # include paths are read-only inputs, not pip's venv write destinations.
    script='''import json,sys
from pip._internal.locations import get_scheme
scheme=get_scheme('_hugin_write_scope',isolated=True)
print(json.dumps({'prefix':sys.prefix,'paths':{name:getattr(scheme,name)
    for name in ('purelib','platlib','headers','scripts','data')}}))
'''
    result=subprocess.run([str(executable),'-I','-c',script],check=True,capture_output=True,text=True)
    facts=json.loads(result.stdout)
    if (not isinstance(facts,dict) or set(facts)!={'prefix','paths'}
            or not isinstance(facts['prefix'],str) or not Path(facts['prefix']).is_absolute()
            or not isinstance(facts['paths'],dict)
            or set(facts['paths'])!={'purelib','platlib','headers','scripts','data'}
            or any(not isinstance(path,str) or not Path(path).is_absolute() for path in facts['paths'].values())):
        raise ValueError('package_metadata_invalid')
    return facts


def _validate_environment_installation(runtime,executable,owned_files,*,reason):
    # A valid outer marker does not own a redirected package/script subtree.
    # Check links before starting Python, whose site import could follow them.
    if any(path.resolve()!=path for path in owned_files):
        raise ValueError(reason)
    pending=[runtime] if runtime.exists() else []
    seen=set()
    while pending:
        directory=pending.pop().resolve()
        if not directory.is_relative_to(runtime):raise ValueError(reason)
        if directory in seen:continue
        seen.add(directory)
        with os.scandir(directory) as entries:
            for entry in entries:
                if (entry.is_symlink() or entry.is_junction()) and not Path(entry.path).resolve().is_relative_to(runtime):
                    raise ValueError(reason)
                if entry.is_dir():pending.append(Path(entry.path))
    if executable.exists():
        facts=_installation_paths(executable)
        if Path(facts['prefix']).resolve()!=runtime or any(
                not Path(path).resolve().is_relative_to(runtime) for path in facts['paths'].values()):
            raise ValueError(reason)


def _environment_spec(root,engine):
    root=Path(root).resolve()
    if engine not in PROFILES:
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
    _validate_environment_installation(runtime,executable,
        (marker,runtime/'hugin-wheel-installation.json',runtime/'hugin-offline-requirements.txt',runtime/'pyvenv.cfg'),
        reason='environment_outside_runtime')
    return runtime,executable,pins,expected_owner,marker


def _python_facts(executable):
    script="import json,sys,struct,tkinter;print(json.dumps({'python':'.'.join(map(str,sys.version_info[:3])),'bits':struct.calcsize('P')*8,'tk':str(tkinter.TkVersion)}))"
    result=subprocess.run([str(executable),'-I','-c',script],check=True,capture_output=True,text=True)
    facts=json.loads(result.stdout)
    if facts != {'python':PYTHON,'bits':64,'tk':'8.6'}:
        raise ValueError('python_version_or_tk_mismatch')
    return facts


def validate_environment(root,engine):
    runtime,executable,pins,_,_=_environment_spec(root,engine)
    proof=runtime/'hugin-wheel-installation.json'
    if proof.exists() and json.loads(proof.read_text(encoding='utf-8')) != _installation_proof(load_wheel_lock(root),engine):
        raise ValueError('environment_wheel_lock_conflict')
    if executable.exists():
        _python_facts(executable)
        installed=_installed_versions(executable,pins)
        if any(version is not None and version != pins[name] for name,version in installed.items()):
            raise ValueError('existing_package_version_conflict')


def _installation_proof(lock,profile):
    return {'schema_version':1,'profile':profile,'python':PYTHON,
            'wheel_profile_sha256':lock.profile_digest(profile)}


def _pip(executable,*arguments,extra_env=None):
    # User/global pip configuration must not redirect an owned installation.
    environment={key:value for key,value in os.environ.items() if not key.upper().startswith('PIP_')}
    environment['PIP_CONFIG_FILE']=os.devnull
    if extra_env:
        environment.update(extra_env)
    subprocess.run([str(executable),'-I','-m','pip','--isolated','--no-cache-dir',*arguments],check=True,env=environment)


def prepare_environment(engine, *, root=ROOT, wheelhouse=None):
    root=Path(root).resolve()
    runtime,executable,pins,expected_owner,marker=_environment_spec(root,engine)
    lock=load_wheel_lock(root)
    wheelhouse=Path(wheelhouse).resolve() if wheelhouse is not None else root/'.runtime/wheelhouse'
    validate_wheelhouse(wheelhouse,lock,(engine,))
    _python_facts(sys.executable)
    proof=runtime/'hugin-wheel-installation.json'
    expected_proof=_installation_proof(lock,engine)
    if proof.exists() and json.loads(proof.read_text(encoding='utf-8')) != expected_proof:
        raise ValueError('environment_wheel_lock_conflict')
    if not runtime.exists():
        runtime.mkdir(parents=True)
        marker.write_text(json.dumps(expected_owner,indent=2)+'\n',encoding='utf-8')
    if not executable.exists():
        venv.EnvBuilder(with_pip=True).create(runtime)
    _validate_environment_installation(runtime,executable,
        (marker,proof,runtime/'hugin-offline-requirements.txt',runtime/'pyvenv.cfg'),
        reason='environment_outside_runtime')
    _python_facts(executable)
    installed=_installed_versions(executable,pins)
    if any(version is not None and version != pins[name] for name,version in installed.items()):
        raise ValueError('existing_package_version_conflict')
    requirements=runtime/'hugin-offline-requirements.txt'
    write_requirements(wheelhouse,lock,engine,requirements)
    # Even a previously online-created owned venv gets verified wheel bytes
    # once. Its exact versions cannot change; the proof makes repeats no-ops.
    command=['install','--disable-pip-version-check',
             '--no-index','--no-deps','--require-hashes','--force-reinstall','-r',str(requirements)]
    if not proof.exists() or any(version is None for version in installed.values()):
        _pip(executable,*command)
        if _installed_versions(executable,pins) != pins:
            raise ValueError('installed_package_version_conflict')
    _pip(executable,'check','--disable-pip-version-check')
    if not proof.exists():
        proof.write_text(json.dumps(expected_proof,indent=2)+'\n',encoding='utf-8')


def _download(executable, destination, pins, index):
    missing=dict(pins)
    seen=set()
    for path in destination.glob('*.whl'):
        name,version=wheel_metadata(path)
        if name in pins:
            if version != pins[name] or name in seen:
                raise ValueError('wheel_package_mismatch')
            missing.pop(name)
            seen.add(name)
    if not missing:
        return
    destination.mkdir(parents=True,exist_ok=True)
    _pip(executable,'download','--disable-pip-version-check',
        '--only-binary=:all:','--no-deps','--index-url',index,'--dest',str(destination),
        *[f'{name}=={version}' for name,version in sorted(missing.items())])


def _fetch_source(url,path,expected_sha256=None):
    import urllib.request
    if not path.exists():
        partial=path.with_suffix(path.suffix+'.partial')
        with urllib.request.urlopen(url,timeout=60) as incoming, partial.open('wb') as output:
            total=0
            while chunk:=incoming.read(1024*1024):
                total+=len(chunk)
                if total>50*1024*1024:
                    raise ValueError('source_archive_limit')
                output.write(chunk)
        if expected_sha256 and digest(partial) != expected_sha256:
            raise ValueError('source_archive_integrity_conflict')
        partial.replace(path)
    if not 0 < path.stat().st_size <= 50*1024*1024:
        raise ValueError('source_archive_limit')
    actual=digest(path)
    if expected_sha256 and actual != expected_sha256:
        raise ValueError('source_archive_integrity_conflict')
    return actual


def _source_spec(root,name,version):
    if name=='faster-qwen3-tts':
        return faster_qwen_source(root),None
    import urllib.request
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=60) as response:
        raw=response.read(1024*1024+1)
    if len(raw)>1024*1024:
        raise ValueError('source_archive_limit')
    data=json.loads(raw)
    candidates=[item for item in data['urls'] if item['packagetype']=='sdist'
                and item['filename']==f'{name}-{version}.tar.gz' and not item['yanked']]
    if len(candidates)!=1:
        raise ValueError('source_archive_unavailable')
    item=candidates[0]
    if not item['url'].startswith('https://files.pythonhosted.org/packages/'):
        raise ValueError('source_archive_unavailable')
    return dict(kind='pypi-sdist',version=version,archive_url=item['url']),item['digests']['sha256']


def _build_environment_spec(root):
    root=Path(root).resolve()
    runtime=(root/'.runtime/wheel-build').resolve()
    if not runtime.is_relative_to(root/'.runtime') or runtime == root/'.runtime':
        raise ValueError('build_environment_outside_runtime')
    marker=runtime/'hugin-build.json'
    executable=runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    requirements=runtime/'build-requirements.txt'
    owner={'schema_version':2,'runtime':str(runtime),'python':PYTHON,
           'build_tools':dict(BUILD_TOOLS),'source_date_epoch':SOURCE_DATE_EPOCH}
    if runtime.exists() and (not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')) != owner):
        raise ValueError('build_environment_ownership_conflict')
    _validate_environment_installation(runtime,executable,(marker,requirements,runtime/'pyvenv.cfg'),
        reason='build_environment_outside_runtime')
    return runtime,executable,marker,requirements,owner


def _build_source_wheel(root,house,name,spec,expected_hash):
    # Establish the write owner before source/tool downloads or build writes.
    runtime,executable,marker,requirements,owner=_build_environment_spec(root)
    source=house/(name+('.zip' if spec['kind']=='git-archive' else '.tar.gz'))
    spec=dict(spec,archive_sha256=_fetch_source(spec['archive_url'],source,expected_hash),
              build_tools=dict(BUILD_TOOLS),source_date_epoch=SOURCE_DATE_EPOCH)
    destination=house/'tts'
    existing=[path for path in destination.glob('*.whl') if wheel_metadata(path)[0]==name]
    receipt=house/(name+'-build.json')
    if existing:
        records=inspect_wheels_for_source(existing,name,spec['version'])
        if not receipt.exists() or json.loads(receipt.read_text(encoding='utf-8')) != {'build':spec,'wheel':records}:
            raise ValueError('wheel_build_receipt_conflict')
        return spec
    tools=house/'_build_tools'
    _download(sys.executable,tools,dict(BUILD_TOOLS),'https://pypi.org/simple')
    tool_records=inspect_wheels(tools,dict(BUILD_TOOLS),'_build_tools')
    if not runtime.exists():
        runtime.mkdir(parents=True)
        marker.write_text(json.dumps(owner,indent=2)+'\n',encoding='utf-8')
        venv.EnvBuilder(with_pip=True).create(runtime)
    _validate_environment_installation(runtime,executable,(marker,requirements,runtime/'pyvenv.cfg'),
        reason='build_environment_outside_runtime')
    _python_facts(executable)
    lines=[f'{(house/item.file).resolve().as_uri()} --hash=sha256:{item.sha256}' for item in tool_records]
    requirements.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    _pip(executable,'install','--disable-pip-version-check','--no-index',
        '--no-deps','--require-hashes','-r',str(requirements))
    if _installed_versions(executable,dict(BUILD_TOOLS)) != dict(BUILD_TOOLS):
        raise ValueError('installed_package_version_conflict')
    _pip(executable,'wheel','--disable-pip-version-check','--no-deps','--no-build-isolation',
        '--no-index','--wheel-dir',str(destination),str(source),
        extra_env={'SOURCE_DATE_EPOCH':str(SOURCE_DATE_EPOCH)})
    wheels=[path for path in destination.glob('*.whl') if wheel_metadata(path)[0]==name]
    receipt.write_text(json.dumps({'build':spec,'wheel':inspect_wheels_for_source(wheels,name,spec['version'])},indent=2)+'\n',encoding='utf-8')
    return spec


def inspect_wheels_for_source(wheels,name,version):
    if len(wheels)!=1 or wheel_metadata(wheels[0])!=(name,version):
        raise ValueError('wheel_package_mismatch')
    path=wheels[0]
    return dict(file=path.name,size=path.stat().st_size,sha256=digest(path))


def prepare_wheelhouse(*,root=ROOT,apply=False):
    root=Path(root).resolve()
    house=(root/'.runtime/wheelhouse').resolve()
    if not house.is_relative_to(root/'.runtime'):
        raise ValueError('environment_outside_runtime')
    pins={profile:package_pins(root,profile) for profile in PROFILES}
    plan={'schema_version':1,'mode':'prepare' if apply else 'plan','writes':bool(apply),
          'downloads':bool(apply),'wheelhouse':str(house),'python':PYTHON,
          'profiles':{profile:len(values) for profile,values in pins.items()},
          'gpu_load':False,'model_download':False}
    if not apply:
        return plan
    _python_facts(sys.executable)
    lock_path=root/'locks/runtime-wheels.json'
    previous=load_wheel_lock(root) if lock_path.exists() else None
    if previous:
        validate_wheelhouse(house,previous,complete=False,require_manifest=(house/'manifest.json').exists())
        if (house/'manifest.json').exists() and all((house/item.file).exists() for records in previous.profiles.values() for item in records):
            return dict(plan,writes=False,downloads=False,already_complete=True)
    owner=house/'preparation.json'
    expected_owner={'schema_version':1,'python':PYTHON,'pins':pins}
    if house.exists() and any(house.iterdir()) and not previous:
        if not owner.exists() or json.loads(owner.read_text(encoding='utf-8')) != expected_owner:
            raise ValueError('wheelhouse_ownership_conflict')
    house.mkdir(parents=True,exist_ok=True)
    if not owner.exists():
        owner.write_text(json.dumps(expected_owner,indent=2)+'\n',encoding='utf-8')
    for profile,values in pins.items():
        ordinary={name:version for name,version in values.items() if package_origin(name,version)=='pypi'}
        cuda={name:version for name,version in values.items() if package_origin(name,version)=='pytorch-cu128'}
        _download(sys.executable,house/profile,ordinary,'https://pypi.org/simple')
        _download(sys.executable,house/profile,cuda,'https://download.pytorch.org/whl/cu128')
    builds={}
    for name,version in pins['tts'].items():
        if package_origin(name,version).endswith('-source'):
            if previous:
                recorded=previous.document['builds'][name]
                source={key:value for key,value in recorded.items() if key not in ('archive_sha256','build_tools','source_date_epoch')}
                expected_hash=recorded['archive_sha256']
            else:
                source,expected_hash=_source_spec(root,name,version)
            builds[name]=_build_source_wheel(root,house,name,source,expected_hash)
    data=assemble_manifest(root,house,builds=builds)
    if previous and previous.document != data:
        raise ValueError('wheel_integrity_conflict')
    encoded=json.dumps(data,indent=2,sort_keys=True)+'\n'
    if not lock_path.exists():
        lock_path.write_text(encoded,encoding='utf-8')
    manifest=house/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8')) != data:
        raise ValueError('wheel_integrity_conflict')
    if not manifest.exists():
        manifest.write_text(encoded,encoding='utf-8')
    validate_wheelhouse(house,load_wheel_lock(root))
    return dict(plan,already_complete=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stt-source',type=Path)
    parser.add_argument('--tts-source',type=Path)
    parser.add_argument('--cuda-source',type=Path)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--install',choices=(*PROFILES,'all'))
    parser.add_argument('--prepare-wheelhouse',action='store_true')
    args=parser.parse_args()
    if args.prepare_wheelhouse:
        if args.install or any((args.stt_source,args.tts_source,args.cuda_source)):
            raise ValueError('preparation_mode_conflict')
        print(json.dumps(prepare_wheelhouse(apply=args.apply),indent=2),flush=True)
        return 0
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
              [str(ROOT/'.runtime'/e) for e in (PROFILES if args.install=='all' else (args.install,))],
          'gpu_load':False,'model_download':False}
    print(json.dumps(plan,indent=2))
    if not args.apply:
        return 0
    if sys.version_info[:3]!=(3,12,10):
        raise ValueError('python_version_mismatch')
    prepared=[(source,target,lock,load_file_lock(lock)) for source,target,lock in copies]
    for source,target,_,records in prepared:
        validate_copy(source,target,records)
    if args.install:
        selected=PROFILES if args.install=='all' else (args.install,)
        _python_facts(sys.executable)
        validate_wheelhouse(ROOT/'.runtime/wheelhouse',load_wheel_lock(ROOT),selected,require_manifest=True)
        for engine in selected:
            validate_environment(ROOT,engine)
    for source,target,lock,records in prepared:
        copy_locked(source,target,lock,records=records)
    if args.install:
        for engine in (PROFILES if args.install=='all' else (args.install,)):
            prepare_environment(engine)
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print('Engine preparation failed: '+type(error).__name__,file=sys.stderr)
        raise SystemExit(2)
