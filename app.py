import base64
from pathlib import Path

import pandas as pd
import streamlit as st

import courtage
import formeln

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

# Fachliche Konstanten/Formeln liegen in formeln.py (gemeinsam mit mein_umsatz.py genutzt).
ADELE_QUOTE = 0.80  # Adeles Stufe 5

# Team: Name -> eigene Quote (für Differenz-Berechnung). Nur diese Personen zählen.
TEAM_QUOTEN = {
    "adel": ADELE_QUOTE,       # Eigengeschäft
    "emirhan": 0.80,           # gleiche Stufe wie Adele -> 0 Differenz
    "seher": 0.55,             # Stufe 3
    "büsra": 0.37,             # Stufe 2
    "busra": 0.37,             # ohne Umlaut, falls so geschrieben
    "birtan": 0.55,
    "ikram": 0.20,
    "mahdi": 0.55,
}

# Sonderfälle, bei denen Adeles Anteil NICHT der normalen Differenz-Formel
# (ADELE_QUOTE - eigene_quote) folgt, sondern direkt festgelegt ist.
ADELE_ANTEIL_OVERRIDE = {
    "mahdi": 0.125,   # geteiltes Overhead mit einer weiteren Person -> nur halbe Differenz (12,5% statt 25%)
    "büsra": 0.215,   # geteiltes Overhead -> nur halbe Differenz (80%-37%=43% -> 21,5% statt 43%)
    "busra": 0.215,   # ohne Umlaut, falls so geschrieben
    "seher": 0.125,   # Stufe 3 (80%-55%=25%), geteiltes Overhead -> halbe Differenz (12,5%)
}

def berechne_zeile(name_kunde, vertriebspartner, produkt, beitrag_text, laufzeit_text, stand_text, monat="", gesellschaft="", courtage_tabelle=None):
    partner_key = vertriebspartner.strip().lower().replace("ş", "s")

    if partner_key not in TEAM_QUOTEN:
        return [{
            "Name Kunde": name_kunde, "Vertriebspartner": vertriebspartner, "Produkt": produkt,
            "Monat": monat, "Beitrag (€)": None, "Status": "nicht im Team", "WP": None, "Auszahlung (€)": None,
            "Quelle": "", "Hinweis": "Zählt nicht (kein Teammitglied)",
        }]

    if partner_key in ADELE_ANTEIL_OVERRIDE:
        quote = ADELE_ANTEIL_OVERRIDE[partner_key]
    elif partner_key == "adel":
        quote = ADELE_QUOTE
    else:
        quote = ADELE_QUOTE - TEAM_QUOTEN[partner_key]

    zeilen = formeln.berechne_positionen(
        name_kunde, quote, produkt, beitrag_text, laufzeit_text, stand_text, monat,
        gesellschaft=gesellschaft, courtage_tabelle=courtage_tabelle,
    )
    for zeile in zeilen:
        zeile["Vertriebspartner"] = vertriebspartner
    return zeilen


COURTAGE_KEY = st.secrets.get("COURTAGE_KEY", "")


@st.cache_resource
def lade_courtage(key):
    return courtage.lade_tabelle(key)


COURTAGE = None
if COURTAGE_KEY:
    try:
        COURTAGE = lade_courtage(COURTAGE_KEY)
    except Exception as e:
        st.warning(f"Courtageliste konnte nicht geladen werden, es gilt der Standardsatz: {e}")

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
            <div style="color:white; font-size:30px; font-weight:700; line-height:1.2;">Umsatz Rechner</div>
            <div style="color:#F3E4D3; font-size:14px; margin-top:4px;">
                Liest deine Geschäfts-Übersicht ein und berechnet Wohlstandspunkte (WP) + Auszahlung automatisch.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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
    schluessel = [c for c in ("Name Kunde", "Vertriebspartner", "Produkt") if c in df.columns]
    if schluessel:
        df = df.dropna(subset=schluessel, how="all")

    alle_zeilen = []
    for _, row in df.iterrows():
        zeilen = berechne_zeile(
            str(row.get("Name Kunde", "")),
            str(row.get("Vertriebspartner", "")),
            str(row.get("Produkt", row.get("Produkt ", ""))),
            row.get("Beitrag"),
            row.get("Laufzeit"),
            row.get("Stand"),
            str(row.get("Monat", "")).strip(),
            gesellschaft="" if pd.isna(row.get("Gesellschaften", row.get("Gesellschaft", ""))) else str(row.get("Gesellschaften", row.get("Gesellschaft", ""))),
            courtage_tabelle=COURTAGE,
        )
        ausgezahlt = str(row.get("Ausgezahlt", "")).strip().lower() in ("true", "wahr", "ja", "x", "1")
        for zeile in zeilen:
            zeile["Ausgezahlt"] = ausgezahlt
        alle_zeilen.extend(zeilen)

    ergebnis_df = pd.DataFrame(alle_zeilen)
    ergebnis_df = ergebnis_df.sort_values(["Vertriebspartner", "Name Kunde"]).reset_index(drop=True)

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
        "nicht im Team": "🚫 Kein Teammitglied",
    }
    ergebnis_df["Status"] = ergebnis_df["Status"].map(STATUS_LABEL).fillna(ergebnis_df["Status"])

    spalten_reihenfolge = ["Name Kunde", "Vertriebspartner", "Monat", "Produkt", "Beitrag (€)", "WP", "Auszahlung (€)", "Quelle", "Status", "Hinweis"]
    ergebnis_df = ergebnis_df[spalten_reihenfolge]

    st.metric("💰 Gesamt-Vergütung (offen + eingereicht + policiert)", f"{gesamt:,.2f} €")

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Sichere Auszahlung (policiert)", f"{sicher:,.2f} €")
    col2.metric("🟡 Ausstehende Vergütung (eingereicht)", f"{ausstehend:,.2f} €")
    col3.metric("🔵 Vergütung offenes Geschäft", f"{offen_summe:,.2f} €")

    col4, col5 = st.columns(2)
    col4.metric("Gesamt-WP", f"{gesamt_wp:,.2f}")
    col5.metric("Zeilen mit offenen Fragen", int((ergebnis_df["Hinweis"] != "").sum()))

    st.divider()
    st.subheader("💸 Auszahlungs-Checkliste")
    st.caption(
        "Abgeschlossenes (policiertes) Geschäft. Abgehakt wird direkt in deiner Google-Tabelle in der Spalte "
        "„Ausgezahlt“, die App liest es alle 60 Sekunden neu. Folgt dem Monatsfilter oben."
    )
    pol = berechnet[berechnet["Status"] == "policiert"].copy()
    pol["Ausgezahlt"] = pol["Ausgezahlt"].fillna(False).astype(bool)
    pol["Vertriebspartner"] = pol["Vertriebspartner"].str.strip()
    noch_offen = pol[~pol["Ausgezahlt"]]["Auszahlung (€)"].sum()
    schon_bezahlt = pol[pol["Ausgezahlt"]]["Auszahlung (€)"].sum()
    pipeline = ausstehend + offen_summe

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("⏳ Policiert, noch nicht ausgezahlt", f"{noch_offen:,.2f} €")
    k2.metric("💶 Bereits ausgezahlt", f"{schon_bezahlt:,.2f} €")
    k3.metric("🟡 Noch in der Pipeline (eingereicht + offen)", f"{pipeline:,.2f} €")
    k4.metric("📥 Insgesamt noch zu erwarten", f"{noch_offen + pipeline:,.2f} €")

    ansicht = st.radio("Anzeigen", ["Noch nicht ausgezahlt", "Bereits ausgezahlt", "Alle"], horizontal=True)
    if ansicht == "Noch nicht ausgezahlt":
        pol = pol[~pol["Ausgezahlt"]]
    elif ansicht == "Bereits ausgezahlt":
        pol = pol[pol["Ausgezahlt"]]
    pol = pol.sort_values(["Ausgezahlt", "Vertriebspartner", "Monat", "Name Kunde"])
    st.dataframe(
        pol[["Ausgezahlt", "Name Kunde", "Vertriebspartner", "Monat", "Produkt", "Auszahlung (€)", "Quelle"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ausgezahlt": st.column_config.CheckboxColumn("Ausgezahlt"),
            "Auszahlung (€)": st.column_config.NumberColumn("Auszahlung (€)", format="%.2f €"),
        },
    )
    if not pol.empty:
        je_partner = (
            pol.groupby("Vertriebspartner", as_index=False)
            .agg(**{"Verträge": ("Name Kunde", "count"), "Summe (€)": ("Auszahlung (€)", "sum")})
            .sort_values("Summe (€)", ascending=False)
        )
        st.caption(f"Summe pro Vertriebspartner ({ansicht.lower()})")
        st.dataframe(
            je_partner, use_container_width=True, hide_index=True,
            column_config={"Summe (€)": st.column_config.NumberColumn("Summe (€)", format="%.2f €")},
        )

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

    st.divider()
    st.subheader("📅 Monatsübersicht pro Kunde")
    st.caption("Nur policiertes (sicheres) Geschäft. Zum Monatsende in deine Bestandskunden-Tabelle übertragen.")

    monatsuebersicht = (
        berechnet[berechnet["Status"] == "policiert"]
        .groupby("Name Kunde", as_index=False)
        .agg(**{"Umsatz (€)": ("Beitrag (€)", "sum"), "WP": ("WP", "sum")})
        .sort_values("Name Kunde")
        .reset_index(drop=True)
    )

    st.dataframe(
        monatsuebersicht,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Umsatz (€)": st.column_config.NumberColumn("Umsatz (€)", format="%.2f €"),
            "WP": st.column_config.NumberColumn("WP", format="%.2f"),
        },
    )

    monat_name = pd.Timestamp.today().strftime("%Y-%m")
    st.download_button(
        "⬇️ Monatsübersicht als CSV herunterladen",
        monatsuebersicht.to_csv(index=False).encode("utf-8"),
        file_name=f"monatsuebersicht_{monat_name}.csv",
        mime="text/csv",
    )

    st.divider()
    st.subheader("📊 Stand nach Status (WP und Vergütung)")
    st.caption("Alles zusammen und aufgeteilt in policiert, eingereicht und offen. Folgt dem Monatsfilter oben.")

    def status_summe(maske):
        teil = berechnet[maske]
        return {"Verträge": len(teil), "WP": teil["WP"].sum(), "Vergütung (€)": teil["Auszahlung (€)"].sum()}

    st_ = berechnet["Status"]
    status_tabelle = pd.DataFrame(
        [
            {"Stand": "✅ Policiert", **status_summe(st_ == "policiert")},
            {"Stand": "🟡 Eingereicht", **status_summe(st_ == "eingereicht")},
            {"Stand": "➕ Policiert + eingereicht (ohne Offene)", **status_summe(st_.isin(["policiert", "eingereicht"]))},
            {"Stand": "🔵 Offen", **status_summe(st_ == "offen")},
            {"Stand": "🧮 Alles zusammen", **status_summe(st_.notna())},
        ]
    )
    st.dataframe(
        status_tabelle,
        use_container_width=True,
        hide_index=True,
        column_config={
            "WP": st.column_config.NumberColumn("WP", format="%.2f"),
            "Vergütung (€)": st.column_config.NumberColumn("Vergütung (€)", format="%.2f €"),
        },
    )

    je_partner_status = (
        berechnet.assign(Vertriebspartner=berechnet["Vertriebspartner"].str.strip())
        .pivot_table(index="Vertriebspartner", columns="Status", values=["WP", "Auszahlung (€)"], aggfunc="sum", fill_value=0)
    )
    zeilen_pp = []
    for partner, r in je_partner_status.iterrows():
        z = {"Vertriebspartner": partner}
        for status, label in (("policiert", "policiert"), ("eingereicht", "eingereicht"), ("offen", "offen")):
            z[f"WP {label}"] = r.get(("WP", status), 0)
        for status, label in (("policiert", "policiert"), ("eingereicht", "eingereicht"), ("offen", "offen")):
            z[f"€ {label}"] = r.get(("Auszahlung (€)", status), 0)
        zeilen_pp.append(z)
    if zeilen_pp:
        st.caption("Aufgeteilt nach Vertriebspartner")
        pp_config = {c: st.column_config.NumberColumn(c, format="%.2f") for c in zeilen_pp[0] if c.startswith("WP")}
        pp_config.update({c: st.column_config.NumberColumn(c, format="%.2f €") for c in zeilen_pp[0] if c.startswith("€")})
        st.dataframe(pd.DataFrame(zeilen_pp), use_container_width=True, hide_index=True, column_config=pp_config)
else:
    st.info("Lade deine CSV-Datei hoch oder richte die Google-Tabellen-Anbindung ein, um loszulegen.")
