"""Explicit current-user startup migration. Default is a read-only plan.

Run only after Hugin and the old input owners have exited normally. Recovery
retains exact original files; no process control, registry edits or app relaunch.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from hugin.activation import activation_record
from hugin.config import load_settings, read_json_object

OLD_LINKS = ('PipPal.lnk', 'Whispering Local STT.lnk')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)+'\n').encode('utf-8')


def file_hash(path):
    if path.resolve() != path:
        raise RuntimeError('path_redirected')
    return digest(path.read_bytes()) if path.exists() else None


def startup_folder():
    import ctypes
    from ctypes import wintypes as W
    shell = ctypes.WinDLL('shell32')
    get_folder = shell.SHGetFolderPathW
    get_folder.argtypes = [W.HWND, ctypes.c_int, W.HANDLE, W.DWORD, W.LPWSTR]
    get_folder.restype = ctypes.c_long
    buffer = ctypes.create_unicode_buffer(260)
    if get_folder(None, 7, None, 0, buffer) != 0:  # CSIDL_STARTUP, current user
        raise RuntimeError('startup_unavailable')
    return Path(buffer.value).resolve()


def native_shortcut(path, spec):
    import comtypes
    from comtypes.client import CreateObject
    comtypes.CoInitialize()
    shell = link = None
    try:
        shell = CreateObject('WScript.Shell', dynamic=True)
        link = shell.CreateShortcut(str(path))
        link.TargetPath = spec['target']
        link.Arguments = spec['arguments']
        link.WorkingDirectory = spec['working_directory']
        link.Description = 'Hugin – lokales Diktieren und Vorlesen'
        link.Save()
        link = shell.CreateShortcut(str(path))
        observed = {'target':link.TargetPath, 'arguments':link.Arguments,
                    'working_directory':link.WorkingDirectory}
        if observed != spec:
            raise RuntimeError('shortcut_readback_failed')
    finally:
        link = shell = None
        comtypes.CoUninitialize()


class DesktopSetup:
    def __init__(self, root, state, startup, *, make_shortcut=native_shortcut):
        self.root = Path(root).resolve()
        self.state = Path(state).resolve()
        self.startup = Path(startup).resolve()
        if not self.state.is_relative_to(self.root) or self.state == self.root:
            raise RuntimeError('state_outside_installation')
        self.backup = self.root/'.runtime/desktop-setup-v1'
        self.make_shortcut = make_shortcut
        self.targets = (self.state/'activation.json',
                        *(self.startup/name for name in OLD_LINKS), self.startup/'Hugin.lnk')
        python = self.root/'.runtime/controller/Scripts/pythonw.exe'
        launch = self.root/'tools/launch.py'
        if not python.is_file() or not launch.is_file():
            raise RuntimeError('installation_missing')
        self.shortcut = {'target':str(python),
                         'arguments':subprocess.list2cmdline([str(launch), '--root', str(self.root)]),
                         'working_directory':str(self.root)}

    def plan(self):
        # This method neither creates a shortcut nor materializes a backup.
        value = {'schema_version':1, 'root':str(self.root), 'startup':str(self.startup),
                 'activation':activation_record(), 'shortcut':self.shortcut,
                 'targets':[{'path':str(path), 'sha256':file_hash(path)} for path in self.targets],
                 'backup':str(self.backup)}
        return dict(value, plan_sha256=digest(encoded(value)))

    def _prepare(self, expected):
        plan = self.plan()
        if plan['plan_sha256'] != expected:
            raise RuntimeError('plan_changed')
        if self.targets[-1].exists():
            raise RuntimeError('existing_hugin_shortcut')
        if self.backup.resolve() != self.backup:
            raise RuntimeError('backup_redirected')
        staging = self.backup.with_name('desktop-prepare-'+str(uuid.uuid4()))
        if staging.resolve() != staging:
            raise RuntimeError('backup_redirected')
        staging.mkdir(parents=True, exist_ok=False)
        after = [encoded(activation_record()), None, None, None]
        stage = staging/'Hugin.lnk'
        self.make_shortcut(stage, self.shortcut)
        after[-1] = stage.read_bytes()
        entries = []
        for index, path in enumerate(self.targets):
            before = path.read_bytes() if path.exists() else None
            if (digest(before) if before is not None else None) != plan['targets'][index]['sha256']:
                raise RuntimeError('target_changed_during_backup')
            entry = {'path':str(path)}
            for direction, content in (('before', before), ('after', after[index])):
                entry[direction] = None if content is None else digest(content)
                if content is not None:
                    (staging/f'{direction}-{index}.bin').write_bytes(content)
            entries.append(entry)
        manifest = {'schema_version':1, 'plan_sha256':expected, 'entries':entries}
        # Publish complete recovery before touching any active file.
        with (staging/'manifest.json').open('xb') as output:
            output.write(encoded(manifest))
        self._entries(staging)
        # A failed preparation leaves only its unique staging directory. A
        # retry can prepare afresh; it never adopts/deletes that partial backup.
        if (staging.resolve() != staging or self.backup.resolve() != self.backup
                or staging.parent != self.root/'.runtime'
                or self.backup.parent != staging.parent or self.backup.exists()):
            raise RuntimeError('backup_changed')
        staging.rename(self.backup)

    def _entries(self, backup=None):
        backup = self.backup if backup is None else backup
        if backup.resolve() != backup:
            raise RuntimeError('backup_redirected')
        manifest = read_json_object(backup/'manifest.json')
        if (set(manifest) != {'schema_version','plan_sha256','entries'}
                or type(manifest['schema_version']) is not int or manifest['schema_version'] != 1
                or not isinstance(manifest['entries'], list) or len(manifest['entries']) != len(self.targets)):
            raise RuntimeError('invalid_manifest')
        for index, (entry, path) in enumerate(zip(manifest['entries'], self.targets)):
            if not isinstance(entry, dict) or set(entry) != {'path','before','after'} or entry['path'] != str(path):
                raise RuntimeError('invalid_manifest_path')
            for direction in ('before','after'):
                value = entry[direction]
                if value is not None:
                    if (not isinstance(value, str) or len(value) != 64
                            or file_hash(backup/f'{direction}-{index}.bin') != value):
                        raise RuntimeError('backup_changed')
            if file_hash(path) not in (entry['before'], entry['after']):
                raise RuntimeError('target_changed')
        # An older/foreign migration cannot silently activate a new profile.
        if (manifest['entries'][0]['after'] != digest(encoded(activation_record()))
                or any(manifest['entries'][i]['after'] is not None for i in (1,2))):
            raise RuntimeError('profile_changed')
        return manifest

    def _set_entry(self, entry, direction):
        path = Path(entry['path'])
        index = self.targets.index(path)
        current = file_hash(path)
        if current == entry[direction]:
            return
        if current not in (entry['before'], entry['after']):
            raise RuntimeError('target_changed')
        if entry[direction] is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            content = (self.backup/f'{direction}-{index}.bin').read_bytes()
            if digest(content) != entry[direction]:
                raise RuntimeError('backup_changed')
            temporary = path.with_name('.hugin-'+str(uuid.uuid4())+'.tmp')
            try:
                with temporary.open('xb') as output:output.write(content)
                if file_hash(path) != current:raise RuntimeError('target_changed')
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        if file_hash(path) != entry[direction]:
            raise RuntimeError('write_readback_failed')

    def apply(self, expected):
        if not self.backup.exists():
            self._prepare(expected)
        manifest = self._entries()
        if manifest['plan_sha256'] != expected:
            raise RuntimeError('plan_changed')
        for entry in manifest['entries']:
            self._set_entry(entry, 'after')
        return {'status':'applied', 'backup':str(self.backup), 'shortcut':self.shortcut}

    def restore(self):
        manifest = self._entries()  # Validate ALL targets/backups before any write.
        for entry in reversed(manifest['entries']):
            self._set_entry(entry, 'before')
        return {'status':'restored', 'backup':str(self.backup)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--apply', metavar='PLAN_SHA256')
    choice.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'win32':raise RuntimeError('windows_only')
    settings = load_settings(args.root)
    setup = DesktopSetup(settings.root, settings.paths['state'], startup_folder())
    result = setup.apply(args.apply) if args.apply else setup.restore() if args.restore else setup.plan()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':main()
