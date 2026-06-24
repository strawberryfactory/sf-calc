"""Tests Versicherungsvergleich. Generische Werte, keine Kundendaten."""

from versicherungsvergleich import rechnen as R, tabellen as T

CFG = {
    "ausschreibung": {"firma": "Test GmbH", "sparten": [
        {"name": "Sachversicherung", "versicherungssumme": 150000, "selbstbehalt": 200},
        {"name": "IT-Haftpflicht", "versicherungssumme": 5000000, "selbstbehalt": 200},
        {"name": "MF AG 40326"}]},
    "offerten": [
        {"versicherer": "Allianz", "status": "offeriert", "positionen": [
            {"sparte": "Sachversicherung", "praemie": 1000, "versicherungssumme": 150000, "selbstbehalt": 200},
            {"sparte": "MF AG 40326", "praemie": 1500}]},
        {"versicherer": "AXA", "status": "offeriert", "positionen": [
            {"sparte": "Sachversicherung", "praemie": 2000, "versicherungssumme": 150000, "selbstbehalt": 500},
            {"sparte": "IT-Haftpflicht", "praemie": 3000, "versicherungssumme": 5000000, "selbstbehalt": 200},
            {"sparte": "MF AG 40326", "praemie": 1600}]},
        {"versicherer": "Mobiliar", "status": "verzichtet", "positionen": []},
    ],
}


def _summe(res, v):
    return [s for s in res["summen"] if s["versicherer"] == v][0]


def test_stempel_befreiung():
    assert T.stempel_satz("Sachversicherung") == 0.05
    assert T.stempel_satz("IT-Haftpflicht") == 0.05
    assert T.stempel_satz("KTG Krankentaggeld") == 0.0
    assert T.stempel_satz("UVG") == 0.0


def test_stempel_und_total():
    r = R.vergleiche(CFG)
    axa = _summe(r, "AXA")           # 2000+3000+1600 = 6600, Stempel 5% = 330
    assert axa["summe_praemien"] == 6600
    assert axa["stempelabgabe"] == 330
    assert axa["total_inkl_stempel"] == 6930


def test_ranking_und_guenstigster():
    r = R.vergleiche(CFG)
    # Allianz 2500*1.05=2625 < AXA 6930 → Allianz Rang 1 (aber unvollständig)
    assert r["ranking"][0]["versicherer"] == "Allianz"
    assert r["guenstigster"] == "Allianz"


def test_vollstaendigkeit():
    r = R.vergleiche(CFG)
    assert _summe(r, "Allianz")["vollstaendig"] is False        # IT-Haftpflicht fehlt
    assert "IT-Haftpflicht" in _summe(r, "Allianz")["fehlende_sparten"]
    assert _summe(r, "AXA")["vollstaendig"] is True


def test_verzicht():
    r = R.vergleiche(CFG)
    assert "Mobiliar" in r["verzichtet"]
    assert all(rk["versicherer"] != "Mobiliar" for rk in r["ranking"])


def test_deckungsabweichung_selbstbehalt():
    r = R.vergleiche(CFG)
    abw = [d for d in r["deckungs_abweichungen"] if d["versicherer"] == "AXA"]
    assert any(d["feld"] == "Selbstbehalt" and d["offeriert"] == 500 for d in abw)


def test_unterdeckung_versicherungssumme():
    cfg = {"ausschreibung": {"sparten": [{"name": "Sachversicherung", "versicherungssumme": 150000}]},
           "offerten": [{"versicherer": "X", "status": "offeriert",
                         "positionen": [{"sparte": "Sachversicherung", "praemie": 500, "versicherungssumme": 100000}]}]}
    r = R.vergleiche(cfg)
    assert any(d["feld"] == "Versicherungssumme" for d in r["deckungs_abweichungen"])
