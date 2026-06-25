"""
cli.py — Versicherungs-Offertenvergleich.

  versicherungsvergleich beispiel > vergleich.json
  versicherungsvergleich vergleichen --config vergleich.json
  versicherungsvergleich vergleichen --config vergleich.json --json --protokoll nachweis.md

Config (JSON): firma, ausschreibung{firma, sparten:[{name, versicherungssumme, selbstbehalt}]},
offerten:[{versicherer, status: offeriert|verzichtet, positionen:[{sparte, praemie,
versicherungssumme, selbstbehalt, bemerkung}]}].
"""

import argparse
import json
import sys

from . import rechnen as R


def chf(x):
    try:
        return f"{x:,.2f}".replace(",", "'")
    except (TypeError, ValueError):
        return "—" if x is None else str(x)


def _protokoll(pfad, cfg, res):
    import os
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    neu = not os.path.exists(pfad)
    out = []
    if neu:
        out.append("# Vergleichsprotokoll — versicherungsvergleich\n")
        out.append("> Rechennachweis: extrahierte Offerten (Eingabe) und deterministischer "
                   "Vergleich (Matrix, Stempelabgabe, Ranking) als Ausgabe.\n")
    out.append(f"\n## `vergleichen` · {ts}\n")
    out.append("**Eingabe (Ausschreibung + extrahierte Offerten)**\n\n```json")
    out.append(json.dumps(cfg, ensure_ascii=False, indent=2))
    out.append("```\n\n**Ausgabe (deterministisch)**\n\n```json")
    out.append(json.dumps(res, ensure_ascii=False, indent=2))
    out.append("```")
    with open(pfad, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def cmd_vergleichen(args):
    cfg = json.loads(open(args.config, encoding="utf-8").read())
    res = R.vergleiche(cfg)
    if getattr(args, "protokoll", None):
        _protokoll(args.protokoll, cfg, res)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    vers = res["versicherer"]
    print(f"\nPrämienvergleich — {res['firma']}")
    print("─" * 70)
    print(f"{'Sparte':<26}" + "".join(f"{v[:13]:>14}" for v in vers))
    for sp in res["sparten"]:
        print(f"{sp[:26]:<26}" + "".join(f"{chf(res['matrix'][v].get(sp)):>14}" for v in vers))
    print("-" * (26 + 14 * len(vers)))
    sm = {s["versicherer"]: s for s in res["summen"]}
    print(f"{'Stempelabgabe':<26}" + "".join(f"{chf(sm[v]['stempelabgabe']):>14}" for v in vers))
    print(f"{'Total inkl. Stempel':<26}" + "".join(f"{chf(sm[v]['total_inkl_stempel']):>14}" for v in vers))
    print("\nRanking (günstigster zuerst):")
    for r in res["ranking"]:
        voll = "" if r["vollstaendig"] else "  (unvollständig)"
        print(f"  {r['rang']}. {r['versicherer']:<22} {chf(r['total_inkl_stempel'])}{voll}")
    if res["verzichtet"]:
        print(f"\nVerzichtet: {', '.join(res['verzichtet'])}")
    if res["deckungs_abweichungen"]:
        print("\nDeckungsabweichungen gegenüber Ausschreibung:")
        for d in res["deckungs_abweichungen"]:
            print(f"  ⚠ {d['versicherer']} / {d['sparte']}: {d['feld']} "
                  f"verlangt {chf(d['verlangt'])}, offeriert {chf(d['offeriert'])}")
    for w in res["warnungen"]:
        print("  ⚠ " + w)


def cmd_beispiel(args):
    bsp = {
        "ausschreibung": {
            "firma": "Beispiel GmbH",
            "sparten": [
                {"name": "Sachversicherung", "versicherungssumme": 150000, "selbstbehalt": 200},
                {"name": "IT-Haftpflicht", "versicherungssumme": 5000000, "selbstbehalt": 200},
                {"name": "MF AG 40326"}, {"name": "MF AG 399562"}, {"name": "MF AG 444639"},
            ],
        },
        "offerten": [
            {"versicherer": "Versicherer A", "status": "offeriert", "positionen": [
                {"sparte": "Sachversicherung", "praemie": 1000, "versicherungssumme": 150000, "selbstbehalt": 200},
                {"sparte": "MF AG 40326", "praemie": 1500},
                {"sparte": "MF AG 399562", "praemie": 1000},
                {"sparte": "MF AG 444639", "praemie": 1500}]},
            {"versicherer": "Versicherer B", "status": "offeriert", "positionen": [
                {"sparte": "Sachversicherung", "praemie": 2000, "versicherungssumme": 150000, "selbstbehalt": 500},
                {"sparte": "IT-Haftpflicht", "praemie": 3500, "versicherungssumme": 5000000, "selbstbehalt": 200},
                {"sparte": "MF AG 40326", "praemie": 1600},
                {"sparte": "MF AG 399562", "praemie": 1000},
                {"sparte": "MF AG 444639", "praemie": 1500}]},
            {"versicherer": "Versicherer C", "status": "offeriert", "positionen": [
                {"sparte": "Sachversicherung", "praemie": 2100, "versicherungssumme": 150000, "selbstbehalt": 200},
                {"sparte": "IT-Haftpflicht", "praemie": 10000, "versicherungssumme": 5000000, "selbstbehalt": 200},
                {"sparte": "MF AG 40326", "praemie": 2000},
                {"sparte": "MF AG 399562", "praemie": 1400},
                {"sparte": "MF AG 444639", "praemie": 1900}]},
            {"versicherer": "Versicherer D", "status": "verzichtet", "positionen": []},
        ],
    }
    print(json.dumps(bsp, ensure_ascii=False, indent=2))


def build_parser():
    p = argparse.ArgumentParser(prog="versicherungsvergleich",
                                description="Versicherungs-Offertenvergleich (deterministisch).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("vergleichen", help="Offerten vergleichen")
    sp.add_argument("--config", required=True)
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--protokoll", default=None, help="Markdown-Vergleichsnachweis (anhängen)")
    sp.set_defaults(func=cmd_vergleichen)
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
