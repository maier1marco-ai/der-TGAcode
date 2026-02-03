import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. TGAcode INDUSTRIAL DESIGN ---
st.set_page_config(page_title="der TGAcode | Audit-Panel", layout="wide")

st.markdown("""
    <style>
    /* Industrial Look */
    .stApp { background-color: #f8fafc; }
    .report-box { 
        background-color: white; 
        padding: 2rem; 
        border: 1px solid #e2e8f0; 
        border-radius: 4px;
        font-family: 'Courier New', Courier, monospace; /* Technischer Look */
    }
    .vob-critical { 
        color: #e11d48; 
        font-weight: bold; 
        border-left: 4px solid #e11d48; 
        padding-left: 10px; 
    }
    /* Top Bar wie auf der Website */
    .header-bar {
        background: #1a1c24;
        color: #00f2fe;
        padding: 10px 20px;
        font-weight: 800;
        font-size: 24px;
        display: flex;
        justify-content: space-between;
    }
    </style>
    <div class="header-bar">
        <div>der TGAcode // Audit-Panel</div>
        <div style="font-size: 12px; color: white; opacity: 0.5;">Sektion: Objektüberwachung</div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. LOGIK FÜR FIRMA/PROJEKT (FIXED) ---
VAULT = "vault_tgacode"
if not os.path.exists(VAULT): os.makedirs(VAULT)

def main():
    # --- NAVIGATION & CREATION ---
    col_nav1, col_nav2 = st.columns(2)
    
    firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
    with col_nav1:
        sel_f = st.selectbox("MANDANT / FIRMA", ["--"] + firmen)
        with st.expander("🆕 Neue Firma"):
            nf = st.text_input("Name")
            if st.button("Firma anlegen"):
                os.makedirs(os.path.join(VAULT, nf))
                st.rerun()

    sel_p = "--"
    if sel_f != "--":
        projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        with col_nav2:
            sel_p = st.selectbox("PROJEKT", ["--"] + projekte)
            with st.expander("🆕 Neues Projekt"):
                np = st.text_input("Bezeichnung")
                if st.button("Projekt anlegen"):
                    os.makedirs(os.path.join(VAULT, sel_f, np))
                    st.rerun()

    if sel_p == "--":
        st.info("System bereit. Bitte Projekt wählen.")
        return

    # --- ACTION AREA ---
    path_p = os.path.join(VAULT, sel_f, sel_p)
    tab_files, tab_audit = st.tabs(["📁 DATEN-VAULT", "🔬 PRÜF-MODUL"])

    with tab_files:
        st.subheader("Basis-Dokumente (LV, Vertrag, Pläne)")
        up = st.file_uploader("PDFs hochladen", accept_multiple_files=True, key="basis")
        if st.button("Speichern"):
            for f in up:
                with open(os.path.join(path_p, f.name), "wb") as file: file.write(f.getbuffer())
            st.rerun()
        
        st.write("Bestand:")
        for d in os.listdir(path_p):
            c1, c2 = st.columns([0.9, 0.1])
            c1.markdown(f"`{d}`")
            if c2.button("X", key=d):
                os.remove(os.path.join(path_p, d))
                st.rerun()

    with tab_audit:
        st.subheader("Nachtrags-Paket")
        nt_up = st.file_uploader("Nachtrag + Anlagen", accept_multiple_files=True, key="nt")
        
        if st.button("PRÜFUNG STARTEN"):
            with st.spinner("Extrahiere Daten..."):
                # KI AUFRUF (SACHLICH)
                basis_data = ""
                for d in os.listdir(path_p):
                    basis_data += f"\nFILE: {d}\n" + "".join([p.extract_text() for p in PdfReader(os.path.join(path_p, d)).pages])
                
                nt_data = ""
                for f in nt_up:
                    nt_data += f"\nFILE: {f.name}\n" + "".join([p.extract_text() for p in PdfReader(f).pages])

                prompt = f"""
                SYSTEM: Du bist 'der TGAcode'. Analysiere sachlich. Keine Höflichkeitsfloskeln. 
                KONTEXT:
                BASIS-DOCS: {basis_data[:10000]}
                NACHTRAG: {nt_data[:10000]}
                
                OUTPUT-STRUKTUR:
                1. FORMAL-CHECK (VOB §...)
                2. MENGEN-CHECK (Tabelle: Soll/Ist/Diff)
                3. PREIS-CHECK (Kalkulationsprüfung)
                4. KÜRZUNGSEMPFEHLUNG (Euro-Betrag)
                """
                
                # API Call hier (Placeholder für dein Gemini Setup)
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                st.session_state.last_report = response.text

        if "last_report" in st.session_state:
            st.markdown("---")
            st.markdown("### PRÜFPROTOKOLL")
            st.markdown(f"<div class='report-box'>{st.session_state.last_report}</div>", unsafe_allow_html=True)
            
            # --- DER DIREKT-CHAT UNTER DEM AUDIT ---
            st.markdown("### Anweisung an die KI")
            feedback = st.chat_input("z.B. 'Überarbeite Punkt 2 mit Fokus auf § 2 Abs. 3 VOB/B'...")
            if feedback:
                # Hier würde die KI den Report basierend auf deinem Feedback anpassen
                st.write(f"Anweisung erhalten: {feedback}")
                # Logik zur Report-Anpassung folgt...

if __name__ == "__main__":
    main()
