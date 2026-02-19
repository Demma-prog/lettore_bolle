import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. IMPOSTAZIONI GRAFICHE DELLA PAGINA ---
# layout="wide" usa tutto lo schermo del monitor, molto meglio per i PC dell'ufficio!
st.set_page_config(page_title="Estrattore EAN", page_icon="📦", layout="wide")

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

# --- INTESTAZIONE GRAFICA ---
st.image("imm.png", use_container_width=True)
st.title("📦 Estrattore Automazione: EAN & Quantità")
st.markdown("Carica un documento (PDF o Immagine) e il vostro Fabio Virtuale genererà istantaneamente il file formattato per il tuo gestionale.")
st.markdown("---") # Riga di separazione elegante

# --- LAYOUT A DUE COLONNE ---
col_sinistra, col_destra = st.columns(2)

with col_sinistra:
    st.subheader("📄 1. Carica il Documento")
    # Ora accettiamo anche i PDF!
    uploaded_file = st.file_uploader("Trascina qui un PDF, JPG o PNG", type=["jpg", "jpeg", "png", "pdf"])
    
    if uploaded_file is not None:
        # Mostriamo l'anteprima solo se è un'immagine (i PDF sono pesanti da visualizzare)
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
        # Pulsante più grande e colorato
        if st.button("🚀 Avvia Estrazione", type="primary", use_container_width=True):
            if model is None:
                st.error("Errore critico: Nessun modello AI disponibile.")
            else:
                with st.spinner("🤖 L'IA sta leggendo il documento... attendi qualche secondo."):
                    
                    prompt = """
                    Sei un estrattore di dati professionale. Guarda questo documento.
                    Contiene codici EAN (codici a barre) e le relative quantità.
                    
                    ISTRUZIONI TASSATIVE:
                    1. Estrai tutte le coppie: Codice EAN (13 cifre) e Quantità.
                    2. Scrivi una coppia per riga usando il separatore | (es: 8058664165889|4.00)
                    3. Correggi eventuali errori visivi (es. la stanghetta del cursore letta come '1').
                    4. I codici EAN devono essere lunghi ESATTAMENTE 13 cifre. Se sono più lunghi, taglia l'inizio.
                    5. Le quantità devono usare il PUNTO per i decimali (es. 10.00). Se la quantità è un numero intero (es. 4) scrivi 4.00.
                    6. RESTITUISCI SOLO LA LISTA, nessuna frase introduttiva.
                    """
                    
                    try:
                        # Prepariamo i dati in base a se è PDF o Immagine
                        if uploaded_file.name.lower().endswith('.pdf'):
                            # Gemini sa leggere i PDF se gli passiamo i dati grezzi in questo modo:
                            document_part = {
                                "mime_type": "application/pdf",
                                "data": uploaded_file.getvalue()
                            }
                            input_dati = [prompt, document_part]
                        else:
                            input_dati = [prompt, image]
                            
                        # Chiamata all'IA
                        response = model.generate_content(input_dati)
                        risultato = response.text.strip()
                        risultato = risultato.replace("```text", "").replace("```", "").strip()
                        
                        st.success("✅ Estrazione completata con successo!")
                        
                        # Mostriamo il risultato in un bel riquadro
                        st.text_area("Anteprima Dati Estratti:", value=risultato, height=350)
                        
                        # Pulsante di download
                        st.download_button(
                            label="📥 Scarica File TXT Pronto",
                            data=risultato,
                            file_name="ean_quantita.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Si è verificato un errore durante l'estrazione: {e}")
