# finanzplanung

Normbasierter Rechner für die **Schweizer Finanzplanung / Vorsorge** — als CLI, damit
Skripte und Skills ihn deterministisch aufrufen können (`--json`). Teil der
strawberryfactory `sf-calc`-Suite, gleicher Stil wie `kabelberechnung`.

> **Keine Kundendaten.** Das Tool enthält ausschliesslich generische Normwerte (AHV/IV,
> BVG, Säule 3a, Tragbarkeit). Personenbezogene Zahlen werden nur als Aufruf-Argumente
> übergeben und nirgends gespeichert.

## Prinzip
Das Rechnen macht **geprüfter Python-Code**, nicht ein Sprachmodell. Normwerte tragen
Stand, Quelle und ein Verifikations-Flag; bei nicht verifizierten Werten **warnt** das
Tool, statt Scheingenauigkeit zu liefern (wie `kabelberechnung` bei fehlenden NIN-Tabellen).

## Verwendung
```bash
python3 -m finanzplanung show --tabellen          # Normwerte + Quellen
python3 -m finanzplanung tragbarkeit --wert 1200000 --hypothek 900000 --einkommen 180000
python3 -m finanzplanung plan --einkommen 100000 --beitragsjahre 44 --bvg-guthaben 500000 --vermoegen 200000
python3 -m finanzplanung plan ... --json          # maschinenlesbar für Skills
```

## Kommandos
| Kommando | Zweck |
|----------|-------|
| `show [--tabellen] [--annahmen]` | Normwerte / Planungsannahmen anzeigen |
| `set <annahme> <wert>` / `reset` | Planungsannahmen (rendite, teuerung, …) |
| `ahv` | AHV-Altersrente (Skala 44, Näherung) |
| `referenzalter` | AHV-Referenzalter aus Jahrgang + Geschlecht (AHV21-Übergang) |
| `ahv-vorbezug` | AHV-Rentenvorbezug: lebenslange Kürzung (reguläre Sätze) |
| `bvg-rente` | BVG-Rente aus Altersguthaben (Umwandlungssatz) |
| `bvg-projektion` | Altersguthaben bis Pensionierung fortschreiben |
| `saeule3a` | Maximaler 3a-Beitrag (mit/ohne PK) |
| `luecke` | Vorsorgelücke (Zielrente − 1./2. Säule) |
| `kapitalbedarf` | Kapital, um eine Jahres-Lücke zu decken (Barwert, real) |
| `verzehr` | Wie lange ein Kapital bei indexierter Entnahme reicht |
| `tragbarkeit` | Wohneigentum: Wohnkostenquote ≤ 33⅓ %, Belehnung ≤ 80 % |
| `plan` | Vollständige Pensionierungs-Analyse (verkettet) |
| `projektion` | Mehrjährige Finanz- und Steuerplanung (Jahres-Tabelle, Lohn→Rente, Vermögensverlauf) |

Die Steuer in `projektion` ist eine **transparent gekennzeichnete Schätzung** (effektiver
Satz, in der echten Veranlagung verankert) — kein kantonaler Tarif im Tool. Jede
Steuerzeile ist als geschätzt markiert (`*` / `steuer_geschaetzt`).

## Rechennachweis
Jedes Rechen-Kommando akzeptiert `--protokoll <datei.md>`: der Aufruf hängt **Eingaben +
exakte Python-Ausgabe** als Markdown an. So bleibt jede Zahl im Bericht später nachvollziehbar
(Eingabe → Tool → Ausgabe). Beispiel:
```bash
python3 -m finanzplanung plan --einkommen 100000 --bvg-rente 49732 --protokoll nachweis.md
```

## Normbezug & Quellen
- **AHV/IV** Rentenskala 44 (BSV/ahv-iv.ch)
- **BVG** SR 831.40 (Umwandlungssatz, Mindestzins, Koordinationsabzug)
- **Säule 3a** ESTV (Maximalbeiträge)
- **Tragbarkeit** FINMA-RS / Banken-Selbstregulierung

- **AHV21-Referenzalter** (in Kraft 1.1.2024): Männer 65; Frauen bis Jg. 1960 = 64,
  Jg. 1961–1963 gestaffelt (+3/+6/+9 Monate), ab Jg. 1964 = 65.

Normjahr-Default ist **2025** (AHV-Maximalrente 2'520/Mt = 30'240/Jahr). Die AHV21-Sonder-
kürzungssätze der Übergangsgeneration Frauen (Jg. 1961–1969) sind **einkommensabhängig und
nicht abgebildet** — der Vorbezug-Rechner nutzt die regulären 6,8 %/Jahr als Obergrenze und
warnt. Werte vor produktivem Einsatz gegen die aktuelle offizielle Mitteilung prüfen.

## Grenzen (ehrlich)
- AHV-Rente ist eine **Näherung** (lineare Interpolation der Rentenformel); exakt nur via
  Rentenvorausberechnung der Ausgleichskasse.
- BVG nutzt den **obligatorischen** Mindest-Umwandlungssatz; überobligatorische Guthaben
  haben oft tiefere Sätze (PK-Reglement).
- Steuern (Kapitalbezugssteuer etc.) sind **nicht** abgebildet — kantonal, separat.
- Planungsannahmen (Rendite, Teuerung, Pensionsalter) sind **vom Berater zu setzen**.

## Tests
```bash
python3 -m pytest finanzplanung/test_finanzplanung.py -q
```
Tests u.a. Validierung des Tragbarkeits-Beispiels (35.4 %, nicht tragbar) sowie
AHV21-Referenzalter (Übergangsgeneration) und Vorbezugskürzung.

## Lizenz
MIT (analog sf-calc).
