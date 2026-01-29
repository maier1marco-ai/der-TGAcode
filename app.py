import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- KONFIGURATION & BRANDING ---
st.set_page_config(page_title="der TGAcode", layout="wide", initial_sidebar_state="expanded")

# Custom CSS für den futuristischen Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { 
        background: linear-gradient(45deg, #00f2fe 0%, #4facfe 100%); 
        color: white; border: none; border-radius: 10px;
        padding: 10px 25px; font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0px 0px 15px #00f2fe; }
    .stTextInput>div>div>input { background-color: #1a1c24; color: white; border: 1px solid #4facfe; }
    .css-163ttbj { background-color: #1a1c24; border-right: 1px solid #4facfe; }
    h1 { color: #00f2fe; font-family: 'Helvetica Neue', sans-serif; letter-spacing: 2px; text-transform: uppercase; }
    .report-card { 
        background: rgba(255, 255, 255, 0.05); 
        backdrop-filter: blur(10px); 
        border-radius: 15px; padding: 20px; 
        border: 1px solid rgba(0, 242, 254, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<center><h1>der TGAcode</h1></center>", unsafe_allow_html=True)
    with st.container():
        pw = st.text_input("System-Key eingeben", type="password")
        if st.button("INITIALISIEREN"):
            if pw == "TGAPRO": # Dein Passwort
                st.session_state.authenticated = True
                st.rerun()
    st.stop()

# --- GEMINI SETUP ---
# Den API Key kannst du später in den Streamlit-Secrets hinterlegen
API_KEY = st.sidebar.text_input("Gemini API Key", type="password")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- SIDEBAR & ARCHIV ---
st.sidebar.markdown("<h1>der TGAcode</h1>", unsafe_allow_html=True)
firma = st.sidebar.text_input("🏢 Firma", "Reiter MK2.2")
projekt = st.sidebar.text_input("📂 Projekt", "Isaria")

path = f"data/{firma}/{projekt}"
os.makedirs(path, exist_ok=True)
lv_path = f"{path}/contract.txt"

st.sidebar.divider()
st.sidebar.subheader("Vertrags-Basis")
lv_file = st.sidebar.file_uploader("LV hochladen", type="pdf")
if lv_file and st.sidebar.button("IM ARCHIV SPEICHERN"):
    text = "".join([p.extract_text() for p in PdfReader(lv_file).pages])
    with open(lv_path, "w", encoding="utf-8") as f:
        f.write(text)
    st.sidebar.success("Basis-Wissen gesichert.")

# --- MAIN INTERFACE ---
st.markdown(f"<h1>Revision: {projekt}</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    nt_file = st.file_uploader("Nachtrag (Temporäre Prüfung)", type="pdf")
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    an_files = st.file_uploader("Anhänge & Kalkulation", type="pdf", accept_multiple_files=True)
    st.markdown('</div>', unsafe_allow_html=True)

if nt_file and os.path.exists(lv_path):
    if st.button("🚀 FULL AUDIT STARTEN"):
        with st.spinner("Künstliche Intelligenz analysiert Preis- und Massenstrukturen..."):
            with open(lv_path, "r", encoding="utf-8") as f:
                lv_data = f.read()
            nt_data = "".join([p.extract_text() for p in PdfReader(nt_file).pages])
            at_data = "".join(["".join([p.extract_text() for p in PdfReader(a).pages]) for a in an_files])

            prompt = f"""
            SYSTEM: Du bist ein technischer Revisor für TGA. Arbeite streng, präzise und fachlich korrekt.
            AUFGABE: Vergleiche den Nachtrag mit dem LV. 
            
            CHECKLISTE (FÜHRE DIESE RECHNERISCH AUS):
            1. VOLLSTÄNDIGKEIT: Liste auf, welche Unterlagen fehlen (Kalkulation, Aufmaß).
            2. ANSPRUCHSPRÜFUNG: Prüfe jede Position des Nachtrags. Existiert sie im LV? (Nenne LV-Pos). Wenn nein: Neue Leistung?
            3. PREISPRÜFUNG: Vergleiche EP Nachtrag mit EP LV. Berechne die Abweichung in Euro und Prozent.
            4. VOB-BEWERTUNG: Ist die Preisfortschreibung nach VOB/B plausibel?
            
            KONTEXT LV: {lv_data[:12000]}
            NACHTRAG: {nt_data[:5000]}
            ANHÄNGE: {at_data[:4000]}
            
            AUSGABE: Erstelle eine saubere Markdown-Tabelle. Danach eine kurze Zusammenfassung der Gesamtsumme der Abweichungen.
            """
            
            response = model.generate_content(prompt)
            st.session_state.last_audit = response.text
            st.markdown(f'<div class="report-card">{st.session_state.last_audit}</div>', unsafe_allow_html=True)

# --- ASSISTANT ---
if "last_audit" in st.session_state:
    st.divider()
    st.subheader("🤖 KI-Assistent für Schriftverkehr")
    cmd = st.chat_input("Was soll ich formulieren? (z.B. Ablehnungsschreiben, Nachforderung von Unterlagen)")
    if cmd:
        with st.spinner("Formuliere fachliches Schreiben..."):
            res = model.generate_content(f"Bericht: {st.session_state.last_audit}\nBefehl: {cmd}\nStil: Hochprofessionell, Bauleiter-Stil, VOB-konform.")
            st.info(res.text)