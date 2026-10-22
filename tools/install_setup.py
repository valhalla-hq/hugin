"""Owned production activation/migration; startup never invokes this adapter."""
from pathlib import Path
import argparse
import json
import os
import sys
import uuid

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from hugin.config import load_settings,read_json_object
from hugin.bindings import PROFILE
from desktop_setup import DesktopSetup,native_shortcut,startup_folder,encoded,digest,file_hash,OLD_LINKS


def read_shortcut(path):
    import comtypes
    from comtypes.client import CreateObject
    comtypes.CoInitialize();shell=link=None
    try:
        shell=CreateObject('WScript.Shell',dynamic=True)
        link=shell.CreateShortcut(str(path))
        return {'target':link.TargetPath,'arguments':link.Arguments,'working_directory':link.WorkingDirectory}
    finally:
        link=shell=None;comtypes.CoUninitialize()


def preference(path):
    if not path.exists():return None
    value=read_json_object(path)
    if (set(value)!={'schema_version','voice'} or type(value['schema_version']) is not int
            or value['schema_version']!=1 or value['voice'] not in ('freya','tyr')):
        raise RuntimeError('preference_invalid')
    if path.resolve()!=path:raise RuntimeError('preference_redirected')
    return path.read_bytes()


def create_atomic(path,content):
    """Publish complete bytes without ever overwriting an intervening owner."""
    if path.resolve()!=path:raise RuntimeError('path_redirected')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name('.hugin-'+str(uuid.uuid4())+'.tmp')
    try:
        with temporary.open('xb') as output:output.write(content)
        os.link(temporary,path)
    finally:temporary.unlink(missing_ok=True)


class ProductionSetup:
    def __init__(self,root,startup,*,make_shortcut=native_shortcut,read_shortcut=read_shortcut):
        self.settings=load_settings(Path(root))
        self.root=self.settings.root;self.startup=Path(startup).resolve()
        self.make_shortcut=make_shortcut;self.read_shortcut=read_shortcut
        self.link=self.startup/'Hugin.lnk'
        self.preference=self.settings.paths['state']/'preferences.json'
        self.uninstalled=self.root/'.runtime/production-uninstalled.json'

    def desktop(self,replace=None):
        return DesktopSetup(self.root,self.settings.paths['state'],self.startup,
            make_shortcut=self.make_shortcut,entrypoint=self.root/'Hugin.exe',replace_shortcut_hash=replace)

    def _previous(self):
        """A matching name/path is insufficient: validate the producer's backup."""
        if not self.link.exists():return None,None
        try:
            observed=self.read_shortcut(self.link)
            root=Path(observed['working_directory']).resolve()
            if root==self.root:raise RuntimeError('unowned_existing_shortcut')
            settings=load_settings(root)
            entrypoint=root/'Hugin.exe' if observed['target']==str(root/'Hugin.exe') else None
            previous=DesktopSetup(root,settings.paths['state'],self.startup,entrypoint=entrypoint)
            record=previous._entries()
            observed_hash=file_hash(self.link)
            if observed!=previous.shortcut or observed_hash!=record['entries'][-1]['after']:
                raise RuntimeError('previous_shortcut_changed')
            return observed_hash,preference(settings.paths['state']/'preferences.json')
        except Exception as cause:
            raise RuntimeError('existing_shortcut_not_owned') from cause

    def _uninstall_record(self,entry):
        return dict(schema_version=1,root=str(self.root),shortcut_sha256=entry['after'])

    def _owned_uninstall(self,entry):
        return (self.uninstalled.exists() and self.uninstalled.resolve()==self.uninstalled
            and self.uninstalled.read_bytes()==encoded(self._uninstall_record(entry)))

    def _absent_link_backup(self,setup):
        receipt=read_json_object(self.uninstalled)
        if (set(receipt)!={'schema_version','root','shortcut_sha256'}
                or type(receipt['schema_version']) is not int or receipt['schema_version']!=1
                or receipt['root']!=str(self.root) or not isinstance(receipt['shortcut_sha256'],str)):
            raise RuntimeError('uninstall_receipt_changed')
        manifest=setup._entries(absent_shortcut_after=receipt['shortcut_sha256'])
        if not self._owned_uninstall(manifest['entries'][-1]):
            raise RuntimeError('uninstall_receipt_changed')
        return manifest

    def _migration_completion(self,plan_hash):
        return dict(schema_version=1,root=str(self.root),plan_sha256=plan_hash,status='completed')

    def _migration(self,plan_hash,voice=None):
        backup=self.root/'.runtime/production-migration-v1'
        if backup.resolve()!=backup:raise RuntimeError('migration_redirected')
        if backup.exists():
            complete=backup/'completed.json'
            if complete.exists():
                if complete.resolve()!=complete or complete.read_bytes()!=encoded(self._migration_completion(plan_hash)):
                    raise RuntimeError('migration_completion_changed')
                return None  # Historical backup is not an active preference source.
            content=preference(backup/'preferences.json')
            if content is None:raise RuntimeError('migration_incomplete')
            expected=dict(schema_version=1,root=str(self.root),plan_sha256=plan_hash,sha256=digest(content))
            if (backup/'manifest.json').read_bytes()!=encoded(expected):
                raise RuntimeError('migration_changed')
            return content
        if voice is None:return None
        stage=backup.with_name('production-migration-prepare-'+str(uuid.uuid4()))
        stage.mkdir(parents=True,exist_ok=False)
        (stage/'preferences.json').write_bytes(voice)
        (stage/'manifest.json').write_bytes(encoded(dict(schema_version=1,root=str(self.root),plan_sha256=plan_hash,sha256=digest(voice))))
        stage.rename(backup)  # Publish complete recovery before active setup writes.
        return voice

    def apply(self):
        preference(self.preference)  # Refuse malformed/redirected state before writes.
        setup=self.desktop();voice=None
        if setup.backup.exists():
            # A prior owned uninstall explicitly permits recreating its absent link.
            if self.uninstalled.exists() and not self.link.exists():
                manifest=self._absent_link_backup(setup)
                voice=self._migration(manifest['plan_sha256'])
                data=(setup.backup/'after-3.bin').read_bytes()
                create_atomic(self.link,data)
            else:
                manifest=setup._entries()
                voice=self._migration(manifest['plan_sha256'])
            plan_hash=manifest['plan_sha256']
        else:
            if any((self.startup/name).exists() for name in OLD_LINKS):
                raise RuntimeError('legacy_startup_not_owned')
            replacement,voice=self._previous()
            setup=self.desktop(replacement)
            plan_hash=setup.plan()['plan_sha256']
            voice=self._migration(plan_hash,voice)
        setup.apply(plan_hash)
        if voice is not None and not self.preference.exists():
            create_atomic(self.preference,voice)
        observed=self.read_shortcut(self.link)
        if observed!=setup.shortcut:raise RuntimeError('shortcut_readback_failed')
        migration=self.root/'.runtime/production-migration-v1'
        complete=migration/'completed.json'
        if migration.exists() and not complete.exists():
            create_atomic(complete,encoded(self._migration_completion(plan_hash)))
        return {'status':'installed','shortcut':observed,'preference_preserved':True,
                'input_profile':PROFILE,'backup':str(setup.backup)}

    def uninstall(self):
        setup=self.desktop()
        if setup.backup.resolve()!=setup.backup:raise RuntimeError('backup_redirected')
        if not setup.backup.exists():
            # DesktopSetup publishes a complete backup before its first active
            # write. Failed preparation grants no authority over Startup links;
            # payload ownership is separately proved by the native installer.
            return {'status':'uninstalled','preferences_retained':True,'activation_never_published':True}
        if not self.link.exists() and self.uninstalled.exists():
            self._absent_link_backup(setup)
            return {'status':'uninstalled','preferences_retained':True}
        manifest=setup._entries();entry=manifest['entries'][-1]
        if entry['before'] is not None and file_hash(self.link)==entry['before']:
            return {'status':'uninstalled','preferences_retained':True,'prior_startup_owner_preserved':True}
        if file_hash(self.link)!=entry['after']:raise RuntimeError('shortcut_not_owned')
        content=encoded(self._uninstall_record(entry))
        if self.uninstalled.exists():
            if self.uninstalled.read_bytes()!=content:raise RuntimeError('uninstall_receipt_changed')
        else:create_atomic(self.uninstalled,content)
        if file_hash(self.link)!=entry['after']:raise RuntimeError('shortcut_changed')
        self.link.unlink()  # Only the exactly proven installed link; no old-app return.
        return {'status':'uninstalled','preferences_retained':True}

    def restore_previous(self):
        # Recreate an explicitly owned absent link if necessary, then use the
        # original transaction's validated byte-for-byte restore semantics.
        self.apply()
        return self.desktop().restore()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    choice=parser.add_mutually_exclusive_group()
    choice.add_argument('--uninstall',action='store_true')
    choice.add_argument('--restore-previous',action='store_true')
    args=parser.parse_args()
    from production_package import verify_release
    if not args.uninstall:verify_release(args.root)
    setup=ProductionSetup(args.root,startup_folder())
    result=(setup.uninstall() if args.uninstall else setup.restore_previous()
        if args.restore_previous else setup.apply())
    print(json.dumps(result))
    return 0


if __name__=='__main__':raise SystemExit(main())
