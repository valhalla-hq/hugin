"""Single owner for exact package pins, wheel facts and offline hash inputs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

PROFILES = ('controller', 'stt', 'tts')
PYTHON = '3.12.10'
PLATFORM = 'win_amd64'
BUILD_TOOLS = (('setuptools','78.1.0'), ('wheel','0.45.1'))
SOURCE_DATE_EPOCH = 315532800


def canonical_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
        raise ValueError('package_metadata_invalid')
    return re.sub(r'[-_.]+', '-', value).lower()


def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def package_pins(root, profile):
    if profile not in PROFILES:
        raise ValueError('unknown_engine')
    root = Path(root)
    pins = {}
    for line in (root/'locks'/f'{profile}.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9.!+_-]+)', line)
        if match:
            name, version = match.groups()
        elif profile == 'tts' and line == (root/'locks/faster-qwen.txt').read_text(encoding='utf-8').strip():
            facts = faster_qwen_source(root)
            if line != 'faster-qwen3-tts @ '+facts['archive_url']:
                raise ValueError('unlocked_package_requirement')
            name, version = 'faster-qwen3-tts', facts['version']
        else:
            raise ValueError('unlocked_package_requirement')
        name = canonical_name(name)
        if name in pins:
            raise ValueError('duplicate_package_requirement')
        pins[name] = version
    if not pins:
        raise ValueError('empty_package_lock')
    return pins


def faster_qwen_source(root):
    facts=json.loads((Path(root)/'locks/engines-provenance.json').read_text(encoding='utf-8'))['tts']
    revision,repository,version=(facts[key] for key in ('faster_qwen_revision','faster_qwen_repository','faster_qwen_version'))
    if (not isinstance(revision,str) or not re.fullmatch('[0-9a-f]{40}',revision)
            or not isinstance(repository,str) or not re.fullmatch(r'https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository)
            or not isinstance(version,str) or not re.fullmatch(r'[A-Za-z0-9.!+_-]+',version)):
        raise ValueError('wheel_build_provenance_invalid')
    return dict(kind='git-archive',version=version,revision=revision,
                archive_url=repository+'/archive/'+revision+'.zip')


def _compatible_tag(python, abi, platform):
    if platform not in ('any', PLATFORM):
        return False
    if abi == 'none' and python == 'py3':
        return True
    if python == 'cp312' and abi in ('cp312', 'abi3'):
        return True
    match = re.fullmatch(r'cp3(\d+)', python)
    return bool(match and int(match[1]) <= 12 and abi == 'abi3')


def wheel_metadata(path):
    path = Path(path)
    parts = path.name[:-4].split('-') if path.suffix == '.whl' else []
    if len(parts) not in (5, 6):
        raise ValueError('wheel_metadata_invalid')
    name, version = parts[:2]
    if not any(_compatible_tag(p, a, t) for p in parts[-3].split('.')
               for a in parts[-2].split('.') for t in parts[-1].split('.')):
        raise ValueError('wheel_platform_mismatch')
    with zipfile.ZipFile(path) as archive:
        metadata = [item for item in archive.infolist() if len(PurePosixPath(item.filename).parts)==2
                    and item.filename.endswith('.dist-info/METADATA')]
        if len(metadata) != 1 or metadata[0].file_size > 1024*1024:
            raise ValueError('wheel_metadata_invalid')
        prefix = metadata[0].filename.removesuffix('METADATA')
        names = archive.namelist()
        if prefix+'WHEEL' not in names or prefix+'RECORD' not in names:
            raise ValueError('wheel_metadata_invalid')
        if any(PurePosixPath(item).is_absolute() or '..' in PurePosixPath(item).parts or '\\' in item for item in names):
            raise ValueError('wheel_metadata_invalid')
        message = BytesParser().parsebytes(archive.read(metadata[0]), headersonly=True)
        if len(message.get_all('Name', [])) != 1 or len(message.get_all('Version', [])) != 1:
            raise ValueError('wheel_metadata_invalid')
        actual = canonical_name(message['Name']), message['Version']
        if actual != (canonical_name(name), version):
            raise ValueError('wheel_metadata_invalid')
        return actual


@dataclass(frozen=True)
class Wheel:
    name: str
    version: str
    file: str
    size: int
    sha256: str
    origin: str


@dataclass(frozen=True)
class WheelLock:
    profiles: dict[str, tuple[Wheel, ...]]
    document: dict

    def profile_digest(self, profile):
        facts = dict(python=PYTHON, platform=PLATFORM, profile=profile,
                     wheels=[asdict(item) for item in self.profiles[profile]])
        sources={item.name for item in self.profiles[profile] if item.origin.endswith('-source')}
        if sources:
            facts['builds'] = {name:self.document['builds'][name] for name in sorted(sources)}
        return hashlib.sha256(json.dumps(facts, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def package_origin(name, version):
    if name == 'faster-qwen3-tts':
        return 'faster-qwen-source'
    if name == 'sox':
        return 'pypi-source'
    return 'pytorch-cu128' if name in ('torch', 'torchaudio') and version.endswith('+cu128') else 'pypi'


def inspect_wheels(folder,pins,prefix):
    records={}
    for path in sorted(Path(folder).glob('*.whl')):
        name,version=wheel_metadata(path)
        if name not in pins or pins[name] != version or name in records:
            raise ValueError('wheel_package_mismatch')
        records[name]=Wheel(name,version,f'{prefix}/{path.name}',path.stat().st_size,digest(path),package_origin(name,version))
    if set(records) != set(pins):
        raise ValueError('wheelhouse_incomplete')
    return tuple(records[name] for name in sorted(records))


def assemble_manifest(root, house, *, builds=None):
    root, house = Path(root), Path(house)
    profiles = {}
    for profile in PROFILES:
        pins = package_pins(root, profile)
        profiles[profile] = [asdict(item) for item in inspect_wheels(house/profile,pins,profile)]
    return dict(schema_version=1, python=PYTHON, platform=PLATFORM, profiles=profiles, builds=builds or {})


def load_wheel_lock(root):
    root = Path(root)
    path = root/'locks/runtime-wheels.json'
    if path.stat().st_size > 1024*1024:
        raise ValueError('wheel_lock_invalid')
    data = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or set(data) != {'schema_version','python','platform','profiles','builds'}
            or type(data['schema_version']) is not int or data['schema_version'] != 1
            or data['python'] != PYTHON or data['platform'] != PLATFORM
            or not isinstance(data['profiles'], dict) or set(data['profiles']) != set(PROFILES)):
        raise ValueError('wheel_lock_invalid')
    profiles = {}
    for profile in PROFILES:
        pins = package_pins(root, profile)
        records = data['profiles'][profile]
        if not isinstance(records, list) or len(records) != len(pins):
            raise ValueError('wheel_package_mismatch')
        parsed = {}
        for item in records:
            if not isinstance(item, dict) or set(item) != set(Wheel.__dataclass_fields__):
                raise ValueError('wheel_lock_invalid')
            name = item['name']
            if not isinstance(name, str) or name != canonical_name(name) or name not in pins or item['version'] != pins[name] or name in parsed:
                raise ValueError('wheel_package_mismatch')
            file = item['file']
            if not isinstance(file, str) or '\\' in file or ':' in file or PurePosixPath(file).parts != (profile, PurePosixPath(file).name) or not file.endswith('.whl'):
                raise ValueError('wheel_lock_invalid')
            if (type(item['size']) is not int or not 0 < item['size'] <= 8*1024**3
                    or not isinstance(item['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', item['sha256'])
                    or item['origin'] != package_origin(name, item['version'])):
                raise ValueError('wheel_lock_invalid')
            parsed[name] = Wheel(**item)
        profiles[profile] = tuple(parsed[name] for name in sorted(parsed))
    sources={}
    for values in profiles.values():
        for item in values:
            if item.origin.endswith('-source'):
                if item.name in sources and sources[item.name] != item.version:
                    raise ValueError('wheel_build_provenance_invalid')
                sources[item.name]=item.version
    if not isinstance(data['builds'],dict) or set(data['builds']) != set(sources):
        raise ValueError('wheel_build_provenance_invalid')
    for name,version in sources.items():
        build=data['builds'][name]
        base={'kind','version','archive_url','archive_sha256','build_tools','source_date_epoch'}
        expected=base|({'revision'} if name=='faster-qwen3-tts' else set())
        if (not isinstance(build,dict) or set(build) != expected or build['version'] != version
                or not isinstance(build['archive_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',build['archive_sha256'])
                or build['build_tools'] != dict(BUILD_TOOLS) or build['source_date_epoch'] != SOURCE_DATE_EPOCH):
            raise ValueError('wheel_build_provenance_invalid')
        if name=='faster-qwen3-tts':
            source=faster_qwen_source(root)
            if any(build[key] != value for key,value in source.items()):
                raise ValueError('wheel_build_provenance_invalid')
        elif (build['kind'] != 'pypi-sdist' or not isinstance(build['archive_url'],str)
                or not build['archive_url'].startswith('https://files.pythonhosted.org/packages/')
                or PurePosixPath(build['archive_url']).name != f'{name}-{version}.tar.gz'):
            raise ValueError('wheel_build_provenance_invalid')
    return WheelLock(profiles, data)


def validate_wheelhouse(house, lock, profiles=PROFILES, *, complete=True, require_manifest=False):
    house = Path(house).resolve()
    if require_manifest:
        metadata=house/'manifest.json'
        if metadata.stat().st_size>1024*1024 or json.loads(metadata.read_text(encoding='utf-8')) != lock.document:
            raise ValueError('wheel_manifest_mismatch')
    checked = []
    for profile in profiles:
        if profile not in lock.profiles:
            raise ValueError('unknown_engine')
        expected = {item.file for item in lock.profiles[profile]}
        actual = {f'{profile}/{path.name}' for path in (house/profile).glob('*.whl')}
        if actual-expected or complete and expected != actual:
            raise ValueError('wheelhouse_incomplete')
        for item in lock.profiles[profile]:
            path = (house/item.file).resolve()
            if not complete and not path.exists():
                continue
            if not path.is_relative_to(house) or path.stat().st_size != item.size or digest(path) != item.sha256:
                raise ValueError('wheel_integrity_conflict')
            if wheel_metadata(path) != (item.name, item.version):
                raise ValueError('wheel_package_mismatch')
            checked.append(item)
    return tuple(checked)


def write_requirements(house, lock, profile, destination):
    records = validate_wheelhouse(house, lock, (profile,))
    lines = [f'{(Path(house)/item.file).resolve().as_uri()} --hash=sha256:{item.sha256}' for item in records]
    content='\n'.join(lines)+'\n'
    destination=Path(destination)
    if not destination.exists() or destination.read_text(encoding='utf-8') != content:
        destination.write_text(content, encoding='utf-8')
