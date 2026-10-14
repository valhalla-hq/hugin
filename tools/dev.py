"""Small explicit developer entry point; absent coverage is never a green test."""
from pathlib import Path
import argparse
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def docs():
    folder = ROOT / 'specs/2026-10-14-hugin-v1'
    spec = (folder / 'spec.md').read_text(encoding='utf-8')
    req = re.findall(r'^\| ((?:REQ|NFR|SEC|OPS)-\d{3}) \|',spec,re.M)
    ac = re.findall(r'^\| (AC-\d{3}) \|',spec,re.M)
    covered = {item for line in spec.splitlines() if line.startswith('| AC-')
        for item in re.findall(r'(?:REQ|NFR|SEC|OPS)-\d{3}',line)}
    problems = []
    if len(req) != len(set(req)) or len(ac) != len(set(ac)) or set(req)-covered:
        problems.append('requirement_coverage')
    for path in [ROOT/'README.md',*folder.glob('*.md')]:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('http://','https://','#')) or re.match(r'^/?[A-Za-z]:/',link):
                continue
            if not (path.parent/link.split('#')[0]).exists():
                problems.append(str(path.relative_to(ROOT))+':'+link)
    from hugin.config import load_settings,verify_voice_assets
    verify_voice_assets(load_settings(ROOT))
    for name in ('stt-model.json','tts-model.json'):
        lock = json.loads((ROOT/'locks'/name).read_text(encoding='utf-8'))
        if not re.fullmatch('[0-9a-f]{40}',lock['revision']):
            problems.append(name+':revision')
        for item in lock['files']:
            if not re.fullmatch('[0-9a-f]{64}',item['sha256']) or type(item['size']) is not int or item['size'] <= 0:
                problems.append(name+':file')
    print(json.dumps({'requirements':len(req),'acceptance_criteria':len(ac),'problems':problems}))
    return 1 if problems else 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command',required=True)
    check = sub.add_parser('check')
    check.add_argument('--docs',action='store_true')
    check.add_argument('--group',choices=('contracts','integration','windows','all'),default='contracts')
    check.add_argument('--interactive',action='store_true')
    bench = sub.add_parser('benchmark')
    bench.add_argument('--scenario',default='baseline-and-hugin')
    bench.add_argument('--cold-warm',action='store_true')
    args = parser.parse_args()
    if args.command == 'benchmark':
        print('Benchmark harness is not implemented yet.',file=sys.stderr)
        return 2
    if args.docs:
        return docs()
    if args.group == 'windows' and not args.interactive:
        print('Native tests require --interactive and an isolated test target.',file=sys.stderr)
        return 2
    if args.interactive:
        import os
        os.environ['HUGIN_INTERACTIVE_TESTS'] = '1'
    suite = unittest.TestSuite()
    groups = ('contracts','integration') if args.group == 'all' else (args.group,)
    for group in groups:
        discovered = unittest.defaultTestLoader.discover(str(ROOT/'tests'/group))
        if not discovered.countTestCases():
            print('No coverage for group: '+group,file=sys.stderr)
            return 2
        suite.addTests(discovered)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
