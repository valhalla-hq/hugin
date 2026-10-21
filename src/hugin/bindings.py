"""The versioned desktop profile owns dispatch and its visible hints."""
from dataclasses import dataclass

PROFILE = 'mouse-back-dictation-v1'


@dataclass(frozen=True)
class Binding:
    action: str
    identity: int
    key: str
    mouse: int
    label: str
    control: bool

    @property
    def shortcut(self):
        return ('Strg+' if self.control else '')+'Alt+'+self.key

    def hint(self, pilot=False):
        prefix = '' if pilot else self.label+' · '
        suffix = ' · erneut: fertig' if self.action == 'dictation' else ' · erneut: Stopp'
        return prefix+self.shortcut+(suffix if pilot else suffix.replace(' · ', '\n', 1))


DICTATION = Binding('dictation', 1, 'Y', 1, 'Maus zurück',False)
READING = Binding('read', 2, 'V', 2, 'Maus vorwärts',True)
BINDINGS = (DICTATION, READING)
