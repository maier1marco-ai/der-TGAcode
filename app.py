import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
import time
import json
import openpyxl  # +++ NEU: Für Excel-Bearbeitung +++
from io import BytesIO  # +++ NEU: Um Excel-Datei im Speicher zu erstellen +++

# --- DESIGN & KERNFUNKTIONEN (unverändert) ---
# ... (Der gesamte obere Teil des Codes bis zur main()-Funktion bleibt exakt gleich)
st.set_page_config(page_title="der TGAcode", layout="wide")
st.markdown("""<style>...</style><div class="top-nav">...</div>""", unsafe_allow_html=True) # Gekürzt zur Lesbarkeit
api_key = st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
# ... alle weiteren Helferfunktionen wie init_ai_model, get_embedder, etc.

# --- UI V4: Hauptfunktion mit Excel-Export ---
def main():
    # ... (Der gesamte obere Teil der main-Funktion bleibt ebenfalls exakt gleich)
    # Projektauswahl, Stammdaten-Management, Datei-Upload, KI-Prüfung...
    # Wir springen direkt zum relevanten Teil am Ende.
    # ANNAHME: Die KI-Prüfung wurde bereits durchgeführt und st.session_state.report existiert.

    # Dieser Code-Teil existiert bereits in deiner App
    st.header("Projektauswahl")
    c1, c2 = st.columns([1, 2])
    with c1:
        firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
        sel_f = st.selectbox("Firma auswählen", ["--"] + firmen, label_visibility="collapsed")
        projekte = []
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        sel_p = st.selectbox("Projekt auswählen", ["--"] + projekte, label_visibility="collapsed")
    with c2:
        with st.expander("➕ Neues Projekt oder Firma anlegen"):
            #... Logik zum Anlegen
            pass
    st.markdown("---")

    if sel_f != "--" and sel_p != "--":
        p_path = os.path.join(VAULT, sel_f, sel_p)
        p_id = f"{sel_f}_{sel_p}".replace(" ", "_")
        
        st.header(f"Projekt-Dashboard: {sel_p}")
        t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Nachtrags-Prüfung"])

        with t1:
            # ... Logik der Projekt-Akte mit Stammdaten ...
            pass
        
        with t2:
            # ... Logik der Nachtrags-Prüfung ...
            # ANNAHME: Dieser Teil läuft wie im vorherigen Code und befüllt st.session_state.report
            # Zum Testen können wir den Report hier simulieren:
            # if "report" not in st.session_state:
            #     st.session_state.report = """Ein langer Bericht... ```json
            #     {
            #         "vob_check": "OK",
            #         "technische_prüfung": "Prüfung nötig",
            #         "preis_check": "Auffällig",
            #         "gesamtsumme_korrigiert": "ca. 9.999,00 EUR",
            #         "empfehlung": "Dringende Verhandlung empfohlen!",
            #         "naechste_schritte": "Preis für Position 3.2 anfechten"
            #     }
            #     ```"""
            pass

            if "report" in st.session_state:
                st.markdown("---")
                st.subheader("Ergebnis der KI-Prüfung")
                st.markdown(f"<div class='report-box'>{st.session_state.report.split('```json')[0]}</div>", unsafe_allow_html=True)

                # +++ NEU: Überarbeitete Sektion für Deckblatt mit Excel-Unterstützung +++
                st.markdown("---")
                st.subheader("Deckblatt aus Excel-Vorlage erstellen")

                template_file = st.file_uploader("Lade deine Deckblatt-Vorlage hoch (.xlsx)", type=["xlsx"])

                if template_file is not None:
                    try:
                        # 1. Extrahiere die JSON-Daten aus dem KI-Report (wie bisher)
                        json_part = st.session_state.report.split('```json')[1].split('```')[0]
                        report_data = json.loads(json_part)

                        # 2. Lade das Excel-Workbook mit openpyxl
                        workbook = openpyxl.load_workbook(template_file)
                        sheet = workbook.active

                        # 3. Durchlaufe alle Zellen und ersetze die Platzhalter
                        for row in sheet.iter_rows():
                            for cell in row:
                                if cell.value and isinstance(cell.value, str):
                                    # Erstelle eine Kopie der Platzhalter-Schlüssel in Großbuchstaben
                                    placeholder_keys = {f"[{k.upper()}]": v for k, v in report_data.items()}
                                    if cell.value in placeholder_keys:
                                        cell.value = placeholder_keys[cell.value]
                        
                        # 4. Speichere die bearbeitete Datei in einen In-Memory-Stream
                        output_stream = BytesIO()
                        workbook.save(output_stream)
                        output_stream.seek(0) # Zurück zum Anfang des Streams

                        st.success("Excel-Vorlage erfolgreich befüllt!")
                        
                        # 5. Biete die bearbeitete Excel-Datei zum Download an
                        st.download_button(
                            label="✅ Fertiges Deckblatt herunterladen",
                            data=output_stream,
                            file_name=f"Deckblatt_{sel_p}_{template_file.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    except Exception as e:
                        st.error(f"Fehler beim Verarbeiten der Excel-Vorlage: {e}")
                        st.info("Stellen Sie sicher, dass die Vorlage eine .xlsx-Datei ist und die Platzhalter exakt mit den JSON-Schlüsseln übereinstimmen (z.B. [EMPFEHLUNG]).")

# Bitte den gesamten Code (inkl. der oberen, unveränderten Teile) in deine .py-Datei kopieren.
if __name__ == "__main__":
    main()



