"""Closed raster clipboard policy; OLE transport is never copied as payload."""
import json

POLICY_FORMATS=('CanUploadToCloudClipboard','CanIncludeInClipboardHistory',
                'ExcludeClipboardContentFromMonitorProcessing')
OLE_FORMATS=('DataObject','Ole Private Data')
RASTER_FORMATS=('PNG',*POLICY_FORMATS,*OLE_FORMATS)
PROOF_LIMIT=2048


def format_ids(values):
    if (not isinstance(values,(list,tuple)) or not 0<len(values)<=256
            or any(type(value) is not int or not 0<value<=65535 for value in values)
            or len(set(values))!=len(values)):
        raise ValueError('invalid clipboard formats')
    return tuple(values)


def raster_candidate(identities,names):
    ids=set(format_ids(identities));metadata={names[name] for name in OLE_FORMATS}
    permitted={2,8,17,names['PNG'],*(names[name] for name in POLICY_FORMATS)}
    if (not metadata<=ids or names['PNG'] not in ids or not ids&{8,17}
            or not ids<=permitted|metadata):
        raise ValueError('unsupported OLE clipboard bundle')
    return tuple(identity for identity in identities if identity not in metadata|{2})


def raster_plan(identities,names,descriptors):
    retained=raster_candidate(identities,names)
    if not isinstance(descriptors,(tuple,list)) or not 0<len(descriptors)<=256:
        raise ValueError('incomplete OLE formats')
    declared=set()
    for item in descriptors:
        if not isinstance(item,(tuple,list)) or len(item)!=5:
            raise ValueError('invalid OLE format')
        identity,aspect,index,medium,device=item
        if (any(type(value) is not int for value in item[:4]) or type(device) is not bool
                or identity not in identities or identity in declared
                or aspect!=1 or index!=-1 or device):
            raise ValueError('unsupported OLE format')
        expected={16} if identity==2 else {1,4,5} if identity==names['PNG'] else {1}
        if identity not in set(retained)|{2} or medium not in expected:
            raise ValueError('unsupported OLE medium')
        declared.add(identity)
    # DIB/DIBV5/bitmap can be synthesized by Windows. All other retained
    # formats must actually be declared, and an OLE raster source must exist.
    if not set(retained)-{8,17}<=declared or not declared&{2,8,17}:
        raise ValueError('incomplete OLE payload coverage')
    return retained


def decode_proof(data):
    if not isinstance(data,bytes) or not 0<len(data)<=PROOF_LIMIT:
        raise ValueError('invalid clipboard proof size')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('duplicate proof key')
            result[key]=value
        return result
    try:proof=json.loads(data,object_pairs_hook=unique)
    except (UnicodeError,json.JSONDecodeError):raise ValueError('invalid clipboard proof') from None
    if not isinstance(proof,dict) or set(proof)!={'sequence','formats'}:
        raise ValueError('invalid clipboard proof shape')
    sequence=proof['sequence']
    if type(sequence) is not int or not 0<sequence<1<<32:
        raise ValueError('invalid clipboard sequence')
    return sequence,format_ids(proof['formats'])


class ClipboardFormatProbe:
    """One bounded, owned metadata process; retained on failed cleanup."""
    def __init__(self,*,spawn=None,timeout=2.0):
        if not 0<timeout<=5:raise ValueError('invalid clipboard probe timeout')
        self.spawn=spawn;self.timeout=timeout;self._process=None

    def read(self):
        from pathlib import Path
        import subprocess
        import sys
        from .clipboard import ClipboardFailure
        from .process import OwnedProcess
        if self._process is not None:raise ClipboardFailure('clipboard_cleanup_failed')
        executable=Path(sys.executable)
        if executable.name.lower()=='pythonw.exe':executable=executable.with_name('python.exe')
        try:
            try:
                self._process=(self.spawn or OwnedProcess)([str(executable),'-I','-S','-B',
                    str(Path(__file__).with_name('clipboard_formats_probe.py'))],
                    stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                    close_fds=True,creationflags=0x08000000,memory_limit=256*1024*1024)
            except Exception as error:
                self._process=getattr(error,'owner',None)
                raise ClipboardFailure('clipboard_failed') from None
            # The producer emits <=2048 bytes, below the anonymous pipe's
            # capacity. Wait for the whole owned family before reading EOF.
            code=self._process.wait(timeout=self.timeout)
            if code==3:raise ClipboardFailure('format_unsupported')
            if code!=0:raise ClipboardFailure('clipboard_failed')
            return decode_proof(self._process.stdout.read(PROOF_LIMIT+1))
        except ClipboardFailure:raise
        except subprocess.TimeoutExpired:raise ClipboardFailure('clipboard_busy') from None
        except Exception:raise ClipboardFailure('clipboard_failed') from None
        finally:self.close()

    def close(self):
        from .clipboard import ClipboardFailure
        owner=self._process
        if owner is None:return
        try:
            if owner.poll() is None:owner.kill();owner.wait(timeout=3)
            owner.close()
        except Exception:raise ClipboardFailure('clipboard_cleanup_failed') from None
        self._process=None
