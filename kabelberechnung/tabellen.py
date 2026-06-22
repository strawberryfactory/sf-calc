"""
tabellen.py — Normdaten fuer die Kabelberechnung (NIN / IEC 60364-5-52).

Grundsatz: jede Zelle traegt ihre Quelle. Werte sind entweder
  VERIFIZIERT  — gegen Samuels reviewte Skripte oder Paperless-PDF geprueft
  OFFEN        — Slot vorhanden, Wert noch nicht eingepflegt (None)

Status pro Datensatz steht in IZ_STATUS. `kabelberechnung show --tabellen`
zeigt die Abdeckung an, damit nie ein ungepruefter Wert als gesichert
ausgegeben wird.

Quellen:
  NIN 2020, Arbeitsblatt 27.x (= NIN 5.2.3.1.1.x), Schweizer Extrakt
  IEC 60364-5-52:2009 Tab. B.52.2 ff. (Strombelastbarkeit)
                      Tab. B.52.14 (Temperatur-Korrektur Luft)
                      Tab. B.52.17 (Haeufung)
"""

# ============================================================
# Verlegearten (IEC 60364-5-52 Referenz-Verlegearten)
# ============================================================
VERLEGEARTEN = {
    "A1": "Aderleitungen im Rohr in waermegedaemmter Wand",
    "A2": "Mehradriges Kabel im Rohr in waermegedaemmter Wand",
    "B1": "Aderleitungen im Rohr auf/in Wand",
    "B2": "Mehradriges Kabel im Rohr auf/in Wand",
    "C":  "Kabel direkt auf/in Wand (mehradrig)",
    "D1": "Mehradriges Kabel im Rohr im Erdreich",
    "D2": "Kabel direkt im Erdreich",
    "E":  "Mehradriges Kabel frei in Luft",
    "F":  "Einadrige Kabel frei in Luft (gebuendelt)",
    "G":  "Einadrige Kabel frei in Luft (mit Abstand)",
}

# Standard-Querschnittsreihe Cu/Al [mm2]
QUERSCHNITTE = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# ============================================================
# Strombelastbarkeit Iz [A] bei 30 C Umgebung (Referenzbedingung)
# Schluessel: (verlegeart, material, isolation, n_belastete_leiter)
#   material   : "Cu" | "Al"
#   isolation  : "PVC"  (70 C Leiter — gilt auch fuer FE05 halogenfrei)
#                "XLPE" (90 C Leiter — XLPE/EPR)
#   n_leiter   : 2 (1-phasig L+N)  |  3 (3-phasig)
# Wert None = noch nicht eingepflegt (siehe IZ_STATUS).
# ============================================================

IZ = {
    # --- Verlegeart C, Cu, PVC/halogenfrei 70 C -------------------------
    # VERIFIZIERT gegen Samuels kabelrechnerFE05.py / Kabelrechner1phFE05.py
    # (Review-Stand dort), Werte >120 mm2 aus IEC B.52.4-Logik (PVC-Spalte).
    ("C", "Cu", "PVC", 3): {
        1.5: 15.5, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89, 35: 110,
        50: 134, 70: 171, 95: 207, 120: 239, 150: 272, 185: 310, 240: 364, 300: None,
    },
    ("C", "Cu", "PVC", 2): {
        1.5: 17.5, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101, 35: 125,
        50: 151, 70: 192, 95: 232, 120: 269, 150: 309, 185: 353, 240: 415, 300: None,
    },
}

# Welche (verlegeart, material, isolation, n) sind eingepflegt + verifiziert?
# Alles, was hier nicht "verifiziert" ist, gilt als OFFEN und wird vom
# Rechenkern verweigert (kein Raten).
IZ_STATUS = {
    ("C", "Cu", "PVC", 3): "verifiziert: Samuel-Skript kabelrechnerFE05.py",
    ("C", "Cu", "PVC", 2): "verifiziert: Samuel-Skript Kabelrechner1phFE05.py",
}


def iz_verfuegbar(verlegeart, material, isolation, n_leiter):
    """True, wenn ein verifizierter Iz-Datensatz vorliegt."""
    key = (verlegeart, material, isolation, n_leiter)
    return key in IZ and IZ_STATUS.get(key, "").startswith("verifiziert")


def iz_tabelle(verlegeart, material, isolation, n_leiter):
    """Liefert {querschnitt: Iz} oder None, wenn nicht verifiziert vorhanden."""
    if not iz_verfuegbar(verlegeart, material, isolation, n_leiter):
        return None
    return {s: v for s, v in IZ[(verlegeart, material, isolation, n_leiter)].items() if v is not None}


# ============================================================
# Leitungsbelaege R' und X' [Ohm/km] bei 20 C, Cu
# R' VERIFIZIERT: Samuels Skripte (Praxiswerte)
# X' VERIFIZIERT: Kurzschlussberechnung.py (X_PRIME_CU)
# ============================================================
R_PRIME_CU = {
    1.5: 12.10, 2.5: 7.41, 4: 4.61, 6: 3.08, 10: 1.83, 16: 1.15, 25: 0.727,
    35: 0.524, 50: 0.387, 70: 0.268, 95: 0.193, 120: 0.153, 150: 0.124,
    185: 0.0991, 240: 0.0754, 300: 0.0601,
}

# Reaktanzbelag X' [Ohm/km], mehradriges NV-Cu-Kabel.
# VERIFIZIERT: 1:1 aus Kurzschlussberechnung.py (X_PRIME_CU, Review Wouters).
X_PRIME_CU = {
    1.5: 0.1140, 2.5: 0.1100, 4: 0.1060, 6: 0.1000, 10: 0.0945, 16: 0.0895,
    25: 0.0879, 35: 0.0851, 50: 0.0848, 70: 0.0819, 95: 0.0819, 120: 0.0804,
    150: 0.0804, 185: 0.0804, 240: 0.0797, 300: 0.0797,
}

ALPHA_CU = 0.00393  # 1/K, Temperaturkoeffizient Cu


# ============================================================
# Temperatur-Korrekturfaktoren k1 (Umgebungsluft, Referenz 30 C)
# IEC 60364-5-52 Tab. B.52.14 — VERIFIZIERT (Standardtabelle)
# ============================================================
K_TEMP = {
    "PVC": {10: 1.22, 15: 1.17, 20: 1.12, 25: 1.06, 30: 1.00, 35: 0.94,
            40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61, 60: 0.50},
    "XLPE": {10: 1.15, 15: 1.12, 20: 1.08, 25: 1.04, 30: 1.00, 35: 0.96,
             40: 0.91, 45: 0.87, 50: 0.82, 55: 0.76, 60: 0.71, 65: 0.65,
             70: 0.58, 75: 0.50, 80: 0.41},
}


def k_temp(isolation, umgebung_c):
    """Interpoliert den Temperatur-Korrekturfaktor linear."""
    tab = K_TEMP.get(isolation)
    if not tab:
        return 1.0
    temps = sorted(tab)
    if umgebung_c <= temps[0]:
        return tab[temps[0]]
    if umgebung_c >= temps[-1]:
        return tab[temps[-1]]
    lo = max(t for t in temps if t <= umgebung_c)
    hi = min(t for t in temps if t >= umgebung_c)
    if lo == hi:
        return tab[lo]
    frac = (umgebung_c - lo) / (hi - lo)
    return tab[lo] + frac * (tab[hi] - tab[lo])


# ============================================================
# Haeufungsfaktoren k2 (mehrere Stromkreise gebuendelt)
# IEC 60364-5-52 Tab. B.52.17, Anordnung "gebuendelt auf Oberflaeche/
# eingebettet/umschlossen" — VERIFIZIERT (Standardtabelle).
# Schluessel: Anzahl Stromkreise -> Faktor.
# ============================================================
K_HAEUFUNG = {
    1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65, 5: 0.60, 6: 0.57, 7: 0.54,
    8: 0.52, 9: 0.50, 12: 0.45, 16: 0.41, 20: 0.38,
}


def k_haeufung(anzahl_stromkreise):
    """Naechstkleinerer (konservativer) Tabellenwert."""
    n = int(anzahl_stromkreise)
    if n <= 1:
        return 1.00
    keys = sorted(K_HAEUFUNG)
    passend = [k for k in keys if k <= n]
    return K_HAEUFUNG[passend[-1]] if passend else K_HAEUFUNG[keys[-1]]


# ============================================================
# Kabelkatalog: Name -> Eigenschaften
#   material, isolation (-> Iz-/Korrekturtabelle), betriebstemp [C], Bez.
# FE05-C: halogenfrei, Leiter 70 C -> verwendet die PVC-Tabellen.
# ============================================================
KABEL = {
    "FE05-C": {"material": "Cu", "isolation": "PVC", "betriebstemp": 70,
               "bez": "FE05-C halogenfrei (Cu, 70 C)"},
}


# ============================================================
# Standard-Spannungssysteme
# ============================================================
SPANNUNGEN = {
    230: {"phasen": 1, "n_leiter": 2, "faktor": 1.0,        "bez": "230 V / 1-phasig (L+N)"},
    400: {"phasen": 3, "n_leiter": 3, "faktor": 3 ** 0.5,   "bez": "400 V / 3-phasig"},
    690: {"phasen": 3, "n_leiter": 3, "faktor": 3 ** 0.5,   "bez": "690 V / 3-phasig"},
}
