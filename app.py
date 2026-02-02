import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. BRANDING (tgacode.com Style) ---
st.set_page_config(page_title="TGAcode Enterprise", layout="wide")
st.markdown("""
    <style>
    :root { --primary: #00f2fe; --dark: #1a1c24; }
    .main { background-color: #fcfcfc; color: #1a1c24; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: 600; font-size: 16px; }
    .tgacode-card { background: white; padding: 25px; border-radius: 4px; border: 1px solid #eee; margin-bottom: 20px; }
    h1, h2 { font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STORAGE CORE (Verzeichnis-Struktur) ---
VAULT_DIR = "tgacode_vault"
if not os.path.exists(VAULT_DIR): os.makedirs(VAULT_DIR)

def get_project_path(firma, projekt, sub):
    path = os.path.join(VAULT_DIR, firma, projekt, sub)
    if not os.path.exists(path): os.makedirs(path)
    return path

# --- 3. KI LOGIK (Auto-Repair) ---
def call_tgacode_ai(prompt):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return "API Key fehlt!"
    genai.configure(api_key=api_key)
    try:
        available = [m.name for m in genai.list_models()]
        model_id = next((m for m in available if 'gemini-1.5-flash' in m), available[0])
        model = genai.GenerativeModel(model_id)
        return model.generate_content(prompt).text
    except Exception as e: return f"Fehler: {e}"

def main():
    st.markdown("<h1>TGA<span style='color:#00f2fe;'>code</span> <small>Enterprise Vault</small></h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🏢 PROJEKT-MATRIX")
        firmen = [f for f in os.listdir(VAULT_DIR) if os.path.isdir(os.path.join(VAULT_DIR, f))]
        sel_f = st.selectbox("FIRMA", ["--"] + firmen)
        
        sel_p = "--"
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(VAULT_DIR, sel_f))]
            sel_p = st.selectbox("PROJEKT", ["--"] + projekte)
            
            with st.expander("➕ NEU ANLEGEN"):
                nf = st.text_input("Name")
                type_sel = st.radio("Was?", ["Firma", "Projekt"])
                if st.button("SPEICHERN"):
                    if type_sel == "Firma" and nf: os.makedirs(os.path.join(VAULT_DIR, nf))
                    elif nf: os.makedirs(os.path.join(VAULT_DIR, sel_f, nf))
                    st.rerun()

    if sel_p == "--":
        st.info("👈 Bitte wählen Sie links eine Firma und ein Projekt aus.")
        st.stop()

    # --- PFADE FÜR DIESES PROJEKT ---
    path_basis = get_project_path(sel_f, sel_p, "BASIS_VERTRAG")
    path_nachtrag = get_project_path(sel_f, sel_p, "NACHTRAEGE")

    tab1, tab2, tab3 = st.tabs(["🏗️ NACHTRAGSPRÜFUNG", "📁 PROJEKT-AKTE (Archiv)", "💬 EXPERTEN-CHAT"])

    # --- TAB 2: PROJEKT-AKTE (Hier kommen ALLE Basics rein) ---
    with tab2:
        st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
        st.subheader("Vertrags-Grundlagen & LV (Multi-Upload)")
        files_basis = st.file_uploader("LV, Vertrag, Pläne, Protokolle (Mehrere PDFs möglich)", type="pdf", accept_multiple_files=True)
        if st.button("IN AKTE ARCHIVIEREN"):
            for f in files_basis:
                text = "".join([p.extract_text() for p in PdfReader(f).pages])
                with open(os.path.join(path_basis, f.name.replace(".pdf", ".txt")), "w", encoding="utf-8") as file:
                    file.write(text)
            st.success(f"{len(files_basis)} Dokumente zur Akte hinzugefügt.")
        
        st.markdown("---")
        st.write("📂 **In der Akte vorhanden:**")
        docs = os.listdir(path_basis)
        for d in docs: st.write(f"- {d.replace('.txt', '.pdf')}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 1: NACHTRAGS-MANAGEMENT ---
    with tab1:
        st.markdown("<div class='tgacode-card'>", unsafe_allow_html=True)
        st.subheader("Nachtrags-Paket prüfen")
        files_nt = st.file_uploader("Nachtrag + alle Anlagen (Berechnungen, Angebote, etc.)", type="pdf", accept_multiple_files=True)
        
        if st.button("🚀 VOLLSTÄNDIGE PRÜFUNG STARTEN"):
            if not docs or not files_nt:
                st.error("⚠️ Es müssen Basis-Dokumente UND Nachtrags-Dokumente vorhanden sein.")
            else:
                with st.spinner("Analysiere Gesamtzusammenhang..."):
                    # 1. Basis-Wissen sammeln
                    all_basis = ""
                    for d in docs: 
                        all_basis += f"\n--- DOKUMENT: {d} ---\n" + open(os.path.join(path_basis, d), "r", encoding="utf-8").read()
                    
                    # 2. Nachtrags-Inhalt lesen
                    all_nt = ""
                    for f in files_nt:
                        all_nt += f"\n--- NACHTRAGS-ANLAGE: {f.name} ---\n" + "".join([p.extract_text() for p in PdfReader(f).pages])
                    
                    # 3. KI Prompt
                    prompt = f"""
                    SYSTEM: Du bist Senior-Objektüberwacher bei TGAcode.
                    PROJEKT-AKTE (Basis): {all_basis[:12000]}
                    AKTUELLER NACHTRAG: {all_nt[:12000]}
                    
                    AUFGABE:
                    1. Vergleiche den Nachtrag mit dem LV UND dem Vertrag.
                    2. Prüfe alle Anlagen auf Plausibilität.
                    3. Erstelle ein detailliertes Prüfprotokoll nach VOB/B.
                    """
                    result = call_tgacode_ai(prompt)
                    st.markdown(result)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 3: CHAT (Greift auf ALLES zu) ---
    with tab3:
        # Hier die gleiche Logik: KI bekommt Inhaltsverzeichnis aller Dokumente
        st.write("Der Chat hat Zugriff auf alle Dokumente in der Akte und die Nachträge.")
        # ... (Chat Code)

if __name__ == "__main__":
    main()
