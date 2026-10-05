"""Gemeinsame K&W-Wohlstandspunkte-Formeln, genutzt von app.py (Adeles Team-Ansicht)
und mein_umsatz.py (persönliche Ansicht für einzelne Vertriebspartner).

Reine Rechenlogik ohne Streamlit-Code, damit beide Apps sie unverändert importieren
können, ohne dass beim Import bereits eine Seite gerendert wird.
"""

import re

import courtage

# --- Fachliche Konstanten (K&W Wohlstandspunkte-System) ---
# Quelle: Canva-Kickoff-Präsentation "K&W - Kick Off 27.06.2026" + Angaben von Adele.
# Update 2026-09-08: Provisionssatz und Gesamtumsatz-Abzug angepasst, gilt für alle Stufen/Partner.

VOLLWERT_PRO_WP = 44.0  # 4,4% * 1000, entspricht 100% Quote (vorher 4,3%)
GESAMTUMSATZ_ABZUG = 0.90  # 10% werden abgezogen, 90% bleiben übrig (vorher 25% Abzug/75%)
STORNORESERVE_ABZUG = 0.90  # 10% Stornoreserve auf jedes Geschäft, für alle gleich, bleiben 90% übrig

# KV (Krankenversicherung) hat seit 2026-09-08 eine eigene Vergütungsformel, komplett
# losgelöst vom WP/Bewertungssumme-Modell der anderen Sparten:
# Auszahlung = KV_MONATSBEITRAEGE_100 * Quote * (Bruttobeitrag - KV_NETTO_ABZUG) * GESAMTUMSATZ_ABZUG * STORNORESERVE_ABZUG
# WP wird trotzdem weiter aus dem Bruttobeitrag berechnet (Bruttobeitrag / 6), rein für die
# Karrierestufen-Statistik -- hat keinen Einfluss mehr auf die Auszahlung.
KV_NETTO_ABZUG = 50.0       # vom Bruttobeitrag abgezogen, um den (vereinfachten) Nettobeitrag zu schätzen
KV_MONATSBEITRAEGE_100 = 9.0  # Monatsbeiträge Provision bei 100% Quote

LEBEN_PRODUKTE = {"bu", "pav", "bav", "rürup", "ruerup", "kidspolice"}
# "zz" (Zahnzusatz) seit 2026-09-30: gleiche Formel wie Sach (WP = Beitrag / 6).
SACH_PRODUKTE = {"sach", "gewerbe sach", "wohngebäude", "wohngebaeude", "zz"}
KRANKEN_PRODUKTE = {"pkv"}
AUSGESCHLOSSEN_PRODUKTE = {"depot"}  # wird aktuell nicht verkauft/berechnet

# Seit 2026-09-08: Die "Stand"-Spalte akzeptiert nur noch genau eines dieser drei Wörter.
# Alles andere (alte Freitexte wie "unterschrieben", "Termin nächste Woche?" etc.) zählt
# nicht mehr und wird als "unklar" behandelt.
STAND_STUFEN = ["offen", "eingereicht", "policiert"]


def parse_beitrag(text):
    """"50€" -> 50.0. Gibt None zurück, wenn kein Betrag erkennbar ist."""
    if isinstance(text, (int, float)):
        return None if text != text else float(text)  # text != text erkennt NaN
    if not isinstance(text, str) or not text.strip():
        return None
    match = re.search(r"[\d.,]+", text.replace(".", "").replace(",", "."))
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def parse_zahl(wert):
    """"22,2" / 22.2 / "144" -> float; None bei leer/ungültig."""
    if isinstance(wert, (int, float)):
        return None if wert != wert else float(wert)
    if not isinstance(wert, str) or not wert.strip():
        return None
    try:
        return float(wert.strip().replace(".", "").replace(",", ".") if "," in wert else wert.strip())
    except ValueError:
        return None


def parse_laufzeit_jahre(text):
    """Versucht eine Jahreszahl aus der Laufzeit-Spalte zu lesen.
    Gibt (jahre, ist_unklar) zurück. jahre ist None, wenn nicht eindeutig."""
    if isinstance(text, (int, float)):
        return (None, True) if text != text else (int(text), False)  # text != text erkennt NaN
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


def stand_status(text):
    if not isinstance(text, str) or not text.strip():
        return "unklar"
    t = text.strip().lower()
    if t in STAND_STUFEN:
        return t
    return "unklar"


def berechne_positionen(
    name_kunde, quote, produkt, beitrag_text, laufzeit_text, stand_text, monat="",
    gesellschaft="", courtage_tabelle=None, wp_vorgabe=None,
):
    """Berechnet WP/Auszahlung für alle Positionen einer Zeile (ggf. mehrere bei Kombi-
    Produkten wie "PAV + Depot"), mit der übergebenen persönlichen `quote` (0.0-1.0) als
    Vergütungssatz. `quote` ist entweder die volle eigene Quote (persönliche Ansicht) oder
    eine Differenz-Quote (Adeles Anteil an Teamgeschäft) -- die Formel selbst ist identisch.

    Mit `courtage_tabelle` (courtage.lade_tabelle) und eingetragener `gesellschaft` kommt der
    Satz aus der Courtageliste (Stufe-5-Satz / 0,80 = Satz bei 100 % Quote, dann mal `quote`);
    sonst gilt der bisherige Standardsatz. `wp_vorgabe` sind in der Tabelle eingetragene WP
    (enthalten die Bewertungsfaktoren der Gesellschaft) und ersetzen bei Leben-Sparten die
    selbst gerechneten WP.
    """
    stand = stand_status(stand_text)
    ges = str(gesellschaft or "").strip()
    if ges.lower() == "nan":
        ges = ""
    ergebnisse = []

    for teilprodukt, teilbeitrag_text in split_produkt_beitrag(produkt, beitrag_text):
        kategorie = produkt_kategorie(teilprodukt)
        beitrag = parse_beitrag(teilbeitrag_text)
        sparte, bevorzugt = courtage.sparte_fuer(teilprodukt)
        nutze_courtage = courtage_tabelle is not None and bool(ges) and sparte is not None

        zeile = {
            "Name Kunde": name_kunde,
            "Produkt": teilprodukt,
            "Monat": monat,
            "Beitrag (€)": None,
            "Status": stand,
            "WP": None,
            "Auszahlung (€)": None,
            "Quelle": "",
            "Hinweis": "",
        }

        if kategorie == "ausgeschlossen":
            zeile["Hinweis"] = "Depot – wird aktuell nicht berechnet"
            ergebnisse.append(zeile)
            continue
        if kategorie == "unbekannt" and not nutze_courtage:
            zeile["Hinweis"] = (
                "Gesellschaft fehlt – bitte in der Spalte Gesellschaft eintragen"
                if sparte is not None and courtage_tabelle is not None
                else "Unbekanntes Produkt – bitte Formel klären"
            )
            ergebnisse.append(zeile)
            continue
        if stand == "unklar":
            zeile["Hinweis"] = "Status nicht erkannt (nur offen/eingereicht/policiert werden gewertet)"
            ergebnisse.append(zeile)
            continue
        if beitrag is None:
            zeile["Hinweis"] = "Kein Beitrag erkannt"
            ergebnisse.append(zeile)
            continue

        multiplikator, _ = produkt_multiplikator_und_name(teilprodukt)
        abzuege = GESAMTUMSATZ_ABZUG * STORNORESERVE_ABZUG

        if nutze_courtage:
            satz = courtage.satz_fuer(courtage_tabelle, sparte, ges, bevorzugt)
            if satz.get("fehler"):
                zeile["Hinweis"] = satz["fehler"]
                ergebnisse.append(zeile)
                continue
            if satz["eur_je_wp"] is not None:
                satz_100 = satz["eur_je_wp"] / courtage.STUFEN_QUOTE[5]
                if sparte in courtage.KV_SPARTEN:
                    # PKV: Provision auf den (vereinfachten) Nettobeitrag, WP bleiben Brutto / 6.
                    basis = beitrag - KV_NETTO_ABZUG if sparte == "PKV" else beitrag
                    if basis <= 0:
                        zeile["Hinweis"] = "Bruttobeitrag zu niedrig für Netto-Abzug (50€) – bitte prüfen"
                        ergebnisse.append(zeile)
                        continue
                    wp_verguetung = basis / 6 * multiplikator
                    wp = wp_vorgabe if wp_vorgabe is not None else beitrag / 6 * multiplikator
                else:
                    if wp_vorgabe is not None:
                        wp = wp_verguetung = wp_vorgabe
                    else:
                        jahre, unklar = parse_laufzeit_jahre(laufzeit_text)
                        if unklar:
                            zeile["Hinweis"] = "Laufzeit fehlt/unklar – bitte manuell nachtragen"
                            ergebnisse.append(zeile)
                            continue
                        if satz["bz_dauer_jahre"]:
                            jahre = min(jahre, satz["bz_dauer_jahre"])
                        wp = wp_verguetung = beitrag * 12 * jahre / 1000 * multiplikator
                auszahlung = wp_verguetung * satz_100 * quote * abzuege
            else:
                wp = wp_vorgabe if wp_vorgabe is not None else beitrag / 6 * multiplikator
                auszahlung = beitrag * multiplikator * (satz["prozent"] / 100 / courtage.STUFEN_QUOTE[5]) * quote * abzuege
            tarif = f" ({satz['tarif'][:30]})" if satz["tarif"] else ""
            zeile["Quelle"] = f"Courtage: {satz['gesellschaft']}{tarif}"
            if satz["hinweis"]:
                zeile["Hinweis"] = satz["hinweis"]
        elif kategorie == "leben":
            jahre, unklar = parse_laufzeit_jahre(laufzeit_text)
            if unklar:
                zeile["Hinweis"] = "Laufzeit fehlt/unklar – bitte manuell nachtragen"
                ergebnisse.append(zeile)
                continue
            bws = beitrag * 12 * jahre
            wp = (bws / 1000) * multiplikator
            auszahlung = wp * VOLLWERT_PRO_WP * quote * abzuege
            zeile["Quelle"] = "Standardsatz"
        elif kategorie == "kranken":
            # Standardformel seit 2026-09-08: direkt in Monatsbeiträgen auf den (vereinfachten) Nettobeitrag.
            wp = (beitrag / 6) * multiplikator  # nur für Karrierestufen-Statistik
            nettobeitrag = beitrag - KV_NETTO_ABZUG
            if nettobeitrag <= 0:
                zeile["Hinweis"] = "Bruttobeitrag zu niedrig für Netto-Abzug (50€) – bitte prüfen"
                ergebnisse.append(zeile)
                continue
            auszahlung = KV_MONATSBEITRAEGE_100 * quote * nettobeitrag * multiplikator * abzuege
            zeile["Quelle"] = "Standardsatz"
        else:  # sach
            wp = (beitrag / 6) * multiplikator
            auszahlung = wp * VOLLWERT_PRO_WP * quote * abzuege
            zeile["Quelle"] = "Standardsatz"

        zeile["Beitrag (€)"] = round(beitrag * multiplikator, 2)
        zeile["WP"] = round(wp, 2)
        zeile["Auszahlung (€)"] = round(auszahlung, 2)
        ergebnisse.append(zeile)

    return ergebnisse
