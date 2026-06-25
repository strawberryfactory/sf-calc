"""Tests revisionspruefung. FIKTIVE Werte, keine Kundendaten."""

from revisionspruefung import rechnen as R

JR = {
    "firma": "Muster AG", "jahr": 2024,
    "bilanz": {"total_aktiven": 1000000, "total_passiven": 1000000,
               "aktienkapital": 100000, "gesetzliche_reserven": 50000,
               "eigenkapital": 500000, "vortrag": 50000,
               "jahresgewinn": 200000, "bilanzgewinn": 250000},
    "er": {"nettoerloes": 2000000, "bruttogewinn": 1500000, "ebitda": 400000,
           "jahresgewinn": 200000, "personalaufwand": -900000},
    "gewinnverwendung": {"bilanzgewinn": 250000, "zuweisung_reserven": 0,
                         "dividende": 200000, "vortrag_neu": 50000},
    "vorjahr": {"bilanz": {"total_aktiven": 900000, "eigenkapital": 300000},
                "er": {"nettoerloes": 1500000, "jahresgewinn": 100000}},
    "kennzahlen_basis": {"bilanzsumme": 1000000, "umsatz": 2000000, "fte": 30},
}


def _check(res, teil):
    return [c for c in res["checks"] if c["pruefung"].startswith(teil)][0]


def test_formelle_checks_ok():
    r = R.pruefe(JR)
    assert r["formell_ok"] is True
    assert _check(r, "Bilanz balanciert")["ok"]
    assert _check(r, "Gewinnverwendung")["ok"]        # 0+200000+50000 = 250000
    assert _check(r, "Bilanzgewinn")["ok"]            # 50000+200000 = 250000


def test_revisionsart_eingeschraenkt():
    assert "eingeschränkte" in _check(R.pruefe(JR), "Revisionsart")["befund"]


def test_kein_kapitalverlust():
    assert _check(R.pruefe(JR), "Kapitalschutz")["ok"]


def test_kapitalverlust_erkannt():
    jr = {**JR, "bilanz": {**JR["bilanz"], "eigenkapital": 60000}}   # < (100000+50000)/2 = 75000
    c = _check(R.pruefe(jr), "Kapitalschutz")
    assert c["ok"] is False and "KAPITALVERLUST" in c["befund"]


def test_ueberschuldung_erkannt():
    jr = {**JR, "bilanz": {**JR["bilanz"], "eigenkapital": -5000}}
    c = _check(R.pruefe(jr), "Kapitalschutz")
    assert c["ok"] is False and "ÜBERSCHULDUNG" in c["befund"]


def test_bilanz_differenz_faellt_auf():
    jr = {**JR, "bilanz": {**JR["bilanz"], "total_passiven": 990000}}
    assert _check(R.pruefe(jr), "Bilanz balanciert")["ok"] is False
    assert R.pruefe(jr)["formell_ok"] is False


def test_analytik_flaggt_wesentliche_abweichung():
    r = R.pruefe(JR)
    assert "Jahresgewinn" in r["wesentliche_abweichungen"]   # +100 %


def test_ordentliche_revision_bei_grossen_schwellen():
    jr = {**JR, "kennzahlen_basis": {"bilanzsumme": 25_000_000, "umsatz": 50_000_000, "fte": 300}}
    assert "ordentliche" in _check(R.pruefe(jr), "Revisionsart")["befund"]
