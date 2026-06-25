# versicherungsvergleich

Deterministischer **Versicherungs-Offertenvergleich** für die `sf-calc`-Suite. Aus der
Ausschreibung (Sparten + geforderte Deckungen) und den **extrahierten** Offerten je
Versicherer entsteht eine Vergleichsmatrix mit Totalen (inkl. Eidg. Stempelabgabe), Ranking,
Vollständigkeits- und Deckungs-Checks. Mit `--json` und `--protokoll`.

> **Keine Kundendaten / keine Web-Recherche.** Die Offertenwerte werden vorgelagert von
> Agenten aus den Offert-Dokumenten extrahiert; dieses Tool rechnet und prüft nur
> (deterministisch) — keine erfundenen Zahlen, keine vergessene Sparte.

## Verwendung
```bash
python3 -m versicherungsvergleich beispiel > vergleich.json
python3 -m versicherungsvergleich vergleichen --config vergleich.json
python3 -m versicherungsvergleich vergleichen --config vergleich.json --json --protokoll nachweis.md
```

## Was es prüft/rechnet
- **Vergleichsmatrix** Sparten × Versicherer → Prämie.
- **Eidg. Stempelabgabe** (StG Art. 21–23): 5 % auf Sach/Haftpflicht/Motorfahrzeug,
  0 % auf KTG/UVG/UVG-Z (befreit). Total inkl. Stempel je Versicherer.
- **Ranking** (günstigster zuerst), `guenstigster`.
- **Vollständigkeit**: welche Sparten je Versicherer offeriert/fehlen; wer verzichtet.
- **Deckungs-Check** gegen die Ausschreibung: Unterdeckung (Versicherungssumme) bzw. höherer
  Selbstbehalt werden geflaggt — Prämien sind nur bei gleicher Deckung vergleichbar.

## Config (JSON)
`ausschreibung.sparten[{name, versicherungssumme, selbstbehalt}]` +
`offerten[{versicherer, status: offeriert|verzichtet, positionen[{sparte, praemie,
versicherungssumme, selbstbehalt, bemerkung, stempel_satz?}]}]`.

## Grenzen (ehrlich)
- Stempelabgabe vereinfacht (Standardfälle); im Einzelfall verifizieren.
- Vergleich nur so gut wie die extrahierten Eingaben — Deckungsabweichungen werden geflaggt,
  aber die fachliche Würdigung (welche Deckung ist nötig) bleibt beim Berater.

## Tests
7 Tests (Stempel-Befreiung, Total, Ranking, Vollständigkeit, Verzicht, Deckungsabweichungen).

## Lizenz
MIT (analog sf-calc).
