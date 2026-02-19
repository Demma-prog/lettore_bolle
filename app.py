import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="Estrattore Listini", page_icon="📄")
st.title("Estrattore Codici a Barre e Prezzi 🚀")
st.write("Carica la foto o lo screenshot del listino. L'Intelligenza Artificiale estrarrà i dati formattati pronti per l'uso.")

# --- APRE LA CASSAFORTE SEGRETA ---
# Qui il codice va a leggere la chiave che hai salvato in "Secrets"
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("Errore: Non riesco a trovare la chiave. Assicurati di averla salvata nei Secrets di Streamlit come GEMINI_API_KEY = 'tua_chiave'")
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

# --- CARICAMENTO E ANALISI ---
uploaded_file = st.file_uploader("Scegli un'immagine (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Immagine caricata", use_container_width=True)
    
    if st.button("Estrai Dati", type="primary"):
        if model is None:
            st.error("Errore critico: API Key non valida o nessun modello AI disponibile.")
        else:
            with st.spinner("L'Intelligenza Artificiale sta analizzando l'immagine... attendi qualche secondo."):
                
                prompt = """
                Sei un estrattore di dati professionale. Guarda questa immagine.
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
                    response = model.generate_content([prompt, image])
                    risultato = response.text.strip()
                    risultato = risultato.replace("```text", "").replace("```", "").strip()
                    
                    st.success("Estrazione completata con successo!")
                    st.text_area("Anteprima Dati Estratti:", value=risultato, height=300)
                    
                    st.download_button(
                        label="📥 Scarica File TXT",
                        data=risultato,
                        file_name="dati_estratti.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"Si è verificato un errore durante l'estrazione: {e}")
