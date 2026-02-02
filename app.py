import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from fpdf import FPDF
import os

# --- 1. CYBER-PUNK INTERFACE CONFIG ---
st.set_page_config(page_title="der TGAcode | AI", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syncopate:wght@400;700&family=Inter:wght@300;500&display=swap');

    /* Globaler Look */
    .main { 
        background: radial-gradient(circle at top right, #0a192f, #020617);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }

    /* Futuristische Glas-Karten */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 242, 254, 0.2);
        border-radius: 20px;
        padding: 25px;
        transition: 0.4s all;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    .glass-card:hover {
        border-color: #00f2fe;
        transform: translateY(-5px);
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.2);
    }

    /* Neon-Titel */
    h1, h2 {
        font-family: 'Syncopate', sans-serif;
        background: linear-gradient(to right, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 4px;
    }

    /* Custom Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(2, 6, 23, 0.9) !important;
        border-right: 1px dashed #00f2fe;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 50px;
        background: transparent;
        border: 1px solid #00f2fe;
        color: #00f2fe;
        padding: 10px 30px;
        text-transform: uppercase;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #00f2fe;
        color: #020617;
        box-shadow: 0 0 30px #00f2fe;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIK: PERSISTENZ ---
DB_PATH = "tga_vault"
if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

# --- 3. DASHBOARD LOGIK ---
def main():
    # Header
    st.markdown("<h1>der TGAcode <span style='font-size:15px; vertical-align:middle;'>v3.0 Neural</span></h1>", unsafe_allow_html=True)
    
    # Sidebar: Firmen- & Projekt-Matrix
    with st.sidebar:
        st.markdown("### PROJECT MATRIX")
        firmen = [f for f in os.listdir(DB_PATH) if os.path.isdir(os.path.join(DB_PATH, f))]
        
        with st.expander("➕ NEUE ENTITÄT ANLEGEN"):
            new_f = st.text_input("Firmenname")
            if st.button("CREATE FIRM"):
                if new_f: os.makedirs(os.path.join(DB_PATH, new_f), exist_ok=True); st.rerun()
        
        sel_f = st.selectbox("FIRMA WÄHLEN", ["--"] + firmen)
        
        sel_p = "--"
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(DB_PATH, sel_f))]
            with st.expander("➕ NEUES PROJEKT"):
                new_p = st.text_input("Projektname")
                if st.button("CREATE PRO"):
                    if new_p: os.makedirs(os.path.join(DB_PATH, sel_f, new_p), exist_ok=True); st.rerun()
            sel_p = st.selectbox("PROJEKT WÄHLEN", ["--"] + projekte)

    # Main Interface
    if sel_p == "--":
        st.markdown("""
            <div class='glass-card' style='text-align:center; margin-top:100px;'>
                <h2 style='color:#00f2fe;'>SYSTEM READY</h2>
                <p>Initialisiere Umgebung... Bitte wähle eine Projekt-Matrix in der Sidebar.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # GRID LAYOUT
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.markdown(f"<div class='glass-card'><h3>DATEN-VAULT</h3>", unsafe_allow_html=True)
            lv_file = st.file_uploader("VERTRAGS-LV HINTERLEGEN", type="pdf")
            if lv_file and st.button("IN VAULT SPEICHERN"):
                text = "".join([p.extract_text() for p in PdfReader(lv_file).pages])
                with open(os.path.join(DB_PATH, sel_f, sel_p, "lv.txt"), "w") as f: f.write(text)
                st.success("DATENSATZ GESICHERT")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<br><div class='glass-card'><h3>OBJEKTÜBERWACHUNG</h3>", unsafe_allow_html=True)
            mode = st.radio("MODUS", ["Mängel-Scanner", "Bautagebuch", "Abnahme-Check"])
            note = st.text_area("LOG-EINTRAG")
            if st.button("LOG COMMIT"):
                st.toast("Eintrag in Projekt-Timeline gespeichert.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='glass-card'><h3>NEURAL CHAT & REVISION</h3>", unsafe_allow_html=True)
            
            # KI Initialisierung (aus Secrets)
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                # CHAT INTERFACE
                if "messages" not in st.session_state: st.session_state.messages = []
                
                for m in st.session_state.messages:
                    with st.chat_message(m["role"]): st.markdown(m["content"])
                
                if prompt := st.chat_input("Was ist der Plan für heute?"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)
                    
                    # Kontext laden
                    lv_context = ""
                    lv_path = os.path.join(DB_PATH, sel_f, sel_p, "lv.txt")
                    if os.path.exists(lv_path):
                        with open(lv_path, "r") as f: lv_context = f.read()[:8000]

                    with st.chat_message("assistant"):
                        full_prompt = f"Du bist das TGAcode Neural Interface. Firma: {sel_f}, Projekt: {sel_p}. LV-Kontext: {lv_context}. Handle wie ein erfahrener Ingenieur. Aufgabe: {prompt}"
                        res = model.generate_content(full_prompt)
                        st.markdown(res.text)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
            
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
