"""Manually launch one checked Hugin pilot. Exit never starts other applications."""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid

SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE/'src'))
from hugin.windows.process import OwnedProcess

# Installation inputs are separate from the reviewed controller/UI checkout.
RUNTIME_INPUTS=('config','locks','assets','src/hugin/workers','src/hugin/protocol.py',
    'src/hugin/config.py','src/hugin/windows/process.py','src/hugin/windows/instance.py')


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],
        creationflags=0x08000000,text=True).strip()


def plan(root,head,runtime_head):
    if any(not re.fullmatch('[0-9a-f]{40}',value) for value in (head,runtime_head)):
        raise ValueError('invalid_head')
    root=Path(root).resolve()
    if git(SOURCE,'rev-parse','HEAD')!=head or git(SOURCE,'status','--porcelain'):
        raise RuntimeError('unchecked_checkout')
    if git(root,'rev-parse','HEAD')!=runtime_head or git(root,'status','--porcelain'):
        raise RuntimeError('runtime_checkout_changed')
    if git(SOURCE,'diff',runtime_head,head,'--',*RUNTIME_INPUTS):
        raise RuntimeError('runtime_inputs_changed')
    return dict(schema_version=1,checkout_head=head,source_root=str(SOURCE),
        runtime_root=str(root),runtime_head=runtime_head,worker_source_equal=True,
        pilot_hotkeys=['Ctrl+Alt+D','Ctrl+Alt+V'],old_stack_return='disabled',
        autostart_changes=False)


def run_owned(command,source,publish,*,factory=OwnedProcess):
    owner=None
    try:
        owner=factory(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,cwd=str(source))
        publish('pilot_running',app_pid=owner.pid)
        code=owner.wait()  # Held process and its complete owned Job family.
        owner.close()
        publish('session_exited',exit_code=code,own_family_exited=True,started_shortcuts=[])
        return code
    except BaseException as error:
        owner=owner or getattr(error,'owner',None)
        if owner is None:
            publish('creation_cleanup_unknown',own_family_exited=None,started_shortcuts=[])
            return 2
        while True:
            try:
                try:
                    # A failed constructor may own handles without a process.
                    # The owner, not a wait/PID assumption, decides closability.
                    owner.close()
                except BaseException:
                    try:
                        owner.kill()
                        owner.wait(timeout=7)
                    finally:owner.close()
                break
            except BaseException:
                publish('own_cleanup_pending',app_pid=owner.pid,started_shortcuts=[])
                # Keep the exact held owner alive even across repeated failures.
                time.sleep(1)
        publish('session_failed',own_family_exited=True,started_shortcuts=[])
        return 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--head',required=True)
    parser.add_argument('--runtime-head',required=True)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    report=plan(args.root,args.head,args.runtime_head)
    if not args.run:
        print(json.dumps(dict(report,status='planned',starts_app=False)),flush=True)
        return 0
    runtime=SOURCE/'.runtime'
    runtime.mkdir(exist_ok=True)
    if runtime.resolve()!=runtime:raise RuntimeError('runtime_redirected')
    path=runtime/('pilot-session-'+str(uuid.uuid4())+'.json')
    with path.open('x',encoding='utf-8') as output:json.dump(dict(report,status='launching'),output)
    def publish(status,**facts):
        temporary=runtime/('pilot-report-'+str(uuid.uuid4())+'.tmp')
        try:
            with temporary.open('x',encoding='utf-8') as output:
                json.dump(dict(report,status=status,supervisor_pid=os.getpid(),**facts),output,indent=2)
            os.replace(temporary,path)
        except OSError:pass  # Reporting must never prevent owned cleanup.
        finally:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass
    root=Path(report['runtime_root'])
    return run_owned([str(root/'.runtime/controller/Scripts/pythonw.exe'),
        str(SOURCE/'tools/launch.py'),'--root',str(root),'--pilot','--show'],SOURCE,publish)


if __name__=='__main__':raise SystemExit(main())
