"""Version-one private pipe framing. Validate lengths before allocating bodies."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import struct
from typing import BinaryIO
import uuid

from .errors import HuginError

CONTROL_BYTES = 65536
FRAME_BYTES = 65536
TRANSCRIPT_BYTES = 262144
_HEADER = struct.Struct('!4sB16s16sQII')
_KINDS = {'pcm': 1, 'text': 2}


def invalid() -> HuginError:
    return HuginError('protocol_invalid', 'worker_protocol')


def _uuid(value: object) -> str:
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError
        return value
    except (ValueError, AttributeError):
        raise invalid() from None


@dataclass(frozen=True)
class Identity:
    engine_instance: str
    request_id: str
    generation: int

    def __post_init__(self):
        _uuid(self.engine_instance)
        _uuid(self.request_id)
        if type(self.generation) is not int or not 0 <= self.generation < 2**63:
            raise invalid()

    @classmethod
    def from_message(cls, message: dict) -> Identity:
        try:
            return cls(message['engine_instance'], message['request_id'], message['generation'])
        except (KeyError, TypeError):
            raise invalid() from None

    def fields(self) -> dict:
        return dict(engine_instance=self.engine_instance, request_id=self.request_id,
                    generation=self.generation)


@dataclass(frozen=True)
class Frame:
    kind: str
    identity: Identity
    offset: int
    data: bytes


def _read_exact(source: BinaryIO, size: int, *, eof: bool = False) -> bytes:
    result = bytearray()
    while len(result) < size:
        fragment = source.read(size - len(result))
        if not fragment:
            if eof and not result:
                raise EOFError
            raise invalid()
        result.extend(fragment)
    return bytes(result)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise invalid()
        result[key] = value
    return result


def _constant(_value):
    raise invalid()


def read_control(source: BinaryIO, limit: int = CONTROL_BYTES) -> dict:
    size = struct.unpack('!I', _read_exact(source, 4, eof=True))[0]
    if not 0 < size <= min(limit, CONTROL_BYTES):
        raise invalid()
    try:
        value = json.loads(_read_exact(source, size).decode('utf-8'),
                           object_pairs_hook=_object, parse_constant=_constant)
        if not isinstance(value, dict):
            raise invalid()
        return value
    except (UnicodeError, ValueError, RecursionError):
        raise invalid() from None


def write_control(target: BinaryIO, value: dict, limit: int = CONTROL_BYTES) -> None:
    try:
        raw = json.dumps(value, ensure_ascii=True, allow_nan=False,
                         separators=(',', ':')).encode('utf-8')
    except (ValueError, TypeError, RecursionError):
        raise invalid() from None
    if not isinstance(value, dict) or not 0 < len(raw) <= min(limit, CONTROL_BYTES):
        raise invalid()
    target.write(struct.pack('!I', len(raw)))
    target.write(raw)
    target.flush()


def _frame_fields(kind, offset, size):
    if kind not in _KINDS or type(offset) is not int or not 0 <= offset < 2**32:
        raise invalid()
    if not 0 < size <= FRAME_BYTES or offset + size >= 2**32:
        raise invalid()
    if kind == 'pcm' and (size % 2 or offset % 2):
        raise invalid()


def write_frame(target: BinaryIO, frame: Frame) -> None:
    if not isinstance(frame.data, bytes):
        raise invalid()
    _frame_fields(frame.kind, frame.offset, len(frame.data))
    target.write(_HEADER.pack(b'HUG1', _KINDS[frame.kind],
        uuid.UUID(frame.identity.engine_instance).bytes,
        uuid.UUID(frame.identity.request_id).bytes, frame.identity.generation,
        frame.offset, len(frame.data)))
    target.write(frame.data)
    target.flush()


def read_frame(source: BinaryIO) -> Frame:
    magic, kind, instance, request, generation, offset, size = _HEADER.unpack(
        _read_exact(source, _HEADER.size, eof=True))
    if magic != b'HUG1' or kind not in (1, 2):
        raise invalid()
    name = 'pcm' if kind == 1 else 'text'
    _frame_fields(name, offset, size)
    identity = Identity(str(uuid.UUID(bytes=instance)), str(uuid.UUID(bytes=request)), generation)
    return Frame(name, identity, offset, _read_exact(source, size))


def validate_digest(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise invalid()
    return value


class TranscriptReceiver:
    """One bounded draft; a result exists only after length/hash/UTF-8 checks."""
    def __init__(self, identity: Identity, length: int, digest: str,
                 limit: int = TRANSCRIPT_BYTES):
        if type(length) is not int or not 0 <= length <= min(limit, TRANSCRIPT_BYTES):
            raise invalid()
        self.identity = identity
        self.length = length
        self.digest = validate_digest(digest)
        self._draft = bytearray()
        self._active = True
        self.text = None

    def add(self, frame: Frame) -> None:
        if (not self._active or frame.kind != 'text' or frame.identity != self.identity
                or frame.offset != len(self._draft) or not frame.data
                or len(frame.data) > FRAME_BYTES or len(self._draft) + len(frame.data) > self.length):
            self.cancel()
            raise invalid()
        self._draft.extend(frame.data)

    def finish(self, length: int, digest: str) -> str:
        try:
            if (not self._active or type(length) is not int or length != self.length
                    or digest != self.digest or len(self._draft) != length
                    or hashlib.sha256(self._draft).hexdigest() != digest):
                raise invalid()
            value = self._draft.decode('utf-8')
        except UnicodeError:
            self.cancel()
            raise invalid() from None
        except HuginError:
            self.cancel()
            raise
        self._draft.clear()
        self._active = False
        self.text = value
        return value

    def cancel(self) -> None:
        self._active = False
        self._draft.clear()
        self.text = None
