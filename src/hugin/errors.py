"""Expected failures carry codes; never format input or native exception payloads."""

MESSAGES = {
    'config_invalid': 'Die Hugin-Konfiguration ist ungültig.',
    'asset_integrity': 'Eine bestätigte Stimm- oder Modelldatei stimmt nicht überein.',
    'input_conflict': 'Eine Hugin-Taste ist bereits durch eine andere Anwendung belegt.',
    'input_failed': 'Die Windows-Eingabesteuerung ist nicht verfügbar.',
    'interface_failed': 'Das Hugin-Fenster konnte nicht vollständig gestartet oder beendet werden.',
    'audio_failed': 'Die Audioausgabe konnte nicht sicher gestoppt werden.',
    'microphone_failed': 'Das Mikrofon ist nicht verfügbar.',
    'capture_limit': 'Die Aufnahme hat ihr Speicherlimit erreicht.',
    'clipboard_failed': 'Die Zwischenablage ist nicht sicher verfügbar.',
    'target_changed': 'Das Einfügeziel hat sich geändert. Der Text kann kopiert werden.',
    'target_unverifiable': 'Das aktive Eingabefeld kann nicht sicher erkannt werden. Der Text kann kopiert werden.',
    'target_unverified': 'Automatisches Einfügen ist für dieses Programm noch nicht geprüft. Der Text kann kopiert werden.',
    'selection_empty': 'Kein kopierbarer Text ausgewählt.',
    'worker_failed': 'Eine lokale Sprachkomponente ist nicht verfügbar.',
    'worker_timeout': 'Eine lokale Sprachkomponente antwortet nicht rechtzeitig.',
    'protocol_invalid': 'Ungültige Daten einer lokalen Sprachkomponente.',
    'resource_limit': 'Eine Hugin-Ressourcengrenze wurde erreicht.',
    'unsupported': 'Diese Funktion ist in dieser Umgebung nicht verfügbar.',
    'activation_pending': 'Hugin ist noch im Pilotbetrieb. Die normalen Tasten werden nach der Abnahme aktiviert.',
}


class HuginError(Exception):
    def __init__(self, code: str, phase: str = 'unknown'):
        self.code = code if code in MESSAGES else 'worker_failed'
        self.phase = phase
        super().__init__(self.code)

    @property
    def message(self) -> str:
        return MESSAGES[self.code]
