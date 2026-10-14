"""Team-Einstellungen dieser Struktur -- das ist die EINZIGE Datei, die pro Struktur angepasst wird.

Alle Namen kleingeschrieben und genau so, wie sie in der Spalte "Vertriebspartner" der Google-Tabelle stehen
(Sonderzeichen wie ş werden automatisch zu s).
Quoten als Dezimalzahl: Stufe 1 = 0.20, 2 = 0.37, 3 = 0.55, 4 = 0.70, 5 = 0.80, 6 = 0.90.
"""

# Du selbst (Strukturleiter): Name wie in der Tabelle (klein) und deine Stufe.
LEITER_KEY = "adel"
LEITER_QUOTE = 0.80

# Alle Personen deiner Struktur: Name -> deren eigene Stufe/Quote. Du selbst musst hier auch stehen.
# Dein Anteil an fremdem Geschäft = deine Quote minus deren Quote (Differenz).
TEAM_QUOTEN = {
    "adel": 0.80,       # Eigengeschäft
    "emirhan": 0.80,    # gleiche Stufe wie Adele -> 0 Differenz
    "seher": 0.55,      # Stufe 3
    "büsra": 0.37,      # Stufe 2
    "busra": 0.37,      # ohne Umlaut, falls so geschrieben
    "birtan": 0.55,
    "ikram": 0.20,
    "mahdi": 0.55,
}

# Sonderfälle: dein Anteil ist NICHT die normale Differenz, sondern fest vorgegeben
# (z.B. geteiltes Overhead mit einer weiteren Person -> nur die halbe Differenz). Leer lassen, wenn es keine gibt.
ANTEIL_OVERRIDE = {
    "mahdi": 0.125,   # geteiltes Overhead -> halbe Differenz (12,5% statt 25%)
    "büsra": 0.215,   # geteiltes Overhead -> halbe Differenz (21,5% statt 43%)
    "busra": 0.215,
    "seher": 0.125,
}
