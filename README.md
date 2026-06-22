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
alias kabelberechnung='python3 .../sf-calc/kabelberechnung'
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
| `verlegeart` | A1 A2 B1 B2 C D E F G | C |
| `kabel` | FE05-C | FE05-C |
| `strom` | A (Pflicht) | — |
| `laenge` | m | 20 |
| `cosphi` | 0–1 | auto (0.85 / 1.0) |
| `umgebung` | °C | 30 |
| `stromkreise` | Anzahl (Häufung) | 1 |
| `max_du` | zul. ΔU % | 3 |

### Parallelverlegung & Kurzschluss-Nachweis

Reicht ein Einzelquerschnitt nicht (hohes `Ib`), schlägt das Tool die Aufteilung
auf **n parallele Kabel** je Aussenleiter vor (n = 2, 3, 4) — automatisch, oder
erzwungen mit `--parallel`.

- Lastseitig: `Iz_gesamt = n · Iz · k_temp · k_häufung(n·Stromkreise)`, `ΔU = ΔU/n`.
- **Kurzschluss (sicherheitskritisch):** jeder *einzelne* Parallelleiter muss den
  **vollen** Ik aushalten (nicht Ik/n — ein Fehler in einem Kabel führt den ganzen
  Strom über diesen Leiter). Adiabatisch: `k²·S² ≥ Ik²·t_aus`.

```bash
kabelberechnung calc --strom 600 --verlegeart E --parallel
kabelberechnung calc --strom 600 --verlegeart E --ik 25 --t-aus 0.1   # mit KS-Nachweis
kurzschlussberechnung calc --json | kabelberechnung calc --strom 600  # Ik per Pipe
```

### `print` → Markdown für `/piag-pdf`

Legt ein `.md` mit piag-pdf-kompatiblem Frontmatter im PIAG-Projektordner ab
(Projektnummer-Auflösung wie die Shell-Funktion `p`). Dateiname:
`<Projekt>_YYMMdd_Kabelberechnung[_<Verteilung>][_<Klemme>].md`.
`--pdf` ruft direkt `piag-pdf` auf.

### Datenstand (wichtig)

Iz-Tabellen werden **nur verifiziert** genutzt — kein Raten. Stand:

- ✅ **A1, A2, B1, B2, C, D und E**, Kupfer, PVC (70 °C) und VPE/EPR (90 °C),
  je 1- und 3-phasig — abgelesen aus **NIN SN 411000:2025**, 5.2.3.1.1.11,
  Tab. 4–7 und 12/14 (Quelle: `referenz/nin_strombelastbarkeit_260622.pdf`).
- ⏳ **F/G** (einadrige Kabel — brauchen zusätzliche Anordnungs-Dimension)
  und **Aluminium** (braucht Al-Kabeltyp + Al-R′ für den Spannungsfall): folgt.

`calc` verweigert nicht-verifizierte Kombinationen mit klarer Meldung.

> **Hinweis:** Das frühere `kabelrechnerFE05.py` nutzte unter dem Label
> „Verlegeart C" faktisch die **B1**-Werte. Dieses Tool verwendet die echten
> NIN-Spalten — Ergebnisse können daher von den Vorläufer-Skripten abweichen.

---

## kurzschlussberechnung

CLI für die Kurzschlussberechnung nach **IEC 60909-0** (Netzeinspeisung → Trafo →
Leitungskaskade). Pro Fehlerort `Ikmax` (cmax 1.10), `Ikmin` (cmin 0.95),
Stossstrom `ip`, thermisch wirksamer Strom `Ith`, zulässige Kurzschlussdauer
`Tkzul` (I²t). Rechenkern aus dem reviewten Studium-Skript (V. Wouters, HSLU).

### Verwendung

```bash
kurzschlussberechnung -h
kurzschlussberechnung set trafo 630     # Standardgrösse, füllt uk/ur automatisch
kurzschlussberechnung set n_trafo 2     # parallele Trafos (Bank = n × kVA)
kurzschlussberechnung set s 95          # Leitungsquerschnitt
kurzschlussberechnung calc              # Schnellmodus (Netz → Trafo → 1 Leitung)
kurzschlussberechnung calc --config netz.py   # komplexe Kaskade (.py mit CONFIG / .json)
kurzschlussberechnung -i                # interaktiv (Trafo zuerst)
```

**Trafo aus Katalog** (für Frühphasen): `set trafo <kVA>` wählt 400 / 630 / 800 /
1000 / 1600 kVA und belegt `uk`/`ur` mit typischen Default-Annahmen (Öl-
Verteiltrafo Dyn5, projektweise prüfen). `set n_trafo <n>` für parallele Trafos.

**Schnellmodus-Parameter** (`set <param> <wert>`): `un`, `sk`, `xq_rq` (Netz);
`trafo`, `n_trafo`, `uk`, `ur` (Trafo); `s`, `laenge`, `material`, `isolierung`,
`n_parallel`, `ta` (Leitung). Aluminium / mehrstufige Kaskaden über `--config`.

### Verbindung zur Kabelberechnung (Pipe)

`--json` gibt nur den Daten-Kontrakt aus → direkt in `kabelberechnung` pipebar:

```bash
kurzschlussberechnung calc --json | kabelberechnung calc --strom 600 --parallel
```

Kontrakt: `{"ik_max_ka": …, "ik_min_ka": …, "t_aus_s": …, "ort": "…"}`
(`ik_max_ka` = Ik3max am Leitungsanfang, worst case für den I²t-Nachweis am Kabel).

---

## Weitere Skripte (Bestand)

| Tool | Zweck |
|------|-------|
| `leistungsrechner.py` | Wirk-/Blind-/Scheinleistung |
| `kabelrechnerFE05.py`, `Kabelrechner1phFE05.py` | Vorläufer von `kabelberechnung` |
| `Kurzschlussberechnung.py` | Vorläufer von `kurzschlussberechnung` (Kern übernommen) |

### leistungsrechner

```bash
python3 leistungsrechner.py <Strom> [--u 400] [--phi 0.85] [--phase L1]
```

Wirk-/Blind-/Scheinleistung aus Strom + Spannung + cos phi. `Strom` als Betrag
(`16`) oder Vektor (`3+4j`); `--phase L1/L2/L3` = 1-phasig (default 3-phasig).

---

## Mitwirken

Pull Requests willkommen. Grundsatz: jede Änderung auf einem `wip/*`-Branch,
PR gegen `main`. Nur Python-Standardbibliothek.

---

## Lizenz

MIT. Siehe [LICENSE](./LICENSE).
