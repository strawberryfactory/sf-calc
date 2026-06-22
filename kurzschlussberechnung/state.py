"""
state.py — Persistenter Zustand der Kurzschlussberechnung (Schnellmodus).

Der Schnellmodus modelliert das haeufigste Szenario: Netzeinspeisung -> Trafo
-> EINE Leitung zum Fehlerort. Fuer komplexe Kaskaden gibt es den Config-Datei-
Modus (siehe cli: --config <datei.py|.json>).

Einstellungen liegen in ~/.config/kurzschlussberechnung/state.json.
"""

import json
from pathlib import Path

from . import kern

CONFIG_DIR = Path.home() / ".config" / "kurzschlussberechnung"
STATE_FILE = CONFIG_DIR / "state.json"

DEFAULTS = {
    # Netzeinspeisung
    "un": 400.0,          # Nennspannung [V]
    "sk": 500.0,          # Kurzschlussleistung Netz Sk" [MVA]
    "xq_rq": 10.0,        # XQ/RQ-Verhaeltnis
    # Trafo
    "srt": 630.0,         # Bemessungsleistung [kVA]
    "uk": 6.0,            # Kurzschlussspannung [%]
    "ur": 1.15,           # Wirkanteil der Kurzschlussspannung [%]
    # Leitung zum Fehlerort
    "s": 95.0,            # Querschnitt [mm2]
    "laenge": 20.0,       # Laenge [m]
    "material": "Cu",     # Cu | Al
    "isolierung": "PVC",  # PVC | XLPE | EPR
    "n_parallel": 1,      # parallele Straenge je Aussenleiter
    "ta": 0.1,            # Ausloesezeit der Schutzeinrichtung [s]
}

PARAM_TYP = {
    "un": float, "sk": float, "xq_rq": float, "srt": float, "uk": float,
    "ur": float, "s": float, "laenge": float, "material": str,
    "isolierung": str, "n_parallel": int, "ta": float,
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
    if param not in PARAM_TYP:
        raise StateFehler(f"Unbekannter Parameter '{param}'. Bekannt: {', '.join(DEFAULTS)}")
    typ = PARAM_TYP[param]
    try:
        wert = typ(roh)
    except ValueError:
        raise StateFehler(f"'{roh}' ist kein gueltiger Wert fuer {param} ({typ.__name__}).")
    if param == "material" and wert not in ("Cu", "Al"):
        raise StateFehler("material muss Cu oder Al sein.")
    if param == "isolierung" and wert not in ("PVC", "XLPE", "EPR"):
        raise StateFehler("isolierung muss PVC, XLPE oder EPR sein.")
    if param in ("un", "sk", "srt", "uk", "s", "laenge", "ta") and wert <= 0:
        raise StateFehler(f"{param} muss groesser als 0 sein.")
    if param == "n_parallel" and wert < 1:
        raise StateFehler("n_parallel muss >= 1 sein.")
    if param == "material" and wert == "Al":
        # Kern hat nur Cu-Tabelle; Al braucht r_prime/x_prime-Override (Config-Modus).
        raise StateFehler("Al im Schnellmodus nicht unterstuetzt (nur Cu). "
                          "Fuer Al den Config-Datei-Modus mit r_prime/x_prime nutzen.")
    return wert


def setzen(param, roh):
    cfg = laden()
    cfg[param] = parse_wert(param, roh)
    speichern(cfg)
    return cfg


def build_config(cfg):
    """Baut aus dem flachen Schnellmodus-State die kern-Config (Quelle/Trafo/1 Leitung)."""
    return {
        "quelle": {"Un_V": cfg["un"], "Sk_MVA": cfg["sk"], "xq_rq_ratio": cfg["xq_rq"]},
        "trafo": {"SrT_kVA": cfg["srt"], "UrT_V": cfg["un"],
                  "uk_pct": cfg["uk"], "ur_pct": cfg["ur"]},
        "Ta_sammelschiene_s": cfg["ta"],
        "leitungen": [{
            "label": f"Leitung ({cfg['n_parallel']}x{cfg['s']:g} {cfg['material']}, {cfg['laenge']:g} m)",
            "S_mm2": cfg["s"], "L_m": cfg["laenge"],
            "material": cfg["material"], "isolierung": cfg["isolierung"],
            "n_parallel": cfg["n_parallel"], "Ta_s": cfg["ta"],
        }],
    }
