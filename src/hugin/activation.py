"""Explicit setup enables desktop inputs; application startup never writes it."""
from .bindings import PROFILE
from .config import read_json_object
from .errors import HuginError


def activation_record():
    return {'schema_version': 1, 'input_profile': PROFILE}


def require_activation(state):
    try:
        record = read_json_object(state/'activation.json')
    except (HuginError, OSError) as error:
        raise HuginError('activation_pending', 'activation') from error
    if (type(record.get('schema_version')) is not int or record != activation_record()):
        raise HuginError('activation_pending', 'activation')
