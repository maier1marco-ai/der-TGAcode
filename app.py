# ==============================================================================
# 1. IMPORTE
# Alle benötigten Bibliotheken werden hier geladen.
# ==============================================================================
import streamlit as st
import os
import time
import json
from io import BytesIO

# Versuche, die Bibliotheken zu importieren und gib eine klare Fehlermeldung, falls sie fehlen
try:
    from PyPDF2 import PdfReader
    import google.generativeai as genai
    import chromadb
    from sentence_transformers import SentenceTransformer
    import openpyxl
except ImportError as e:
    st.error(f"Eine benötigte Bibliothek fehlt: {e}. Bitte stelle sicher, dass deine requirements.txt-Datei korrekt ist und alle Pakete enthält (streamlit, PyPDF2, google-generativeai, chromadb, sentence-transformers, openpyxl).")
    st.stop()


# ==============================================================================
# 2. KONFIGURATION & GLOBALE VARIABLEN
# Alle "Einstellungen" und globalen Variablen werden hier EINMAL definiert.
# ==============================================================================

# Der Name des Hauptordners für alle Projektdaten
VAULT = "vault_tgacode"

# Erstelle den Hauptordner, falls er nicht existiert
# Wichtiger Hinweis: In der Streamlit Cloud ist dies nur temporär!
try:
    os.makedirs(VAULT, exist_ok=True)
except Exception as e:
    st.error(f"Konnte das Verzeichnis '{VAULT}' nicht erstellen. Fehler: {e}")
    st.stop()

# Konfiguriere den Google Gemini API Key aus den Streamlit Secrets
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
# Diese Funktionen und Modelle werden von der Haupt-App verwendet.
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

# Lade die KI-Modelle und den ChromaDB-Client beim Start der App
ai_model = init_ai_model()
embedder = get_embedder()
chroma = chromadb.Client()

if not ai_model:
    st.error("Kein unterstütztes Gemini-Modell gefunden oder konnte nicht initialisiert werden.")
    st.stop()

def read_pdf(file):
    #... (Diese Funktion bleibt unverändert)
    text = ""
    try:
        reader = PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    except: pass
    return text

def index_project(path, p_id):
    #... (Diese Funktion bleibt unverändert)
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
# Diese Funktion wird ganz am Ende aufgerufen und zeichnet die App-Oberfläche.
# ==============================================================================
def main():
    st.title("UPDATE-TEST - VERSION 123 - HAT GEKLAPPT!") # <--- DIESE ZEILE EINFÜGEN
    
    # Der Rest deiner main() Funktion beginnt hier
    st.header("Projektauswahl")
    # ... usw.

    # Setze das Seiten-Design (CSS)
    st.markdown("""<style>...</style><div class="top-nav">...</div>""", unsafe_allow_html=True) # Gekürzt

    st.header("Projektauswahl")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        # Dieser Aufruf wird jetzt funktionieren, da VAULT global definiert ist
        firmen = [f for f in os.listdir(VAULT) if os.path.isdir(os.path.join(VAULT, f))]
        sel_f = st.selectbox("Firma auswählen", ["--"] + firmen, label_visibility="collapsed")
        
        projekte = []
        if sel_f != "--":
            projekte = [p for p in os.listdir(os.path.join(VAULT, sel_f))]
        sel_p = st.selectbox("Projekt auswählen", ["--"] + projekte, label_visibility="collapsed")

    # ... (Der Rest deiner main()-Funktion folgt hier, exakt wie im vorherigen Code)
    # ... z.B. das Erstellen neuer Firmen/Projekte, die Tabs für "Projekt-Akte" und "Nachtrags-Prüfung", etc.
    # Dieser Teil ist unverändert, ich kürze ihn hier zur besseren Übersicht.

    if sel_f != "--" and sel_p != "--":
        p_path = os.path.join(VAULT, sel_f, sel_p)
        p_id = f"{sel_f}_{sel_p}".replace(" ", "_")
        
        st.header(f"Projekt-Dashboard: {sel_p}")
        t1, t2 = st.tabs(["📁 Projekt-Akte", "🚀 Nachtrags-Prüfung"])

        with t1:
            # ... Logik der Projekt-Akte ...
            pass
        
        with t2:
            # ... Logik der Nachtrags-Prüfung ...
            pass


# ==============================================================================
# 5. STARTPUNKT DES SCRIPTS
# Wenn das Skript direkt ausgeführt wird, rufe die main()-Funktion auf.
# ==============================================================================
if __name__ == "__main__":
    main()


