import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
import time
import json
import openpyxl
from io import BytesIO

# --- DESIGN V2: Modernes UI für TGAcode ---
st.set_page_config(page_title="der TGAcode", layout="wide")
st.markdown("""
<style>
    /* CSS bleibt hier wie im letzten Code-Snippet */
    body { color: #fafafa; background-color: #0d1117; }
    .stApp { background-color: #0d1117; }
    .st-emotion-cache-18ni7ap { background: #161b22; }
    .st-emotion-cache-16txtl3 { padding: 2rem 2rem; }
    h1, h2, h3 { color: #c9d1d9; }
    .top-nav { background-color: #161b22; padding: 1rem 2rem; border-bottom: 2px solid #00f2fe; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; }
    .logo { font-size: 26px; font-weight: 800; color: #f0f6fc; }
    .accent { color: #00f2fe; }
    .stButton>button { background: linear-gradient(45deg, #00f2fe, #2c7fff); color: white; border: none; width: 100%; font-weight: bold; padding: 10px 0; border-radius: 8px; transition: transform 0.1s ease-in-out; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #00f2fe; }
    .report-box { background-color: #161b22; padding: 25px; border-radius: 10px; border: 1px solid #30363d; line-height: 1.6; }
    .report-box h1, .report-box h3 { border-bottom: 1px solid #30363d; padding-bottom: 8px; }
</style>
<div class="top-nav">
    <div class="logo">der <span class="accent">TGAcode</span></div>
    <div style="color: #8b949e;">AI-Powered Project Analysis</div>
</div>
""", unsafe_allow_html=True)


# --- GLOBALE VARIABLEN & INITIALISIERUNG ---
# Diese Definitionen müssen am Anfang des Skripts stehen, außerhalb von main()
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("API Key fehlt in Streamlit Secrets!")
    st.stop()
genai.configure(api_key=api_key)

VAULT = "vault_tgacode" # WICHTIG: Definition von VAULT
os.makedirs(VAULT, exist_ok=True)


# --- HELFERFUNKTIONEN & MODELLE ---
@st.cache_resource
def init_ai_model():
    model_candidates = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-1.5-flash"]
    for m in model_candidates:
        try:
            model = genai.GenerativeModel(m)
            model.generate_content("ping", generation_config={"max_output_tokens": 1})
            return model
        except: continue
    return None

@st.cache_resource
def get_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

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
            words = text.split()
            chunks = [" ".join(words[i:i+400]) for i in range(0, len(words), 400)]
            if chunks:
                col.add(ids=[f"{f}_{i}" for i in range(len(chunks))], documents=chunks, 
                        embeddings=[embedder.encode(c).tolist() for c in chunks])

# Globale Modelle laden
ai_model = init_ai_model()
embedder = get_embedder()
chroma = chromadb.Client()

if not ai_model:
    st.error("Kein unterstütztes Gemini-Modell gefunden.")
    st.stop()


# --- HAUPTFUNKTION DER APP ---
def main():
    st.header("Projektauswahl")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
        sel_f = st.selectbox("Firma auswählen", ["--"] + firmen, label_visibility="collapsed")
        
        projekte = []
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        sel_p = st.selectbox("Projekt auswählen", ["--"] + projekte, label_visibility="collapsed")

    with c2:
        with st.expander("➕ Neues Projekt oder Firma anlegen"):
            nc1, nc2 = st.columns(2)
            with nc1:
                nf = st.text_input("Neue Firma")
                if st.button("Firma anlegen"):
                    os.makedirs(os.path.join(VAULT, nf), exist_ok=True); st.rerun()
            with nc2:
                np_firma = st.selectbox("Für Firma", ["--"] + firmen)
                np = st.text_input("Neues Projekt")
                if st.button("Projekt anlegen") and np_firma != "--":
                    os.makedirs(os.path.join(VAULT, np_firma, np), exist_ok=True); st.rerun()
    st.markdown("---")

    if sel_f != "--" and sel_p != "--":
        p_path = os.path.join(VAULT, sel_f, sel_p)
        p_id = f"{sel_f}_{sel_p}".replace(" ", "_")
        
        st.header(f"Projekt-Dashboard: {sel_p}")
        t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Nachtrags-Prüfung"])

        with t1:
            st.subheader("Stammdaten & Projekt-Regeln (Gedächtnis)")
            stammdaten_path = os.path.join(p_path, "_projekt_stammdaten.txt")
            current_stammdaten = ""
            if os.path.exists(stammdaten_path):
                with open(stammdaten_path, "r", encoding="utf-8") as f:
                    current_stammdaten = f.read()
            
            stammdaten_input = st.text_area("Hier können permanente Regeln für dieses Projekt hinterlegt werden (z.B. 'Stundensatz Fa. Reiter ist 48€').", value=current_stammdaten, height=150)
            if st.button("Stammdaten speichern"):
                with open(stammdaten_path, "w", encoding="utf-8") as f:
                    f.write(stammdaten_input)
                st.success("Stammdaten wurden gespeichert!")
            
            st.markdown("---")
            # ... (Rest der Projekt-Akte) ...

        with t2:
            st.subheader("Nachtrag zur Prüfung hochladen")
            # ... (Logik der Nachtrags-Prüfung) ...
            
            if "report" in st.session_state:
                st.markdown("---")
                # ... (Anzeige des Reports und der Deckblatt-Funktion) ...


# --- STARTPUNKT DES SKRIPTS ---
if __name__ == "__main__":
    main()
