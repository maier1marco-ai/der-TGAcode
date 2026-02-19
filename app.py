# ==============================================================================
# 1. IMPORTE
# ==============================================================================
import streamlit as st
import os
import time
import json
from io import BytesIO

try:
    from PyPDF2 import PdfReader
    import google.generativeai as genai
    import chromadb
    from sentence_transformers import SentenceTransformer
    import openpyxl
except ImportError as e:
    st.error(f"Eine benötigte Bibliothek fehlt: {e}. Bitte stelle sicher, dass deine requirements.txt-Datei korrekt ist und alle Pakete enthält.")
    st.stop()


# ==============================================================================
# 2. KONFIGURATION & GLOBALE VARIABLEN
# ==============================================================================
VAULT = "vault_tgacode"

try:
    os.makedirs(VAULT, exist_ok=True)
except Exception as e:
    st.error(f"Konnte das Verzeichnis '{VAULT}' nicht erstellen. Fehler: {e}")
    st.stop()

try:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY nicht in Streamlit Secrets gefunden.")
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Fehler bei der Konfiguration des Gemini API Keys: {e}")
    st.stop()


# ==============================================================================
# 3. HELFERFUNKTIONEN & MODELLE LADEN
# ==============================================================================

@st.cache_resource
def init_ai_model():
    """Lädt und testet das Gemini-Modell."""
    model_candidates = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-1.5-flash"]
    for m in model_candidates:
        try:
            model = genai.GenerativeModel(m)
            model.generate_content("ping", generation_config={"max_output_tokens": 1})
            return model
        except Exception:
            continue
    return None

@st.cache_resource
def get_embedder():
    """Lädt das Sentence-Transformer-Modell für die Vektorisierung."""
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        st.error(f"Fehler beim Laden des Embedding-Modells: {e}")
        st.stop()

ai_model = init_ai_model()
embedder = get_embedder()
chroma = chromadb.Client()

if not ai_model:
    st.error("Kein unterstütztes Gemini-Modell gefunden oder konnte nicht initialisiert werden.")
    st.stop()

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


# ==============================================================================
# 4. HAUPTFUNKTION (DIE STREAMLIT APP-LOGIK)
# ==============================================================================
def main():
    st.markdown("""
    <style>
        body { color: #fafafa; background-color: #0d1117; } .stApp { background-color: #0d1117; } .st-emotion-cache-18ni7ap { background: #161b22; } .st-emotion-cache-16txtl3 { padding: 2rem 2rem; } h1, h2, h3 { color: #c9d1d9; } .top-nav { background-color: #161b22; padding: 1rem 2rem; border-bottom: 2px solid #00f2fe; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; } .logo { font-size: 26px; font-weight: 800; color: #f0f6fc; } .accent { color: #00f2fe; } .stButton>button { background: linear-gradient(45deg, #00f2fe, #2c7fff); color: white; border: none; width: 100%; font-weight: bold; padding: 10px 0; border-radius: 8px; transition: transform 0.1s ease-in-out; } .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #00f2fe; } .report-box { background-color: #161b22; padding: 25px; border-radius: 10px; border: 1px solid #30363d; line-height: 1.6; } .report-box h1, .report-box h3 { border-bottom: 1px solid #30363d; padding-bottom: 8px; }
    </style>
    <div class="top-nav">
        <div class="logo">der <span class="accent">TGAcode</span></div>
        <div style="color: #8b949e;">AI-Powered Project Analysis</div>
    </div>
    """, unsafe_allow_html=True)

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
            
            stammdaten_input = st.text_area("Hier können permanente Regeln für dieses Projekt hinterlegt werden.", value=current_stammdaten, height=150)
            if st.button("Stammdaten speichern"):
                with open(stammdaten_path, "w", encoding="utf-8") as f:
                    f.write(stammdaten_input)
                st.success("Stammdaten wurden gespeichert!")
            
            st.markdown("---")
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
                docs = [d for d in os.listdir(p_path) if not d.startswith("_")]
                if not docs: st.info("Noch keine Dokumente in dieser Akte.")
                else: 
                    for d in docs: st.code(d)
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
                    with st.status("Starte KI-Analyse...", expanded=True) as status:
                        status.write("Agent 1 (Analyst): Untersucht den Nachtrag...")
                        time.sleep(1)
                        nt_text = "".join([read_pdf(f) for f in nt])
                        question_prompt = f"Du bist ein Analyst für TGA-Bauprojekte. Lies den Nachtrag, identifiziere die 3-5 Kernforderungen und formuliere für jede eine präzise Frage, um relevante Infos in den Projektunterlagen zu finden. Gib NUR die Liste der Fragen aus.\n\nNACHTRAG:{nt_text[:4000]}"
                        questions_response = ai_model.generate_content(question_prompt)
                        questions = questions_response.text.strip().split('\n')
                        status.update(label="Agent 1 (Analyst): Rechercheplan erstellt! ✅")
                        
                        status.write("Agent 2 (Gutachter): Sucht relevante Projektdaten...")
                        time.sleep(1)
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
                        time.sleep(1)
                        stammdaten_text = ""
                        stammdaten_path = os.path.join(p_path, "_projekt_stammdaten.txt")
                        if os.path.exists(stammdaten_path):
                            with open(stammdaten_path, "r", encoding="utf-8") as f:
                                stammdaten_text = f.read()

                        report_prompt = f"""
                        SYSTEM: Du bist 'der TGAcode', ein KI-Gutachter für TGA-Bauprojekte (VOB).
                        DEINE AUFGABE: Erstelle einen finalen Prüfbericht und eine JSON-Zusammenfassung.
                        DIR LIEGEN FOLGENDE DOKUMENTE VOR:
                        1. PROJEKT-STAMMDATEN (HÖCHSTE PRIORITÄT): {stammdaten_text}
                        2. DER ZU PRÜFENDE NACHTRAG: {nt_text}
                        3. RECHERCHE-ERGEBNISSE AUS DER PROJEKT-AKTE: {final_ctx}
                        ANWEISUNG:
                        1. Erstelle einen strukturierten Prüfbericht im Markdown-Format (Zusammenfassung, VOB-Check, Technik/Preis-Check, Empfehlung).
                        2. Füge ANSCHLIESSEND einen sauberen JSON-Codeblock an mit den Schlüsseln: "vob_check", "technische_prüfung", "preis_check", "gesamtsumme_korrigiert", "empfehlung", "naechste_schritte".
                        Beispiel für den JSON-Block am Ende:
                        ```json
                        {{
                            "vob_check": "OK", "technische_prüfung": "Prüfung nötig", "preis_check": "Auffällig", "gesamtsumme_korrigiert": "ca. 1.230,00 EUR", "empfehlung": "Verhandlung empfohlen", "naechste_schritte": "Preis für Position 3.2 anfechten"
                        }}
                        ```
                        """
                        st.session_state.report = ai_model.generate_content(report_prompt).text
                        status.update(label="Analyse abgeschlossen!", state="complete", expanded=False)

            if "report" in st.session_state:
                st.markdown("---")
                st.subheader("Ergebnis der KI-Prüfung")
                st.markdown(f"<div class='report-box'>{st.session_state.report.split('```json')[0]}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("Deckblatt aus Excel-Vorlage erstellen")
                template_file = st.file_uploader("Lade deine Deckblatt-Vorlage hoch (.xlsx)", type=["xlsx"])
                if template_file is not None:
                    try:
                        json_part = st.session_state.report.split('```json')[1].split('```')[0]
                        report_data = json.loads(json_part)
                        workbook = openpyxl.load_workbook(template_file)
                        sheet = workbook.active
                        for row in sheet.iter_rows():
                            for cell in row:
                                if cell.value and isinstance(cell.value, str):
                                    placeholder_keys = {f"[{k.upper()}]": v for k, v in report_data.items()}
                                    if cell.value in placeholder_keys:
                                        cell.value = placeholder_keys[cell.value]
                        output_stream = BytesIO()
                        workbook.save(output_stream)
                        output_stream.seek(0)
                        st.success("Excel-Vorlage erfolgreich befüllt!")
                        st.download_button(label="✅ Fertiges Deckblatt herunterladen", data=output_stream, file_name=f"Deckblatt_{sel_p}_{template_file.name}", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except Exception as e:
                        st.error(f"Fehler beim Verarbeiten der Excel-Vorlage: {e}")

# ==============================================================================
# 5. STARTPUNKT DES SCRIPTS
# ==============================================================================
if __name__ == "__main__":
    main()
