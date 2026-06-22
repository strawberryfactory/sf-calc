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
# Verlegearten nach NIN 5.2.3 Tabelle 2 (= IEC 60364-5-52)
# ============================================================
VERLEGEARTEN = {
    "A1": "Aderleitungen im Rohr in waermegedaemmter Wand",
    "A2": "Mehradriges Kabel im Rohr in waermegedaemmter Wand",
    "B1": "Aderleitungen im Rohr auf/in Wand",
    "B2": "Mehradriges Kabel im Rohr auf/in Wand",
    "C":  "Kabel direkt auf/in Wand (mehradrig)",
    "D":  "Kabel im Erdreich (Rohr oder direkt)",
    "E":  "Mehradriges Kabel frei in Luft",
    "F":  "Einadrige Kabel frei in Luft (Beruehrung)",
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

# Quelle aller Iz-Werte: NIN SN 411000:2025, 5.2.3.1.1.11, Tabellen 4-7
# (A1/A2/B1/B2/C/D) und Tabellen 12/14 (E), je 30 C Umgebung / 20 C Erdreich.
# Visuell aus dem Norm-PDF abgelesen (referenz/nin_strombelastbarkeit_260622.pdf).
#
# Spaltenreihenfolge der A-D-Tabellen: (A1, A2, B1, B2, C, D)
_AD_SPALTEN = ("A1", "A2", "B1", "B2", "C", "D")

# (isolation, n_leiter) -> { querschnitt: (A1, A2, B1, B2, C, D) }
_NIN_AD_CU = {
    # NIN Tab. 4 — PVC 70 C, zwei belastete Leiter, Kupfer
    ("PVC", 2): {
        1.5: (14.5, 14, 17.5, 16.5, 19.5, 22), 2.5: (19.5, 18.5, 24, 23, 27, 29),
        4: (26, 25, 32, 30, 36, 37), 6: (34, 32, 41, 38, 46, 46),
        10: (46, 43, 57, 52, 63, 60), 16: (61, 57, 76, 69, 85, 78),
        25: (80, 75, 101, 90, 112, 99), 35: (99, 92, 125, 111, 138, 119),
        50: (119, 110, 151, 133, 168, 140), 70: (151, 139, 192, 168, 213, 173),
        95: (182, 167, 232, 201, 258, 204), 120: (210, 192, 269, 232, 299, 231),
        150: (240, 219, 300, 258, 344, 261), 185: (273, 248, 341, 294, 392, 292),
        240: (321, 291, 400, 344, 461, 336), 300: (367, 334, 458, 394, 530, 379),
    },
    # NIN Tab. 6 — PVC 70 C, drei belastete Leiter, Kupfer
    ("PVC", 3): {
        1.5: (13.5, 13, 16.5, 15, 17.5, 18), 2.5: (18, 17.5, 21, 20, 24, 24),
        4: (24, 23, 28, 27, 32, 30), 6: (31, 29, 36, 34, 41, 38),
        10: (42, 39, 50, 46, 57, 50), 16: (56, 52, 68, 62, 76, 64),
        25: (73, 68, 89, 80, 96, 82), 35: (89, 83, 110, 99, 119, 98),
        50: (108, 99, 134, 118, 144, 116), 70: (136, 125, 171, 149, 184, 143),
        95: (164, 150, 207, 179, 223, 169), 120: (188, 172, 239, 206, 259, 192),
        150: (216, 196, 262, 225, 299, 217), 185: (245, 223, 296, 255, 341, 243),
        240: (286, 261, 346, 297, 403, 280), 300: (328, 298, 394, 339, 464, 316),
    },
    # NIN Tab. 5 — VPE/EPR 90 C, zwei belastete Leiter, Kupfer
    ("XLPE", 2): {
        1.5: (19, 18.5, 23, 22, 24, 25), 2.5: (26, 25, 31, 30, 33, 33),
        4: (35, 33, 42, 40, 45, 43), 6: (45, 42, 54, 51, 58, 53),
        10: (61, 57, 75, 69, 80, 71), 16: (81, 76, 100, 91, 107, 91),
        25: (106, 99, 133, 119, 138, 116), 35: (131, 121, 164, 146, 171, 139),
        50: (158, 145, 198, 175, 209, 164), 70: (200, 183, 253, 221, 269, 203),
        95: (241, 220, 306, 265, 328, 239), 120: (278, 253, 354, 305, 382, 271),
        150: (318, 290, 393, 334, 441, 306), 185: (362, 329, 449, 384, 506, 343),
        240: (424, 386, 528, 459, 599, 395), 300: (486, 442, 603, 532, 693, 446),
    },
    # NIN Tab. 7 — VPE/EPR 90 C, drei belastete Leiter, Kupfer
    ("XLPE", 3): {
        1.5: (17, 16.5, 20, 19.5, 22, 21), 2.5: (23, 22, 28, 26, 30, 28),
        4: (31, 30, 37, 35, 40, 36), 6: (40, 38, 48, 44, 52, 44),
        10: (54, 51, 66, 60, 71, 58), 16: (73, 68, 88, 80, 96, 75),
        25: (95, 89, 117, 105, 119, 96), 35: (117, 109, 144, 128, 147, 115),
        50: (141, 130, 175, 154, 179, 135), 70: (179, 164, 222, 194, 229, 167),
        95: (216, 197, 269, 233, 278, 197), 120: (249, 227, 312, 268, 322, 223),
        150: (285, 259, 342, 300, 371, 251), 185: (324, 295, 384, 340, 424, 261),
        240: (380, 346, 450, 398, 500, 324), 300: (435, 396, 514, 455, 576, 365),
    },
}

# Verlegeart E (mehradriges Kabel frei in Luft), Kupfer.
# (isolation, n_leiter) -> { querschnitt: Iz }
# NIN Tab. 12 Spalten 1/2 (PVC), Tab. 14 Spalten 1/2 (VPE/EPR).
_NIN_E_CU = {
    ("PVC", 2): {1.5: 22, 2.5: 30, 4: 40, 6: 51, 10: 70, 16: 94, 25: 119, 35: 148,
                 50: 180, 70: 232, 95: 282, 120: 328, 150: 379, 185: 434, 240: 514, 300: 593},
    ("PVC", 3): {1.5: 18.5, 2.5: 25, 4: 34, 6: 43, 10: 60, 16: 80, 25: 101, 35: 126,
                 50: 153, 70: 196, 95: 238, 120: 276, 150: 319, 185: 364, 240: 430, 300: 497},
    ("XLPE", 2): {1.5: 26, 2.5: 36, 4: 49, 6: 63, 10: 86, 16: 115, 25: 149, 35: 185,
                  50: 225, 70: 289, 95: 352, 120: 410, 150: 473, 185: 542, 240: 641, 300: 741},
    ("XLPE", 3): {1.5: 23, 2.5: 32, 4: 42, 6: 54, 10: 75, 16: 100, 25: 127, 35: 158,
                  50: 192, 70: 246, 95: 298, 120: 346, 150: 399, 185: 456, 240: 538, 300: 621},
}


def _baue_iz():
    """Setzt IZ + IZ_STATUS aus den NIN-Spaltentabellen zusammen."""
    iz, status = {}, {}
    for (iso, n), tab in _NIN_AD_CU.items():
        for i, va in enumerate(_AD_SPALTEN):
            iz[(va, "Cu", iso, n)] = {s: werte[i] for s, werte in tab.items()}
            status[(va, "Cu", iso, n)] = "verifiziert: NIN SN 411000:2025 Tab. 4-7"
    for (iso, n), tab in _NIN_E_CU.items():
        iz[("E", "Cu", iso, n)] = dict(tab)
        status[("E", "Cu", iso, n)] = "verifiziert: NIN SN 411000:2025 Tab. 12/14"
    return iz, status


IZ, IZ_STATUS = _baue_iz()


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
# k-Faktor fuer den adiabatischen Kurzschluss-Nachweis (I2t)
# IEC 60364-5-54 Tab. 43A, Einheit A*s^0.5/mm2.
# Verwendung:  t_zul = (k * S / Ik)^2   bzw.   S_min = Ik * sqrt(t) / k
# Schluessel: (material, isolation). Leiter-Anfangstemp 70 C (PVC) / 90 C (XLPE),
# Endtemp PVC 160 C, XLPE/EPR 250 C.
# ============================================================
K_FAKTOR = {
    ("Cu", "PVC"): 115,
    ("Cu", "XLPE"): 143,   # gilt auch fuer EPR
    ("Al", "PVC"): 76,
    ("Al", "XLPE"): 94,
}


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
