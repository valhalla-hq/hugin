"""Own portable package paths, inventories and exact recorded-file verification."""
import hashlib
from pathlib import Path, PurePosixPath
import re


def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()


def write_search_path(scripts):
    # Relative to the private executable, never an installed venv's home.
    with (Path(scripts)/'python312._pth').open('x',encoding='utf-8',newline='\n') as output:
        output.write('.\nLib\n../Lib/site-packages\nDLLs\n../../../src\nimport site\n')


def parse_records(records):
    if not isinstance(records,list) or not records or len(records)>100000:
        raise ValueError('payload_manifest_invalid')
    names=set();result=[]
    for record in records:
        if not isinstance(record,dict) or set(record)!={'file','size','sha256'}:
            raise ValueError('payload_manifest_invalid')
        name=record['file'];size=record['size'];sha=record['sha256']
        if (not isinstance(name,str) or not name or '\\' in name or ':' in name
                or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
                or PurePosixPath(name).as_posix()!=name or name.casefold() in names
                or type(size) is not int or not 0<=size<2**63
                or not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha)):
            raise ValueError('payload_manifest_invalid')
        names.add(name.casefold());result.append(dict(record))
    return result


def inventory(root):
    root=Path(root).resolve();records=[]
    for path in sorted(root.rglob('*')):
        name=path.relative_to(root).as_posix()
        if path.is_symlink() or path.resolve()!=path:
            raise ValueError('payload_redirected')
        if not path.is_file():continue
        if name.startswith(('.runtime/state/','.runtime/desktop-','.runtime/production-')):
            raise ValueError('state_in_payload')
        records.append(dict(file=name,size=path.stat().st_size,sha256=digest(path)))
    return parse_records(records)


def verify_inventory(root,records,*,exact=True):
    root=Path(root).resolve();records=parse_records(records)
    for record in records:
        path=root/record['file']
        if (path.resolve()!=path or not path.is_file() or path.stat().st_size!=record['size']
                or digest(path)!=record['sha256']):
            raise ValueError('payload_integrity_failed')
    if exact and {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}!={r['file'] for r in records}:
        raise ValueError('payload_files_changed')


def load_release(root):
    from hugin.config import read_json_object
    value=read_json_object(Path(root)/'release-manifest.json',limit=32*1024*1024)
    if (set(value)!={'schema_version','app','version','source_commit','python_version','package_profiles','files'}
            or type(value['schema_version']) is not int or value['schema_version']!=1
            or value['app']!='Hugin' or value['python_version']!='3.12.10'
            or not isinstance(value['version'],str) or not re.fullmatch(r'\d+\.\d+\.\d+',value['version'])
            or not isinstance(value['source_commit'],str) or not re.fullmatch('[0-9a-f]{40}',value['source_commit'])
            or not isinstance(value['package_profiles'],dict)
            or set(value['package_profiles'])!={'controller','stt','tts'}):
        raise ValueError('release_manifest_invalid')
    value['files']=parse_records(value['files'])
    return value


def verify_release(root):
    value=load_release(root)
    # Installed state, bytecode caches and Inno's uninstaller are separate owners.
    verify_inventory(root,value['files'],exact=False)
    return value
