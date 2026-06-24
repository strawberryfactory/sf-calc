"""
rechnen.py — Rechenkern Unternehmens-Finanzplan (3-Statement-Modell, OR-konform).

Generisch, keine Kundendaten. Aus Annahmen (Investition/Abschreibung, Finanzierung,
je Jahr Ertrag + Aufwand, Steuersatz) entstehen deterministisch:
  Plan-Erfolgsrechnung · Plan-Bilanz · Geldfluss/Liquidität · Kennzahlen.

Bilanz-Logik (selbstabstimmend, Bilanzcheck = 0):
  Anlagevermögen = Investition − kumulierte Abschreibung
  Darlehen-Rest  = Darlehen − kumulierte Amortisation
  Eigenkapital   = Aktienkapital + kumulierter Gewinn
  Bank (Residual)= (Darlehen-Rest + Eigenkapital) − Anlagevermögen − Debitoren
  → Aktiven (Bank+Debitoren+Anlagevermögen) = Passiven (Darlehen+Eigenkapital)
"""


class RechenFehler(Exception):
    pass


def _abschreibung_reihe(investition, nutzungsdauer, methode, jahre, erstjahr_anteil):
    """Abschreibungsbetrag pro Planjahr (linear oder degressiv)."""
    reihe = []
    if methode == "linear":
        jahresrate = investition / nutzungsdauer
        for i in range(jahre):
            if i >= nutzungsdauer:
                reihe.append(0.0)
            elif i == 0:
                reihe.append(jahresrate * erstjahr_anteil)
            else:
                reihe.append(jahresrate)
    elif methode == "degressiv":
        satz = 1.0 / nutzungsdauer * 2  # doppelt-degressiv
        rest = investition
        for i in range(jahre):
            rate = rest * satz * (erstjahr_anteil if i == 0 else 1.0)
            rate = min(rate, rest)
            reihe.append(rate)
            rest -= rate
    else:
        raise RechenFehler(f"Unbekannte Abschreibungsmethode '{methode}'.")
    return reihe


def mehrjahresplan(cfg: dict) -> dict:
    """Erzeugt Plan-ER, Plan-Bilanz, Geldfluss und Kennzahlen aus der Konfiguration."""
    jahre_labels = cfg.get("jahre")
    if not jahre_labels:
        raise RechenFehler("'jahre' (Liste der Planjahre) fehlt.")
    n = len(jahre_labels)

    def reihe(key, default=0.0):
        v = cfg.get(key, default)
        if isinstance(v, list):
            if len(v) != n:
                raise RechenFehler(f"'{key}' muss {n} Werte haben (hat {len(v)}).")
            return [float(x) for x in v]
        return [float(v)] * n

    # Ertrag: direkt, oder Auslastung × Vollkapazität
    if "ertrag" in cfg:
        ertrag = reihe("ertrag")
    elif "auslastung" in cfg and "vollkapazitaet" in cfg:
        ausl = reihe("auslastung"); voll = float(cfg["vollkapazitaet"])
        ertrag = [a * voll for a in ausl]
    else:
        raise RechenFehler("Ertrag fehlt: 'ertrag' ODER 'auslastung'+'vollkapazitaet'.")

    personal = reihe("personalaufwand")
    uebrig = reihe("uebriger_aufwand")
    steuersatz = float(cfg.get("steuersatz", 0.0))
    debi_quote = float(cfg.get("debitoren_quote", 0.0))

    investition = float(cfg.get("investition", 0.0))
    nutzungsdauer = int(cfg.get("nutzungsdauer", 1))
    methode = cfg.get("abschr_methode", "linear")
    erstjahr_anteil = float(cfg.get("erstjahr_anteil", 1.0))
    abschr = _abschreibung_reihe(investition, nutzungsdauer, methode, n, erstjahr_anteil)

    aktienkapital = float(cfg.get("aktienkapital", 0.0))
    darlehen = float(cfg.get("darlehen", 0.0))
    zins = float(cfg.get("zins", 0.0))
    # Amortisation: vorgegeben, sonst automatisch parallel zur Abschreibung
    if "amortisation" in cfg:
        amort = reihe("amortisation")
    else:
        amort = list(abschr)

    er_rows, bi_rows, gf_rows = [], [], []
    kumul_abschr = kumul_amort = kumul_gewinn = 0.0
    darlehen_anfang = darlehen
    bank_vorjahr = 0.0

    for i in range(n):
        finanzaufwand = zins * darlehen_anfang * (erstjahr_anteil if i == 0 else 1.0)
        aufwand_betrieb = personal[i] + uebrig[i] + finanzaufwand
        ebitda = ertrag[i] - aufwand_betrieb
        ebt = ebitda - abschr[i]
        steuern = steuersatz * ebt if ebt > 0 else 0.0
        erfolg = ebt - steuern

        kumul_abschr += abschr[i]
        kumul_amort += amort[i]
        kumul_gewinn += erfolg
        anlagevermoegen = max(0.0, investition - kumul_abschr)
        darlehen_rest = max(0.0, darlehen - kumul_amort)
        eigenkapital = aktienkapital + kumul_gewinn
        debitoren = debi_quote * ertrag[i]
        bank = (darlehen_rest + eigenkapital) - anlagevermoegen - debitoren

        er_rows.append({
            "jahr": jahre_labels[i], "ertrag": round(ertrag[i]),
            "personalaufwand": round(personal[i]), "uebriger_aufwand": round(uebrig[i]),
            "finanzaufwand": round(finanzaufwand), "aufwand_betrieb": round(aufwand_betrieb),
            "ebitda": round(ebitda), "abschreibung": round(abschr[i]),
            "ebt": round(ebt), "steuern": round(steuern), "erfolg": round(erfolg),
        })
        bi_rows.append({
            "jahr": jahre_labels[i], "bank": round(bank), "debitoren": round(debitoren),
            "anlagevermoegen": round(anlagevermoegen),
            "total_aktiven": round(bank + debitoren + anlagevermoegen),
            "darlehen": round(darlehen_rest), "aktienkapital": round(aktienkapital),
            "kumulierter_gewinn": round(kumul_gewinn), "eigenkapital": round(eigenkapital),
            "total_passiven": round(darlehen_rest + eigenkapital),
            "check": round((bank + debitoren + anlagevermoegen) - (darlehen_rest + eigenkapital), 2),
        })
        gf_rows.append({
            "jahr": jahre_labels[i],
            "cashflow_operativ": round(erfolg + abschr[i] - (debitoren - (gf_rows[-1]["_debi"] if gf_rows else 0))),
            "investition": round(-investition if i == 0 else 0),
            "finanzierung": round((aktienkapital + darlehen if i == 0 else 0) - amort[i]),
            "veraenderung_bank": round(bank - bank_vorjahr),
            "bank_ende": round(bank), "_debi": debitoren,
        })
        darlehen_anfang = darlehen_rest
        bank_vorjahr = bank

    for r in gf_rows:
        r.pop("_debi", None)

    eingeschwungen = er_rows[-1]
    kennzahlen = {
        "ebitda_marge": round(eingeschwungen["ebitda"] / eingeschwungen["ertrag"], 4) if eingeschwungen["ertrag"] else None,
        "ebt_marge": round(eingeschwungen["ebt"] / eingeschwungen["ertrag"], 4) if eingeschwungen["ertrag"] else None,
        "eigenkapitalquote": round(bi_rows[-1]["eigenkapital"] / bi_rows[-1]["total_passiven"], 4) if bi_rows[-1]["total_passiven"] else None,
    }
    return {
        "firma": cfg.get("firma", ""), "jahre": jahre_labels,
        "erfolgsrechnung": er_rows, "bilanz": bi_rows, "geldfluss": gf_rows,
        "kennzahlen": kennzahlen,
        "bilanz_ok": all(abs(r["check"]) < 1.0 for r in bi_rows),
        "warnungen": ["Steuer = Gewinnsteuersatz als Annahme (kein kantonaler Tarif); "
                      "Planzahlen beruhen auf Annahmen und sind keine Zusicherung."],
    }
