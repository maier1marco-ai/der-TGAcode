import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer

# =========================================================
# SICHERHEIT: API KEY PRÜFEN
# =========================================================
if not os.getenv("GEMINI_API_KEY"):
    st.error("❌ GEMINI_API_KEY ist nicht gesetzt. Bitte zuerst den API-Key einrichten.")
    st.stop()

# =========================================================
# GRUNDSETUP
# =========================================================
st.set_page_config(page_title="der TGAcode", layout="wide")

VAULT = "vault_tgacode"
os.makedirs(VAULT, exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel("gemini-1.5-pro")

embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.Client()

# =========================================================
# DESIGN
# =========================================================
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
    background: #1a1c24;
    color: #00f2fe;
    border: 1px solid #00f2fe;
    width: 100%;
    font-weight: bold;
}
.stButton>button:hover {
    background: #00f2fe;
    color: #1a1c24;
}
</style>
<div class="top-nav">
    <div class="logo">der <span class="accent">TGAcode</span></div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# HILFSFUNKTIONEN
# =========================================================
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text

def split_text(text, size=400):
    words = text.split()
    return [
        " ".join(words[i:i+size])
        for i in range(0, len(words), size)
    ]

# =========================================================
# VEKTOR-DATENBANK
# =========================================================
def index_project(project_path, project_id):
    collection = chroma.get_or_create_collection(project_id)
    collection.delete(where={})  # alte Daten löschen

    for f in os.listdir(project_path):
        if f.lower().endswith(".pdf"):
            text = read_pdf(os.path.join(project_path, f))
            chunks = split_text(text)

            for i, chunk in enumerate(chunks):
                collection.add(
                    ids=[f"{f}_{i}"],
                    documents=[chunk],
                    embeddings=[embedder.encode(chunk).tolist()]
                )

def query_project(project_id, query, k=10):
    collection = chroma.get_collection(project_id)
    emb = embedder.encode(query).tolist()
    result = collection.query(
        query_embeddings=[emb],
        n_results=k
    )
    return "\n".join(result["documents"][0])

# =========================================================
# KI-PROMPT
# =========================================================
PROMPT = """
Du bist ein öffentlich bestellter TGA-Sachverständiger und Bauvertragsprüfer.

### Relevante Vertrags- und Projektstellen:
{kontext}

### Eingereichter Nachtrag:
{nachtrag}

Bewerte streng und professionell:

1. Vertragliche Grundlage (VOB/B, BGB)
2. Leistungsänderung oder Zusatzleistung?
3. Anordnung / Verursachung
4. Preisliche Plausibilität
5. Formale Mängel
6. Risiko Auftraggeber

Gib das Ergebnis exakt in dieser Struktur zurück:

AMPEL: 🟢 / 🟡 / 🔴
RISIKO-SCORE: 0–100 %

KURZFAZIT:
- maximal 4 Sätze

KRITISCHE PUNKTE:
- Bulletpoints

RÜCKFRAGEN AN AN:
- Bulletpoints

EMPFEHLUNG:
- Annehmen / Kürzen / Ablehnen

RECHTLICHER HINWEIS:
- Haftung / Nachweis / Risiko
"""

# =========================================================
# UI – PROJEKTAUSWAHL
# =========================================================
st.markdown("### Projekt-Auswahl")
c1, c2, c3 = st.columns(3)

firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]

with c1:
    sel_f = st.selectbox("Firma", ["--"] + firmen)
    with st.expander("Firma anlegen"):
        nf = st.text_input("Firmenname")
        if st.button("Firma erstellen") and nf:
            os.makedirs(os.path.join(VAULT, nf))
            st.rerun()

sel_p = "--"
if sel_f != "--":
    projekte = os.listdir(os.path.join(VAULT, sel_f))
    with c2:
        sel_p = st.selectbox("Projekt", ["--"] + projekte)
        with st.expander("Projekt anlegen"):
            np = st.text_input("Projektname")
            if st.button("Projekt erstellen") and np:
                os.makedirs(os.path.join(VAULT, sel_f, np))
                st.rerun()
else:
    with c2:
        st.info("Bitte zuerst eine Firma auswählen")

with c3:
    if sel_p != "--":
        st.success(f"Aktiv: {sel_p}")
    else:
        st.warning("Kein Projekt aktiv")

st.divider()

# =========================================================
# ARBEITSBEREICH
# =========================================================
if sel_p != "--":
    path_p = os.path.join(VAULT, sel_f, sel_p)
    project_id = f"{sel_f}_{sel_p}"

    t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Nachtragsprüfung"])

    # -------------------- PROJEKT-AKTE
    with t1:
        st.markdown("#### Projektunterlagen (PDF)")
        uploads = st.file_uploader("PDFs hochladen", accept_multiple_files=True)

        if st.button("Dokumente speichern"):
            for f in uploads:
                with open(os.path.join(path_p, f.name), "wb") as out:
                    out.write(f.getbuffer())
            st.success("Dokumente gespeichert")
            st.rerun()

        if st.button("📚 Projektwissen indexieren"):
            with st.spinner("Projekt wird analysiert..."):
                index_project(path_p, project_id)
            st.success("Projektwissen bereit")

        st.markdown("**Vorhandene Dateien:**")
        for d in os.listdir(path_p):
            st.code(d)

    # -------------------- NACHRAGSPRÜFUNG
    with t2:
        st.markdown("#### Nachtrag hochladen")
        nt_files = st.file_uploader("Nachtrag + Anlagen", accept_multiple_files=True)

        if not nt_files:
            st.info("ℹ️ Bitte zuerst den Nachtrag hochladen.")

        if st.button("🔥 Nachtrag prüfen"):
            if not os.listdir(path_p):
                st.warning("⚠️ Projekt enthält noch keine Unterlagen.")
                st.stop()

            with st.spinner("KI prüft den Nachtrag..."):
                nachtrag_text = ""
                for f in nt_files:
                    nachtrag_text += read_pdf(f)

                kontext = query_project(
                    project_id,
                    "Vertrag Leistungsbeschreibung Nachtrag Änderung Preis Anordnung"
                )

                prompt = PROMPT.format(
                    kontext=kontext,
                    nachtrag=nachtrag_text
                )

                result = ai_model.generate_content(prompt).text

            st.markdown("## 🧾 Prüfergebnis")
            st.markdown(result)

            st.divider()
            st.caption("""
⚠️ **Hinweis:**  
Diese KI-gestützte Prüfung ersetzt keine rechtliche oder fachgutachterliche Prüfung.
Alle Ergebnisse dienen ausschließlich als Entscheidungshilfe.
""")
