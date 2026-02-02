import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from fpdf import FPDF
import os
import json
from datetime import datetime

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="der TGAcode | OS", layout="wide", initial_sidebar_state="expanded")

# Futuristisches UI-Update
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .main { background-color: #050a0f; color: #e0e0e0; }
    .stSidebar { background-color: #0a1118 !important; border-right: 1px solid #00f2fe; }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; color: #00f2fe; text-transform: uppercase; }
    .stButton>button { 
        background: linear-gradient(90deg, #00f2fe, #4facfe); 
        color: black; border-radius: 5px; border: none; font-weight: bold;
        transition: 0.5s; box-shadow: 0 0 10px #00f2fe;
    }
    .stButton>button:hover { box-shadow: 0 0 25px #00f2fe; transform: translateY(-2px); }
    .project-card { 
        background: rgba(0, 242, 254, 0.05); border-left: 5px solid #00f2fe;
        padding: 15px; margin-bottom: 10px; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATENSPEICHER LOGIK ---
DB_ROOT = "tgacode_db"
if not os.path.exists(DB_ROOT):
    os.makedirs(DB_ROOT)

def save_project_data(firma, projekt, content, filename):
    path = os.path.join(DB_ROOT, firma, projekt)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, filename), "w", encoding="utf-8") as f:
        f.write(content)

def load_project_data(firma, projekt, filename):
    path = os.path.join(DB_ROOT, firma, projekt, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# --- 3. AUTH & KI SETUP ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<center><h1 style='font-size: 60px;'>der TGAcode</h1></center>", unsafe_allow_html=True)
    pw = st.text_input("Enter Access Key", type="password")
    if st.button("UNLOCK SYSTEM"):
        if pw == "TGAPRO": 
            st.session_state.auth = True
            st.rerun()
    st.stop()

# KI Initialisierung
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    st.error("API Key missing in Secrets!")
    st.stop()

# --- 4. SIDEBAR: PROJEKT-VERWALTUNG ---
st.sidebar.title("🏢 Projekt-Center")
firmen_liste = [f for f in os.listdir(DB_ROOT) if os.path.isdir(os.path.join(DB_ROOT, f))]
neue_firma = st.sidebar.text_input("+ Neue Firma")
if st.sidebar.button("Firma anlegen"):
    if neue_firma: os.makedirs(os.path.join(DB_ROOT, neue_firma), exist_ok=True); st.rerun()

auswahl_firma = st.sidebar.selectbox("Firma wählen", ["Bitte wählen"] + firmen_liste)

auswahl_projekt = "Bitte wählen"
if auswahl_firma != "Bitte wählen":
    projekte = os.listdir(os.path.join(DB_ROOT, auswahl_firma))
    neues_pro = st.sidebar.text_input("+ Neues Projekt")
    if st.sidebar.button("Projekt anlegen"):
        if neues_pro: os.makedirs(os.path.join(DB_ROOT, auswahl_firma, neues_pro), exist_ok=True); st.rerun()
    auswahl_projekt = st.sidebar.selectbox("Projekt wählen", ["Bitte wählen"] + projekte)

# --- 5. HAUPTBEREICH ---
if auswahl_projekt != "Bitte wählen":
    st.title(f"{auswahl_projekt} // {auswahl_firma}")
    
    tabs = st.tabs(["🚀 Dashboard", "📊 Revision", "🏗️ Objektüberwachung", "💬 Universal Chat"])

    # --- TAB 1: DASHBOARD (SPEICHERN) ---
    with tabs[0]:
        st.subheader("Projekt-Datenbank")
        lv_upload = st.file_uploader("Vertrags-LV hochladen (Dauerhaft)", type="pdf")
        if lv_upload and st.button("In Datenbank archivieren"):
            text = "".join([p.extract_text() for p in PdfReader(lv_upload).pages])
            save_project_data(auswahl_firma, auswahl_projekt, text, "lv_basis.txt")
            st.success("LV dauerhaft gespeichert.")
        
        saved_lv = load_project_data(auswahl_firma, auswahl_projekt, "lv_basis.txt")
        if saved_lv:
            st.info("✅ Vertrags-LV ist im System hinterlegt.")

    # --- TAB 3: OBJEKTÜBERWACHUNG ---
    with tabs[2]:
        st.subheader("Abnahme & Begehung")
        gewerk = st.selectbox("Gewerk", ["Heizung", "Lüftung", "Sanitär", "Elektro"])
        mangel = st.text_area("Mangelbeschreibung / Notiz")
        if st.button("Mangel erfassen"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            old_log = load_project_data(auswahl_firma, auswahl_projekt, "mangel_log.txt") or ""
            new_log = old_log + f"\n[{timestamp}] {gewerk}: {mangel}"
            save_project_data(auswahl_firma, auswahl_projekt, new_log, "mangel_log.txt")
            st.success("Notiz gespeichert.")
        
        st.text_area("Protokoll-Historie", load_project_data(auswahl_firma, auswahl_projekt, "mangel_log.txt") or "Keine Einträge", height=200)

    # --- TAB 4: UNIVERSAL CHAT (DAS HERZSTÜCK) ---
    with tabs[3]:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # System-Prompt für "echte" Persönlichkeit
        system_logic = f"""
        Du bist 'der TGAcode', ein Elite-KI-Experte für TGA, VOB und Objektüberwachung. 
        Du bist locker, aber extrem kompetent. Du hilfst bei Nachträgen, Abnahmen und Schriftverkehr.
        Kontext: Firma {auswahl_firma}, Projekt {auswahl_projekt}.
        LV-Wissen: {saved_lv[:5000] if saved_lv else 'Noch kein LV hochgeladen.'}
        """

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        prompt = st.chat_input("Lass uns über das Projekt sprechen...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                full_prompt = f"{system_logic}\n\nUser fragt: {prompt}"
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                
                # Check für PDF-Erstellungswunsch
                if "pdf" in prompt.lower() or "protokoll" in prompt.lower():
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt="der TGAcode - Projektprotokoll", ln=1, align='C')
                    pdf.ln(10)
                    pdf.multi_cell(0, 10, txt=response.text.encode('latin-1', 'replace').decode('latin-1'))
                    pdf_path = "bericht.pdf"
                    pdf.output(pdf_path)
                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 Generiertes PDF herunterladen", f, file_name=f"TGAcode_{auswahl_projekt}.pdf")

            st.session_state.chat_history.append({"role": "assistant", "content": response.text})

else:
    st.title("Willkommen beim TGAcode")
    st.info("Bitte wähle links eine Firma und ein Projekt aus oder lege neue an.")
