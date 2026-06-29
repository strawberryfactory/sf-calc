"""
rechnen.py — Rechenkern der Finanzplanung (Schweizer Vorsorge).

Reine Funktionen, keine Kundendaten. Jeder Block nennt seinen Normbezug.
Grundsatz (wie kabelberechnung): bei nicht verifizierten Normwerten wird gewarnt,
nicht stillschweigend gerechnet.

Module:
  ahv_altersrente          1. Säule (Skala 44, Näherung)
  bvg_rente                2. Säule: Guthaben → Rente (Umwandlungssatz)
  bvg_guthaben_projektion  2. Säule: Altersguthaben bis Pensionierung fortschreiben
  saeule_3a_max            steuerlich abziehbares 3a-Maximum
  vorsorgeluecke           Zielrente − (AHV + BVG)
  kapitalbedarf            benötigtes Kapital, um eine Jahres-Lücke zu decken
  kapitalverzehr_dauer     wie lange reicht ein Kapital bei indexierter Entnahme
  tragbarkeit              Wohneigentum: Wohnkostenquote ≤ 33⅓ %, Belehnung ≤ 80 %
"""

from . import tabellen as T


class RechenFehler(Exception):
    """Fachlicher Fehler (z.B. unplausible Eingabe)."""


def _warn_unverifiziert(datensatz, label, warnungen):
    if not datensatz.get("verifiziert", False):
        warnungen.append(
            f"{label}: Normwert nicht verifiziert ({datensatz.get('quelle','?')}) "
            f"→ vor Einsatz prüfen."
        )


# ─────────────────────────────────────────────────────────────
# 1. Säule — AHV-Altersrente (Rentenskala 44, Näherung)
# Vollrente min bei massg. Ø-Einkommen ≤ min. Jahresrente, max ab oberem
# Grenzbetrag (= 6× min. Jahresrente). Dazwischen linear interpoliert.
# Exakte Rente: offizielle Rentenformel / IK-Auszug der AK.
# ─────────────────────────────────────────────────────────────
def ahv_altersrente(beitragsjahre, durchschnittseinkommen, jahr=2024):
    warnungen = []
    yr, a = T.jahr_oder_neuestes(T.AHV, jahr)
    _warn_unverifiziert(a, f"AHV {yr}", warnungen)
    if beitragsjahre < 0:
        raise RechenFehler("Beitragsjahre < 0.")

    rente_min_j = a["rente_min_monat"] * 12
    rente_max_j = a["rente_max_monat"] * 12
    oberer_grenzbetrag = rente_min_j * 6          # Knickpunkt Vollrente-Maximum

    if durchschnittseinkommen <= rente_min_j:
        vollrente_j = rente_min_j
    elif durchschnittseinkommen >= oberer_grenzbetrag:
        vollrente_j = rente_max_j
    else:
        anteil = (durchschnittseinkommen - rente_min_j) / (oberer_grenzbetrag - rente_min_j)
        vollrente_j = rente_min_j + anteil * (rente_max_j - rente_min_j)

    skala = min(beitragsjahre / a["voll_beitragsjahre"], 1.0)
    rente_j = vollrente_j * skala
    warnungen.append("AHV-Rente ist eine Näherung (Skala 44, lineare Interpolation); "
                     "exakter Wert via Rentenvorausberechnung der Ausgleichskasse.")
    return {
        "rente_jahr": round(rente_j, 0),
        "rente_monat": round(rente_j / 12, 0),
        "vollrente_jahr": round(vollrente_j, 0),
        "skalenfaktor": round(skala, 3),
        "stand": yr, "warnungen": warnungen,
    }


# ─────────────────────────────────────────────────────────────
# AHV21 — Referenzalter aus Jahrgang + Geschlecht
# ─────────────────────────────────────────────────────────────
def ahv_referenzalter(jahrgang, geschlecht):
    warnungen = []
    ra = T.referenzalter_ahv(int(jahrgang), geschlecht)
    jahre = int(ra)
    monate = round((ra - jahre) * 12)
    tab = T.AHV_REFERENZALTER
    uebergang = jahrgang in tab["frau_uebergang"]
    if uebergang:
        warnungen.append(
            f"Frau Jg. {jahrgang} gehört zur AHV21-Übergangsgeneration → "
            f"Referenzalter {jahre} Jahre {monate} Monate (nicht 64).")
    return {
        "referenzalter": ra,
        "referenzalter_jahre": jahre,
        "referenzalter_monate": monate,
        "uebergangsgeneration": bool(uebergang),
        "quelle": tab["quelle"],
        "warnungen": warnungen,
    }


# ─────────────────────────────────────────────────────────────
# AHV — Rentenvorbezug: lebenslange Kürzung der Altersrente
# Reguläre Sätze (6.8 %/Jahr). Übergangsgeneration Frauen (1961–1969):
# einkommensabhängige Sondersätze → hier NICHT gerechnet, sondern gewarnt.
# ─────────────────────────────────────────────────────────────
def ahv_vorbezug(rente_voll_jahr, jahrgang, geschlecht, bezugsalter):
    warnungen = []
    v = T.AHV_VORBEZUG
    _warn_unverifiziert(v, "AHV-Vorbezug", warnungen)
    ra = T.referenzalter_ahv(int(jahrgang), geschlecht)
    vorbezug_jahre = ra - float(bezugsalter)
    if vorbezug_jahre <= 0:
        raise RechenFehler(
            f"Bezugsalter {bezugsalter} liegt nicht vor dem Referenzalter {ra} "
            f"— kein Vorbezug.")
    if vorbezug_jahre > v["frueheste_vorbezugsjahre_regulaer"] + 1e-9:
        warnungen.append(
            f"Vorbezug von {vorbezug_jahre:.2f} Jahren überschreitet den regulären "
            f"Rahmen ({v['frueheste_vorbezugsjahre_regulaer']} Jahre vor Referenzalter). "
            f"Frühestmöglicher AHV-Bezug regulär ab {ra - v['frueheste_vorbezugsjahre_regulaer']:.2f}; "
            f"die Phase davor ist anders zu überbrücken (PK-Überbrückungsrente / Erspartes).")
    lo, hi = v["uebergangsgeneration_jahrgaenge"]
    g = geschlecht.strip().lower()
    if g in ("frau", "f", "w", "weiblich") and lo <= jahrgang <= hi:
        warnungen.append(
            f"Frau Jg. {jahrgang} ist in der Übergangsgeneration ({lo}–{hi}): es gelten "
            f"REDUZIERTE, einkommensabhängige Kürzungssätze (und Vorbezug ab 62 möglich). "
            f"Die hier verwendeten regulären {v['kuerzung_pro_jahr']*100:.1f} %/Jahr sind "
            f"eine Obergrenze — Sondersätze separat über die Ausgleichskasse bestimmen.")
    kuerzung_quote = min(vorbezug_jahre, v["frueheste_vorbezugsjahre_regulaer"]) * v["kuerzung_pro_jahr"]
    rente_gekuerzt = float(rente_voll_jahr) * (1 - kuerzung_quote)
    warnungen.append(
        "Vorbezugskürzung ist lebenslang und gilt auch nach Erreichen des Referenzalters.")
    return {
        "rente_voll_jahr": round(float(rente_voll_jahr), 0),
        "bezugsalter": float(bezugsalter),
        "referenzalter": ra,
        "vorbezug_jahre": round(vorbezug_jahre, 2),
        "kuerzung_quote": round(kuerzung_quote, 4),
        "kuerzung_jahr": round(float(rente_voll_jahr) * kuerzung_quote, 0),
        "rente_gekuerzt_jahr": round(rente_gekuerzt, 0),
        "rente_gekuerzt_monat": round(rente_gekuerzt / 12, 0),
        "warnungen": warnungen,
    }


# ─────────────────────────────────────────────────────────────
# 2. Säule — BVG-Rente aus Altersguthaben
# Rente = Altersguthaben × Umwandlungssatz. Alternative: Kapitalbezug.
# ─────────────────────────────────────────────────────────────
def bvg_rente(altersguthaben, umwandlungssatz=None, jahr=2024):
    warnungen = []
    yr, b = T.jahr_oder_neuestes(T.BVG, jahr)
    _warn_unverifiziert(b, f"BVG {yr}", warnungen)
    if altersguthaben < 0:
        raise RechenFehler("Altersguthaben < 0.")
    uws = umwandlungssatz if umwandlungssatz is not None else b["umwandlungssatz_65"]
    rente_j = altersguthaben * uws
    if umwandlungssatz is None:
        warnungen.append(f"Umwandlungssatz = gesetzl. Minimum {uws*100:.1f} % (Obligatorium). "
                         f"Überobligatorische Guthaben haben oft tiefere Sätze → Reglement prüfen.")
    return {
        "rente_jahr": round(rente_j, 0),
        "rente_monat": round(rente_j / 12, 0),
        "kapital": round(altersguthaben, 0),
        "umwandlungssatz": uws, "stand": yr, "warnungen": warnungen,
    }


# 2. Säule — Altersguthaben bis Pensionierung fortschreiben
def bvg_guthaben_projektion(guthaben_heute, koord_lohn, alter_heute, alter_pension,
                            zins=None, jahr=2024):
    warnungen = []
    yr, b = T.jahr_oder_neuestes(T.BVG, jahr)
    _warn_unverifiziert(b, f"BVG {yr}", warnungen)
    if alter_pension <= alter_heute:
        raise RechenFehler("Pensionsalter ≤ heutiges Alter.")
    z = zins if zins is not None else b["mindestzins"]
    guthaben = float(guthaben_heute)
    for alter in range(int(alter_heute), int(alter_pension)):
        gutschrift = koord_lohn * T.altersgutschrift_satz(alter)
        guthaben = guthaben * (1 + z) + gutschrift
    warnungen.append(f"Projektion mit BVG-Mindestzins {z*100:.2f} % und obligat. "
                     f"Altersgutschriften; reale PK kann abweichen (Reglement).")
    return {
        "guthaben_pension": round(guthaben, 0),
        "zins": z, "jahre": int(alter_pension - alter_heute),
        "stand": yr, "warnungen": warnungen,
    }


# ─────────────────────────────────────────────────────────────
# Säule 3a — maximaler abziehbarer Beitrag
# ─────────────────────────────────────────────────────────────
def saeule_3a_max(mit_pk, erwerbseinkommen, jahr=2024):
    warnungen = []
    yr, s = T.jahr_oder_neuestes(T.SAEULE_3A, jahr)
    _warn_unverifiziert(s, f"Säule 3a {yr}", warnungen)
    if mit_pk:
        maximum = s["max_mit_pk"]
    else:
        maximum = min(erwerbseinkommen * s["max_ohne_pk_quote"], s["max_ohne_pk_deckel"])
    return {"max_beitrag": round(maximum, 0), "mit_pk": bool(mit_pk),
            "stand": yr, "warnungen": warnungen}


# ─────────────────────────────────────────────────────────────
# Vorsorgelücke — Zielrente vs. Renteneinkommen aus 1. + 2. Säule
# ─────────────────────────────────────────────────────────────
def vorsorgeluecke(letztes_einkommen, ahv_rente_jahr, bvg_rente_jahr,
                   ersatzquote_ziel=None):
    q = ersatzquote_ziel if ersatzquote_ziel is not None else T.ANNAHMEN_DEFAULT["ersatzquote_ziel"]
    zielrente = letztes_einkommen * q
    einkommen_vorsorge = ahv_rente_jahr + bvg_rente_jahr
    luecke = zielrente - einkommen_vorsorge
    return {
        "zielrente_jahr": round(zielrente, 0),
        "einkommen_12_saeule": round(einkommen_vorsorge, 0),
        "luecke_jahr": round(luecke, 0),
        "luecke_monat": round(luecke / 12, 0),
        "ersatzquote_ziel": q,
        "deckungsgrad": round(einkommen_vorsorge / zielrente, 3) if zielrente else None,
    }


# ─────────────────────────────────────────────────────────────
# Kapitalbedarf — Barwert einer indexierten Jahres-Lücke (real rate)
# PV = L · (1 − (1+r)^−n) / r ,  r = reale Rendite = (1+rendite)/(1+teuerung) − 1
# ─────────────────────────────────────────────────────────────
def kapitalbedarf(jahres_luecke, jahre, rendite=None, teuerung=None):
    rendite = rendite if rendite is not None else T.ANNAHMEN_DEFAULT["rendite"]
    teuerung = teuerung if teuerung is not None else T.ANNAHMEN_DEFAULT["teuerung"]
    if jahre <= 0:
        raise RechenFehler("Bezugsdauer ≤ 0 Jahre.")
    r = (1 + rendite) / (1 + teuerung) - 1
    if abs(r) < 1e-9:
        pv = jahres_luecke * jahre
    else:
        pv = jahres_luecke * (1 - (1 + r) ** (-jahre)) / r
    return {
        "kapitalbedarf": round(pv, 0),
        "jahres_luecke": round(jahres_luecke, 0),
        "jahre": jahre, "rendite": rendite, "teuerung": teuerung,
        "reale_rendite": round(r, 4),
        "warnungen": ["Annahmen Rendite/Teuerung sind zu bestätigen "
                      "(siehe finanzplanung show --annahmen)."],
    }


# ─────────────────────────────────────────────────────────────
# Kapitalverzehr — wie lange reicht ein Kapital bei indexierter Entnahme
# ─────────────────────────────────────────────────────────────
def kapitalverzehr_dauer(kapital, jahres_entnahme, rendite=None, teuerung=None,
                         max_jahre=60):
    rendite = rendite if rendite is not None else T.ANNAHMEN_DEFAULT["rendite"]
    teuerung = teuerung if teuerung is not None else T.ANNAHMEN_DEFAULT["teuerung"]
    if jahres_entnahme <= 0:
        raise RechenFehler("Jahresentnahme ≤ 0.")
    rest = float(kapital)
    entnahme = float(jahres_entnahme)
    for jahr in range(1, max_jahre + 1):
        rest = rest * (1 + rendite) - entnahme
        entnahme *= (1 + teuerung)         # Entnahme steigt mit Teuerung
        if rest <= 0:
            return {"dauer_jahre": jahr, "reicht_unbegrenzt": False,
                    "rendite": rendite, "teuerung": teuerung}
    return {"dauer_jahre": max_jahre, "reicht_unbegrenzt": True,
            "rendite": rendite, "teuerung": teuerung,
            "warnungen": [f"Kapital reicht ≥ {max_jahre} Jahre (Entnahme < Rendite)."]}


# ─────────────────────────────────────────────────────────────
# Tragbarkeit Wohneigentum (selbstbewohnt)
# Wohnkosten = kalk. Zins · Hypothek + Nebenkosten · Wert + Amortisation
# Tragbar, wenn Wohnkosten ≤ 33⅓ % Bruttoeinkommen UND Belehnung ≤ 80 %.
# ─────────────────────────────────────────────────────────────
def tragbarkeit(immobilienwert, hypothek, bruttoeinkommen,
                kalk_zins=None, nebenkosten_quote=None, amortisation=None):
    t = T.TRAGBARKEIT
    kz = kalk_zins if kalk_zins is not None else t["kalk_zinssatz"]
    nk = nebenkosten_quote if nebenkosten_quote is not None else t["nebenkosten_quote"]
    if immobilienwert <= 0 or bruttoeinkommen <= 0:
        raise RechenFehler("Immobilienwert und Einkommen müssen > 0 sein.")

    belehnung = hypothek / immobilienwert
    # Amortisation: Betrag über 66⅔ % in amortisation_jahre tilgen (falls nicht vorgegeben)
    if amortisation is None:
        zweite_hyp = max(0.0, hypothek - t["belehnung_2_hypothek"] * immobilienwert)
        amortisation = zweite_hyp / t["amortisation_jahre"]

    zins_kosten = hypothek * kz
    nebenkosten = immobilienwert * nk
    wohnkosten = zins_kosten + nebenkosten + amortisation
    quote = wohnkosten / bruttoeinkommen

    return {
        "belehnung": round(belehnung, 4),
        "belehnung_ok": belehnung <= t["belehnung_max"],
        "zins_kosten": round(zins_kosten, 0),
        "nebenkosten": round(nebenkosten, 0),
        "amortisation": round(amortisation, 0),
        "wohnkosten_jahr": round(wohnkosten, 0),
        "tragbarkeitsquote": round(quote, 4),
        "tragbar": quote <= t["tragbarkeitsgrenze"] and belehnung <= t["belehnung_max"],
        "kalk_zins": kz, "nebenkosten_quote": nk,
        "grenze": t["tragbarkeitsgrenze"],
    }


# ─────────────────────────────────────────────────────────────
# Mehrjährige Finanz- und Steuerplanung (Projektion)
# Spalte pro Jahr: Erwerb/Renten → Total → Steuer (GESCHÄTZT) →
# Einkommen nach Steuern → Saldo gg. Ausgaben → Vermögensverlauf.
#
# Vorsorge-/Vermögensteile sind deterministisch. Die STEUER ist eine
# transparente Schätzung: effektiver Satz × (steuerbares Einkommen), wobei
# der Satz aus einer realen Veranlagung verankert wird. Jede Steuerzeile
# ist als geschätzt markiert (steuer_geschaetzt=True + Ankerangabe), damit
# es in der Ausgabe nachvollziehbar bleibt. KEIN kantonaler Tarif im Tool.
# ─────────────────────────────────────────────────────────────
def projektion(start_jahr, start_alter, pensionsalter, end_alter,
               lohn, ahv_rente, pk_rente, ausgaben, vermoegen_start,
               rendite=None, teuerung=None,
               steuersatz_eff=0.0, abzug_pauschale=0.0, steuer_anker=None,
               ahv_alter=65):
    warnungen = []
    rendite = rendite if rendite is not None else T.ANNAHMEN_DEFAULT["rendite"]
    teuerung = teuerung if teuerung is not None else T.ANNAHMEN_DEFAULT["teuerung"]
    if end_alter <= start_alter:
        raise RechenFehler("Endalter ≤ Startalter.")
    if pensionsalter < start_alter:
        raise RechenFehler("Pensionsalter < Startalter.")

    if steuersatz_eff:
        anker_txt = (f"Anker: {steuer_anker}" if steuer_anker
                     else "Anker: vom Berater gesetzt")
        warnungen.append(
            f"Steuer ist eine SCHÄTZUNG (effektiver Satz {steuersatz_eff*100:.1f} %, "
            f"{anker_txt}); kantonal/individuell zu verifizieren.")
    else:
        warnungen.append("Kein Steuersatz gesetzt → Steuer = 0 (vor Steuern).")

    rows = []
    vermoegen = float(vermoegen_start)
    ausgaben_j = float(ausgaben)
    for alter in range(int(start_alter), int(end_alter) + 1):
        jahr = int(start_jahr) + (alter - int(start_alter))
        erwerb = float(lohn) if alter < pensionsalter else 0.0
        r_pk = float(pk_rente) if alter >= pensionsalter else 0.0
        r_ahv = float(ahv_rente) if alter >= ahv_alter else 0.0
        total_eink = erwerb + r_pk + r_ahv

        steuerbar = max(0.0, total_eink - abzug_pauschale)
        steuer = round(steuerbar * steuersatz_eff, 0)
        eink_nach_steuer = total_eink - steuer
        saldo = eink_nach_steuer - ausgaben_j
        vermoegen = vermoegen * (1 + rendite) + saldo

        rows.append({
            "jahr": jahr, "alter": alter,
            "erwerb": round(erwerb, 0), "rente_ahv": round(r_ahv, 0),
            "rente_pk": round(r_pk, 0), "total_einkommen": round(total_eink, 0),
            "steuer": steuer, "steuer_geschaetzt": bool(steuersatz_eff),
            "einkommen_nach_steuer": round(eink_nach_steuer, 0),
            "ausgaben": round(ausgaben_j, 0), "saldo": round(saldo, 0),
            "vermoegen_ende": round(vermoegen, 0),
        })
        ausgaben_j *= (1 + teuerung)        # Ausgaben mit Teuerung fortschreiben

    return {
        "rows": rows,
        "annahmen": {"rendite": rendite, "teuerung": teuerung,
                     "steuersatz_eff": steuersatz_eff, "abzug_pauschale": abzug_pauschale,
                     "pensionsalter": pensionsalter, "ahv_alter": ahv_alter},
        "vermoegen_start": round(float(vermoegen_start), 0),
        "vermoegen_ende": rows[-1]["vermoegen_ende"] if rows else None,
        "warnungen": warnungen,
    }
