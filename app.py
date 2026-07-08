import io
import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="K&W Umsatz Rechner", page_icon="logo.png", layout="wide")


def check_password():
    """Zeigt ein Passwort-Feld, solange kein korrektes Passwort eingegeben wurde."""

    def password_entered():
        if st.session_state["password"] == st.secrets.get("APP_PASSWORD", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Passwort", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Falsches Passwort")
    return False


if not check_password():
    st.stop()

# --- Fachliche Konstanten (K&W Wohlstandspunkte-System) ---
# Quelle: Canva-Kickoff-Präsentation "K&W - Kick Off 27.06.2026" + Angaben von Adele.

VOLLWERT_PRO_WP = 43.0  # 4,3% * 1000, entspricht 100% Quote
GESAMTUMSATZ_ABZUG = 0.75  # 25% werden immer abgezogen, 75% bleiben übrig
ADELE_QUOTE = 0.80  # Adeles Stufe 5

# Team: Name -> eigene Quote (für Differenz-Berechnung). Nur diese Personen zählen.
TEAM_QUOTEN = {
    "adel": ADELE_QUOTE,       # Eigengeschäft
    "emirhan": 0.80,           # gleiche Stufe wie Adele -> 0 Differenz
    "seher": 0.675,
    "büsra": 0.675,
    "busra": 0.675,            # ohne Umlaut, falls so geschrieben
    "birtan": 0.55,
    "ikram": 0.20,
}

LEBEN_PRODUKTE = {"bu", "pav", "bav", "rürup", "ruerup", "kidspolice"}
SACH_PRODUKTE = {"sach", "gewerbe sach", "wohngebäude", "wohngebaeude"}
KRANKEN_PRODUKTE = {"pkv"}
AUSGESCHLOSSEN_PRODUKTE = {"depot"}  # wird aktuell nicht verkauft/berechnet


def parse_beitrag(text):
    """"50€" -> 50.0. Gibt None zurück, wenn kein Betrag erkennbar ist."""
    if not isinstance(text, str) or not text.strip():
        return None
    match = re.search(r"[\d.,]+", text.replace(".", "").replace(",", "."))
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def parse_laufzeit_jahre(text):
    """Versucht eine Jahreszahl aus der Laufzeit-Spalte zu lesen.
    Gibt (jahre, ist_unklar) zurück. jahre ist None, wenn nicht eindeutig."""
    if not isinstance(text, str) or not text.strip():
        return None, True
    t = text.strip().lower()
    if "voll" in t:
        return None, True  # "volle Laufzeit" -> muss manuell nachgetragen werden
    match = re.search(r"\d+", t)
    if match:
        return int(match.group()), False
    return None, True


def split_produkt_beitrag(produkt, beitrag_text):
    """Zerlegt Kombi-Zeilen wie 'PAV + Depot' / '50€ + 50€' in einzelne Positionen."""
    produkte = [p.strip() for p in str(produkt).split("+")]
    betraege = [b.strip() for b in str(beitrag_text).split("+")] if isinstance(beitrag_text, str) else [beitrag_text]
    if len(betraege) == len(produkte):
        return list(zip(produkte, betraege))
    if len(produkte) > 1 and len({produkt_kategorie(p) for p in produkte}) == 1:
        # Nur ein Betrag für mehrere Positionen derselben Kategorie (z.B. "Wohngebäude + Sach", "115€")
        # -> als eine Position zusammenfassen, sonst würde der Betrag doppelt gezählt.
        return [(" + ".join(produkte), beitrag_text)]
    # Nicht sauber trennbar und unterschiedliche Kategorien -> pro Position offen lassen,
    # statt den Betrag zu erraten.
    return [(p, None) for p in produkte]


def produkt_multiplikator_und_name(produkt_name):
    """"2x Kidspolice" -> (2, "kidspolice"). Ohne Präfix -> (1, name)."""
    p = produkt_name.strip().lower()
    match = re.match(r"^(\d+)x\s*(.+)$", p)
    if match:
        return int(match.group(1)), match.group(2)
    return 1, p


def produkt_kategorie(produkt_name):
    # Bei zusammengeführten Positionen (z.B. "Wohngebäude + Sach") reicht der erste Teil,
    # da split_produkt_beitrag nur gleiche Kategorien zusammenführt.
    erster_teil = produkt_name.split("+")[0].strip()
    _, p = produkt_multiplikator_und_name(erster_teil)
    if p in AUSGESCHLOSSEN_PRODUKTE:
        return "ausgeschlossen"
    if p in LEBEN_PRODUKTE:
        return "leben"
    if p in SACH_PRODUKTE:
        return "sach"
    if p in KRANKEN_PRODUKTE:
        return "kranken"
    return "unbekannt"


STAND_POSITIV_KEYWORDS = ["eingereicht", "unterschrieben", "policiert", "abgeschickt"]
STAND_UNKLAR_KEYWORDS = ["?", "termin", "angebot"]


def stand_status(text):
    if not isinstance(text, str) or not text.strip():
        return "unklar"
    t = text.lower()
    if any(k in t for k in STAND_UNKLAR_KEYWORDS):
        return "unklar"
    if any(k in t for k in STAND_POSITIV_KEYWORDS):
        return "zaehlt"
    return "unklar"


def berechne_zeile(name_kunde, vertriebspartner, produkt, beitrag_text, laufzeit_text, stand_text):
    partner_key = vertriebspartner.strip().lower()
    ergebnisse = []

    if partner_key not in TEAM_QUOTEN:
        return [{
            "Name Kunde": name_kunde, "Vertriebspartner": vertriebspartner, "Produkt": produkt,
            "Status": "nicht im Team", "WP": None, "Auszahlung (€)": None,
            "Hinweis": "Zählt nicht (kein Teammitglied)",
        }]

    stand = stand_status(stand_text)
    for teilprodukt, teilbeitrag_text in split_produkt_beitrag(produkt, beitrag_text):
        kategorie = produkt_kategorie(teilprodukt)
        beitrag = parse_beitrag(teilbeitrag_text)

        zeile = {
            "Name Kunde": name_kunde,
            "Vertriebspartner": vertriebspartner,
            "Produkt": teilprodukt,
            "Status": stand,
            "WP": None,
            "Auszahlung (€)": None,
            "Hinweis": "",
        }

        if kategorie == "ausgeschlossen":
            zeile["Hinweis"] = "Depot – wird aktuell nicht berechnet"
            ergebnisse.append(zeile)
            continue
        if kategorie == "unbekannt":
            zeile["Hinweis"] = "Unbekanntes Produkt – bitte Formel klären"
            ergebnisse.append(zeile)
            continue
        if stand != "zaehlt":
            zeile["Hinweis"] = "Status noch nicht vergütungsfähig"
            ergebnisse.append(zeile)
            continue
        if beitrag is None:
            zeile["Hinweis"] = "Kein Beitrag erkannt"
            ergebnisse.append(zeile)
            continue

        multiplikator, _ = produkt_multiplikator_und_name(teilprodukt)

        if kategorie == "leben":
            jahre, unklar = parse_laufzeit_jahre(laufzeit_text)
            if unklar:
                zeile["Hinweis"] = "Laufzeit fehlt/unklar – bitte manuell nachtragen"
                ergebnisse.append(zeile)
                continue
            bws = beitrag * 12 * jahre
            wp = (bws / 1000) * multiplikator
        else:  # sach oder kranken
            wp = (beitrag / 6) * multiplikator

        eigene_quote = TEAM_QUOTEN[partner_key]
        differenz_quote = ADELE_QUOTE - eigene_quote if partner_key != "adel" else ADELE_QUOTE
        auszahlung = wp * VOLLWERT_PRO_WP * differenz_quote * GESAMTUMSATZ_ABZUG

        zeile["WP"] = round(wp, 2)
        zeile["Auszahlung (€)"] = round(auszahlung, 2)
        ergebnisse.append(zeile)

    return ergebnisse


col_logo, col_title = st.columns([1, 5], vertical_alignment="center")
with col_logo:
    st.image("logo.png")
with col_title:
    st.title("Umsatz Rechner")
    st.caption("Liest deine Geschäfts-Übersicht ein und berechnet Wohlstandspunkte (WP) + Auszahlung automatisch.")

st.divider()

SHEET_CSV_URL = st.secrets.get("SHEET_CSV_URL", "")


@st.cache_data(ttl=60)
def lade_google_sheet(url):
    return pd.read_csv(url)


df = None

if SHEET_CSV_URL:
    if st.button("🔄 Aktualisieren"):
        lade_google_sheet.clear()
    try:
        df = lade_google_sheet(SHEET_CSV_URL)
        st.success("Daten aus der Google-Tabelle geladen (aktualisiert sich automatisch alle 60 Sekunden).")
    except Exception as e:
        st.error(f"Konnte die Google-Tabelle nicht laden: {e}")

with st.expander("Stattdessen CSV-Datei manuell hochladen"):
    uploaded = st.file_uploader("CSV-Datei hochladen", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)

if df is not None:
    df.columns = [c.strip() for c in df.columns]

    alle_zeilen = []
    for _, row in df.iterrows():
        alle_zeilen.extend(berechne_zeile(
            str(row.get("Name Kunde", "")),
            str(row.get("Vertriebspartner", "")),
            str(row.get("Produkt", row.get("Produkt ", ""))),
            row.get("Beitrag"),
            row.get("Laufzeit"),
            row.get("Stand"),
        ))

    ergebnis_df = pd.DataFrame(alle_zeilen)

    STATUS_LABEL = {
        "zaehlt": "✅ Zählt",
        "unklar": "⚠️ Unklar",
        "nicht im Team": "🚫 Kein Teammitglied",
    }
    ergebnis_df["Status"] = ergebnis_df["Status"].map(STATUS_LABEL).fillna(ergebnis_df["Status"])
    ergebnis_df = ergebnis_df.sort_values(["Vertriebspartner", "Name Kunde"]).reset_index(drop=True)

    spalten_reihenfolge = ["Name Kunde", "Vertriebspartner", "Produkt", "WP", "Auszahlung (€)", "Status", "Hinweis"]
    ergebnis_df = ergebnis_df[spalten_reihenfolge]

    berechnet = ergebnis_df[ergebnis_df["Auszahlung (€)"].notna()]
    gesamt = berechnet["Auszahlung (€)"].sum()
    gesamt_wp = berechnet["WP"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamt-WP", f"{gesamt_wp:,.2f}")
    col2.metric("Gesamt-Auszahlung", f"{gesamt:,.2f} €")
    col3.metric("Zeilen mit offenen Fragen", int((ergebnis_df["Hinweis"] != "").sum()))

    spalten_config = {
        "WP": st.column_config.NumberColumn("WP", format="%.2f"),
        "Auszahlung (€)": st.column_config.NumberColumn("Auszahlung (€)", format="%.2f €"),
    }

    st.subheader("Ergebnis pro Zeile")
    st.dataframe(ergebnis_df, use_container_width=True, hide_index=True, column_config=spalten_config)

    offene = ergebnis_df[ergebnis_df["Hinweis"] != ""]
    if not offene.empty:
        st.subheader("⚠️ Zeilen, die ich nicht automatisch berechnen konnte")
        st.dataframe(offene, use_container_width=True, hide_index=True, column_config=spalten_config)
else:
    st.info("Lade deine CSV-Datei hoch oder richte die Google-Tabellen-Anbindung ein, um loszulegen.")
