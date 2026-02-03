import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer

# --- DESIGN & BRANDING ---
st.set_page_config(page_title="der TGAcode", layout="wide")
st.markdown("""
<style>
.top-nav { background-color: #1a1c24; padding: 20px; color: white; border-bottom: 4px solid #00f2fe; margin-bottom: 30px; }
.logo { font-size: 26px; font-weight: 800; }
.accent { color: #00f2fe; }
.stButton>button { background: #1a1c24; color: #00f2fe; border: 1px solid #00f2fe; width: 100%; font-weight: bold; }
.report-box { background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }
</style>
<div class="top-nav"><div class="logo">der <span class="accent">TGAcode</span></div></div>
""", unsafe_allow_html=True)

# --- API & MODELL-WAHL FIX ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("API Key fehlt!")
    st.stop()

genai.configure(api_key=api_key)

def init_ai_model():
    # Versuche verschiedene Modell-Strings, um den 404 Fehler zu umgehen
    model_variants = ["gemini-1.5-flash", "gemini-1.5-pro", "models/gemini-1.5-flash", "models/gemini-1.5-pro"]
    for m in model_variants:
        try:
            model = genai.GenerativeModel(m)
            # Test-Aufruf um Validität zu prüfen
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            return model
        except:
            continue
    st.error("Kein passendes KI-Modell gefunden. Bitte API-Berechtigungen prüfen.")
    return None

ai_model = init_ai_model()

@st.cache_resource
def get_embedder(): return SentenceTransformer("all-MiniLM-L6-v2")
embedder = get_embedder()
chroma = chromadb.Client()
VAULT = "vault_tgacode"
os.makedirs(VAULT, exist_ok=True)

# --- LOGIK ---
def read_pdf(file):
    text = ""
    try:
        reader = PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    except: pass
    return text

def index_project(path, p_id):
    col = chroma.get_or_create_collection(p_id)
    ids = col.get()["ids"]
    if ids: col.delete(ids=ids)
    for f in os.listdir(path):
        if f.lower().endswith(".pdf"):
            text = read_pdf(os.path.join(path, f))
            chunks = [" ".join(text.split()[i:i+400]) for i in range(0, len(text.split()), 400)]
            if chunks:
                col.add(ids=[f"{f}_{i}" for i in range(len(chunks))], documents=chunks, 
                        embeddings=[embedder.encode(c).tolist() for c in chunks])

# --- UI ---
def main():
    c1, c2, c3 = st.columns(3)
    firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
    
    with c1:
        sel_f = st.selectbox("Firma", ["--"] + firmen)
        with st.expander("Firma anlegen"):
            nf = st.text_input("Name")
            if st.button("Anlegen", key="f"):
                os.makedirs(os.path.join(VAULT, nf), exist_ok=True); st.rerun()

    sel_p = "--"
    if sel_f != "--":
        projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        with c2:
            sel_p = st.selectbox("Projekt", ["--"] + projekte)
            with st.expander("Projekt anlegen"):
                np = st.text_input("Projekt")
                if st.button("Anlegen", key="p"):
                    os.makedirs(os.path.join(VAULT, sel_f, np), exist_ok=True); st.rerun()
    
    if sel_p != "--":
        p_path = os.path.join(VAULT, sel_f, sel_p)
        p_id = f"{sel_f}_{sel_p}".replace(" ", "_")
        t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Prüfung"])

        with t1:
            up = st.file_uploader("Upload", accept_multiple_files=True)
            ca, cb = st.columns(2)
            if ca.button("Speichern"):
                for f in up:
                    with open(os.path.join(p_path, f.name), "wb") as o: o.write(f.getbuffer())
                st.rerun()
            if cb.button("Indexieren"):
                index_project(p_path, p_id); st.success("Bereit")
            for d in os.listdir(p_path):
                cx, cy = st.columns([0.9, 0.1])
                cx.code(d)
                if cy.button("X", key=d): os.remove(os.path.join(p_path, d)); st.rerun()

        with t2:
            nt = st.file_uploader("Nachtrag PDF", accept_multiple_files=True)
            if st.button("Prüfung starten"):
                nt_text = "".join([read_pdf(f) for f in nt])
                ctx = ""
                try:
                    res = chroma.get_collection(p_id).query(query_embeddings=[embedder.encode(nt_text[:500]).tolist()], n_results=5)
                    ctx = "\n".join(res["documents"][0])
                except: ctx = "Kein Kontext vorhanden."
                
                prompt = f"SYSTEM: Du bist 'der TGAcode'. Analysiere sachlich.\nKONTEXT:\n{ctx}\n\nNACHTRAG:\n{nt_text}\n\nSTRUKTUR: VOB-Check, Preis-Check, Empfehlung."
                st.session_state.report = ai_model.generate_content(prompt).text

            if "report" in st.session_state:
                st.markdown(f"<div class='report-box'>{st.session_state.report}</div>", unsafe_allow_html=True)
                instr = st.chat_input("Anweisung an der TGAcode...")
                if instr:
                    st.session_state.report = ai_model.generate_content(f"Bericht:\n{st.session_state.report}\n\nAnweisung: {instr}\n\nÜberarbeite sachlich.").text
                    st.rerun()

if __name__ == "__main__":
    main()
