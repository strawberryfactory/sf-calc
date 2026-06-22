"""
ausgabe.py — Konsolen- und JSON-Ausgabe der Kurzschlussberechnung.

Der JSON-Kontrakt (json_kontrakt) ist die Schnittstelle zum kabelberechnung-
Tool:  kurzschlussberechnung --json | kabelberechnung calc ...
"""

import math

from . import kern


def _fmt(v, fmt='.3f'):
    if v is None:
        return '-'
    if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
        return '-'
    return format(v, fmt)


def _print_grundimpedanzen(grund):
    print(f"    Netz:   RQ = {grund['RQ']:.4f}  XQ = {grund['XQ']:.4f}  "
          f"ZQ = {grund['ZQ']:.4f} mOhm")
    print(f"    Trafo:  RT = {grund['RT']:.3f}  XT = {grund['XT']:.3f}  "
          f"ZT = {grund['ZT']:.3f} mOhm")
    print(f"    Leitungstemperatur: {grund['leitungs_temp_c']} C")


def _print_knoten_tabelle(knoten, titel):
    print(f"\n  {titel}")
    print("  " + "-" * 92)
    print(f"  {'Knoten':<32} {'Ik3[kA]':>8} {'ip3[kAp]':>9} {'Ith3[kA]':>9}"
          f" {'Ik1[kA]':>8} {'Tkzul3[s]':>10} {'Ta[s]':>7} {'I2t':>5}")
    print("  " + "-" * 92)
    for kn in knoten:
        t3, ta = kn['Tkzul3'], kn['Ta_s']
        check = '-'
        if t3 is not None and ta is not None:
            check = 'OK' if t3 >= ta else 'NEIN'
        print(f"  {kn['label'][:32]:<32} {kn['Ik3']/1000:>8.2f}"
              f" {kn['ip3']/1000:>9.2f} {kn['Ith3']/1000:>9.2f}"
              f" {kn['Ik1']/1000:>8.2f} {_fmt(t3):>10} {ta:>7.3f} {check:>5}")
    print("  " + "-" * 92)


def konsole(ergebnis):
    cfg = ergebnis['config']
    q, t = cfg['quelle'], cfg['trafo']
    print("=" * 72)
    print("Kurzschlussberechnung nach IEC 60909-0")
    print("=" * 72)
    print(f"Netz:   Un = {q['Un_V']:g} V, Sk\" = {q['Sk_MVA']:g} MVA")
    print(f"Trafo:  SrT = {t['SrT_kVA']:g} kVA, uk = {t['uk_pct']:g} %, "
          f"ur = {t['ur_pct']:g} %")
    print(f"Kaskade: {len(cfg.get('leitungen', []))} Leitung(en)")

    print(f"\nIKMAX (cmax = {kern.C_MAX_LV:.2f}, kalte Leitung {kern.TEMP_KALT_C} C):")
    _print_grundimpedanzen(ergebnis['grundimpedanzen_max'])
    _print_knoten_tabelle(ergebnis['knoten_max'], "Fehlerorte (Ikmax):")

    print(f"\nIKMIN (cmin = {kern.C_MIN_LV:.2f}, heisse Leitung {kern.TEMP_BETRIEB_HEISS_C} C):")
    _print_grundimpedanzen(ergebnis['grundimpedanzen_min'])
    _print_knoten_tabelle(ergebnis['knoten_min'], "Fehlerorte (Ikmin):")
    print()


def json_kontrakt(ergebnis, leitung_index=None):
    """
    Baut den JSON-Kontrakt fuer den Pipe nach kabelberechnung.

    Bezug ist die zu schuetzende Leitung (Default: letzte Leitung der Kaskade).
    Fuer den I2t-Nachweis am Kabel ist der hoechste Strom massgebend -> Ik3max
    am ANFANG der Leitung (= Knoten davor), nicht am Fehlerort am Ende.

    {ik_max_ka, ik_min_ka, t_aus_s, ort}
      ik_max_ka : Ik3max am Leitungsanfang (worst case I2t)
      ik_min_ka : Ik1min am Leitungsende (Auslesicherheit)
      t_aus_s   : Ausloesezeit der Schutzeinrichtung dieser Leitung
      ort       : Bezeichnung der Leitung
    """
    knoten_max = ergebnis['knoten_max']
    knoten_min = ergebnis['knoten_min']
    n_leit = len(ergebnis['config'].get('leitungen', []))

    if n_leit == 0:
        # nur Sammelschiene
        return {"ik_max_ka": round(knoten_max[0]['Ik3'] / 1000, 3),
                "ik_min_ka": round(knoten_min[0]['Ik1'] / 1000, 3),
                "t_aus_s": knoten_max[0]['Ta_s'],
                "ort": knoten_max[0]['label']}

    L = n_leit if leitung_index is None else leitung_index   # 1-basiert
    L = max(1, min(L, n_leit))
    anfang = knoten_max[L - 1]   # Knoten VOR der Leitung -> hoechster Ik
    ende_max = knoten_max[L]
    ende_min = knoten_min[L]
    return {
        "ik_max_ka": round(anfang['Ik3'] / 1000, 3),
        "ik_min_ka": round(ende_min['Ik1'] / 1000, 3),
        "t_aus_s": ende_max['Ta_s'],
        "ort": ende_max['label'],
    }
