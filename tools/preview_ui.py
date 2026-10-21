"""Synthetic UI preview only: no settings, input hooks, clipboard or engines."""
from pathlib import Path
import argparse
from dataclasses import replace
import math
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from hugin.ui import HuginWindow,View
from hugin.bindings import DICTATION,READING


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',choices=('idle','recording','processing','playing','complete','error'),default='idle')
    parser.add_argument('--cycle',action='store_true')
    parser.add_argument('--seconds',type=float,default=0,help='Close this preview automatically after N seconds')
    args=parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds<0:parser.error('seconds must be finite and nonnegative')
    labels={'idle':'Bereit für dein Diktat','recording':'Aufnahme läuft',
        'processing':'Diktat wird verarbeitet','playing':'Vorlesen läuft',
        'complete':'Bereit für dein Diktat','error':'Einfügen nicht möglich'}
    current=View(mode='Designvorschau',activity='idle',
        dictation_shortcut=DICTATION.hint(),reading_shortcut=READING.hint())
    def action(kind,value):
        nonlocal current
        if kind=='voice':current=replace(current,voice=value)
        elif kind=='quit':window.request_stop()
        elif kind=='clear':current=replace(current,text='')
        # Copy/diagnostics intentionally have no external side effects.
        window.post(current)
    window=HuginWindow(action,with_tray=False)
    window.root.title('Hugin · Designvorschau (synthetisch)')
    window.root.protocol('WM_DELETE_WINDOW',window.request_stop)
    started=time.monotonic();previous=None;receipt=0;deadline=0
    def update():
        nonlocal current,previous,receipt,deadline
        now=time.monotonic();elapsed=now-started
        if args.seconds and elapsed>=args.seconds:
            window.request_stop();return
        states=('idle','recording','processing','complete','playing','error')
        state=states[int(elapsed/4)%len(states)] if args.cycle else args.state
        if state!=previous:
            if state=='complete':receipt+=1;deadline=now+1.2
            else:deadline=0
            previous=state
        current=replace(current,status=labels[state],activity='idle' if state=='complete' else state,
            active_action='dictation' if state in ('recording','processing') else 'reading' if state=='playing' else '',
            audio_level=(.08+.25*math.sin(elapsed*3)**2) if state=='recording' else 0,
            completion_id=receipt,completion_until=deadline,
            error='Synthetische Vorschau: Das Zielfeld konnte nicht bestätigt werden.' if state=='error' else '',
            detail='Synthetische Zustände · keine Aufnahme oder Textübergabe')
        window.post(current)
        window.root.after(50,update)
    try:
        window.show();update();window.run()
        if window.failure:raise window.failure
    finally:window.stop()


if __name__=='__main__':main()
