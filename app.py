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
.report-box { 
    background-color: #f8fafc; padding: 20px; border-radius: 8px; 
    border: 1px solid #e2e8f0; font-family: monospace;
}
</style>
<div class="top-nav">
    <div class="logo">der <span class="accent">TGAcode</span></div>
</div>
""", unsafe_allow_html=True)

# API Key & Modell
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ GEMINI_API_KEY fehlt in den Secrets.")
    st.stop()

genai.configure(api_key=api_key)
ai_model = genai.GenerativeModel("gemini-1.5-pro")

@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

embedder = load_embedder()
chroma = chromadb.Client()

VAULT = "vault_tgacode"
if not os.path.exists(VAULT):
    os.makedirs(VAULT)

# =========================================================
# FUNKTIONEN
# =========================================================
def read_pdf(file):
    text = ""
    try:
        reader = PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    except: pass
    return text

def index_project(project_path, project_id):
    collection = chroma.get_or_create_collection(project_id)
    existing = collection.get()
    if existing["ids"]: collection.delete(ids=existing["ids"])
    
    for f in os.listdir(project_path):
        if f.lower().endswith(".pdf"):
            full_path = os.path.join(project_path, f)
            text = read_pdf(full_path)
            words = text.split()
            chunks = [" ".join(words[i:i+400]) for i in range(0, len(words), 400)]
            if chunks:
                collection.add(
                    ids=[f"{f}_{i}" for i in range(len(chunks))],
                    documents=chunks,
                    embeddings=[embedder.encode(c).tolist() for c in chunks]
                )

def query_project(project_id, query):
    try:
        collection = chroma.get_collection(project_id)
        res = collection.query(query_embeddings=[embedder.encode(query).tolist()], n_results=8)
        return "\n".join(res["documents"][0])
    except: return "Kein Basiswissen gefunden."

# =========================================================
# MAIN APP
# =========================================================
def main():
    st.markdown("### Projekt-Auswahl")
    c1, c2, c3 = st.columns(3)

    firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
    
    with c1:
        sel_f = st.selectbox("Firma", ["--"] + firmen)
        with st.expander("Firma anlegen"):
            nf = st.text_input("Firmenname")
            if st.button("Anlegen", key="new_f"):
                os.makedirs(os.path.join(VAULT, nf), exist_ok=True)
                st.rerun()

    sel_p = "--"
    if sel_f != "--":
        projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        with c2:
            sel_p = st.selectbox("Projekt", ["--"] + projekte)
            with st.expander("Projekt anlegen"):
                np = st.text_input("Projektname")
                if st.button("Anlegen", key="new_p"):
                    os.makedirs(os.path.join(VAULT, sel_f, np), exist_ok=True)
                    st.rerun()
    
    with c3:
        if sel_p != "--": st.success(f"Aktiv: {sel_p}")
        else: st.warning("Projekt wählen")

    st.divider()

    if sel_p != "--":
        path_p = os.path.join(VAULT, sel_f, sel_p)
        project_id = f"{sel_f}_{sel_p}".replace(" ", "_")
        
        t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Prüfung"])

        with t1:
            st.markdown("#### Dokumente verwalten")
            up = st.file_uploader("PDFs hochladen", accept_multiple_files=True)
            col_a, col_b = st.columns(2)
            if col_a.button("Speichern"):
                for f in up:
                    with open(os.path.join(path_p, f.name), "wb") as o: o.write(f.getbuffer())
                st.rerun()
            if col_b.button("Indexieren"):
                index_project(path_p, project_id)
                st.success("Wissen bereit.")
            
            for d in os.listdir(path_p):
                cx, cy = st.columns([0.9, 0.1])
                cx.code(d)
                if cy.button("X", key=d):
                    os.remove(os.path.join(path_p, d))
                    st.rerun()

        with t2:
            st.markdown("#### Nachtrag prüfen")
            nt_files = st.file_uploader("Nachtrag + Anlagen", accept_multiple_files=True)
            
            if st.button("Prüfung starten"):
                with st.spinner("der TGAcode analysiert..."):
                    nt_text = ""
                    for f in nt_files: nt_text += read_pdf(f)
                    kontext = query_project(project_id, nt_text[:1000])
                    
                    prompt = f"SYSTEM: Du bist 'der TGAcode'. Analysiere sachlich.\nKONTEXT:\n{kontext}\n\nNACHTRAG:\n{nt_text}\n\nSTRUKTUR: VOB-Check, Mengen-Check, Preis-Check, Empfehlung."
                    res = ai_model.generate_content(prompt)
                    st.session_state.last_audit = res.text

            if "last_audit" in st.session_state:
                st.markdown(f"<div class='report-box'>{st.session_state.last_audit}</div>", unsafe_allow_html=True)
                
                st.divider()
                st.markdown("#### Chat-Anweisung zum Ergebnis")
                feedback = st.chat_input("Anweisung an der TGAcode...")
                if feedback:
                    # Direkte Interaktion mit dem letzten Ergebnis
                    new_prompt = f"Du hast diesen Bericht erstellt:\n{st.session_state.last_audit}\n\nAnweisung vom User: {feedback}\n\nÜberarbeite den Bericht entsprechend."
                    new_res = ai_model.generate_content(new_prompt)
                    st.session_state.last_audit = new_res.text
                    st.rerun()

if __name__ == "__main__":
    main()
