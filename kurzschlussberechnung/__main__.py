"""Einstiegspunkt.

Funktioniert als Modul (`python3 -m kurzschlussberechnung`) und bei direktem
Aufruf des Verzeichnisses (`python3 kurzschlussberechnung`) -> Alias-tauglich.
"""

if __package__ in (None, ""):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from kurzschlussberechnung.cli import main
else:
    from .cli import main


if __name__ == "__main__":
    main()
