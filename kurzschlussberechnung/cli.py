"""
cli.py — Kommandozeile fuer die Kurzschlussberechnung.

  kurzschlussberechnung -h
  kurzschlussberechnung set s 95
  kurzschlussberechnung show
  kurzschlussberechnung reset
  kurzschlussberechnung calc                 # Schnellmodus aus State
  kurzschlussberechnung calc --config netz.py|.json   # komplexe Kaskade
  kurzschlussberechnung calc --json          # nur JSON-Kontrakt (fuer Pipe)
  kurzschlussberechnung -i                   # interaktiv

Pipe in die Kabelberechnung:
  kurzschlussberechnung calc --json | kabelberechnung calc --strom 600 --parallel
"""

import argparse
import json
import sys

from . import kern
from . import state as S
from . import ausgabe


def _load_config(path):
    """Laedt eine kern-Config aus .py (Variable CONFIG) oder .json."""
    if path.endswith(".py"):
        import importlib.util
        spec = importlib.util.spec_from_file_location("user_config", path)
        if spec is None or spec.loader is None:
            raise OSError(f"Konnte {path} nicht als Python-Modul laden")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "CONFIG"):
            raise ValueError(f"{path} muss eine Top-Level-Variable CONFIG (dict) exportieren")
        return mod.CONFIG
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────
# Subcommands
# ─────────────────────────────────────────────────────────────
def cmd_set(args):
    cfg = S.setzen(args.parameter, args.wert)
    print(f"✓ {args.parameter} = {cfg[args.parameter]}")


def cmd_reset(args):
    S.reset()
    print("✓ Auf Standardwerte zurueckgesetzt.")


def cmd_show(args):
    cfg = S.laden()
    print("\nAktuelle Einstellungen (Schnellmodus):")
    print("  Netz:")
    print(f"    un          {cfg['un']:g} V")
    print(f"    sk          {cfg['sk']:g} MVA")
    print(f"    xq_rq       {cfg['xq_rq']:g}")
    print("  Trafo:")
    bank = f"{cfg['n_trafo']}x " if cfg["n_trafo"] > 1 else ""
    print(f"    trafo       {bank}{cfg['trafo']:g} kVA"
          + (f"  (= {cfg['trafo'] * cfg['n_trafo']:g} kVA total)" if cfg["n_trafo"] > 1 else ""))
    print(f"    n_trafo     {cfg['n_trafo']}")
    print(f"    uk          {cfg['uk']:g} %")
    print(f"    ur          {cfg['ur']:g} %")
    print("  Leitung zum Fehlerort:")
    print(f"    s           {cfg['s']:g} mm2")
    print(f"    laenge      {cfg['laenge']:g} m")
    print(f"    material    {cfg['material']}")
    print(f"    isolierung  {cfg['isolierung']}")
    print(f"    n_parallel  {cfg['n_parallel']}")
    print(f"    ta          {cfg['ta']:g} s")
    print()


def _hole_ergebnis(args):
    """Liefert (ergebnis, leitung_index) aus --config oder dem Schnellmodus-State."""
    if getattr(args, "config", None):
        config = _load_config(args.config)
    else:
        config = S.build_config(S.laden())
    return kern.berechne_szenario(config), getattr(args, "leitung", None)


def cmd_calc(args):
    ergebnis, leitung_index = _hole_ergebnis(args)
    if args.json:
        # Nur den Kontrakt auf stdout -> pipebar nach kabelberechnung.
        print(json.dumps(ausgabe.json_kontrakt(ergebnis, leitung_index), ensure_ascii=False))
    else:
        ausgabe.konsole(ergebnis)


def cmd_interactive(args):
    cfg = S.laden()
    print("\nKurzschlussberechnung — interaktiv (Enter = aktueller Wert)\n")
    # Trafo zuerst: Groesse aus Katalog waehlen, dann Anzahl parallel.
    # uk/ur werden aus der Groesse uebernommen (Default-Annahmen).
    print("Trafo waehlen:")
    groessen = list(kern.TRAFO_KATALOG)
    for i, kva in enumerate(groessen, 1):
        kat = kern.TRAFO_KATALOG[kva]
        mark = "*" if kva == cfg["trafo"] else " "
        print(f"  [{i}]{mark} {kva:>4} kVA   (uk {kat['uk_pct']:g} %, ur {kat['ur_pct']:g} %)")
    cfg["trafo"] = _wahl(groessen, cfg["trafo"], "Trafo")
    kat = kern.TRAFO_KATALOG[cfg["trafo"]]
    cfg["uk"], cfg["ur"] = kat["uk_pct"], kat["ur_pct"]   # Annahmen aus Katalog
    cfg["n_trafo"] = _zahl("  Anzahl parallel n_trafo", cfg["n_trafo"], int)

    print("Netzeinspeisung:")
    cfg["un"] = _zahl("  Nennspannung un [V]", cfg["un"], float)
    cfg["sk"] = _zahl("  Kurzschlussleistung Sk\" [MVA]", cfg["sk"], float)
    print("Leitung zum Fehlerort:")
    cfg["s"] = _zahl("  Querschnitt s [mm2]", cfg["s"], float)
    cfg["laenge"] = _zahl("  Laenge [m]", cfg["laenge"], float)
    cfg["n_parallel"] = _zahl("  parallele Straenge n", cfg["n_parallel"], int)
    cfg["ta"] = _zahl("  Ausloesezeit ta [s]", cfg["ta"], float)

    if input("\nEinstellungen speichern? (j/N): ").strip().lower() == "j":
        S.speichern(cfg)
        print("✓ gespeichert")

    ausgabe.konsole(kern.berechne_szenario(S.build_config(cfg)))


def _wahl(optionen, aktuell, label):
    roh = input(f"{label} (1-{len(optionen)}) > ").strip()
    if not roh:
        return aktuell
    try:
        idx = int(roh)
        if 1 <= idx <= len(optionen):
            return optionen[idx - 1]
    except ValueError:
        pass
    print("  ungueltig, behalte", aktuell)
    return aktuell


def _zahl(label, aktuell, typ):
    roh = input(f"{label}" + (f" ({aktuell:g})" if aktuell is not None else "") + " > ").strip()
    if not roh:
        return aktuell
    try:
        return typ(float(roh)) if typ is int else typ(roh)
    except ValueError:
        print("  ungueltig, behalte", aktuell)
        return aktuell


# ─────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────
def build_parser():
    parser = argparse.ArgumentParser(
        prog="kurzschlussberechnung",
        description="Kurzschlussberechnung nach IEC 60909-0 "
                    "(Netzeinspeisung, Trafo, Leitungskaskade).",
        epilog="Beispiele:\n"
               "  kurzschlussberechnung set s 95\n"
               "  kurzschlussberechnung calc\n"
               "  kurzschlussberechnung calc --config netz.py\n"
               "  kurzschlussberechnung calc --json | kabelberechnung calc --strom 600 --parallel\n"
               "  kurzschlussberechnung -i\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="interaktiver Modus")
    sub = parser.add_subparsers(dest="command")

    p_set = sub.add_parser("set", help="Parameter dauerhaft setzen")
    p_set.add_argument("parameter", choices=list(S.DEFAULTS))
    p_set.add_argument("wert")
    p_set.set_defaults(func=cmd_set)

    p_show = sub.add_parser("show", help="aktuelle Einstellungen zeigen")
    p_show.set_defaults(func=cmd_show)

    p_reset = sub.add_parser("reset", help="auf Standardwerte zuruecksetzen")
    p_reset.set_defaults(func=cmd_reset)

    p_calc = sub.add_parser("calc", help="Berechnung ausfuehren")
    p_calc.add_argument("--config", help="Config-Datei (.py mit CONFIG oder .json)")
    p_calc.add_argument("--json", action="store_true",
                        help="nur JSON-Kontrakt ausgeben (fuer Pipe in kabelberechnung)")
    p_calc.add_argument("--leitung", type=int, metavar="N",
                        help="Index der zu schuetzenden Leitung fuer --json (Default: letzte)")
    p_calc.set_defaults(func=cmd_calc)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.interactive:
            cmd_interactive(args)
        elif getattr(args, "func", None):
            args.func(args)
        else:
            parser.print_help()
    except S.StateFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
