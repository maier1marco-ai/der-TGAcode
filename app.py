import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import time
from fpdf import FPDF # Für professionelle PDF-Generierung

# --- 1. DESIGN SYSTEM & IMMERSION ---
st.set_page_config(page_title="der TGAcode OS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Gesamt-Layout & Hintergrund */
    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f0f2f5 0%, #e0e5ec 100%); /* Sanfter Verlauf */
        color: #1a1c24;
    }
    
    /* Top-Navigation mit Schatten */
    .top-nav {
        background-color: #1a1c24; /* Dunkler TGAcode Hintergrund */
        padding: 15px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        border-bottom: 4px solid #00f2fe; /* TGAcode Akzent */
        margin-bottom: 40px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15); /* Dezenter Schatten */
    }
    .top-nav .logo {
        font-size: 2.2rem; /* Größerer Logo-Text */
        font-weight: 800;
        letter-spacing: -1px;
    }
    .top-nav .tagline {
        font-size: 0.9rem;
        opacity: 0.7;
        font-weight: 300;
    }

    /* Tabs Design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: center;
        margin-bottom: 25px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        width: 200px;
        background-color: #f0f2f5;
        border-radius: 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: all 0.3s ease;
        font-weight: 600;
        color: #4b5563;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e2e8f0;
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background-color: #00f2fe; /* Aktiver Tab - TGAcode Blau */
        color: #1a1c24;
        font-weight: 700;
        box-shadow: 0 4px 10px rgba(0, 242, 254, 0.3);
    }
    
    /* Content Cards (für mehr Struktur) */
    .tgacode-content-card {
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        margin-bottom: 30px;
    }

    /* Buttons (modern & clean) */
    .stButton>button {
        background-color: #1a1c24; /* Dunkelgrau */
        color: #00f2fe; /* TGAcode Blau */
        border: none;
        padding: 12px 25px;
        border-radius: 8px;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #00f2fe;
        color: #1a1c24;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 242, 254, 0.2);
    }

    /* Eingabefelder */
    .stTextInput>div>div>input, .stFileUploader>section>input {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        padding: 10px 15px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Dashboard Grid für Auswahl */
    .project-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 30px;
        margin-top: 40px;
    }
    .project-card {
        background: #ffffff;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .project-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.1);
        border-color: #00f2fe;
    }
    .project-card h3 {
        color: #1a1c24;
        margin-top: 0;
        font-size: 1.4rem;
    }
    .project-card p {
        color: #64748b;
        font-size: 0.9rem;
    }

    /* Verstecke Streamlit Header/Footer */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { right: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATEN-STRUKTUR (Vault) ---
VAULT_ROOT = "tgacode_vault"
if not os.path.exists(VAULT_ROOT): os.makedirs(VAULT_ROOT)

# --- 3. KI LOGIK (Generischer Aufruf) ---
def call_tgacode_ai(prompt, selected_project_docs=""):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return "Fehler: Gemini API Key fehlt in den Streamlit Secrets."
    
    genai.configure(api_key=api_key)
    
    try:
        model_name = 'gemini-1.5-flash-latest' # Versuch das neueste Flash-Modell
        model = genai.GenerativeModel(model_name)
        
        # KI-Persönlichkeit & Kontext
        full_prompt = f"""
        Du bist 'der TGAcode', ein Senior-Experte für Objektüberwachung und Nachtragsmanagement.
        Deine Aufgabe ist es, präzise, faktenbasierte und VOB-konforme Analysen und Empfehlungen zu liefern.
        Nutze alle verfügbaren Projektdokumente als deine Wissensbasis.
        
        --- PROJEKT-DOKUMENTE ---
        {selected_project_docs}
        --- ENDE DOKUMENTE ---
        
        NUTZERANFRAGE: {prompt}
        """
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        # Fehlermeldungen bei API-Problemen
        st.error(f"KI-Verbindungsfehler: {e}. Bitte prüfen Sie den API-Key oder die Modell-Verfügbarkeit.")
        return ""

# --- MAIN APP LOGIC ---
def main():
    # Top Navigation Bar
    st.markdown(f"""
        <div class="top-nav">
            <div class="logo">der <span style="color:#00f2fe;">TGAcode</span></div>
            <div class="tagline">DIGITAL ENGINEERING & OBJEKTÜBERWACHUNG</div>
        </div>
    """, unsafe_allow_html=True)

    # --- Initialisierung des Session State für persistente Daten ---
    if "selected_firma" not in st.session_state: st.session_state.selected_firma = "--"
    if "selected_projekt" not in st.session_state: st.session_state.selected_projekt = "--"

    # --- Projekt-Matrix / Home Screen ---
    if st.session_state.selected_projekt == "--":
        st.markdown("<h2>Willkommen im <span style='color:#00f2fe;'>TGAcode</span> OS</h2>", unsafe_allow_html=True)
        st.write("Verwalten Sie Ihre Projekte, prüfen Sie Nachträge und arbeiten Sie mit der KI zusammen.")

        firmen = [f for f in os.listdir(VAULT_ROOT) if os.path.isdir(os.path.join(VAULT_ROOT, f))]
        
        st.markdown("<div class='tgacode-content-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Mandanten & Projekte</h3>")
        st.markdown("<div class='project-grid'>")
        
        # FIRMEN-ANZEIGE / AUSWAHL
        for f_name in ["--"] + firmen:
            if f_name == "--":
                st.markdown(f"""
                    <div class="project-card" style="text-align:center;">
                        <h3>➕ Neue Firma</h3>
                        <p>Hier klicken, um eine neue Firma anzulegen.</p>
                    </div>
                """, unsafe_allow_html=True)
                # Klick-Event für die neue Firma (noch nicht aktiv)
            else:
                st.markdown(f"""
                    <div class="project-card">
                        <h3>{f_name}</h3>
                        <p>{len(os.listdir(os.path.join(VAULT_ROOT, f_name)))} Projekte</p>
                        <button onclick="window.parent.postMessage('streamlit:setSessionState', '*', {{selected_firma: '{f_name}'}})" style="width:auto; margin-top:10px;">Auswählen</button>
                    </div>
                """, unsafe_allow_html=True) # Der JS-Hack funktioniert so nicht direkt in Streamlit
        
        st.markdown("</div>") # End project-grid

        # Manuelle Auswahl für Demo
        col_select_f, col_select_p = st.columns(2)
        with col_select_f:
            selected_f_input = st.selectbox("Firma wählen", ["--"] + firmen)
            if selected_f_input != "--": st.session_state.selected_firma = selected_f_input

        if st.session_state.selected_firma != "--":
            projekte = [p for p in os.listdir(os.path.join(VAULT_ROOT, st.session_state.selected_firma)) if os.path.isdir(os.path.join(VAULT_ROOT, st.session_state.selected_firma, p))]
            with col_select_p:
                selected_p_input = st.selectbox("Projekt wählen", ["--"] + projekte)
                if selected_p_input != "--": st.session_state.selected_projekt = selected_p_input
            
        st.markdown("<br>") # Abstand

        # Erstellung von Firma/Projekt
        st.markdown("<h3>➕ Neue Einträge erstellen</h3>")
        col_new_f, col_new_p = st.columns(2)
        with col_new_f:
            new_firma_name = st.text_input("Name der neuen Firma:")
            if st.button("Neue Firma anlegen"):
                if new_firma_name:
                    os.makedirs(os.path.join(VAULT_ROOT, new_firma_name), exist_ok=True)
                    st.success(f"Firma '{new_firma_name}' erstellt.")
                    st.session_state.selected_firma = new_firma_name
                    st.rerun()
        with col_new_p:
            if st.session_state.selected_firma != "--":
                new_projekt_name = st.text_input(f"Neues Projekt für '{st.session_state.selected_firma}':")
                if st.button("Neues Projekt anlegen"):
                    if new_projekt_name:
                        os.makedirs(os.path.join(VAULT_ROOT, st.session_state.selected_firma, new_projekt_name), exist_ok=True)
                        st.success(f"Projekt '{new_projekt_name}' in '{st.session_state.selected_firma}' erstellt.")
                        st.session_state.selected_projekt = new_projekt_name
                        st.rerun()
            else:
                st.info("Wählen Sie zuerst eine Firma, um ein Projekt anzulegen.")
        
        st.markdown("</div>", unsafe_allow_html=True) # End tgacode-content-card

    # --- PROJEKT-DASHBOARD NACH AUSWAHL ---
    else:
        st.markdown(f"<h2>Projekt: <span style='color:#00f2fe;'>{st.session_state.selected_projekt}</span> <small>({st.session_state.selected_firma})</small></h2>")
        
        # Tabs für die Hauptfunktionen
        tab_vault, tab_audit, tab_chat = st.tabs(["📁 PROJEKT-AKTE", "🚀 NACHTRAGS-AUDIT", "💬 TGACODE-CHAT"])

        # --- TAB: PROJEKT-AKTE (Multi-Upload & Delete) ---
        with tab_vault:
            st.markdown("<div class='tgacode-content-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Dokumenten-Management</h3>")
            current_project_path = os.path.join(VAULT_ROOT, st.session_state.selected_firma, st.session_state.selected_projekt)
            
            uploaded_files = st.file_uploader("Neue Dokumente hinzufügen (LV, Vertrag, Pläne, etc.)", accept_multiple_files=True, type="pdf")
            if st.button("Dokumente in Akte speichern"):
                if uploaded_files:
                    for f in uploaded_files:
                        file_path = os.path.join(current_project_path, f.name)
                        with open(file_path, "wb") as file:
                            file.write(f.getbuffer())
                    st.success(f"{len(uploaded_files)} Dokument(e) archiviert.")
                    time.sleep(1) # Kurze Pause für Visualisierung
                    st.rerun()
                else:
                    st.info("Bitte wählen Sie zuerst Dateien zum Hochladen aus.")
            
            st.markdown("---")
            st.write("📂 **Aktueller Dokumentenbestand:**")
            col_doc, col_del = st.columns([0.8, 0.2])
            for f_name in os.listdir(current_project_path):
                with col_doc: st.markdown(f"• `{f_name}`")
                with col_del:
                    if st.button("Löschen", key=f"delete_{f_name}"):
                        os.remove(os.path.join(current_project_path, f_name))
                        st.success(f"'{f_name}' gelöscht.")
                        time.sleep(1)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # --- TAB: NACHTRAGS-AUDIT ---
        with tab_audit:
            st.markdown("<div class='tgacode-content-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Nachtrags-Deep-Audit</h3>")
            
            audit_files = st.file_uploader("Nachtrag + alle Anlagen (PDFs)", accept_multiple_files=True, type="pdf")
            
            if st.button("Analyse starten (KI-gestützt)"):
                if not audit_files:
                    st.error("Bitte laden Sie die Nachtrags-Dokumente hoch.")
                else:
                    with st.spinner("TGAcode OS analysiert alle Dokumente im Kontext..."):
                        # 1. Alle Projektdokumente aus dem Vault laden
                        all_project_docs = ""
                        current_project_path = os.path.join(VAULT_ROOT, st.session_state.selected_firma, st.session_state.selected_projekt)
                        for doc_name in os.listdir(current_project_path):
                            if doc_name.endswith(".pdf"): # Nur PDFs laden
                                doc_path = os.path.join(current_project_path, doc_name)
                                try:
                                    reader = PdfReader(doc_path)
                                    doc_text = "".join([page.extract_text() or "" for page in reader.pages])
                                    all_project_docs += f"\n--- DOKUMENT: {doc_name} ---\n{doc_text[:10000]}\n" # Limit pro Doc für KI
                                except Exception as e:
                                    st.warning(f"Konnte PDF '{doc_name}' nicht lesen: {e}")
                            elif doc_name.endswith(".txt"): # Auch TXT-Dateien (z.B. frühere LV-Texte) laden
                                doc_path = os.path.join(current_project_path, doc_name)
                                with open(doc_path, "r", encoding="utf-8") as f:
                                    all_project_docs += f"\n--- DOKUMENT: {doc_name} ---\n{f.read()[:10000]}\n"


                        # 2. Alle Nachtrags-Dokumente laden
                        all_nachtrag_docs = ""
                        for f in audit_files:
                            try:
                                reader = PdfReader(f)
                                nachtrag_text = "".join([page.extract_text() or "" for page in reader.pages])
                                all_nachtrag_docs += f"\n--- NACHTRAGS-ANLAGE: {f.name} ---\n{nachtrag_text[:10000]}\n"
                            except Exception as e:
                                st.warning(f"Konnte Nachtrags-PDF '{f.name}' nicht lesen: {e}")

                        # 3. KI-Prompt mit allen Daten
                        audit_prompt = f"""
                        SYSTEM-ROLLE: Du bist 'der TGAcode', ein Senior-Objektüberwacher und VOB-Spezialist für das Projekt '{st.session_state.selected_projekt}' der Firma '{st.session_state.selected_firma}'.
                        DEINE AUFGABE IST ES, EINEN NACHTRAG PRÄZISE UND VOLLSTÄNDIG ZU PRÜFEN.
                        
                        --- VERFÜGBARE PROJEKTDOKUMENTE (BASISWISSEN) ---
                        {all_project_docs}
                        --- ENDE BASISWISSEN ---
                        
                        --- ZU PRÜFENDER NACHTRAG ---
                        {all_nachtrag_docs}
                        --- ENDE NACHTRAG ---
                        
                        Führe folgende Schritte durch und präsentiere das Ergebnis in einem strukturierten Prüfprotokoll:
                        
                        1.  **Formale Prüfung:** Sind alle VOB/B Fristen (z.B. § 6 Abs. 1 VOB/B) und formalen Anforderungen erfüllt? Ist die Anspruchsgrundlage (z.B. § 2 Abs. 5, § 2 Abs. 6 VOB/B) korrekt benannt und belegt?
                        2.  **Inhaltliche & Technische Plausibilität:** Gibt es eine klare Kausalität zwischen Ursache und Nachtrag? Ist die Leistung technisch notwendig? Sind die Mengen aus den Anlagen plausibel im Vergleich zu den Basis-Dokumenten?
                        3.  **Kalkulatorische Bewertung:** Weichen die Preise von den im LV / Vertrag vereinbarten ab? Welche Positionen sind überhöht? Gibt es ersparte Leistungen oder Mengen?
                        4.  **Konkrete Empfehlung:** Formuliere einen klaren Kürzungsvorschlag oder eine Ablehnung pro Position, mit Angabe des relevanten VOB/B-Paragraphen und einer nachvollziehbaren Begründung.
                        
                        Antworte direkt mit dem Prüfprotokoll. Keine Rückfragen.
                        """
                        
                        audit_result = call_tgacode_ai(audit_prompt)
                        st.session_state.last_audit_result = audit_result
                        st.markdown("### Prüfprotokoll:")
                        st.markdown(audit_result)
            
            if "last_audit_result" in st.session_state:
                st.download_button(
                    label="Prüfprotokoll als PDF exportieren",
                    data=create_pdf_from_text(st.session_state.last_audit_result, st.session_state.selected_projekt),
                    file_name=f"TGAcode_Pruefprotokoll_{st.session_state.selected_projekt}.pdf",
                    mime="application/pdf"
                )
            st.markdown("</div>", unsafe_allow_html=True)
            
        # --- TAB: TGACODE-CHAT ---
        with tab_chat:
            st.markdown("<div class='tgacode-content-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Dialog mit Ihrem TGA-Experten</h3>")
            
            if "chat_messages" not in st.session_state:
                st.session_state.chat_messages = []

            # Display chat messages from history on app rerun
            for message in st.session_state.chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # React to user input
            if prompt := st.chat_input("Ihre Frage an der TGAcode..."):
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("TGAcode denkt nach..."):
                        # Wieder alle Projektdokumente für den Chat-Kontext laden
                        all_chat_docs = ""
                        current_project_path = os.path.join(VAULT_ROOT, st.session_state.selected_firma, st.session_state.selected_projekt)
                        for doc_name in os.listdir(current_project_path):
                            if doc_name.endswith(".pdf"):
                                doc_path = os.path.join(current_project_path, doc_name)
                                try:
                                    reader = PdfReader(doc_path)
                                    doc_text = "".join([page.extract_text() or "" for page in reader.pages])
                                    all_chat_docs += f"\n--- DOKUMENT: {doc_name} ---\n{doc_text[:5000]}\n" # Geringeres Limit für Chat-Fluidität
                                except Exception as e:
                                    st.warning(f"Konnte PDF '{doc_name}' nicht lesen für Chat-Kontext: {e}")
                            elif doc_name.endswith(".txt"):
                                doc_path = os.path.join(current_project_path, doc_name)
                                with open(doc_path, "r", encoding="utf-8") as f:
                                    all_chat_docs += f"\n--- DOKUMENT: {doc_name} ---\n{f.read()[:5000]}\n"


                        chat_response = call_tgacode_ai(prompt, all_chat_docs)
                        st.markdown(chat_response)
                st.session_state.chat_messages.append({"role": "assistant", "content": chat_response})
            st.markdown("</div>", unsafe_allow_html=True)

# --- PDF GENERIERUNGS FUNKTION ---
def create_pdf_from_text(text, project_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=f"TGAcode Prüfprotokoll - Projekt: {project_name}", ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 10)
    # FPDF benötigt oft latin-1 oder cp1252 für Umlaute.
    # Wir müssen den Text entsprechend kodieren.
    try:
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, clean_text)
    except Exception as e:
        st.warning(f"Fehler bei PDF-Kodierung: {e}. Nicht-ASCII Zeichen können fehlen.")
        pdf.multi_cell(0, 5, text.encode('ascii', 'replace').decode('ascii')) # Fallback
        
    pdf_output = pdf.output(dest='S').encode('latin-1') # 'S' gibt als String zurück
    return pdf_output


if __name__ == "__main__":
    main()
