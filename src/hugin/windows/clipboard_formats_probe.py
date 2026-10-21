"""Isolated OLE format metadata only: no GetData, input or clipboard writes."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import json
import sys

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from hugin.windows.clipboard_formats import raster_plan,PROOF_LIMIT


class FormatEtc(C.Structure):
    _fields_=[('format',W.WORD),('device',C.c_void_p),('aspect',W.DWORD),
              ('index',W.LONG),('medium',W.DWORD)]


def ole_formats():
    ole=C.WinDLL('ole32')
    ole.OleInitialize.argtypes=[C.c_void_p];ole.OleInitialize.restype=W.LONG
    ole.OleUninitialize.argtypes=[];ole.OleUninitialize.restype=None
    ole.OleGetClipboard.argtypes=[C.POINTER(C.c_void_p)];ole.OleGetClipboard.restype=W.LONG
    ole.CoTaskMemFree.argtypes=[C.c_void_p];ole.CoTaskMemFree.restype=None
    def method(pointer,index,result,*args):
        table=C.cast(pointer,C.POINTER(C.POINTER(C.c_void_p))).contents
        return C.WINFUNCTYPE(result,C.c_void_p,*args)(table[index])
    obj=C.c_void_p();enum=C.c_void_p();records=[]
    if ole.OleInitialize(None) not in (0,1):raise RuntimeError('OLE unavailable')
    try:
        if ole.OleGetClipboard(C.byref(obj))!=0 or not obj:
            raise RuntimeError('OLE clipboard unavailable')
        if method(obj,8,W.LONG,W.DWORD,C.POINTER(C.c_void_p))(obj,1,C.byref(enum))!=0 or not enum:
            raise RuntimeError('OLE enumeration unavailable')
        for _ in range(257):
            fmt=FormatEtc();count=W.ULONG()
            hr=method(enum,3,W.LONG,W.ULONG,C.POINTER(FormatEtc),C.POINTER(W.ULONG))(
                enum,1,C.byref(fmt),C.byref(count))
            try:
                if hr==1 and count.value==0:return tuple(records)
                if hr!=0 or count.value!=1 or len(records)>=256:
                    raise ValueError('incomplete OLE enumeration')
                records.append((fmt.format,fmt.aspect,fmt.index,fmt.medium,bool(fmt.device)))
            finally:
                if fmt.device:ole.CoTaskMemFree(fmt.device)
        raise ValueError('OLE enumeration capacity')
    finally:
        for pointer in (enum,obj):
            if pointer:method(pointer,2,W.ULONG)(pointer)
        ole.OleUninitialize()


def inspect(backend,enumerate_ole=ole_formats):
    with backend._opened():
        sequence=backend.sequence();identities=backend._format_ids()
    descriptors=enumerate_ole()
    raster_plan(identities,backend.registered,descriptors)
    with backend._opened():
        if backend.sequence()!=sequence or backend._format_ids()!=identities:
            raise RuntimeError('clipboard changed during proof')
    return dict(sequence=sequence,formats=identities)


def main():
    if sys.platform!='win32':return 2
    from hugin.windows.clipboard import NativeClipboard
    backend=None
    try:
        backend=NativeClipboard()
        result=inspect(backend)
        encoded=json.dumps(result,separators=(',',':')).encode('ascii')
        if len(encoded)>PROOF_LIMIT:raise ValueError('proof capacity')
        sys.stdout.buffer.write(encoded);sys.stdout.buffer.flush()
        return 0
    except ValueError:return 3
    except Exception:return 2
    finally:
        if backend is not None:backend.close()


if __name__=='__main__':raise SystemExit(main())
