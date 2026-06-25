"""
ausgabe.py — Formatierung der Resultate (Text fürs Terminal, CHF-Format Schweiz).
Maschinenlesbare Ausgabe läuft über --json direkt im cli.
"""


def chf(x):
    """1234567.5 → \"1'234'567.50\" (Schweizer Tausendertrennung)."""
    try:
        return f"{x:,.2f}".replace(",", "'")
    except (TypeError, ValueError):
        return str(x)


def chf0(x):
    try:
        return f"{x:,.0f}".replace(",", "'")
    except (TypeError, ValueError):
        return str(x)


def prozent(x, stellen=1):
    try:
        return f"{x*100:.{stellen}f} %"
    except (TypeError, ValueError):
        return str(x)


def warnungen_block(res):
    w = res.get("warnungen") or []
    if not w:
        return ""
    return "\n".join("  ⚠ " + z for z in w)


def titel(text):
    return f"\n{text}\n" + "─" * len(text)


def protokoll_append(path, cmd, eingaben: dict, res: dict, tool="finanzplanung"):
    """Hängt Eingaben + Python-Ausgabe als Markdown an einen Rechennachweis an.
    So bleibt jede Zahl im Bericht später nachvollziehbar (Eingabe → Tool → Ausgabe)."""
    import os
    import json
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    neu = not os.path.exists(path)
    out = []
    if neu:
        out.append(f"# Berechnungsprotokoll — {tool}\n")
        out.append("> Rechennachweis: je CLI-Aufruf die Eingaben und die exakte "
                   "Python-Ausgabe. Erlaubt das Nachvollziehen aller Zahlen im Bericht.\n")
    out.append(f"\n## `{cmd}` · {ts}\n")
    out.append("**Eingaben**\n")
    out.append("| Parameter | Wert |")
    out.append("| --- | --- |")
    for k, v in eingaben.items():
        out.append(f"| {k} | {v} |")
    out.append("\n**Ausgabe (Python, deterministisch)**\n")
    out.append("```json")
    out.append(json.dumps(res, ensure_ascii=False, indent=2))
    out.append("```")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
