"""
ausgabe.py — Konsolen- und Markdown-Ausgabe der Kabelberechnung.
"""

from datetime import datetime

from . import tabellen as T
from . import rechnen


def _kopf(cfg, abg, leistung_kw):
    """Gemeinsame Kennzahlen-Zeilen (als Liste von (label, wert))."""
    return [
        ("System", abg["sys_bez"]),
        ("Kabel", abg["kabel_bez"]),
        ("Verlegeart", f"{cfg['verlegeart']} — {T.VERLEGEARTEN[cfg['verlegeart']]}"),
        ("Strom Ib", f"{cfg['strom']:.2f} A"),
        ("Laenge", f"{cfg['laenge']:.1f} m"),
        ("cos phi", f"{abg['cosphi']:.3f}"),
        ("Leistung", f"{leistung_kw:.2f} kW"),
        ("Umgebung", f"{cfg['umgebung']:.0f} C"),
        ("Stromkreise", f"{cfg['stromkreise']} (k_haeuf {T.k_haeufung(cfg['stromkreise']):.2f})"),
        ("Temp-Faktor", f"{T.k_temp(abg['isolation'], cfg['umgebung']):.3f}"),
        ("Zul. dU", f"{cfg['max_du']:.2f} %"),
    ]


def konsole(cfg, abg, empfehlung, zeilen):
    p_kw = rechnen.leistung_kw(cfg["strom"], cfg["spannung"], abg["cosphi"])
    print()
    for label, wert in _kopf(cfg, abg, p_kw):
        print(f"{label+':':<14}{wert}")
    print()

    if empfehlung:
        print("Empfehlung:")
        print(f"  Querschnitt:    {empfehlung['s']} mm2")
        print(f"  Iz (korr.):     {empfehlung['iz']:.1f} A  (Tab. {empfehlung['iz30']:.1f} A @30C)")
        print(f"  Spannungsfall:  {empfehlung['du']:.2f} %")
    else:
        print("Kein Querschnitt erfuellt thermisch UND Spannungsfall im Tabellenbereich.")
    print()

    print("Uebersicht:")
    print("  mm2    Iz[A]   dU[%]   Thermik   dU")
    for z in zeilen:
        th = "OK" if z["therm_ok"] else "NEIN"
        du = "OK" if z["du_ok"] else "NEIN"
        print(f"  {str(z['s']).rjust(4)}  {z['iz']:>6.1f}  {z['du']:>6.2f}   {th:<7}  {du}")
    print()


def markdown(cfg, abg, empfehlung, zeilen, projekt, verteilung="", klemme="",
             verfasser="Samuel Hangartner"):
    """Erzeugt das piag-pdf-kompatible Markdown (Frontmatter + Body)."""
    p_kw = rechnen.leistung_kw(cfg["strom"], cfg["spannung"], abg["cosphi"])
    heute = datetime.now()
    datum = heute.strftime("%d.%m.%Y")

    teile = ["Kabelberechnung"]
    if verteilung:
        teile.append(verteilung)
    if klemme:
        teile.append(f"Klemme {klemme}")
    titel = " — ".join(teile)

    fm = [
        "---",
        f'projekt: "{projekt}"',
        f'titel: "{titel}"',
        'version: "1.0"',
        f'datum: "{datum}"',
        'status: "in Arbeit"',
        f'dokument: "{dateiname(cfg, projekt, verteilung, klemme, heute, suffix=False)}"',
        f'verfasser: "{verfasser}"',
        'verfasser_rolle: "GEE"',
        "---",
        "",
    ]

    body = [
        f"# Kabelberechnung {projekt}",
        "",
        "## Eingaben und Annahmen",
        "",
        "| Grösse | Wert |",
        "|--------|------|",
    ]
    for label, wert in _kopf(cfg, abg, p_kw):
        body.append(f"| {label} | {wert} |")
    if verteilung or klemme:
        body.append(f"| Verteilung | {verteilung or '—'} |")
        body.append(f"| Klemme | {klemme or '—'} |")
    body += ["", "## Ergebnis", ""]
    if empfehlung:
        body += [
            f"**Empfohlener Querschnitt: {empfehlung['s']} mm²**",
            "",
            f"- Strombelastbarkeit Iz (korrigiert): {empfehlung['iz']:.1f} A "
            f"(Tabellenwert {empfehlung['iz30']:.1f} A bei 30 °C)",
            f"- Spannungsfall: {empfehlung['du']:.2f} % (zulässig {cfg['max_du']:.2f} %)",
        ]
    else:
        body.append("Kein Querschnitt erfüllt beide Nachweise im Tabellenbereich.")
    body += ["", "## Übersicht aller Querschnitte", "",
             "| mm² | Iz korr. [A] | ΔU [%] | Thermik | Spannungsfall |",
             "|-----|------|------|---------|---------------|"]
    for z in zeilen:
        th = "OK" if z["therm_ok"] else "✗"
        du = "OK" if z["du_ok"] else "✗"
        body.append(f"| {z['s']} | {z['iz']:.1f} | {z['du']:.2f} | {th} | {du} |")
    body += ["", "---", "",
             "_Berechnung nach NIN / IEC 60364-5-52. Thermischer Nachweis "
             "(Ib ≤ Iz·k_temp·k_häufung) und Spannungsfall (inkl. Reaktanz). "
             "Vordimensionierung — Kurzschluss-/Abschaltnachweis separat._"]

    return "\n".join(fm + body) + "\n"


def dateiname(cfg, projekt, verteilung, klemme, dt=None, suffix=True):
    """3142_YYMMdd_Kabelberechnung[_Verteilung][_Klemme]"""
    dt = dt or datetime.now()
    teile = [str(projekt), dt.strftime("%y%m%d"), "Kabelberechnung"]
    if verteilung:
        teile.append(_slug(verteilung))
    if klemme:
        teile.append(_slug(klemme))
    name = "_".join(teile)
    return name + ".md" if suffix else name


def _slug(text):
    return "".join(c if c.isalnum() else "" for c in text.replace(" ", ""))
