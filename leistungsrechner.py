import sys
import math
import cmath
from datetime import datetime


def fail(msg):
    print(f"Fehler: {msg}")
    sys.exit(1)


if len(sys.argv) < 2:
    print("Verwendung: python3 leistungsrechner.py <Strom> [Optionen]")
    print("  Strom:        16  oder  3+4j  (Vektor)")
    print("  --u 400       Spannung in V (default 400)")
    print("  --phi 0.85    cos phi (default 0.85, nur ohne Vektor)")
    print("  --phase L1    1-phasig L1/L2/L3 (default 3-phasig)")
    sys.exit(1)

args = sys.argv[1:]


def get_arg(flag, default=None):
    return args[args.index(flag) + 1] if flag in args else default


I_input = args[0]
phase = get_arg("--phase", "3")

# Spannung
try:
    U = float(get_arg("--u", "400"))
except ValueError:
    fail("Spannung muss eine Zahl sein")
if U <= 0:
    fail("Spannung muss grösser als 0 sein")
if phase == "3" and not 370 <= U <= 420:
    if input(f"Warnung: {U} V ist untypisch für 3-phasig. Weiter? (j/n): ").lower() != "j":
        sys.exit(0)

# Strom (skalar oder komplex)
try:
    if "j" in I_input:
        I = complex(I_input)
        I_betrag = abs(I)
        winkel = math.degrees(cmath.phase(I))
        cos_phi = math.cos(cmath.phase(I))
    else:
        I_betrag = float(I_input)
        cos_phi = float(get_arg("--phi", "0.85"))
        if not -1 <= cos_phi <= 1:
            fail("cos_phi muss zwischen -1 und 1 sein")
        winkel = math.degrees(math.acos(cos_phi))
except ValueError:
    fail("Strom als Zahl (16) oder Vektor (3+4j), cos_phi als Zahl")

if I_betrag <= 0:
    fail("Strom muss grösser als 0 sein")

# Berechnung (Faktor: sqrt(3) für 3-phasig, 1 für 1-phasig)
if phase == "3":
    faktor = math.sqrt(3)
    system_str = f"{U:g} V / 3-phasig"
elif phase in ("L1", "L2", "L3"):
    faktor = 1
    system_str = f"{U:g} V / 1-phasig {phase}"
else:
    fail("--phase muss 3, L1, L2 oder L3 sein")

S = U * I_betrag * faktor
P = S * cos_phi
Q = S * math.sin(math.radians(winkel))

# Ausgabe
print()
print(f"System:      {system_str}")
print(f"Spannung:    {U} V")
print(f"Strom:       {I_betrag:.2f} A  |  Winkel: {winkel:.1f}°")
print(f"cos phi:     {cos_phi:.4f}")
print()
print(f"P (Wirk):    {P:.2f} W   /  {P/1000:.2f} kW")
print(f"Q (Blind):   {Q:.2f} VAr /  {Q/1000:.2f} kVAr")
print(f"S (Schein):  {S:.2f} VA  /  {S/1000:.2f} kVA")
print()

with open("leistungsrechner.log", "a") as log:
    log.write(f"{datetime.now()} | {system_str} I={I_betrag:.2f}A phi={winkel:.1f}° P={P:.2f}W Q={Q:.2f}VAr S={S:.2f}VA\n")
