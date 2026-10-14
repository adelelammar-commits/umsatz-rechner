# Umsatz Rechner für deine Struktur einrichten

Gebaut für K&W-Strukturen: berechnet Wohlstandspunkte (WP) und deine Auszahlung (Eigengeschäft + Differenz aus dem Team)
aus einer Google-Tabelle, inklusive Courtageliste je Gesellschaft und Stufe.

## Das Einfachste: Claude Code die Arbeit machen lassen

1. Das Repo auf GitHub **forken**: https://github.com/adelelammar-commits/umsatz-rechner (Button „Fork“) und lokal klonen.
2. Von Adele den **Courtage-Schlüssel** (`COURTAGE_KEY`) privat anfordern. Er gehört NIE ins Repo.
3. Claude Code im Projektordner öffnen und diesen Prompt einfügen (Platzhalter vorher ausfüllen):

```
Richte diesen Umsatz Rechner für meine Struktur ein. Lies zuerst SETUP.md, team.py, app.py und formeln.py.
Ich bin: <dein Name> (so schreibe ich mich in der Tabelle), meine Stufe: <1-6>.
Mein Team (Name = Schreibweise in der Tabelle, Stufe):
  - <Name>, Stufe <x>
  - <Name>, Stufe <x>
Sonderfälle (geteiltes Overhead o.ä., mein Anteil statt Differenz): <Name: Anteil in %, oder "keine">
Aufgaben:
1. Trage mich und mein Team in team.py ein (Quoten: Stufe 1=0.20, 2=0.37, 3=0.55, 4=0.70, 5=0.80, 6=0.90).
2. Erstelle mir lokal .streamlit/secrets.toml (steht in .gitignore, nicht committen) mit APP_PASSWORD (ich nenne es dir),
   SHEET_CSV_URL (Google-Tabelle) und COURTAGE_KEY (ich gebe ihn dir).
3. Teste die App lokal mit streamlit run app.py.
4. Hilf mir, die App auf share.streamlit.io zu deployen (Repo = mein Fork, Datei app.py) und die Secrets dort einzutragen.
Ändere NICHT die Rechenlogik in formeln.py/courtage.py, ohne mich zu fragen.
```

## Die Google-Tabelle

**Vorlage mit einem Klick kopieren** (Dropdowns und Kästchen sind schon drin):
https://docs.google.com/spreadsheets/d/13GoCV3-S5PkYXE3YiW5LU477GSclF5svf05-t8vHyIY/copy

Oder selbst bauen: Erste Zeile, genau diese Spaltenüberschriften:

| Name Kunde | Vertriebspartner | Gesellschaften | Produkt | Beitrag | Laufzeit | Stand | Monat | Ausgezahlt |
|---|---|---|---|---|---|---|---|---|

- **Vertriebspartner**: Name aus `team.py` (du selbst bei Eigengeschäft)
- **Gesellschaften**: z. B. Bayerische, Nürnberger, Hanse Merkur, Hannoversche, Allianz
- **Produkt**: PAV, Rürup, BU, bAV, PKV, ZZ, RL, RS, KFZ, Sach …
- **Beitrag**: Euro pro Monat, **Laufzeit**: Jahre (oder „volle Laufzeit“)
- **Stand**: offen / eingereicht / policiert
- **Monat**: z. B. Oktober
- **Ausgezahlt**: Kästchen (Einfügen → Kästchen), wird abgehakt, wenn die Provision da ist

Tabelle teilen: **Teilen → Jeder mit dem Link → Betrachter**. Als `SHEET_CSV_URL` dann
`https://docs.google.com/spreadsheets/d/<TABELLEN-ID>/export?format=csv&gid=0`.

## Secrets (Streamlit → App → Settings → Secrets)

```toml
APP_PASSWORD = "dein-passwort"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/<ID>/export?format=csv&gid=0"
COURTAGE_KEY = "<von Adele>"
```

## Persönliche App für einzelne Partner (optional)

`mein_umsatz.py` zeigt einer Person nur ihr eigenes Geschäft. Pro Person ein eigener Git-Branch plus eigenes Deployment
(Datei `mein_umsatz.py`), Secrets dort: `APP_PASSWORD`, `SHEET_CSV_URL`, `COURTAGE_KEY`, `MITARBEITER_NAME`, `MITARBEITER_QUOTE`
und zuletzt eine Tabelle `[UNTERSTELLTE]` (Name = Overhead-Satz). Die Tabelle MUSS ganz unten stehen.

## Vertraulich

Die Courtagelisten sind „nur für Vertriebspartner von K&W“. `courtage_s5.enc` ist verschlüsselt, der Schlüssel darf nur an
K&W-Partner gehen. Ohne Schlüssel läuft die App mit dem Standardsatz (ungenauer).
