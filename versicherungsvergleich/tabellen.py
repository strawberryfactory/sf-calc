"""
tabellen.py — Normwerte für den Versicherungsvergleich.

Eidgenössische Stempelabgabe auf Versicherungsprämien (Bundesgesetz über die Stempelabgaben,
StG Art. 21–23). Generisch, keine Kundendaten.

Faustregel (vereinfacht, vor Einsatz prüfen):
  - 5 %   auf die meisten Nichtleben-/Schadenprämien (Sach, Haftpflicht, Motorfahrzeug-Kasko)
  - 0 %   befreit: Kranken-, Unfall- (UVG/UVG-Z), Invaliditäts-, Arbeitslosenversicherung,
          Lebensversicherung mit periodischer Prämie, Sachschäden Vieh u.a.
  - 2.5 % Lebensversicherung mit Einmalprämie (hier nicht relevant)
"""

STEMPELABGABE = {
    "satz_standard": 0.05,
    "befreit_kategorien": {"ktg", "uvg", "uvgz", "kranken", "unfall", "personenversicherung"},
    "quelle": "StG Art. 21–23 (Eidg. Stempelabgabe auf Versicherungsprämien)",
    "verifiziert": True,
}

# Mappt einen Sparten-/Kategorienamen auf eine normierte Kategorie für den Stempelsatz.
_KEYWORDS = {
    "ktg": "ktg", "krankentaggeld": "ktg", "kranken": "kranken",
    "uvg-z": "uvgz", "uvgz": "uvgz", "uvg zusatz": "uvgz",
    "uvg": "uvg", "unfall": "unfall",
    "sach": "sach", "feuer": "sach", "elementar": "sach", "diebstahl": "sach",
    "haftpflicht": "haftpflicht", "bh3": "haftpflicht", "berufshaftpflicht": "haftpflicht",
    "motorfahrzeug": "motorfahrzeug", "mf": "motorfahrzeug", "fahrzeug": "motorfahrzeug",
}


def kategorie(name: str) -> str:
    n = (name or "").lower()
    for kw, kat in _KEYWORDS.items():
        if kw in n:
            return kat
    return "sonstige"


def stempel_satz(name: str, override: float = None) -> float:
    """Stempelsatz für eine Sparte (0.05 Standard, 0.0 befreit). override gewinnt."""
    if override is not None:
        return override
    return 0.0 if kategorie(name) in STEMPELABGABE["befreit_kategorien"] else STEMPELABGABE["satz_standard"]
