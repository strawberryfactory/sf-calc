"""
rechnen.py — Rechenkern der Kabelberechnung.

Zwei Nachweise nach NIN / IEC 60364:
  1. Thermisch:     Ib <= Iz_korrigiert = Iz,30C * k_temp * k_haeufung
  2. Spannungsfall: dU% <= max_du
                    3-phasig: dU = sqrt(3) * I * L * (R'*cos + X'*sin)
                    1-phasig: dU = 2     * I * L * (R'*cos + X'*sin)
                    R' temperaturkorrigiert auf Betriebstemperatur.
"""

import math

from . import tabellen as T


class RechenFehler(Exception):
    """Fachlicher Fehler (z.B. Verlegeart-Daten nicht verifiziert)."""


def leistung_kw(strom_a, spannung_v, cos_phi):
    """Wirkleistung [kW] je nach Spannungssystem."""
    sys = T.SPANNUNGEN[spannung_v]
    p_w = sys["faktor"] * spannung_v * strom_a * cos_phi
    return p_w / 1000.0


def r_prime_betrieb(querschnitt, betriebstemp_c=70):
    """R'(T) = R'(20) * [1 + alpha*(T-20)]  — Cu."""
    r20 = T.R_PRIME_CU[querschnitt]
    return r20 * (1 + T.ALPHA_CU * (betriebstemp_c - 20))


def spannungsfall_prozent(strom_a, laenge_m, cos_phi, querschnitt, spannung_v,
                          betriebstemp_c=70):
    """Relativer Spannungsfall [%] inkl. Reaktanz."""
    sys = T.SPANNUNGEN[spannung_v]
    r = r_prime_betrieb(querschnitt, betriebstemp_c)      # Ohm/km
    x = T.X_PRIME_CU[querschnitt]                          # Ohm/km
    sin_phi = math.sqrt(max(0.0, 1 - cos_phi ** 2))
    # Vorfaktor: sqrt(3) bei 3-phasig (Aussenleiterspannung), 2 bei 1-phasig (Hin+Rueck)
    vorfaktor = sys["faktor"] if sys["phasen"] == 3 else 2.0
    delta_u = vorfaktor * strom_a * (laenge_m / 1000.0) * (r * cos_phi + x * sin_phi)
    return (delta_u / spannung_v) * 100.0


def iz_korrigiert(iz_30, isolation, umgebung_c, anzahl_stromkreise):
    """Iz bei realer Umgebung/ Haeufung."""
    return iz_30 * T.k_temp(isolation, umgebung_c) * T.k_haeufung(anzahl_stromkreise)


def dimensioniere(strom_a, laenge_m, cos_phi, spannung_v, verlegeart,
                  material="Cu", isolation="PVC", umgebung_c=30,
                  anzahl_stromkreise=1, max_du=3.0, betriebstemp_c=70):
    """
    Liefert (empfehlung, alle_zeilen).
      empfehlung = kleinster Querschnitt, der thermisch UND dU besteht (oder None)
      alle_zeilen = Liste je Querschnitt mit Detailwerten
    Wirft RechenFehler, wenn fuer die Kombination keine verifizierte Iz-Tabelle da ist.
    """
    sys = T.SPANNUNGEN[spannung_v]
    n_leiter = sys["n_leiter"]

    tab = T.iz_tabelle(verlegeart, material, isolation, n_leiter)
    if tab is None:
        status = T.IZ_STATUS.get((verlegeart, material, isolation, n_leiter), "nicht eingepflegt")
        raise RechenFehler(
            f"Keine verifizierte Iz-Tabelle fuer Verlegeart {verlegeart}, "
            f"{material}/{isolation}, {n_leiter} belastete Leiter ({status}). "
            f"Verfuegbar: 'kabelberechnung show --tabellen'."
        )

    zeilen = []
    for s in sorted(tab):
        iz30 = tab[s]
        izk = iz_korrigiert(iz30, isolation, umgebung_c, anzahl_stromkreise)
        du = spannungsfall_prozent(strom_a, laenge_m, cos_phi, s, spannung_v, betriebstemp_c)
        therm_ok = strom_a <= izk
        du_ok = du <= max_du
        zeilen.append({
            "s": s, "iz30": iz30, "iz": izk, "du": du,
            "therm_ok": therm_ok, "du_ok": du_ok, "ok": therm_ok and du_ok,
        })

    empfehlung = next((z for z in zeilen if z["ok"]), None)
    return empfehlung, zeilen


# ─────────────────────────────────────────────────────────────
# Adiabatischer Kurzschluss-Nachweis am Einzelleiter
# ─────────────────────────────────────────────────────────────
def adiabatischer_nachweis(ik_a, querschnitt, k_faktor, t_aus_s=None):
    """
    Prueft, ob EIN Leiter mit Querschnitt S den Kurzschlussstrom Ik thermisch
    aushaelt (IEC 60364-5-54, adiabatische Naeherung):

        zulaessige Zeit   t_zul = (k * S / Ik)^2
        Mindestquerschnitt S_min = Ik * sqrt(t_aus) / k

    Bei Parallelverlegung MUSS hier der VOLLE Ik eingesetzt werden, nicht Ik/n:
    ein Fehler in einem einzelnen Parallelkabel fuehrt den ganzen Strom ueber
    diesen einen Leiter (NIN 5.2.3 / IEC 60364-4-43 §434).

    Rueckgabe (dict):
      t_zul      zulaessige Kurzschlussdauer [s] fuer dieses S bei diesem Ik
      s_min      noetiger Mindestquerschnitt [mm2] (nur wenn t_aus gegeben)
      ok         True, wenn t_zul >= t_aus (nur wenn t_aus gegeben, sonst None)
    """
    t_zul = (k_faktor * querschnitt / ik_a) ** 2
    s_min = None
    ok = None
    if t_aus_s is not None:
        s_min = ik_a * math.sqrt(t_aus_s) / k_faktor
        ok = t_zul >= t_aus_s
    return {"t_zul": t_zul, "s_min": s_min, "ok": ok}


# ─────────────────────────────────────────────────────────────
# Aufteilung auf n parallele Kabel pro Aussenleiter
# ─────────────────────────────────────────────────────────────
def dimensioniere_parallel(strom_a, laenge_m, cos_phi, spannung_v, verlegeart,
                           material="Cu", isolation="PVC", umgebung_c=30,
                           anzahl_stromkreise=1, max_du=3.0, betriebstemp_c=70,
                           n_werte=(2, 3, 4), ik_a=None, t_aus_s=None, k_faktor=None):
    """
    Schlaegt fuer jede Parallelzahl n den kleinsten Querschnitt vor, der LAST-
    seitig (thermisch + Spannungsfall) passt. Optionaler Kurzschluss-Nachweis
    am Einzelleiter, wenn ik_a gegeben ist.

    Lastseitige Annahmen:
      Iz_gesamt = n * Iz(S)@30C * k_temp * k_haeufung(n_gebuendelt)
      n_gebuendelt = n * anzahl_stromkreise
        -> die n Parallelkabel liegen gebuendelt; jedes zaehlt fuer die
           Haeufung. Konservativ; bei getrennter Verlegung kleiner waehlen.
      dU = dU_einzeln(S) / n   (R'/X' je Phase teilen sich auf n Wege)

    Rueckgabe: Liste je n mit dem kleinsten passenden S (oder None, wenn keiner
    im Tabellenbereich passt), inkl. KS-Nachweis falls ik_a gesetzt.
    """
    sys = T.SPANNUNGEN[spannung_v]
    n_leiter = sys["n_leiter"]
    tab = T.iz_tabelle(verlegeart, material, isolation, n_leiter)
    if tab is None:
        status = T.IZ_STATUS.get((verlegeart, material, isolation, n_leiter), "nicht eingepflegt")
        raise RechenFehler(
            f"Keine verifizierte Iz-Tabelle fuer Verlegeart {verlegeart}, "
            f"{material}/{isolation}, {n_leiter} belastete Leiter ({status})."
        )
    if k_faktor is None:
        k_faktor = T.K_FAKTOR.get((material, isolation))

    vorschlaege = []
    for n in n_werte:
        k_group = T.k_haeufung(n * anzahl_stromkreise)
        k_t = T.k_temp(isolation, umgebung_c)
        treffer = None
        for s in sorted(tab):
            iz_gesamt = n * tab[s] * k_t * k_group
            du = spannungsfall_prozent(strom_a, laenge_m, cos_phi, s,
                                       spannung_v, betriebstemp_c) / n
            if strom_a <= iz_gesamt and du <= max_du:
                treffer = {"n": n, "s": s, "iz_gesamt": iz_gesamt,
                           "k_group": k_group, "du": du}
                break
        if treffer and ik_a is not None and k_faktor is not None:
            treffer["ks"] = adiabatischer_nachweis(ik_a, treffer["s"], k_faktor, t_aus_s)
        vorschlaege.append(treffer if treffer else {"n": n, "s": None,
                                                     "k_group": k_group})
    return vorschlaege, k_faktor
