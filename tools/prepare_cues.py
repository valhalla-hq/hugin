"""Plan or add verified local Whispering PCM; never fetch or replace files."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import tempfile

SOURCE_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE_ROOT/'tools'))
sys.path.insert(0,str(SOURCE_ROOT/'src'))
from hugin.cues import ASSET_DIRECTORY,CUE_FILES,load_cue_signals
from prepare_engines import copy_locked

UPSTREAM='https://github.com/EpicenterHQ/epicenter/tree/a6b15c28db9076742d7ae7014f8ec9f97aa615d1/apps/whispering/src/lib/services/isomorphic/sound/assets'
ORIGINALS={
    'start':(8237,'45b05643beb6c208b5b2199fe16957eb793f1aac881a4416f7144d61df9918ff'),
    'end':(7993,'b1c008bf7f57d20b29f28c12b663dd60379874718d92ae2b78a6f1c16a72cae2'),
    'complete':(20906,'a8ee51dbd686f13d05898437943df493910664124f5c685086ffbb29359a8998'),
}
NOTICE=('Whispering 7.11.0 event sounds: manual-start, manual-stop, transcriptionComplete.\n'
    'Original creators: ZapSplat and Sound Ex Machina.\n'+UPSTREAM+'\n'
    'https://www.zapsplat.com/license-type/standard-license/\n'
    'Upstream repository license: AGPL-3.0. Third-party audio rights are separate;\n'
    'this local preparation does not establish rights to redistribute audio.\n'
    'Decoded with av 16.1.0 to mono PCM16/24kHz, no gain, trimming or repetition.\n')


def digest(data):return hashlib.sha256(data).hexdigest()


def decode(path,kind):
    import av
    if av.__version__!='16.1.0':raise ValueError('cue_decoder_version')
    size,expected=ORIGINALS[kind]
    with path.open('rb') as source:original=source.read(size+1)
    if len(original)!=size or digest(original)!=expected:raise ValueError('cue_original_mismatch')
    # Decode the verified bytes, not a second read of a replaceable path.
    import io
    pcm=bytearray()
    with av.open(io.BytesIO(original)) as source:
        stream=source.streams.audio[0]
        resampler=av.AudioResampler(format='s16',layout='mono',rate=24000)
        def append(frame):
            if len(pcm)+frame.samples*2>CUE_FILES[kind][0]:raise ValueError('cue_pcm_capacity')
            pcm.extend(frame.to_ndarray().tobytes())
        for frame in source.decode(stream):
            for converted in resampler.resample(frame):append(converted)
        for converted in resampler.resample(None):append(converted)
    if len(pcm)!=CUE_FILES[kind][0] or digest(pcm)!=CUE_FILES[kind][1]:
        raise ValueError('cue_pcm_mismatch')
    return bytes(pcm)


def prepare(root,source,apply=False):
    root=root.resolve();destination=(root/ASSET_DIRECTORY).resolve()
    if not destination.is_relative_to(root):raise ValueError('cue_destination_outside_root')
    payload={kind+'.pcm':decode(source/(kind+'.mp3'),kind) for kind in CUE_FILES}
    payload['NOTICE.txt']=NOTICE.encode('utf-8')
    plan=[]
    for name,data in payload.items():
        path=destination/name
        if path.exists():
            with path.open('rb') as existing:current=existing.read(len(data)+1)
            if current!=data:raise ValueError('cue_existing_mismatch')
            action='present'
        else:action='create'
        plan.append(dict(file=name,size=len(data),sha256=digest(data),action=action))
    if apply:
        destination.mkdir(parents=True,exist_ok=True)
        if destination.resolve()!=destination:raise ValueError('cue_destination_redirected')
        # Reuse the runtime asset producer: validated staging, same-directory
        # temporary copy, atomic hard-link create, never replace a final file.
        records=tuple({key:item[key] for key in ('file','size','sha256')} for item in plan)
        with tempfile.TemporaryDirectory(prefix='hugin-cues-') as temporary:
            staging=Path(temporary)
            for name,data in payload.items():(staging/name).write_bytes(data)
            copy_locked(staging,destination,None,records=records,allow_extra=True)
        load_cue_signals(root)
    return dict(status='prepared' if apply else 'planned',destination=str(destination),files=plan)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    print(json.dumps(prepare(args.root,args.source,args.apply)))
