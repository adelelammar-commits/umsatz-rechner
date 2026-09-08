import base64
from pathlib import Path

import pandas as pd
import streamlit as st

import formeln

st.set_page_config(page_title="Mein Umsatz", page_icon="logo.png", layout="wide")


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

# Diese App zeigt IMMER nur die eigene, volle Vergütung einer einzelnen Person auf ihrer
# eigenen Karrierestufe -- kein Team-/Differenz-Modell wie in Adeles app.py. Name, Quote,
# Google-Tabelle und Passwort kommen pro Person aus den Streamlit-Secrets dieser Deployment-
# Instanz, damit jede Person eine eigene, komplett getrennte App-Instanz bekommt und
# niemand die Zahlen einer anderen Person sehen kann.
MITARBEITER_NAME = st.secrets.get("MITARBEITER_NAME", "Mein")
MITARBEITER_QUOTE = float(st.secrets.get("MITARBEITER_QUOTE", 0))

LOGO_BASE64 = base64.b64encode(Path("logo.png").read_bytes()).decode()

st.markdown(
    f"""
    <style>
    div[data-testid="stMetric"] {{
        background-color: #F7F1EA;
        border: 1px solid #E7D7C2;
        border-radius: 14px;
        padding: 16px 20px;
    }}
    div[data-testid="stMetricLabel"] {{
        color: #8A5E33;
    }}
    </style>
    <div style="
        background: linear-gradient(135deg, #B17946, #543719);
        padding: 24px 32px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        gap: 22px;
        margin-bottom: 28px;
    ">
        <img src="data:image/png;base64,{LOGO_BASE64}" style="width:64px; height:64px; border-radius:12px;">
        <div>
            <div style="color:white; font-size:30px; font-weight:700; line-height:1.2;">{MITARBEITER_NAME}s Umsatz</div>
            <div style="color:#F3E4D3; font-size:14px; margin-top:4px;">
                Deine eigene Geschäfts-Übersicht: Wohlstandspunkte (WP) + deine eigene Vergütung, automatisch berechnet.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if MITARBEITER_QUOTE <= 0:
    st.error("Es ist noch keine eigene Quote (MITARBEITER_QUOTE) in den Secrets hinterlegt.")
    st.stop()

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
        st.success("Daten aus deiner Google-Tabelle geladen (aktualisiert sich automatisch alle 60 Sekunden).")
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
        alle_zeilen.extend(formeln.berechne_positionen(
            str(row.get("Name Kunde", "")),
            MITARBEITER_QUOTE,
            str(row.get("Produkt", row.get("Produkt ", ""))),
            row.get("Beitrag"),
            row.get("Laufzeit"),
            row.get("Stand"),
            str(row.get("Monat", "")).strip(),
        ))

    ergebnis_df = pd.DataFrame(alle_zeilen)
    ergebnis_df = ergebnis_df.sort_values(["Name Kunde"]).reset_index(drop=True)

    monate_vorhanden = sorted(m for m in ergebnis_df["Monat"].unique() if m)
    monat_auswahl = st.selectbox("📅 Monat", ["Alle Monate"] + monate_vorhanden)
    if monat_auswahl != "Alle Monate":
        ergebnis_df = ergebnis_df[ergebnis_df["Monat"] == monat_auswahl].reset_index(drop=True)

    berechnet = ergebnis_df[ergebnis_df["Auszahlung (€)"].notna()].copy()

    sicher = berechnet[berechnet["Status"] == "policiert"]["Auszahlung (€)"].sum()
    ausstehend = berechnet[berechnet["Status"] == "eingereicht"]["Auszahlung (€)"].sum()
    offen_summe = berechnet[berechnet["Status"] == "offen"]["Auszahlung (€)"].sum()
    gesamt = berechnet["Auszahlung (€)"].sum()
    gesamt_wp = berechnet["WP"].sum()

    STATUS_LABEL = {
        "offen": "🔵 Offen",
        "eingereicht": "🟡 Eingereicht",
        "policiert": "✅ Policiert",
        "unklar": "⚠️ Unklar",
    }
    ergebnis_df["Status"] = ergebnis_df["Status"].map(STATUS_LABEL).fillna(ergebnis_df["Status"])

    spalten_reihenfolge = ["Name Kunde", "Monat", "Produkt", "Beitrag (€)", "WP", "Auszahlung (€)", "Status", "Hinweis"]
    ergebnis_df = ergebnis_df[spalten_reihenfolge]

    st.metric("💰 Gesamt-Vergütung (offen + eingereicht + policiert)", f"{gesamt:,.2f} €")

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Sichere Auszahlung (policiert)", f"{sicher:,.2f} €")
    col2.metric("🟡 Ausstehende Vergütung (eingereicht)", f"{ausstehend:,.2f} €")
    col3.metric("🔵 Vergütung offenes Geschäft", f"{offen_summe:,.2f} €")

    st.metric("Gesamt-WP", f"{gesamt_wp:,.2f}")

    spalten_config = {
        "Beitrag (€)": st.column_config.NumberColumn("Beitrag (€)", format="%.2f €"),
        "WP": st.column_config.NumberColumn("WP", format="%.2f"),
        "Auszahlung (€)": st.column_config.NumberColumn("Auszahlung aufs Konto (€)", format="%.2f €"),
    }

    st.subheader("Ergebnis pro Zeile")
    st.dataframe(ergebnis_df, use_container_width=True, hide_index=True, column_config=spalten_config)

    offene = ergebnis_df[ergebnis_df["Hinweis"] != ""]
    if not offene.empty:
        st.subheader("⚠️ Zeilen, die ich nicht automatisch berechnen konnte")
        st.dataframe(offene, use_container_width=True, hide_index=True, column_config=spalten_config)
else:
    st.info("Lade deine CSV-Datei hoch oder richte die Google-Tabellen-Anbindung ein, um loszulegen.")
