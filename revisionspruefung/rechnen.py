"""
rechnen.py — Prüfkern eingeschränkte Revision (Schweizer Standard SER, OR Art. 728 ff.).

Deterministische Prüf-/Plausibilisierungs-Logik (Essenz eines Fastview-Prüftools):
formelle Abstimmungen, gesetzliche Schwellen, Kapitalschutz (Art. 725 ff.) und analytische
Vorjahresvergleiche. KEINE Kundendaten — alles aus der übergebenen Jahresrechnung.

WICHTIG: Das Tool stellt Sachverhalte fest und flaggt Auffälligkeiten — es ersetzt NICHT
das Prüfungsurteil. Befragungen und Detailprüfungen (SER) bleiben beim Revisor.
"""


class RechenFehler(Exception):
    pass


def _ok(b, betrag_a, betrag_b, tol=0.10):
    return abs(betrag_a - betrag_b) <= tol


def _check(bez, ok, befund, **werte):
    return {"pruefung": bez, "ok": bool(ok), "befund": befund, **werte}


def pruefe(cfg: dict) -> dict:
    bil = cfg.get("bilanz", {})
    er = cfg.get("er", {})
    gv = cfg.get("gewinnverwendung", {})
    basis = cfg.get("kennzahlen_basis", {})
    vj = cfg.get("vorjahr", {})        # {bilanz:{}, er:{}}
    checks = []

    # 1) Bilanz balanciert
    ta, tp = bil.get("total_aktiven"), bil.get("total_passiven")
    if ta is None or tp is None:
        raise RechenFehler("bilanz.total_aktiven / total_passiven fehlen.")
    checks.append(_check("Bilanz balanciert (Aktiven = Passiven)", _ok(True, ta, tp),
                         f"Aktiven {ta:.2f} / Passiven {tp:.2f}",
                         differenz=round(ta - tp, 2)))

    # 2) ER-Gewinn = in der Bilanz ausgewiesener Jahresgewinn
    er_gewinn = er.get("jahresgewinn")
    bil_gewinn = bil.get("jahresgewinn")
    if er_gewinn is not None and bil_gewinn is not None:
        checks.append(_check("Jahresgewinn ER = Jahresgewinn Bilanz",
                             _ok(True, er_gewinn, bil_gewinn),
                             f"ER {er_gewinn:.2f} / Bilanz {bil_gewinn:.2f}"))

    # 3) Bilanzgewinn = Vortrag + Jahresgewinn
    vortrag = bil.get("vortrag")
    bilanzgewinn = bil.get("bilanzgewinn", gv.get("bilanzgewinn"))
    if vortrag is not None and bil_gewinn is not None and bilanzgewinn is not None:
        checks.append(_check("Bilanzgewinn = Vortrag + Jahresgewinn",
                             _ok(True, vortrag + bil_gewinn, bilanzgewinn),
                             f"{vortrag:.2f} + {bil_gewinn:.2f} = {bilanzgewinn:.2f}"))

    # 4) Antrag Gewinnverwendung stimmt auf
    if gv:
        summe = (gv.get("zuweisung_reserven", 0) + gv.get("dividende", 0)
                 + gv.get("vortrag_neu", 0))
        bg = gv.get("bilanzgewinn", bilanzgewinn)
        if bg is not None:
            checks.append(_check("Gewinnverwendung = Bilanzgewinn",
                                 _ok(True, summe, bg),
                                 f"Zuweisung+Dividende+Vortrag {summe:.2f} = Bilanzgewinn {bg:.2f}"))

    # 4b) Ausschüttung vs. Liquidität / Going Concern (Art. 675/725 OR n.F.)
    # Eine Dividende darf nicht nur rechnerisch aus dem Bilanzgewinn zulässig sein,
    # sie muss auch liquide bezahlbar sein. Forderungen L+L sind erst nach Geldeingang
    # verfügbar und zählen hier NICHT als sofortige Deckung.
    dividende = gv.get("dividende")
    fm = bil.get("fluessige_mittel")
    if dividende and fm is not None:
        forderungen = bil.get("forderungen_llb")
        deckung = fm - dividende
        ok = dividende <= fm
        if ok:
            befund = (f"Dividende {dividende:.0f} aus flüssigen Mitteln {fm:.0f} bezahlbar "
                      f"(Rest {deckung:.0f}).")
        else:
            befund = (f"LIQUIDITÄT: Dividende {dividende:.0f} > flüssige Mittel {fm:.0f} "
                      f"(Unterdeckung {-deckung:.0f}). Ausschüttbarkeit und Fortführung "
                      f"prüfen (Art. 675/725 OR n.F.).")
            if forderungen is not None:
                befund += (f" Forderungen L+L {forderungen:.0f} stehen erst nach "
                           f"Geldeingang zur Verfügung.")
        checks.append(_check("Liquidität Ausschüttung (Art. 675/725 OR)", ok, befund,
                             dividende=round(dividende), fluessige_mittel=round(fm),
                             deckung=round(deckung)))

    # 5) Kapitalschutz Art. 725a/725b OR
    ek = bil.get("eigenkapital")
    ak = bil.get("aktienkapital", 0)
    ges_res = bil.get("gesetzliche_reserven", 0)
    if ek is not None:
        schwelle = (ak + ges_res) / 2
        ueberschuldung = ek < 0
        kapitalverlust = (ek < schwelle) and not ueberschuldung
        if ueberschuldung:
            befund = f"ÜBERSCHULDUNG: Eigenkapital {ek:.0f} < 0 → Art. 725b OR (Anzeige)."
        elif kapitalverlust:
            befund = (f"KAPITALVERLUST: EK {ek:.0f} < halbes AK+Reserven {schwelle:.0f} "
                      f"→ Art. 725a OR (Massnahmen).")
        else:
            befund = f"Kein Kapitalverlust: EK {ek:.0f} ≥ {schwelle:.0f}."
        checks.append(_check("Kapitalschutz (Art. 725a/725b OR)",
                             not ueberschuldung and not kapitalverlust, befund,
                             eigenkapital=round(ek), schwelle=round(schwelle)))

    # 6) Revisionsart (Schwellen Art. 727 / Opting-out 727a)
    bs = basis.get("bilanzsumme", ta)
    umsatz = basis.get("umsatz", er.get("nettoerloes"))
    fte = basis.get("fte")
    gross = [bs is not None and bs > 20_000_000,
             umsatz is not None and umsatz > 40_000_000,
             fte is not None and fte > 250]
    if sum(1 for x in gross if x) >= 2:
        art = "ordentliche Revision"
    elif fte is not None and fte < 10:
        art = "eingeschränkte Revision (Opting-out möglich bei Zustimmung aller Aktionäre)"
    else:
        art = "eingeschränkte Revision"
    checks.append(_check("Revisionsart (Art. 727/727a OR)", True, art,
                         bilanzsumme=bs, umsatz=umsatz, fte=fte))

    # 7) Analytische Prüfung — Vorjahresvergleich + Kennzahlen
    analytik = []
    schwelle_wesentlich = cfg.get("wesentlichkeit_prozent", 0.20)

    def vergleich(label, jetzt, frueher):
        if jetzt is None or not frueher:
            return
        delta = (jetzt - frueher) / abs(frueher) if frueher else None
        wesentlich = delta is not None and abs(delta) >= schwelle_wesentlich
        analytik.append({"position": label, "jahr": round(jetzt), "vorjahr": round(frueher),
                         "veraenderung": round(delta, 3) if delta is not None else None,
                         "wesentlich": wesentlich})

    vb, ve = vj.get("bilanz", {}), vj.get("er", {})
    vergleich("Nettoerlös", er.get("nettoerloes"), ve.get("nettoerloes"))
    vergleich("Bruttogewinn", er.get("bruttogewinn"), ve.get("bruttogewinn"))
    vergleich("EBITDA", er.get("ebitda"), ve.get("ebitda"))
    vergleich("Jahresgewinn", er.get("jahresgewinn"), ve.get("jahresgewinn"))
    vergleich("Personalaufwand", er.get("personalaufwand"), ve.get("personalaufwand"))
    vergleich("Total Aktiven", ta, vb.get("total_aktiven"))
    vergleich("Eigenkapital", ek, vb.get("eigenkapital"))

    kennzahlen = {}
    if er.get("nettoerloes"):
        if er.get("bruttogewinn") is not None:
            kennzahlen["bruttomarge"] = round(er["bruttogewinn"] / er["nettoerloes"], 4)
        if er.get("personalaufwand") is not None:
            kennzahlen["personalquote"] = round(abs(er["personalaufwand"]) / er["nettoerloes"], 4)

    formell_ok = all(c["ok"] for c in checks
                     if c["pruefung"].startswith(("Bilanz", "Jahresgewinn", "Bilanzgewinn",
                                                  "Gewinnverwendung", "Liquidität",
                                                  "Kapitalschutz")))
    wesentliche_abweichungen = [a for a in analytik if a["wesentlich"]]

    return {
        "firma": cfg.get("firma", ""), "jahr": cfg.get("jahr"),
        "checks": checks, "analytik": analytik, "kennzahlen": kennzahlen,
        "formell_ok": formell_ok,
        "wesentliche_abweichungen": [a["position"] for a in wesentliche_abweichungen],
        "gesamturteil": (
            "Formelle Prüfung ohne Beanstandung. "
            + ("Keine wesentlichen Vorjahresabweichungen. "
               if not wesentliche_abweichungen else
               "Wesentliche Vorjahresabweichungen festgestellt — gemäss SER mit Befragungen "
               "und Detailprüfungen zu klären, bevor das Prüfungsurteil abgegeben wird. ")
            if formell_ok else
            "FORMELLE BEANSTANDUNG — eine Pflichtprüfung (Abstimmung, Gewinnverwendung, "
            "Liquidität/Ausschüttung oder Kapitalschutz) ist nicht erfüllt; vor "
            "Berichterstattung klären."),
        "warnungen": [
            "Tool stellt Sachverhalte fest und flaggt Auffälligkeiten; das Prüfungsurteil "
            "(inkl. Befragungen/Detailprüfungen nach SER) bleibt beim zugelassenen Revisor.",
            "Bei Erstellung UND Revision durch dieselbe Firma: Unabhängigkeit/Selbstprüfung "
            "organisatorisch und personell sicherstellen (Art. 729 OR).",
        ],
    }
