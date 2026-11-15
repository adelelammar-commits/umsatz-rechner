import base64
import html
from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import courtage
import formeln

st.set_page_config(
    page_title="K&W Umsatz Rechner", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed"
)

LOGO_BASE64 = base64.b64encode(Path("logo.png").read_bytes()).decode()
APP_TITEL = st.secrets.get("APP_TITEL", "Umsatz Rechner")

# ---------------------------------------------------------------------------
# Design: Farben, Schrift, Karten
# ---------------------------------------------------------------------------
BRAUN = "#B17946"
DUNKEL = "#543719"
STATUS_NAME = {"policiert": "Policiert", "eingereicht": "Eingereicht", "offen": "Offen", "unklar": "Unklar"}
STATUS_FARBE = {"Policiert": "#2E7D5B", "Eingereicht": "#D9A23A", "Offen": "#4A7FB5", "Unklar": "#9AA0A6"}
STATUS_RANG = {"Policiert": 0, "Eingereicht": 1, "Offen": 2, "Unklar": 3}
STATUS_LABEL = {
    "offen": "🔵 Offen",
    "eingereicht": "🟡 Eingereicht",
    "policiert": "✅ Policiert",
    "unklar": "⚠️ Unklar",
    "nicht im Team": "🚫 Kein Teammitglied",
}
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, .stMarkdown, p, label, input, textarea, button, h1, h2, h3, h4 { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }

.hero { background: linear-gradient(120deg, #B17946 0%, #7A5230 55%, #3F2912 100%); border-radius: 22px;
        padding: 26px 32px; display: flex; align-items: center; justify-content: space-between; gap: 20px;
        flex-wrap: wrap; margin-bottom: 18px; box-shadow: 0 12px 32px rgba(84,55,25,.18); }
.hero-links { display: flex; align-items: center; gap: 20px; }
.hero img { width: 62px; height: 62px; border-radius: 14px; box-shadow: 0 4px 14px rgba(0,0,0,.2); }
.hero .titel { color: #fff; font-size: 28px; font-weight: 800; letter-spacing: -.02em; line-height: 1.15; }
.hero .untertitel { color: #F3E4D3; font-size: 14px; margin-top: 4px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.28); color: #fff; border-radius: 999px;
        padding: 6px 13px; font-size: 12.5px; font-weight: 500; white-space: nowrap; }
.chip .punkt { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #6EE7A8; margin-right: 6px; }

.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 4px 0 14px; }
.kpi { --akzent: #B17946; background: #fff; border: 1px solid #EFE6DC; border-radius: 16px; padding: 16px 18px 15px 20px;
       box-shadow: 0 1px 2px rgba(84,55,25,.04), 0 8px 22px rgba(84,55,25,.06); position: relative; overflow: hidden; }
.kpi::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--akzent); }
.kpi .label { font-size: 11.5px; color: #8A6B4E; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
.kpi .wert { font-size: 25px; font-weight: 800; color: #2B1B0C; margin-top: 6px; letter-spacing: -.02em;
             font-variant-numeric: tabular-nums; }
.kpi .sub { font-size: 12.5px; color: #8C8278; margin-top: 3px; }
.kpi .bar { height: 6px; border-radius: 99px; background: #F3ECE4; margin-top: 10px; overflow: hidden; }
.kpi .bar > div { height: 100%; border-radius: 99px; background: var(--akzent); }
.kpi.haupt { background: linear-gradient(135deg, #543719, #85592F); border: none; }
.kpi.haupt::before { display: none; }
.kpi.haupt .label { color: #EBD8C3; }
.kpi.haupt .wert { color: #fff; font-size: 28px; }
.kpi.haupt .sub { color: #E2CCB4; }

.abschnitt { font-size: 17px; font-weight: 700; color: #2B1B0C; margin: 2px 0 0; letter-spacing: -.01em; }
.abschnitt-sub { color: #8C8278; font-size: 13px; margin: 2px 0 10px; }

.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #EFE6DC; }
.stTabs [data-baseweb="tab"] { height: 46px; padding: 0 18px; border-radius: 12px 12px 0 0; font-weight: 600; }
.stTabs [aria-selected="true"] { background: #F7F1EA; }
[data-testid="stDataFrame"] { border: 1px solid #EFE6DC; border-radius: 12px; overflow: hidden; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px; }
.stButton button, .stDownloadButton button { border-radius: 10px; font-weight: 600; }

.p-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; margin: 6px 0 18px; }
.pkarte { background: #fff; border: 1px solid #EFE6DC; border-radius: 16px; padding: 16px 18px;
          box-shadow: 0 1px 2px rgba(84,55,25,.04), 0 8px 22px rgba(84,55,25,.06); }
.pkopf { display: flex; align-items: center; gap: 12px; }
.avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #B17946, #543719); color: #fff;
          display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px; flex-shrink: 0; }
.pname { font-weight: 700; color: #2B1B0C; font-size: 15.5px; }
.prang { font-size: 12px; color: #8C8278; }
.pwerte { display: flex; justify-content: space-between; margin-top: 14px; }
.pwerte .k { font-size: 11px; color: #8A6B4E; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; }
.pwerte .v { font-size: 17px; font-weight: 800; color: #2B1B0C; font-variant-numeric: tabular-nums; }
.stapel { display: flex; height: 8px; border-radius: 99px; overflow: hidden; background: #F3ECE4; margin-top: 12px; }
.stapel span { height: 100%; }
.legende { display: flex; gap: 12px; font-size: 11.5px; color: #8C8278; margin-top: 7px; flex-wrap: wrap; }
.legende i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }

@media (max-width: 640px) {
  .kpi-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
  .kpi { padding: 13px 12px 12px 15px; }
  .kpi .wert { font-size: 18px; }
  .kpi .label { font-size: 10px; }
  .kpi.haupt { grid-column: 1 / -1; }
  .kpi.haupt .wert { font-size: 26px; }
  .hero { padding: 20px; }
  .hero .titel { font-size: 22px; }
}
.login { max-width: 420px; margin: 8vh auto 0; text-align: center; }
.login img { width: 72px; height: 72px; border-radius: 16px; margin-bottom: 14px; box-shadow: 0 6px 18px rgba(84,55,25,.2); }
.login .titel { font-size: 24px; font-weight: 800; color: #2B1B0C; }
.login .sub { color: #8C8278; font-size: 14px; margin: 4px 0 18px; }
</style>
""",
    unsafe_allow_html=True,
)


def eur(x, nachkomma=2):
    s = f"{x:,.{nachkomma}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{s} €"


def zahl(x, nachkomma=2):
    return f"{x:,.{nachkomma}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def prozent(teil, ganzes):
    return 0 if not ganzes else teil / ganzes * 100


def kpi_karte(label, wert, sub="", akzent=BRAUN, anteil=None, haupt=False):
    bar = f'<div class="bar"><div style="width:{max(0, min(100, anteil)):.1f}%"></div></div>' if anteil is not None else ""
    klasse = "kpi haupt" if haupt else "kpi"
    return (
        f'<div class="{klasse}" style="--akzent:{akzent}"><div class="label">{label}</div>'
        f'<div class="wert">{wert}</div><div class="sub">{sub}</div>{bar}</div>'
    )


def kpi_reihe(karten):
    st.markdown('<div class="kpi-grid">' + "".join(karten) + "</div>", unsafe_allow_html=True)


def abschnitt(titel, unterzeile=""):
    sub = f'<div class="abschnitt-sub">{unterzeile}</div>' if unterzeile else ""
    st.markdown(f'<div class="abschnitt">{titel}</div>{sub}', unsafe_allow_html=True)


def monat_rang(monat):
    return MONATE.index(monat) if monat in MONATE else 99


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
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

    st.markdown(
        f'<div class="login"><img src="data:image/png;base64,{LOGO_BASE64}"><div class="titel">{html.escape(APP_TITEL)}</div>'
        '<div class="sub">Bitte melde dich mit deinem Passwort an.</div></div>',
        unsafe_allow_html=True,
    )
    _, mitte, _ = st.columns([1, 1.2, 1])
    with mitte:
        st.text_input("Passwort", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("Falsches Passwort")
    return False


if not check_password():
    st.stop()

# Fachliche Konstanten/Formeln liegen in formeln.py (gemeinsam mit mein_umsatz.py genutzt).
# Team und Quoten dieser Struktur stehen in team.py -- nur diese Datei muss man pro Struktur anpassen.
from team import ANTEIL_OVERRIDE as ADELE_ANTEIL_OVERRIDE
from team import LEITER_KEY, LEITER_QUOTE as ADELE_QUOTE
from team import TEAM_QUOTEN
try:
    from team import FEST_ANTEIL
except ImportError:  # ältere team.py ohne diese Einstellung
    FEST_ANTEIL = {}

# Eigene App für einen anderen Leiter (z.B. Emirhan) aus DEMSELBEN Code: stehen in den Streamlit-Secrets
# LEITER_KEY, LEITER_QUOTE und eine Tabelle [TEAM_QUOTEN], ersetzen sie die Einstellungen aus team.py.
# Optional dazu [ANTEIL_OVERRIDE] und [FEST_ANTEIL]. Die Tabellen müssen in den Secrets ganz unten stehen.
if "TEAM_QUOTEN" in st.secrets:
    def _quoten(name):
        return {str(k).strip().lower(): float(v) for k, v in dict(st.secrets.get(name, {})).items()}

    LEITER_KEY = str(st.secrets["LEITER_KEY"]).strip().lower()
    ADELE_QUOTE = float(st.secrets["LEITER_QUOTE"])
    TEAM_QUOTEN = _quoten("TEAM_QUOTEN")
    TEAM_QUOTEN.setdefault(LEITER_KEY, ADELE_QUOTE)
    ADELE_ANTEIL_OVERRIDE = _quoten("ANTEIL_OVERRIDE")
    FEST_ANTEIL = _quoten("FEST_ANTEIL")


def berechne_zeile(name_kunde, vertriebspartner, produkt, beitrag_text, laufzeit_text, stand_text, monat="", gesellschaft="", courtage_tabelle=None, alte_regel=True):
    partner_key = vertriebspartner.strip().lower().replace("ş", "s")

    if partner_key not in TEAM_QUOTEN:
        return [{
            "Name Kunde": name_kunde, "Vertriebspartner": vertriebspartner, "Produkt": produkt,
            "Monat": monat, "Beitrag (€)": None, "Status": "nicht im Team", "WP": None, "Auszahlung (€)": None,
            "Quelle": "", "Hinweis": "Zählt nicht (kein Teammitglied)",
        }]

    # Neue Regel (ab Oktober 2026): keine halbierten Anteile mehr, sondern die volle Differenz.
    # Der alte Sonderanteil gilt nur noch für Zeilen mit Haken in der Spalte "Alte Regel".
    # Feste Absprachen (FEST_ANTEIL in team.py) gelten für alle Zeilen ohne Haken bei "Alte Regel".
    if alte_regel and partner_key in ADELE_ANTEIL_OVERRIDE:
        quote = ADELE_ANTEIL_OVERRIDE[partner_key]
    elif partner_key in FEST_ANTEIL:
        quote = FEST_ANTEIL[partner_key]
    elif partner_key == LEITER_KEY:
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

# ---------------------------------------------------------------------------
# Kopfbereich
# ---------------------------------------------------------------------------
SHEET_CSV_URL = st.secrets.get("SHEET_CSV_URL", "")
heute = date.today().strftime("%d.%m.%Y")
live_chip = '<span class="chip"><span class="punkt"></span>Live aus Google Sheets</span>' if SHEET_CSV_URL else ""
st.markdown(
    f"""<div class="hero"><div class="hero-links"><img src="data:image/png;base64,{LOGO_BASE64}"><div>
<div class="titel">{html.escape(APP_TITEL)}</div>
<div class="untertitel">Provisionen, Wohlstandspunkte und Team auf einen Blick</div></div></div>
<div class="chips">{live_chip}<span class="chip">📅 Stand {heute}</span></div></div>""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def lade_google_sheet(url):
    return pd.read_csv(url)


leiste_filter, _, leiste_knopf = st.columns([2, 3, 1], vertical_alignment="bottom")
with leiste_knopf:
    if SHEET_CSV_URL and st.button("🔄 Aktualisieren", width="stretch"):
        lade_google_sheet.clear()

df = None

if SHEET_CSV_URL:
    try:
        df = lade_google_sheet(SHEET_CSV_URL)
    except Exception as e:
        st.error(f"Konnte die Google-Tabelle nicht laden: {e}")

with st.sidebar:
    st.markdown("### 📂 Daten")
    st.caption("Normalerweise kommen die Daten live aus der Google-Tabelle. Hier kannst du stattdessen eine CSV-Datei hochladen.")
    uploaded = st.file_uploader("CSV-Datei hochladen", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)

if df is None:
    st.info("Lade links eine CSV-Datei hoch oder richte die Google-Tabellen-Anbindung ein, um loszulegen.")
    st.stop()

# ---------------------------------------------------------------------------
# Berechnung
# ---------------------------------------------------------------------------
df.columns = [c.strip() for c in df.columns]
schluessel = [c for c in ("Name Kunde", "Vertriebspartner", "Produkt") if c in df.columns]
if schluessel:
    df = df.dropna(subset=schluessel, how="all")

# Fehlt die Spalte "Alte Regel" ganz, gilt überall der bisherige Anteil (wie bisher).
hat_regelspalte = "Alte Regel" in df.columns

alle_zeilen = []
for _, row in df.iterrows():
    alte_regel = (
        str(row.get("Alte Regel", "")).strip().lower() in ("true", "wahr", "ja", "x", "1")
        if hat_regelspalte else True
    )
    monat_wert = row.get("Monat", "")
    zeilen = berechne_zeile(
        str(row.get("Name Kunde", "")),
        str(row.get("Vertriebspartner", "")),
        str(row.get("Produkt", row.get("Produkt ", ""))),
        row.get("Beitrag"),
        row.get("Laufzeit"),
        row.get("Stand"),
        "" if pd.isna(monat_wert) else str(monat_wert).strip(),
        gesellschaft="" if pd.isna(row.get("Gesellschaften", row.get("Gesellschaft", ""))) else str(row.get("Gesellschaften", row.get("Gesellschaft", ""))),
        courtage_tabelle=COURTAGE,
        alte_regel=alte_regel,
    )
    ausgezahlt = str(row.get("Ausgezahlt", "")).strip().lower() in ("true", "wahr", "ja", "x", "1")
    for zeile in zeilen:
        zeile["Ausgezahlt"] = ausgezahlt
    alle_zeilen.extend(zeilen)

if not alle_zeilen:
    st.info("Die Tabelle enthält noch keine Geschäfte. Sobald Zeilen eingetragen sind, erscheint hier die Auswertung.")
    st.stop()

ergebnis_df = pd.DataFrame(alle_zeilen)
ergebnis_df = ergebnis_df.sort_values(["Vertriebspartner", "Name Kunde"]).reset_index(drop=True)
# Gleiche Person mit unterschiedlicher Schreibweise (z.B. Büşra/Büsra) zusammenfassen.
ergebnis_df["Vertriebspartner"] = (
    ergebnis_df["Vertriebspartner"].str.strip().str.replace("ş", "s").str.replace("Ş", "S").str.title()
)

# Für die Kurve immer alle Monate, unabhängig vom Filter.
berechnet_alle = ergebnis_df[ergebnis_df["Auszahlung (€)"].notna()].copy()

monate_vorhanden = sorted((m for m in ergebnis_df["Monat"].unique() if m), key=lambda m: (monat_rang(m), m))
with leiste_filter:
    monat_auswahl = st.selectbox("📅 Zeitraum", ["Alle Monate"] + monate_vorhanden)
if monat_auswahl != "Alle Monate":
    ergebnis_df = ergebnis_df[ergebnis_df["Monat"] == monat_auswahl].reset_index(drop=True)

berechnet = ergebnis_df[ergebnis_df["Auszahlung (€)"].notna()].copy()


def summe(status, feld):
    return berechnet[berechnet["Status"] == status][feld].sum()


sicher = summe("policiert", "Auszahlung (€)")
ausstehend = summe("eingereicht", "Auszahlung (€)")
offen_summe = summe("offen", "Auszahlung (€)")
gesamt = berechnet["Auszahlung (€)"].sum()
gesamt_wp = berechnet["WP"].sum()
gesamt_umsatz = berechnet["Beitrag (€)"].sum()
wp_pol, wp_ein, wp_off = summe("policiert", "WP"), summe("eingereicht", "WP"), summe("offen", "WP")
anzahl_hinweise = int((ergebnis_df["Hinweis"] != "").sum())

# ---------------------------------------------------------------------------
# Kennzahlen
# ---------------------------------------------------------------------------
zeitraum = "alle Monate" if monat_auswahl == "Alle Monate" else monat_auswahl
kpi_reihe([
    kpi_karte("Gesamt-Vergütung", eur(gesamt), f"{len(berechnet)} Verträge · {zeitraum}", haupt=True),
    kpi_karte("Sicher (policiert)", eur(sicher), f"{prozent(sicher, gesamt):.0f} % der Vergütung",
              STATUS_FARBE["Policiert"], prozent(sicher, gesamt)),
    kpi_karte("Ausstehend (eingereicht)", eur(ausstehend), f"{prozent(ausstehend, gesamt):.0f} % der Vergütung",
              STATUS_FARBE["Eingereicht"], prozent(ausstehend, gesamt)),
    kpi_karte("Offenes Geschäft", eur(offen_summe), f"{prozent(offen_summe, gesamt):.0f} % der Vergütung",
              STATUS_FARBE["Offen"], prozent(offen_summe, gesamt)),
])
kpi_reihe([
    kpi_karte("Umsatz", eur(gesamt_umsatz), "Summe der Beiträge", DUNKEL),
    kpi_karte("Gesamt-WP", zahl(gesamt_wp), "Wohlstandspunkte", BRAUN),
    kpi_karte("WP policiert", zahl(wp_pol), f"{prozent(wp_pol, gesamt_wp):.0f} % der WP",
              STATUS_FARBE["Policiert"], prozent(wp_pol, gesamt_wp)),
    kpi_karte("WP eingereicht", zahl(wp_ein), f"{prozent(wp_ein, gesamt_wp):.0f} % der WP",
              STATUS_FARBE["Eingereicht"], prozent(wp_ein, gesamt_wp)),
    kpi_karte("WP offen", zahl(wp_off), f"{prozent(wp_off, gesamt_wp):.0f} % der WP",
              STATUS_FARBE["Offen"], prozent(wp_off, gesamt_wp)),
])
if anzahl_hinweise:
    st.warning(f"⚠️ {anzahl_hinweise} Zeilen konnten nicht automatisch berechnet werden. Details im Reiter „Geschäfte“.")

# ---------------------------------------------------------------------------
# Diagramme
# ---------------------------------------------------------------------------
def status_skala(staende):
    da = [s for s in STATUS_FARBE if s in set(staende)]
    return alt.Scale(domain=da, range=[STATUS_FARBE[s] for s in da])
ACHSE_Y = dict(format=",.0f", gridDash=[3, 3], gridColor="#EFE6DC", domain=False, ticks=False, labelColor="#8C8278")


def x_monat(reihenfolge):
    return alt.X("Monat:N", sort=reihenfolge, title=None,
                 axis=alt.Axis(labelAngle=0, labelFontSize=12, labelColor="#5C4A3A", domainColor="#E3D6C8", ticks=False))


def fertig(chart, hoehe):
    return (
        chart.properties(height=hoehe)
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont="Inter", titleFont="Inter")
        .configure_legend(labelFont="Inter", labelFontSize=12, symbolType="circle", orient="top", title=None)
    )


def umsatz_kurve(pro_monat, reihenfolge):
    x = x_monat(reihenfolge)
    pro_monat = pro_monat.assign(Rang=pro_monat["Monat"].map(reihenfolge.index)).sort_values("Rang")
    lang = pro_monat.melt(id_vars=["Monat", "Rang"], value_vars=["Umsatz", "Vergütung"], var_name="Kennzahl", value_name="Betrag")
    reihe = alt.Order("Rang:Q")
    farbe = alt.Color("Kennzahl:N", scale=alt.Scale(domain=["Umsatz", "Vergütung"], range=[BRAUN, "#2E7D5B"]),
                      legend=alt.Legend(title=None))
    tooltip = [alt.Tooltip("Monat:N"), alt.Tooltip("Kennzahl:N"), alt.Tooltip("Betrag:Q", format=",.2f", title="Betrag (€)")]
    flaeche = alt.Chart(pro_monat).mark_area(
        interpolate="monotone", color=BRAUN, opacity=0.13,
    ).encode(x=x, y=alt.Y("Umsatz:Q", title=None, axis=alt.Axis(**ACHSE_Y)), order=reihe)
    linien = alt.Chart(lang).mark_line(interpolate="monotone", strokeWidth=3).encode(
        x=x, y="Betrag:Q", color=farbe, order=reihe)
    punkte = alt.Chart(lang).mark_circle(size=95, opacity=1, stroke="white", strokeWidth=2).encode(
        x=x, y="Betrag:Q", color=farbe, tooltip=tooltip)
    werte = alt.Chart(lang).mark_text(dy=-15, fontWeight="bold", fontSize=12).encode(
        x=x, y="Betrag:Q", color=farbe, text=alt.Text("Betrag:Q", format=",.0f"))
    return fertig(flaeche + linien + punkte + werte, 340)


def status_balken(daten, feld, reihenfolge, format_):
    d = daten.groupby(["Monat", "Status"], as_index=False)[feld].sum()
    d["Stand"] = d["Status"].map(STATUS_NAME).fillna(d["Status"])
    d["Rang"] = d["Stand"].map(STATUS_RANG).fillna(9)
    chart = alt.Chart(d).mark_bar(size=34, cornerRadius=3).encode(
        x=x_monat(reihenfolge),
        y=alt.Y(f"sum({feld}):Q", title=None, axis=alt.Axis(**ACHSE_Y)),
        color=alt.Color("Stand:N", scale=status_skala(d["Stand"]), legend=alt.Legend(title=None)),
        order=alt.Order("Rang:Q", sort="ascending"),
        tooltip=[alt.Tooltip("Monat:N"), alt.Tooltip("Stand:N"), alt.Tooltip(f"{feld}:Q", format=format_)],
    )
    return fertig(chart, 280)


def status_donut(daten):
    d = daten.groupby("Status", as_index=False)["WP"].sum()
    d["Stand"] = d["Status"].map(STATUS_NAME).fillna(d["Status"])
    d = d[d["WP"] > 0]
    ring = alt.Chart(d).mark_arc(innerRadius=72, outerRadius=112, cornerRadius=5, padAngle=0.015).encode(
        theta=alt.Theta("WP:Q"),
        color=alt.Color("Stand:N", scale=status_skala(d["Stand"]), legend=alt.Legend(title=None)),
        tooltip=[alt.Tooltip("Stand:N"), alt.Tooltip("WP:Q", format=",.2f")],
    )
    zahl_text = alt.Chart(pd.DataFrame({"z": [zahl(d["WP"].sum(), 0)]})).mark_text(
        dy=-6, fontSize=26, fontWeight="bold", color="#2B1B0C").encode(text="z:N")
    unter_text = alt.Chart(pd.DataFrame({"z": ["WP gesamt"]})).mark_text(
        dy=18, fontSize=12, color="#8C8278").encode(text="z:N")
    return fertig(ring + zahl_text + unter_text, 280)


def partner_balken(daten):
    d = daten.groupby(["Vertriebspartner", "Status"], as_index=False)["WP"].sum()
    d["Stand"] = d["Status"].map(STATUS_NAME).fillna(d["Status"])
    d["Rang"] = d["Stand"].map(STATUS_RANG).fillna(9)
    reihenfolge = daten.groupby("Vertriebspartner")["WP"].sum().sort_values(ascending=False).index.tolist()
    chart = alt.Chart(d).mark_bar(size=20, cornerRadius=3).encode(
        y=alt.Y("Vertriebspartner:N", sort=reihenfolge, title=None,
                axis=alt.Axis(labelFontSize=12, labelColor="#5C4A3A", domain=False, ticks=False)),
        x=alt.X("sum(WP):Q", title=None, axis=alt.Axis(**ACHSE_Y)),
        color=alt.Color("Stand:N", scale=status_skala(d["Stand"]), legend=alt.Legend(title=None)),
        order=alt.Order("Rang:Q", sort="ascending"),
        tooltip=[alt.Tooltip("Vertriebspartner:N"), alt.Tooltip("Stand:N"), alt.Tooltip("WP:Q", format=",.2f")],
    )
    return fertig(chart, max(180, 38 * len(reihenfolge)))


# ---------------------------------------------------------------------------
# Partner-Auswertung (für Reiter "Entwicklung" und "Partner")
# ---------------------------------------------------------------------------
gp_zeilen = []
for partner, teil in berechnet.groupby("Vertriebspartner"):
    nach = lambda status, feld: teil[teil["Status"] == status][feld].sum()  # noqa: E731
    gp_zeilen.append({
        "Vertriebspartner": partner,
        "Verträge": len(teil),
        "Umsatz gesamt (€)": teil["Beitrag (€)"].sum(),
        "WP gesamt": teil["WP"].sum(),
        "Umsatz policiert (€)": nach("policiert", "Beitrag (€)"),
        "WP policiert": nach("policiert", "WP"),
        "WP eingereicht": nach("eingereicht", "WP"),
        "WP offen": nach("offen", "WP"),
        "Deine Vergütung (€)": teil["Auszahlung (€)"].sum(),
    })
gp_df = (
    pd.DataFrame(gp_zeilen).sort_values("WP gesamt", ascending=False).reset_index(drop=True)
    if gp_zeilen else pd.DataFrame()
)

tab_entw, tab_partner, tab_ausz, tab_gesch = st.tabs(["📈 Entwicklung", "👥 Partner", "💸 Auszahlungen", "📋 Geschäfte"])

# ---------------------------------------------------------------------------
# Reiter: Entwicklung
# ---------------------------------------------------------------------------
with tab_entw:
    mit_monat = berechnet_alle[berechnet_alle["Monat"] != ""]
    if mit_monat.empty:
        st.info("Trage in der Spalte „Monat“ Werte ein, dann erscheint hier die Umsatzkurve.")
    else:
        reihenfolge = sorted(mit_monat["Monat"].unique(), key=lambda m: (monat_rang(m), m))
        pro_monat = mit_monat.groupby("Monat", as_index=False).agg(
            Umsatz=("Beitrag (€)", "sum"), Vergütung=("Auszahlung (€)", "sum"), WP=("WP", "sum"))
        with st.container(border=True):
            abschnitt("Umsatzentwicklung",
                      "Umsatz (Summe der Beiträge) und deine Vergütung pro Monat, über alle Status. Zeigt immer alle Monate.")
            st.altair_chart(umsatz_kurve(pro_monat, reihenfolge), use_container_width=True)
        links, rechts = st.columns(2)
        with links, st.container(border=True):
            abschnitt("Vergütung pro Monat", "Aufgeteilt nach Stand des Vertrags")
            st.altair_chart(status_balken(mit_monat, "Auszahlung (€)", reihenfolge, ",.2f"), use_container_width=True)
        with rechts, st.container(border=True):
            abschnitt("WP pro Monat", "Aufgeteilt nach Stand des Vertrags")
            st.altair_chart(status_balken(mit_monat, "WP", reihenfolge, ",.2f"), use_container_width=True)

    if not berechnet.empty:
        links, rechts = st.columns([2, 3])
        with links, st.container(border=True):
            abschnitt("WP nach Stand", zeitraum[:1].upper() + zeitraum[1:])
            st.altair_chart(status_donut(berechnet), use_container_width=True)
        with rechts, st.container(border=True):
            abschnitt("WP pro Geschäftspartner", zeitraum[:1].upper() + zeitraum[1:])
            st.altair_chart(partner_balken(berechnet), use_container_width=True)

# ---------------------------------------------------------------------------
# Reiter: Partner
# ---------------------------------------------------------------------------
with tab_partner:
    if gp_df.empty:
        st.info("Für diese Auswahl gibt es noch keine berechneten Geschäfte.")
    else:
        abschnitt("Rangliste nach WP", f"Umsatz = Summe der Beiträge · {zeitraum}")
        karten = []
        for rang, r in gp_df.iterrows():
            medaille = {0: "🥇", 1: "🥈", 2: "🥉"}.get(rang, f"#{rang + 1}")
            wp = r["WP gesamt"] or 0
            teile = "".join(
                f'<span style="width:{prozent(r[f"WP {s.lower()}"], wp):.1f}%;background:{STATUS_FARBE[s]}"></span>'
                for s in ("Policiert", "Eingereicht", "Offen")
            )
            initialen = "".join(w[0] for w in str(r["Vertriebspartner"]).split()[:2]).upper() or "?"
            karten.append(
                f'<div class="pkarte"><div class="pkopf"><div class="avatar">{html.escape(initialen)}</div><div>'
                f'<div class="pname">{html.escape(str(r["Vertriebspartner"]))}</div>'
                f'<div class="prang">{medaille} · {int(r["Verträge"])} Verträge</div></div></div>'
                f'<div class="pwerte"><div><div class="k">WP</div><div class="v">{zahl(wp)}</div></div>'
                f'<div style="text-align:right"><div class="k">Umsatz</div><div class="v">{eur(r["Umsatz gesamt (€)"])}</div></div></div>'
                f'<div class="stapel">{teile}</div>'
                f'<div class="legende"><span><i style="background:{STATUS_FARBE["Policiert"]}"></i>{zahl(r["WP policiert"], 0)} pol.</span>'
                f'<span><i style="background:{STATUS_FARBE["Eingereicht"]}"></i>{zahl(r["WP eingereicht"], 0)} eing.</span>'
                f'<span><i style="background:{STATUS_FARBE["Offen"]}"></i>{zahl(r["WP offen"], 0)} offen</span></div></div>'
            )
        st.markdown('<div class="p-grid">' + "".join(karten) + "</div>", unsafe_allow_html=True)

        with st.container(border=True):
            abschnitt("Alle Zahlen pro Partner", "„Deine Vergütung“ ist dein Anteil an den Geschäften dieses Partners.")
            gp_config = {c: st.column_config.NumberColumn(c, format="%.2f €") for c in gp_df.columns if "(€)" in c}
            gp_config.update({c: st.column_config.NumberColumn(c, format="%.2f") for c in gp_df.columns if c.startswith("WP")})
            st.dataframe(gp_df, width="stretch", hide_index=True, column_config=gp_config)

        with st.container(border=True):
            abschnitt("Geschäfte eines Partners", "Wähle einen Partner, um seine einzelnen Kunden zu sehen.")
            partner_wahl = st.selectbox("Partner", ["–"] + gp_df["Vertriebspartner"].tolist(), label_visibility="collapsed")
            if partner_wahl != "–":
                einzel = berechnet[berechnet["Vertriebspartner"] == partner_wahl].copy()
                einzel["Status"] = einzel["Status"].map(STATUS_LABEL).fillna(einzel["Status"])
                st.dataframe(
                    einzel[["Name Kunde", "Monat", "Produkt", "Beitrag (€)", "WP", "Auszahlung (€)", "Status"]]
                    .sort_values(["Monat", "Name Kunde"]),
                    width="stretch", hide_index=True,
                    column_config={
                        "Beitrag (€)": st.column_config.NumberColumn("Umsatz (€)", format="%.2f €"),
                        "WP": st.column_config.NumberColumn("WP", format="%.2f"),
                        "Auszahlung (€)": st.column_config.NumberColumn("Deine Vergütung (€)", format="%.2f €"),
                    },
                )

# ---------------------------------------------------------------------------
# Reiter: Auszahlungen
# ---------------------------------------------------------------------------
with tab_ausz:
    abschnitt("Auszahlungs-Checkliste",
              "Policiertes Geschäft. Abgehakt wird in deiner Google-Tabelle in der Spalte „Ausgezahlt“; "
              "die App liest es alle 60 Sekunden neu. Folgt dem Zeitraum oben.")
    pol = berechnet[berechnet["Status"] == "policiert"].copy()
    pol["Ausgezahlt"] = pol["Ausgezahlt"].fillna(False).astype(bool)
    noch_offen = pol[~pol["Ausgezahlt"]]["Auszahlung (€)"].sum()
    schon_bezahlt = pol[pol["Ausgezahlt"]]["Auszahlung (€)"].sum()
    pipeline = ausstehend + offen_summe

    kpi_reihe([
        kpi_karte("Policiert, noch nicht ausgezahlt", eur(noch_offen), f"{int((~pol['Ausgezahlt']).sum())} Verträge", "#C2410C"),
        kpi_karte("Bereits ausgezahlt", eur(schon_bezahlt), f"{int(pol['Ausgezahlt'].sum())} Verträge",
                  STATUS_FARBE["Policiert"], prozent(schon_bezahlt, schon_bezahlt + noch_offen)),
        kpi_karte("Noch in der Pipeline", eur(pipeline), "eingereicht + offen", STATUS_FARBE["Eingereicht"]),
        kpi_karte("Insgesamt noch zu erwarten", eur(noch_offen + pipeline), "nicht ausgezahlt + Pipeline", DUNKEL),
    ])

    ansicht = st.segmented_control(
        "Anzeigen", ["Noch nicht ausgezahlt", "Bereits ausgezahlt", "Alle"], default="Noch nicht ausgezahlt"
    ) or "Alle"
    if ansicht == "Noch nicht ausgezahlt":
        pol = pol[~pol["Ausgezahlt"]]
    elif ansicht == "Bereits ausgezahlt":
        pol = pol[pol["Ausgezahlt"]]
    pol = pol.sort_values(["Ausgezahlt", "Vertriebspartner", "Monat", "Name Kunde"])
    st.dataframe(
        pol[["Ausgezahlt", "Name Kunde", "Vertriebspartner", "Monat", "Produkt", "Auszahlung (€)", "Quelle"]],
        width="stretch",
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
            je_partner, width="stretch", hide_index=True,
            column_config={"Summe (€)": st.column_config.NumberColumn("Summe (€)", format="%.2f €")},
        )

# ---------------------------------------------------------------------------
# Reiter: Geschäfte
# ---------------------------------------------------------------------------
with tab_gesch:
    anzeige_df = ergebnis_df.copy()
    anzeige_df["Status"] = anzeige_df["Status"].map(STATUS_LABEL).fillna(anzeige_df["Status"])
    anzeige_df = anzeige_df[["Name Kunde", "Vertriebspartner", "Monat", "Produkt", "Beitrag (€)", "WP", "Auszahlung (€)", "Quelle", "Status", "Hinweis"]]

    spalten_config = {
        "Beitrag (€)": st.column_config.NumberColumn("Beitrag (€)", format="%.2f €"),
        "WP": st.column_config.NumberColumn("WP", format="%.2f"),
        "Auszahlung (€)": st.column_config.NumberColumn("Auszahlung aufs Konto (€)", format="%.2f €"),
    }

    with st.container(border=True):
        abschnitt("Alle Geschäfte", f"Ergebnis pro Zeile · {zeitraum}")
        suche = st.text_input("Suche", placeholder="🔎 Kunde, Partner oder Produkt suchen …", label_visibility="collapsed")
        gefiltert = anzeige_df
        if suche.strip():
            s = suche.strip().lower()
            treffer = (
                anzeige_df["Name Kunde"].astype(str).str.lower().str.contains(s, regex=False)
                | anzeige_df["Vertriebspartner"].astype(str).str.lower().str.contains(s, regex=False)
                | anzeige_df["Produkt"].astype(str).str.lower().str.contains(s, regex=False)
            )
            gefiltert = anzeige_df[treffer]
        st.dataframe(gefiltert, width="stretch", hide_index=True, column_config=spalten_config)

    offene = anzeige_df[anzeige_df["Hinweis"] != ""]
    if not offene.empty:
        with st.expander(f"⚠️ {len(offene)} Zeilen, die ich nicht automatisch berechnen konnte", expanded=False):
            st.dataframe(offene, width="stretch", hide_index=True, column_config=spalten_config)

    links, rechts = st.columns([3, 2])
    with links, st.container(border=True):
        abschnitt("Monatsübersicht pro Kunde",
                  "Nur policiertes (sicheres) Geschäft. Zum Monatsende in deine Bestandskunden-Tabelle übertragen.")
        monatsuebersicht = (
            berechnet[berechnet["Status"] == "policiert"]
            .groupby("Name Kunde", as_index=False)
            .agg(**{"Umsatz (€)": ("Beitrag (€)", "sum"), "WP": ("WP", "sum")})
            .sort_values("Name Kunde")
            .reset_index(drop=True)
        )
        st.dataframe(
            monatsuebersicht, width="stretch", hide_index=True,
            column_config={
                "Umsatz (€)": st.column_config.NumberColumn("Umsatz (€)", format="%.2f €"),
                "WP": st.column_config.NumberColumn("WP", format="%.2f"),
            },
        )
        st.download_button(
            "⬇️ Als CSV herunterladen",
            monatsuebersicht.to_csv(index=False).encode("utf-8"),
            file_name=f"monatsuebersicht_{pd.Timestamp.today().strftime('%Y-%m')}.csv",
            mime="text/csv",
        )

    with rechts, st.container(border=True):
        abschnitt("Stand nach Status", "WP und Vergütung zusammengefasst")

        def status_summe(maske):
            teil = berechnet[maske]
            return {"Verträge": len(teil), "WP": teil["WP"].sum(), "Vergütung (€)": teil["Auszahlung (€)"].sum()}

        st_ = berechnet["Status"]
        status_tabelle = pd.DataFrame([
            {"Stand": "✅ Policiert", **status_summe(st_ == "policiert")},
            {"Stand": "🟡 Eingereicht", **status_summe(st_ == "eingereicht")},
            {"Stand": "➕ Policiert + eingereicht", **status_summe(st_.isin(["policiert", "eingereicht"]))},
            {"Stand": "🔵 Offen", **status_summe(st_ == "offen")},
            {"Stand": "🧮 Alles zusammen", **status_summe(st_.notna())},
        ])
        st.dataframe(
            status_tabelle, width="stretch", hide_index=True,
            column_config={
                "WP": st.column_config.NumberColumn("WP", format="%.2f"),
                "Vergütung (€)": st.column_config.NumberColumn("Vergütung (€)", format="%.2f €"),
            },
        )
