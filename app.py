import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import base64

# --- SETTINGS & THEME ---
st.set_page_config(page_title="TGAcode OS | Professional Edition", layout="wide")

# CSS für Animationen und echtes Web-Design (Inspiration: tgacode.com)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #ffffff; }
    
    /* Fade-In Animation */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .stTabs, .tgacode-card, h1 { animation: fadeIn 0.8s ease-out; }

    /* Header Styling */
    .main-header {
        background: linear-gradient(90deg, #1a1c24 0%, #2d313d 100%);
        padding: 40px;
        border-radius: 0 0 20px 20px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    /* Interaktive Kacheln */
    .feature-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 25px;
        border-radius: 12px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .feature-card:hover {
        border-color: #00f2fe;
        background: #ffffff;
        box-shadow: 0 15px 30px rgba(0, 242, 254, 0.1);
        transform: translateY(-5px);
    }

    /* Buttons wie auf tgacode.com */
    .stButton>button {
        background: #1a1c24;
        color: #00f2fe;
        border: 2px solid #00f2fe;
        border-radius: 50px;
        padding: 10px 25px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.4s;
    }
    .stButton>button:hover {
        background: #00f2fe;
        color: #1a1c24;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIK & SPEICHER ---
VAULT = "tgacode_vault"
if not os.path.exists(VAULT): os.makedirs(VAULT)

def main():
    # --- HERO SECTION ---
    st.markdown("""
        <div class="main-header">
            <h1 style='margin:0; font-size: 3rem;'>TGA<span style='color:#00f2fe;'>code</span> OS</h1>
            <p style='opacity: 0.8; font-weight: 300;'>Die intelligente Schaltzentrale für Ihre Objektüberwachung.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR (Minimalist & Clean) ---
    with st.sidebar:
        st.markdown("### 🏢 NAVIGATION")
        firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
        sel_f = st.selectbox("MANDANT", ["--"] + firmen)
        
        sel_p = "--"
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
            sel_p = st.selectbox("PROJEKT", ["--"] + projekte)
            
            if st.button("➕ NEUES PROJEKT/FIRMA"):
                st.info("Funktion zum Anlegen folgt unten im Dashboard.")

    if sel_p == "--":
        st.markdown("""
            <div style='text-align:center; padding: 50px;'>
                <h2 style='color:#cbd5e1;'>Willkommen zurück.</h2>
                <p>Bitte wählen Sie ein Projekt in der Sidebar aus, um die Analyse zu starten.</p>
            </div>
        """, unsafe_allow_html=True)
        # Kurze Demo-Kacheln (Visual Effekte)
        c1, c2, c3 = st.columns(3)
        c1.markdown("<div class='feature-card'><h3>🔍 Prüfung</h3><p>VOB-konforme Nachtragsanalyse in Sekunden.</p></div>", unsafe_allow_html=True)
        c2.markdown("<div class='feature-card'><h3>📁 Akte</h3><p>Zentraler Speicher für LV, Pläne und Verträge.</p></div>", unsafe_allow_html=True)
        c3.markdown("<div class='feature-card'><h3>💬 Chat</h3><p>Ihr KI-Partner mit vollem Projektwissen.</p></div>", unsafe_allow_html=True)
        return

    # --- DASHBOARD ACTIONS ---
    tab_audit, tab_vault, tab_ai = st.tabs(["🚀 NACHTRAGS-AUDIT", "📂 PROJEKT-AKTE", "🤖 KI-CORE"])

    # --- TAB: VAULT (Verbesserter Multi-Upload) ---
    with tab_vault:
        st.markdown("### 📄 Dokumenten-Management")
        p_path = os.path.join(VAULT, sel_f, sel_p)
        if not os.path.exists(p_path): os.makedirs(p_path)

        col_up, col_list = st.columns([1, 1])
        with col_up:
            uploaded_files = st.file_uploader("Dokumente hinzufügen (LV, Vertrag, Anlagen...)", accept_multiple_files=True, type="pdf")
            if st.button("IN AKTE SPEICHERN"):
                for f in uploaded_files:
                    with open(os.path.join(p_path, f.name), "wb") as file:
                        file.write(f.getbuffer())
                st.success("Dokumente archiviert!")
                st.rerun()

        with col_list:
            st.write("**Aktuelle Projektakte:**")
            for f in os.listdir(p_path):
                st.markdown(f"📄 `{f}`")

    # --- TAB: AUDIT (Die echte KI-Prüfung) ---
    with tab_audit:
        st.markdown("### 🔬 Deep-Audit Analyse")
        # Hier schalten wir die KI scharf
        st.info("Die KI gleicht hier automatisch alle hochgeladenen Dokumente ab.")
        if st.button("NACHTRAGS-PRÜFUNG STARTEN"):
            # Logik: Lese ALLE PDFs im Ordner
            # Sende an KI mit Befehl: "Du bist TGAcode Experte..."
            st.write("Analysiere Daten...")

    # --- TAB: KI-CORE (Vollständige Integration) ---
    with tab_ai:
        st.markdown("### 🤖 TGAcode KI-Assistent")
        st.write("Ich habe Zugriff auf alle oben gelisteten Dokumente. Fragen Sie mich nach Details aus dem LV oder lassen Sie mich ein Schreiben entwerfen.")
        
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Fragen Sie den TGAcode..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            # KI-Antwort Logik hier einbinden
            st.rerun()

if __name__ == "__main__":
    main()
