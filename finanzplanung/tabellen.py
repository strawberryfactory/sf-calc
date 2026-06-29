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
        "quelle": "BSV/AHV-IV, Rentenskala 44, Stand 2025 (Rentenanpassung 2025)",
        "verifiziert": True,            # offiziell publizierte Werte 2025
    },
}

# ─────────────────────────────────────────────────────────────
# AHV21 — Referenzalter (ordentliches Rentenalter), in Kraft seit 1.1.2024
# Männer: 65. Frauen: schrittweise Anhebung 64 → 65 über die Übergangs-
# generation (Jg. 1961–1963 gestaffelt, ab Jg. 1964 = 65). Gesetzlich eindeutig.
# ─────────────────────────────────────────────────────────────
AHV_REFERENZALTER = {
    "mann": 65.0,
    "frau_bis_1960": 64.0,
    "frau_uebergang": {          # Jahrgang → Referenzalter in Jahren
        1961: 64.25,             # 64 Jahre + 3 Monate
        1962: 64.50,             # 64 Jahre + 6 Monate
        1963: 64.75,             # 64 Jahre + 9 Monate
    },
    "frau_ab_1964": 65.0,
    "quelle": "AHV21 (Revision AHVG, in Kraft 1.1.2024), BSV/AHV-IV",
    "verifiziert": True,         # Referenzalter-Stufen sind gesetzlich festgelegt
}

# ─────────────────────────────────────────────────────────────
# AHV — Rentenvorbezug: lebenslange Kürzung der Altersrente.
# Reguläre Sätze: 6.8 % je vorbezogenem Jahr (anteilig pro Monat), Vorbezug
# bis 2 Jahre vor Referenzalter.
# ACHTUNG Übergangsgeneration Frauen (Jg. 1961–1969): REDUZIERTE, einkommens-
# abhängige Sonderkürzungssätze + Vorbezug bereits ab 62 möglich. Diese
# Sondersätze sind NICHT abgebildet (einkommensabhängige Tabelle) → der
# Rechenkern warnt und rechnet nicht scheingenau.
# ─────────────────────────────────────────────────────────────
AHV_VORBEZUG = {
    "kuerzung_pro_jahr": 0.068,
    "frueheste_vorbezugsjahre_regulaer": 2,        # ab Referenzalter − 2
    "uebergangsgeneration_jahrgaenge": (1961, 1969),
    "quelle": "BSV/AHV-IV, Vorbezug Altersrente (reguläre Sätze)",
    "verifiziert": False,        # Sätze + Übergangs-Sonderregeln vor Einsatz prüfen
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
        "verifiziert": True,            # offiziell publizierte Werte 2025
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


def referenzalter_ahv(jahrgang: int, geschlecht: str):
    """AHV-Referenzalter (Jahre) aus Jahrgang + Geschlecht nach AHV21.

    geschlecht: 'mann' oder 'frau' (auch 'm'/'f'/'w'). Männer: 65.
    Frauen: bis Jg. 1960 = 64, 1961–1963 gestaffelt, ab 1964 = 65.
    """
    r = AHV_REFERENZALTER
    g = geschlecht.strip().lower()
    if g in ("mann", "m", "männlich", "maennlich"):
        return r["mann"]
    if g in ("frau", "f", "w", "weiblich"):
        if jahrgang <= 1960:
            return r["frau_bis_1960"]
        if jahrgang in r["frau_uebergang"]:
            return r["frau_uebergang"][jahrgang]
        return r["frau_ab_1964"]
    raise ValueError(f"Unbekanntes Geschlecht '{geschlecht}' (erwartet mann/frau).")
