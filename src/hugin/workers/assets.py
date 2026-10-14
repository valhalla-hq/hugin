"""Complete file-lock validation before importing native engine code."""
import hashlib
import json
from pathlib import Path, PurePosixPath
from dataclasses import dataclass

from hugin.errors import HuginError


@dataclass(frozen=True)
class FileLock:
    document: dict
    files: tuple[dict, ...]


def read_file_lock(lock: Path) -> FileLock:
    """Own lock parsing once; callers use these validated file facts."""
    try:
        document = json.loads(lock.read_text(encoding='utf-8'))
        records = document['files']
        if not isinstance(records,list) or not records:
            raise ValueError
        names = set()
        for item in records:
            if not isinstance(item,dict) or set(item) != {'file','size','sha256'}:
                raise ValueError
            name=item['file']
            if (not isinstance(name,str) or not name or '\\' in name or ':' in name
                    or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
                    or PurePosixPath(name).as_posix() != name or name in names):
                raise ValueError
            if type(item['size']) is not int or not 0 < item['size'] < 2**63:
                raise ValueError
            digest=item['sha256']
            if not isinstance(digest,str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError
            names.add(name)
        return FileLock(document,tuple(dict(item) for item in records))
    except (OSError,ValueError,KeyError,TypeError):
        raise HuginError('asset_integrity','engine_assets') from None


def load_file_lock(lock: Path) -> tuple[dict, ...]:
    return read_file_lock(lock).files


def verify_records(directory: Path, records: tuple[dict, ...], *, exact: bool = True) -> None:
    try:
        names = set()
        for item in records:
            path = (directory / item['file']).resolve()
            if (item['file'] in names or not path.is_relative_to(directory.resolve())
                    or path == directory.resolve() or path.stat().st_size != item['size']):
                raise ValueError
            names.add(item['file'])
            with path.open('rb') as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != item['sha256']:
                    raise ValueError
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
        if not names or (exact and actual != names):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise HuginError('asset_integrity', 'engine_assets') from None


def verify_files(directory: Path, lock: Path, *, exact: bool = True) -> None:
    verify_records(directory,load_file_lock(lock),exact=exact)
