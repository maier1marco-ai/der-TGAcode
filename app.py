import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. TGAcode BRANDING & UI (Inspired by tgacode.com) ---
st.set_page_config(page_title="TGAcode | Digital Engineering", layout="wide")

st.markdown("""
    <style>
    :root {
        --primary: #00f2fe;
        --dark: #1a1c24;
        --bg: #fdfdfd;
        --text: #334155;
    }
    .main { background-color: var(--bg); color: var(--text); }
    
    /* Clean Cards wie auf der Website */
    .tgacode-card {
        background: white;
        padding: 35px;
        border-radius: 4px; /* Eckiger, professioneller Look */
        border: 1px solid #edf2f7;
        box-shadow: 0 10px 25px rgba(0,0,0,0.02);
        margin-bottom: 25px;
    }
    
    /* Typografie */
    h1, h2, h3 { color: var(--dark); font-family: 'Inter', sans-serif; font-weight: 800; text-transform: none; letter-spacing: -0.5px; }
    .brand-accent { color: var(--primary); }

    /* Buttons Schwarz/Cyan */
    .stButton>button {
        background-color: var(--dark);
        color: white;
        border-radius: 2px;
        border: none;
        padding: 15px 30px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: var(--primary); color: var(--dark); border: none; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STORAGE SYSTEM ---
DB_PATH = "tgacode_vault"
if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

# --- 3. AUTO-REPAIR MODEL SELECTOR ---
def get_working_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        # Fragt Google direkt: "Was darf dieser Key nutzen?"
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Bevorzugte Reihenfolge
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'gemini-1.5-flash']:
            if target in available: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except: return None

def main():
    # Logo Header
    st.markdown("<h1>TGA<span class='brand-accent'>code</span> <span style='font-size:12px; font-weight:300; color:gray;'>BETA 4.0</span></h1>", unsafe_allow_html=True)
    
    # --- SIDEBAR NAVI ---
    with st.sidebar:
        st.markdown("### 🏢 MANDANTEN & PROJEKTE")
        firmen = [f for f in os.listdir(DB_PATH) if os.path.isdir(os.path.join(DB_PATH, f))]
        
        with st.expander("✨ NEUE FIRMA"):
            nf = st.text_input("Name")
            if st.button("ANLEGEN"):
                if nf: os.makedirs(os.path.join(DB_PATH, nf), exist_ok=True); st.rerun()
        
        sel_f = st.selectbox("FIRMA WÄHLEN", ["--"] + firmen)
        
        sel_p = "--"
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(DB_PATH, sel_f))]
            with st.expander("📂 NEUES PROJEKT"):
                np = st.text_input("Bezeichnung")
                if st.button("ERSTELLEN"):
                    if np: os.makedirs(os.path.join(DB_PATH, sel_f, np), exist_ok=True); st.rerun()
            sel_p = st.selectbox("PROJEKT WÄHLEN", ["--"] + projekte)

    # --- DASHBOARD ---
    if sel_p == "--":
        st.info("Bitte wählen Sie links ein Projekt aus, um das TGAcode Interface zu starten.")
    else:
        st.subheader(f"Dashboard: {sel_p}")
        tab1, tab2, tab3 = st.tabs(["🚀 NACHTRAGSPRÜFUNG", "📁 PROJEKT-ARCHIV", "💬 EXPERTEN-CHAT"])

        # KONTEXT LADEN
        lv_path = os.path.join(DB_PATH, sel_f, sel_p, "lv_base.txt")
        lv_exists = os.path.exists(lv_path)

        with tab2:
            st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
            st.markdown("### VERTRAGS-LV (BASIS)")
            up = st.file_uploader("LV PDF hochladen (Einmalig)", type="pdf")
            if up and st.button("IM VAULT SPEICHERN"):
                txt = "".join([p.extract_text() for p in PdfReader(up).pages])
                with open(lv_path, "w", encoding="utf-8") as f: f.write(txt)
                st.success("LV im Archiv gesichert.")
                st.rerun()
            if lv_exists: st.write("✅ LV-Datenbank ist bereit.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab1:
            st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
            st.markdown("### NEUEN NACHTRAG PRÜFEN")
            nt_up = st.file_uploader("Nachtrag PDF hochladen", type="pdf")
            
            if nt_up:
                if st.button("ZUR PRÜFUNG EINREICHEN"):
                    model = get_working_model()
                    if model:
                        with st.spinner("TGAcode prüft nach VOB/B..."):
                            lv_content = open(lv_path, "r", encoding="utf-8").read() if lv_exists else "Kein LV."
                            nt_content = "".join([p.extract_text() for p in PdfReader(nt_up).pages])
                            
                            prompt = f"""
                            Du bist der TGAcode KI-Agent für Objektüberwachung. 
                            PRÜFE DIESEN NACHTRAG GEGEN DAS LV.
                            BASIS-LV: {lv_content[:8000]}
                            NACHTRAG: {nt_content[:8000]}
                            ERGEBNIS: Liste alle Unstimmigkeiten, VOB-Paragraphen und konkrete Kürzungsvorschläge auf.
                            """
                            try:
                                res = model.generate_content(prompt)
                                st.session_state.audit_result = res.text
                            except Exception as e:
                                st.error(f"Fehler: {e}")
                    else: st.error("API Verbindung fehlgeschlagen.")

            if "audit_result" in st.session_state:
                st.divider()
                st.markdown(st.session_state.audit_result)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
            st.markdown("### TGA-EXPERTEN CHAT")
            if "chat_history" not in st.session_state: st.session_state.chat_history = []
            
            for m in st.session_state.chat_history:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
            if c_in := st.chat_input("Fragen Sie etwas zum Projekt..."):
                st.session_state.chat_history.append({"role": "user", "content": c_in})
                model = get_working_model()
                res = model.generate_content(f"Projekt-Experte: {c_in}")
                st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
