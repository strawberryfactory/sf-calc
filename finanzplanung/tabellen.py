"""
tabellen.py — Normwerte und Eckdaten der Schweizer Vorsorge / Finanzplanung.

Generische, öffentliche Parameter (AHV/IV, BVG, Säule 3a, Tragbarkeit). KEINE
Kundendaten. Jeder Wert trägt Stand (Jahr), Quelle und ein Verifikations-Flag.
Bei verifiziert=False warnt der Rechenkern, statt eine Scheingenauigkeit zu liefern
(analog kabelberechnung: lieber ehrlich verweigern als falsch rechnen).

Quellen: BSV / AHV-IV (ahv-iv.ch), BVG (SR 831.40), ESTV. Werte vor produktivem
Einsatz gegen die aktuelle offizielle Mitteilung prüfen.
"""

# ─────────────────────────────────────────────────────────────
# AHV — 1. Säule (Altersrente, Vollrente bei lückenloser Beitragsdauer)
# Skala 44: volle Rente ab 44 Beitragsjahren. Monatswerte → ×12 = Jahr.
# ─────────────────────────────────────────────────────────────
AHV = {
    2024: {
        "rente_max_monat": 2450.0,      # Vollrente Maximum (Einzelperson)
        "rente_min_monat": 1225.0,      # Vollrente Minimum
        "plafond_ehepaar_monat": 3675.0,  # 150 % Maximum (Ehepaar/eingetr. P.)
        "voll_beitragsjahre": 44,
        "quelle": "BSV/AHV-IV, Rentenskala 44, Stand 2024",
        "verifiziert": True,
    },
    2025: {
        "rente_max_monat": 2520.0,
        "rente_min_monat": 1260.0,
        "plafond_ehepaar_monat": 3780.0,
        "voll_beitragsjahre": 44,
        "quelle": "BSV/AHV-IV, Rentenskala 44, Stand 2025",
        "verifiziert": False,           # vor Einsatz gegen offizielle Mitteilung prüfen
    },
}

# ─────────────────────────────────────────────────────────────
# BVG — 2. Säule (obligatorischer Teil)
# ─────────────────────────────────────────────────────────────
BVG = {
    2024: {
        "umwandlungssatz_65": 0.068,    # gesetzl. Mindest-Umwandlungssatz (Obligatorium)
        "mindestzins": 0.0125,          # BVG-Mindestzinssatz auf Altersguthaben
        "eintrittsschwelle": 22050.0,   # Mindestjahreslohn für BVG-Pflicht
        "koordinationsabzug": 25725.0,
        "oberer_grenzlohn": 88200.0,
        "max_koord_lohn": 62475.0,      # oberer Grenzlohn − Koordinationsabzug
        "min_koord_lohn": 3675.0,
        "quelle": "BVG SR 831.40 / BSV, Stand 2024",
        "verifiziert": True,
    },
}

# Altersgutschriften BVG in % des koordinierten Lohns (Obligatorium), nach Alter.
BVG_ALTERSGUTSCHRIFTEN = {
    (25, 34): 0.07,
    (35, 44): 0.10,
    (45, 54): 0.15,
    (55, 65): 0.18,
}

# ─────────────────────────────────────────────────────────────
# Säule 3a — maximaler steuerlich abziehbarer Beitrag
# ─────────────────────────────────────────────────────────────
SAEULE_3A = {
    2024: {
        "max_mit_pk": 7056.0,           # mit 2. Säule
        "max_ohne_pk_quote": 0.20,      # ohne 2. Säule: 20 % des Erwerbseinkommens …
        "max_ohne_pk_deckel": 35280.0,  # … höchstens dieser Betrag
        "quelle": "ESTV, Stand 2024",
        "verifiziert": True,
    },
    2025: {
        "max_mit_pk": 7258.0,
        "max_ohne_pk_quote": 0.20,
        "max_ohne_pk_deckel": 36288.0,
        "quelle": "ESTV, Stand 2025",
        "verifiziert": False,
    },
}

# ─────────────────────────────────────────────────────────────
# Tragbarkeit Wohneigentum (Banken-/FINMA-Praxis, selbstbewohnt)
# ─────────────────────────────────────────────────────────────
TRAGBARKEIT = {
    "kalk_zinssatz": 0.05,              # kalkulatorischer Zinssatz (Standard ~5 %)
    "nebenkosten_quote": 0.01,          # 1 % des Immobilienwerts p. a.
    "tragbarkeitsgrenze": 1.0 / 3.0,    # Wohnkosten ≤ 33⅓ % des Bruttoeinkommens
    "belehnung_max": 0.80,              # max. Hypothek (selbstbewohnt)
    "belehnung_2_hypothek": 0.6667,     # 1. Hypothek bis 66⅔ %; darüber 2. Hypothek
    "amortisation_jahre": 15,           # 2. Hypothek auf 66⅔ % amortisieren (oder bis 65)
    "quelle": "FINMA-RS / Bankenpraxis Selbstregulierung",
    "verifiziert": True,
}

# ─────────────────────────────────────────────────────────────
# Default-Planungsannahmen (überschreibbar; Pflicht zu dokumentieren!)
# ─────────────────────────────────────────────────────────────
ANNAHMEN_DEFAULT = {
    "rendite": 0.015,                   # erwartete Nettorendite Vorsorgevermögen p. a.
    "teuerung": 0.010,                  # angenommene Teuerung p. a.
    "lebenserwartung": 90,              # Planungshorizont Endalter (konservativ)
    "ersatzquote_ziel": 0.80,           # Zielrente in % des letzten Einkommens
    "quelle": "Planungsannahmen – mit Kunde zu bestätigen",
    "verifiziert": False,               # IMMER vom Berater zu setzen
}


def jahr_oder_neuestes(tabelle: dict, jahr):
    """Liefert den Datensatz für 'jahr' oder den neuesten verfügbaren."""
    if jahr in tabelle:
        return jahr, tabelle[jahr]
    neuestes = max(tabelle)
    return neuestes, tabelle[neuestes]


def altersgutschrift_satz(alter: int):
    """BVG-Altersgutschrift in % des koord. Lohns für ein Alter (0 unter 25 / ab 65)."""
    for (lo, hi), satz in BVG_ALTERSGUTSCHRIFTEN.items():
        if lo <= alter <= hi:
            return satz
    return 0.0
