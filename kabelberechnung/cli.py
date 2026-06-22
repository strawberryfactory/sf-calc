"""
cli.py — Kommandozeile fuer die Kabelberechnung.

  kabelberechnung -h
  kabelberechnung set verlegeart C
  kabelberechnung show [--tabellen]
  kabelberechnung reset
  kabelberechnung calc [--strom 16 --laenge 25 ...]
  kabelberechnung -i
  kabelberechnung print <projektnr> [--verteilung UV4OG --klemme K12] [--pdf]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import tabellen as T
from . import state as S
from . import rechnen
from . import ausgabe


# ─────────────────────────────────────────────────────────────
# Berechnung aus aufgeloestem Zustand
# ─────────────────────────────────────────────────────────────
def _rechne(cfg):
    if cfg.get("strom") in (None, 0):
        raise S.StateFehler("Kein Strom gesetzt. 'kabelberechnung set strom 16' oder '--strom 16'.")
    abg = S.aufloesen(cfg)
    empfehlung, zeilen = rechnen.dimensioniere(
        strom_a=cfg["strom"], laenge_m=cfg["laenge"], cos_phi=abg["cosphi"],
        spannung_v=cfg["spannung"], verlegeart=cfg["verlegeart"],
        material=abg["material"], isolation=abg["isolation"],
        umgebung_c=cfg["umgebung"], anzahl_stromkreise=cfg["stromkreise"],
        max_du=cfg["max_du"], betriebstemp_c=abg["betriebstemp"],
    )
    return abg, empfehlung, zeilen


def _flags_anwenden(cfg, args):
    """calc-/print-Flags uebersteuern den gespeicherten Zustand (nicht-persistent)."""
    for param in S.DEFAULTS:
        wert = getattr(args, param, None)
        if wert is not None:
            cfg[param] = S.parse_wert(param, str(wert))
    return cfg


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
    abg = S.aufloesen(cfg)
    print("\nAktuelle Einstellungen:")
    for k in S.DEFAULTS:
        wert = cfg[k]
        zusatz = ""
        if k == "cosphi" and wert is None:
            zusatz = f"  (auto: {abg['cosphi']:.2f})"
        if k == "strom" and wert is None:
            zusatz = "  (nicht gesetzt)"
        print(f"  {k:<12} {wert}{zusatz}")
    print(f"\n  -> {abg['sys_bez']}, {abg['kabel_bez']}, "
          f"Verlegeart {cfg['verlegeart']}")
    if args.tabellen:
        _zeige_tabellen()
    print()


def _zeige_tabellen():
    print("\nVerifizierte Iz-Tabellen (Verlegeart/Material/Isolation/Leiter):")
    for key in sorted(T.IZ):
        status = T.IZ_STATUS.get(key, "offen")
        marker = "✓" if status.startswith("verifiziert") else "○"
        va, mat, iso, n = key
        print(f"  {marker} {va:<3} {mat}/{iso}/{n}L   {status}")
    fehlend = [va for va in T.VERLEGEARTEN
               if not any(k[0] == va and T.IZ_STATUS.get(k, "").startswith("verifiziert")
                          for k in T.IZ)]
    if fehlend:
        print(f"\n  Noch offen (keine verifizierten Daten): {', '.join(fehlend)}")


def _ik_aufloesen(args):
    """
    Liefert (ik_a, t_aus_s) fuer den Kurzschluss-Nachweis.
    Quelle in Prioritaet:  --ik Flag  >  stdin-JSON (Pipe)  >  nichts.

    Pipe-Format (z.B. aus kurzschlussberechnung):
      {"ik_max_ka": 25.0, "t_aus_s": 0.1, ...}
    """
    # 1) explizites Flag (kA -> A)
    if getattr(args, "ik", None) is not None:
        return args.ik * 1000.0, getattr(args, "t_aus", None)
    # 2) Pipe auf stdin (nur wenn nicht-interaktiv und Daten vorhanden)
    if not sys.stdin.isatty():
        roh = sys.stdin.read().strip()
        if roh:
            try:
                daten = json.loads(roh)
                ik_ka = daten.get("ik_max_ka") or daten.get("ik_ka")
                if ik_ka is not None:
                    t_aus = getattr(args, "t_aus", None) or daten.get("t_aus_s")
                    return float(ik_ka) * 1000.0, t_aus
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
    return None, getattr(args, "t_aus", None)


def cmd_calc(args):
    cfg = _flags_anwenden(S.laden(), args)
    ik_a, t_aus_s = _ik_aufloesen(args)
    abg, empfehlung, zeilen = _rechne(cfg)
    ausgabe.konsole(cfg, abg, empfehlung, zeilen)

    # Parallel-Vorschlag: explizit (--parallel) oder automatisch, wenn kein
    # einzelner Querschnitt thermisch+dU passt (typisch bei sehr hohem Ib).
    if getattr(args, "parallel", False) or empfehlung is None:
        vorschlaege, k_faktor = rechnen.dimensioniere_parallel(
            strom_a=cfg["strom"], laenge_m=cfg["laenge"], cos_phi=abg["cosphi"],
            spannung_v=cfg["spannung"], verlegeart=cfg["verlegeart"],
            material=abg["material"], isolation=abg["isolation"],
            umgebung_c=cfg["umgebung"], anzahl_stromkreise=cfg["stromkreise"],
            max_du=cfg["max_du"], betriebstemp_c=abg["betriebstemp"],
            ik_a=ik_a, t_aus_s=t_aus_s, k_faktor=getattr(args, "kfaktor", None),
        )
        ausgabe.konsole_parallel(cfg, abg, vorschlaege, k_faktor, ik_a, t_aus_s)


def cmd_interactive(args):
    cfg = S.laden()
    print("\nKabelberechnung — interaktiv (Enter = aktueller Wert)\n")

    # Verlegeart
    arten = list(T.VERLEGEARTEN)
    print("Verlegeart:")
    for i, va in enumerate(arten, 1):
        verif = any(k[0] == va and T.IZ_STATUS.get(k, "").startswith("verifiziert") for k in T.IZ)
        mark = "*" if va == cfg["verlegeart"] else " "
        flag = "" if verif else "  (noch keine Daten)"
        print(f"  [{i}]{mark} {va} — {T.VERLEGEARTEN[va]}{flag}")
    cfg["verlegeart"] = _wahl(arten, cfg["verlegeart"], "Verlegeart")

    # Spannung
    spgn = list(T.SPANNUNGEN)
    print("\nSpannung:")
    for i, sp in enumerate(spgn, 1):
        mark = "*" if sp == cfg["spannung"] else " "
        print(f"  [{i}]{mark} {T.SPANNUNGEN[sp]['bez']}")
    cfg["spannung"] = _wahl(spgn, cfg["spannung"], "Spannung")

    cfg["strom"] = _zahl("Strom Ib [A]", cfg["strom"], float)
    cfg["laenge"] = _zahl("Laenge [m]", cfg["laenge"], float)
    cfg["max_du"] = _zahl("Zul. Spannungsfall [%]", cfg["max_du"], float)

    if input("\nEinstellungen speichern? (j/N): ").strip().lower() == "j":
        S.speichern(cfg)
        print("✓ gespeichert")

    abg, empfehlung, zeilen = _rechne(cfg)
    ausgabe.konsole(cfg, abg, empfehlung, zeilen)


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
    roh = input(f"{label}" + (f" ({aktuell})" if aktuell is not None else "") + " > ").strip()
    if not roh:
        return aktuell
    try:
        return typ(roh)
    except ValueError:
        print("  ungueltig, behalte", aktuell)
        return aktuell


# ─────────────────────────────────────────────────────────────
# print: Markdown ins Projektverzeichnis (Aufloesung wie `p`)
# ─────────────────────────────────────────────────────────────
def _projekt_dir(projektnr):
    base_kandidaten = sorted(Path.home().glob("Library/CloudStorage/*Partner*"))
    if not base_kandidaten:
        raise S.StateFehler("PIAG-Ordner (*Partner*) in CloudStorage nicht gefunden.")
    base = base_kandidaten[0]
    treffer = sorted(base.glob(f"{projektnr}*"))
    treffer = [t for t in treffer if t.is_dir()]
    if not treffer:
        raise S.StateFehler(f"Projekt {projektnr} nicht gefunden in {base}.")
    return treffer[0]


def cmd_print(args):
    cfg = _flags_anwenden(S.laden(), args)
    abg, empfehlung, zeilen = _rechne(cfg)
    md = ausgabe.markdown(cfg, abg, empfehlung, zeilen, projekt=args.projektnr,
                          verteilung=args.verteilung or "", klemme=args.klemme or "")
    ziel_dir = _projekt_dir(args.projektnr)
    name = ausgabe.dateiname(cfg, args.projektnr, args.verteilung or "", args.klemme or "")
    ziel = ziel_dir / name
    ziel.write_text(md, encoding="utf-8")
    print(f"✓ Markdown geschrieben: {ziel}")

    if args.pdf:
        skript = Path.home() / "Documents/3_wissen/3f_KI-skills/piag-pdf/piag_report.py"
        if not skript.exists():
            print(f"  (piag-pdf nicht gefunden unter {skript} — PDF uebersprungen)")
            return
        pdf = ziel.with_suffix(".pdf")
        try:
            subprocess.run([sys.executable, str(skript), str(ziel), "-o", str(pdf)], check=True)
            print(f"✓ PDF erzeugt: {pdf}")
        except subprocess.CalledProcessError as e:
            print(f"  PDF-Erzeugung fehlgeschlagen: {e}")
    else:
        print("  Tipp: in Claude '/piag-pdf' auf die Datei anwenden, oder '--pdf' nutzen.")


# ─────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────
def _calc_flags(p):
    p.add_argument("--strom", type=float, help="Strom Ib [A]")
    p.add_argument("--laenge", type=float, help="Laenge [m]")
    p.add_argument("--spannung", type=int, choices=list(T.SPANNUNGEN), help="230/400/690")
    p.add_argument("--verlegeart", choices=list(T.VERLEGEARTEN))
    p.add_argument("--kabel", choices=list(T.KABEL))
    p.add_argument("--cosphi", type=float)
    p.add_argument("--umgebung", type=float, help="Umgebungstemperatur [C]")
    p.add_argument("--stromkreise", type=int, help="Anzahl gebuendelter Stromkreise")
    p.add_argument("--max_du", type=float, help="zul. Spannungsfall [%%]")
    # Parallelverlegung / Kurzschluss (transient, nicht im State)
    p.add_argument("--parallel", action="store_true",
                   help="Aufteilung auf parallele Kabel (n=2,3,4) vorschlagen")
    p.add_argument("--ik", type=float, metavar="kA",
                   help="Kurzschlussstrom Ik [kA] fuer Einzelleiter-Nachweis")
    p.add_argument("--t-aus", dest="t_aus", type=float, metavar="s",
                   help="Ausloesezeit der Schutzeinrichtung [s]")
    p.add_argument("--kfaktor", type=float,
                   help="k-Faktor ueberschreiben (Default aus Kabel)")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="kabelberechnung",
        description="Kabeldimensionierung nach NIN / IEC 60364-5-52 "
                    "(thermisch + Spannungsfall).",
        epilog="Beispiele:\n"
               "  kabelberechnung set verlegeart C\n"
               "  kabelberechnung set strom 16\n"
               "  kabelberechnung calc --laenge 25\n"
               "  kabelberechnung -i\n"
               "  kabelberechnung print 3142 --verteilung UV4OG --klemme K12\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="interaktiver Modus (durchklicken)")
    sub = parser.add_subparsers(dest="command")

    p_set = sub.add_parser("set", help="Parameter dauerhaft setzen")
    p_set.add_argument("parameter", choices=list(S.DEFAULTS))
    p_set.add_argument("wert")
    p_set.set_defaults(func=cmd_set)

    p_show = sub.add_parser("show", help="aktuelle Einstellungen zeigen")
    p_show.add_argument("--tabellen", action="store_true", help="Tabellen-Abdeckung zeigen")
    p_show.set_defaults(func=cmd_show)

    p_reset = sub.add_parser("reset", help="auf Standardwerte zuruecksetzen")
    p_reset.set_defaults(func=cmd_reset)

    p_calc = sub.add_parser("calc", help="Berechnung ausfuehren")
    _calc_flags(p_calc)
    p_calc.set_defaults(func=cmd_calc)

    p_print = sub.add_parser("print", help="Markdown (piag-pdf) ins Projekt schreiben")
    p_print.add_argument("projektnr", help="z.B. 3142")
    p_print.add_argument("--verteilung", help="z.B. UV4OG")
    p_print.add_argument("--klemme", help="z.B. K12")
    p_print.add_argument("--pdf", action="store_true", help="gleich PDF via piag-pdf erzeugen")
    _calc_flags(p_print)
    p_print.set_defaults(func=cmd_print)

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
    except (S.StateFehler, rechnen.RechenFehler) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
