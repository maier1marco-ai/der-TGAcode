import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# --- 1. DESIGN & BRANDING (Futuristic UI) ---
st.set_page_config(page_title="der TGAcode", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Hintergrund und Grundfarben */
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* Buttons: Neon-Gradient */
    .stButton>button { 
        background: linear-gradient(45deg, #00f2fe 0%, #4facfe 100%); 
        color: white; border: none; border-radius: 10px;
        padding: 10px 25px; font-weight: bold; transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0px 0px 15px #00f2fe; }
    
    /* Eingabefelder */
    .stTextInput>div>div>input { background-color: #1a1c24; color: white; border: 1px solid #4facfe; }
    
    /* Titel-Styling */
    h1 { color: #00f2fe; font-family: 'Helvetica Neue', sans-serif; letter-spacing: 2px; text-transform: uppercase; text-shadow: 0 0 10px rgba(0,242,254,0.5); }
    
    /* Karten-Design für Uploads und Ergebnisse */
    .report-card { 
        background: rgba(255, 255, 255, 0.03); 
        backdrop-filter: blur(10px); 
        border-radius: 15px; padding: 25px; 
        border: 1px solid rgba(0, 242, 254, 0.2);
        margin-bottom: 20px;
    }
    
    /* Sidebar Styling */
    .css-163ttbj { background-color: #1a1c24; border-right: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTIFIZIERUNG ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br><center><h1>der TGAcode</h1><p>ENGINEERING REVISION SYSTEM</p></center>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        pw = st.text_input("System-Key (Passwort)", type="password")
        if st.button("SYSTEM INITIALISIEREN"):
            if pw == "TGAPRO": # <--- Dein Passwort
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Key ungültig.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 3. GEMINI KI-INITIALISIERUNG (Auto-Detection Modus) ---
api_key_env = st.secrets.get("GEMINI_API_KEY")

if not api_key_env:
    api_key_env = st.sidebar.text_input("Gemini API Key manuell eingeben", type="password")

if api_key_env:
    try:
        genai.configure(api_key=api_key_env)
        
        # Wir listen alle verfügbaren Modelle auf und suchen nach einem Flash-Modell
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Bevorzugte Modelle in dieser Reihenfolge
        choices = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']
        
        selected_model = None
        for choice in choices:
            if choice in available_models:
                selected_model = choice
                break
        
        if not selected_model:
            # Falls keins der Liste gefunden wurde, nimm das erste verfügbare
            selected_model = available_models[0]
            
        model = genai.GenerativeModel(selected_model)
        st.sidebar.success(f"Aktiv: {selected_model}") # Zeigt dir in der Sidebar, was er gefunden hat
        
    except Exception as e:
        st.error(f"Verbindungsfehler zur Google API: {e}")
        st.info("Tipp: Prüfe, ob dein API-Key im Google AI Studio wirklich 'Active' ist.")
        st.stop()
else:
    st.warning("⚠️ Bitte Gemini API Key in den Streamlit Secrets hinterlegen.")
    st.stop()

# --- 4. PROJEKT-ARCHIV (Sidebar) ---
st.sidebar.markdown("<h1>der TGAcode</h1>", unsafe_allow_html=True)
firma = st.sidebar.text_input("🏢 Firma", "Beispiel_Firma")
projekt = st.sidebar.text_input("📂 Projekt", "Projekt_01")

# Pfad-Logik
base_path = f"data/{firma}/{projekt}"
os.makedirs(base_path, exist_ok=True)
lv_storage = os.path.join(base_path, "basis_lv.txt")

st.sidebar.divider()
st.sidebar.subheader("Vertrags-Basis (LV)")
lv_file = st.sidebar.file_uploader("LV hochladen", type="pdf", key="lv_up")

if lv_file and st.sidebar.button("IM ARCHIV SICHERN"):
    with st.spinner("Speichere LV..."):
        text = "".join([p.extract_text() for p in PdfReader(lv_file).pages])
        with open(lv_storage, "w", encoding="utf-8") as f:
            f.write(text)
        st.sidebar.success("Projekt-Wissen gesichert.")

# --- 5. HAUPT-DASHBOARD ---
st.markdown(f"<h1>Revision: {projekt}</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("📄 Nachtrags-Dokument")
    nt_file = st.file_uploader("Nachtrag zur Prüfung (Temporär)", type="pdf")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("📎 Anlagen")
    an_files = st.file_uploader("Kalkulationen / Nachweise", type="pdf", accept_multiple_files=True)
    st.markdown('</div>', unsafe_allow_html=True)

if nt_file and os.path.exists(lv_storage):
    if st.button("🚀 FULL AUDIT STARTEN"):
        with st.spinner("KI führt Deep-Analysis durch..."):
            # Daten lesen
            with open(lv_storage, "r", encoding="utf-8") as f:
                lv_data = f.read()
            nt_data = "".join([p.extract_text() for p in PdfReader(nt_file).pages])
            at_data = "".join(["".join([p.extract_text() for p in PdfReader(a).pages]) for a in an_files])

            prompt = f"""
            DU BIST TGA-REVISOR. ARBEITE STRENG NACH VOB UND HOAI LP 08.
            AUFGABE: Vergleiche den Nachtrag mit dem LV.
            
            PRÜFSCHRITTE:
            1. VOLLSTÄNDIGKEIT: Fehlen Dokumente (Kalkulation, Aufmaß)?
            2. ANSPRUCH: Ist die Leistung im LV enthalten? (LV-Pos nennen). Wenn nein: Zusatzleistung?
            3. PREIS-CHECK: Vergleiche EP Nachtrag mit EP LV. Berechne Abweichung (€ / %).
            4. KALKULATION: Ist die Preisfortschreibung im Anhang plausibel?
            
            LV-BASIS: {lv_data[:12000]}
            NACHTRAG: {nt_data[:5000]}
            ANHÄNGE: {at_data[:4000]}
            
            AUSGABE: Erstelle eine Tabelle (Pos | Status | Feststellung | VOB-Begründung | Empfehlung).
            Fasse die Gesamtkosten-Differenz am Ende kurz zusammen.
            """
            
            response = model.generate_content(prompt)
            st.session_state.audit_text = response.text

    if "audit_text" in st.session_state:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.audit_text)
        st.markdown('</div>', unsafe_allow_html=True)

       # --- 6. DER UNIVERSELLE TGA-CHAT ---
        st.divider()
        st.subheader("🤖 der TGAcode | Projekt-Dialog")
        st.info("Hier kannst du Dokumente entwerfen, Logik prüfen oder VOB-Strategien besprechen.")

        # Chat-Historie initialisieren
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Anzeige der bisherigen Chatverläufe
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Benutzereingabe
        user_input = st.chat_input("Frag mich etwas zum Projekt...")

        if user_input:
            # User-Nachricht anzeigen & speichern
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Antwort generieren mit vollem Kontext
            with st.chat_message("assistant"):
                with st.spinner("Denke nach..."):
                    # Wir geben der KI ALLES: Audit-Bericht + deine Frage
                    full_context = f"""
                    Du bist der leitende TGA-Experte für das Projekt {projekt}.
                    Hier ist der aktuelle Revisionsbericht:
                    {st.session_state.audit_text}
                    
                    Nutze diesen Bericht und dein gesamtes Wissen über VOB, HOAI und TGA-Normen, 
                    um die folgende Nutzeranfrage zu beantworten oder Dokumente zu erstellen:
                    {user_input}
                    """
                    
                    response = model.generate_content(full_context)
                    st.markdown(response.text)
            
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})



