import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer

# --- DESIGN: moderner Look ---
st.set_page_config(page_title="der TGAcode", layout="wide")
st.markdown("""
<style>
.top-nav { background-color: #1a1c24; padding: 20px; color: white; border-bottom: 4px solid #00f2fe; margin-bottom: 30px; border-radius: 0 0 8px 8px; }
.logo { font-size: 28px; font-weight: 800; }
.accent { color: #00f2fe; }
.report-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-top: 15px; }
.stButton>button { background: #1a1c24; color: #00f2fe; border: 1px solid #00f2fe; width: 100%; font-weight: bold; padding: 10px 0; }
.stButton>button:hover { background: #00f2fe; color: #1a1c24; }
.chat-box { background-color: #e2e8f0; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
</style>
<div class="top-nav"><div class="logo">der <span class="accent">TGAcode</span></div></div>
""", unsafe_allow_html=True)

# --- API & Modell ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("API Key fehlt in Streamlit Secrets!")
    st.stop()

genai.configure(api_key=api_key)

def init_ai_model():
    models = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-1.5-flash"]
    for m in models:
        try:
            model = genai.GenerativeModel(m)
            model.generate_content("ping", generation_config={"max_output_tokens": 1})
            return model
        except:
            continue
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

# --- PDF Logik ---
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
                col.add(ids=[f"{f}_{i}" for i in range(len(chunks))],
                        documents=chunks,
                        embeddings=[embedder.encode(c).tolist() for c in chunks])

# --- MAIN APP ---
def main():
    c1, c2, c3 = st.columns(3)
    firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]

    with c1:
        sel_f = st.selectbox("Firma", ["--"] + firmen)
        with st.expander("Firma anlegen"):
            nf = st.text_input("Name")
            if st.button("Anlegen", key="f"):
                os.makedirs(os.path.join(VAULT, nf), exist_ok=True)
                st.rerun()

    sel_p = "--"
    if sel_f != "--":
        projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        with c2:
            sel_p = st.selectbox("Projekt", ["--"] + projekte)
            with st.expander("Projekt anlegen"):
                np = st.text_input("Projekt")
                if st.button("Anlegen", key="p"):
                    os.makedirs(os.path.join(VAULT, sel_f, np), exist_ok=True)
                    st.rerun()

    if sel_p != "--":
        p_path = os.path.join(VAULT, sel_f, sel_p)
        p_id = f"{sel_f}_{sel_p}".replace(" ", "_")
        t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Prüfung"])

        # ---------------- Projekt-Akte
        with t1:
            up = st.file_uploader("Upload", accept_multiple_files=True)
            ca, cb = st.columns(2)
            if ca.button("Speichern"):
                for f in up:
                    with open(os.path.join(p_path, f.name), "wb") as o:
                        o.write(f.getbuffer())
                st.success("Dokumente gespeichert")
                st.rerun()
            if cb.button("📚 Wissen indexieren"):
                index_project(p_path, p_id)
                st.success("Projektwissen bereit")

            for d in os.listdir(p_path):
                cx, cy = st.columns([0.9, 0.1])
                cx.code(d)
                if cy.button("X", key=d): os.remove(os.path.join(p_path, d)); st.rerun()

        # ---------------- Nachtragsprüfung
        with t2:
            nt = st.file_uploader("Nachtrag PDF", accept_multiple_files=True)
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            if st.button("🔥 Prüfung starten"):
                if not nt: st.warning("Bitte Nachtrag hochladen.")
                else:
                    with st.spinner("Der TGAcode analysiert..."):
                        nt_text = "".join([read_pdf(f) for f in nt])
                        ctx = ""
                        try:
                            res = chroma.get_collection(p_id).query(
                                query_embeddings=[embedder.encode(nt_text[:500]).tolist()],
                                n_results=5
                            )
                            ctx = "\n".join(res["documents"][0])
                        except: ctx = "Kein Kontext vorhanden."
                        prompt = f"SYSTEM: Du bist 'der TGAcode'. Analysiere streng sachlich.\nKONTEXT:\n{ctx}\nNACHTRAG:\n{nt_text}\nSTRUKTUR: VOB-Check, Preis-Check, Empfehlung."
                        report = ai_model.generate_content(prompt).text
                        st.session_state.chat_history.append({"role": "system", "content": report})
                        st.session_state.current_report = report

            # ---------------- Chat Input
            st.markdown("<h4>💬 Chat mit TGAcode</h4>", unsafe_allow_html=True)
            instr = st.chat_input("Anweisung an die TGAcode...")
            if instr:
                # Neuer Prompt kombiniert bisherigen Bericht + neue Instruktion
                combined_prompt = f"Bericht:\n{st.session_state.current_report}\n\nAnweisung: {instr}\nÜberarbeite sachlich und vollständig."
                response = ai_model.generate_content(combined_prompt).text
                st.session_state.chat_history.append({"role": "user", "content": instr})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.session_state.current_report = response
                st.rerun()

            # ---------------- Chat anzeigen
            for msg in st.session_state.chat_history[-10:]:
                role = msg["role"]
                content = msg["content"]
                box_class = "chat-box" if role == "assistant" else "report-box"
                st.markdown(f"<div class='{box_class}'><b>{role.upper()}:</b> {content}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
