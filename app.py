import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer

# =========================================================
# SETUP & DESIGN (der TGAcode)
# =========================================================
st.set_page_config(page_title="der TGAcode", layout="wide")

# CSS für den TGAcode Look
st.markdown("""
<style>
.main { background-color: #ffffff; }
.top-nav {
    background-color: #1a1c24;
    padding: 20px 40px;
    color: white;
    border-bottom: 4px solid #00f2fe;
    margin-bottom: 30px;
}
.logo { font-size: 26px; font-weight: 800; }
.accent { color: #00f2fe; }
.stButton>button {
    background: #1a1c24; color: #00f2fe; border: 1px solid #00f2fe;
    width: 100%; font-weight: bold; border-radius: 4px; padding: 10px;
}
.stButton>button:hover { background: #00f2fe; color: #1a1c24; }
code { color: #1a1c24; background: #f0f2f5; }
</style>
<div class="top-nav">
    <div class="logo">der <span class="accent">TGAcode</span></div>
</div>
""", unsafe_allow_html=True)

# API Key aus Secrets (für Streamlit Cloud)
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ GEMINI_API_KEY fehlt in den Secrets.")
    st.stop()

genai.configure(api_key=api_key)
ai_model = genai.GenerativeModel("gemini-1.5-pro")

# Vektor-Setup
@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

embedder = load_embedder()
chroma = chromadb.Client()

VAULT = "vault_tgacode"
os.makedirs(VAULT, exist_ok=True)

# =========================================================
# HILFSFUNKTIONEN
# =========================================================
def read_pdf(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    except Exception as e:
        st.error(f"Fehler beim Lesen von {file_path}: {e}")
    return text

def split_text(text, size=400):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

def index_project(project_path, project_id):
    collection = chroma.get_or_create_collection(project_id)
    # Bestehende Daten für sauberen Neu-Index löschen
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    for f in os.listdir(project_path):
        if f.lower().endswith(".pdf"):
            text = read_pdf(os.path.join(project_path, f))
            chunks = split_text(text)
            if chunks:
                collection.add(
                    ids=[f"{f}_{i}" for i in range(len(chunks))],
                    documents=chunks,
                    embeddings=[embedder.encode(chunk).tolist() for chunk in chunks]
                )

def query_project(project_id, query, k=8):
    try:
        collection = chroma.get_collection(project_id)
        emb = embedder.encode(query).tolist()
        result = collection.query(query_embeddings=[emb], n_results=k)
        return "\n".join(result["documents"][0])
    except:
        return "Kein indexiertes Wissen gefunden."

# =========================================================
# UI – PROJEKT-AUSWAHL
# =========================================================
st.markdown("### Projekt-Auswahl")
c1, c2, c3 = st.columns(3)

firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]

with c1:
    sel_f = st.selectbox("Firma", ["--"] + firmen)
    with st.expander("Firma anlegen"):
        nf = st.text_input("Firmenname")
        if st.button("Firma erstellen") and nf:
            os.makedirs(os.path.join(VAULT, nf), exist_ok=True)
            st.rerun()

sel_p = "--"
if sel_f != "--":
    projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f)) if os.path.isdir(os.path.join(VAULT, sel_f, p))]
    with c2:
        sel_p = st.selectbox("Projekt", ["--"] + projekte)
        with st.expander("Projekt anlegen"):
            np = st.text_input("Projektname")
            if st.button("Projekt erstellen") and np:
                os.makedirs(os.path.join(VAULT, sel_f, np), exist_ok=True)
                st.rerun()
else:
    with c2: st.info("Bitte zuerst Firma wählen")

with c3:
    if sel_p != "--": st.success(f"Aktiv: {sel_p}")
    else: st.warning("Kein Projekt aktiv")

st.divider()

# =========================================================
# ARBEITSBEREICH
# =========================================================
if sel_p != "--":
    path_p = os.path.join(VAULT, sel_f, sel_p)
    project_id = f"{sel_f}_{sel_p}".replace(" ", "_")

    t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Prüfung"])

    with t1:
        st.markdown("#### Projekt-Akte (LV, Vertrag, Pläne)")
        uploads = st.file_uploader("PDFs hinzufügen", accept_multiple_files=True)
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("Dokumente speichern"):
            for f in uploads:
                with open(os.path.join(path_p, f.name), "wb") as out:
                    out.write(f.getbuffer())
            st.rerun()

        if col_btn2.button("📚 Projektwissen indexieren"):
            with st.spinner("Indexiere Projekt-Akte..."):
                index_project(path_p, project_id)
            st.success("Wissen bereitgestellt.")

        st.markdown("**Bestand:**")
        for d in os.listdir(path_p):
            cd, cx = st.columns([0.85, 0.15])
            cd.code(d)
            if cx.button("X", key=d):
                os.remove(os.path.join(path_p, d))
                st.rerun()

    with t2:
        st.markdown("#### Nachtragsprüfung")
        nt_files = st.file_uploader("Nachtrag + Anlagen hochladen", accept_multiple_files=True)

        if st.button("🚀 Prüfung starten"):
            if not nt_files:
                st.warning("Kein Nachtrag gefunden.")
                st.stop()
            
            with st.spinner("der TGAcode analysiert..."):
                # Nachtrag lesen
                nt_text = ""
                for f in nt_files:
                    reader = PdfReader(f)
                    for page in reader.pages:
                        nt_text += (page.extract_text() or "") + "\n"

                # Kontext aus Projekt-Akte holen
                kontext = query_project(project_id, nt_text[:2000]) # Nutze Anfang des Nachtrags für Suche

                prompt = f"""
                SYSTEM: Du bist 'der TGAcode'. Analysiere sachlich und streng nach VOB/B.
                
                KONTEXT AUS PROJEKT-AKTE:
                {kontext}

                EINGEREICHTER NACHTRAG:
                {nt_text}

                STRUKTUR:
                1. VERTRIEBLICHE/RECHTLICHE PRÜFUNG (VOB/B)
                2. TECHNISCHE PLAUSIBILITÄT
                3. PREISPRÜFUNG (TABELLE)
                4. KONKRETE KÜRZUNGSEMPFEHLUNG
                """
                
                result = ai_model.generate_content(prompt).text
                st.markdown("### Prüfprotokoll")
                st.markdown(result)

if __name__ == "__main__":
    main()
Alle Ergebnisse dienen ausschließlich als Entscheidungshilfe.
""")

