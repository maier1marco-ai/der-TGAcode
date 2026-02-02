import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. CYBER-PUNK INTERFACE CONFIG ---
st.set_page_config(page_title="der TGAcode | AI", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syncopate:wght@400;700&family=Inter:wght@300;500&display=swap');
    .main { background: radial-gradient(circle at top right, #0a192f, #020617); color: #e2e8f0; font-family: 'Inter', sans-serif; }
    .glass-card { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); border: 1px solid rgba(0, 242, 254, 0.2); border-radius: 20px; padding: 25px; transition: 0.4s all; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8); }
    h1, h2 { font-family: 'Syncopate', sans-serif; background: linear-gradient(to right, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 4px; }
    [data-testid="stSidebar"] { background-color: rgba(2, 6, 23, 0.9) !important; border-right: 1px dashed #00f2fe; }
    .stButton>button { border-radius: 50px; background: transparent; border: 1px solid #00f2fe; color: #00f2fe; padding: 10px 30px; text-transform: uppercase; font-weight: bold; width: 100%; }
    .stButton>button:hover { background: #00f2fe; color: #020617; box-shadow: 0 0 30px #00f2fe; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIK: PERSISTENZ ---
DB_PATH = "tga_vault"
if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

def main():
    st.markdown("<h1>der TGAcode <span style='font-size:15px;'>v3.1 Neural</span></h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### PROJECT MATRIX")
        firmen = [f for f in os.listdir(DB_PATH) if os.path.isdir(os.path.join(DB_PATH, f))]
        new_f = st.text_input("Firmenname")
        if st.button("CREATE FIRM"):
            if new_f: os.makedirs(os.path.join(DB_PATH, new_f), exist_ok=True); st.rerun()
        sel_f = st.selectbox("FIRMA WÄHLEN", ["--"] + firmen)
        
        sel_p = "--"
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(DB_PATH, sel_f))]
            new_p = st.text_input("Projektname")
            if st.button("CREATE PRO"):
                if new_p: os.makedirs(os.path.join(DB_PATH, sel_f, new_p), exist_ok=True); st.rerun()
            sel_p = st.selectbox("PROJEKT WÄHLEN", ["--"] + projekte)

    if sel_p == "--":
        st.markdown("<div class='glass-card' style='text-align:center; margin-top:100px;'><h2>SYSTEM READY</h2><p>Bitte Projekt-Matrix wählen.</p></div>", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.markdown("<div class='glass-card'><h3>DATEN-VAULT</h3>", unsafe_allow_html=True)
            lv_file = st.file_uploader("VERTRAGS-LV HINTERLEGEN", type="pdf")
            if lv_file and st.button("IN VAULT SPEICHERN"):
                text = "".join([p.extract_text() for p in PdfReader(lv_file).pages])
                with open(os.path.join(DB_PATH, sel_f, sel_p, "lv.txt"), "w", encoding="utf-8") as f: f.write(text)
                st.success("GESICHERT")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='glass-card'><h3>NEURAL CHAT</h3>", unsafe_allow_html=True)
            
            # --- DER FIX GEGEN "NOT FOUND" ---
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                
                # Dynamische Modell-Suche
                try:
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    # Suche nach dem besten verfügbaren Modell
                    if 'models/gemini-1.5-flash' in available_models:
                        model_id = 'models/gemini-1.5-flash'
                    elif 'models/gemini-1.5-flash-latest' in available_models:
                        model_id = 'models/gemini-1.5-flash-latest'
                    else:
                        model_id = available_models[0] # Notfall: Nimm das erste funktionierende
                    
                    model = genai.GenerativeModel(model_id)
                    st.caption(f"Verbunden via: {model_id}")
                except Exception as e:
                    st.error(f"Konnektivitäts-Fehler: {e}")
                    st.stop()
                
                if "messages" not in st.session_state: st.session_state.messages = []
                for m in st.session_state.messages:
                    with st.chat_message(m["role"]): st.markdown(m["content"])
                
                if prompt := st.chat_input("Was ist der Plan?"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)
                    
                    lv_path = os.path.join(DB_PATH, sel_f, sel_p, "lv.txt")
                    lv_context = open(lv_path, "r", encoding="utf-8").read()[:8000] if os.path.exists(lv_path) else "Kein LV."

                    with st.chat_message("assistant"):
                        # Der "Profi-Modus" Instruktions-Satz
                        full_prompt = f"System: Du bist 'der TGAcode', ein Senior-Experte für Objektüberwachung und Nachtragsmanagement. Sei präzise, fachlich brillant und hilf dem Nutzer proaktiv. Projekt: {sel_p}. Kontext: {lv_context}. Frage: {prompt}"
                        try:
                            res = model.generate_content(full_prompt)
                            st.markdown(res.text)
                            st.session_state.messages.append({"role": "assistant", "content": res.text})
                        except Exception as e:
                            st.error(f"KI Fehler beim Generieren: {e}")
            
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
