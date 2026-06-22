# sf-calc

Elektro-Rechner fuer den GEE-Alltag (Kabel, Kurzschluss, PV, Leistung).

> Teil der strawberryfactory GEE Tools Suite.

---

## kabelberechnung

CLI zur Kabeldimensionierung nach **NIN / IEC 60364-5-52**: thermischer
Nachweis (Ib ≤ Iz · k_temp · k_häufung) **und** Spannungsfall (inkl. Reaktanz).
Stilvorbild: `note` / `agenda` — persistenter Zustand, der pro Aufruf via Flags
übersteuerbar ist, plus ein interaktiver Modus.

### Installation / Alias

```bash
alias kabelberechnung='python3 -m kabelberechnung'
# benötigt sf-calc im PYTHONPATH, z.B.:
export PYTHONPATH="$HOME/Documents/1_arbeit/1d_strawberryfactory/repos/sf-calc:$PYTHONPATH"
```

Nur Python-Standardbibliothek. Einstellungen liegen in
`~/.config/kabelberechnung/state.json`.

### Verwendung

```bash
kabelberechnung -h                       # Hilfe
kabelberechnung set verlegeart C         # Parameter dauerhaft setzen
kabelberechnung set strom 16
kabelberechnung show [--tabellen]        # Zustand / Tabellen-Abdeckung
kabelberechnung calc [--laenge 25 ...]   # rechnen (Flags übersteuern)
kabelberechnung -i                       # interaktiv durchklicken (1, 2, 3 …)
kabelberechnung print 3142 --verteilung UV4OG --klemme K12 [--pdf]
```

**Parameter** (`set <param> <wert>` oder als `--flag` bei `calc`/`print`):

| Param | Werte | Default |
|-------|-------|---------|
| `spannung` | 230 (1-ph) / 400 (3-ph) / 690 (3-ph) | 400 |
| `verlegeart` | A1 A2 B1 B2 C D1 D2 E F G | C |
| `kabel` | FE05-C | FE05-C |
| `strom` | A (Pflicht) | — |
| `laenge` | m | 20 |
| `cosphi` | 0–1 | auto (0.85 / 1.0) |
| `umgebung` | °C | 30 |
| `stromkreise` | Anzahl (Häufung) | 1 |
| `max_du` | zul. ΔU % | 3 |

### `print` → Markdown für `/piag-pdf`

Legt ein `.md` mit piag-pdf-kompatiblem Frontmatter im PIAG-Projektordner ab
(Projektnummer-Auflösung wie die Shell-Funktion `p`). Dateiname:

```
<Projekt>_YYMMdd_Kabelberechnung[_<Verteilung>][_<Klemme>].md
```

`--pdf` ruft direkt `piag-pdf` auf; sonst in Claude `/piag-pdf` auf die Datei anwenden.

### Datenstand (wichtig)

Iz-Tabellen werden **nur verifiziert** genutzt — kein Raten. Stand:

- ✅ **Verlegeart C**, Cu, 70 °C (FE05/PVC), 1- und 3-phasig — verifiziert
  gegen die reviewten Skripte.
- ⏳ Übrige Verlegearten (A1/A2/B1/B2/D/E/F/G) und weitere Kabel/Materialien:
  Slots vorhanden, Werte werden aus NIN/Paperless nachgepflegt und von
  Samuel freigegeben. `calc` verweigert nicht-verifizierte Kombinationen mit
  klarer Meldung. Abdeckung: `kabelberechnung show --tabellen`.

Korrekturfaktoren (Temperatur Tab. B.52.14, Häufung Tab. B.52.17) und die
Reaktanzbeläge X′ sind eingepflegt.

---

## Weitere Skripte (Bestand)

| Tool | Zweck |
|------|-------|
| `leistungsrechner.py` | Wirk-/Blind-/Scheinleistung |
| `kabelrechnerFE05.py`, `Kabelrechner1phFE05.py` | Vorläufer von `kabelberechnung` |
| `Kurzschlussberechnung.py` | Ik max/min nach IEC 60909-0 |

---

## Lizenz

MIT. Siehe [LICENSE](./LICENSE).
