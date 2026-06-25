if __package__ in (None, ""):
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from revisionspruefung.cli import main
else:
    from .cli import main
if __name__ == "__main__":
    main()
