"""Own portable package paths, inventories and exact recorded-file verification."""
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
import hashlib
import os
import stat
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


def _files(root):
    """Examine each directory/entry once; never follow payload reparse points."""
    pending=[root];count=0
    while pending:
        directory=pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                facts=entry.stat(follow_symlinks=False)
                if (stat.S_ISLNK(facts.st_mode) or
                        getattr(facts,'st_file_attributes',0)&0x400):
                    raise ValueError('payload_redirected')
                path=Path(entry.path)
                if stat.S_ISDIR(facts.st_mode):pending.append(path)
                elif stat.S_ISREG(facts.st_mode):
                    count+=1
                    if count>100000:raise ValueError('payload_capacity')
                    yield path,facts.st_size
                else:raise ValueError('payload_file_type_invalid')


def _hash_files(files):
    # Small bounded batches keep both open files and pending futures bounded.
    iterator=iter(files)
    with ThreadPoolExecutor(max_workers=8) as pool:
        while batch:=list(islice(iterator,64)):
            hashes=list(pool.map(lambda item:digest(item[0]),batch))
            for (path,size),sha in zip(batch,hashes):yield path,size,sha


def inventory(root):
    root=Path(root).resolve();records=[];files=[]
    for path,size in _files(root):
        name=path.relative_to(root).as_posix()
        if name.startswith(('.runtime/state/','.runtime/desktop-','.runtime/production-')):
            raise ValueError('state_in_payload')
        files.append((path,size))
    for path,size,sha in _hash_files(files):
        records.append(dict(file=path.relative_to(root).as_posix(),size=size,sha256=sha))
    return parse_records(sorted(records,key=lambda record:record['file']))


def verify_inventory(root,records,*,exact=True):
    root=Path(root).resolve();records=parse_records(records)
    present={path.relative_to(root).as_posix():(path,size) for path,size in _files(root)}
    if exact and set(present)!={r['file'] for r in records}:
        raise ValueError('payload_files_changed')
    for record in records:
        found=present.get(record['file'])
        if found is None or found[1]!=record['size']:raise ValueError('payload_integrity_failed')
    expected={record['file']:record['sha256'] for record in records}
    for path,_,sha in _hash_files(present[record['file']] for record in records):
        if sha!=expected[path.relative_to(root).as_posix()]:raise ValueError('payload_integrity_failed')


def installer_file_list(records):
    """Only authenticated payload records enter Inno, never a later wildcard."""
    records=parse_records(records)
    names=[record['file'] for record in records]+['release-manifest.json']
    lines=[]
    for name in names:
        # These are actual Windows filenames, but keep serialization explicit.
        if any(char in name for char in '\"*?<>|\r\n'):raise ValueError('installer_filename_invalid')
        path=PurePosixPath(name)
        source=name.replace('/',chr(92)).replace('{','{{')
        parent=str(path.parent).replace('/',chr(92)).replace('{','{{')
        destination='{app}'+('' if parent=='.' else chr(92)+parent)
        lines.append('Source: "{#Payload}'+chr(92)+source+'"; DestDir: "'+destination+'"; Flags: ignoreversion')
    return '\n'.join(lines)+'\n'


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
