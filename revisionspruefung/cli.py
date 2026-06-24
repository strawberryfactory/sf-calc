"""
cli.py — Prüfung eingeschränkte Revision (SER).

  revisionspruefung pruefen --config jr.json
  revisionspruefung pruefen --config jr.json --json --protokoll nachweis.md
  revisionspruefung beispiel    # Beispiel-Config ausgeben

Config (JSON): firma, jahr, bilanz{...}, er{...}, gewinnverwendung{...},
vorjahr{bilanz,er}, kennzahlen_basis{bilanzsumme,umsatz,fte}.
"""

import argparse
import json
import sys

from . import rechnen as R


def _protokoll(pfad, cfg, res):
    import os
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    neu = not os.path.exists(pfad)
    out = []
    if neu:
        out.append("# Prüfprotokoll — revisionspruefung (eingeschränkte Revision SER)\n")
        out.append("> Rechennachweis: geprüfte Jahresrechnung (Eingabe) und exakte "
                   "Prüf-Ausgabe. Nachvollziehbar, ersetzt aber das Prüfungsurteil nicht.\n")
    out.append(f"\n## `pruefen` · {ts}\n")
    out.append("**Eingabe (Jahresrechnung)**\n\n```json")
    out.append(json.dumps(cfg, ensure_ascii=False, indent=2))
    out.append("```\n\n**Prüf-Ausgabe (deterministisch)**\n\n```json")
    out.append(json.dumps(res, ensure_ascii=False, indent=2))
    out.append("```")
    with open(pfad, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def cmd_pruefen(args):
    cfg = json.loads(open(args.config, encoding="utf-8").read())
    res = R.pruefe(cfg)
    if getattr(args, "protokoll", None):
        _protokoll(args.protokoll, cfg, res)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    print(f"\nPrüfung eingeschränkte Revision — {res['firma']} {res['jahr'] or ''}")
    print("─" * 60)
    for c in res["checks"]:
        mark = "✓" if c["ok"] else "✗"
        print(f"  [{mark}] {c['pruefung']}\n       {c['befund']}")
    if res["analytik"]:
        print("\n  Analytische Prüfung (Vorjahresvergleich):")
        for a in res["analytik"]:
            v = f"{a['veraenderung']*100:+.1f} %" if a["veraenderung"] is not None else "—"
            flag = "  ⚠ wesentlich" if a["wesentlich"] else ""
            print(f"     {a['position']:<16} {a['jahr']:>12,} (VJ {a['vorjahr']:>12,})  {v}{flag}"
                  .replace(",", "'"))
    if res["kennzahlen"]:
        print("\n  Kennzahlen:", ", ".join(f"{k} {v*100:.1f} %" for k, v in res["kennzahlen"].items()))
    print(f"\n  Gesamturteil: {res['gesamturteil']}")
    for w in res["warnungen"]:
        print("  ⚠ " + w)


def cmd_beispiel(args):
    bsp = {
        "firma": "Muster AG", "jahr": 2024,
        "bilanz": {"total_aktiven": 1000000, "total_passiven": 1000000,
                   "aktienkapital": 100000, "gesetzliche_reserven": 50000,
                   "eigenkapital": 500000, "vortrag": 50000,
                   "jahresgewinn": 200000, "bilanzgewinn": 250000},
        "er": {"nettoerloes": 2000000, "bruttogewinn": 1500000, "ebitda": 400000,
               "ebit": 350000, "jahresgewinn": 200000, "personalaufwand": -900000},
        "gewinnverwendung": {"bilanzgewinn": 250000, "zuweisung_reserven": 0,
                             "dividende": 200000, "vortrag_neu": 50000},
        "vorjahr": {"bilanz": {"total_aktiven": 900000, "eigenkapital": 300000},
                    "er": {"nettoerloes": 1500000, "bruttogewinn": 1100000,
                           "ebitda": 250000, "jahresgewinn": 100000,
                           "personalaufwand": -850000}},
        "kennzahlen_basis": {"bilanzsumme": 1000000, "umsatz": 2000000, "fte": 30},
    }
    print(json.dumps(bsp, ensure_ascii=False, indent=2))


def build_parser():
    p = argparse.ArgumentParser(prog="revisionspruefung",
                                description="Prüfung eingeschränkte Revision (SER) — deterministische Checks.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("pruefen", help="Jahresrechnung prüfen")
    sp.add_argument("--config", required=True)
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--protokoll", default=None, help="Markdown-Prüfnachweis (anhängen)")
    sp.set_defaults(func=cmd_pruefen)
    sp = sub.add_parser("beispiel", help="Beispiel-Config ausgeben")
    sp.set_defaults(func=cmd_beispiel)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except R.RechenFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
