"""
state.py — Persistenter Zustand der Kabelberechnung.

Einstellungen liegen in ~/.config/kabelberechnung/state.json.
'set' schreibt einzelne Parameter, 'reset' setzt auf Defaults.
calc-Flags uebersteuern den Zustand pro Aufruf (ohne ihn zu aendern).
"""

import json
from pathlib import Path

from . import tabellen as T

CONFIG_DIR = Path.home() / ".config" / "kabelberechnung"
STATE_FILE = CONFIG_DIR / "state.json"

DEFAULTS = {
    "spannung": 400,        # 230 | 400 | 690
    "verlegeart": "C",
    "kabel": "FE05-C",
    "strom": None,          # A   (Pflicht zur Berechnung)
    "laenge": 20.0,         # m
    "cosphi": None,         # None = auto (0.85 bei 3-ph, 1.0 bei 1-ph)
    "umgebung": 30,         # C
    "stromkreise": 1,       # Haeufung
    "max_du": 3.0,          # zul. Spannungsfall %
}

# Validierung/Parsing je Parameter
PARAM_TYP = {
    "spannung": int, "verlegeart": str, "kabel": str, "strom": float,
    "laenge": float, "cosphi": float, "umgebung": float,
    "stromkreise": int, "max_du": float,
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
    STATE_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def reset():
    cfg = dict(DEFAULTS)
    speichern(cfg)
    return cfg


def parse_wert(param, roh):
    """Konvertiert + validiert einen einzelnen Parameterwert."""
    if param not in PARAM_TYP:
        raise StateFehler(f"Unbekannter Parameter '{param}'. Bekannt: {', '.join(DEFAULTS)}")
    typ = PARAM_TYP[param]
    try:
        wert = typ(roh)
    except ValueError:
        raise StateFehler(f"'{roh}' ist kein gueltiger Wert fuer {param} ({typ.__name__}).")

    if param == "spannung" and wert not in T.SPANNUNGEN:
        raise StateFehler(f"Spannung muss 230, 400 oder 690 sein (war {wert}).")
    if param == "verlegeart" and wert not in T.VERLEGEARTEN:
        raise StateFehler(f"Verlegeart muss eine von {', '.join(T.VERLEGEARTEN)} sein.")
    if param == "kabel" and wert not in T.KABEL:
        raise StateFehler(f"Kabel muss eines von {', '.join(T.KABEL)} sein.")
    if param == "cosphi" and not (0 < wert <= 1):
        raise StateFehler("cosphi muss zwischen 0 und 1 liegen.")
    if param in ("strom", "laenge", "max_du") and wert <= 0:
        raise StateFehler(f"{param} muss groesser als 0 sein.")
    return wert


def setzen(param, roh):
    cfg = laden()
    cfg[param] = parse_wert(param, roh)
    speichern(cfg)
    return cfg


def aufloesen(cfg):
    """Leitet abgeleitete Werte ab (cosphi-auto, Kabel -> material/isolation)."""
    sys = T.SPANNUNGEN[cfg["spannung"]]
    kabel = T.KABEL[cfg["kabel"]]
    cosphi = cfg["cosphi"]
    if cosphi is None:
        cosphi = 0.85 if sys["phasen"] == 3 else 1.0
    return {
        "material": kabel["material"],
        "isolation": kabel["isolation"],
        "betriebstemp": kabel["betriebstemp"],
        "cosphi": cosphi,
        "phasen": sys["phasen"],
        "n_leiter": sys["n_leiter"],
        "sys_bez": sys["bez"],
        "kabel_bez": kabel["bez"],
    }
