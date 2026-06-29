"""
Tests für den Finanzplanungs-Rechner. Generische Werte, keine Kundendaten.
Ausführen:  python3 -m pytest finanzplanung/test_finanzplanung.py -q
"""

import math
import pytest
from finanzplanung import rechnen as R


def approx(a, b, tol=1.0):
    return abs(a - b) <= tol


# ── AHV21 Referenzalter ───────────────────────────────────────
def test_referenzalter_mann_65():
    assert R.ahv_referenzalter(1971, "mann")["referenzalter"] == 65.0


def test_referenzalter_frau_ab_1964_65():
    r = R.ahv_referenzalter(1971, "frau")
    assert r["referenzalter"] == 65.0
    assert r["uebergangsgeneration"] is False


def test_referenzalter_frau_bis_1960_64():
    assert R.ahv_referenzalter(1958, "frau")["referenzalter"] == 64.0


def test_referenzalter_frau_uebergang_gestaffelt():
    r = R.ahv_referenzalter(1962, "frau")
    assert r["referenzalter"] == 64.5            # 64 Jahre + 6 Monate
    assert r["referenzalter_monate"] == 6
    assert r["uebergangsgeneration"] is True


# ── AHV-Vorbezug ──────────────────────────────────────────────
def test_ahv_vorbezug_zwei_jahre_kuerzung():
    # Frau Jg. 1971 (Referenzalter 65), Bezug ab 63 → 2 Jahre Vorbezug → 13.6 %
    r = R.ahv_vorbezug(30_240, 1971, "frau", 63)
    assert approx(r["vorbezug_jahre"], 2.0, 0.01)
    assert approx(r["kuerzung_quote"], 0.136, 0.0001)
    assert approx(r["rente_gekuerzt_jahr"], 30_240 * (1 - 0.136), 1.0)


def test_ahv_vorbezug_uebergangsgeneration_warnt():
    r = R.ahv_vorbezug(30_240, 1965, "frau", 63)   # Jg. 1965 in 1961–1969
    assert any("Übergangsgeneration" in w for w in r["warnungen"])


def test_ahv_vorbezug_ohne_vorbezug_fehler():
    with pytest.raises(R.RechenFehler):
        R.ahv_vorbezug(30_240, 1971, "frau", 65)   # Bezug = Referenzalter


def test_tragbarkeit_folienbeispiel():
    # 1.2 Mio Wert, 900k Hypothek (300k EM), 180k Einkommen → 35.4 %, nicht tragbar
    r = R.tragbarkeit(1_200_000, 900_000, 180_000)
    assert approx(r["zins_kosten"], 45_000)
    assert approx(r["nebenkosten"], 12_000)
    assert approx(r["amortisation"], 6_664, 5)
    assert round(r["tragbarkeitsquote"], 3) == 0.354
    assert r["belehnung_ok"] is True          # 75 %
    assert r["tragbar"] is False


def test_bvg_rente_umwandlungssatz():
    r = R.bvg_rente(500_000)                   # 500'000 × 6.8 %
    assert approx(r["rente_jahr"], 34_000)
    assert r["umwandlungssatz"] == 0.068


def test_ahv_max_ab_grenzbetrag():
    # Einkommen über oberem Grenzbetrag (88'200) + volle Beitragsjahre → Maximalrente
    r = R.ahv_altersrente(44, 100_000)
    assert approx(r["rente_jahr"], 2450 * 12)  # 29'400
    assert r["skalenfaktor"] == 1.0


def test_ahv_teilrente_skala():
    r = R.ahv_altersrente(22, 100_000)         # halbe Beitragsdauer
    assert approx(r["rente_jahr"], 2450 * 12 * 0.5, 5)


def test_ahv_min_bei_tiefem_einkommen():
    r = R.ahv_altersrente(44, 10_000)          # unter min. Jahresrente
    assert approx(r["rente_jahr"], 1225 * 12)  # 14'700


def test_vorsorgeluecke():
    r = R.vorsorgeluecke(100_000, 29_400, 34_000, ersatzquote_ziel=0.80)
    assert approx(r["zielrente_jahr"], 80_000)
    assert approx(r["luecke_jahr"], 80_000 - 63_400)


def test_kapitalbedarf_realrate():
    # bei Rendite==Teuerung ist die reale Rendite 0 → PV = Lücke × Jahre
    r = R.kapitalbedarf(20_000, 25, rendite=0.01, teuerung=0.01)
    assert approx(r["kapitalbedarf"], 20_000 * 25)


def test_kapitalverzehr_endlich():
    r = R.kapitalverzehr_dauer(200_000, 30_000, rendite=0.015, teuerung=0.01)
    assert r["reicht_unbegrenzt"] is False
    assert 1 <= r["dauer_jahre"] <= 10


def test_saeule3a_ohne_pk_deckel():
    r = R.saeule_3a_max(False, 300_000)        # 20 % = 60'000, aber Deckel 35'280
    assert approx(r["max_beitrag"], 35_280)


def test_bvg_projektion_waechst():
    r = R.bvg_guthaben_projektion(300_000, 50_000, 50, 65)
    assert r["guthaben_pension"] > 300_000


def test_projektion_lohn_renten_uebergang():
    r = R.projektion(start_jahr=2026, start_alter=60, pensionsalter=62, end_alter=66,
                     lohn=100_000, ahv_rente=24_000, pk_rente=40_000, ausgaben=70_000,
                     vermoegen_start=300_000, rendite=0.0, teuerung=0.0,
                     steuersatz_eff=0.10, abzug_pauschale=0.0, ahv_alter=65)
    rows = {x["alter"]: x for x in r["rows"]}
    assert rows[60]["erwerb"] == 100_000 and rows[60]["rente_pk"] == 0
    assert rows[62]["erwerb"] == 0 and rows[62]["rente_pk"] == 40_000   # Pensionierung
    assert rows[64]["rente_ahv"] == 0 and rows[65]["rente_ahv"] == 24_000  # AHV ab 65
    assert rows[60]["steuer"] == 10_000 and rows[60]["steuer_geschaetzt"] is True


def test_projektion_steuer_null_ohne_satz():
    r = R.projektion(2026, 60, 62, 63, lohn=100_000, ahv_rente=0, pk_rente=0,
                     ausgaben=0, vermoegen_start=0, rendite=0.0, teuerung=0.0)
    assert all(x["steuer"] == 0 for x in r["rows"])
    assert any("vor Steuern" in w for w in r["warnungen"])
