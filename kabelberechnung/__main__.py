"""Einstiegspunkt.

Funktioniert sowohl als Modul (`python3 -m kabelberechnung`) als auch
bei direktem Aufruf des Verzeichnisses (`python3 kabelberechnung`).
"""

if __package__ in (None, ""):
    # direkt als Skript aufgerufen -> Paket-Wurzel auf den Pfad legen
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from kabelberechnung.cli import main
else:
    from .cli import main


if __name__ == "__main__":
    main()
