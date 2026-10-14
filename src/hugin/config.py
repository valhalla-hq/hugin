"""Parse configuration once and bind portable, owned asset identities."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tomllib
from types import MappingProxyType
from typing import Mapping

from .errors import HuginError


@dataclass(frozen=True)
class Voice:
    id: str
    name: str
    source_id: str
    reference: Path
    reference_text: Path
    hashes: Mapping[str, str]


@dataclass(frozen=True)
class Settings:
    root: Path
    default_voice: str
    language: str
    paths: Mapping[str, Path]
    limits: Mapping[str, int]
    stt: Mapping[str, object]
    voices: Mapping[str, Voice]


def read_config_text(path: Path, limit=65536) -> str:
    try:
        with path.open('rb') as source: data=source.read(limit+1)
        if len(data)>limit: raise ValueError
        return data.decode('utf-8')
    except (OSError,ValueError,UnicodeError):
        raise HuginError('config_invalid','configuration') from None


def read_json_object(path: Path, limit=65536) -> dict:
    def reject_constant(_): raise ValueError
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError
            result[key]=value
        return result
    try:
        value=json.loads(read_config_text(path,limit),object_pairs_hook=unique,
            parse_constant=reject_constant)
        if not isinstance(value,dict): raise ValueError
        return value
    except (ValueError,TypeError,RecursionError):
        raise HuginError('config_invalid','configuration') from None


def _keys(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise HuginError('config_invalid', 'configuration')


def _owned_path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise HuginError('config_invalid', 'configuration')
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root) or candidate == root:
        raise HuginError('config_invalid', 'configuration')
    return candidate


def load_settings(root: Path) -> Settings:
    root = root.resolve()
    try:
        data = tomllib.loads(read_config_text(root/'config/hugin.toml'))
        _keys(data, ('schema_version', 'default_voice', 'language', 'paths', 'limits', 'stt'))
        if type(data['schema_version']) is not int or data['schema_version'] != 1:
            raise HuginError('config_invalid', 'configuration')
        _keys(data['paths'], ('stt_model', 'tts_model', 'state'))
        paths = {key: _owned_path(root, value) for key, value in data['paths'].items()}
        _keys(data['limits'], ('capture_bytes','frame_bytes','control_bytes','transcript_bytes',
            'selection_bytes','clipboard_bytes','audio_buffer_ms','result_ttl_seconds',
            'cancel_seconds','exit_seconds','ready_seconds'))
        limits = data['limits']
        if any(type(value) is not int or not 0 < value <= 64 * 1024 * 1024 for value in limits.values()):
            raise HuginError('config_invalid', 'configuration')
        if limits['capture_bytes'] % 2 or limits['frame_bytes'] > 65536 or limits['control_bytes'] > 65536:
            raise HuginError('config_invalid', 'configuration')
        if limits['transcript_bytes'] > 262144 or limits['selection_bytes'] > 262144:
            raise HuginError('config_invalid', 'configuration')
        if limits['audio_buffer_ms'] > 250 or limits['clipboard_bytes'] > 33554432:
            raise HuginError('config_invalid', 'configuration')
        _keys(data['stt'], ('device', 'compute_type', 'cpu_threads', 'idle_unload_seconds'))
        stt = data['stt']
        if stt['device'] not in ('cuda','cpu') or stt['compute_type'] not in ('int8_float16','int8'):
            raise HuginError('config_invalid', 'configuration')
        if any(type(stt[key]) is not int or not 0 < stt[key] <= 3600 for key in ('cpu_threads','idle_unload_seconds')):
            raise HuginError('config_invalid', 'configuration')
        manifest = read_json_object(root/'config/voices.json')
        _keys(manifest, ('schema_version', 'voices'))
        if type(manifest['schema_version']) is not int or manifest['schema_version'] != 1 or set(manifest['voices']) != {'freya','tyr'}:
            raise HuginError('config_invalid', 'configuration')
        voices = {}
        for key, item in manifest['voices'].items():
            _keys(item, ('name','source_id','reference','reference_text','files'))
            if item['source_id'] != {'freya':'deutsch-3','tyr':'deutsch-a'}[key]:
                raise HuginError('config_invalid', 'configuration')
            if item['name'] != {'freya':'Freya','tyr':'Tyr'}[key]:
                raise HuginError('config_invalid', 'configuration')
            directory = 'assets/voices/'+item['source_id']+'/'
            if item['reference'] != directory+'referenz.wav' or item['reference_text'] != directory+'referenz.txt':
                raise HuginError('config_invalid', 'configuration')
            hashes = item['files']
            if not isinstance(hashes, dict) or set(hashes) != {'referenz.wav','referenz.txt','bestaetigte-hoerprobe.wav'}:
                raise HuginError('config_invalid', 'configuration')
            for filename, digest in hashes.items():
                if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                    raise HuginError('config_invalid', 'configuration')
            voices[key] = Voice(key,item['name'],item['source_id'],_owned_path(root,item['reference']),
                _owned_path(root,item['reference_text']),MappingProxyType(hashes))
        if data['default_voice'] not in voices or data['language'] not in ('German','English'):
            raise HuginError('config_invalid', 'configuration')
        return Settings(root,data['default_voice'],data['language'],MappingProxyType(paths),
            MappingProxyType(limits),MappingProxyType(stt),MappingProxyType(voices))
    except HuginError:
        raise
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        raise HuginError('config_invalid', 'configuration') from None


def verify_voice_assets(settings: Settings) -> None:
    for voice in settings.voices.values():
        for name, expected in voice.hashes.items():
            path = voice.reference.parent / name
            try:
                with path.open('rb') as source:
                    actual = hashlib.file_digest(source,'sha256').hexdigest()
                if not path.resolve().is_relative_to(settings.root) or actual != expected:
                    raise HuginError('asset_integrity', 'voices')
            except OSError:
                raise HuginError('asset_integrity', 'voices') from None
