import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. IMPOSTAZIONI GRAFICHE DELLA PAGINA ---
st.set_page_config(page_title="Estrattore EAN", page_icon="📦", layout="wide")

# --- INTESTAZIONE GRAFICA CON BANNER CENTRATO ---
# Le 3 colonne servono a "schiacciare" il banner al centro. Proporzioni: 1 : 2 : 1
col_spazio_sx, col_banner, col_spazio_dx = st.columns([1, 2, 1])
with col_banner:
    st.image("imm.png", use_container_width=True)

st.title("📦 Estrattore Automazione: EAN & Quantità")
st.markdown("Carica un documento (PDF o Immagine) e il vostro Fabio Virtuale genererà istantaneamente il file formattato per il tuo gestionale.")
st.markdown("---")

# --- APRE LA CASSAFORTE SEGRETA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("🔒 Errore: Chiave API non trovata nei Secrets di Streamlit.")
    st.stop()

# --- FUNZIONE AUTO-SELEZIONE MODELLO ---
@st.cache_resource
def ottieni_modello():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5' in m.name:
                    return genai.GenerativeModel(m.name)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                return genai.GenerativeModel(m.name)
    except Exception as e:
        return None
    return genai.GenerativeModel('gemini-1.5-flash')

model = ottieni_modello()

# --- LAYOUT A DUE COLONNE (CARICAMENTO E RISULTATI) ---
col_sinistra, col_destra = st.columns(2)

with col_sinistra:
    st.subheader("📄 1. Carica il Documento")
    # Qui accettiamo sia immagini che PDF
    uploaded_file = st.file_uploader("Trascina qui un PDF, JPG o PNG", type=["jpg", "jpeg", "png", "pdf"])
    
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith('.pdf'):
            st.info(f"✅ Documento PDF caricato correttamente: **{uploaded_file.name}**")
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Anteprima del documento", use_container_width=True)

with col_destra:
    st.subheader("⚡ 2. Estrazione Dati")
    
    if uploaded_file is None:
        st.info("👈 Inizia caricando un documento nella colonna di sinistra.")
    else:
        if st.button("🚀 Avvia Estrazione", type="primary", use_container_width=True):
            if model is None:
                st.error("Errore critico: Nessun modello AI disponibile.")
            else:
                with st.spinner("🤖 L'IA sta leggendo il documento... attendi qualche secondo."):
                    
                    # --- IL CERVELLO DELL'IA ---
                   prompt = """
                    Sei un estrattore di dati professionale. Guarda questo documento.
                    Contiene codici a barre (EAN o interni) e le relative quantità.
                    
                    ISTRUZIONI TASSATIVE:
                    1. Estrai tutte le coppie: Codice e Quantità.
                    2. Scrivi una coppia per riga usando il separatore | (es: 8058664165889|4.00, 12345678|2.00, 123456789|1.00)
                    3. Correggi eventuali errori visivi (es. la stanghetta del cursore letta come '1' all'inizio del codice).
                    4. LUNGHEZZA CODICI: I codici validi possono avere 8, 9 o 13 cifre. Estraili tutti mantenendo la loro lunghezza originale. SOLO se trovi un codice anomalo di 14 o 15 cifre (solitamente causato da un errore di lettura del cursore), rimuovi i numeri in eccesso all'inizio per riportarlo a 13 cifre.
                    5. Le quantità devono usare il PUNTO per i decimali (es. 10.00). Se la quantità è un numero intero (es. 4) scrivi 4.00.
                    6. RESTITUISCI SOLO LA LISTA, nessuna frase introduttiva.
                    """
                    
                    try:
                        # Riconosce se passare il PDF o l'immagine a Gemini
                        if uploaded_file.name.lower().endswith('.pdf'):
                            document_part = {
                                "mime_type": "application/pdf",
                                "data": uploaded_file.getvalue()
                            }
                            input_dati = [prompt, document_part]
                        else:
                            input_dati = [prompt, image]
                            
                        response = model.generate_content(input_dati)
                        risultato = response.text.strip()
                        risultato = risultato.replace("```text", "").replace("```", "").strip()
                        
                        st.success("✅ Estrazione completata con successo!")
                        
                        st.text_area("Anteprima Dati Estratti:", value=risultato, height=350)
                        
                        st.download_button(
                            label="📥 Scarica File TXT Pronto",
                            data=risultato,
                            file_name="ean_quantita.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Si è verificato un errore durante l'estrazione: {e}")
