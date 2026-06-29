"""
Tests Unternehmens-Finanzplan. FIKTIVE Werte, keine Kundendaten.
Geprüft werden die Modell-Beziehungen (nicht Magic-Numbers): Bilanzabstimmung,
EBITDA/EBT/Steuer-Logik, Abschreibung, sinkendes Anlagevermögen/Darlehen.
"""

from unternehmensfinanzplan import rechnen as R

CFG = {
    "firma": "Muster AG",
    "jahre": [2025, 2026, 2027, 2028, 2029],
    "ertrag": [200000, 600000, 700000, 750000, 800000],
    "personalaufwand": [150000, 260000, 280000, 300000, 320000],
    "uebriger_aufwand": [70000, 100000, 100000, 100000, 100000],
    "investition": 400000, "nutzungsdauer": 5, "abschr_methode": "linear",
    "erstjahr_anteil": 0.5, "aktienkapital": 100000, "darlehen": 350000,
    "zins": 0.03, "amortisation": [0, 70000, 70000, 70000, 70000],
    "steuersatz": 0.13, "debitoren_quote": 0.10,
}


def approx(a, b, tol=1.0):
    return abs(a - b) <= tol


def test_bilanz_stimmt():
    r = R.mehrjahresplan(CFG)
    assert r["bilanz_ok"] is True
    assert all(abs(b["check"]) < 1.0 for b in r["bilanz"])


def test_er_beziehungen():
    r = R.mehrjahresplan(CFG)
    for er in r["erfolgsrechnung"]:
        # betrieblicher Aufwand OHNE Finanzaufwand (Zinsen)
        assert approx(er["aufwand_betrieb"],
                      er["personalaufwand"] + er["uebriger_aufwand"])
        assert approx(er["ebitda"], er["ertrag"] - er["aufwand_betrieb"])
        # EBITDA ist VOR Zinsen: Finanzaufwand erst zwischen EBIT und EBT
        assert approx(er["ebit"], er["ebitda"] - er["abschreibung"])
        assert approx(er["ebt"], er["ebit"] - er["finanzaufwand"])
        erwartete_steuer = round(0.13 * er["ebt"]) if er["ebt"] > 0 else 0
        assert approx(er["steuern"], erwartete_steuer, 1.0)
        assert approx(er["erfolg"], er["ebt"] - er["steuern"])


def test_ebitda_enthaelt_keinen_finanzaufwand():
    """Regressionsschutz: bei Zins > 0 darf EBITDA sich nicht ändern, wenn nur
    der Zinssatz variiert — der Finanzaufwand wirkt erst unterhalb EBIT."""
    cfg_a = dict(CFG, zins=0.0)
    cfg_b = dict(CFG, zins=0.10)
    ra = R.mehrjahresplan(cfg_a)["erfolgsrechnung"]
    rb = R.mehrjahresplan(cfg_b)["erfolgsrechnung"]
    for a, b in zip(ra, rb):
        assert approx(a["ebitda"], b["ebitda"])   # EBITDA zinsunabhängig
        assert approx(a["ebit"], b["ebit"])       # EBIT zinsunabhängig
        # EBT sinkt bei höherem Zins (Finanzaufwand grösser)
        assert b["finanzaufwand"] >= a["finanzaufwand"]


def test_dscr_und_nettoverschuldung():
    r = R.mehrjahresplan(CFG)
    k = r["kennzahlen"]
    gf = r["geldfluss"]
    # DSCR im Endjahr = (Cashflow operativ + Zins) / (Amortisation + Zins)
    letzt = gf[-1]
    er_letzt = r["erfolgsrechnung"][-1]
    schuldendienst = CFG["amortisation"][-1] + er_letzt["finanzaufwand"]
    erwartet = round((letzt["cashflow_operativ"] + er_letzt["finanzaufwand"]) / schuldendienst, 2)
    assert approx(k["dscr"], erwartet, 0.01)
    # Nettoverschuldung = Darlehen-Rest − Bank
    bi_letzt = r["bilanz"][-1]
    assert approx(k["nettoverschuldung"], bi_letzt["darlehen"] - bi_letzt["bank"], 1.0)


def test_abschreibung_linear_mit_erstjahr():
    r = R.mehrjahresplan(CFG)
    ab = [e["abschreibung"] for e in r["erfolgsrechnung"]]
    assert approx(ab[0], 40000)   # 400000/5 * 0.5
    assert approx(ab[1], 80000)   # 400000/5


def test_steuer_nur_auf_gewinn():
    r = R.mehrjahresplan(CFG)
    assert r["erfolgsrechnung"][0]["ebt"] < 0          # Anlaufjahr Verlust
    assert r["erfolgsrechnung"][0]["steuern"] == 0


def test_anlagevermoegen_und_darlehen_sinken():
    r = R.mehrjahresplan(CFG)
    av = [b["anlagevermoegen"] for b in r["bilanz"]]
    fk = [b["darlehen"] for b in r["bilanz"]]
    assert av[0] > av[-1]
    assert approx(av[-1], 40000)                        # 400000 - (40000 + 4*80000)
    assert approx(fk[-1], 70000)                        # 350000 - 4*70000


def test_auslastung_variante():
    cfg = dict(CFG); del cfg["ertrag"]
    cfg["auslastung"] = [0.5, 1.0, 1.0, 1.0, 1.0]; cfg["vollkapazitaet"] = 800000
    r = R.mehrjahresplan(cfg)
    assert r["erfolgsrechnung"][1]["ertrag"] == 800000
    assert r["erfolgsrechnung"][0]["ertrag"] == 400000
