# revisionspruefung

Deterministische **Prüf-Checks für die eingeschränkte Revision** (Schweizer Standard SER,
OR Art. 728 ff.) — Teil der `sf-calc`-Suite. Bildet die Essenz eines Excel-Prüftools
(z.B. Fastview) als CLI ab: formelle Abstimmungen, Kapitalschutz, Schwellen, analytische
Vorjahresvergleiche. Mit `--json` und `--protokoll`.

> **Keine Kundendaten.** Prüft die übergebene Jahresrechnung. Das Tool stellt Sachverhalte
> fest und flaggt Auffälligkeiten — das **Prüfungsurteil** (Befragungen/Detailprüfungen nach
> SER) bleibt beim zugelassenen Revisor.

## Verwendung
```bash
python3 -m revisionspruefung beispiel > jr.json
python3 -m revisionspruefung pruefen --config jr.json
python3 -m revisionspruefung pruefen --config jr.json --json --protokoll nachweis.md
```

## Prüfungen
- **Bilanz balanciert** (Aktiven = Passiven).
- **Jahresgewinn ER = Bilanz**, **Bilanzgewinn = Vortrag + Jahresgewinn**.
- **Gewinnverwendung** stimmt auf den Bilanzgewinn.
- **Kapitalschutz** Art. 725a (Kapitalverlust) / 725b (Überschuldung).
- **Revisionsart** (ordentlich/eingeschränkt/Opting-out) nach Art. 727/727a.
- **Analytische Prüfung**: Vorjahresvergleich (wesentliche Abweichungen) + Kennzahlen
  (Bruttomarge, Personalquote).

## Grenzen (ehrlich)
- Kein Prüfungsurteil, keine Befragungen/Detailprüfungen — die bleiben beim Revisor.
- Bei Erstellung UND Revision durch dieselbe Firma: Unabhängigkeit/Selbstprüfung
  organisatorisch/personell sicherstellen (Art. 729 OR).

## Tests
8 Tests, validiert gegen ein bekanntes JR-Beispiel (alle Abstimmungen, Kapitalverlust- und
Überschuldungs-Erkennung, Schwellen).

## Lizenz
MIT (analog sf-calc).
