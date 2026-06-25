"""Einstiegspunkt. Funktioniert als Modul (python3 -m finanzplanung)
und bei direktem Aufruf des Verzeichnisses (python3 finanzplanung)."""

if __package__ in (None, ""):
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from finanzplanung.cli import main
else:
    from .cli import main

if __name__ == "__main__":
    main()
