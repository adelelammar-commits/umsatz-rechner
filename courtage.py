"""Zugriff auf die K&W-Courtageliste (vertraulich, daher nur verschlüsselt im Repo).

Die Tabelle enthält die Sätze für Stufe 5. Alle anderen Stufen sind exakt proportional
(Faktor relativ zu Stufe 5), daher genügt eine Tabelle plus STUFEN_FAKTOR.
Der Schlüssel liegt ausschließlich in den Streamlit-Secrets (COURTAGE_KEY).
"""

import gzip
import io
import re
import unicodedata
from pathlib import Path

import pandas as pd

DATEI = Path(__file__).with_name("courtage_s5.enc")

STUFEN_QUOTE = {1: 0.20, 2: 0.37, 3: 0.55, 4: 0.70, 5: 0.80, 6: 0.90}
STUFEN_FAKTOR = {stufe: quote / 0.80 for stufe, quote in STUFEN_QUOTE.items()}


def lade_tabelle(key):
    from cryptography.fernet import Fernet

    roh = Fernet(key.encode()).decrypt(DATEI.read_bytes())
    return pd.read_csv(io.BytesIO(gzip.decompress(roh)), keep_default_na=True).fillna({"tarif": ""})


def verschluessele_tabelle(df, key):
    from cryptography.fernet import Fernet

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    DATEI.write_bytes(Fernet(key.encode()).encrypt(gzip.compress(csv_bytes)))


def finde_zeilen(tabelle, sparte, gesellschaft, tarif=None):
    """Alle passenden Zeilen. Vergleich ohne Groß-/Kleinschreibung; tarif=None ignoriert den Tarif."""
    t = tabelle[
        (tabelle["sparte"].str.lower() == sparte.strip().lower())
        & (tabelle["gesellschaft"].str.lower() == gesellschaft.strip().lower())
    ]
    if tarif is not None:
        t = t[t["tarif"].str.lower() == tarif.strip().lower()]
    return t


# --- Zuordnung der Produkte aus den Tabellen zu den Sparten der Courtageliste ---
# Wert: (Sparte, bevorzugte Tarif-Stichwörter). Produkte ohne Eintrag (z.B. "Sach", "KV", "Immo")
# werden nicht aus der Liste gerechnet, sondern mit dem bisherigen Standardsatz.
PRODUKT_ZU_SPARTE = {
    "pav": ("Rente", ()),
    "rürup": ("Rente", ("basisrente", "rürup")),
    "ruerup": ("Rente", ("basisrente", "rürup")),
    "bu": ("BU", ()),
    "bav": ("bAV", ()),
    "pkv": ("PKV", ()),
    "rl": ("Risikoleben", ()),
    "risikoleben": ("Risikoleben", ()),
    "rs": ("RS", ()),
    "kfz": ("PKW", ()),
    "zz": ("KV-Zusatz", ("zahn",)),
}
# Bei diesen (Sparte, Gesellschaft) wird bei mehreren Tarifen bewusst immer der niedrigste Satz genommen,
# ohne Hinweis (Vorgabe Adele 2026-10-05: Hannoversche BU immer der niedrige Tarif).
NIEDRIGSTER_TARIF = {("BU", "Hannoversche")}
KV_SPARTEN = {"PKV", "KV-Zusatz", "GKV", "bKV"}

_STOPWOERTER = {
    "die", "der", "das", "versicherung", "versicherungen", "versicherungs", "vers", "verssdienst",
    "ag", "gmbh", "se", "ag", "konzern", "gruppe", "lebensversicherung", "holding", "und",
}


def sparte_fuer(produkt_name):
    """Gibt (Sparte, Tarif-Stichwörter) zurück oder (None, ()) bei unbekanntem Produkt."""
    schluessel = re.sub(r"^\d+x\s*", "", produkt_name.strip().lower()).split("+")[0].strip()
    return PRODUKT_ZU_SPARTE.get(schluessel, (None, ()))


def _norm(name):
    s = unicodedata.normalize("NFKD", str(name).lower())
    s = "".join(c for c in s if not unicodedata.combining(c)).replace("ß", "ss")
    s = re.sub(r"ae|oe|ue", lambda m: m.group(0)[0], s)
    tokens = [t for t in re.split(r"[^a-z0-9]+", s) if t and t not in _STOPWOERTER]
    return "".join(tokens)


def finde_gesellschaft(tabelle, sparte, gesellschaft):
    """Ordnet die eingetragene Gesellschaft ("Bayerische") dem Listennamen ("die Bayerische") zu.
    Gibt (name, fehler) zurück: genau eines von beiden ist gesetzt."""
    namen = sorted(tabelle.loc[tabelle["sparte"] == sparte, "gesellschaft"].unique())
    gesucht = _norm(gesellschaft)
    if len(gesucht) < 3:
        return None, f"Gesellschaft „{gesellschaft}“ ist zu kurz zum Zuordnen"
    for regel in (
        lambda n: n == gesucht,
        lambda n: n.startswith(gesucht) or (len(n) >= 4 and gesucht.startswith(n)),
        lambda n: len(gesucht) >= 5 and gesucht in n,
    ):
        treffer = [name for name in namen if regel(_norm(name))]
        if len(treffer) == 1:
            return treffer[0], None
        if len(treffer) > 1:
            return None, f"Gesellschaft „{gesellschaft}“ ist mehrdeutig ({', '.join(treffer[:3])} …) – bitte genauer eintragen"
    return None, f"Gesellschaft „{gesellschaft}“ steht in der Courtageliste nicht bei {sparte}"


def satz_fuer(tabelle, sparte, gesellschaft, bevorzugt=()):
    """Sucht die Zeile der Courtageliste (Stufe-5-Werte). Rückgabe: dict mit eur_je_wp, prozent,
    bz_dauer_jahre, gesellschaft, tarif -- oder {"fehler": "..."}."""
    name, fehler = finde_gesellschaft(tabelle, sparte, gesellschaft)
    if fehler:
        return {"fehler": fehler}
    zeilen = tabelle[(tabelle["sparte"] == sparte) & (tabelle["gesellschaft"] == name)]
    zeilen = zeilen[zeilen[["eur_je_wp", "verguetung_prozent", "bp_prozent"]].notna().any(axis=1)]
    if zeilen.empty:
        return {"fehler": f"Für {name} ist bei {sparte} kein Satz in der Courtageliste hinterlegt"}
    tarif = zeilen["tarif"].str.lower()
    wahl = None
    ohne = zeilen.iloc[0:0]
    if bevorzugt:
        passend = zeilen[tarif.apply(lambda t: any(b in t for b in bevorzugt))]
        if len(passend):
            zeilen, tarif = passend, passend["tarif"].str.lower()
    if len(zeilen) == 1:
        wahl = zeilen.iloc[0]
    elif (tarif == "").sum() == 1:
        wahl = zeilen[tarif == ""].iloc[0]
    else:
        ohne = zeilen[~tarif.str.contains("einmal|zuzahlung|bestandsprov|gruppen|nav bp|pflege", regex=True)]
        if len(ohne) == 1:
            wahl = ohne.iloc[0]
        else:
            lfd = ohne[ohne["tarif"].str.lower().str.contains("lfd|laufend|fondsgeb", regex=True)]
            if len(lfd) == 1:
                wahl = lfd.iloc[0]
    hinweis = None
    if wahl is None:
        kandidaten = ohne if len(ohne) else zeilen
        satz = kandidaten["eur_je_wp"].fillna(kandidaten["verguetung_prozent"]).fillna(kandidaten["bp_prozent"])
        wahl = kandidaten.loc[satz.idxmin()]
        hinweis = None if (sparte, name) in NIEDRIGSTER_TARIF else f"Tarif nicht eindeutig – niedrigster Satz verwendet ({wahl['tarif'] or 'Standard'}); Tarif bitte klären"
    prozent = wahl["verguetung_prozent"] if pd.notna(wahl["verguetung_prozent"]) else wahl["bp_prozent"]
    return {
        "eur_je_wp": None if pd.isna(wahl["eur_je_wp"]) else float(wahl["eur_je_wp"]),
        "prozent": None if pd.isna(prozent) else float(prozent),
        "bz_dauer_jahre": None if pd.isna(wahl["bz_dauer_jahre"]) else int(wahl["bz_dauer_jahre"]),
        "gesellschaft": name,
        "tarif": wahl["tarif"],
        "hinweis": hinweis,
    }
