import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import time
from fpdf import FPDF

# --- 1. BRANDING & UI BOOSTER ---
st.set_page_config(page_title="der TGAcode | Enterprise", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; background-color: #f4f7f9; }
    
    /* Der TGAcode Header */
    .top-nav {
        background: #1a1c24; padding: 20px 50px; border-bottom: 4px solid #00f2fe;
        display: flex; justify-content: space-between; align-items: center; color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .logo-text { font-size: 28px; font-weight: 900; letter-spacing: -1px; }
    .accent { color: #00f2fe; }
    
    /* Deep Audit Card */
    .audit-card {
        background: white; border-left: 8px solid #00f2fe; border-radius: 8px;
        padding: 25px; margin: 20px 0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    /* Status Badges */
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-vob { background: #e0f2fe; color: #0369a1; }
    .badge-alert { background: #fee2e2; color: #991b1b; }
    </style>
    
    <div class="top-nav">
        <div class="logo-text">der <span class="accent">TGAcode</span></div>
        <div style="opacity:0.6">VOB-NACHTRAGS-INTELLIGENZ v5.2</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. INTELLIGENTE MODELL-WAHL (Fix für 404) ---
def get_safe_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        # Liste alle Modelle auf, die Content generieren können
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Priorität: 1. Flash 1.5, 2. Flash 1.5 Latest, 3. Pro
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']:
            if target in models:
                return genai.GenerativeModel(target)
        return genai.GenerativeModel(models[0]) # Fallback auf das erste verfügbare
    except Exception as e:
        st.error(f"Modell-Fehler: {e}")
        return None

# --- 3. CORE FUNKTIONEN ---
VAULT = "vault_tgacode"
if not os.path.exists(VAULT): os.makedirs(VAULT)

def main():
    # --- PROJEKT AUSWAHL ---
    st.markdown("### 🏢 Projekt-Zentrale")
    col_f, col_p = st.columns(2)
    
    firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
    with col_f:
        sel_f = st.selectbox("Firma wählen", ["--"] + firmen)
        with st.expander("Neue Firma"):
            nf = st.text_input("Firmenname")
            if st.button("Firma anlegen"): os.makedirs(os.path.join(VAULT, nf)); st.rerun()

    sel_p = "--"
    if sel_f != "--":
        projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        with col_p:
            sel_p = st.selectbox("Projekt wählen", ["--"] + projekte)
            with st.expander("Neues Projekt"):
                np = st.text_input("Projektname")
                if st.button("Projekt anlegen"): os.makedirs(os.path.join(VAULT, sel_f, np)); st.rerun()

    if sel_p == "--":
        st.info("Bitte wählen Sie links die Firma und das Projekt aus.")
        return

    # --- MAIN INTERFACE ---
    path_p = os.path.join(VAULT, sel_f, sel_p)
    t1, t2, t3 = st.tabs(["📁 PROJEKT-AKTE", "🔬 DEEP-AUDIT", "💬 EXPERTEN-CHAT"])

    with t1:
        st.markdown("#### Vertragsgrundlagen (LV, Vertrag, Pläne)")
        up = st.file_uploader("Dokumente hochladen", accept_multiple_files=True, type="pdf")
        if st.button("In Akte sichern"):
            for f in up:
                with open(os.path.join(path_p, f.name), "wb") as file: file.write(f.getbuffer())
            st.success("Dokumente gespeichert.")
            st.rerun()
        
        st.divider()
        st.write("Vorhanden:")
        for doc in os.listdir(path_p):
            col_d1, col_d2 = st.columns([0.9, 0.1])
            col_d1.code(f"📄 {doc}")
            if col_d2.button("X", key=f"del_{doc}"): 
                os.remove(os.path.join(path_p, doc))
                st.rerun()

    with t2:
        st.markdown("<div class='audit-card'>", unsafe_allow_html=True)
        st.markdown("### 🚀 Nachtrags-Deep-Audit")
        st.write("Vergleicht alle Akten-Dokumente mit dem neuen Nachtrag.")
        
        nt_up = st.file_uploader("Aktueller Nachtrag + Anlagen", accept_multiple_files=True, type="pdf", key="nt")
        
        if st.button("VOB-PRÜFUNG STARTEN"):
            if not nt_up:
                st.warning("Kein Nachtrag zum Prüfen hochgeladen.")
            else:
                model = get_safe_model()
                with st.spinner("der TGAcode analysiert die Datenstruktur..."):
                    # Texte extrahieren
                    basis_text = ""
                    for d in os.listdir(path_p):
                        reader = PdfReader(os.path.join(path_p, d))
                        basis_text += f"\n--- DATEI: {d} ---\n" + "".join([p.extract_text() for p in reader.pages])
                    
                    nt_text = ""
                    for f in nt_up:
                        reader = PdfReader(f)
                        nt_text += f"\n--- ANLAGE: {f.name} ---\n" + "".join([p.extract_text() for p in reader.pages])
                    
                    prompt = f"""
                    Rolle: Senior Objektüberwacher 'der TGAcode'.
                    AUFGABE: Deep Audit eines Nachtrags.
                    BASIS: {basis_text[:12000]}
                    NACHTRAG: {nt_text[:12000]}
                    
                    STRUKTUR DER ANTWORT:
                    - Nutzen Sie Markdown-Tabellen für Kostenvergleiche.
                    - Markieren Sie kritische Punkte mit '⚠️'.
                    - Nennen Sie explizit VOB-Paragraphen.
                    - Geben Sie eine klare Kürzungsempfehlung in Euro.
                    """
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.write("Chat-Funktion mit Zugriff auf Projekt-Akte...")

if __name__ == "__main__":
    main()
