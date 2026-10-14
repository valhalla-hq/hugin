"""Whitelisted installed-version facts, read without importing native engines."""
from importlib import metadata
from pathlib import Path
import re

PACKAGES={
    'stt':('faster-whisper','ctranslate2','numpy','av'),
    'tts':('faster-qwen3-tts','qwen-tts','torch','torchaudio','transformers','numpy'),
}


def observed_versions(root: Path):
    groups={}
    for engine,wanted in PACKAGES.items():
        versions=dict.fromkeys(wanted)
        directory=(root/'.runtime'/engine/'Lib/site-packages').resolve()
        if not directory.is_relative_to(root.resolve()) or not directory.is_dir():
            groups[engine]=versions;continue
        seen=set()
        try:
            for distribution in metadata.distributions(path=[str(directory)]):
                name=re.sub(r'[-_.]+','-',distribution.metadata.get('Name','').casefold())
                if name not in versions: continue
                value=distribution.version
                if name in seen:
                    versions[name]=None
                else:
                    versions[name]=value if isinstance(value,str) and re.fullmatch(r'[0-9][A-Za-z0-9.!+_-]{0,63}',value) else None
                seen.add(name)
        except (OSError,ValueError,UnicodeError,KeyError,TypeError):
            versions=dict.fromkeys(wanted)
        groups[engine]=versions
    return groups
