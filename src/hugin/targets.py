"""Agent-maintained pilot approvals, separate from product controls."""
from dataclasses import dataclass
import math
from pathlib import Path

from .errors import HuginError
from .config import read_json_object


@dataclass(frozen=True)
class DeliveryApproval:
    control_class: str
    restore_delay_seconds: float
    package_family: str | None = None


@dataclass(frozen=True)
class VerifiedEditApproval:
    restore_delay_seconds: float


@dataclass(frozen=True)
class TargetApprovals:
    delivery: tuple[DeliveryApproval,...]
    capture_fallback: tuple[str,...]
    verified_edit: VerifiedEditApproval | None


def _proof(root, evidence):
    if not isinstance(evidence,str) or not evidence or Path(evidence).is_absolute():raise ValueError
    proof=(root/evidence).resolve()
    if not proof.is_relative_to(root.resolve()) or proof.suffix!='.md' or not proof.is_file():raise ValueError


def _delay(value):
    if type(value) not in (int,float) or not .02<=value<=2 or not math.isfinite(value):raise ValueError
    return float(value)


def load_target_approvals(root: Path) -> TargetApprovals:
    try:
        path=root/'config/targets.json'
        data=read_json_object(path)
        if not isinstance(data,dict) or set(data)!={'schema_version','delivery','capture_fallback','verified_edit'}:
            raise ValueError
        if type(data['schema_version']) is not int or data['schema_version']!=2: raise ValueError
        generic=data['verified_edit']
        if generic is not None:
            if not isinstance(generic,dict) or set(generic)!={'restore_delay_seconds','evidence'}:raise ValueError
            _proof(root,generic['evidence'])
            generic=VerifiedEditApproval(_delay(generic['restore_delay_seconds']))
        groups={}
        for kind in ('delivery','capture_fallback'):
            records=data[kind]
            if not isinstance(records,list) or len(records)>32: raise ValueError
            result=[];seen=set()
            for record in records:
                keys={'control_class','evidence'}|({'restore_delay_seconds'} if kind=='delivery' else set())
                if not isinstance(record,dict) or set(record) not in (
                        keys,keys|{'package_family'} if kind=='delivery' else keys):raise ValueError
                name=record['control_class'];evidence=record['evidence']
                if not isinstance(name,str) or not name or len(name)>256 or '\0' in name or '*' in name or name in seen:
                    raise ValueError
                seen.add(name)
                _proof(root,evidence)
                if kind=='delivery':
                    family=record.get('package_family')
                    if 'package_family' in record and (not isinstance(family,str)
                            or not 17<=len(family)<=64 or '\0' in family or '*' in family):raise ValueError
                    result.append(DeliveryApproval(name,_delay(record['restore_delay_seconds']),family))
                else: result.append(name)
            groups[kind]=tuple(result)
        return TargetApprovals(groups['delivery'],groups['capture_fallback'],generic)
    except (OSError,ValueError,TypeError,KeyError):
        raise HuginError('config_invalid','target_approvals') from None
