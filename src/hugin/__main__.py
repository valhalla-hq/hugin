from pathlib import Path
import argparse
import sys

from .config import load_settings,verify_voice_assets
from .errors import HuginError


def main():
    parser = argparse.ArgumentParser(prog='Hugin')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--preview',action='store_true',help='UI only; no input, mic or engine startup')
    parser.add_argument('--pilot',action='store_true',help='Alternative test hotkeys; mouse buttons remain untouched')
    parser.add_argument('--show',action='store_true')
    args = parser.parse_args()
    try:
        settings = load_settings(args.root)
        verify_voice_assets(settings)
        if args.preview:
            from .ui import HuginWindow,View
            from dataclasses import replace
            view = View(status='Entwicklungs-Vorschau',detail='Eingaben und Sprachverarbeitung sind deaktiviert.',
                voice=settings.default_voice,components='Whispering und PipPal bleiben verfügbar.')

            def action(kind,value):
                nonlocal view
                if kind == 'voice':
                    view = replace(view,voice=value)
                    window.post(view)
                elif kind == 'quit':
                    window.request_stop()
                elif kind == 'diagnose':
                    view = replace(view,error='Die Vorschau startet keine Sprachkomponenten.')
                    window.post(view)

            window = HuginWindow(action)
            try:
                window.post(view)
                window.show()
                window.run()
                if window.failure: raise window.failure
                return 0
            finally: window.stop()
        if not args.pilot:
            # Productive hooks require the separately checked migration record.
            # Development launches cannot take the old stack's mouse bindings.
            raise HuginError('activation_pending','activation')
        from .application import Application
        return Application(settings,pilot=args.pilot,show=args.show).run()
    except HuginError as error:
        if sys.stderr is not None:
            print(error.message,file=sys.stderr)
        elif sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes
            dialog = ctypes.WinDLL('user32').MessageBoxW
            dialog.argtypes = [wintypes.HWND,wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.UINT]
            dialog.restype = ctypes.c_int
            dialog(None,error.message,'Hugin',0x10)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
