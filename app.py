import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. TGAcode BRANDING & DESIGN SYSTEM ---
st.set_page_config(page_title="TGAcode | Digital Engineering", layout="wide")

# Custom CSS für den Look von tgacode.com
st.markdown("""
    <style>
    /* White & Clean Design mit TGA-Akzenten */
    :root {
        --primary: #00f2fe;
        --dark: #1a1c24;
        --bg: #f8fafc;
    }
    .main { background-color: var(--bg); color: var(--dark); }
    
    /* Header & Navigation */
    .stHeader { background-color: white; border-bottom: 1px solid #e2e8f0; }
    
    /* Professionelle Cards */
    .tgacode-card {
        background: white;
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Typography */
    h1, h2, h3 { color: var(--dark); font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 700; }
    .brand-text { color: var(--primary); font-weight: 900; letter-spacing: -1px; }

    /* Buttons */
    .stButton>button {
        background-color: var(--dark);
        color: white;
        border-radius: 6px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: var(--primary);
        color: var(--dark);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--dark);
        color: white;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p { color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STORAGE ENGINE ---
DB_PATH = "tgacode_vault"
if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

def main():
    # Top Bar
    col_logo, col_status = st.columns([1, 4])
    with col_logo:
        st.markdown("<h1 style='margin-top:-10px;'>TGA<span class='brand-text'>code</span></h1>", unsafe_allow_html=True)
    
    # --- SIDEBAR: PROJECT NAVIGATOR ---
    with st.sidebar:
        st.markdown("### PROJEKT-VERWALTUNG")
        firmen = [f for f in os.listdir(DB_PATH) if os.path.isdir(os.path.join(DB_PATH, f))]
        
        with st.expander("🏢 NEUE FIRMA / MANDANT"):
            nf = st.text_input("Firmenname")
            if st.button("HINZUFÜGEN"):
                if nf: os.makedirs(os.path.join(DB_PATH, nf), exist_ok=True); st.rerun()
        
        sel_f = st.selectbox("FIRMA", ["--"] + firmen)
        
        sel_p = "--"
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(DB_PATH, sel_f))]
            with st.expander("📂 NEUES PROJEKT"):
                np = st.text_input("Projektbezeichnung")
                if st.button("PROJEKT ANLEGEN"):
                    if np: os.makedirs(os.path.join(DB_PATH, sel_f, np), exist_ok=True); st.rerun()
            sel_p = st.selectbox("PROJEKT", ["--"] + projekte)

    # --- MAIN INTERFACE ---
    if sel_p == "--":
        st.markdown("""
            <div style='text-align:center; padding: 100px;'>
                <h2 style='opacity:0.3;'>WÄHLEN SIE EIN PROJEKT AUS DER MATRIX</h2>
                <p style='opacity:0.5;'>TGAcode - Digitales Controlling & Objektüberwachung</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"## {sel_p} <small style='color:gray;'>| {sel_f}</small>", unsafe_allow_html=True)
        
        tab_rev, tab_chat, tab_config = st.tabs(["📊 NACHTRAGSPRÜFUNG", "💬 PROJEKT-CHAT", "⚙️ ARCHIV"])

        # --- TAB: ARCHIV (BASIS DATEN) ---
        with tab_config:
            st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
            st.subheader("Vertragsgrundlagen (Vault)")
            lv_up = st.file_uploader("Basis-LV hochladen (Dauerhaft)", type="pdf", key="vault_lv")
            if lv_up and st.button("IM VAULT SICHERN"):
                text = "".join([p.extract_text() for p in PdfReader(lv_up).pages])
                with open(os.path.join(DB_PATH, sel_f, sel_p, "lv_base.txt"), "w", encoding="utf-8") as f:
                    f.write(text)
                st.success("LV erfolgreich im Projekt-Vault archiviert.")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- TAB: REVISION (DAS KERNGESCHÄFT) ---
        with tab_rev:
            col_in, col_out = st.columns([1, 1.5])
            
            with col_in:
                st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
                st.subheader("Nachtrags-Upload")
                nt_file = st.file_uploader("Aktuellen Nachtrag prüfen (PDF)", type="pdf", key="nt_upload")
                mode = st.selectbox("Prüf-Tiefe", ["VOB/B Standard", "VOB/B Streng (Kürzung)", "Nur Plausibilität"])
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_out:
                st.markdown("<div class='tgacode-card' style='min-height:400px;'>", unsafe_allow_html=True)
                st.subheader("Prüfprotokoll")
                
                if nt_file and st.button("🚀 PRÜFUNG STARTEN"):
                    # KI Logik
                    api_key = st.secrets.get("GEMINI_API_KEY")
                    if api_key:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        
                        # Kontext aus Vault laden
                        lv_p = os.path.join(DB_PATH, sel_f, sel_p, "lv_base.txt")
                        lv_c = open(lv_p, "r", encoding="utf-8").read() if os.path.exists(lv_p) else "Kein LV."
                        nt_c = "".join([p.extract_text() for p in PdfReader(nt_file).pages])
                        
                        prompt = f"""
                        Du bist der digitale TGAcode Experte für Objektüberwachung.
                        AUFGABE: Prüfe den Nachtrag basierend auf dem LV.
                        MODUS: {mode}
                        
                        BASIS-LV: {lv_c[:8000]}
                        NACHTRAG: {nt_c[:8000]}
                        
                        ERGEBNIS: Erstelle eine Tabelle mit Pos, Status, Begründung (VOB) und Kürzungsvorschlag.
                        """
                        res = model.generate_content(prompt)
                        st.markdown(res.text)
                        st.session_state.current_audit = res.text
                    else:
                        st.warning("Bitte API-Key in den Secrets hinterlegen.")
                else:
                    st.info("Warten auf Nachtrags-Dokument...")
                st.markdown("</div>", unsafe_allow_html=True)

        # --- TAB: CHAT (LERNENDES SYSTEM) ---
        with tab_chat:
            st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
            if "messages" not in st.session_state: st.session_state.messages = []
            
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.markdown(m["content"])
                
            if chat_in := st.chat_input("Fragen zum Projekt oder zum Nachtrag?"):
                st.session_state.messages.append({"role": "user", "content": chat_in})
                # Hier würde die KI-Antwort-Logik mit Kontext stehen (ähnlich wie oben)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
