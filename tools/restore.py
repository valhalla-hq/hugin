"""Read-only restore planner. Apply is introduced only with a tested restorer."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    if args.apply:
        print('Restore apply is not implemented; no changes made.',file=sys.stderr)
        return 2
    models = {kind:json.loads((ROOT/'locks'/filename).read_text(encoding='utf-8'))
        for kind,filename in (('stt','stt-model.json'),('tts','tts-model.json'))}
    print(json.dumps({'mode':'plan','target':str(args.target.resolve()),'target_exists':args.target.exists(),
        'writes':False,'downloads':False,'models':{key:{'revision':value['revision'],
        'files':len(value['files']),'bytes':sum(item['size'] for item in value['files'])}
        for key,value in models.items()}},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
