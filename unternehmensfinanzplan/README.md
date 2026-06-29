# unternehmensfinanzplan

Deterministischer **Unternehmens-Finanzplan (3-Statement)** für die strawberryfactory
`sf-calc`-Suite — Plan-Erfolgsrechnung, Plan-Bilanz, Geldfluss/Liquidität und Kennzahlen
aus dokumentierten Annahmen. CLI mit `--json`, damit Skills ihn deterministisch nutzen.

> **Keine Kundendaten.** Generisch; Zahlen kommen ausschliesslich aus der übergebenen Config.

## Prinzip
Das Rechnen macht geprüfter Code, OR-nah (Bilanz/ER-Gliederung), Bilanz selbstabstimmend
(Check = 0). Die Steuer ist ein **Gewinnsteuersatz als Annahme** (kein kantonaler Tarif) —
wie beim privaten Finanzplan transparent zu deklarieren.

## Verwendung
```bash
python3 -m unternehmensfinanzplan beispiel > plan.json     # Vorlage
python3 -m unternehmensfinanzplan plan --config plan.json  # Tabellen
python3 -m unternehmensfinanzplan plan --config plan.json --json
```

## Config (JSON)
| Feld | Bedeutung |
|------|-----------|
| `jahre` | Liste der Planjahre |
| `ertrag` ODER `auslastung`+`vollkapazitaet` | Ertrag je Jahr oder Auslastung × Vollkapazität |
| `personalaufwand`, `uebriger_aufwand` | je Jahr (Zahl oder Liste) |
| `investition`, `nutzungsdauer`, `abschr_methode` (linear/degressiv), `erstjahr_anteil` | Anlagevermögen/Abschreibung |
| `aktienkapital`, `darlehen`, `zins`, `amortisation` | Finanzierung (Amortisation opt., sonst = Abschreibung) |
| `steuersatz`, `debitoren_quote` | Gewinnsteuersatz (Annahme), Debitoren als % des Ertrags |

## Rechennachweis
`plan` akzeptiert `--protokoll <datei.md>`: hängt die **Eingabe-Config + exakte Python-Ausgabe**
als Markdown an — jede Zahl im Bericht bleibt nachvollziehbar.
```bash
python3 -m unternehmensfinanzplan plan --config plan.json --protokoll nachweis.md
```

## Output
Plan-ER (Ertrag → EBITDA → EBIT → EBT → Steuern → Erfolg), Plan-Bilanz (Bank als Residual,
Debitoren, Anlagevermögen / Darlehen, Eigenkapital), Geldfluss (inkl. Schuldendienst und
DSCR je Jahr), Kennzahlen (EBITDA-/EBIT-/EBT-Marge, Eigenkapitalquote, DSCR inkl. Minimum
über den Plan, Nettoverschuldung, Nettoverschuldung/EBITDA). `bilanz_ok` bestätigt den
Bilanzcheck.

**EBITDA** ist strikt *vor* Zinsen, Steuern und Abschreibungen definiert:
EBITDA = Ertrag − betrieblicher Aufwand (Personal + übriger Aufwand). Der Finanzaufwand
(Zinsen) wird erst zwischen EBIT und EBT abgezogen: EBIT = EBITDA − Abschreibung,
EBT = EBIT − Finanzaufwand. **DSCR** = (Cashflow operativ + Zins) / (Amortisation + Zins).

## Grenzen (ehrlich)
- Steuer = pauschaler Gewinnsteuersatz (kein kantonaler Tarif, Tax-on-Tax nicht modelliert).
- Geldfluss vereinfacht jährlich (kein Monatsraster).
- Planzahlen beruhen auf Annahmen und sind keine Zusicherung.

## Tests
Tests mit einer fiktiven Beispiel-Config: prüfen die Beziehungen (EBITDA = Ertrag −
betrieblicher Aufwand *vor Zinsen*, EBIT = EBITDA − Abschreibung, EBT = EBIT − Finanzaufwand,
EBITDA bleibt zinsunabhängig, DSCR/Nettoverschuldung, Steuer nur auf Gewinn, Bilanzcheck = 0,
sinkendes Anlagevermögen/Darlehen).

## Lizenz
MIT (analog sf-calc).
