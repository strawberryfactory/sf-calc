"""
rechnen.py — Versicherungs-Offertenvergleich (deterministisch).

Aus der Ausschreibung (Sparten + geforderte Deckungen) und den extrahierten Offerten
(je Versicherer Positionen mit Prämie/Deckung) entsteht:
  Vergleichsmatrix · Totale inkl. Eidg. Stempelabgabe · Ranking · Vollständigkeit
  (wer offeriert/verzichtet) · Deckungs-Check gegen die Ausschreibung.

Das Modell/die Agenten EXTRAHIEREN die Offertenwerte; dieses Modul rechnet und prüft nur
(keine erfundenen Zahlen, keine vergessene Sparte).
"""

from . import tabellen as T


class RechenFehler(Exception):
    pass


def vergleiche(cfg: dict) -> dict:
    aussch = cfg.get("ausschreibung", {})
    sparten_spec = aussch.get("sparten", [])
    if not sparten_spec:
        raise RechenFehler("ausschreibung.sparten fehlt.")
    offerten = cfg.get("offerten", [])

    # Sparten-Reihenfolge: aus der Ausschreibung, plus allfällige zusätzliche aus Offerten
    sparten = [s["name"] for s in sparten_spec]
    spec_by_name = {s["name"]: s for s in sparten_spec}
    for off in offerten:
        for p in off.get("positionen", []):
            if p.get("sparte") and p["sparte"] not in sparten:
                sparten.append(p["sparte"])

    matrix = {}              # versicherer -> {sparte: praemie}
    summen = []              # je Versicherer
    deckungs_abweichungen = []

    for off in offerten:
        vname = off.get("versicherer", "?")
        status = off.get("status", "offeriert")
        zeile = {}
        summe = stempel = 0.0
        for p in off.get("positionen", []):
            sp = p.get("sparte")
            praemie = p.get("praemie")
            if sp is None or praemie is None:
                continue
            zeile[sp] = round(float(praemie), 2)
            satz = T.stempel_satz(sp, p.get("stempel_satz"))
            summe += float(praemie)
            stempel += float(praemie) * satz
            # Deckungs-Check gegen Ausschreibung
            spec = spec_by_name.get(sp)
            if spec:
                vs_soll, vs_ist = spec.get("versicherungssumme"), p.get("versicherungssumme")
                if vs_soll and vs_ist is not None and float(vs_ist) < float(vs_soll):
                    deckungs_abweichungen.append({
                        "versicherer": vname, "sparte": sp, "feld": "Versicherungssumme",
                        "verlangt": vs_soll, "offeriert": vs_ist})
                sb_soll, sb_ist = spec.get("selbstbehalt"), p.get("selbstbehalt")
                if sb_soll is not None and sb_ist is not None and float(sb_ist) > float(sb_soll):
                    deckungs_abweichungen.append({
                        "versicherer": vname, "sparte": sp, "feld": "Selbstbehalt",
                        "verlangt": sb_soll, "offeriert": sb_ist})
        matrix[vname] = zeile
        fehlend = [s for s in sparten if s not in zeile] if status == "offeriert" else sparten
        summen.append({
            "versicherer": vname, "status": status,
            "summe_praemien": round(summe, 2), "stempelabgabe": round(stempel, 2),
            "total_inkl_stempel": round(summe + stempel, 2),
            "anzahl_positionen": len(zeile), "fehlende_sparten": fehlend,
            "vollstaendig": status == "offeriert" and not fehlend,
        })

    # Ranking: nur Versicherer mit Offerte und mindestens einer Position, günstigster zuerst
    rang = sorted([s for s in summen if s["status"] == "offeriert" and s["anzahl_positionen"] > 0],
                  key=lambda s: s["total_inkl_stempel"])
    ranking = [{"rang": i + 1, "versicherer": s["versicherer"],
                "total_inkl_stempel": s["total_inkl_stempel"],
                "vollstaendig": s["vollstaendig"]} for i, s in enumerate(rang)]

    verzichtet = [s["versicherer"] for s in summen if s["status"] != "offeriert"]
    unvollstaendig = [s["versicherer"] for s in summen
                      if s["status"] == "offeriert" and not s["vollstaendig"]]

    warnungen = [
        "Prämien aus den Offerten extrahiert; Vergleichs-Arithmetik (Total, Stempelabgabe, "
        "Ranking) ist deterministisch geprüft.",
        "Stempelabgabe vereinfacht (5 % Sach/Haftpflicht/Motorfahrzeug, 0 % KTG/UVG) — "
        "im Einzelfall verifizieren (StG Art. 21–23).",
    ]
    if deckungs_abweichungen:
        warnungen.append("Deckungsabweichungen gegenüber der Ausschreibung festgestellt — "
                         "Prämien sind nur bei gleicher Deckung vergleichbar.")
    if unvollstaendig:
        warnungen.append(f"Unvollständige Offerten (nicht alle Sparten): {', '.join(unvollstaendig)}.")

    return {
        "firma": aussch.get("firma", cfg.get("firma", "")),
        "sparten": sparten,
        "versicherer": [s["versicherer"] for s in summen],
        "matrix": matrix,
        "summen": summen,
        "ranking": ranking,
        "guenstigster": ranking[0]["versicherer"] if ranking else None,
        "verzichtet": verzichtet,
        "deckungs_abweichungen": deckungs_abweichungen,
        "warnungen": warnungen,
    }
