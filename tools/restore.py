"""Restore a named Hugin checkout's owned runtime; default is read-only.

Model/DLL bytes come from an explicitly selected Hugin source checkout. Package
installation uses exact version pins and the existing pip cache opportunistically;
a complete offline wheelhouse with cryptographic wheel locks is not yet supplied.
"""
from pathlib import Path
import argparse
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from hugin.config import load_settings,verify_voice_assets
from hugin.workers.assets import read_file_lock
from prepare_engines import validate_copy,copy_locked,prepare_environment,validate_environment


def _runtime_paths(root):
    settings=load_settings(root)
    verify_voice_assets(settings)
    runtime=root/'.runtime'
    if (not runtime.resolve().is_relative_to(root) or runtime.resolve() == root
            or not (root/'src/hugin').is_dir()):
        raise ValueError('target_requires_hugin_checkout')
    paths={'stt':settings.paths['stt_model'],'tts':settings.paths['tts_model'],
           'cuda':runtime/'cuda'}
    if any(not path.resolve().is_relative_to(runtime) for path in paths.values()):
        raise ValueError('target_model_outside_runtime')
    return paths


def _copies(source_root,target):
    source_root,target=Path(source_root).resolve(),Path(target).resolve()
    sources,targets=_runtime_paths(source_root),_runtime_paths(target)
    copies=[]
    for engine in ('stt','tts','cuda'):
        filename='cuda.json' if engine=='cuda' else engine+'-model.json'
        source_lock=source_root/'locks'/filename
        target_lock=target/'locks'/filename
        source_facts,target_facts=read_file_lock(source_lock),read_file_lock(target_lock)
        records=source_facts.files
        if source_facts.document != target_facts.document:
            raise ValueError('source_target_lock_mismatch')
        validate_copy(sources[engine],targets[engine],records)
        copies.append((sources[engine],targets[engine],target_lock,records))
    return copies


def _disk_path(path):
    while not path.exists():
        if path == path.parent:
            raise ValueError('target_volume_unavailable')
        path=path.parent
    return path


def plan_restore(source_root,target,*,install=('stt','tts')):
    source_root,target=Path(source_root).resolve(),Path(target).resolve()
    copies=_copies(source_root,target)
    missing=sum(item['size'] for _,destination,_,records in copies
                for item in records if not (destination/item['file']).exists())
    free=shutil.disk_usage(_disk_path(target)).free
    if any(engine not in ('stt','tts') for engine in install):
        raise ValueError('unknown_engine')
    for engine in install:
        validate_environment(target,engine)
    reserve=12*1024**3 if install else 0  # Explicit estimate, separate from observed free bytes.
    return {'schema_version':1,'mode':'plan','target':str(target),'source_root':str(source_root),
        'writes':False,'model_downloads':False,'gpu_load':False,
        'copies':[{'source':str(s),'destination':str(d),'files':len(r),
                   'locked_bytes':sum(item['size'] for item in r)} for s,d,_,r in copies],
        'environments':[str(target/'.runtime'/engine) for engine in install],
        'missing_file_bytes':missing,'environment_reserve_bytes_estimate':reserve,
        'effective_free_bytes':free,'enough_space':free >= missing+reserve,
        'offline_package_restore_verified':False,
        'package_source':'exact version pins; pip cache then configured package indexes',
        'limitations':['Initialize target from the pinned Hugin Git checkout before apply.',
            'No cryptographically locked offline wheelhouse; cache hits do not prove offline restore.',
            'No GPU, audio, input, autostart or old-installation changes.']}


def apply_restore(source_root,target,*,install=('stt','tts')):
    target=Path(target).resolve()
    plan=plan_restore(source_root,target,install=install)
    if sys.version_info[:3] != (3,12,10):
        raise ValueError('python_version_mismatch')
    if not plan['enough_space']:
        raise ValueError('insufficient_disk_space')
    copies=_copies(Path(source_root).resolve(),target)
    for source,destination,lock,records in copies:
        copy_locked(source,destination,lock,records=records)
    for engine in install:
        prepare_environment(engine,root=target)
    return dict(plan,mode='applied',writes=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--source-root',type=Path,default=ROOT)
    parser.add_argument('--install',choices=('none','stt','tts','all'),default='all')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    install=() if args.install=='none' else (('stt','tts') if args.install=='all' else (args.install,))
    try:
        plan=plan_restore(args.source_root,args.target,install=install)
    except Exception as error:
        print(json.dumps({'mode':'plan','target':str(args.target.resolve()),'writes':False,
            'ready':False,'error':_reason(error),
            'action':'Provide validated Hugin source/target checkouts with matching locks and local source runtime files.'}))
        return 2
    print(json.dumps(plan,indent=2),flush=True)
    if args.apply:
        try:
            apply_restore(args.source_root,args.target,install=install)
            print(json.dumps({'mode':'applied','target':str(args.target.resolve()),
                'engine_environments':list(install),'offline_package_restore_verified':False}))
        except Exception as error:
            print('Restore failed: '+_reason(error),file=sys.stderr)
            return 2
    return 0


def _reason(error):
    from hugin.errors import HuginError
    if isinstance(error,HuginError):
        return error.code
    reasons={'target_requires_hugin_checkout','target_model_outside_runtime',
        'source_target_lock_mismatch','target_volume_unavailable','unknown_engine',
        'python_version_mismatch','insufficient_disk_space','destination_unlocked_files',
        'destination_outside_root','destination_integrity_conflict','copied_integrity_conflict',
        'environment_outside_runtime','environment_ownership_or_lock_conflict',
        'existing_package_version_conflict','installed_package_version_conflict',
        'unlocked_package_requirement','duplicate_package_requirement','empty_package_lock',
        'package_metadata_invalid'}
    return error.args[0] if isinstance(error,ValueError) and error.args and isinstance(error.args[0],str) and error.args[0] in reasons else 'restore_failed'


if __name__ == '__main__':
    raise SystemExit(main())
