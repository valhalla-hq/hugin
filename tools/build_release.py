"""Build an offline Hugin artifact from clean Git and SHA256-locked local inputs."""
from pathlib import Path
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from hugin.config import load_settings,verify_voice_assets
from hugin.cues import ASSET_DIRECTORY,load_cue_signals
from hugin.workers.assets import read_file_lock,verify_records
from production_package import digest,inventory,write_search_path,verify_release
from runtime_packages import PROFILES,PYTHON,load_wheel_lock,validate_wheelhouse,write_requirements

SOURCE_PATHS=('src','config','locks','assets','tools/launch.py','tools/desktop_setup.py',
              'tools/install_setup.py','tools/production_package.py','tools/installation_probe.py')


def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()


def copy_python(base,scripts):
    scripts.mkdir(parents=True,exist_ok=False)
    for name in ('DLLs','Lib','tcl'):
        shutil.copytree(base/name,scripts/name,
            ignore=shutil.ignore_patterns('__pycache__','site-packages','test','tests','idlelib','ensurepip'))
    for path in base.iterdir():
        if path.is_file() and (path.suffix in ('.dll','.exe') or path.name=='LICENSE.txt'):
            shutil.copy2(path,scripts/path.name)
    write_search_path(scripts)


def materialize_profile(payload,source,profile,lock,work):
    scripts=payload/'.runtime'/profile/'Scripts'
    copy_python(Path(sys.base_prefix),scripts)
    target=payload/'.runtime'/profile/'Lib/site-packages'
    requirements=work/(profile+'-requirements.txt')
    write_requirements(source/'.runtime/wheelhouse',lock,profile,requirements)
    with (work/(profile+'-pip.txt')).open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-m','pip','--disable-pip-version-check','install',
            '--no-index','--no-deps','--require-hashes','--no-compile','--no-warn-script-location',
            '--target',str(target),'-r',str(requirements)],check=True,stdout=log,stderr=subprocess.STDOUT)
    # pip's generated console launchers refer to the build interpreter and are
    # not application entry points. Package-owned subdirectory binaries stay.
    generated=target/'bin'
    if generated.exists():
        if generated.resolve()!=generated or not generated.is_relative_to(payload):
            raise ValueError('generated_script_path_invalid')
        shutil.rmtree(generated)
    if profile=='controller':
        # Provision the trusted static namespace before any COM client import.
        # Dynamic UIA interfaces remain memory-only in the existing owner.
        subprocess.run([str(scripts/'python.exe'),'-B','-c',
            'from hugin.windows.selection_probe import _load_comtypes;_load_comtypes()'],check=True)


def copy_assets(payload,source):
    for name,directory in (('stt-model','models/stt'),('tts-model','models/tts'),('cuda','cuda')):
        facts=read_file_lock(payload/'locks'/(name+'.json'))
        origin=source/'.runtime'/directory;target=payload/'.runtime'/directory
        verify_records(origin,facts.files)
        for record in facts.files:
            output=target/record['file'];output.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(origin/record['file'],output)
        verify_records(target,facts.files)
    cues=load_cue_signals(source)
    for name,pcm in cues.items():
        output=payload/ASSET_DIRECTORY/(name+'.pcm');output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(pcm)


def launcher(payload,version,work,head):
    # The icon producer and native recipe come from the same pinned tree as the
    # payload. Never reread a mutable worktree midway through a long build.
    subprocess.run([str(payload/'.runtime/controller/Scripts/python.exe'),'-B','-c',
        "import sys;from hugin.branding import hugin_icon;hugin_icon(256).save(sys.argv[1],format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])",
        str(payload/'Hugin.ico')],check=True)
    source=work/'HuginLauncher.cs'
    source.write_text(git('show',head+':packaging/HuginLauncher.cs').replace('@VERSION@',version),encoding='utf-8')
    target=work/'InstallationTarget.cs'
    target.write_text(git('show',head+':packaging/InstallationTarget.cs'),encoding='utf-8')
    compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    subprocess.run([str(compiler),'/nologo','/target:winexe','/platform:x64','/optimize+',
        '/codepage:65001','/reference:System.Web.Extensions.dll','/reference:System.Windows.Forms.dll','/win32icon:'+str(payload/'Hugin.ico'),
        '/out:'+str(payload/'Hugin.exe'),str(source),str(target)],check=True)
    return dict(compiler_sha256=digest(compiler),launcher_sha256=digest(payload/'Hugin.exe'))


def build(source,output,iscc):
    if sys.platform!='win32' or sys.version_info[:3]!=(3,12,10):raise ValueError('build_requires_pinned_windows_python')
    if git('status','--porcelain'):raise ValueError('build_requires_clean_source')
    head=git('rev-parse','HEAD')
    import ast
    version=ast.literal_eval(git('show',head+':src/hugin/__init__.py').split('__version__ = ',1)[1].splitlines()[0])
    source=Path(source).resolve();output=Path(output).resolve();iscc=Path(iscc).resolve()
    if output.exists() or output==source or output.is_relative_to(source):raise ValueError('build_output_must_be_new_separate_directory')
    if sys.base_prefix==sys.prefix or not (Path(sys.base_prefix)/'tcl').is_dir():raise ValueError('build_python_base_invalid')
    output.mkdir(parents=True,exist_ok=False);payload=output/'app';payload.mkdir()
    work=output/'build-evidence';work.mkdir()
    started=time.perf_counter();cpu=time.process_time()
    archive=subprocess.check_output(['git','-C',str(ROOT),'archive','--format=tar',head,'--',*SOURCE_PATHS])
    with tarfile.open(fileobj=io.BytesIO(archive)) as files:files.extractall(payload,filter='data')
    lock=load_wheel_lock(payload)
    validate_wheelhouse(source/'.runtime/wheelhouse',lock,require_manifest=True)
    verify_voice_assets(load_settings(payload))
    for profile in PROFILES:
        print(json.dumps(dict(stage='private_runtime',profile=profile)),flush=True)
        materialize_profile(payload,source,profile,lock,work)
    print(json.dumps(dict(stage='locked_models_cuda_cues')),flush=True)
    copy_assets(payload,source)
    native=launcher(payload,version,work,head)
    print(json.dumps(dict(stage='inventory_and_hash_payload')),flush=True)
    records=inventory(payload)
    manifest=dict(schema_version=1,app='Hugin',version=version,source_commit=head,
        python_version=PYTHON,package_profiles={p:{w.name:w.version for w in lock.profiles[p]} for p in PROFILES},files=records)
    (payload/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    verify_release(payload)
    print(json.dumps(dict(stage='verify_private_imports')),flush=True)
    subprocess.run([str(payload/'.runtime/controller/Scripts/python.exe'),'-B',
        str(payload/'tools/installation_probe.py'),'--root',str(payload),
        '--report',str(work/'portable-probe.json')],check=True)
    installer=output/'installer';installer.mkdir()
    print(json.dumps(dict(stage='compile_installer',payload_bytes=sum(r['size'] for r in records),files=len(records))),flush=True)
    recipe=work/'Hugin.iss'
    recipe.write_text(git('show',head+':packaging/Hugin.iss'),encoding='utf-8-sig')
    with (work/'inno.txt').open('w',encoding='utf-8') as log:
        subprocess.run([str(iscc),'/DPayload='+str(payload),'/DVersion='+version,'/DCommitShort='+head[:12],'/DManifestSHA='+digest(payload/'release-manifest.json'),'/DOutput='+str(installer),str(recipe)],check=True,stdout=log,stderr=subprocess.STDOUT)
    artifacts=inventory(installer)
    receipt=dict(schema_version=1,version=version,source_commit=head,source_tree=git('rev-parse',head+':src'),
        unsigned=True,installer_files=artifacts,payload_files=len(records),payload_bytes=sum(r['size'] for r in records),
        wall_seconds=round(time.perf_counter()-started,3),controller_cpu_seconds=round(time.process_time()-cpu,3),
        native=native,iscc_sha256=digest(iscc),base_python_exe_sha256=digest(Path(sys.base_prefix)/'python.exe'),
        costs_unmeasured=['compiler/pip process-family CPU and peak memory','bit-identical rebuild','agent tokens'])
    (output/'build-manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt),flush=True)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-runtime',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--iscc',type=Path,required=True)
    args=parser.parse_args()
    build(args.source_runtime,args.output,args.iscc)
    return 0


if __name__=='__main__':raise SystemExit(main())
