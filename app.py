import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
import time

# --- DESIGN V2: Modernes UI für TGAcode ---
st.set_page_config(page_title="der TGAcode", layout="wide")
st.markdown("""
<style>
    /* Dunkles, modernes Farbschema */
    body { color: #fafafa; background-color: #0d1117; }
    .stApp { background-color: #0d1117; }
    .st-emotion-cache-18ni7ap { background: #161b22; } /* Main container background */
    .st-emotion-cache-16txtl3 { padding: 2rem 2rem; } /* Main padding */
    h1, h2, h3 { color: #c9d1d9; }
    
    /* Top-Nav & Logo */
    .top-nav {
        background-color: #161b22;
        padding: 1rem 2rem;
        border-bottom: 2px solid #00f2fe;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .logo { font-size: 26px; font-weight: 800; color: #f0f6fc; }
    .accent { color: #00f2fe; }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #00f2fe, #2c7fff);
        color: white;
        border: none;
        width: 100%;
        font-weight: bold;
        padding: 10px 0;
        border-radius: 8px;
        transition: transform 0.1s ease-in-out;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px #00f2fe;
    }

    /* Report Box */
    .report-box { 
        background-color: #161b22; 
        padding: 25px; 
        border-radius: 10px; 
        border: 1px solid #30363d; 
        line-height: 1.6;
    }
    .report-box h1, .report-box h3 {
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
    }
</style>
<div class="top-nav">
    <div class="logo">der <span class="accent">TGAcode</span></div>
    <div style="color: #8b949e;">AI-Powered Project Analysis</div>
</div>
""", unsafe_allow_html=True)


# --- API & MODELL-WAHL (unverändert) ---
# ... (dein restlicher Code für API, Modell, PDF-Reader etc. bleibt hier unverändert)
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("API Key fehlt in Streamlit Secrets!")
    st.stop()
genai.configure(api_key=api_key)
def init_ai_model():
    model_candidates = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-1.5-flash"]
    for m in model_candidates:
        try:
            model = genai.GenerativeModel(m)
            model.generate_content("ping", generation_config={"max_output_tokens": 1})
            return model
        except: continue
    return None
ai_model = init_ai_model()
if not ai_model:
    st.error("Kein unterstütztes Modell gefunden.")
    st.stop()
@st.cache_resource
def get_embedder(): return SentenceTransformer("all-MiniLM-L6-v2")
embedder = get_embedder()
chroma = chromadb.Client()
VAULT = "vault_tgacode"
os.makedirs(VAULT, exist_ok=True)
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

# --- UI V2: Modernisierte Hauptfunktion ---
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
            st.subheader("Dokumente verwalten")
            up = st.file_uploader("Neue Dokumente hochladen", accept_multiple_files=True, type="pdf")
            if up:
                if st.button("In Akte speichern"):
                    for f in up:
                        with open(os.path.join(p_path, f.name), "wb") as o: o.write(f.getbuffer())
                    st.rerun()

            st.markdown("---")
            col_a, col_b = st.columns([2,1])
            with col_a:
                st.subheader("Bestehende Dokumente")
                docs = os.listdir(p_path)
                if not docs:
                    st.info("Noch keine Dokumente in dieser Akte.")
                else:
                    for d in docs:
                        st.code(d)
            with col_b:
                st.subheader("Projekt-Wissen")
                if st.button("📚 Wissen neu indexieren"):
                    with st.spinner("Projektwissen wird analysiert und indexiert..."):
                        index_project(p_path, p_id)
                    st.success("Projektwissen ist auf dem neuesten Stand!")
        
        with t2:
            st.subheader("Nachtrag zur Prüfung hochladen")
            nt = st.file_uploader("Nachtrag PDF", accept_multiple_files=True, type="pdf", label_visibility="collapsed")
            
            if st.button("🔥 KI-Prüfung starten", type="primary"):
                if not nt: 
                    st.warning("Bitte zuerst einen Nachtrag hochladen.")
                else:
                    # HIER: Der zweistufige Agenten-Prozess mit st.status visualisiert
                    with st.status("Starte KI-Analyse...", expanded=True) as status:
                        status.write("Agent 1 (Analyst): Untersucht den Nachtrag...")
                        time.sleep(1) # Nur für den Demo-Effekt
                        nt_text = "".join([read_pdf(f) for f in nt])
                        question_prompt = f"Du bist ein Analyst für TGA-Bauprojekte. Lies den Nachtrag, identifiziere die 3-5 Kernforderungen und formuliere für jede eine präzise Frage, um relevante Infos in den Projektunterlagen zu finden. Gib NUR die Liste der Fragen aus.\n\nNACHTRAG:{nt_text[:4000]}"
                        questions_response = ai_model.generate_content(question_prompt)
                        questions = questions_response.text.strip().split('\n')
                        status.update(label="Agent 1 (Analyst): Rechercheplan erstellt! ✅")
                        
                        status.write("Agent 2 (Gutachter): Sucht relevante Projektdaten...")
                        time.sleep(1) # Nur für den Demo-Effekt
                        final_ctx = ""
                        try:
                            collection = chroma.get_collection(p_id)
                            for q in questions:
                                if q.strip():
                                    res = collection.query(query_texts=[q], n_results=3)
                                    final_ctx += f"Recherche-Ergebnis für Frage '{q}':\n" + "\n".join(res["documents"][0]) + "\n\n---\n\n"
                        except Exception as e:
                            final_ctx = f"Fehler bei der Datenbeschaffung: {e}"
                        status.update(label="Agent 2 (Gutachter): Daten aus Projekt-Akte geladen! ✅")

                        status.write("Agent 2 (Gutachter): Erstellt den finalen Bericht...")
                        time.sleep(1) # Nur für den Demo-Effekt
                        report_prompt = f"SYSTEM: Du bist 'der TGAcode', ein KI-Gutachter für TGA-Bauprojekte (VOB). DEINE AUFGABE: Erstelle einen finalen Prüfbericht basierend auf dem Nachtrag und den Recherche-Ergebnissen. Halte dich exakt an die Gliederung (Zusammenfassung, VOB-Check, Technik/Preis-Check, Empfehlung) und nutze Markdown.\n\nDER ZU PRÜFENDE NACHTRAG:\n---\n{nt_text}\n---\n\nRECHERCHE-ERGEBNISSE AUS DER PROJEKT-AKTE:\n---\n{final_ctx}\n---"
                        st.session_state.report = ai_model.generate_content(report_prompt).text
                        status.update(label="Analyse abgeschlossen!", state="complete", expanded=False)

            if "report" in st.session_state:
                st.markdown("---")
                st.subheader("Ergebnis der KI-Prüfung")
                st.markdown(f"<div class='report-box'>{st.session_state.report}</div>", unsafe_allow_html=True)
                
                with st.expander("Anweisung zur Überarbeitung geben"):
                    instr = st.text_area("Deine Anweisung an die KI...", height=100)
                    if st.button("Bericht überarbeiten lassen"):
                        with st.spinner("Bericht wird überarbeitet..."):
                            refine_prompt = f"Bestehender Bericht:\n{st.session_state.report}\n\nAnweisung des Nutzers: {instr}\n\nBitte überarbeite den ursprünglichen Bericht sachlich und präzise gemäß der Anweisung. Behalte die ursprüngliche Markdown-Struktur bei."
                            st.session_state.report = ai_model.generate_content(refine_prompt).text
                        st.rerun()

if __name__ == "__main__":
    main()


