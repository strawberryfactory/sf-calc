"""
cli.py — Unternehmens-Finanzplan (3-Statement).

  unternehmensfinanzplan plan --config plan.json
  unternehmensfinanzplan plan --config plan.json --json
  unternehmensfinanzplan beispiel        # fiktive Beispiel-Config ausgeben

Config (JSON): jahre, ertrag ODER auslastung+vollkapazitaet, personalaufwand,
uebriger_aufwand, investition, nutzungsdauer, abschr_methode, erstjahr_anteil,
aktienkapital, darlehen, zins, amortisation (opt.), steuersatz, debitoren_quote, firma.
"""

import argparse
import json
import sys

from . import rechnen as R


def chf(x):
    try:
        return f"{x:,.0f}".replace(",", "'")
    except (TypeError, ValueError):
        return str(x)


def _tabelle(titel, spalten, zeilen):
    print(f"\n{titel}")
    print("─" * len(titel))
    kopf = f"{'':<24}" + "".join(f"{j:>12}" for j in spalten)
    print(kopf)
    for label, werte in zeilen:
        print(f"{label:<24}" + "".join(f"{chf(w):>12}" for w in werte))


def _protokoll(pfad, cfg, res):
    """Eingaben (Config) + Python-Ausgabe als Markdown-Rechennachweis anhängen."""
    import os, datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    neu = not os.path.exists(pfad)
    out = []
    if neu:
        out.append("# Berechnungsprotokoll — unternehmensfinanzplan\n")
        out.append("> Rechennachweis: Eingabe-Config und exakte Python-Ausgabe je Lauf. "
                   "Erlaubt das Nachvollziehen aller Zahlen im Bericht.\n")
    out.append(f"\n## `plan` · {ts}\n")
    out.append("**Eingaben (Config)**\n")
    out.append("```json")
    out.append(json.dumps(cfg, ensure_ascii=False, indent=2))
    out.append("```")
    out.append("\n**Ausgabe (Python, deterministisch)**\n")
    out.append("```json")
    out.append(json.dumps(res, ensure_ascii=False, indent=2))
    out.append("```")
    with open(pfad, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def cmd_plan(args):
    cfg = json.loads(open(args.config, encoding="utf-8").read())
    res = R.mehrjahresplan(cfg)
    if getattr(args, "protokoll", None):
        _protokoll(args.protokoll, cfg, res)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    jahre = res["jahre"]
    er = res["erfolgsrechnung"]
    _tabelle(f"Plan-Erfolgsrechnung — {res['firma']}", jahre, [
        ("Ertrag", [r["ertrag"] for r in er]),
        ("Personalaufwand", [r["personalaufwand"] for r in er]),
        ("Übriger Aufwand", [r["uebriger_aufwand"] for r in er]),
        ("EBITDA", [r["ebitda"] for r in er]),
        ("Abschreibungen", [r["abschreibung"] for r in er]),
        ("EBIT", [r["ebit"] for r in er]),
        ("Finanzaufwand", [r["finanzaufwand"] for r in er]),
        ("EBT", [r["ebt"] for r in er]),
        ("Steuern", [r["steuern"] for r in er]),
        ("Erfolg", [r["erfolg"] for r in er]),
    ])
    bi = res["bilanz"]
    _tabelle("Plan-Bilanz", jahre, [
        ("Bank/Liquidität", [r["bank"] for r in bi]),
        ("Debitoren", [r["debitoren"] for r in bi]),
        ("Anlagevermögen", [r["anlagevermoegen"] for r in bi]),
        ("Total Aktiven", [r["total_aktiven"] for r in bi]),
        ("Darlehen (FK)", [r["darlehen"] for r in bi]),
        ("Aktienkapital", [r["aktienkapital"] for r in bi]),
        ("Kumul. Gewinn", [r["kumulierter_gewinn"] for r in bi]),
        ("Eigenkapital", [r["eigenkapital"] for r in bi]),
        ("Total Passiven", [r["total_passiven"] for r in bi]),
        ("Bilanzcheck", [r["check"] for r in bi]),
    ])
    gf = res["geldfluss"]
    _tabelle("Geldfluss / Schuldendienst", jahre, [
        ("Cashflow operativ", [r["cashflow_operativ"] for r in gf]),
        ("Schuldendienst", [r["schuldendienst"] for r in gf]),
        ("DSCR", [f"{r['dscr']:.2f}×" if r["dscr"] is not None else "n/a" for r in gf]),
        ("Bank Ende", [r["bank_ende"] for r in gf]),
    ])
    k = res["kennzahlen"]

    def _pct(v):
        return f"{v*100:.1f} %" if v is not None else "n/a"

    def _x(v):
        return f"{v:.2f}×" if v is not None else "n/a"

    print(f"\nKennzahlen (Endjahr): EBITDA-Marge {_pct(k['ebitda_marge'])} · "
          f"EBIT-Marge {_pct(k['ebit_marge'])} · EBT-Marge {_pct(k['ebt_marge'])} · "
          f"Eigenkapitalquote {_pct(k['eigenkapitalquote'])}")
    print(f"Bank-Kennzahlen: DSCR {_x(k['dscr'])} (Min über Plan {_x(k['dscr_min'])}) · "
          f"Nettoverschuldung {chf(k['nettoverschuldung'])} · "
          f"Nettoverschuldung/EBITDA {_x(k['nettoverschuldung_ebitda'])}")
    print(f"Bilanz stimmt: {'ja' if res['bilanz_ok'] else 'NEIN'}")
    for w in res["warnungen"]:
        print("  ⚠ " + w)


def cmd_beispiel(args):
    beispiel = {
        "firma": "Muster Dienstleistungs AG", "jahre": [2025, 2026, 2027, 2028, 2029],
        "auslastung": [0.50, 0.80, 0.90, 0.95, 1.00], "vollkapazitaet": 800000,
        "personalaufwand": [150000, 260000, 280000, 300000, 320000],
        "uebriger_aufwand": [70000, 100000, 100000, 100000, 100000],
        "investition": 400000, "nutzungsdauer": 5, "abschr_methode": "linear",
        "erstjahr_anteil": 0.50, "aktienkapital": 100000, "darlehen": 350000,
        "zins": 0.03, "amortisation": [0, 70000, 70000, 70000, 70000],
        "steuersatz": 0.13, "debitoren_quote": 0.10,
    }
    print(json.dumps(beispiel, ensure_ascii=False, indent=2))


def build_parser():
    p = argparse.ArgumentParser(prog="unternehmensfinanzplan",
                                description="Unternehmens-Finanzplan (3-Statement), OR-nah.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("plan", help="Plan aus JSON-Config rechnen")
    sp.add_argument("--config", required=True)
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--protokoll", default=None, help="Markdown-Rechennachweis (anhängen)")
    sp.set_defaults(func=cmd_plan)
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
