"""
kern.py — Rechenkern der Kurzschlussberechnung nach IEC 60909-0.

Niederspannungsnetz mit Netzeinspeisung + Trafo + Kaskade von Leitungen.
Pro Fehlerort:
  Ikmax  (cmax = 1.10, kalte Leitung 20 C)   -> Ausschaltvermoegen
  Ikmin  (cmin = 0.95, heisse Leitung 80 C)  -> Auslesicherheit
  ip     Stosskurzschlussstrom
  Ith    thermisch wirksamer Kurzschlussstrom
  Tkzul  zulaessige Kurzschlussdauer (I2t-Nachweis)

Herkunft: Studium-Excel "Kurzschlussberechnung 20100308.xls" (EKON2, Wouters,
HSLU 2010), korrigiert und auf IEC 60909-0:2016 gebracht. Korrekturen
(Review V. Wouters 27.04.2026):
  - c konsistent: cmax = 1.10 / cmin = 0.95 (NV 400 V, +-10% nach EN 50160/NIN).
  - Ikmin separat (heisse Leitung, cmin), heisse Leitungstemp = 80 C einheitlich
    (IEC 60909-0 §3.3). NICHT zu verwechseln mit Endtemp nach KS (I2t/k-Faktor).
  - Einpoliger KS: Zk1 = |2*Z1 + Z0| (komplexe Addition).
  - k-Faktor (Studium "q") -> "k" (IEC 60364-5-54).
"""

import math

# -----------------------------
# IEC-60909-Konstanten
# -----------------------------
# Spannungsfaktor c nach IEC 60909-0:2016, Tab. 1
# CH-NV mit Toleranzband +-10% (EN 50160 / NIN) -> cmax = 1.10
C_MAX_LV = 1.10
C_MIN_LV = 0.95

F_HZ = 50.0

ALPHA_CU = 0.00393    # Temperaturkoeffizient Cu 1/K
ALPHA_AL = 0.00403

TEMP_KALT_C = 20      # Referenz-Leitertemperatur fuer R bei 20 C

# Leitungstemperatur fuer Ikmin (R(T) = R(20)*[1+alpha*(T-20)]):
# IEC 60909-0:2016 §3.3 -> vereinfachte Methode mit 80 C einheitlich.
TEMP_BETRIEB_HEISS_C = 80

# Maximal zulaessige Endtemperatur nach KS-Ausschaltung (nur Doku / I2t-Kontext).
TEMP_END_NACH_KS_C = {'PVC': 160, 'XLPE': 250, 'EPR': 250, 'G': 250}

# k-Faktor fuer I2t-Nachweis, A*sqrt(s)/mm2 (IEC 60364-5-54 Tab. 43A)
K_FAKTOR = {
    ('Cu', 'PVC'): 115, ('Cu', 'XLPE'): 143, ('Cu', 'EPR'): 143,
    ('Al', 'PVC'): 76,  ('Al', 'XLPE'): 94,  ('Al', 'EPR'): 94,
}

# -----------------------------
# Kabel-Impedanzen (Referenzwerte 20 C), Cu, in mOhm/m.
# Quelle: Studium-Excel Wouters + NIN-Tabellenwerte.
# -----------------------------
R_PRIME_20_CU = {
    1.5: 12.10, 2.5: 7.28, 4: 4.56, 6: 3.03, 10: 1.81, 16: 1.14, 25: 0.722,
    35: 0.524, 50: 0.387, 70: 0.268, 95: 0.193, 120: 0.155, 150: 0.124,
    185: 0.0991, 240: 0.0754, 300: 0.0601,
}

X_PRIME_CU = {
    1.5: 0.1140, 2.5: 0.1100, 4: 0.1060, 6: 0.1000, 10: 0.0945, 16: 0.0895,
    25: 0.0879, 35: 0.0851, 50: 0.0848, 70: 0.0819, 95: 0.0819, 120: 0.0804,
    150: 0.0804, 185: 0.0804, 240: 0.0797, 300: 0.0797,
}

# Nullimpedanz-Faktoren fuer 4-Leiter-Kabel ohne separaten Schirm.
R0_FAKTOR_DEFAULT = 4.0
X0_FAKTOR_TBL = {
    1.5: 3.99, 2.5: 4.01, 4: 3.98, 6: 4.03, 10: 4.02, 16: 3.98, 25: 4.13,
    35: 3.78, 50: 3.76, 70: 3.66, 95: 3.65, 120: 3.65, 150: 3.65, 185: 3.65,
    240: 3.67, 300: 3.66,
}

NORMQUERSCHNITTE_MM2 = list(R_PRIME_20_CU.keys())


# -----------------------------
# Impedanzfunktionen
# -----------------------------
def netz_impedanz(Sk_MVA, Un_V, xq_rq_ratio=10.0):
    """Thevenin-Impedanz der oeffentlichen Netzeinspeisung (RQ, XQ, ZQ in mOhm).

    Annahme XQ/RQ = 10 (Standard MS/HS-Netze, IEC 60909-0 4.2.1).
    Ohne c-Faktor; c kommt erst bei der Ik-Berechnung dazu.
    """
    ZQ_ohm = Un_V ** 2 / (Sk_MVA * 1e6)
    ratio = xq_rq_ratio
    norm = math.sqrt(1 + ratio ** 2)
    XQ_ohm = ZQ_ohm * ratio / norm
    RQ_ohm = ZQ_ohm / norm
    return RQ_ohm * 1000.0, XQ_ohm * 1000.0, ZQ_ohm * 1000.0


def trafo_impedanz(SrT_kVA, UrT_V, uk_pct, ur_pct,
                   r0_r1_ratio=1.0, x0_x1_ratio=0.95):
    """Trafo-Impedanz (Positiv- und Nullsequenz) in mOhm.

    ZT = uk/100 * UrT^2 / SrT ; RT = ur/100 * UrT^2 / SrT ; XT = sqrt(ZT^2-RT^2).
    Nullsequenz Default: Dyn5 mit r0/r1 = 1.0, x0/x1 = 0.95.
    """
    Sr_VA = SrT_kVA * 1000.0
    ZT = uk_pct / 100.0 * UrT_V ** 2 / Sr_VA
    RT = ur_pct / 100.0 * UrT_V ** 2 / Sr_VA
    XT = math.sqrt(max(ZT ** 2 - RT ** 2, 0.0))
    R0T = RT * r0_r1_ratio
    X0T = XT * x0_x1_ratio
    return (RT * 1000.0, XT * 1000.0, ZT * 1000.0, R0T * 1000.0, X0T * 1000.0)


def leitung_RX(S_mm2, L_m, material='Cu', isolierung='PVC',
               temp_c=20, n_parallel=1,
               r_prime_override=None, x_prime_override=None):
    """Widerstand und Reaktanz einer Leitung in mOhm (RL, XL, gesamt).

    R(T) = R(20) * (1 + alpha*(T-20)). n_parallel: Zahl paralleler Straenge.
    """
    if r_prime_override is not None:
        r_prime_20 = r_prime_override
        x_prime = x_prime_override if x_prime_override is not None else 0.08
    else:
        if material != 'Cu':
            raise ValueError("Nur Cu-Tabelle eingebaut. Fuer Al bitte "
                             "r_prime_override/x_prime_override setzen.")
        r_prime_20 = R_PRIME_20_CU.get(S_mm2)
        x_prime = (x_prime_override if x_prime_override is not None
                   else X_PRIME_CU.get(S_mm2))
        if r_prime_20 is None or x_prime is None:
            raise ValueError(
                f"Kein Tabellenwert fuer {S_mm2} mm2 {material}. "
                f"Bekannte Querschnitte: {NORMQUERSCHNITTE_MM2}")

    alpha = ALPHA_CU if material == 'Cu' else ALPHA_AL
    r_prime_T = r_prime_20 * (1.0 + alpha * (temp_c - TEMP_KALT_C))
    RL = r_prime_T * L_m / n_parallel
    XL = x_prime * L_m / n_parallel
    return RL, XL


def leitung_nullimpedanz(RL, XL, S_mm2=None,
                         r0_faktor=R0_FAKTOR_DEFAULT, x0_faktor=None):
    """Nullsequenz einer Leitung aus Faktoren auf Positivsequenz (R0L, X0L)."""
    if x0_faktor is None:
        x0_faktor = X0_FAKTOR_TBL.get(S_mm2, 3.66) if S_mm2 else 3.66
    return RL * r0_faktor, XL * x0_faktor


# -----------------------------
# Kurzschluss-Groessen
# -----------------------------
def kappa_faktor(R_mOhm, X_mOhm):
    """DC-Stossfaktor kappa nach IEC 60909-0 (Methode A): 1.02 + 0.98*exp(-3 R/X)."""
    if X_mOhm <= 0:
        return 1.0
    return 1.02 + 0.98 * math.exp(-3.0 * R_mOhm / X_mOhm)


def ik3_wert(c, Un_V, Zk3_mOhm):
    """Dreipoliger Anfangs-KS-Wechselstrom Ik3" in A: c*Un / (sqrt(3)*Zk3)."""
    return c * Un_V / (math.sqrt(3) * Zk3_mOhm * 1e-3)


def ik1_wert(c, Un_V, R1_mOhm, X1_mOhm, R0_mOhm, X0_mOhm):
    """Einpoliger KS-Strom Ik1" (Phase-Erde/N) in A.

    Ik1 = sqrt(3)*c*Un / |2*Z1 + Z0|, mit |2*Z1+Z0| = sqrt((2R1+R0)^2+(2X1+X0)^2).
    Gibt (Ik1, Zk1_mOhm) zurueck.
    """
    R_sum = 2.0 * R1_mOhm + R0_mOhm
    X_sum = 2.0 * X1_mOhm + X0_mOhm
    Zk1_mOhm = math.sqrt(R_sum ** 2 + X_sum ** 2)
    Ik1 = math.sqrt(3) * c * Un_V / (Zk1_mOhm * 1e-3)
    return Ik1, Zk1_mOhm


def ip_wert(kappa, Ik_A):
    """Stoss-Kurzschluss-Strom ip = kappa * sqrt(2) * Ik" in A."""
    return kappa * math.sqrt(2) * Ik_A


def m_dc_komponente(kappa, Ta_s, f_Hz=F_HZ):
    """DC-Anteil m nach IEC 60909-0, Gl. 65."""
    if kappa <= 1.0 or Ta_s <= 0:
        return 0.0
    ln_term = math.log(kappa - 1.0)
    if ln_term == 0:
        return 0.0
    num = math.exp(4.0 * f_Hz * Ta_s * ln_term) - 1.0
    denom = 2.0 * f_Hz * Ta_s * ln_term
    return num / denom


def ith_wert(Ik_A, kappa, Ta_s, f_Hz=F_HZ, n=1.0):
    """Thermisch wirksamer KS-Strom Ith = Ik*sqrt(m+n). n=1.0 = generatorfern."""
    m = m_dc_komponente(kappa, Ta_s, f_Hz)
    return Ik_A * math.sqrt(m + n)


def tkzul_wert(k, S_mm2, Ik_A):
    """Zulaessige Kurzschlussdauer tk,zul = (k*S/Ik)^2 in s."""
    if Ik_A <= 0:
        return float('inf')
    return (k * S_mm2 / Ik_A) ** 2


# -----------------------------
# Orchestrierung
# -----------------------------
def _leitungs_impedanzen(leitung, temp_c):
    """Gibt (RL, XL, R0L, X0L) einer Leitung zurueck."""
    S = leitung['S_mm2']
    RL, XL = leitung_RX(
        S_mm2=S, L_m=leitung['L_m'],
        material=leitung.get('material', 'Cu'),
        isolierung=leitung.get('isolierung', 'PVC'),
        temp_c=temp_c, n_parallel=leitung.get('n_parallel', 1),
        r_prime_override=leitung.get('r_prime_mOhm_per_m'),
        x_prime_override=leitung.get('x_prime_mOhm_per_m'),
    )
    R0L, X0L = leitung_nullimpedanz(
        RL, XL, S_mm2=S,
        r0_faktor=leitung.get('r0_faktor', R0_FAKTOR_DEFAULT),
        x0_faktor=leitung.get('x0_faktor'),
    )
    return RL, XL, R0L, X0L


def _netz_und_trafo_impedanzen(quelle, trafo):
    RQ, XQ, ZQ = netz_impedanz(quelle['Sk_MVA'], quelle['Un_V'],
                               quelle.get('xq_rq_ratio', 10.0))
    RT, XT, ZT, R0T, X0T = trafo_impedanz(
        trafo['SrT_kVA'], trafo['UrT_V'], trafo['uk_pct'], trafo['ur_pct'],
        trafo.get('r0_r1_ratio', 1.0), trafo.get('x0_x1_ratio', 0.95),
    )
    # Nullsequenz Netz: vereinfacht = Positivsequenz, ueberschreibbar.
    R0Q = quelle.get('r0q_mOhm', RQ)
    X0Q = quelle.get('x0q_mOhm', XQ)
    return (RQ, XQ, ZQ, R0Q, X0Q, RT, XT, ZT, R0T, X0T)


def _knoten_berechnen(label, c, Un_V, R_kum, X_kum, R0_kum, X0_kum,
                      Ta_s, leitung_fuer_tkzul=None, f_Hz=F_HZ, n_decay=1.0):
    """Kern-Rechnung fuer einen Fehlerort."""
    Zk3 = math.sqrt(R_kum ** 2 + X_kum ** 2)
    phi3_deg = math.degrees(math.atan2(X_kum, R_kum))

    Ik3 = ik3_wert(c, Un_V, Zk3)
    Ik1, Zk1 = ik1_wert(c, Un_V, R_kum, X_kum, R0_kum, X0_kum)
    phi1_deg = math.degrees(math.atan2(2.0 * X_kum + X0_kum, 2.0 * R_kum + R0_kum))

    k3 = kappa_faktor(R_kum, X_kum)
    R_fehler1 = 2.0 * R_kum + R0_kum
    X_fehler1 = 2.0 * X_kum + X0_kum
    k1 = kappa_faktor(R_fehler1, X_fehler1)

    ip3 = ip_wert(k3, Ik3)
    ip1 = ip_wert(k1, Ik1)
    ith3 = ith_wert(Ik3, k3, Ta_s, f_Hz, n_decay)
    ith1 = ith_wert(Ik1, k1, Ta_s, f_Hz, n_decay)

    tkzul3 = tkzul1 = None
    if leitung_fuer_tkzul is not None:
        key = (leitung_fuer_tkzul.get('material', 'Cu'),
               leitung_fuer_tkzul.get('isolierung', 'PVC'))
        k = leitung_fuer_tkzul.get('k_override') or K_FAKTOR.get(key)
        S = leitung_fuer_tkzul['S_mm2']
        n_par = leitung_fuer_tkzul.get('n_parallel', 1)
        if k is not None:
            # I2t-Nachweis IEC 60364-5-54: tk,zul = (k*S/Ith)^2. Bei paralleler
            # Fuehrung wirkt Ith/n_par je Strang; Querschnitt S bleibt je Strang.
            tkzul3 = tkzul_wert(k, S, ith3 / n_par)
            tkzul1 = tkzul_wert(k, S, ith1 / n_par)

    return {
        'label': label, 'c': c,
        'Rk': R_kum, 'Xk': X_kum, 'Zk3': Zk3, 'phi3_deg': phi3_deg,
        'R0k': R0_kum, 'X0k': X0_kum, 'Zk1': Zk1, 'phi1_deg': phi1_deg,
        'Ik3': Ik3, 'Ik1': Ik1, 'kappa3': k3, 'kappa1': k1,
        'ip3': ip3, 'ip1': ip1, 'Ith3': ith3, 'Ith1': ith1,
        'Ta_s': Ta_s, 'Tkzul3': tkzul3, 'Tkzul1': tkzul1,
    }


def _rechne_fall(config, c_mode):
    """Berechnet alle Knoten fuer einen Fall ('max' = Ikmax, 'min' = Ikmin)."""
    quelle = config['quelle']
    trafo = config['trafo']
    leitungen = config.get('leitungen', [])
    Un = quelle['Un_V']

    if c_mode == 'max':
        c = C_MAX_LV
        leitungs_temp = TEMP_KALT_C       # kalte Leitung -> hoechster Strom
    else:
        c = C_MIN_LV
        leitungs_temp = TEMP_BETRIEB_HEISS_C  # heisse Leitung -> Auslesicherheit

    (RQ, XQ, ZQ, R0Q, X0Q, RT, XT, ZT, R0T, X0T) = \
        _netz_und_trafo_impedanzen(quelle, trafo)

    R_kum, X_kum = RQ + RT, XQ + XT
    R0_kum, X0_kum = R0Q + R0T, X0Q + X0T

    Ta_ss = config.get('Ta_sammelschiene_s', 0.1)
    knoten = [_knoten_berechnen(
        label='Sammelschiene (nach Trafo)', c=c, Un_V=Un,
        R_kum=R_kum, X_kum=X_kum, R0_kum=R0_kum, X0_kum=X0_kum,
        Ta_s=Ta_ss, leitung_fuer_tkzul=None)]

    for i, leitung in enumerate(leitungen, start=1):
        RL, XL, R0L, X0L = _leitungs_impedanzen(leitung, temp_c=leitungs_temp)
        R_kum += RL; X_kum += XL; R0_kum += R0L; X0_kum += X0L
        knoten.append(_knoten_berechnen(
            label=leitung.get('label', f'Leitung {i} (Ende)'), c=c, Un_V=Un,
            R_kum=R_kum, X_kum=X_kum, R0_kum=R0_kum, X0_kum=X0_kum,
            Ta_s=leitung.get('Ta_s', 0.1), leitung_fuer_tkzul=leitung))

    return knoten, {
        'RQ': RQ, 'XQ': XQ, 'ZQ': ZQ, 'RT': RT, 'XT': XT, 'ZT': ZT,
        'R0T': R0T, 'X0T': X0T, 'leitungs_temp_c': leitungs_temp,
    }


def berechne_szenario(config):
    """Komplette Kurzschlussberechnung. config-Struktur siehe state.beispiel_config()."""
    knoten_max, grund_max = _rechne_fall(config, 'max')
    knoten_min, grund_min = _rechne_fall(config, 'min')
    return {
        'config': config,
        'grundimpedanzen_max': grund_max,
        'grundimpedanzen_min': grund_min,
        'knoten_max': knoten_max,
        'knoten_min': knoten_min,
    }
