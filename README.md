# sf-calc

Elektro-Rechner fuer den GEE-Alltag (Kabel, Kurzschluss, PV, Leistung).

> Teil der strawberryfactory GEE Tools Suite.

---

## kurzschlussberechnung

CLI für die Kurzschlussberechnung nach **IEC 60909-0** (Netzeinspeisung → Trafo →
Leitungskaskade). Rechnet pro Fehlerort `Ikmax` (cmax 1.10, kalte Leitung),
`Ikmin` (cmin 0.95, heisse Leitung), Stossstrom `ip`, thermisch wirksamen Strom
`Ith` und die zulässige Kurzschlussdauer `Tkzul` (I²t-Nachweis). Rechenkern
aus dem reviewten Studium-Skript (V. Wouters, HSLU).

### Installation / Alias

```bash
alias kurzschlussberechnung='python3 .../sf-calc/kurzschlussberechnung'
export PYTHONPATH="$HOME/Documents/1_arbeit/1d_strawberryfactory/repos/sf-calc:$PYTHONPATH"
```

Nur Python-Standardbibliothek. Einstellungen in `~/.config/kurzschlussberechnung/state.json`.

### Verwendung

```bash
kurzschlussberechnung -h
kurzschlussberechnung set sk 500        # Netz-Kurzschlussleistung [MVA]
kurzschlussberechnung set s 95          # Leitungsquerschnitt [mm2]
kurzschlussberechnung show
kurzschlussberechnung calc              # Schnellmodus (Netz → Trafo → 1 Leitung)
kurzschlussberechnung calc --config netz.py   # komplexe Kaskade (.py mit CONFIG / .json)
kurzschlussberechnung -i                # interaktiv
```

**Trafo aus Katalog** (für Frühphasen): `set trafo 630` wählt eine Standardgrösse
(400 / 630 / 800 / 1000 / 1600 kVA) und füllt `uk`/`ur` mit typischen Default-
Annahmen; `set n_trafo 2` für parallele Trafos (Bank = n × kVA, gleiches uk/ur).
Im interaktiven Modus wird der Trafo zuerst gewählt.

**Schnellmodus-Parameter** (`set <param> <wert>`): `un`, `sk`, `xq_rq` (Netz);
`trafo`, `n_trafo`, `uk`, `ur` (Trafo, uk/ur aus Katalog vorbelegt); `s`, `laenge`,
`material`, `isolierung`, `n_parallel`, `ta` (Leitung). Für mehrstufige Kaskaden
oder Aluminium den `--config`-Modus nutzen.

### Verbindung zur Kabelberechnung (Pipe)

`--json` gibt nur den Daten-Kontrakt aus → direkt in `kabelberechnung` pipebar:

```bash
kurzschlussberechnung calc --json | kabelberechnung calc --strom 600 --parallel
```

Kontrakt: `{"ik_max_ka": …, "ik_min_ka": …, "t_aus_s": …, "ort": "…"}`
(`ik_max_ka` = Ik3max am Leitungsanfang, worst case für den I²t-Nachweis am Kabel).

---

## Lizenz

MIT. Siehe [LICENSE](./LICENSE).
