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
    "emirhan": 0.55,    # vorübergehend 55 % (Stand 2026-11-05), Adels Anteil fest 10 % -> FEST_ANTEIL
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
    "emirhan": 0.0,   # bis Oktober 2026 gleiche Stufe wie Adel -> 0 Differenz (Zeilen mit "Alte Regel")
}

# Feste Anteile für alle Zeilen OHNE Haken bei "Alte Regel" (statt der Differenz).
# Für Absprachen, bei denen dein Anteil bewusst nicht die Differenz ist. Leer lassen, wenn es keine gibt.
FEST_ANTEIL = {
    "emirhan": 0.10,  # Emirhan vorübergehend auf 55 %, Adels Differenz fest 10 % (Stand 2026-11-05)
}
