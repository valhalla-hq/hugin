"""Complete file-lock validation before importing native engine code."""
import hashlib
import json
from pathlib import Path

from hugin.errors import HuginError


def verify_files(directory: Path, lock: Path, *, exact: bool = True) -> None:
    try:
        records = json.loads(lock.read_text(encoding='utf-8'))['files']
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
