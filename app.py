import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. DESIGN SYSTEM (der TGAcode Style) ---
st.set_page_config(page_title="der TGAcode", layout="wide")

st.markdown("""
    <style>
    /* Top Navigation Style */
    .top-nav {
        background-color: #1a1c24;
        padding: 15px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        border-bottom: 3px solid #00f2fe;
        margin-bottom: 30px;
    }
    .main { background-color: #ffffff; }
    
    /* Buttons & Inputs */
    .stButton>button {
        background: #1a1c24; color: #00f2fe; border: 1px solid #00f2fe;
        border-radius: 4px; padding: 10px 20px; font-weight: bold;
    }
    .stButton>button:hover { background: #00f2fe; color: #1a1c24; }
    
    /* Verstecke die Standard Sidebar */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stHeader"] { display: none; }
    
    /* Karten-Design */
    .content-card {
        border: 1px solid #e2e8f0; padding: 25px; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); background: white;
    }
    </style>
    
    <div class="top-nav">
        <div style="font-size: 24px; font-weight: 800;">der <span style="color:#00f2fe;">TGAcode</span></div>
        <div style="font-size: 14px; opacity: 0.7;">DIGITAL ENGINEERING & OBJEKTÜBERWACHUNG</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. DATEN-STRUKTUR ---
VAULT = "vault_tgacode"
if not os.path.exists(VAULT): os.makedirs(VAULT)

def main():
    # --- PROJEKT SELEKTOR & ERSTELLUNG (Kreative Kacheln) ---
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.subheader("Firma")
        firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
        sel_f = st.selectbox("Wähle eine Firma", ["--"] + firmen, label_visibility="collapsed")
        
        with st.expander("➕ Neue Firma erstellen"):
            neue_f = st.text_input("Firmenname")
            if st.button("Firma anlegen"):
                if neue_f: os.makedirs(os.path.join(VAULT, neue_f)); st.rerun()

    with col2:
        st.subheader("Projekt")
        sel_p = "--"
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
            sel_p = st.selectbox("Wähle ein Projekt", ["--"] + projekte, label_visibility="collapsed")
            
            with st.expander("➕ Neues Projekt erstellen"):
                neues_p = st.text_input("Projektname")
                if st.button("Projekt anlegen"):
                    if neues_p: os.makedirs(os.path.join(VAULT, sel_f, neues_p)); st.rerun()
        else:
            st.info("Wähle zuerst eine Firma")

    with col3:
        st.subheader("Status")
        if sel_p != "--":
            st.success(f"Aktiv: {sel_p}")
        else:
            st.warning("Kein Projekt geladen")

    st.divider()

    if sel_p != "--":
        # --- HAUPTBEREICH NACH SELEKTION ---
        t1, t2, t3 = st.tabs(["📄 Projekt-Akte", "🚀 Nachtragsprüfung", "💬 der TGAcode Chat"])
        
        path_p = os.path.join(VAULT, sel_f, sel_p)

        with t1:
            st.markdown("<div class='content-card'>", unsafe_allow_html=True)
            st.markdown("### Dokumente für dieses Projekt")
            uploaded = st.file_uploader("LV, Vertrag, Pläne hochladen (Multi)", accept_multiple_files=True, type="pdf")
            if st.button("Dokumente speichern"):
                for f in uploaded:
                    with open(os.path.join(path_p, f.name), "wb") as file:
                        file.write(f.getbuffer())
                st.success("Dokumente archiviert.")
            
            st.write("**Vorhandene Dateien:**")
            for f in os.listdir(path_p): st.write(f"• {f}")
            st.markdown("</div>", unsafe_allow_html=True)

        with t2:
            st.markdown("<div class='content-card'>", unsafe_allow_html=True)
            st.markdown("### Nachtrag prüfen")
            nt_files = st.file_uploader("Nachtrag + Anlagen hochladen", accept_multiple_files=True, type="pdf")
            if st.button("VOB-Prüfung starten"):
                # Hier greift die KI auf den gesamten Ordner path_p zu
                st.info("Analysiere Nachtrag gegen Basis-Dokumente...")
            st.markdown("</div>", unsafe_allow_html=True)

        with t3:
            st.markdown("<div class='content-card'>", unsafe_allow_html=True)
            st.markdown("### Chat mit der TGAcode KI")
            # Chat Logik hier...
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
