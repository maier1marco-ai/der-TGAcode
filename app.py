import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. DESIGN: der TGAcode (Clean & Website-Stil) ---
st.set_page_config(page_title="der TGAcode", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    /* Top Navigation */
    .top-nav {
        background-color: #1a1c24;
        padding: 20px 40px;
        color: white;
        border-bottom: 4px solid #00f2fe;
        margin-bottom: 30px;
    }
    .logo { font-size: 26px; font-weight: 800; }
    .accent { color: #00f2fe; }
    
    /* Buttons */
    .stButton>button {
        background: #1a1c24; color: #00f2fe; border: 1px solid #00f2fe;
        border-radius: 4px; padding: 10px 20px; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background: #00f2fe; color: #1a1c24; }
    
    /* Content Bereich */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f8fafc; border-radius: 4px 4px 0 0; padding: 10px 20px; 
    }
    </style>
    
    <div class="top-nav">
        <div class="logo">der <span class="accent">TGAcode</span></div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. DATENBANK (Ordnerstruktur) ---
VAULT = "vault_tgacode"
if not os.path.exists(VAULT): os.makedirs(VAULT)

def main():
    # --- AUSWAHL: Firma & Projekt ---
    st.markdown("### Projekt-Auswahl")
    c1, c2, c3 = st.columns(3)
    
    # FIRMA
    firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
    with c1:
        sel_f = st.selectbox("Firma", ["--"] + firmen)
        with st.expander("Firma erstellen"):
            nf = st.text_input("Name der Firma")
            if st.button("Firma anlegen"):
                if nf: os.makedirs(os.path.join(VAULT, nf)); st.rerun()

    # PROJEKT
    sel_p = "--"
    if sel_f != "--":
        projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        with c2:
            sel_p = st.selectbox("Projekt", ["--"] + projekte)
            with st.expander("Projekt erstellen"):
                np = st.text_input("Name des Projekts")
                if st.button("Projekt anlegen"):
                    if np: os.makedirs(os.path.join(VAULT, sel_f, np)); st.rerun()
    else:
        with c2: st.info("Bitte zuerst Firma wählen")

    # STATUS
    with c3:
        if sel_p != "--": st.success(f"Aktiv: {sel_p}")
        else: st.warning("Kein Projekt gewählt")

    st.divider()

    if sel_p != "--":
        # --- ARBEITSBEREICH ---
        path_p = os.path.join(VAULT, sel_f, sel_p)
        t1, t2, t3 = st.tabs(["📁 Projekt-Akte", "🚀 Prüfung", "💬 Chat"])

        with t1:
            st.markdown("#### Dokumente (LV, Vertrag, Pläne)")
            up = st.file_uploader("PDFs hochladen", accept_multiple_files=True)
            if st.button("Speichern"):
                for f in up:
                    with open(os.path.join(path_p, f.name), "wb") as file: file.write(f.getbuffer())
                st.rerun()
            
            st.write("**In der Projekt-Akte:**")
            for d in os.listdir(path_p):
                col_d, col_x = st.columns([0.9, 0.1])
                col_d.code(d)
                if col_x.button("Löschen", key=d):
                    os.remove(os.path.join(path_p, d))
                    st.rerun()

        with t2:
            st.markdown("#### Nachtragsprüfung")
            nt_up = st.file_uploader("Nachtrag + Anlagen hochladen", accept_multiple_files=True)
            if st.button("Prüfung starten"):
                # KI Logik hier... (Greift auf alle Dateien in path_p zu)
                st.info("Prüfung wird durchgeführt...")

        with t3:
            st.markdown("#### Chat mit der TGAcode KI")
            # Chat Logik hier...
            st.chat_input("Anweisung an der TGAcode...")

if __name__ == "__main__":
    main()s
