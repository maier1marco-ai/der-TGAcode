import streamlit as st
import os
from PyPDF2 import PdfReader
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer

# --- DESIGN: der TGAcode ---
st.set_page_config(page_title="der TGAcode", layout="wide")
st.markdown("""
<style>
.top-nav { background-color: #1a1c24; padding: 20px; color: white; border-bottom: 4px solid #00f2fe; margin-bottom: 30px; }
.logo { font-size: 26px; font-weight: 800; }
.accent { color: #00f2fe; }
.report-box { background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }
.stButton>button { background: #1a1c24; color: #00f2fe; border: 1px solid #00f2fe; width: 100%; font-weight: bold; }
</style>
<div class="top-nav"><div class="logo">der <span class="accent">TGAcode</span></div></div>
""", unsafe_allow_html=True)

# --- API & MODELL-WAHL (Update Feb 2026) ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("API Key fehlt in Streamlit Secrets!")
    st.stop()

genai.configure(api_key=api_key)

def init_ai_model():
    # Wir nutzen 2026 die stabilen Versionen der 2.5er und 3er Serie
    model_candidates = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-1.5-flash"]
    for m in model_candidates:
        try:
            model = genai.GenerativeModel(m)
            # Kurztest
            model.generate_content("ping", generation_config={"max_output_tokens": 1})
            return model
        except:
            continue
    return None

ai_model = init_ai_model()
if not ai_model:
    st.error("Kein unterstütztes Modell gefunden. Bitte 'gemini-2.5-flash' in Google AI Studio freischalten.")
    st.stop()

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
            words = text.split()
            chunks = [" ".join(words[i:i+400]) for i in range(0, len(words), 400)]
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
            if cb.button("📚 Wissen indexieren"):
                with st.spinner("Projektwissen wird indexiert..."):
                    index_project(p_path, p_id)
                st.success("Projektwissen bereit!")
            
            st.markdown("---")
            st.subheader("Dokumente in der Akte")
            for d in os.listdir(p_path):
                cx, cy = st.columns([0.9, 0.1])
                cx.code(d)
                if cy.button("❌", key=d, help=f"Löscht die Datei {d}"): 
                    os.remove(os.path.join(p_path, d))
                    st.rerun()

        with t2:
            nt = st.file_uploader("Nachtrag PDF zur Prüfung hochladen", accept_multiple_files=True)
            if st.button("🔥 Prüfung starten"):
                if not nt: 
                    st.warning("Bitte zuerst einen Nachtrag hochladen.")
                else:
                    # ==== NEUE, VERBESSERTE ANALYSE-LOGIK ====
                    
                    # STUFE 1: Nachtrag verstehen und Schlüsselfragen generieren
                    with st.spinner("der TGAcode analysiert... (Stufe 1/2: Nachtrag verstehen)"):
                        nt_text = "".join([read_pdf(f) for f in nt])

                        question_prompt = f"""
                        Du bist ein Analyst für TGA-Bauprojekte. Lies den folgenden Nachtrag.
                        Identifiziere die 3-5 wichtigsten Kernpunkte oder Forderungen (z.B. neue Positionen, geänderte Mengen, neue Preise).
                        Formuliere für jeden Kernpunkt eine präzise, eigenständige Frage, um im ursprünglichen Leistungsverzeichnis oder den Projektunterlagen relevante Informationen zu finden.
                        Gib NUR die Liste der Fragen aus.

                        NACHTRAG:
                        {nt_text[:4000]}
                        """
                        final_ctx = ""
                        try:
                            # Generiere die Schlüsselfragen basierend auf dem Nachtrag
                            questions_response = ai_model.generate_content(question_prompt)
                            questions = questions_response.text.strip().split('\n')
                            
                            st.info(f"Folgende Fragen werden an die Projekt-Akte gestellt:\n{questions_response.text}")
                            
                            st.spinner("der TGAcode analysiert... (Stufe 2/2: Kontext suchen & Bericht erstellen)")
                            collection = chroma.get_collection(p_id)
                            
                            # Für jede Frage, suche den relevanten Kontext in der Vektordatenbank
                            for q in questions:
                                if q.strip():
                                    res = collection.query(query_texts=[q], n_results=3)
                                    final_ctx += f"Frage: {q}\nKontext:\n" + "\n".join(res["documents"][0]) + "\n\n---\n\n"

                        except Exception as e:
                            st.error(f"Fehler bei der Kontextsuche: {e}. Nutze Fallback-Methode.")
                            try:
                                # Fallback zur alten Methode, falls die Fragengenerierung fehlschlägt
                                res = chroma.get_collection(p_id).query(query_embeddings=[embedder.encode(nt_text[:500]).tolist()], n_results=5)
                                final_ctx = "\n".join(res["documents"][0])
                            except:
                                final_ctx = "Kein Kontext für die Analyse vorhanden."
                        
                    # STUFE 2: Finalen Bericht mit strukturiertem Prompt und reichem Kontext generieren
                    with st.spinner("Bericht wird erstellt..."):
                        report_prompt = f"""
                        SYSTEM: Du bist 'der TGAcode', ein hochpräziser KI-Assistent für die Analyse von Bauprojekten, spezialisiert auf deutsche TGA-Projekte und die VOB.
                        Deine Aufgabe: Analysiere den folgenden Nachtrag objektiv und sachlich auf Basis des bereitgestellten Projekt-Kontexts.

                        PROJEKT-KONTEXT AUS DER PROJEKT-AKTE:
                        ---
                        {final_ctx}
                        ---

                        NACHTRAG (VOLLTEXT):
                        ---
                        {nt_text}
                        ---

                        ANWEISUNG: Erstelle einen detaillierten Prüfbericht. Nutze ausschließlich Markdown für die Formatierung. Halte dich exakt an die folgende Gliederung:

                        # Prüfbericht zum Nachtrag

                        ### **Zusammenfassung für das Management**
                        *   Fasse die wichtigsten Ergebnisse und deine Kernempfehlung in 3-4 prägnanten Stichpunkten zusammen.

                        ### **1. VOB/B-Konformitäts-Check**
                        *   Prüfe die formale und sachliche Grundlage des Nachtrags gemäß VOB/B.
                        *   Handelt es sich um eine berechtigte Forderung (z.B. geänderte Leistung nach § 2 Abs. 5, zusätzliche Leistung nach § 2 Abs. 6)?
                        *   Gibt es formale Mängel oder Auffälligkeiten?

                        ### **2. Technische Prüfung & Preis-Check**
                        *   Vergleiche die technischen Spezifikationen und Mengen im Nachtrag mit dem Projekt-Kontext. Gibt es Abweichungen?
                        *   Bewerte die angesetzten Preise. Sind sie marktüblich und angemessen? Hebe Positionen mit auffälligen Preisen hervor.
                        *   Beziehe dich, wenn möglich, direkt auf den bereitgestellten Kontext.

                        ### **3. Empfehlung & Nächste Schritte**
                        *   Gib eine klare Handlungsempfehlung: Annahme, Annahme unter Vorbehalt, Verhandlung oder Ablehnung.
                        *   Liste konkrete nächste Schritte auf (z.B. "Preisspiegel für Position X anfordern", "Technische Klärung für Bauteil Y mit Planer suchen").
                        """
                        st.session_state.report = ai_model.generate_content(report_prompt).text
                        st.success("Analyse abgeschlossen!")

            if "report" in st.session_state:
                st.markdown("---")
                st.markdown(st.session_state.report, unsafe_allow_html=True)
                
                st.markdown("---")
                instr = st.chat_input("Anweisung zur Überarbeitung des Berichts...")
                if instr:
                    with st.spinner("Bericht wird überarbeitet..."):
                        refine_prompt = f"Bestehender Bericht:\n{st.session_state.report}\n\nAnweisung des Nutzers: {instr}\n\nBitte überarbeite den ursprünglichen Bericht sachlich und präzise gemäß der Anweisung. Behalte die ursprüngliche Markdown-Struktur bei."
                        st.session_state.report = ai_model.generate_content(refine_prompt).text
                    st.rerun()

if __name__ == "__main__":
    main()
