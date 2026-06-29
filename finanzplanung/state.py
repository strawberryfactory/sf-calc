"""
state.py — Persistente Planungsannahmen der Finanzplanung.

Liegt in ~/.config/finanzplanung/state.json. 'set' schreibt einzelne Annahmen,
'reset' setzt auf Defaults. calc-Flags übersteuern den Zustand pro Aufruf.
KEINE Kundendaten — nur Annahmen und das Normjahr.
"""

import json
from pathlib import Path

from . import tabellen as T

CONFIG_DIR = Path.home() / ".config" / "finanzplanung"
STATE_FILE = CONFIG_DIR / "state.json"

DEFAULTS = {
    "jahr": 2025,                                       # Normjahr (AHV/BVG/3a)
    "rendite": T.ANNAHMEN_DEFAULT["rendite"],           # Nettorendite p. a.
    "teuerung": T.ANNAHMEN_DEFAULT["teuerung"],         # Teuerung p. a.
    "lebenserwartung": T.ANNAHMEN_DEFAULT["lebenserwartung"],
    "ersatzquote": T.ANNAHMEN_DEFAULT["ersatzquote_ziel"],
}

PARAM_TYP = {
    "jahr": int, "rendite": float, "teuerung": float,
    "lebenserwartung": int, "ersatzquote": float,
}


class StateFehler(Exception):
    pass


def laden():
    cfg = dict(DEFAULTS)
    if STATE_FILE.exists():
        try:
            cfg.update(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def speichern(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def parse_wert(param, wert):
    if param not in PARAM_TYP:
        raise StateFehler(f"Unbekannte Annahme '{param}'. Gültig: {', '.join(PARAM_TYP)}.")
    try:
        return PARAM_TYP[param](wert)
    except ValueError:
        raise StateFehler(f"Wert '{wert}' passt nicht zu {param} ({PARAM_TYP[param].__name__}).")


def setzen(param, wert):
    cfg = laden()
    cfg[param] = parse_wert(param, str(wert))
    speichern(cfg)
    return cfg


def reset():
    if STATE_FILE.exists():
        STATE_FILE.unlink()
