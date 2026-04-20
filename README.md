# sf-calc

**Elektro-Rechner** fuer den GEE-Alltag. Kleine, fokussierte Python-Skripte
fuer Schnellberechnungen am Arbeitsplatz.

> Teil der strawberryfactory GEE Tools Suite. Siehe [sf-docs](https://github.com/strawberryfactory/sf-docs).

---

## Inhalt (aktuell)

| Tool | Zweck |
|------|-------|
| `leistungsrechner.py` | Wirk-/Blind-/Scheinleistung aus Strom + Spannung + cos phi |

## Inhalt (geplant)

| Tool | Zweck |
|------|-------|
| `kabeldimensionierung.py` | Kabelquerschnitt nach Strombelastbarkeit und Spannungsfall |
| `kurzschluss.py` | Ik max/min nach NIN 4.3 |
| `pv_ertragsschaetzung.py` | Jahresertrag fuer PV-Anlage |

---

## Verwendung

### Leistungsrechner

```bash
python3 leistungsrechner.py <Strom> [Optionen]
```

**Argumente:**
- `Strom`: Stromwert, entweder Betrag (`16`) oder Vektor (`3+4j`)
- `--u 400`: Spannung in V (default 400)
- `--phi 0.85`: cos phi (default 0.85, nur ohne Vektor)
- `--phase L1`: 1-phasig L1/L2/L3 (default 3-phasig)

**Beispiele:**

```bash
# 3-phasig, 16 A bei 400 V, cos phi 0.85
python3 leistungsrechner.py 16

# 1-phasig L1 bei 230 V, 10 A
python3 leistungsrechner.py 10 --u 230 --phase L1

# Vektor-Eingabe
python3 leistungsrechner.py 3+4j --u 400
```

---

## Requirements

- Python 3.11+
- Nur Standard-Library (aktuell)

---

## Mitwirken

Pull Requests willkommen. Grundsatz: jede Aenderung auf einem `wip/*`-Branch,
PR gegen `main`. Tests folgen.

---

## Lizenz

MIT. Siehe [LICENSE](./LICENSE).
