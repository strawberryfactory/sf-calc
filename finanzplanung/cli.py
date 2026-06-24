"""
cli.py — Kommandozeile der Finanzplanung (Schweizer Vorsorge).

  finanzplanung -h
  finanzplanung show [--tabellen] [--annahmen]
  finanzplanung set rendite 0.02
  finanzplanung ahv --beitragsjahre 44 --einkommen 90000
  finanzplanung bvg-rente --guthaben 500000
  finanzplanung bvg-projektion --guthaben 300000 --koordlohn 50000 --alter 50 --pension 65
  finanzplanung saeule3a --einkommen 120000 --mit-pk
  finanzplanung luecke --einkommen 100000 --ahv 29400 --bvg 34000
  finanzplanung kapitalbedarf --luecke 20000 --jahre 25
  finanzplanung verzehr --kapital 500000 --entnahme 30000
  finanzplanung tragbarkeit --wert 1200000 --hypothek 900000 --einkommen 180000
  finanzplanung plan --einkommen 100000 --beitragsjahre 44 --bvg-guthaben 500000 [--vermoegen 200000]

Jedes Rechen-Kommando akzeptiert --json (maschinenlesbar für Skills).
"""

import argparse
import json
import sys

from . import tabellen as T
from . import state as S
from . import rechnen as R
from . import ausgabe as A


def _protokoll(args, res):
    """Schreibt Eingaben + Ausgabe als Markdown-Rechennachweis, falls --protokoll gesetzt."""
    pfad = getattr(args, "protokoll", None)
    if not pfad:
        return
    skip = {"func", "json", "protokoll", "cmd"}
    eingaben = {k: v for k, v in vars(args).items() if k not in skip and v is not None}
    A.protokoll_append(pfad, getattr(args, "cmd", "?"), eingaben, res)


def _emit(res, args, text_fn):
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(text_fn(res))
        wb = A.warnungen_block(res)
        if wb:
            print(wb)
    _protokoll(args, res)


# ───────────────────────── set / show / reset ─────────────────────────
def cmd_set(args):
    cfg = S.setzen(args.parameter, args.wert)
    print(f"✓ {args.parameter} = {cfg[args.parameter]}")


def cmd_reset(args):
    S.reset()
    print("✓ Annahmen auf Defaults zurückgesetzt.")


def cmd_show(args):
    cfg = S.laden()
    if args.annahmen or not args.tabellen:
        print(A.titel("Planungsannahmen (überschreibbar, zu dokumentieren)"))
        print(f"  Normjahr         {cfg['jahr']}")
        print(f"  Rendite p.a.     {A.prozent(cfg['rendite'])}")
        print(f"  Teuerung p.a.    {A.prozent(cfg['teuerung'])}")
        print(f"  Endalter Plan    {cfg['lebenserwartung']}")
        print(f"  Ersatzquote Ziel {A.prozent(cfg['ersatzquote'])}")
        print("  ⚠ Annahmen sind mit Kunde/BCO zu bestätigen.")
    if args.tabellen:
        yr, ahv = T.jahr_oder_neuestes(T.AHV, cfg["jahr"])
        yrb, bvg = T.jahr_oder_neuestes(T.BVG, cfg["jahr"])
        yrs, s3a = T.jahr_oder_neuestes(T.SAEULE_3A, cfg["jahr"])
        print(A.titel(f"Normwerte (Stand {yr}/{yrb}/{yrs})"))
        print(f"  AHV Vollrente max   {A.chf0(ahv['rente_max_monat'])} /Mt   "
              f"min {A.chf0(ahv['rente_min_monat'])} /Mt   "
              f"[{'verifiziert' if ahv['verifiziert'] else 'NICHT verifiziert'}]")
        print(f"  BVG Umwandlungssatz {A.prozent(bvg['umwandlungssatz_65'])}   "
              f"Mindestzins {A.prozent(bvg['mindestzins'],2)}   "
              f"Koord.abzug {A.chf0(bvg['koordinationsabzug'])}")
        print(f"  Säule 3a max mit PK {A.chf0(s3a['max_mit_pk'])}   "
              f"ohne PK {A.chf0(s3a['max_ohne_pk_deckel'])}")
        print(f"  Tragbarkeit: kalk. Zins {A.prozent(T.TRAGBARKEIT['kalk_zinssatz'])}, "
              f"Grenze {A.prozent(T.TRAGBARKEIT['tragbarkeitsgrenze'])}, "
              f"Belehnung max {A.prozent(T.TRAGBARKEIT['belehnung_max'])}")
        print(f"  Quellen: {ahv['quelle']} · {bvg['quelle']} · {s3a['quelle']}")


# ───────────────────────── Rechen-Kommandos ─────────────────────────
def cmd_ahv(args):
    res = R.ahv_altersrente(args.beitragsjahre, args.einkommen, jahr=_jahr(args))
    _emit(res, args, lambda r: (
        A.titel("AHV-Altersrente (1. Säule)") +
        f"\n  Rente        {A.chf0(r['rente_jahr'])} /Jahr  ({A.chf0(r['rente_monat'])} /Mt)"
        f"\n  Vollrente    {A.chf0(r['vollrente_jahr'])} /Jahr"
        f"\n  Skalenfaktor {r['skalenfaktor']}  (Beitragsjahre)"))


def cmd_bvg_rente(args):
    res = R.bvg_rente(args.guthaben, umwandlungssatz=args.umwandlungssatz, jahr=_jahr(args))
    _emit(res, args, lambda r: (
        A.titel("BVG-Rente (2. Säule)") +
        f"\n  Altersguthaben {A.chf0(r['kapital'])}"
        f"\n  Umwandlungssatz {A.prozent(r['umwandlungssatz'])}"
        f"\n  Rente          {A.chf0(r['rente_jahr'])} /Jahr  ({A.chf0(r['rente_monat'])} /Mt)"))


def cmd_bvg_projektion(args):
    res = R.bvg_guthaben_projektion(args.guthaben, args.koordlohn, args.alter,
                                    args.pension, zins=args.zins, jahr=_jahr(args))
    _emit(res, args, lambda r: (
        A.titel("BVG Altersguthaben-Projektion") +
        f"\n  Guthaben bei Pensionierung {A.chf0(r['guthaben_pension'])}"
        f"\n  über {r['jahre']} Jahre, Zins {A.prozent(r['zins'],2)}"))


def cmd_saeule3a(args):
    res = R.saeule_3a_max(args.mit_pk, args.einkommen, jahr=_jahr(args))
    _emit(res, args, lambda r: (
        A.titel("Säule 3a — Maximalbeitrag") +
        f"\n  Max. abziehbar {A.chf0(r['max_beitrag'])}  "
        f"({'mit' if r['mit_pk'] else 'ohne'} Pensionskasse)"))


def cmd_luecke(args):
    res = R.vorsorgeluecke(args.einkommen, args.ahv, args.bvg, ersatzquote_ziel=args.ersatzquote)
    _emit(res, args, lambda r: (
        A.titel("Vorsorgelücke") +
        f"\n  Zielrente            {A.chf0(r['zielrente_jahr'])} /Jahr "
        f"({A.prozent(r['ersatzquote_ziel'])} des Einkommens)"
        f"\n  Einkommen 1.+2. S.   {A.chf0(r['einkommen_12_saeule'])} /Jahr"
        f"\n  Lücke                {A.chf0(r['luecke_jahr'])} /Jahr  ({A.chf0(r['luecke_monat'])} /Mt)"
        f"\n  Deckungsgrad         {A.prozent(r['deckungsgrad']) if r['deckungsgrad'] else '-'}"))


def cmd_kapitalbedarf(args):
    res = R.kapitalbedarf(args.luecke, args.jahre, rendite=args.rendite, teuerung=args.teuerung)
    _emit(res, args, lambda r: (
        A.titel("Kapitalbedarf zur Deckung der Lücke") +
        f"\n  Benötigtes Kapital {A.chf0(r['kapitalbedarf'])}"
        f"\n  für {r['jahre']} Jahre · Lücke {A.chf0(r['jahres_luecke'])}/J"
        f"\n  reale Rendite {A.prozent(r['reale_rendite'],2)} "
        f"(Rendite {A.prozent(r['rendite'])} / Teuerung {A.prozent(r['teuerung'])})"))


def cmd_verzehr(args):
    res = R.kapitalverzehr_dauer(args.kapital, args.entnahme,
                                 rendite=args.rendite, teuerung=args.teuerung)
    _emit(res, args, lambda r: (
        A.titel("Kapitalverzehr") +
        f"\n  Kapital reicht {r['dauer_jahre']} Jahre"
        + ("  (≥ Horizont)" if r.get('reicht_unbegrenzt') else "")))


def cmd_tragbarkeit(args):
    res = R.tragbarkeit(args.wert, args.hypothek, args.einkommen,
                        kalk_zins=args.zins, nebenkosten_quote=args.nebenkosten,
                        amortisation=args.amortisation)
    _emit(res, args, lambda r: (
        A.titel("Tragbarkeit Wohneigentum") +
        f"\n  Belehnung        {A.prozent(r['belehnung'])}  "
        f"[{'ok' if r['belehnung_ok'] else 'ZU HOCH (>80 %)'}]"
        f"\n  Zinskosten       {A.chf0(r['zins_kosten'])}/J  (kalk. {A.prozent(r['kalk_zins'])})"
        f"\n  Nebenkosten      {A.chf0(r['nebenkosten'])}/J"
        f"\n  Amortisation     {A.chf0(r['amortisation'])}/J"
        f"\n  Wohnkosten total {A.chf0(r['wohnkosten_jahr'])}/J"
        f"\n  Tragbarkeitsquote {A.prozent(r['tragbarkeitsquote'])}  "
        f"(Grenze {A.prozent(r['grenze'])})"
        f"\n  → {'TRAGBAR' if r['tragbar'] else 'NICHT tragbar'}"))


def cmd_plan(args):
    """Vollständige Pensionierungs-Analyse (verkettet)."""
    cfg = S.laden()
    jahr = _jahr(args)
    ahv_eink = args.ahv_einkommen if args.ahv_einkommen is not None else args.einkommen
    ahv = R.ahv_altersrente(args.beitragsjahre, ahv_eink, jahr=jahr)

    if args.bvg_guthaben is not None:
        bvg = R.bvg_rente(args.bvg_guthaben, umwandlungssatz=args.umwandlungssatz, jahr=jahr)
    elif args.bvg_rente is not None:
        bvg = {"rente_jahr": args.bvg_rente, "rente_monat": round(args.bvg_rente/12),
               "warnungen": []}
    else:
        bvg = {"rente_jahr": 0, "rente_monat": 0, "warnungen": ["Keine BVG-Angabe."]}

    luecke = R.vorsorgeluecke(args.einkommen, ahv["rente_jahr"], bvg["rente_jahr"],
                              ersatzquote_ziel=args.ersatzquote or cfg["ersatzquote"])
    jahre = (cfg["lebenserwartung"] - (args.pensionsalter or 65))
    bedarf = R.kapitalbedarf(max(0, luecke["luecke_jahr"]), max(1, jahre),
                             rendite=args.rendite, teuerung=args.teuerung)
    ergebnis = {"ahv": ahv, "bvg": bvg, "luecke": luecke, "kapitalbedarf": bedarf,
                "annahmen": {"jahr": jahr, "pensionsalter": args.pensionsalter or 65,
                             "endalter": cfg["lebenserwartung"]}}
    if args.vermoegen is not None and luecke["luecke_jahr"] > 0:
        ergebnis["verzehr"] = R.kapitalverzehr_dauer(
            args.vermoegen, luecke["luecke_jahr"],
            rendite=args.rendite, teuerung=args.teuerung)

    _protokoll(args, ergebnis)
    if args.json:
        print(json.dumps(ergebnis, ensure_ascii=False, indent=2))
        return
    print(A.titel("Pensionierungs-Analyse"))
    print(f"  AHV-Rente            {A.chf0(ahv['rente_jahr'])} /Jahr")
    print(f"  BVG-Rente            {A.chf0(bvg['rente_jahr'])} /Jahr")
    print(f"  Zielrente            {A.chf0(luecke['zielrente_jahr'])} /Jahr")
    print(f"  → Vorsorgelücke      {A.chf0(luecke['luecke_jahr'])} /Jahr "
          f"(Deckungsgrad {A.prozent(luecke['deckungsgrad']) if luecke['deckungsgrad'] else '-'})")
    print(f"  → Kapitalbedarf      {A.chf0(bedarf['kapitalbedarf'])} "
          f"(für {bedarf['jahre']} Jahre)")
    if "verzehr" in ergebnis:
        print(f"  Vorhandenes Kapital reicht {ergebnis['verzehr']['dauer_jahre']} Jahre")
    print("\n  ⚠ Annahmen (Rendite/Teuerung/Pensionsalter) bestätigen; "
          "AHV/BVG sind Näherungen.")


def cmd_projektion(args):
    res = R.projektion(
        args.start_jahr, args.start_alter, args.pensionsalter, args.end_alter,
        lohn=args.lohn, ahv_rente=args.ahv_rente, pk_rente=args.pk_rente,
        ausgaben=args.ausgaben, vermoegen_start=args.vermoegen,
        rendite=args.rendite, teuerung=args.teuerung,
        steuersatz_eff=args.steuersatz, abzug_pauschale=args.abzug,
        steuer_anker=args.steuer_anker, ahv_alter=args.ahv_alter)
    _protokoll(args, res)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    print(A.titel("Finanz- und Steuerplanung — Jahresprojektion"))
    kopf = (f"{'Jahr':>5} {'Alt':>3} {'Erwerb':>10} {'AHV':>9} {'PK':>9} "
            f"{'Total':>10} {'Steuer*':>9} {'n.Steuer':>10} {'Ausgaben':>10} "
            f"{'Saldo':>9} {'Vermögen':>11}")
    print(kopf); print("─" * len(kopf))
    for r in res["rows"]:
        print(f"{r['jahr']:>5} {r['alter']:>3} {A.chf0(r['erwerb']):>10} "
              f"{A.chf0(r['rente_ahv']):>9} {A.chf0(r['rente_pk']):>9} "
              f"{A.chf0(r['total_einkommen']):>10} {A.chf0(r['steuer']):>9} "
              f"{A.chf0(r['einkommen_nach_steuer']):>10} {A.chf0(r['ausgaben']):>10} "
              f"{A.chf0(r['saldo']):>9} {A.chf0(r['vermoegen_ende']):>11}")
    print(f"\n  Vermögen Start {A.chf0(res['vermoegen_start'])} → "
          f"Ende {A.chf0(res['vermoegen_ende'])}")
    print("  * Steuer = Schätzung (siehe Warnung), nicht-kantonaler Tarif.")
    print(A.warnungen_block(res))


def _jahr(args):
    return getattr(args, "jahr", None) or S.laden()["jahr"]


# ───────────────────────── Parser ─────────────────────────
def build_parser():
    p = argparse.ArgumentParser(prog="finanzplanung",
                                description="Schweizer Finanzplanung / Vorsorge — normbasierter Rechner.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("set", help="Annahme setzen"); sp.add_argument("parameter"); sp.add_argument("wert"); sp.set_defaults(func=cmd_set)
    sp = sub.add_parser("reset", help="Annahmen zurücksetzen"); sp.set_defaults(func=cmd_reset)
    sp = sub.add_parser("show", help="Annahmen/Normwerte zeigen")
    sp.add_argument("--tabellen", action="store_true"); sp.add_argument("--annahmen", action="store_true")
    sp.set_defaults(func=cmd_show)

    def add_json(x):
        x.add_argument("--json", action="store_true")
        x.add_argument("--jahr", type=int)
        x.add_argument("--protokoll", default=None, help="Markdown-Rechennachweis (anhängen)")

    sp = sub.add_parser("ahv", help="AHV-Altersrente")
    sp.add_argument("--beitragsjahre", type=float, required=True)
    sp.add_argument("--einkommen", type=float, required=True, help="massg. Ø-Jahreseinkommen")
    add_json(sp); sp.set_defaults(func=cmd_ahv)

    sp = sub.add_parser("bvg-rente", help="BVG-Rente aus Altersguthaben")
    sp.add_argument("--guthaben", type=float, required=True)
    sp.add_argument("--umwandlungssatz", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_bvg_rente)

    sp = sub.add_parser("bvg-projektion", help="Altersguthaben bis Pensionierung")
    sp.add_argument("--guthaben", type=float, required=True)
    sp.add_argument("--koordlohn", type=float, required=True)
    sp.add_argument("--alter", type=int, required=True)
    sp.add_argument("--pension", type=int, required=True)
    sp.add_argument("--zins", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_bvg_projektion)

    sp = sub.add_parser("saeule3a", help="Säule-3a-Maximum")
    sp.add_argument("--einkommen", type=float, required=True)
    g = sp.add_mutually_exclusive_group()
    g.add_argument("--mit-pk", dest="mit_pk", action="store_true", default=True)
    g.add_argument("--ohne-pk", dest="mit_pk", action="store_false")
    add_json(sp); sp.set_defaults(func=cmd_saeule3a)

    sp = sub.add_parser("luecke", help="Vorsorgelücke")
    sp.add_argument("--einkommen", type=float, required=True)
    sp.add_argument("--ahv", type=float, required=True)
    sp.add_argument("--bvg", type=float, required=True)
    sp.add_argument("--ersatzquote", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_luecke)

    sp = sub.add_parser("kapitalbedarf", help="Kapital für Jahres-Lücke")
    sp.add_argument("--luecke", type=float, required=True)
    sp.add_argument("--jahre", type=int, required=True)
    sp.add_argument("--rendite", type=float, default=None)
    sp.add_argument("--teuerung", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_kapitalbedarf)

    sp = sub.add_parser("verzehr", help="Kapitalverzehr-Dauer")
    sp.add_argument("--kapital", type=float, required=True)
    sp.add_argument("--entnahme", type=float, required=True)
    sp.add_argument("--rendite", type=float, default=None)
    sp.add_argument("--teuerung", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_verzehr)

    sp = sub.add_parser("tragbarkeit", help="Tragbarkeit Wohneigentum")
    sp.add_argument("--wert", type=float, required=True)
    sp.add_argument("--hypothek", type=float, required=True)
    sp.add_argument("--einkommen", type=float, required=True)
    sp.add_argument("--zins", type=float, default=None)
    sp.add_argument("--nebenkosten", type=float, default=None)
    sp.add_argument("--amortisation", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_tragbarkeit)

    sp = sub.add_parser("plan", help="Vollständige Pensionierungs-Analyse")
    sp.add_argument("--einkommen", type=float, required=True, help="letztes Jahreseinkommen")
    sp.add_argument("--beitragsjahre", type=float, default=44)
    sp.add_argument("--ahv-einkommen", dest="ahv_einkommen", type=float, default=None)
    sp.add_argument("--bvg-guthaben", dest="bvg_guthaben", type=float, default=None)
    sp.add_argument("--bvg-rente", dest="bvg_rente", type=float, default=None)
    sp.add_argument("--umwandlungssatz", type=float, default=None)
    sp.add_argument("--pensionsalter", type=int, default=None)
    sp.add_argument("--vermoegen", type=float, default=None, help="freies Vorsorgekapital")
    sp.add_argument("--ersatzquote", type=float, default=None)
    sp.add_argument("--rendite", type=float, default=None)
    sp.add_argument("--teuerung", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("projektion", help="Mehrjährige Finanz- und Steuerplanung (Tabelle)")
    sp.add_argument("--start-jahr", dest="start_jahr", type=int, required=True)
    sp.add_argument("--start-alter", dest="start_alter", type=int, required=True)
    sp.add_argument("--pensionsalter", type=int, required=True)
    sp.add_argument("--end-alter", dest="end_alter", type=int, required=True)
    sp.add_argument("--lohn", type=float, default=0, help="Jahreslohn bis Pensionierung")
    sp.add_argument("--ahv-rente", dest="ahv_rente", type=float, default=0, help="AHV-Jahresrente ab AHV-Alter")
    sp.add_argument("--pk-rente", dest="pk_rente", type=float, default=0, help="2.-Säule-Jahresrente ab Pensionsalter")
    sp.add_argument("--ausgaben", type=float, default=0, help="Jahresausgaben (Lebenshaltung)")
    sp.add_argument("--vermoegen", type=float, default=0, help="freies Vermögen zu Beginn")
    sp.add_argument("--ahv-alter", dest="ahv_alter", type=int, default=65)
    sp.add_argument("--steuersatz", type=float, default=0.0, help="effektiver Steuersatz (Schätzung, Anker)")
    sp.add_argument("--abzug", type=float, default=0.0, help="pauschaler Abzug → steuerbares Einkommen")
    sp.add_argument("--steuer-anker", dest="steuer_anker", default=None, help="Quelle des Steuersatzes (z.B. 'Veranlagung 2024')")
    sp.add_argument("--rendite", type=float, default=None)
    sp.add_argument("--teuerung", type=float, default=None)
    add_json(sp); sp.set_defaults(func=cmd_projektion)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (R.RechenFehler, S.StateFehler) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
